from django.test import SimpleTestCase

from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    _is_course_scan_error,
)


class TestIsCourseScanError(SimpleTestCase):
    def test_returns_true_for_valid_error_shape(self):
        error_obj = {
            "type": "assignment",
            "title": "Assignment 1",
            "error": ValueError("failed"),
            "canvas_url": "https://canvas.example.com/courses/1/assignments/1",
        }

        self.assertTrue(_is_course_scan_error(error_obj))

    def test_returns_false_for_non_dict(self):
        self.assertFalse(_is_course_scan_error("not-a-dict"))
        self.assertFalse(_is_course_scan_error(123))
        self.assertFalse(_is_course_scan_error(None))

    def test_returns_false_when_required_keys_missing(self):
        missing_title = {
            "type": "assignment",
            "error": ValueError("failed"),
            "canvas_url": "https://canvas.example.com/courses/1/assignments/1",
        }
        self.assertFalse(_is_course_scan_error(missing_title))

    def test_returns_false_when_field_types_are_invalid(self):
        invalid_error_type = {
            "type": "assignment",
            "title": "Assignment 1",
            "error": "failed",
            "canvas_url": "https://canvas.example.com/courses/1/assignments/1",
        }
        self.assertFalse(_is_course_scan_error(invalid_error_type))

        invalid_title_type = {
            "type": "assignment",
            "title": 99,
            "error": ValueError("failed"),
            "canvas_url": "https://canvas.example.com/courses/1/assignments/1",
        }
        self.assertFalse(_is_course_scan_error(invalid_title_type))

        invalid_canvas_url_type = {
            "type": "assignment",
            "title": "Assignment 1",
            "error": ValueError("failed"),
            "canvas_url": 404,
        }
        self.assertFalse(_is_course_scan_error(invalid_canvas_url_type))

        invalid_type_type = {
            "type": 1,
            "title": "Assignment 1",
            "error": ValueError("failed"),
            "canvas_url": "https://canvas.example.com/courses/1/assignments/1",
        }
        self.assertFalse(_is_course_scan_error(invalid_type_type))
