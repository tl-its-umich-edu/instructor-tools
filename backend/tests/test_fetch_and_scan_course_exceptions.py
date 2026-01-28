from django.test import TestCase
from unittest.mock import patch, MagicMock
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    fetch_and_scan_course,
)
from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from canvas_oauth.exceptions import InvalidOAuthReturnError
from django.contrib.auth.models import User


class TestFetchAndScanCourseExceptionHandling(TestCase):
    """Test suite for exception handling in fetch_and_scan_course function."""

    def setUp(self):
        """Set up test fixtures."""
        self.course_id = 999
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.task = {
            'course_id': self.course_id,
            'user_id': self.user.id,
            'canvas_callback_url': 'http://localhost/callback'
        }

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_manager_creation_exception(self, mock_factory):
        """Test that manager creation exceptions result in FAILED status."""
        # Create initial CourseScan
        course_scan = CourseScan.objects.create(course_id=self.course_id, status=CourseScanStatus.PENDING.value)
        
        # Make manager creation fail
        mock_factory.create_manager.side_effect = InvalidOAuthReturnError("Auth failed")
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        course_scan.refresh_from_db()
        self.assertEqual(course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_content_fetch_failure(
        self, mock_factory, mock_async_to_sync, mock_unpack
    ):
        """Test that content fetch failure (unpack returns False) results in FAILED status."""
        course_scan = CourseScan.objects.create(course_id=self.course_id, status=CourseScanStatus.PENDING.value)
        
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_manager.canvas_api = mock_canvas_api
        
        # Make unpack_and_store_content_images return False (fetch failed)
        mock_unpack.return_value = False
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        course_scan.refresh_from_db()
        self.assertEqual(course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_get_courses_images_exception(
        self, mock_factory, mock_async_to_sync, mock_unpack
    ):
        """Test that exceptions in async_to_sync(get_courses_images) result in FAILED status."""
        course_scan = CourseScan.objects.create(course_id=self.course_id, status=CourseScanStatus.PENDING.value)
        
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_manager.canvas_api = mock_canvas_api
        
        # Make async_to_sync raise an exception
        mock_async_to_sync.side_effect = RuntimeError("Async fetch failed")
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        course_scan.refresh_from_db()
        self.assertEqual(course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_course_creation_exception(
        self, mock_factory, mock_course_class, mock_async_to_sync, mock_unpack
    ):
        """Test that Course object creation exceptions result in FAILED status."""
        course_scan = CourseScan.objects.create(course_id=self.course_id, status=CourseScanStatus.PENDING.value)
        
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_manager.canvas_api = mock_canvas_api
        
        # Make Course creation fail
        mock_course_class.side_effect = Exception("Course creation failed")
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        course_scan.refresh_from_db()
        self.assertEqual(course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_image_content_extraction_exception(
        self, mock_factory, mock_async_to_sync, mock_unpack, mock_retrieve_alt
    ):
        """Test that ImageContentExtractionException results in FAILED status."""
        course_scan = CourseScan.objects.create(course_id=self.course_id, status=CourseScanStatus.PENDING.value)
        
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_manager.canvas_api = mock_canvas_api
        
        mock_async_to_sync.return_value = MagicMock(return_value=([], [], []))
        mock_unpack.return_value = True
        
        # Make retrieve_and_store_alt_text raise ImageContentExtractionException
        mock_retrieve_alt.side_effect = ImageContentExtractionException(errors=['Alt text fetch failed'])
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        course_scan.refresh_from_db()
        self.assertEqual(course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_marks_failed_on_unexpected_exception(
        self, mock_factory, mock_async_to_sync, mock_unpack, mock_retrieve_alt
    ):
        """Test that any unexpected exception results in FAILED status."""
        course_scan = CourseScan.objects.create(course_id=self.course_id, status=CourseScanStatus.PENDING.value)
        
        # Setup successful manager
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_manager.canvas_api = mock_canvas_api
        
        mock_async_to_sync.return_value = MagicMock(return_value=([], [], []))
        mock_unpack.return_value = True
        
        # Make retrieve_and_store_alt_text raise a generic exception
        mock_retrieve_alt.side_effect = ValueError("Unexpected error occurred")
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify status is FAILED
        course_scan.refresh_from_db()
        self.assertEqual(course_scan.status, CourseScanStatus.FAILED.value)

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
        mock_manager.canvas_api = mock_canvas_api
        
        mock_async_to_sync.return_value = MagicMock(return_value=([], [], []))
        mock_unpack.return_value = True
        mock_retrieve_alt.return_value = {}
        
        # Call the function
        fetch_and_scan_course(self.task)
        
        # Verify update_course_scan was called with COMPLETED status at the end
        calls = mock_update_scan.call_args_list
        # Last call should be with COMPLETED status
        self.assertEqual(calls[-1][0], (self.course_id, CourseScanStatus.COMPLETED.value))
