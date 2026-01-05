
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

logger = logging.getLogger(__name__)

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')

class AltTextScanViewSet(LoggingMixin,viewsets.ViewSet):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
            parameters=[OpenApiParameter('course_id', location='path', required=True)],
    )
    def start_scan(self, request: Request, course_id: int) -> Response:
        logger.info(f"request.build_absolute_uri(reverse('canvas-oauth-callback')): {request.build_absolute_uri(reverse('canvas-oauth-callback'))}")
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
    
    def get_last_scan(self, request: Request, course_id: int) -> Response:
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
