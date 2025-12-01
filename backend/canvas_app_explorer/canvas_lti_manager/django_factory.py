from canvas_oauth.oauth import get_oauth_token
from django.http import HttpRequest

from .manager import CanvasLtiManager

class DjangoCourseLtiManagerFactory:
    """
    Factory class creating CourseLtiManager instances using HttpRequest objects.
    Assumes course_id is set in the session and that the Django Canvas OAuth app is set up.
    """

    def __init__(self, api_url: str):
        self.api_url = api_url

    def create_manager(self, request: HttpRequest) -> CanvasLtiManager:
        course_id = request.session['course_id']
        token = get_oauth_token(request)
        return CanvasLtiManager(self.api_url, token, course_id)
