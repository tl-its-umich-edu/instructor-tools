import logging
from typing import List

from backend.canvas_app_explorer.models import CourseScanErrorLog
from backend.canvas_app_explorer.alt_text_helper.background_tasks.types import CourseScanError

logger = logging.getLogger(__name__)


def log_course_scan_errors(course_scan_id: int, errors: List[CourseScanError]) -> None:
    """Persist one or more CourseScanError entries to the database."""
    if not errors:
        return
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
    except Exception as e:
        logger.error(f"Failed to persist CourseScanErrorLog entries for course_scan_id {course_scan_id}: {e}")
