from __future__ import annotations

from http import HTTPStatus
import logging
from typing import Any

from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, JsonResponse

from backend.canvas_app_explorer.context_processors import CAE_COURSE_USER_CONTEXT_SIGNING_SALT

logger = logging.getLogger(__name__)

SIGNED_PAYLOAD_HEADER = 'X-Signed-Course-User-Payload'


class CourseTabIsolationMiddleware:
    """
    Validates a signed course/user payload header for API requests and stores
    the verified course id on request.course_id.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith('/api/'):
            signed_payload = request.headers.get(SIGNED_PAYLOAD_HEADER)
            if not signed_payload:
                return self._bad_request_response('Missing signed course context header.')

            try:
                request.course_id = self._verify_and_extract_course_id(request, signed_payload)
            except PermissionDenied as exc:
                return self._bad_request_response(str(exc))

        return self.get_response(request)

    def _bad_request_response(self, message: str) -> JsonResponse:
        return JsonResponse(
            {
                'status_code': HTTPStatus.BAD_REQUEST,
                'message': message,
            },
            status=HTTPStatus.BAD_REQUEST,
        )

    def _verify_and_extract_course_id(self, request: HttpRequest, signed_payload: str) -> int:
        try:
            payload: Any = signing.loads(
                signed_payload,
                salt=CAE_COURSE_USER_CONTEXT_SIGNING_SALT,
                key=settings.CAE_COURSE_USER_CONTEXT_SIGNING_KEY,
            )
        except (signing.BadSignature, signing.SignatureExpired, TypeError, Exception) as exc:
            logger.warning('Invalid signed course payload header: %s', exc)
            raise PermissionDenied('Invalid course context signature.')

        if not isinstance(payload, dict):
            raise PermissionDenied('Invalid course context payload format.')

        if 'course_id' not in payload:
            raise PermissionDenied('Invalid course context payload content.')

        try:
            course_id = int(payload['course_id'])
            payload_username = payload.get('user')
        except (TypeError, ValueError):
            raise PermissionDenied('Invalid course_id in signed payload.')

        if payload_username is not None and not isinstance(payload_username, str):
            raise PermissionDenied('Invalid user in signed payload.')

        request_username = getattr(request.user, 'username', None)

        if payload_username and request.user.is_authenticated and payload_username != request_username:
            raise PermissionDenied('Signed payload user mismatch.')

        return course_id
