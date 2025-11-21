from canvas_oauth.oauth import get_oauth_token
from django.http import HttpRequest
import logging

from .manager import CanvasLtiManager
from canvasapi import Canvas

logger = logging.getLogger(__name__)

class DjangoCourseLtiManagerFactory:
    """
    Factory class creating CourseLtiManager instances using HttpRequest objects.
    Assumes course_id is set in the session and that the Django Canvas OAuth app is set up.
    """

    def __init__(self, api_url: str):
        self.api_url = api_url

    def create_manager(self, request: HttpRequest) -> CanvasLtiManager:
        course_id = request.session['course_id']
        logger.info(f"COURSE_ID = {course_id}")
        logger.info(f"Request details: {request.__dict__}")
        token = get_oauth_token(request)
        return CanvasLtiManager(self.api_url, token, course_id)
    
    def get_canvasapi(self, request: HttpRequest) -> Canvas:
        token = get_oauth_token(request)
        return Canvas(self.api_url, token)
