from django.test import TestCase
from unittest.mock import patch, AsyncMock
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

        images = extract_images_from_html(html)
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
        images_default = extract_images_from_html(html)
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

        images = extract_images_from_html(html)
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

        images = extract_images_from_html(html)
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

        images = extract_images_from_html(html)
        self.assertIsInstance(images, list)
        # All three images should be picked up since they have filenames with image extensions
        self.assertEqual(len(images), 3)
        
        self.assertIn("77777777", images[0])
        
        self.assertIn("88888888", images[1])
        
        self.assertIn("99999999", images[2])
    
    def test_get_courses_images_filters_out_items_with_empty_images(self):
    # sample payload: some items have empty images lists and should be filtered out
        sample_assignments = [
            {"id": 1509690, "name": "Assignment 1", "images": [], "type": "assignment"},
            {
                "id": 2936007,
                "name": "Assignment 2",
                "images": [
                    {
                        "image_id": "43525485",
                        "download_url": "https://umich.test.instructure.com/files/43525485/download?verifier=DWBmBFpQ7vEUEyTdTf4e2wwESRGRpCMCnRtCxeDg&download_frd=1",
                    }
                ],
                "type": "assignment",
            },
        ]

        sample_pages = [
            {"id": 1664893, "name": "Page 1", "images": [
                {
                    "image_id": "43525482",
                    "download_url": "https://umich.test.instructure.com/files/43525482/download?verifier=Qomqu8ZhT5G2k5s6xa2qpS6orXV0ItIlE7sfhq1c&download_frd=1",
                }
            ], "type": "page"},
            {"id": 1664894, "name": "Page 2", "images": [], "type": "page"},
        ]

        expected_filtered = [
            {
                "id": 2936007,
                "name": "Assignment 2",
                "images": [
                    {
                        "image_id": "43525485",
                        "download_url": "https://umich.test.instructure.com/files/43525485/download?verifier=DWBmBFpQ7vEUEyTdTf4e2wwESRGRpCMCnRtCxeDg&download_frd=1",
                    }
                ],
                "type": "assignment",
            },
            {
                "id": 1664893,
                "name": "Page 1",
                "images": [
                    {
                        "image_id": "43525482",
                        "download_url": "https://umich.test.instructure.com/files/43525482/download?verifier=Qomqu8ZhT5G2k5s6xa2qpS6orXV0ItIlE7sfhq1c&download_frd=1",
                    }
                ],
                "type": "page",
            },
        ]

        # Patch the async fetch helpers to return our sample data (no network calls)
        module_path = "backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan"
        
        async def mock_fetch_content_items(fn, course):
            if fn.__name__ == 'get_assignments':
                return sample_assignments
            elif fn.__name__ == 'get_pages':
                return sample_pages
            return []

        mock_fetch = AsyncMock(side_effect=mock_fetch_content_items)
        
        with patch(f"{module_path}.fetch_content_items_async", mock_fetch), \
             patch(f"{module_path}.save_scan_results") as mock_save:

            # Create a dummy course object and a dummy canvas_api (non-None) to exercise the canvas_api path
            from canvasapi.course import Course
            dummy_course = Course(None, {'id': 403334})

            # 1. Call get_courses_images to get raw results
            # Note: get_courses_images is already wrapped with @async_to_sync, so call it directly
            raw_results = get_courses_images(dummy_course)

            # 2. Call unpack_and_store_content_images which does the filtering and calls save_scan_results
            from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import unpack_and_store_content_images
            unpack_and_store_content_images(raw_results, dummy_course)

            # 3. Assert that save_scan_results was called once and verify it received the filtered results
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            
            # save_scan_results(course_id, items) - course_id is first arg, items is second
            course_id = call_args[0][0]
            payload = call_args[0][1]  # Second positional argument: items list
            
            self.assertEqual(course_id, 403334, "Course ID should match")
            self.assertEqual(len(payload), 2, "Expected 2 items with images after filtering")
            
            # Verify the filtered items match expected content
            item_ids = [item["id"] for item in payload]
            self.assertIn(2936007, item_ids, "Assignment 2 should be included")
            self.assertIn(1664893, item_ids, "Page 1 should be included")
            
            # Verify items with empty images were filtered out
            for item in payload:
                self.assertGreater(len(item.get("images", [])), 0, 
                                 f"Item {item['id']} should have at least one image")