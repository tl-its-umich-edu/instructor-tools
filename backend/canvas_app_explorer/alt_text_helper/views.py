
from http import HTTPStatus
import logging


from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import authentication, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from django.urls import reverse

from rest_framework_tracking.mixins import LoggingMixin

from django_q.tasks import async_task
from django.db.utils import DatabaseError
from backend import settings
from backend.canvas_app_explorer.canvas_lti_manager.django_factory import DjangoCourseLtiManagerFactory
from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus
from backend.canvas_app_explorer.alt_text_helper.get_content_images import GetContentImages

logger = logging.getLogger(__name__)

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')

class AltTextScanViewSet(LoggingMixin,viewsets.ViewSet):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
            parameters=[OpenApiParameter('course_id', location='path', required=True)],
    )
    def start_scan(self, request: Request) -> Response:
        course_id = request.data.get('course_id')
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
            return Response({"status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "message": message})

class AltTextGetContentImagesViewSet(LoggingMixin,viewsets.ViewSet):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
            parameters=[OpenApiParameter('content_type', location='query', required=True)],
    )
    def get_content_images(self, request: Request, course_id: str = None) -> Response:
        # course_id comes from path parameter
        content_type = request.query_params.get('content_type')
        logger.info(f"Getting content images for course_id: {course_id}, content_type: {content_type}")
        canvas_api = MANAGER_FACTORY.create_manager(request).canvas_api
        content_images = GetContentImages(course_id, content_type, canvas_api)
        images = content_images.get_images_by_course()
        return Response({'course': course_id, 'content_type': content_type}, status=HTTPStatus.OK)
