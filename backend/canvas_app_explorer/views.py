import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import authentication, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from backend.canvas_app_explorer import models, serializers
from backend.canvas_app_explorer.canvas_lti_manager.django_factory import DjangoCourseLtiManagerFactory
from backend.canvas_app_explorer.canvas_lti_manager.exception import CanvasHTTPError

logger = logging.getLogger(__name__)

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')


class LTIToolViewSet(viewsets.ViewSet):
    """
    API endpoint that lists LTI tools available in the course context, and allows for enabling/disabling navigation.
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

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
        queryset = models.LtiTool.objects.filter(canvas_id__isnull=False, canvas_id__in=available_tool_ids, is_public=True)\
            .order_by('name')
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
