
from http import HTTPStatus
import logging
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import authentication, permissions, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from django.urls import reverse
from rest_framework_tracking.mixins import LoggingMixin
from django_q.tasks import async_task
from django.db.utils import DatabaseError
from backend.canvas_app_explorer.models import ContentItem, CourseScan, CourseScanStatus, ImageItem
from backend import settings
from backend.canvas_app_explorer.canvas_lti_manager.django_factory import DjangoCourseLtiManagerFactory
from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus
from backend.canvas_app_explorer.serializers import ContentQuerySerializer, ReviewContentItemSerializer
from backend.canvas_app_explorer.alt_text_helper.alt_text_update import AltTextUpate

logger = logging.getLogger(__name__)

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')

class CourseIdRequiredMixin:
    def _require_course_id(self, request: Request):
        """Return a tuple (course_id, None) or (None, Response) when missing privileges."""
        course_id = request.session.get('course_id')
        if course_id is None:
            message = "you don't have access for this course"
            logger.error(message)
            return None, Response(status=HTTPStatus.BAD_REQUEST, data={"status_code": HTTPStatus.BAD_REQUEST, "message": message})
        return course_id, None

class AltTextScanViewSet(LoggingMixin, CourseIdRequiredMixin, viewsets.ViewSet):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def start_scan(self, request: Request) -> Response:
        course_id, error_resp = self._require_course_id(request)
        if error_resp:
            return error_resp
        
        task_payload = {
            'course_id': course_id,
            'user_id': request.user.id,
            'canvas_callback_url': request.build_absolute_uri(reverse('canvas-oauth-callback')),
        }
        try:
            task_id = async_task('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.fetch_and_scan_course', task=task_payload)
            logger.info(f"Started alt text scan task {task_id} for course_id: {course_id}")

            # persist CourseScan: create new or update existing for this course
            obj, created = CourseScan.objects.update_or_create(
                course_id=int(course_id),
                defaults={
                    'q_task_id': str(task_id),
                    'status': CourseScanStatus.PENDING.value,
                }
            )
            logger.info(f"{obj} created: {created}")
            resp = {
                    'course_id': obj.course_id,
                    'id': obj.id,
                    'q_task_id': obj.q_task_id,
                    'status': obj.status,
                }
            return Response(resp, status=HTTPStatus.OK)
        except (DatabaseError, Exception) as e:
            message = f"Failed to initiate course scan due to {e}"
            logger.error(message)
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "message": message})
    
    def get_last_scan(self, request: Request) -> Response:
        course_id, error_resp = self._require_course_id(request)
        if error_resp:
            return error_resp
        try:
            scan_queryset = CourseScan.objects.filter(course_id=course_id)
            if not scan_queryset.exists():
                logger.info(f"No scan found for course id {course_id} and user {request.user.id}")
                resp = { 'found': False }
                return Response(resp, status=HTTPStatus.OK)
            
            scan_obj = scan_queryset.first()
            scan_detail = {
                    'id': scan_obj.id,
                    'course_id': scan_obj.course_id,
                    'status': scan_obj.status,
                    'created_at': scan_obj.created_at,
                    'updated_at': scan_obj.updated_at,
                    'course_content': self.__get_scan_course_content(scan_obj.course_id)
                }
            logger.info(f"Returning scan {scan_obj.id} for course id {course_id} and user {request.user.id}")
            resp = {
                'found': True,
                'scan_detail': scan_detail
            }
            return Response(resp, status=HTTPStatus.OK)
        except (DatabaseError, Exception) as e:
            message = f"Failed to retrieve last course scan for course_id {course_id} due to {e}"
            logger.error(message)
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "message": message})
        
    def __get_scan_course_content(self, course_id: int) -> object:
        try:
            content_by_type = {}
            for content_type,_ in ContentItem.CONTENT_TYPE_CHOICES:
                content_queryset = ContentItem.objects.filter(course_id=course_id, content_type=content_type).all()
                content_by_type[f'{content_type}_list'] = [
                    {
                        'id': content_item.id,
                        'canvas_id': content_item.content_id,
                        'canvas_name': content_item.content_name,
                        'image_count': ImageItem.objects.filter(content_item=content_item).count()
                    }
                    for content_item in content_queryset
                ]
            return content_by_type
        except (Exception) as e:
            logger.error(f"Problem appending course content to scan for course id f{course_id}")
            raise e

class AltTextContentGetAndUpdateViewSet(LoggingMixin, CourseIdRequiredMixin, viewsets.ViewSet):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='content_type', description='Type of content to  like assignment, page, quiz', required=True, type=str),
        ]
    )
    def get_content_images(self, request: Request) -> Response:
        course_id, error_resp = self._require_course_id(request)
        if error_resp:
            return error_resp
        # Support both DRF Request (has .query_params) and Django WSGIRequest (has .GET)
        params = getattr(request, 'query_params', request.GET)
        serializer = ContentQuerySerializer(data=params)
        if not serializer.is_valid():
            logger.error("Invalid query parameters for get_content_images: %s", serializer.errors)
            return Response(status=HTTPStatus.BAD_REQUEST, data={"status_code": HTTPStatus.BAD_REQUEST, "message": serializer.errors})

        content_type = serializer.validated_data['content_type']


        # fetch content items and associated images from DB
        try:
            # include quiz questions when requesting quizzes
            if content_type == ContentItem.CONTENT_TYPE_QUIZ:
                types_to_query = [ContentItem.CONTENT_TYPE_QUIZ, ContentItem.CONTENT_TYPE_QUIZ_QUESTION]
            else:
                types_to_query = [content_type]

            items_qs = ContentItem.objects.filter(course_id=course_id, content_type__in=types_to_query).prefetch_related('images')
            content_items = []

            for content_item in items_qs:
                images = []
                for img in content_item.images.all():
                    image_url = img.image_url
                    images.append({
                        'image_url': image_url,
                        'image_id': img.id,
                        'image_alt_text': img.image_alt_text,
                    })

                content_items.append({
                    'content_id': content_item.content_id,
                    'content_name': content_item.content_name,
                    'content_parent_id': content_item.content_parent_id,
                    'content_type': content_item.content_type,
                    'images': images,
                })

            resp = {'content_items': content_items}
            return Response(resp, status=HTTPStatus.OK)
        except (DatabaseError, Exception) as e:
            logger.error(f"Failed to fetch content images from DB for course {course_id} and content_type {content_type}: {e}")
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "message": str(e)})

    def alt_text_update(self, request: Request) -> Response:
        course_id, error_resp = self._require_course_id(request)
        if error_resp:
            return error_resp
        
        serializer = ReviewContentItemSerializer(data=request.data, many=True)
        if not serializer.is_valid():
             return Response(status=HTTPStatus.BAD_REQUEST, data={"message": serializer.errors})

        try:
             service = AltTextUpate(course_id, serializer.validated_data)
             service.process()
             return Response(status=HTTPStatus.OK)
        except Exception as e:
            logger.error(f"Failed to submit review: {e}")
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"message": str(e)})


