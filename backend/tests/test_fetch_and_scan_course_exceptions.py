from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import timedelta
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    fetch_and_scan_course,
    canvas_setup,
)
from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus, CourseScanErrorLog
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from backend.canvas_app_explorer.utils import generate_canvas_content_url
from canvas_oauth.exceptions import InvalidOAuthReturnError
from canvas_oauth.models import CanvasOAuth2Token
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.utils import timezone


class TestCanvasSetupFunction(TestCase):
    def setUp(self):
        self.course_id = 999
        self.course_scan = CourseScan.objects.create(course_id=self.course_id)
        self.user = User.objects.create_user(username='setup_user', password='testpass')
        self.request = RequestFactory().get('/oauth/oauth-callback')
        self.request.user = self.user

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_canvas_setup_happy_path_returns_canvas_api_and_token(self, mock_factory):
        mock_manager = MagicMock()
        mock_manager.canvas_api = MagicMock()
        mock_manager.api_key = 'token-123'
        mock_factory.create_manager.return_value = mock_manager

        canvas_api, bearer_token = canvas_setup(self.course_scan.id, self.course_id, self.request)

        self.assertEqual(canvas_api, mock_manager.canvas_api)
        self.assertEqual(bearer_token, 'token-123')

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_canvas_setup_invalid_oauth_deletes_token_and_reraises(self, mock_factory):
        CanvasOAuth2Token.objects.create(
            user=self.user,
            access_token='access-token',
            refresh_token='refresh-token',
            expires=timezone.now() + timedelta(hours=1),
        )
        mock_factory.create_manager.side_effect = InvalidOAuthReturnError('Auth failed')

        with self.assertRaises(InvalidOAuthReturnError):
            canvas_setup(self.course_scan.id, self.course_id, self.request)

        self.assertFalse(CanvasOAuth2Token.objects.filter(user=self.user).exists())

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_canvas_setup_generic_exception_is_caught_and_reraised(self, mock_factory):
        mock_factory.create_manager.side_effect = RuntimeError('manager setup failed')

        with self.assertRaises(RuntimeError):
            canvas_setup(self.course_scan.id, self.course_id, self.request)


class TestFetchAndScanCourseExceptionHandling(TestCase):
    """Test suite for exception handling in fetch_and_scan_course function."""

    def setUp(self):
        """Set up test fixtures."""
        self.course_id = 999
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.course_scan = CourseScan.objects.create(course_id=self.course_id, status=CourseScanStatus.PENDING.value)
        self.task = {
            'course_scan_id': self.course_scan.id,
            'course_id': self.course_id,
            'user_id': self.user.id,
            'canvas_callback_url': 'http://localhost/callback'
        }

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_manager_creation_exception(self, mock_factory):
        """Test that manager creation exceptions result in FAILED status."""
        # Make manager creation fail
        mock_factory.create_manager.side_effect = InvalidOAuthReturnError("Auth failed")
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        self.course_scan.refresh_from_db()
        self.assertEqual(self.course_scan.status, CourseScanStatus.FAILED.value)

        # When setup fails, error records are persisted for scan visibility/auditing
        self.assertTrue(CourseScanErrorLog.objects.filter(course_scan=self.course_scan).exists())

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_content_fetch_failure(
        self, mock_factory, mock_async_to_sync, mock_unpack
    ):
        """Test that content fetch failure (unpack returns errors) results in FAILED status."""
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_canvas_api._Canvas__requester = None
        mock_manager.canvas_api = mock_canvas_api
        mock_manager.api_key = 'fake-token'
        
        # Make unpack_and_store_content_images return errors (fetch failed)
        mock_unpack.return_value = ([], [{
            'type': 'content_fetch_error',
            'title': 'Course',
            'error': Exception('fetch failed'),
            'canvas_url': 'https://example.com/course',
        }])
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        self.course_scan.refresh_from_db()
        self.assertEqual(self.course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_get_courses_images_exception(
        self, mock_factory, mock_async_to_sync, mock_unpack
    ):
        """Test that exceptions in async_to_sync(get_courses_images) result in FAILED status."""
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_canvas_api._Canvas__requester = None
        mock_manager.canvas_api = mock_canvas_api
        mock_manager.api_key = 'fake-token'
        
        # Make async_to_sync raise an exception
        mock_async_to_sync.side_effect = RuntimeError("Async fetch failed")
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        self.course_scan.refresh_from_db()
        self.assertEqual(self.course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_course_creation_exception(
        self, mock_factory, mock_course_class, mock_async_to_sync, mock_unpack
    ):
        """Test that Course object creation exceptions result in FAILED status."""
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_canvas_api._Canvas__requester = None
        mock_manager.canvas_api = mock_canvas_api
        mock_manager.api_key = 'fake-token'
        
        # Make Course creation fail
        mock_course_class.side_effect = Exception("Course creation failed")
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        self.course_scan.refresh_from_db()
        self.assertEqual(self.course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_image_content_extraction_exception(
        self, mock_factory, mock_async_to_sync, mock_unpack, mock_retrieve_alt
    ):
        """Test that ImageContentExtractionException results in FAILED status."""
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_canvas_api._Canvas__requester = None
        mock_manager.canvas_api = mock_canvas_api
        mock_manager.api_key = 'fake-token'
        
        mock_async_to_sync.return_value = MagicMock(return_value=([], [], []))
        mock_unpack.return_value = ([], [])
        
        # Make retrieve_and_store_alt_text raise ImageContentExtractionException
        mock_retrieve_alt.side_effect = ImageContentExtractionException(errors=['Alt text fetch failed'])
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        self.course_scan.refresh_from_db()
        self.assertEqual(self.course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_unexpected_exception(
        self, mock_factory, mock_async_to_sync, mock_unpack, mock_retrieve_alt
    ):
        """Test that any unexpected exception results in FAILED status."""
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_canvas_api._Canvas__requester = None
        mock_manager.canvas_api = mock_canvas_api
        mock_manager.api_key = 'fake-token'
        
        mock_async_to_sync.return_value = MagicMock(return_value=([], [], []))
        mock_unpack.return_value = ([], [])
        
        # Make retrieve_and_store_alt_text raise a generic exception
        mock_retrieve_alt.side_effect = ValueError("Unexpected error occurred")
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        self.course_scan.refresh_from_db()
        self.assertEqual(self.course_scan.status, CourseScanStatus.FAILED.value)

        # Verify the unexpected_error payload is persisted through update_course_scan -> log_course_scan_errors
        logged_error = CourseScanErrorLog.objects.filter(course_scan=self.course_scan).first()
        self.assertIsNotNone(logged_error)
        self.assertEqual(logged_error.error_type, 'unexpected_error')
        self.assertEqual(logged_error.error_title, 'Course')
        self.assertIn('Unexpected error occurred', logged_error.error_message)
        self.assertEqual(logged_error.canvas_url, generate_canvas_content_url(self.course_id, 'course'))

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.update_course_scan')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_completes_successfully(
        self, mock_factory, mock_async_to_sync, mock_unpack, mock_retrieve_alt, mock_update_scan
    ):
        """Test that successful scan completes with COMPLETED status."""
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_canvas_api._Canvas__requester = None
        mock_manager.canvas_api = mock_canvas_api
        mock_manager.api_key = 'fake-token'
        
        mock_async_to_sync.return_value = MagicMock(return_value=([], [], []))
        mock_unpack.return_value = ([], [])
        mock_retrieve_alt.return_value = True
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify update_course_scan was called with COMPLETED status at the end
        calls = mock_update_scan.call_args_list
        # Last call should be with COMPLETED status
        self.assertEqual(calls[-1][0], (self.course_scan.id, CourseScanStatus.COMPLETED))
        self.assertEqual(calls[-1][1].get('course_id'), self.course_id)
