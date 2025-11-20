
from http import HTTPStatus
import logging

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import authentication, permissions, status, viewsets
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
    def start_scan(self, request: Request, course_id: str = None) -> Response:
        # placeholder for scan logic, test Django Q2 setup
        logger.info(f"Received request to start alt text scan for course_id: {request.data.get('course_id')}")
        # task_id = async_task('backend.canvas_app_explorer.alt_text_helper.tasks.simple_math_task')
        task_payload = {
            'course_id': request.data.get('course_id'),
            'user_id': request.user.id,
            'canvas_callback_url': request.build_absolute_uri(reverse('canvas-oauth-callback')),
        }
        task_id = async_task('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.fetch_and_scan_course', task=task_payload)
        logger.info(f"Started alt text scan task {task_id} for course_id: {request.data.get('course_id')}")
        # persist CourseScan: create new or update existing for this course
        canvas_id_val = request.data.get('course_id') or course_id
        try:
            canvas_id_int = int(canvas_id_val)
        except (TypeError, ValueError):
            logger.warning("Invalid course_id provided for CourseScan: %r", canvas_id_val)
            return Response({"detail": "Invalid course_id"}, status=HTTPStatus.BAD_REQUEST)

        try:
            with transaction.atomic():
                obj, created = CourseScan.objects.update_or_create(
                    course_id=canvas_id_int,
                    defaults={
                        'q_task_id': str(task_id),
                        'status': 'pending',
                    }
                )
            logger.info("CourseScan %s for course_id=%s (q_task_id=%s)", 'created' if created else 'updated', canvas_id_int, task_id)
        except IntegrityError:
            logger.exception("IntegrityError saving CourseScan for course_id=%s", canvas_id_int)
        except Exception:
            logger.exception("Unexpected error saving CourseScan for course_id=%s", canvas_id_int)

        return Response(task_id)

