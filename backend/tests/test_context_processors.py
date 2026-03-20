from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from django.core import signing
from django.test import RequestFactory, TestCase

from backend.canvas_app_explorer.context_processors import (
    CAE_COURSE_USER_CONTEXT_SIGNING_SALT,
    cae_globals,
    get_signed_course_user_payload,
)


def verify_signed_course_user_payload(
    signed_payload: str,
    max_age: int | None = None,
) -> dict:
    return signing.loads(
        signed_payload,
        salt=CAE_COURSE_USER_CONTEXT_SIGNING_SALT,
        key=settings.CAE_COURSE_USER_CONTEXT_SIGNING_KEY,
        max_age=max_age,
    )


class TestContextProcessors(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _add_session(self, request):
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

    def test_get_signed_course_user_payload_round_trip(self):
        user_payload = {'username': 'alice', 'is_staff': False}

        signed_payload = get_signed_course_user_payload(42, user_payload)

        self.assertIsNotNone(signed_payload)
        verified = verify_signed_course_user_payload(signed_payload)
        self.assertEqual(verified['course_id'], 42)
        self.assertEqual(verified['user'], 'alice')

    def test_verify_signed_course_user_payload_rejects_tampering(self):
        user_payload = {'username': 'alice', 'is_staff': False}
        signed_payload = get_signed_course_user_payload(42, user_payload)

        with self.assertRaises(signing.BadSignature):
            verify_signed_course_user_payload(f'{signed_payload}tampered')

    def test_cae_globals_includes_signed_course_user_payload(self):
        request = self.factory.get('/')
        self._add_session(request)
        request.session['course_id'] = 77

        user = User.objects.create_user(username='bob', password='pw')
        request.user = user

        context = cae_globals(request)

        self.assertIn('cae_globals', context)
        self.assertIn('signed_course_user_payload', context['cae_globals'])

        verified = verify_signed_course_user_payload(
            context['cae_globals']['signed_course_user_payload']
        )

        self.assertEqual(verified['course_id'], 77)
        self.assertEqual(verified['user'], 'bob')

    def test_get_signed_course_user_payload_returns_none_without_required_values(self):
        self.assertIsNone(get_signed_course_user_payload(None, {'username': 'alice', 'is_staff': False}))
        self.assertIsNone(get_signed_course_user_payload(1, None))
