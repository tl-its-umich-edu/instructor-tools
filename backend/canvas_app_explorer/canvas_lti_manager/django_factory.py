from canvas_oauth.oauth import get_oauth_token
from django.http import HttpRequest

from .manager import CanvasLtiManager

class DjangoCourseLtiManagerFactory:
    """
    Factory class creating CourseLtiManager instances using HttpRequest objects.
    course_id is sent from the API call that was sent using signed payload generated in 
    the cae_globals context processor, so the factory relies on the CourseTabIsolationMiddleware 
    to validate the payload and set request.course_id. The middleware raises exceptions for missing/invalid payloads, 
    so this factory assumes that if request.course_id is present, it is valid.
    """

    def __init__(self, api_url: str):
        self.api_url = api_url

    def create_manager(self, request: HttpRequest) -> CanvasLtiManager:
        course_id = getattr(request, 'course_id')
        token = get_oauth_token(request)
        return CanvasLtiManager(self.api_url, token, course_id)
