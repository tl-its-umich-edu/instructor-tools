import logging
import time
from typing import List

from django.db.utils import DatabaseError
from backend.canvas_app_explorer.models import CourseScanErrorLog
from backend.canvas_app_explorer.alt_text_helper.background_tasks.types import CourseScanError

logger = logging.getLogger(__name__)

# Retry configuration for error logging persistence
# Used when attempting to save CourseScanErrorLog entries to the database
ERROR_LOG_MAX_RETRY_ATTEMPTS = 3  # Maximum number of retry attempts for DB persistence
ERROR_LOG_RETRY_BACKOFF_BASE = 2  # Base for exponential backoff calculation (2^attempt seconds)


def log_course_scan_errors(course_scan_id: int, errors: List[CourseScanError]) -> None:
    """
    Persist one or more CourseScanError entries to the database with retry logic.
    
    Attempts to persist errors to the database with exponential backoff retries.
    If all retries fail, errors are logged to console as a fallback mechanism.
    This ensures that errors are not lost even if the database is temporarily unavailable.
    
    Retry behavior is controlled by module-level constants:
    - ERROR_LOG_MAX_RETRY_ATTEMPTS: Maximum number of retry attempts
    - ERROR_LOG_RETRY_BACKOFF_BASE: Base for exponential backoff (backoff = base^attempt seconds)
    
    :param course_scan_id: The CourseScan ID to associate with the errors
    :param errors: List of CourseScanError dicts to persist
    """
    max_retries = ERROR_LOG_MAX_RETRY_ATTEMPTS
    if not errors:
        return

    for attempt in range(max_retries):
        try:
            rows = [
                CourseScanErrorLog(
                    course_scan_id=course_scan_id,
                    error_type=error['type'],
                    error_title=error.get('title'),
                    error_message=str(error['error']),
                    canvas_url=error.get('canvas_url', ''),
                )
                for error in errors
            ]
            CourseScanErrorLog.objects.bulk_create(rows)
            logger.debug(
                "Logged %d CourseScanError entries to database: course_scan_id=%s",
                len(rows),
                course_scan_id,
            )
            return  # Success - exit early
        except DatabaseError as db_error:
            # Database-related errors are transient; retry with exponential backoff
            if attempt < max_retries - 1:
                backoff_seconds = ERROR_LOG_RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed to log {len(errors)} error(s) "
                    f"for course_scan_id {course_scan_id}. Retrying in {backoff_seconds}s. "
                    f"DB Error: {db_error}"
                )
                time.sleep(backoff_seconds)
                continue
            else:
                # Final attempt failed - log all errors to console as fallback
                logger.error(
                    f"CRITICAL: Failed to persist {len(errors)} CourseScanErrorLog entries after "
                    f"{max_retries} attempts for course_scan_id {course_scan_id}. "
                    f"Falling back to console logging. Database Error: {db_error}"
                )
                _log_errors_to_console(course_scan_id, errors)
                return
        except Exception as unexpected_error:
            # Unexpected errors should not retry
            logger.error(
                f"Unexpected error persisting CourseScanErrorLog entries for course_scan_id {course_scan_id}: "
                f"{unexpected_error}. Falling back to console logging."
            )
            _log_errors_to_console(course_scan_id, errors)
            return


def _log_errors_to_console(course_scan_id: int, errors: List[CourseScanError]) -> None:
    """
    Fallback logging function when database persistence fails.
    
    Logs all error details to console/stdout for capture by container logging systems.
    This ensures errors are not completely lost even if database is unavailable.
    
    :param course_scan_id: The CourseScan ID for context
    :param errors: List of CourseScanError dicts to log
    """
    for idx, error in enumerate(errors, start=1):
        logger.error(
            f"[CONSOLE_FALLBACK] Error {idx}/{len(errors)} for course_scan_id {course_scan_id}: "
            f"type={error.get('type')}, title={error.get('title')}, "
            f"message={str(error.get('error'))}, canvas_url={error.get('canvas_url', 'N/A')}"
        )
