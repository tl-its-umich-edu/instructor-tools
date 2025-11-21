
from http import HTTPStatus
import logging

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from django.urls import reverse

from rest_framework_tracking.mixins import LoggingMixin

from django_q.tasks import async_task
from django.db import transaction
from django.db.utils import IntegrityError
from backend.canvas_app_explorer.models import CourseScan

logger = logging.getLogger(__name__)

class AltTextScanViewSet(LoggingMixin,viewsets.ViewSet):
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
                    'status': 'pending',
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
        except (IntegrityError, Exception) as e:
            message = f"Failed to initiate course scan due to {e}"
            logger.error(message)
            return Response({"status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "message": message})

