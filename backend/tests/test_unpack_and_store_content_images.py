"""
Comprehensive test suite for unpack_and_store_content_images function.

Tests the orchestration of content extraction results, filtering, persistence,
and return value logic for the alt-text background task pipeline.
"""
from unittest.mock import Mock, patch, MagicMock, call
from django.test import TestCase
from canvasapi.course import Course

from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus, CourseScanErrorLog
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    unpack_and_store_content_images,
)


class TestUnpackAndStoreContentImagesHappyPath(TestCase):
    """Tests for successful unpack and store operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.course = Mock(spec=Course)
        self.course.id = 999
        self.course_scan = CourseScan.objects.create(
            course_id=999,
            status=CourseScanStatus.RUNNING.value,
        )

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_happy_path_all_success_returns_true(self, mock_save):
        """
        All content items have valid images (no errors).
        Expected: Returns True.
        """
        mock_save.return_value = True

        results = [
            # Assignments with images
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': ['url1.png', 'url2.jpg'],
                },
            ],
            # Pages with images
            [
                {
                    'id': 2,
                    'type': 'page',
                    'title': 'Page 1',
                    'images': ['url3.gif'],
                },
            ],
            # Quizzes with images
            [
                {
                    'id': 3,
                    'type': 'quiz',
                    'title': 'Quiz 1',
                    'images': ['url4.png', 'url5.png'],
                },
            ],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertTrue(result, "Expected True for all success items")
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 3, "Expected 3 items saved")

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_mixed_success_and_item_level_errors(self, mock_save):
        """
        Some items succeed, some are complete fetch failures (CourseScanError dicts).
        Expected: Returns list of errors, saves only successful items.
        """
        mock_save.return_value = True

        results = [
            # Assignment success
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': ['url1.png'],
                },
                # Assignment fetch failure (CourseScanError)
                {
                    'type': 'assignment',
                    'title': 'Assignment 2',
                    'error': 'API error',
                    'canvas_url': 'https://canvas.example.com/courses/999/assignments',
                },
            ],
            # Pages all success
            [
                {
                    'id': 2,
                    'type': 'page',
                    'title': 'Page 1',
                    'images': ['url2.png'],
                },
            ],
            # Quizzes empty
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertIsInstance(result, list, "Expected list of errors")
        self.assertEqual(len(result), 1, "Expected 1 error")
        self.assertEqual(result[0]['type'], 'assignment')
        self.assertEqual(result[0]['error'], 'API error')

        # Verify only successful items saved
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 2, "Expected 2 successful items saved")

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_nested_errors_in_images_filtered_and_logged(self, mock_save):
        """
        Content item has images list with both URLs and CourseScanError dicts (nested errors).
        Expected: Item with nested errors is excluded, errors are logged, pipeline continues.
        """
        mock_save.return_value = True

        results = [
            # Assignment with mixed images and errors
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': [
                        'url1.png',
                        {
                            'type': 'question',
                            'title': 'Question in assignment',
                            'error': 'Failed to fetch question',
                            'canvas_url': 'https://canvas.example.com/courses/999/questions/1',
                        },
                    ],
                },
                # Assignment with all valid images
                {
                    'id': 2,
                    'type': 'assignment',
                    'title': 'Assignment 2',
                    'images': ['url2.png'],
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertIsInstance(result, list, "Expected list of errors")
        self.assertEqual(len(result), 1, "Expected 1 nested error")
        self.assertEqual(result[0]['type'], 'question')
        self.assertEqual(result[0]['error'], 'Failed to fetch question')

        # Verify only the clean assignment was saved
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 1, "Expected 1 clean item saved")
        self.assertEqual(saved_items[0]['id'], 2)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_items_without_images_filtered_out(self, mock_save):
        """
        Some items have no images, some have images.
        Expected: Only items with images are saved.
        """
        mock_save.return_value = True

        results = [
            # Assignment with images
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': ['url1.png'],
                },
                # Assignment without images
                {
                    'id': 2,
                    'type': 'assignment',
                    'title': 'Assignment 2',
                    'images': [],
                },
                # Assignment with no images key
                {
                    'id': 3,
                    'type': 'assignment',
                    'title': 'Assignment 3',
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertTrue(result, "Expected True for successful save")
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 1, "Expected only 1 item with images saved")
        self.assertEqual(saved_items[0]['id'], 1)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_database_save_failure_returns_error_wrapped_in_list(self, mock_save):
        """
        Database save returns an error dict (system-level failure).
        Expected: Returns the error wrapped in a list, no True return.
        """
        db_error = {
            'type': 'system_error',
            'title': 'Database Error',
            'error': 'Connection failed',
            'canvas_url': 'https://canvas.example.com/courses/999',
        }
        mock_save.return_value = db_error

        results = [
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': ['url1.png'],
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertIsInstance(result, list, "Expected list for DB error")
        self.assertEqual(len(result), 1, "Expected single error in list")
        self.assertEqual(result[0]['type'], 'system_error')
        self.assertEqual(result[0]['error'], 'Connection failed')

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_all_items_are_errors_returns_error_list(self, mock_save):
        """
        All items in results are CourseScanError dicts (no successful content).
        Expected: Returns error list, save still called with empty list.
        """
        mock_save.return_value = True

        results = [
            # All assignment failures
            [
                {
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'error': 'API error 1',
                    'canvas_url': 'https://canvas.example.com/courses/999/assignments/1',
                },
                {
                    'type': 'assignment',
                    'title': 'Assignment 2',
                    'error': 'API error 2',
                    'canvas_url': 'https://canvas.example.com/courses/999/assignments/2',
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertIsInstance(result, list, "Expected list of errors")
        self.assertEqual(len(result), 2, "Expected 2 errors")
        
        # Verify save was still called (with empty list)
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 0, "Expected empty save list")

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_empty_results_returns_true(self, mock_save):
        """
        Empty results (no assignments, pages, or quizzes).
        Expected: Returns True, save called with empty list.
        """
        mock_save.return_value = True

        results = [[], [], []]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertTrue(result, "Expected True for empty results")
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 0, "Expected empty list saved")

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_invalid_item_types_skipped(self, mock_save):
        """
        Results contain non-dict items (e.g., None, strings, lists).
        Expected: Skipped gracefully, no errors raised.
        """
        mock_save.return_value = True

        results = [
            # Mixed valid and invalid items
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': ['url1.png'],
                },
                None,  # Invalid
                "not a dict",  # Invalid
                123,  # Invalid
                {
                    'id': 2,
                    'type': 'assignment',
                    'title': 'Assignment 2',
                    'images': ['url2.png'],
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertTrue(result, "Expected True")
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 2, "Expected only 2 valid dicts saved")


class TestUnpackAndStoreContentImagesErrorHandling(TestCase):
    """Tests for error handling and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.course = Mock(spec=Course)
        self.course.id = 999
        self.course_scan = CourseScan.objects.create(
            course_id=999,
            status=CourseScanStatus.RUNNING.value,
        )

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_error_dict_structure_validation(self, mock_save):
        """
        Verify error dicts are properly structured with all required fields.
        Expected: All errors have type, title, error, canvas_url keys.
        """
        mock_save.return_value = True

        results = [
            [
                {
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'error': 'Test error message',
                    'canvas_url': 'https://canvas.example.com/courses/999/assignments/1',
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertIsInstance(result, list)
        error = result[0]
        self.assertIn('type', error)
        self.assertIn('title', error)
        self.assertIn('error', error)
        self.assertIn('canvas_url', error)
        self.assertEqual(error['type'], 'assignment')
        self.assertEqual(error['title'], 'Assignment 1')
        self.assertEqual(error['error'], 'Test error message')

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_missing_canvas_url_uses_default(self, mock_save):
        """
        Error dict missing canvas_url field.
        Expected: Default canvas_url generated from course_id.
        """
        mock_save.return_value = True

        results = [
            [
                {
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'error': 'Test error',
                    # canvas_url intentionally omitted
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertIsInstance(result, list)
        error = result[0]
        self.assertIsNotNone(error['canvas_url'])
        self.assertIn('999', str(error['canvas_url']))

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_multiple_errors_all_returned(self, mock_save):
        """
        Multiple errors from different content types.
        Expected: All errors collected and returned in order.
        """
        mock_save.return_value = True

        results = [
            # Assignment error
            [
                {
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'error': 'Assignment error',
                    'canvas_url': 'https://canvas.example.com/courses/999/assignments',
                },
            ],
            # Page error
            [
                {
                    'type': 'page',
                    'title': 'Page 1',
                    'error': 'Page error',
                    'canvas_url': 'https://canvas.example.com/courses/999/pages',
                },
            ],
            # Quiz error + nested question error
            [
                {
                    'type': 'quiz',
                    'title': 'Quiz 1',
                    'error': 'Quiz error',
                    'canvas_url': 'https://canvas.example.com/courses/999/quizzes',
                },
                {
                    'id': 1,
                    'type': 'quiz',
                    'title': 'Quiz 2',
                    'images': [
                        'url1.png',
                        {
                            'type': 'question',
                            'title': 'Question 1',
                            'error': 'Question error',
                            'canvas_url': 'https://canvas.example.com/courses/999/questions',
                        },
                    ],
                },
            ],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4, "Expected 4 errors total (assignment, page, quiz, question)")
        error_types = [e['type'] for e in result]
        self.assertIn('assignment', error_types)
        self.assertIn('page', error_types)
        self.assertIn('quiz', error_types)
        self.assertIn('question', error_types)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_images_with_non_string_values_excluded(self, mock_save):
        """
        Item has images list but some are not strings (e.g., dicts, None).
        Expected: Item is excluded from save.
        """
        mock_save.return_value = True

        results = [
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': [
                        'url1.png',
                        None,  # Invalid
                    ],
                },
                {
                    'id': 2,
                    'type': 'assignment',
                    'title': 'Assignment 2',
                    'images': ['url2.png'],
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertTrue(result, "Expected True")
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 1, "Expected only item with all-string images")
        self.assertEqual(saved_items[0]['id'], 2)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_success_with_extraction_errors_continues_pipeline(self, mock_save):
        """
        Some items saved successfully, but extraction errors also exist.
        Expected: Returns error list (stops alt-text pipeline), but saves successful items first.
        """
        mock_save.return_value = True

        results = [
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': ['url1.png'],
                },
                {
                    'type': 'assignment',
                    'title': 'Assignment 2',
                    'error': 'Fetch failed',
                    'canvas_url': 'https://canvas.example.com/courses/999',
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        # Returns error list (so pipeline knows to stop)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        # But successful item was still saved
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 1, "Expected successful item saved")


class TestUnpackAndStoreContentImagesIntegration(TestCase):
    """Integration tests with actual database operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.course = Mock(spec=Course)
        self.course.id = 999
        self.course_scan = CourseScan.objects.create(
            course_id=999,
            status=CourseScanStatus.RUNNING.value,
        )

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_logging_context_includes_course_info(self, mock_save):
        """
        Verify logging includes course_scan_id and course_id.
        Expected: Logging called with proper context (verified via mock call).
        """
        mock_save.return_value = True

        results = [
            [
                {
                    'id': 1,
                    'type': 'assignment',
                    'title': 'Assignment 1',
                    'images': ['url1.png'],
                },
            ],
            [],
            [],
        ]

        result = unpack_and_store_content_images(results, self.course, self.course_scan.id, 999)

        self.assertTrue(result)
        # save_scan_results should be called with correct course_scan_id and course_id
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        self.assertEqual(call_args[0], self.course_scan.id, "course_scan_id mismatch")
        self.assertEqual(call_args[1], 999, "course_id mismatch")

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.save_scan_results')
    def test_large_number_of_items_all_processed(self, mock_save):
        """
        Test with large number of items to verify no limits on processing.
        Expected: All items processed correctly.
        """
        mock_save.return_value = True

        # Create 100 items spread across content types
        large_results = [
            # 50 assignments
            [
                {
                    'id': i,
                    'type': 'assignment',
                    'title': f'Assignment {i}',
                    'images': [f'url{i}.png'],
                }
                for i in range(50)
            ],
            # 30 pages
            [
                {
                    'id': 50 + i,
                    'type': 'page',
                    'title': f'Page {i}',
                    'images': [f'url{50 + i}.png'],
                }
                for i in range(30)
            ],
            # 20 quizzes
            [
                {
                    'id': 80 + i,
                    'type': 'quiz',
                    'title': f'Quiz {i}',
                    'images': [f'url{80 + i}.png'],
                }
                for i in range(20)
            ],
        ]

        result = unpack_and_store_content_images(large_results, self.course, self.course_scan.id, 999)

        self.assertTrue(result)
        mock_save.assert_called_once()
        saved_items = mock_save.call_args[0][2]
        self.assertEqual(len(saved_items), 100, "Expected all 100 items saved")
