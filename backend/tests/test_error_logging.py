"""Tests for error logging functionality with retry logic."""
import logging
from unittest.mock import patch, MagicMock, call
from django.test import TestCase
from django.db.utils import DatabaseError

from backend.canvas_app_explorer.models import CourseScanErrorLog, CourseScan
from backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging import (
    log_course_scan_errors,
    _log_errors_to_console,
    ERROR_LOG_MAX_RETRY_ATTEMPTS,
    ERROR_LOG_RETRY_BACKOFF_BASE,
)


class LogCourseScanErrorsTestCase(TestCase):
    """Test cases for log_course_scan_errors function."""

    def setUp(self):
        """Set up test fixtures."""
        self.course_scan = CourseScan.objects.create(
            course_id=12345,
            status='running',
        )
        self.errors = [
            {
                'type': 'assignment',
                'title': 'Assignment 1',
                'error': ValueError('Test error'),
                'canvas_url': 'https://canvas.example.com/courses/12345/assignments/1',
            },
            {
                'type': 'page',
                'title': 'Page 1',
                'error': RuntimeError('Another test error'),
                'canvas_url': 'https://canvas.example.com/courses/12345/pages/test',
            },
        ]

    def test_log_course_scan_errors_success(self):
        """Test successful error logging to database."""
        log_course_scan_errors(self.course_scan.id, self.errors)
        
        # Verify errors were persisted
        logged_errors = CourseScanErrorLog.objects.filter(
            course_scan_id=self.course_scan.id
        )
        self.assertEqual(logged_errors.count(), 2)
        
        # Check error types (order independent)
        error_types = set(logged_errors.values_list('error_type', flat=True))
        self.assertEqual(error_types, {'assignment', 'page'})

    def test_log_course_scan_errors_empty_list(self):
        """Test that empty error list returns early."""
        with patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.CourseScanErrorLog.objects.bulk_create') as mock_bulk_create:
            log_course_scan_errors(self.course_scan.id, [])
            mock_bulk_create.assert_not_called()

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging._log_errors_to_console')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.time.sleep')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.CourseScanErrorLog.objects.bulk_create')
    def test_log_course_scan_errors_retry_on_database_error(self, mock_bulk_create, mock_sleep, mock_console):
        """Test retry logic when database error occurs."""
        # Simulate database error on first two attempts, success on third
        mock_bulk_create.side_effect = [
            DatabaseError('Connection failed'),
            DatabaseError('Connection timeout'),
            None,  # Success
        ]
        
        with patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.logger') as mock_logger:
            log_course_scan_errors(self.course_scan.id, self.errors)
            
            # Verify retries occurred
            self.assertEqual(mock_bulk_create.call_count, 3)
            # Verify sleep was called with exponential backoff (base^0=1s, base^1=2s)
            expected_backoffs = [ERROR_LOG_RETRY_BACKOFF_BASE ** i for i in range(ERROR_LOG_MAX_RETRY_ATTEMPTS - 1)]
            mock_sleep.assert_has_calls([call(backoff) for backoff in expected_backoffs])
            # Verify warning logs for retries
            warning_calls = [c for c in mock_logger.warning.call_args_list]
            self.assertEqual(len(warning_calls), 2)
            # Verify console fallback NOT called (succeeded on final attempt)
            mock_console.assert_not_called()

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging._log_errors_to_console')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.time.sleep')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.CourseScanErrorLog.objects.bulk_create')
    def test_log_course_scan_errors_fallback_on_persistent_database_error(
        self, mock_bulk_create, mock_sleep, mock_console
    ):
        """Test fallback to console logging when all retries fail."""
        # Always raise database error
        mock_bulk_create.side_effect = DatabaseError('Persistent connection failure')
        
        with patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.logger') as mock_logger:
            log_course_scan_errors(self.course_scan.id, self.errors)
            
            # Verify all retries were attempted
            self.assertEqual(mock_bulk_create.call_count, ERROR_LOG_MAX_RETRY_ATTEMPTS)
            # Verify sleep was called (max_retries - 1) times with exponential backoff
            expected_sleep_count = ERROR_LOG_MAX_RETRY_ATTEMPTS - 1
            self.assertEqual(mock_sleep.call_count, expected_sleep_count)
            # Verify final error log with CRITICAL
            final_error_call = [c for c in mock_logger.error.call_args_list if 'CRITICAL' in str(c)]
            self.assertTrue(len(final_error_call) > 0)
            # Verify console fallback WAS called
            mock_console.assert_called_once_with(self.course_scan.id, self.errors)

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging._log_errors_to_console')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.CourseScanErrorLog.objects.bulk_create')
    def test_log_course_scan_errors_unexpected_error_no_retry(
        self, mock_bulk_create, mock_console
    ):
        """Test that unexpected errors don't trigger retries."""
        # Raise unexpected error (not DatabaseError)
        mock_bulk_create.side_effect = ValueError('Unexpected programming error')
        
        with patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.logger') as mock_logger:
            log_course_scan_errors(self.course_scan.id, self.errors)
            
            # Verify only one attempt (no retries for unexpected errors)
            self.assertEqual(mock_bulk_create.call_count, 1)
            # Verify error was logged
            mock_logger.error.assert_called()
            # Verify console fallback was called immediately
            mock_console.assert_called_once()

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging.logger')
    def test_log_errors_to_console(self, mock_logger):
        """Test console fallback logging format."""
        _log_errors_to_console(self.course_scan.id, self.errors)
        
        # Verify console logs were written for each error
        self.assertEqual(mock_logger.error.call_count, 2)
        error_calls = [str(c) for c in mock_logger.error.call_args_list]
        # Verify [CONSOLE_FALLBACK] marker is present
        self.assertTrue(any('[CONSOLE_FALLBACK]' in call for call in error_calls))
        # Verify error details are logged
        self.assertTrue(any('assignment' in call for call in error_calls))
        self.assertTrue(any('page' in call for call in error_calls))
