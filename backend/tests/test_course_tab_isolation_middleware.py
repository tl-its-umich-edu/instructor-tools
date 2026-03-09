from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import signing
from django.http import HttpResponse
import json
from django.test import RequestFactory, TestCase

from backend.canvas_app_explorer.context_processors import CAE_COURSE_USER_CONTEXT_SIGNING_SALT
from backend.canvas_app_explorer.middleware import CourseTabIsolationMiddleware


class TestCourseTabIsolationMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _add_session(self, request):
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

    def _signed_payload(self, course_id, username: str) -> str:
        payload = {
            'course_id': course_id,
            'user': username,
        }
        return signing.dumps(
            payload,
            salt=CAE_COURSE_USER_CONTEXT_SIGNING_SALT,
            key=settings.CAE_COURSE_USER_CONTEXT_SIGNING_KEY,
            compress=True,
        )

    def test_sets_request_course_id_from_valid_signed_payload(self):
        request = self.factory.get('/api/alt-text/scan')
        self._add_session(request)
        request.user = User.objects.create_user(username='alice', password='pw')
        request.META['HTTP_X_SIGNED_COURSE_USER_PAYLOAD'] = self._signed_payload(123, 'alice')

        captured = {}

        def get_response(req):
            captured['course_id'] = req.course_id
            return HttpResponse(status=200)

        middleware = CourseTabIsolationMiddleware(get_response)
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(captured['course_id'], 123)

    def test_returns_bad_request_for_tampered_payload(self):
        request = self.factory.get('/api/alt-text/scan')
        self._add_session(request)
        request.user = User.objects.create_user(username='alice', password='pw')
        request.META['HTTP_X_SIGNED_COURSE_USER_PAYLOAD'] = f"{self._signed_payload(123, 'alice')}tampered"

        middleware = CourseTabIsolationMiddleware(lambda req: HttpResponse(status=200))
        response = middleware(request)

        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body['status_code'], 400)
        self.assertEqual(body['message'], 'Invalid course context signature.')

    def test_returns_bad_request_for_user_mismatch(self):
        request = self.factory.get('/api/alt-text/scan')
        self._add_session(request)
        request.user = User.objects.create_user(username='alice', password='pw')
        request.META['HTTP_X_SIGNED_COURSE_USER_PAYLOAD'] = self._signed_payload(123, 'bob')

        middleware = CourseTabIsolationMiddleware(lambda req: HttpResponse(status=200))
        response = middleware(request)

        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body['status_code'], 400)
        self.assertEqual(body['message'], 'Signed payload user mismatch.')

    def test_returns_bad_request_when_header_missing(self):
        request = self.factory.get('/api/alt-text/scan')
        self._add_session(request)
        request.session['course_id'] = 77
        request.user = AnonymousUser()

        middleware = CourseTabIsolationMiddleware(lambda req: HttpResponse(status=200))
        response = middleware(request)

        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body['status_code'], 400)
        self.assertEqual(body['message'], 'Missing signed course context header.')

    def test_returns_bad_request_when_course_id_is_none(self):
        request = self.factory.get('/api/alt-text/scan')
        self._add_session(request)
        request.user = User.objects.create_user(username='alice', password='pw')
        request.META['HTTP_X_SIGNED_COURSE_USER_PAYLOAD'] = self._signed_payload(None, 'alice')

        middleware = CourseTabIsolationMiddleware(lambda req: HttpResponse(status=200))
        response = middleware(request)

        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body['status_code'], 400)
        self.assertEqual(body['message'], 'Invalid course context payload content.')

    def test_returns_bad_request_when_course_id_is_empty_string(self):
        request = self.factory.get('/api/alt-text/scan')
        self._add_session(request)
        request.user = User.objects.create_user(username='alice', password='pw')
        request.META['HTTP_X_SIGNED_COURSE_USER_PAYLOAD'] = self._signed_payload('', 'alice')

        middleware = CourseTabIsolationMiddleware(lambda req: HttpResponse(status=200))
        response = middleware(request)

        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body['status_code'], 400)
        self.assertEqual(body['message'], 'Invalid course context payload content.')
