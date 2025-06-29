import logging

from django.db.models import Q  # Add this import at the top

from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import authentication, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from backend.canvas_app_explorer import models, serializers
from backend.canvas_app_explorer.canvas_lti_manager.django_factory import DjangoCourseLtiManagerFactory
from backend.canvas_app_explorer.canvas_lti_manager.exception import CanvasHTTPError

from rest_framework_tracking.models import APIRequestLog
from rest_framework_tracking.mixins import LoggingMixin
from django.utils import timezone
from django.db import transaction



logger = logging.getLogger(__name__)

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')

class UserEventViewSet(LoggingMixin, viewsets.ViewSet):
    """ViewSet for tracking frontend user events"""
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        """Log frontend events"""
        event_type = request.data.get('event_type')
        event_data = request.data.get('event_data', {})

        # The LoggingMixin will automatically log this request
        extra_data = {
            'event_type': event_type,
            'event_data': event_data,
            'course_id': request.session.get('course_id'),
        }

        # Update the log with relevant data
        self.log.update({
            'requested_at': timezone.now(),
            'path': self.request.path,
            'remote_addr': self.request.META.get('REMOTE_ADDR', ''),
            'host': self.request.META.get('HTTP_HOST', ''),
            'method': self.request.method,
            'user_id': getattr(self.request.user, 'id', None),
            'view': self.__class__.__name__,
            'view_method': self.request.method,
            'status_code': status.HTTP_201_CREATED,
            'query_params': self.request.query_params.dict(),
            'data': extra_data,
        })

        return Response(status=status.HTTP_201_CREATED)

class LTIToolViewSet(LoggingMixin, viewsets.ViewSet):
    """
    API endpoint that lists LTI tools available in the course context, and allows for enabling/disabling navigation.
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    # Add custom logging if needed
    logging_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']  # Only log these methods

    # Customize what gets logged
    def handle_log(self):
        """Hook to customize the log entry"""
        logger.info("Logging API request...")

        # Extract extra_data separately since it's handled differently
        extra_data = {
            'custom_field': 'custom_value',
            'course_id': self.request.session.get('course_id'),
        }

        # Get response and status_code safely
        response = getattr(self, 'response', None)
        status_code = response.status_code if response else None

        # Update the log with standard fields
        self.log.update({
            'requested_at': timezone.now(),
            'remote_addr': self.request.META.get('REMOTE_ADDR', ''),
            'host': self.request.META.get('HTTP_HOST', ''),
            'method': self.request.method,
            'user_id': getattr(self.request.user, 'id', None),
            'view': self.__class__.__name__,
            'view_method': self.request.method,
            'path': self.request.path,
            'status_code': status_code
        })

        # Create and save the log entry
        log_entry = APIRequestLog(**self.log)
        log_entry.data = extra_data
        log_entry.save()

        logger.info(f"Logging completed for user {self.request.user.id} in course {self.request.session.get('course_id')}")


    lookup_url_kwarg = 'canvas_id'

    def list(self, request: Request) -> Response:
        logger.debug(f"Course ID: {request.session['course_id']}")

        manager = MANAGER_FACTORY.create_manager(request)
        try:
            available_tools = manager.get_tools_available_in_course()
        except CanvasHTTPError as error:
            logger.error(error)
            return Response(data=error.to_dict(), status=error.status_code)

        logger.debug('available_tools: ' + ', '.join([tool.__str__() for tool in available_tools]))
        available_tool_ids = [t.id for t in available_tools]
        queryset = models.LtiTool.objects.filter(
            Q(canvas_id__isnull=False, canvas_id__in=available_tool_ids)
            | Q(launch_url__isnull=False)
        ).order_by('name')
        serializer = serializers.LtiToolWithNavSerializer(
            queryset, many=True, context={ 'available_tools': available_tools }
        )
        return Response(serializer.data)

    @extend_schema(
        parameters=[OpenApiParameter('canvas_id', location='path', required=True)],
        request=serializers.UpdateLtiToolNavigationSerializer
    )
    def update(self, request: Request, canvas_id: str):
        logger.debug(f"Canvas ID: {canvas_id}; request data: {request.data}")
        try:
            canvas_id_num = int(canvas_id)
        except ValueError:
            bad_request_data = {
                'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'canvas_id must be an integer.'
            }
            return Response(data=bad_request_data, status=status.HTTP_400_BAD_REQUEST)
        serializer = serializers.UpdateLtiToolNavigationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        navigation_enabled: bool = serializer.validated_data['navigation_enabled']

        manager = MANAGER_FACTORY.create_manager(request)
        try:
            manager.update_tool_navigation(canvas_id_num, not navigation_enabled)
        except CanvasHTTPError as error:
            logger.error(error)
            return Response(data=error.to_dict(), status=error.status_code)
        return Response(status=status.HTTP_200_OK)
