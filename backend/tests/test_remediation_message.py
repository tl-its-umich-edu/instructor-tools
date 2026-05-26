from django.test import TestCase
from backend.canvas_app_explorer.alt_text_helper.views import AltTextScanViewSet


class TestRemediationMessage(TestCase):
    """Test the _get_remediation_message method of AltTextScanViewSet."""

    def setUp(self):
        """Initialize the viewset for testing."""
        self.viewset = AltTextScanViewSet()

    def test_system_level_error_type_returns_system_message(self):
        """System-level error types should return system-level message."""
        for error_type in ['canvas_manager_setup_error', 'content_database_save']:
            with self.subTest(error_type=error_type):
                message = self.viewset._get_remediation_message(error_type, 'Some Title')
                self.assertEqual(message, 'Try again, refresh browser, or contact support')

    def test_system_level_error_title_returns_system_message(self):
        """System-level error titles should return system-level message."""
        for error_title in ['Course', 'assignments', 'pages', 'quizzes']:
            with self.subTest(error_title=error_title):
                message = self.viewset._get_remediation_message('some_error', error_title)
                self.assertEqual(message, 'Try again, refresh browser, or contact support')

    def test_item_level_error_returns_edit_delete_message(self):
        """Item-level errors should return edit or delete message."""
        for error_type in ['image_process_error', 'alt_text_process_error']:
            with self.subTest(error_type=error_type):
                message = self.viewset._get_remediation_message(error_type, 'Some Image')
                self.assertEqual(message, 'Edit or delete the image in this content')

    def test_generic_error_returns_edit_delete_message(self):
        """Generic (non-system, non-token) errors should return edit or delete message."""
        message = self.viewset._get_remediation_message('unknown_error', 'Unknown')
        self.assertEqual(message, 'Edit or delete the image in this content')

    def test_system_level_title_overrides_item_level_error_type(self):
        """System-level title should override item-level error type."""
        message = self.viewset._get_remediation_message('image_process_error', 'Course')
        self.assertEqual(message, 'Try again, refresh browser, or contact support')

    def test_token_error_type_returns_edit_delete_message(self):
        """Token Error type (when not system-level title) returns edit/delete message."""
        # Current implementation doesn't have special handling for Token Error
        # so it falls through to default behavior
        message = self.viewset._get_remediation_message('Token Error', 'Some Title')
        self.assertEqual(message, 'Edit or delete the image in this content')
