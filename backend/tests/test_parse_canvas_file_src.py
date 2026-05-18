"""
Test suite for _parse_canvas_file_src function.

Tests cover:
- Happy paths: Valid Canvas file preview URLs, user file URLs, public images
- Query parameter preservation and download_frd addition
- Error cases: Missing file_id, invalid URLs, malformed paths
- Edge cases: None/empty input
"""

from django.test import TestCase
from django.test.utils import override_settings
from urllib.parse import urlparse, parse_qs

from backend import settings
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    _parse_canvas_file_src,
)


class TestParseCanvasFileSrc(TestCase):
    """Test suite for _parse_canvas_file_src function."""

    def test_parse_canvas_file_src_happy_path_course_file_url(self):
        """Test converting a course file preview URL to download URL."""
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/42932047/preview'
        result = _parse_canvas_file_src(img_src)
        
        self.assertIsNotNone(result)
        self.assertIn('/files/42932047/download', result)
        self.assertIn('download_frd=1', result)
        self.assertIn(settings.CANVAS_OAUTH_CANVAS_DOMAIN, result)

    def test_parse_canvas_file_src_happy_path_user_file_url(self):
        """Test converting a user file preview URL to download URL."""
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/users/999/files/12345/preview'
        result = _parse_canvas_file_src(img_src)
        
        self.assertIsNotNone(result)
        self.assertIn('/files/12345/download', result)
        self.assertIn('download_frd=1', result)

    def test_parse_canvas_file_src_happy_path_public_image(self):
        """Test that public Canvas images are returned as-is."""
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/images/play_overlay.png'
        result = _parse_canvas_file_src(img_src)
        
        self.assertEqual(result, img_src)

    def test_parse_canvas_file_src_happy_path_nested_public_image(self):
        """Test that nested public Canvas images (e.g., /images/book_stro/icon.png) are returned as-is."""
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/images/book_stro/icon.png'
        result = _parse_canvas_file_src(img_src)
        
        self.assertEqual(result, img_src)

    def test_parse_canvas_file_src_preserves_query_params(self):
        """Test that original query parameters are preserved in download URL."""
        verifier = 'abc123verifier'
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/42932047/preview?verifier={verifier}'
        result = _parse_canvas_file_src(img_src)
        
        self.assertIsNotNone(result)
        self.assertIn(f'verifier={verifier}', result)

    def test_parse_canvas_file_src_adds_download_frd_param(self):
        """Test that download_frd=1 is added to the download URL."""
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/42932047/preview'
        result = _parse_canvas_file_src(img_src)
        
        # Parse the result URL to verify download_frd is present
        parsed = urlparse(result)
        query_params = parse_qs(parsed.query)
        self.assertIn('download_frd', query_params)
        self.assertEqual(query_params['download_frd'][0], '1')

    def test_parse_canvas_file_src_preserves_and_adds_params(self):
        """Test that both original params and download_frd are present."""
        verifier = 'test_verifier_value'
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/42932047/preview?verifier={verifier}'
        result = _parse_canvas_file_src(img_src)
        
        parsed = urlparse(result)
        query_params = parse_qs(parsed.query)
        self.assertIn('verifier', query_params)
        self.assertIn('download_frd', query_params)
        self.assertEqual(query_params['verifier'][0], verifier)
        self.assertEqual(query_params['download_frd'][0], '1')

    def test_parse_canvas_file_src_raises_on_missing_file_id(self):
        """Test that ValueError is raised when file_id cannot be extracted."""
        # URL with /files/ but no file_id after it
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/'
        
        with self.assertRaises(ValueError) as context:
            _parse_canvas_file_src(img_src)
        
        self.assertIn('File ID not found', str(context.exception))

    def test_parse_canvas_file_src_raises_on_invalid_url_format(self):
        """Test that exception is raised for malformed URLs."""
        # URL without /files/ pattern at all
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/some_other_path'
        
        with self.assertRaises(ValueError) as context:
            _parse_canvas_file_src(img_src)
        
        self.assertIn('File ID not found', str(context.exception))

    def test_parse_canvas_file_src_raises_on_invalid_scheme(self):
        """Test that exception is raised for invalid URL schemes."""
        # Malformed URL without scheme
        img_src = 'not-a-valid-url'
        
        with self.assertRaises(Exception):
            _parse_canvas_file_src(img_src)

    def test_parse_canvas_file_src_returns_none_on_empty_input(self):
        """Test that None is returned for empty/None input."""
        result_none = _parse_canvas_file_src(None)
        self.assertIsNone(result_none)
        
        result_empty = _parse_canvas_file_src('')
        self.assertIsNone(result_empty)

    def test_parse_canvas_file_src_constructs_correct_download_url(self):
        """Test that download URL is correctly constructed."""
        file_id = '42932047'
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/{file_id}/preview'
        result = _parse_canvas_file_src(img_src)
        
        expected_url_part = f'/files/{file_id}/download'
        self.assertIn(expected_url_part, result)

    def test_parse_canvas_file_src_preserves_domain(self):
        """Test that the original domain is preserved in download URL."""
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/42932047/preview'
        result = _parse_canvas_file_src(img_src)
        
        parsed_result = urlparse(result)
        parsed_original = urlparse(img_src)
        
        self.assertEqual(parsed_result.scheme, parsed_original.scheme)
        self.assertEqual(parsed_result.netloc, parsed_original.netloc)

    def test_parse_canvas_file_src_handles_multiple_query_params(self):
        """Test that multiple query parameters are preserved."""
        img_src = f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/42932047/preview?verifier=abc&foo=bar&baz=qux'
        result = _parse_canvas_file_src(img_src)
        
        parsed = urlparse(result)
        query_params = parse_qs(parsed.query)
        
        self.assertIn('verifier', query_params)
        self.assertIn('foo', query_params)
        self.assertIn('baz', query_params)
        self.assertIn('download_frd', query_params)
        self.assertEqual(query_params['foo'][0], 'bar')
        self.assertEqual(query_params['baz'][0], 'qux')
