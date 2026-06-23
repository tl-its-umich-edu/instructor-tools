from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from backend.canvas_app_explorer.canvas_roles import (
    get_additional_staff_course_role_values,
    get_default_staff_course_role_values,
    get_effective_staff_course_role_values,
)
from backend.canvas_app_explorer.lti1p3 import create_user_in_django


class TestCanvasRoleResolution(TestCase):
    def test_effective_roles_always_include_default_roles(self):
        with patch('backend.canvas_app_explorer.canvas_roles.config') as mock_config:
            mock_config.ADDITIONAL_STAFF_COURSE_ROLES = ''

            effective_roles = get_effective_staff_course_role_values()
            default_roles = get_default_staff_course_role_values()

            for role in default_roles:
                self.assertIn(role, effective_roles)

            self.assertIn('account admin', effective_roles)
            self.assertIn('sub-account admin', effective_roles)
            self.assertIn('teacherenrollment', effective_roles)

    def test_additional_roles_are_trimmed_and_deduplicated(self):
        with patch('backend.canvas_app_explorer.canvas_roles.config') as mock_config:
            mock_config.ADDITIONAL_STAFF_COURSE_ROLES = (
                ' Junior Admin ,Instructional Designer,Junior Admin, Root privileges for any Admin '
            )

            additional_roles = get_additional_staff_course_role_values()

            self.assertEqual(
                set(additional_roles),
                {'junior admin', 'instructional designer', 'root privileges for any admin'},
            )

    def test_additional_roles_support_single_value_and_none(self):
        with patch('backend.canvas_app_explorer.canvas_roles.config') as mock_config:
            mock_config.ADDITIONAL_STAFF_COURSE_ROLES = 'Junior Admin'
            self.assertEqual(get_additional_staff_course_role_values(), ['junior admin'])

            mock_config.ADDITIONAL_STAFF_COURSE_ROLES = None
            self.assertEqual(get_additional_staff_course_role_values(), [])

    def test_effective_roles_merge_default_and_additional(self):
        with patch('backend.canvas_app_explorer.canvas_roles.config') as mock_config:
            mock_config.ADDITIONAL_STAFF_COURSE_ROLES = 'Junior Admin,Instructional Designer'

            effective_roles = get_effective_staff_course_role_values()

            self.assertIn('account admin', effective_roles)
            self.assertIn('sub-account admin', effective_roles)
            self.assertIn('teacherenrollment', effective_roles)
            self.assertIn('junior admin', effective_roles)
            self.assertIn('instructional designer', effective_roles)


class TestLtiRoleAuthorizationWithConfigurableRoles(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request_with_session(self):
        request = self.factory.post('/launch')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def _launch_data(self, username: str, course_roles: str):
        return {
            'https://purl.imsglobal.org/spec/lti/claim/custom': {
                'user_username': username,
                'canvas_course_id': '123',
                'canvas_course_roles': course_roles,
            },
            'https://purl.imsglobal.org/spec/lti/claim/context': {'title': 'Test Course'},
            'https://purl.imsglobal.org/spec/lti/claim/roles': [],
            'https://purl.imsglobal.org/spec/lti/claim/lis': {'person_sourcedid': f'sis-{username}'},
            'email': f'{username}@example.edu',
            'given_name': 'Test',
            'family_name': 'User',
            'name': 'Test User',
        }

    def test_default_teacher_role_still_authorized(self):
        request = self._request_with_session()
        launch_data = self._launch_data('teacher-user', 'TEACHERENROLLMENT')

        with patch(
            'backend.canvas_app_explorer.lti1p3.get_effective_staff_course_role_values',
            return_value=['account admin', 'sub-account admin', 'teacherenrollment'],
        ):
            create_user_in_django(request, launch_data)

        self.assertEqual(request.session['course_id'], 123)

    def test_junior_admin_can_be_authorized_via_configured_roles(self):
        request = self._request_with_session()
        launch_data = self._launch_data('junior-admin-user', 'JUNIOR ADMIN')

        with patch(
            'backend.canvas_app_explorer.lti1p3.get_effective_staff_course_role_values',
            return_value=['account admin', 'sub-account admin', 'teacherenrollment', 'junior admin'],
        ):
            create_user_in_django(request, launch_data)

        self.assertEqual(request.session['course_id'], 123)

    def test_root_privileges_role_can_be_authorized_via_configured_roles(self):
        request = self._request_with_session()
        launch_data = self._launch_data('root-admin-user', 'ROOT PRIVILEGES FOR ANY ADMIN')

        with patch(
            'backend.canvas_app_explorer.lti1p3.get_effective_staff_course_role_values',
            return_value=[
                'account admin',
                'sub-account admin',
                'teacherenrollment',
                'root privileges for any admin',
            ],
        ):
            create_user_in_django(request, launch_data)

        self.assertEqual(request.session['course_id'], 123)

    def test_unconfigured_non_staff_role_is_denied(self):
        request = self._request_with_session()
        launch_data = self._launch_data('non-staff-user', 'Junior Admin')

        with patch(
            'backend.canvas_app_explorer.lti1p3.get_effective_staff_course_role_values',
            return_value=['account admin', 'sub-account admin', 'teacherenrollment'],
        ):
            with self.assertRaises(PermissionDenied):
                create_user_in_django(request, launch_data)
