from django.test import TestCase
from unittest.mock import patch, AsyncMock
from asgiref.sync import async_to_sync
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    extract_images_from_html,
    get_courses_images,
)

class TestParsingImageContentHTML(TestCase):
    def test_extract_images_from_html_parses_canvas_preview_urls(self):
        # sample page body with two preview images (from provided JSON)
        html = (
            '<p>'
            '<img src="https://umich.test.instructure.com/courses/403334/files/42932050/preview" '
            'alt="Untitled-2 (6)-1.png" width="200" height="200" loading="lazy" />'
            '<img src="https://umich.test.instructure.com/courses/403334/files/42932045/preview" '
            'alt="dfdf.png" width="200" height="113" loading="lazy" />'
            '</p>'
        )

        images = extract_images_from_html(html, course_id=403334)
        self.assertIsInstance(images, list)
        self.assertEqual(len(images), 2)

        # Check that URLs are returned and contain the file IDs
        self.assertIn("42932050", images[0])
        
        self.assertIn("42932045", images[1])
    
    def test_include_presentation_images_when_requested(self):
        # HTML contains one presentation-role image and one normal image
        html = (
            '<p>'
            '<img role="presentation" src="https://umich.test.instructure.com/courses/403334/files/11111111/preview" '
            'alt="this is alt text" />'
            '<img src="https://umich.test.instructure.com/courses/403334/files/22222222/preview" '
            'alt="valid altext" />'
            '</p>'
        )

        # By default presentation images are skipped
        images_default = extract_images_from_html(html, course_id=403334)
        # Only normal-image should be returned (presentation skipped)
        self.assertEqual(len(images_default), 0)

    def test_presentation_images_are_skipped_by_default(self):
        # HTML with a single presentation-role image — should be ignored by default
        html = (
            '<p>'
            '<img role="presentation" src="https://umich.test.instructure.com/courses/403334/files/33333333/preview" '
            'alt="alttext.png" />'
            '</p>'
        )

        images = extract_images_from_html(html, course_id=403334)
        self.assertIsInstance(images, list)
        # presentation-role image should not be included by default
        self.assertEqual(len(images), 0)
    
    def test_role_presentation_image_extention_nice_alt_text(self):
        # HTML with a single presentation-role image with alt text that does not look like a filename
        html = (
            '<p>'
            '<img role="presentation" src="https://umich.test.instructure.com/courses/403334/files/44444444/preview" ' 'alt="A descriptive alt text" />'
            '<img src="https://umich.test.instructure.com/courses/403334/files/55555555/preview" ' 'alt="A descriptive alt text" />'
            '<img src="https://umich.test.instructure.com/courses/403334/files/66666666/preview" ' 'alt="image.jpeg" />'
            '</p>'
        )

        images = extract_images_from_html(html, course_id=403334)
        self.assertIsInstance(images, list)
        # presentation-role image should not be included by default
        self.assertEqual(len(images), 1)
        # Check that the URL contains the file ID
        self.assertIn("66666666", images[0])
    
    def test_extract_images_with_various_file_extensions(self):
        # Test that images with various file extensions (bufr, dcx, etc.) are picked up
        html = (
            '<p>'
            '<img src="https://umich.test.instructure.com/courses/403334/files/77777777/preview" '
            'alt="moreimag.bufr" />'
            '<img src="https://umich.test.instructure.com/courses/403334/files/88888888/preview" '
            'alt="another_image.dcx" />'
            '<img src="https://umich.test.instructure.com/courses/403334/files/99999999/preview" '
            'alt="regular.png" />'
            '</p>'
        )

        images = extract_images_from_html(html, course_id=403334)
        self.assertIsInstance(images, list)
        # All three images should be picked up since they have filenames with image extensions
        self.assertEqual(len(images), 3)
        
        self.assertIn("77777777", images[0])
        
        self.assertIn("88888888", images[1])
        
        self.assertIn("99999999", images[2])
    
    def test_no_async_to_sync_warnings_on_async_functions(self):
        """Ensure async_to_sync functions don't raise warnings about non-async callables."""
        import warnings
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Call the async function via async_to_sync
            from canvasapi.course import Course
            dummy_course = Course(None, {'id': 403334})
            
            with patch("backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.fetch_content_items_async", new_callable=AsyncMock, return_value=[]):
                raw_results = async_to_sync(get_courses_images)(dummy_course)
            
            # Check for the specific warning
            async_sync_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, UserWarning)
                and "async_to_sync was passed a non-async-marked callable" in str(warning.message)
            ]
            self.assertEqual(
                len(async_sync_warnings),
                0,
                "async_to_sync should not warn about non-async callables",
            )