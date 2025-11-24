
from http import HTTPStatus
import logging

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import authentication, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework_tracking.mixins import LoggingMixin

from django_q.tasks import async_task

logger = logging.getLogger(__name__)

class AltTextScanViewSet(LoggingMixin,viewsets.ViewSet):
    @extend_schema(
            parameters=[OpenApiParameter('course_id', location='path', required=True)],
    )
    def start_scan(self, request: Request, course_id: str = None) -> Response:
        # placeholder for scan logic, test Django Q2 setup
        task_id = async_task('backend.canvas_app_explorer.alt_text_helper.tasks.simple_math_task')
        
        return Response(task_id)

