import asyncio
import logging
import re
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase

from backend.canvas_app_explorer.decorators import log_execution_time


class TestLogExecutionTimeDecorator(TestCase):
    """Tests for the log_execution_time decorator"""

    # Configurable sleep times for tests
    MINIMAL_ASYNC_SLEEP = 0.01  # Minimal sleep for async functions that need to yield control
    MEASURABLE_SLEEP = 0.05     # Sleep duration for timing accuracy tests

    def test_sync_function_execution_logging(self):
        """Test that sync functions log execution time"""
        @log_execution_time
        def sync_function():
            return "result"

        with patch('backend.canvas_app_explorer.decorators.logger') as mock_logger:
            result = sync_function()
            
            # Verify function executes correctly
            self.assertEqual(result, "result")
            
            # Verify logger was called with execution time
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            self.assertIn("sync_function", call_args)
            self.assertIn("execution time", call_args)
            self.assertIn("seconds", call_args)

    def test_sync_function_with_arguments(self):
        """Test sync function with arguments"""
        @log_execution_time
        def sync_function_with_args(a, b, c=None):
            return a + b + (c or 0)

        with patch('backend.canvas_app_explorer.decorators.logger') as mock_logger:
            result = sync_function_with_args(1, 2, c=3)
            
            self.assertEqual(result, 6)
            mock_logger.info.assert_called_once()

    def test_sync_function_exception_still_logs(self):
        """Test that execution time is logged even if sync function raises exception"""
        @log_execution_time
        def sync_function_with_error():
            raise ValueError("Test error")

        with patch('backend.canvas_app_explorer.decorators.logger') as mock_logger:
            with self.assertRaises(ValueError):
                sync_function_with_error()
            
            # Verify logger was still called even though exception was raised
            mock_logger.info.assert_called_once()

    def test_async_function_execution_logging(self):
        """Test that async functions log execution time"""
        @log_execution_time
        async def async_function():
            await asyncio.sleep(self.MINIMAL_ASYNC_SLEEP)
            return "async_result"

        with patch('backend.canvas_app_explorer.decorators.logger') as mock_logger:
            result = asyncio.run(async_function())
            
            # Verify function executes correctly
            self.assertEqual(result, "async_result")
            
            # Verify logger was called with execution time
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            self.assertIn("async_function", call_args)
            self.assertIn("execution time", call_args)
            self.assertIn("seconds", call_args)

    def test_async_function_with_arguments(self):
        """Test async function with arguments"""
        @log_execution_time
        async def async_function_with_args(a, b, c=None):
            await asyncio.sleep(self.MINIMAL_ASYNC_SLEEP)
            return a + b + (c or 0)

        with patch('backend.canvas_app_explorer.decorators.logger') as mock_logger:
            result = asyncio.run(async_function_with_args(1, 2, c=3))
            
            self.assertEqual(result, 6)
            mock_logger.info.assert_called_once()

    def test_async_function_exception_still_logs(self):
        """Test that execution time is logged even if async function raises exception"""
        @log_execution_time
        async def async_function_with_error():
            await asyncio.sleep(self.MINIMAL_ASYNC_SLEEP)
            raise ValueError("Test async error")

        with patch('backend.canvas_app_explorer.decorators.logger') as mock_logger:
            with self.assertRaises(ValueError):
                asyncio.run(async_function_with_error())
            
            # Verify logger was still called even though exception was raised
            mock_logger.info.assert_called_once()

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves original function name and docstring"""
        @log_execution_time
        def documented_function():
            """This is a docstring"""
            return "value"

        self.assertEqual(documented_function.__name__, "documented_function")
        self.assertEqual(documented_function.__doc__, "This is a docstring")

    def test_sync_execution_time_accuracy(self):
        """Test that execution time is reasonably accurate for sync functions"""
        @log_execution_time
        def slow_function():
            time.sleep(self.MEASURABLE_SLEEP)
            return "done"

        with patch('backend.canvas_app_explorer.decorators.logger') as mock_logger:
            slow_function()
            
            call_args = mock_logger.info.call_args[0][0]
            # Extract the number from the logged message
            # Message format: "function_name execution time: X.XX seconds"
            match = re.search(r'(\d+\.\d+)', call_args)
            self.assertIsNotNone(match)
            execution_time = float(match.group(1))
            
            # Verify execution time is at least the expected sleep duration
            self.assertGreaterEqual(execution_time, self.MEASURABLE_SLEEP)

    def test_async_execution_time_accuracy(self):
        """Test that execution time is reasonably accurate for async functions"""
        @log_execution_time
        async def slow_async_function():
            await asyncio.sleep(self.MEASURABLE_SLEEP)
            return "done"

        with patch('backend.canvas_app_explorer.decorators.logger') as mock_logger:
            asyncio.run(slow_async_function())
            
            call_args = mock_logger.info.call_args[0][0]
            # Extract the number from the logged message
            match = re.search(r'(\d+\.\d+)', call_args)
            self.assertIsNotNone(match)
            execution_time = float(match.group(1))
            
            # Verify execution time is at least the expected sleep duration
            self.assertGreaterEqual(execution_time, self.MEASURABLE_SLEEP)
