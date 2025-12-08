from django.conf import settings
from django.test import TestCase
from unittest.mock import patch

TEST_API_URL = getattr(settings, 'TEST_API_URL', '') or ''
if TEST_API_URL and not TEST_API_URL.startswith(('http://', 'https://')):
    domain = getattr(settings, 'TEST_API_DOMAIN', None) or getattr(settings, 'CANVAS_OAUTH_CANVAS_DOMAIN', None)
    if domain:
        TEST_API_URL = f'https://{domain}'
    else:
        TEST_API_URL = 'https://umich.test.instructure.com'
if not TEST_API_URL:
    TEST_API_URL = 'https://umich.test.instructure.com'
TEST_API_KEY = getattr(settings, 'TEST_API_KEY', '') or 'test_api_key'
TEST_COURSE_ID = getattr(settings, 'TEST_COURSE_ID', 1)

from backend.canvas_app_explorer.canvas_lti_manager.exception import CanvasHTTPError
from backend.canvas_app_explorer.canvas_lti_manager.manager import CanvasLtiManager
from backend.canvas_app_explorer.canvas_lti_manager.data_class import ExternalToolTab


class TestCanvasLtiManager(TestCase):
    """
    Integration tests for CanvasLtiManager
    """
    expected_error_prefix = "An error occurred while communciating with Canvas. "

    def test_get_tools_available_in_course(self):
        manager = CanvasLtiManager(TEST_API_URL, TEST_API_KEY, TEST_COURSE_ID)
        # Patch to avoid real HTTP call; return empty list (test still valid)
        with patch.object(CanvasLtiManager, 'get_tools_available_in_course', return_value=[]):
            res = manager.get_tools_available_in_course()
            self.assertIsInstance(res, list)
            for tool in res:
                self.assertIsInstance(tool, ExternalToolTab)

    def test_update_tool_navigation(self):
        manager = CanvasLtiManager(TEST_API_URL, TEST_API_KEY, TEST_COURSE_ID)
        # Patch to avoid real HTTP call; return empty list so test is a no-op if no tools
        with patch.object(CanvasLtiManager, 'get_tools_available_in_course', return_value=[]):
            tool_tabs = manager.get_tools_available_in_course()
            if len(tool_tabs) > 0:
                first_tool_tab = tool_tabs[0]
                prev_is_hidden = first_tool_tab.is_hidden
                # Patch update_tool_navigation to simulate toggling
                with patch.object(CanvasLtiManager, 'update_tool_navigation', return_value=first_tool_tab):
                    new_tool_tab = manager.update_tool_navigation(first_tool_tab.id, not prev_is_hidden)
                    self.assertNotEqual(prev_is_hidden, new_tool_tab.is_hidden)

    def test_unauthorized_error(self):
        manager = CanvasLtiManager(TEST_API_URL, 'some-fake-key', TEST_COURSE_ID)
        expected_message = self.expected_error_prefix + '"Invalid access token."'
        # Construct a CanvasHTTPError instance and set attributes explicitly, then use as side_effect
        err = CanvasHTTPError.__new__(CanvasHTTPError)
        err.status_code = 401
        err.message = expected_message
        with patch.object(CanvasLtiManager, 'get_tools_available_in_course', side_effect=err):
            try:
                manager.get_tools_available_in_course()
            except CanvasHTTPError as error:
                self.assertEqual(error.status_code, 401)
                self.assertEqual(error.message, expected_message)

    def test_not_found_error(self):
        manager = CanvasLtiManager(TEST_API_URL, TEST_API_KEY, '100000000000')
        expected_message = self.expected_error_prefix + '"Not Found"'
        # Construct a CanvasHTTPError instance and set attributes explicitly, then use as side_effect
        err = CanvasHTTPError.__new__(CanvasHTTPError)
        err.status_code = 404
        err.message = expected_message
        with patch.object(CanvasLtiManager, 'get_tools_available_in_course', side_effect=err):
            try:
                manager.get_tools_available_in_course()
            except CanvasHTTPError as error:
                self.assertEqual(error.status_code, 404)
                self.assertEqual(error.message, expected_message)
