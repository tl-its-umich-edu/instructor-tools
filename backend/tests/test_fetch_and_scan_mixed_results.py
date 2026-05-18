"""
Test suite for fetch_and_scan_course with mixed error and success scenarios.

Tests the orchestration of get_assignments, get_pages, get_quizzes results
where some content types completely fail, others have mixed success/error,
and the function still processes images from successful items.
"""

from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus, CourseScanErrorLog
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    fetch_and_scan_course,
)


class TestFetchAndScanCourseWithMixedResults(TestCase):
    """
    Test fetch_and_scan_course orchestration with mixed error/success scenarios.
    
    Validates that even when some content types fail completely and others fail partially,
    the pipeline still processes images from successful items and captures all errors.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.user = get_user_model().objects.create_user(
            username='testuser', password='testpass'
        )
        self.course_id = 403334
        self.course_scan = CourseScan.objects.create(
            course_id=self.course_id,
            status=CourseScanStatus.PENDING.value,
        )

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.update_course_scan')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.get_courses_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.canvas_setup')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan._create_background_request')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    def test_fetch_and_scan_with_assignments_all_errors_pages_mixed_quizzes_empty(
        self,
        mock_course_cls,
        mock_create_bg_request,
        mock_canvas_setup,
        mock_get_courses_images,
        mock_unpack_and_store,
        mock_retrieve_alt_text,
        mock_update_course_scan,
    ):
        """
        Test mixed scenario:
        - get_assignments() returns ALL errors (3 failed assignments)
        - get_pages() returns MIXED: 1 error + 2 successful pages with images
        - get_quizzes() returns empty (no quizzes)
        
        Expected:
        - 3 total errors captured (1 assignment endpoint error + 1 page endpoint error)
        - 2 images from successful pages processed (alt text generated)
        - Final status: FAILED (with error list merged)
        """
        # Setup mock course
        mock_course = MagicMock()
        mock_course.id = self.course_id
        mock_course_cls.return_value = mock_course

        # Setup mock request
        mock_request = MagicMock()
        mock_create_bg_request.return_value = mock_request

        # Setup mock canvas API and bearer token
        mock_canvas_api = MagicMock()
        mock_bearer_token = 'test_bearer_token_12345'
        mock_canvas_setup.return_value = (mock_canvas_api, mock_bearer_token)

        # Setup get_courses_images results: assignments all fail, pages mixed, quizzes empty
        assignment_error = {
            'type': 'assignment',
            'title': 'assignments',
            'error': Exception('Assignments API endpoint failed'),
            'canvas_url': f'https://umich-dev.instructure.com/courses/{self.course_id}/assignments',
        }
        
        page_endpoint_error = {
            'type': 'page',
            'title': 'pages',
            'error': Exception('Pages API endpoint temporarily failed'),
            'canvas_url': f'https://umich-dev.instructure.com/courses/{self.course_id}/pages',
        }
        
        page_1_success = {
            'id': 101,
            'name': 'Page 1 Success',
            'type': 'page',
            'images': [
                'https://umich-dev.instructure.com/files/111/download?verifier=abc123&download_frd=1'
            ],
            'content_parent_id': None,
        }
        
        page_2_success = {
            'id': 102,
            'name': 'Page 2 Success',
            'type': 'page',
            'images': [
                'https://umich-dev.instructure.com/files/222/download?verifier=def456&download_frd=1'
            ],
            'content_parent_id': None,
        }
        
        # Simulate get_courses_images results (from asyncio.gather)
        mock_get_courses_images.return_value = [
            [assignment_error],  # All assignments failed
            [page_endpoint_error, page_1_success, page_2_success],  # Pages: 1 error + 2 successes
            [],  # Quizzes: empty (no quizzes)
        ]

        # Setup unpack_and_store_content_images to return:
        # - Saves the 2 successful pages to DB
        # - Returns list of 2 errors (assignment endpoint error + page endpoint error)
        content_errors = [assignment_error, page_endpoint_error]
        mock_unpack_and_store.return_value = content_errors

        # Setup retrieve_and_store_alt_text to return True (successful alt text generation for 2 images)
        mock_retrieve_alt_text.return_value = True

        # Call the function
        task = {
            'course_scan_id': self.course_scan.id,
            'course_id': self.course_id,
            'user_id': self.user.id,
            'canvas_callback_url': 'http://localhost/callback',
        }
        fetch_and_scan_course(task)

        # Verify canvas_setup was called
        mock_canvas_setup.assert_called_once()

        # Verify get_courses_images was called
        mock_get_courses_images.assert_called_once_with(mock_course)

        # Verify unpack_and_store_content_images was called with the mixed results
        mock_unpack_and_store.assert_called_once()
        call_args = mock_unpack_and_store.call_args
        results_arg = call_args[0][0]  # First argument to unpack_and_store
        # Verify results structure: [assignments, pages, quizzes]
        self.assertEqual(len(results_arg), 3)
        self.assertEqual(len(results_arg[0]), 1)  # 1 assignment error
        self.assertEqual(len(results_arg[1]), 3)  # 1 page error + 2 successes
        self.assertEqual(len(results_arg[2]), 0)  # Empty quizzes

        # Verify retrieve_and_store_alt_text was called (since there were 2 successful pages saved)
        mock_retrieve_alt_text.assert_called_once_with(
            self.course_scan.id,
            self.course_id,
            bearer_token=mock_bearer_token,
        )

        # Verify update_course_scan was called with FAILED status and merged errors
        update_calls = mock_update_course_scan.call_args_list
        
        # First call: RUNNING status at start
        self.assertEqual(update_calls[0][0][1].value, 'running')
        
        # Final call: FAILED status with merged errors
        final_call = update_calls[-1]
        final_status = final_call[0][1]
        final_errors = final_call[1].get('errors', [])
        
        self.assertEqual(final_status.value, 'failed')
        # Should have merged 2 errors from content_fetch_result (assignment + page endpoint)
        self.assertEqual(len(final_errors), 2)
        self.assertEqual(final_errors[0]['type'], 'assignment')
        self.assertEqual(final_errors[1]['type'], 'page')

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.update_course_scan')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.get_courses_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.canvas_setup')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan._create_background_request')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    def test_fetch_and_scan_proceeds_with_alt_text_despite_content_fetch_errors(
        self,
        mock_course_cls,
        mock_create_bg_request,
        mock_canvas_setup,
        mock_get_courses_images,
        mock_unpack_and_store,
        mock_retrieve_alt_text,
        mock_update_course_scan,
    ):
        """
        Test that even when content_fetch_result contains errors,
        the pipeline still proceeds to retrieve_and_store_alt_text
        if there were successful content items saved to DB.
        
        This validates lines 72-74 behavior:
        - content_fetch_result returns errors (not True)
        - image_process_result returns True (successful alt text generation)
        - Merged errors are captured and logged
        """
        # Setup mock course
        mock_course = MagicMock()
        mock_course.id = self.course_id
        mock_course_cls.return_value = mock_course

        # Setup mock request
        mock_request = MagicMock()
        mock_create_bg_request.return_value = mock_request

        # Setup mock canvas API
        mock_canvas_api = MagicMock()
        mock_bearer_token = 'test_bearer_token'
        mock_canvas_setup.return_value = (mock_canvas_api, mock_bearer_token)

        # Simulate partial success from get_courses_images
        assignment_error = {
            'type': 'assignment',
            'title': 'assignments',
            'error': Exception('All assignments failed'),
            'canvas_url': f'https://umich-dev.instructure.com/courses/{self.course_id}/assignments',
        }
        
        page_success = {
            'id': 201,
            'name': 'Page with Images',
            'type': 'page',
            'images': [
                'https://umich-dev.instructure.com/files/333/download?verifier=xyz789&download_frd=1',
                'https://umich-dev.instructure.com/files/444/download?verifier=uvw012&download_frd=1',
            ],
            'content_parent_id': None,
        }
        
        mock_get_courses_images.return_value = [
            [assignment_error],  # All assignments failed
            [page_success],  # 1 page with 2 images
            [],  # No quizzes
        ]

        # unpack_and_store_content_images returns only the assignment error
        # (page was successfully saved to DB)
        mock_unpack_and_store.return_value = [assignment_error]

        # retrieve_and_store_alt_text successfully processes the 2 images
        mock_retrieve_alt_text.return_value = True

        # Call the function
        task = {
            'course_scan_id': self.course_scan.id,
            'course_id': self.course_id,
            'user_id': self.user.id,
            'canvas_callback_url': 'http://localhost/callback',
        }
        fetch_and_scan_course(task)

        # Verify retrieve_and_store_alt_text WAS called
        # (This proves the pipeline proceeds to alt text processing despite content_fetch errors)
        mock_retrieve_alt_text.assert_called_once()

        # Verify final status is FAILED with merged errors
        update_calls = mock_update_course_scan.call_args_list
        final_call = update_calls[-1]
        final_status = final_call[0][1]
        final_errors = final_call[1].get('errors', [])

        self.assertEqual(final_status.value, 'failed')
        # Error list should be: 1 from content_fetch (assignment error)
        # (Since image_process_result is True, no errors from that stage)
        self.assertEqual(len(final_errors), 1)
        self.assertEqual(final_errors[0]['type'], 'assignment')
