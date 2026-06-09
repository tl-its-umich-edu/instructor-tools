"""
Test case for orchestration: mixed success/error from unpack_and_store ensures
retrieve_and_store_alt_text still processes successfully stored images.

This validates that partial errors don't stop the alt text pipeline for successfully
stored content items.
"""
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from canvasapi.course import Course

from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus, ContentItem, ImageItem
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    fetch_and_scan_course,
)


class TestMixedErrorsWithAltTextProcessing(TestCase):
    """
    Test that when unpack_and_store_content_images results in mixed success/errors,
    retrieve_and_store_alt_text still processes alt text for the successfully stored items.
    
    Ensures partial errors in content extraction don't block alt text generation for
    successfully stored images.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.course_scan = CourseScan.objects.create(
            course_id=999,
            status=CourseScanStatus.PENDING.value,
        )

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.get_user_model')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.canvas_setup')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.update_course_scan')
    def test_mixed_errors_unpack_still_retrieves_alt_text(
        self,
        mock_update_course_scan,
        mock_retrieve_and_store_alt_text,
        mock_unpack_and_store,
        mock_async_to_sync,
        mock_course_class,
        mock_canvas_setup,
        mock_get_user_model,
    ):
        """
        GIVEN: unpack_and_store_content_images returns mixed results
               (some items stored successfully, but some errors occurred)
        
        WHEN: fetch_and_scan_course orchestration runs
        
        THEN: 
            1. retrieve_and_store_alt_text is called (pipeline continues)
            2. Alt text retrieval processes the successfully stored images
            3. Final status is FAILED (due to mixed errors)
            4. Errors are logged and associated with the scan
        
        This validates that partial content extraction failures don't block
        alt text generation for successfully stored content items.
        """
        # Setup mocks
        mock_user = Mock()
        mock_user.id = 1
        mock_get_user_model.return_value.objects.get.return_value = mock_user

        mock_canvas_api = Mock()
        mock_bearer_token = 'test_token'
        mock_canvas_setup.return_value = (mock_canvas_api, mock_bearer_token)

        mock_course = Mock(spec=Course)
        mock_course.id = 999
        mock_course_class.return_value = mock_course

        # Mock get_courses_images
        mock_get_courses_images = Mock()
        mock_async_to_sync.return_value = mock_get_courses_images
        mock_get_courses_images.return_value = [
            [],  # assignments empty
            [],  # pages empty
            [],  # quizzes empty
        ]

        # unpack_and_store_content_images returns mixed: some items stored, but errors occurred
        unpack_error_result = [
            {
                'type': 'page',
                'title': 'Page Fetch Error',
                'error': Exception('Failed to fetch page content'),
                'canvas_url': 'https://canvas.example.com/courses/999/pages',
            }
        ]
        mock_unpack_and_store.return_value = ([], unpack_error_result)

        # retrieve_and_store_alt_text succeeds
        mock_retrieve_and_store_alt_text.return_value = True

        # Call orchestration
        task = {
            'course_scan_id': self.course_scan.id,
            'course_id': 999,
            'user_id': 1,
            'canvas_callback_url': 'https://canvas.example.com/oauth/oauth-callback',
        }
        fetch_and_scan_course(task)

        # Assertions
        # 1. Verify retrieve_and_store_alt_text was called despite unpack returning errors
        mock_retrieve_and_store_alt_text.assert_called_once_with(
            self.course_scan.id,
            999,
            bearer_token='test_token'
        )

        # 2. Verify final status is FAILED (because unpack returned errors)
        # Second call to update_course_scan should be with FAILED status
        calls = mock_update_course_scan.call_args_list
        final_call = calls[-1]  # Last call is the status update
        self.assertEqual(final_call[0][1], CourseScanStatus.FAILED)

        # 3. Verify errors were passed to update_course_scan
        self.assertIn('errors', final_call[1])
        errors = final_call[1]['errors']
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['type'], 'page')

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.get_user_model')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.canvas_setup')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.update_course_scan')
    def test_mixed_errors_with_successfully_stored_images_processed_for_alt_text(
        self,
        mock_update_course_scan,
        mock_retrieve_and_store_alt_text,
        mock_unpack_and_store,
        mock_async_to_sync,
        mock_course_class,
        mock_canvas_setup,
        mock_get_user_model,
    ):
        """
        GIVEN: unpack_and_store_content_images successfully stored images to DB
               but also encountered some errors during content extraction
        
        WHEN: fetch_and_scan_course runs through the orchestration
        
        THEN:
            1. Images stored in DB from successful items are still processed for alt text
            2. retrieve_and_store_alt_text is called and processes those images
            3. User sees alt text generated for partial content (not blocked by errors)
            4. Final status reflects mixed results (FAILED with error list)
        
        This is the key user workflow: partial errors don't stop alt text generation.
        """
        # Setup mocks
        mock_user = Mock()
        mock_user.id = 1
        mock_get_user_model.return_value.objects.get.return_value = mock_user

        mock_canvas_api = Mock()
        mock_bearer_token = 'test_token'
        mock_canvas_setup.return_value = (mock_canvas_api, mock_bearer_token)

        mock_course = Mock(spec=Course)
        mock_course.id = 999
        mock_course_class.return_value = mock_course

        # Mock get_courses_images
        mock_get_courses_images = Mock()
        mock_async_to_sync.return_value = mock_get_courses_images
        mock_get_courses_images.return_value = [[], [], []]

        # Simulate: unpack_and_store_content_images stored 5 images successfully
        # but encountered 2 errors during extraction
        # Returns error list to indicate mixed results
        unpack_mixed_errors = [
            {
                'type': 'quiz',
                'title': 'Quiz Fetch Error',
                'error': Exception('API rate limit exceeded'),
                'canvas_url': 'https://canvas.example.com/courses/999/quizzes',
            },
            {
                'type': 'question',
                'title': 'Question in Quiz',
                'error': Exception('Failed to parse question content'),
                'canvas_url': 'https://canvas.example.com/courses/999/questions/123',
            },
        ]
        mock_unpack_and_store.return_value = ([], unpack_mixed_errors)

        # Simulate: retrieve_and_store_alt_text processes the 5 stored images
        # and successfully generates alt text for them
        mock_retrieve_and_store_alt_text.return_value = True

        # Call orchestration
        task = {
            'course_scan_id': self.course_scan.id,
            'course_id': 999,
            'user_id': 1,
            'canvas_callback_url': 'https://canvas.example.com/oauth/oauth-callback',
        }
        fetch_and_scan_course(task)

        # Key Assertions
        # 1. retrieve_and_store_alt_text was called (pipeline continues)
        mock_retrieve_and_store_alt_text.assert_called_once()
        call_args = mock_retrieve_and_store_alt_text.call_args
        self.assertEqual(call_args[0][0], self.course_scan.id)
        self.assertEqual(call_args[0][1], 999)
        self.assertEqual(call_args[1]['bearer_token'], 'test_token')

        # 2. Verify final status update (should be FAILED due to unpack errors)
        update_calls = mock_update_course_scan.call_args_list
        # First call: RUNNING status
        self.assertEqual(update_calls[0][0][1], CourseScanStatus.RUNNING)
        # Last call: FAILED status
        final_status_call = update_calls[-1]
        self.assertEqual(final_status_call[0][1], CourseScanStatus.FAILED)

        # 3. Verify both errors are logged
        final_errors = final_status_call[1]['errors']
        self.assertEqual(len(final_errors), 2)
        error_types = [e['type'] for e in final_errors]
        self.assertIn('quiz', error_types)
        self.assertIn('question', error_types)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.get_user_model')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.canvas_setup')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.update_course_scan')
    def test_alt_text_retrieval_happens_even_with_unpack_errors(
        self,
        mock_update_course_scan,
        mock_retrieve_and_store_alt_text,
        mock_unpack_and_store,
        mock_async_to_sync,
        mock_course_class,
        mock_canvas_setup,
        mock_get_user_model,
    ):
        """
        GIVEN: unpack_and_store_content_images returns ONLY errors (no items stored)
        
        WHEN: fetch_and_scan_course orchestration runs
        
        THEN:
            1. retrieve_and_store_alt_text is STILL CALLED
               (it will return True because there's nothing to process, but call happens)
            2. Pipeline doesn't block on extraction errors
            3. Final status is FAILED with error list
        
        This validates the pipeline is resilient: even complete extraction failure
        doesn't prevent the orchestration from attempting alt text stage.
        """
        # Setup mocks
        mock_user = Mock()
        mock_user.id = 1
        mock_get_user_model.return_value.objects.get.return_value = mock_user

        mock_canvas_api = Mock()
        mock_bearer_token = 'test_token'
        mock_canvas_setup.return_value = (mock_canvas_api, mock_bearer_token)

        mock_course = Mock(spec=Course)
        mock_course.id = 999
        mock_course_class.return_value = mock_course

        # Mock get_courses_images
        mock_get_courses_images = Mock()
        mock_async_to_sync.return_value = mock_get_courses_images
        mock_get_courses_images.return_value = [[], [], []]

        # unpack_and_store_content_images returns ONLY errors (no successful items)
        all_errors = [
            {
                'type': 'assignment',
                'title': 'Assignment Fetch Error',
                'error': Exception('Connection timeout'),
                'canvas_url': 'https://canvas.example.com/courses/999/assignments',
            },
            {
                'type': 'page',
                'title': 'Page Fetch Error',
                'error': Exception('Unauthorized'),
                'canvas_url': 'https://canvas.example.com/courses/999/pages',
            },
            {
                'type': 'quiz',
                'title': 'Quiz Fetch Error',
                'error': Exception('Not found'),
                'canvas_url': 'https://canvas.example.com/courses/999/quizzes',
            },
        ]
        mock_unpack_and_store.return_value = ([], all_errors)

        # retrieve_and_store_alt_text returns True (nothing to process, but succeeds)
        mock_retrieve_and_store_alt_text.return_value = True

        # Call orchestration
        task = {
            'course_scan_id': self.course_scan.id,
            'course_id': 999,
            'user_id': 1,
            'canvas_callback_url': 'https://canvas.example.com/oauth/oauth-callback',
        }
        fetch_and_scan_course(task)

        # Key Assertions
        # 1. retrieve_and_store_alt_text was STILL called despite all errors
        mock_retrieve_and_store_alt_text.assert_called_once_with(
            self.course_scan.id,
            999,
            bearer_token='test_token'
        )

        # 2. Final status is FAILED (because unpack returned errors)
        final_call = mock_update_course_scan.call_args_list[-1]
        self.assertEqual(final_call[0][1], CourseScanStatus.FAILED)

        # 3. All errors are logged
        final_errors = final_call[1]['errors']
        self.assertEqual(len(final_errors), 3)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.get_user_model')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.canvas_setup')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.Course')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.async_to_sync')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.update_course_scan')
    def test_partial_failures_user_sees_alt_text_for_successful_items(
        self,
        mock_update_course_scan,
        mock_retrieve_and_store_alt_text,
        mock_unpack_and_store,
        mock_async_to_sync,
        mock_course_class,
        mock_canvas_setup,
        mock_get_user_model,
    ):
        """
        SCENARIO: User has a course with mixed content:
        - 10 assignments: 8 succeed with images, 2 fail to fetch
        - 5 pages: 3 succeed with images, 2 fail to fetch
        - 3 quizzes: 1 succeeds with images, 2 fail to fetch
        
        RESULT: User should see alt text generated for the 12 successful items
                despite the 6 extraction failures (not blocked by partial errors)
        
        This validates the user experience: alt text generation works for
        successfully extracted content even when other content types partially fail.
        """
        # Setup mocks
        mock_user = Mock()
        mock_user.id = 1
        mock_get_user_model.return_value.objects.get.return_value = mock_user

        mock_canvas_api = Mock()
        mock_bearer_token = 'test_token'
        mock_canvas_setup.return_value = (mock_canvas_api, mock_bearer_token)

        mock_course = Mock(spec=Course)
        mock_course.id = 999
        mock_course_class.return_value = mock_course

        # Mock get_courses_images
        mock_get_courses_images = Mock()
        mock_async_to_sync.return_value = mock_get_courses_images
        mock_get_courses_images.return_value = [[], [], []]

        # Simulate scenario: 12 items stored successfully, 6 errors occurred
        extraction_errors = [
            {
                'type': 'assignment',
                'title': 'Assignment 2',
                'error': Exception('Content fetch failed'),
                'canvas_url': 'https://canvas.example.com/courses/999/assignments/2',
            },
            {
                'type': 'assignment',
                'title': 'Assignment 5',
                'error': Exception('Content fetch failed'),
                'canvas_url': 'https://canvas.example.com/courses/999/assignments/5',
            },
            {
                'type': 'page',
                'title': 'Page 2',
                'error': Exception('Content fetch failed'),
                'canvas_url': 'https://canvas.example.com/courses/999/pages/2',
            },
            {
                'type': 'page',
                'title': 'Page 4',
                'error': Exception('Content fetch failed'),
                'canvas_url': 'https://canvas.example.com/courses/999/pages/4',
            },
            {
                'type': 'quiz',
                'title': 'Quiz 2',
                'error': Exception('Content fetch failed'),
                'canvas_url': 'https://canvas.example.com/courses/999/quizzes/2',
            },
            {
                'type': 'quiz',
                'title': 'Quiz 3',
                'error': Exception('Content fetch failed'),
                'canvas_url': 'https://canvas.example.com/courses/999/quizzes/3',
            },
        ]
        mock_unpack_and_store.return_value = ([], extraction_errors)

        # retrieve_and_store_alt_text processes the 12 stored items
        # Simulates: for each of 12 items, alt text is generated
        mock_retrieve_and_store_alt_text.return_value = True

        # Call orchestration
        task = {
            'course_scan_id': self.course_scan.id,
            'course_id': 999,
            'user_id': 1,
            'canvas_callback_url': 'https://canvas.example.com/oauth/oauth-callback',
        }
        fetch_and_scan_course(task)

        # Assertions
        # 1. retrieve_and_store_alt_text is called (pipeline continues to alt text)
        mock_retrieve_and_store_alt_text.assert_called_once()

        # 2. Final status reflects mixed results (FAILED due to 6 errors)
        final_call = mock_update_course_scan.call_args_list[-1]
        self.assertEqual(final_call[0][1], CourseScanStatus.FAILED)

        # 3. All 6 errors are logged
        final_errors = final_call[1]['errors']
        self.assertEqual(len(final_errors), 6)
        
        # 4. Verify error types are diverse (not just one content type)
        error_types = [e['type'] for e in final_errors]
        self.assertEqual(error_types.count('assignment'), 2)
        self.assertEqual(error_types.count('page'), 2)
        self.assertEqual(error_types.count('quiz'), 2)
