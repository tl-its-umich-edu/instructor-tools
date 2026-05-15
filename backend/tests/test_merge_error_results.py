"""
Test cases for canvas_tools_alt_text_scan error merging functionality.
"""
import unittest
from typing import List, Union

from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    _merge_error_results,
)
from backend.canvas_app_explorer.alt_text_helper.background_tasks.types import CourseScanError


class TestMergeErrorResults(unittest.TestCase):
    """Test suite for _merge_error_results function."""

    def test_merge_two_error_lists(self):
        """Test merging two lists of errors."""
        error1: CourseScanError = {
            'type': 'assignment',
            'title': 'Assignments',
            'error': Exception('Assignment fetch failed'),
            'canvas_url': 'https://canvas.example.com/courses/1/assignments',
        }
        error2: CourseScanError = {
            'type': 'page',
            'title': 'Pages',
            'error': Exception('Page fetch failed'),
            'canvas_url': 'https://canvas.example.com/courses/1/pages',
        }
        
        result = _merge_error_results([error1], [error2])
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['type'], 'assignment')
        self.assertEqual(result[1]['type'], 'page')

    def test_merge_list_and_single_error(self):
        """Test merging a list of errors with a single error dict."""
        error1: CourseScanError = {
            'type': 'assignment',
            'title': 'Assignments',
            'error': Exception('Assignment fetch failed'),
            'canvas_url': 'https://canvas.example.com/courses/1/assignments',
        }
        error2: CourseScanError = {
            'type': 'content_database_save',
            'title': 'Database',
            'error': Exception('Save failed'),
            'canvas_url': 'https://canvas.example.com/courses/1',
        }
        
        result = _merge_error_results([error1], error2)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['type'], 'assignment')
        self.assertEqual(result[1]['type'], 'content_database_save')

    def test_merge_all_true_values(self):
        """Test merging when all results are True (success)."""
        result = _merge_error_results(True, True, True)
        
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_merge_mixed_true_and_errors(self):
        """Test merging mix of True values and errors."""
        error: CourseScanError = {
            'type': 'quiz',
            'title': 'Quizzes',
            'error': Exception('Quiz fetch failed'),
            'canvas_url': 'https://canvas.example.com/courses/1/quizzes',
        }
        
        result = _merge_error_results(True, [error], True)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'quiz')

    def test_merge_single_error_dict(self):
        """Test merging single error dict (not in a list)."""
        error: CourseScanError = {
            'type': 'course_scan_update_error',
            'title': 'CourseScan Update',
            'error': Exception('Update failed'),
            'canvas_url': 'https://canvas.example.com/courses/1',
        }
        
        result = _merge_error_results(error)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'course_scan_update_error')

    def test_merge_multiple_error_lists(self):
        """Test merging multiple lists of errors."""
        error1: CourseScanError = {
            'type': 'assignment',
            'title': 'Assignments',
            'error': Exception('Error 1'),
            'canvas_url': 'url1',
        }
        error2: CourseScanError = {
            'type': 'page',
            'title': 'Pages',
            'error': Exception('Error 2'),
            'canvas_url': 'url2',
        }
        error3: CourseScanError = {
            'type': 'quiz',
            'title': 'Quizzes',
            'error': Exception('Error 3'),
            'canvas_url': 'url3',
        }
        
        result = _merge_error_results([error1, error2], [error3])
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['type'], 'assignment')
        self.assertEqual(result[1]['type'], 'page')
        self.assertEqual(result[2]['type'], 'quiz')

    def test_merge_empty_list_with_error(self):
        """Test merging empty list with an error."""
        error: CourseScanError = {
            'type': 'unexpected_error',
            'title': 'Unexpected',
            'error': Exception('Unexpected error'),
            'canvas_url': 'https://canvas.example.com/courses/1',
        }
        
        result = _merge_error_results([], error)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'unexpected_error')

    def test_merge_preserves_error_details(self):
        """Test that error details are preserved during merge."""
        error_msg = 'Specific error message'
        error: CourseScanError = {
            'type': 'assignment',
            'title': 'Assignments',
            'error': Exception(error_msg),
            'canvas_url': 'https://canvas.example.com/courses/1/assignments',
        }
        
        result = _merge_error_results([error])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0]['error']), error_msg)
        self.assertEqual(result[0]['canvas_url'], 'https://canvas.example.com/courses/1/assignments')

    def test_merge_with_no_arguments(self):
        """Test merge with no arguments."""
        result = _merge_error_results()
        
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_merge_returns_list(self):
        """Test that merge always returns a list."""
        error: CourseScanError = {
            'type': 'test',
            'title': 'Test',
            'error': Exception('Test error'),
            'canvas_url': 'url',
        }
        
        result1 = _merge_error_results(True)
        result2 = _merge_error_results(error)
        result3 = _merge_error_results([error])
        
        self.assertIsInstance(result1, list)
        self.assertIsInstance(result2, list)
        self.assertIsInstance(result3, list)


if __name__ == '__main__':
    unittest.main()
