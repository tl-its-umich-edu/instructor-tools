from django.test import TestCase

from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    extract_images_from_html,
)


class TestExtractImagesFromHtmlExceptionHandling(TestCase):
    """Edge-case coverage for extract_images_from_html.

    The function returns the raw ``img src`` verbatim — it no longer rewrites Canvas file
    URLs, and no longer wraps per-image failures in CourseScanError. Tests that exercised
    that removed error-wrapping behavior were dropped with it; what remains here covers the
    filtering rules that decide whether an image is collected at all.
    """

    def test_extract_images_happy_path_returns_urls(self):
        """Successful extraction returns the src values as-is."""
        # Alt text ending with an image extension passes the filename-alt filter
        html = (
            '<img src="https://external.com/img1.png" alt="image1.png" />'
            '<img src="https://external.com/img2.png" alt="image2.jpg" />'
        )

        result = extract_images_from_html(html)

        self.assertEqual(result, [
            'https://external.com/img1.png',
            'https://external.com/img2.png',
        ])

    def test_extract_images_empty_html_returns_empty_list(self):
        """Empty HTML returns an empty list."""
        self.assertEqual(extract_images_from_html(''), [])

    def test_extract_images_no_src_attribute_skipped_no_exception(self):
        """Images without a src attribute are safely skipped."""
        html = '<img alt="No Source" /><img src="https://external.com/valid.png" alt="file.png" />'

        result = extract_images_from_html(html)

        self.assertEqual(result, ['https://external.com/valid.png'])

    def test_extract_images_decorative_presentation_role_skipped(self):
        """Images with role='presentation' are skipped as decorative."""
        html = (
            '<img src="https://external.com/decorative.png" alt="deco.png" role="presentation" />'
            '<img src="https://external.com/content.png" alt="content.jpg" />'
        )

        result = extract_images_from_html(html)

        self.assertEqual(result, ['https://external.com/content.png'])

    def test_extract_images_canvas_file_url_returned_unmodified(self):
        """Canvas file preview URLs are stored verbatim, query string included.

        This is what makes the exact-match join in AltTextUpdate._update_alt_text_html work:
        whatever is in the HTML is what lands in ImageItem.image_url.
        """
        src = 'https://umich.instructure.com/courses/403334/files/42932047/preview?verifier=abc123'
        html = f'<img src="{src}" alt="diagram.png" />'

        self.assertEqual(extract_images_from_html(html), [src])
