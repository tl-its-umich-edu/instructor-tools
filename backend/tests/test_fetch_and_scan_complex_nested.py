"""
Test suite for fetch_and_scan_course with complex nested error scenarios.

Tests a realistic scenario with:
- All assignments succeeding (2 assignments, 2 images)
- Pages with mixed results (1 error, 2 successful, 2 images)
- Quizzes with mixed results:
  - Quiz 1: succeeds with 3 questions (1 image + 2 questions with URL parse error + 2 images)
  - Quiz 2: endpoint fails (1 error)
Total: 3 errors captured, 7 images processed for alt text
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    fetch_and_scan_course,
)


class TestFetchAndScanCourseComplexNestedScenario(TestCase):
    """
    Test fetch_and_scan_course with complex nested errors and successes.
    
    Scenario:
    - Assignments: 2 successful (all pass)
    - Pages: 1 error + 2 successful (mixed)
    - Quiz 1: 1 success with 3 questions (1 URL parse error + 2 successful)
    - Quiz 2: 1 endpoint failure
    
    Total errors: 3 (1 page endpoint + 1 quiz endpoint + 1 question URL parse)
    Total images for alt text: 7 (2 assignment + 2 page + 1 quiz + 2 questions)
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
    def test_complex_scenario_mixed_results_across_all_content_types(
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
        Test comprehensive mixed scenario with nested errors and successes.
        
        Assignments (ALL PASS):
        - Assignment 1: 1 image
        - Assignment 2: 1 image
        
        Pages (MIXED - 1 error + 2 success):
        - Pages endpoint error: 1
        - Page 1: 1 image
        - Page 2: 1 image
        
        Quizzes (MIXED):
        - Quiz 1 (SUCCESS): 1 image + 3 questions
          - Question 1: 1 image (success)
          - Question 2: 1 image (success)
          - Question 3: URL parse error (from _parse_canvas_file_src)
        - Quiz 2 (FAIL): endpoint error
        
        Expected:
        - 3 total errors: page endpoint, quiz 2 endpoint, question 3 URL parse
        - 7 images for alt text: 2 assignment + 2 page + 1 quiz + 2 questions
        - Pipeline proceeds to alt text (since 7 items have images)
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
        mock_bearer_token = 'test_bearer_token_complex'
        mock_canvas_setup.return_value = (mock_canvas_api, mock_bearer_token)

        # ============ ASSIGNMENTS (ALL PASS - 2 assignments) ============
        assignment_1 = {
            'id': 1001,
            'name': 'Assignment 1',
            'type': 'assignment',
            'images': ['https://umich-dev.instructure.com/files/111/download?verifier=a1&download_frd=1'],
            'content_parent_id': None,
        }
        assignment_2 = {
            'id': 1002,
            'name': 'Assignment 2',
            'type': 'assignment',
            'images': ['https://umich-dev.instructure.com/files/112/download?verifier=a2&download_frd=1'],
            'content_parent_id': None,
        }

        # ============ PAGES (MIXED - 1 error + 2 success) ============
        page_error = {
            'type': 'page',
            'title': 'pages',
            'error': Exception('Pages API endpoint temporarily unavailable'),
            'canvas_url': f'https://umich-dev.instructure.com/courses/{self.course_id}/pages',
        }
        page_1 = {
            'id': 2001,
            'name': 'Page 1',
            'type': 'page',
            'images': ['https://umich-dev.instructure.com/files/221/download?verifier=p1&download_frd=1'],
            'content_parent_id': None,
        }
        page_2 = {
            'id': 2002,
            'name': 'Page 2',
            'type': 'page',
            'images': ['https://umich-dev.instructure.com/files/222/download?verifier=p2&download_frd=1'],
            'content_parent_id': None,
        }

        # ============ QUIZZES (MIXED) ============
        # Quiz 1: SUCCESS with 3 questions (1 success + 1 success + 1 URL parse error)
        quiz_1_desc = {
            'id': 3001,
            'name': 'Quiz 1',
            'type': 'quiz',
            'images': ['https://umich-dev.instructure.com/files/331/download?verifier=q1&download_frd=1'],
            'content_parent_id': None,
        }

        # Quiz 1 Questions
        # Question 1: Success
        question_1 = {
            'id': 4001,
            'name': 'Question 1',
            'type': 'quiz_question',
            'images': ['https://umich-dev.instructure.com/files/441/download?verifier=q1q1&download_frd=1'],
            'content_parent_id': 3001,
        }

        # Question 2: Success
        question_2 = {
            'id': 4002,
            'name': 'Question 2',
            'type': 'quiz_question',
            'images': ['https://umich-dev.instructure.com/files/442/download?verifier=q1q2&download_frd=1'],
            'content_parent_id': 3001,
        }

        # Question 3: URL parse error (from _parse_canvas_file_src)
        question_3_error = {
            'type': 'quiz_question',
            'title': 'Quiz 1',
            'error': ValueError('File ID not found in URL path'),
            'canvas_url': f'https://umich-dev.instructure.com/courses/{self.course_id}/quizzes/3001/questions/4003',
        }

        # Quiz 2: Endpoint FAILURE
        quiz_2_error = {
            'type': 'quiz',
            'title': 'quizzes',
            'error': Exception('Quiz 2 API endpoint failed'),
            'canvas_url': f'https://umich-dev.instructure.com/courses/{self.course_id}/quizzes',
        }

        # Setup get_courses_images to return structured results:
        # [assignments, pages, quizzes]
        mock_get_courses_images.return_value = [
            [assignment_1, assignment_2],  # 2 successful assignments
            [page_error, page_1, page_2],  # 1 error + 2 successful pages
            [
                quiz_1_desc,
                [question_1, question_2, question_3_error],  # Quiz 1 with 3 questions (2 success, 1 error)
                quiz_2_error,  # Quiz 2 error
            ],
        ]

        # Setup unpack_and_store_content_images:
        # Returns 7 successful items and 3 errors (page endpoint + quiz 2 + question 3 URL parse)
        content_errors = [page_error, quiz_2_error, question_3_error]
        success_items = [assignment_1, assignment_2, page_1, page_2, quiz_1_desc, question_1, question_2]
        mock_unpack_and_store.return_value = (success_items, content_errors)

        # Setup retrieve_and_store_alt_text to succeed
        # (Processes 7 images: 2 assignment + 2 page + 1 quiz + 2 questions)
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
        mock_get_courses_images.assert_called_once()

        # Verify unpack_and_store_content_images was called
        mock_unpack_and_store.assert_called_once()
        call_args = mock_unpack_and_store.call_args
        results_arg = call_args[0][0]
        
        # Verify results structure
        self.assertEqual(len(results_arg), 3)  # [assignments, pages, quizzes]
        self.assertEqual(len(results_arg[0]), 2)  # 2 assignments
        self.assertEqual(len(results_arg[1]), 3)  # 1 page error + 2 successful pages
        # Quizzes have complex structure: quiz_1_desc, questions list, quiz_2_error
        self.assertEqual(len(results_arg[2]), 3)

        # Verify retrieve_and_store_alt_text WAS called
        # (This proves pipeline proceeded despite 3 errors, because 7 items were saved)
        mock_retrieve_alt_text.assert_called_once_with(
            self.course_scan.id,
            self.course_id,
            bearer_token=mock_bearer_token,
        )

        # Verify final status is FAILED with merged 3 errors
        update_calls = mock_update_course_scan.call_args_list
        
        # First call: RUNNING status at start
        self.assertEqual(update_calls[0][0][1].value, 'running')
        
        # Final call: FAILED status with 3 merged errors
        final_call = update_calls[-1]
        final_status = final_call[0][1]
        final_errors = final_call[1].get('errors', [])
        
        self.assertEqual(final_status.value, 'failed')
        # Should have 3 errors: page endpoint + quiz 2 + question 3 URL parse
        self.assertEqual(len(final_errors), 3)
        
        # Verify error types
        error_types = [e['type'] for e in final_errors]
        self.assertIn('page', error_types)
        self.assertIn('quiz', error_types)
        self.assertIn('quiz_question', error_types)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.update_course_scan')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.get_courses_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.canvas_setup')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan._create_background_request')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    def test_url_parse_error_captured_and_wrapped_in_error_dict(
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
        Test that URL parse errors from _parse_canvas_file_src are properly captured
        and wrapped in CourseScanError dict format with all required fields.
        
        This validates the error handling in extract_images_from_html when
        _parse_canvas_file_src raises an exception.
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

        # Create scenario with URL parse errors from question processing
        question_with_parse_error = {
            'type': 'quiz_question',
            'title': 'Question with Parse Error',
            'error': ValueError('File ID not found in URL path: invalid_url'),
            'canvas_url': f'https://umich-dev.instructure.com/courses/{self.course_id}/quizzes/999/questions/888',
        }

        mock_get_courses_images.return_value = [[], [], [question_with_parse_error]]
        mock_unpack_and_store.return_value = ([], [question_with_parse_error])
        mock_retrieve_alt_text.return_value = True

        # Call the function
        task = {
            'course_scan_id': self.course_scan.id,
            'course_id': self.course_id,
            'user_id': self.user.id,
            'canvas_callback_url': 'http://localhost/callback',
        }
        fetch_and_scan_course(task)

        # Verify error is captured with all CourseScanError fields
        update_calls = mock_update_course_scan.call_args_list
        final_call = update_calls[-1]
        final_errors = final_call[1].get('errors', [])

        self.assertEqual(len(final_errors), 1)
        error = final_errors[0]

        # Verify all CourseScanError fields are present
        self.assertEqual(error['type'], 'quiz_question')
        self.assertEqual(error['title'], 'Question with Parse Error')
        self.assertIsInstance(error['error'], ValueError)
        self.assertIn('File ID not found', str(error['error']))
        self.assertIn(f'/courses/{self.course_id}/quizzes/999/questions/888', error['canvas_url'])
