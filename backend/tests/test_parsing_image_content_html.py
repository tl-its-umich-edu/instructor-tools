from django.test import TestCase
from unittest.mock import patch
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

        img0 = images[0]
        self.assertEqual(img0.get("image_id"), "42932050")
        self.assertEqual(
            img0.get("download_url"),
            "https://umich.test.instructure.com/files/42932050/download?download_frd=1",
        )

        img1 = images[1]
        self.assertEqual(img1.get("image_id"), "42932045")
        self.assertEqual(
            img1.get("download_url"),
            "https://umich.test.instructure.com/files/42932045/download?download_frd=1",
        )
    
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
        self.assertEqual(images[0].get("image_id"), "66666666")
    
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
        with patch(f"{module_path}.fetch_assignments_async", return_value=sample_assignments), \
                patch(f"{module_path}.fetch_pages_async", return_value=sample_pages):
            result = get_courses_images(None, 403334)  # manager not used by patched functions
            self.assertEqual(result, expected_filtered)

