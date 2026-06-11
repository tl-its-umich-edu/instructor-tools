from django.test import TestCase
from unittest.mock import patch, MagicMock
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    extract_images_from_html,
)
from backend.canvas_app_explorer.utils import generate_canvas_content_url
from backend import settings
from backend import settings


class TestExtractImagesFromHtmlExceptionHandling(TestCase):
    """Test suite for exception handling in extract_images_from_html function."""

    def setUp(self):
        self.course_id = 403334
        self.content_type = 'assignment'
        self.content_title = 'Test Assignment'
        self.content_id = 12345
        self.content_parent_id = None

    def test_extract_images_happy_path_returns_urls(self):
        """Test successful image extraction returns list of URLs."""
        # Alt text ending with extension passes the filename-alt filter
        html = '<img src="https://external.com/img1.png" alt="image1.png" /><img src="https://external.com/img2.png" alt="image2.jpg" />'
        
        result = extract_images_from_html(
            html,
            self.course_id,
            self.content_type,
            self.content_title,
            self.content_id,
            self.content_parent_id,
        )
        
        self.assertEqual(len(result), 2)
        self.assertIn('https://external.com/img1.png', result)
        self.assertIn('https://external.com/img2.png', result)

    def test_extract_images_empty_html_returns_empty_list(self):
        """Test that empty HTML returns empty list."""
        html = ''
        
        result = extract_images_from_html(
            html,
            self.course_id,
            self.content_type,
            self.content_title,
            self.content_id,
            self.content_parent_id,
        )
        
        self.assertEqual(result, [])

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan._parse_canvas_file_src')
    def test_extract_images_exception_during_processing_wrapped_in_course_scan_error(self, mock_parse):
        """Test that exceptions during image processing are caught and wrapped in CourseScanError format."""
        # Setup HTML with Canvas image that will trigger exception during parsing
        html = f'<img src="https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/12345/preview" alt="test.png" />'
        
        # Make _parse_canvas_file_src raise an exception
        mock_parse.side_effect = ValueError('Invalid file URL format')
        
        result = extract_images_from_html(
            html,
            self.course_id,
            self.content_type,
            self.content_title,
            self.content_id,
            self.content_parent_id,
        )
        
        # Result should be a list with one CourseScanError dict
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        
        error = result[0]
        self.assertEqual(error['type'], self.content_type)
        self.assertEqual(error['title'], self.content_title)
        self.assertIsInstance(error['error'], ValueError)
        self.assertIn('Invalid file URL format', str(error['error']))
        self.assertEqual(
            error['canvas_url'],
            generate_canvas_content_url(self.course_id, self.content_type, self.content_id, self.content_parent_id)
        )

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan._parse_canvas_file_src')
    def test_extract_images_multiple_exceptions_wrapped_separately(self, mock_parse):
        """Test that multiple exceptions are each wrapped in their own CourseScanError."""
        # Setup HTML with multiple Canvas images with alt text that passes filename check
        html = f'''
            <img src="https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/111/preview" alt="image1.png" />
            <img src="https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/222/preview" alt="image2.jpg" />
        '''
        
        # Make _parse_canvas_file_src raise exception twice
        mock_parse.side_effect = [
            ValueError('Invalid format 1'),
            RuntimeError('Parse error 2'),
        ]
        
        result = extract_images_from_html(
            html,
            self.course_id,
            self.content_type,
            self.content_title,
            self.content_id,
            self.content_parent_id,
        )
        
        # Result should be list with two separate CourseScanError dicts
        self.assertEqual(len(result), 2)
        
        error1 = result[0]
        self.assertEqual(error1['type'], self.content_type)
        self.assertIn('Invalid format 1', str(error1['error']))
        
        error2 = result[1]
        self.assertEqual(error2['type'], self.content_type)
        self.assertIn('Parse error 2', str(error2['error']))

    def test_extract_images_exception_preserves_course_scan_error_fields(self):
        """Test that exception wrapping preserves all CourseScanError fields correctly."""
        html = f'<img src="https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/999/preview" alt="test.jpg" />'
        
        with patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan._parse_canvas_file_src') as mock_parse:
            mock_parse.side_effect = RuntimeError('Test error message')
            
            result = extract_images_from_html(
                html,
                self.course_id,
                'page',
                'Test Page',
                9999,
                None,
            )
        
        self.assertEqual(len(result), 1)
        error = result[0]
        
        # Validate all required CourseScanError fields are present
        self.assertIn('type', error)
        self.assertIn('title', error)
        self.assertIn('error', error)
        self.assertIn('canvas_url', error)
        
        # Validate field values
        self.assertEqual(error['type'], 'page')
        self.assertEqual(error['title'], 'Test Page')
        self.assertIsInstance(error['error'], RuntimeError)
        self.assertTrue(error['canvas_url'].startswith('http'))

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan._parse_canvas_file_src')
    def test_extract_images_mixed_success_and_errors_returns_only_errors(self, mock_parse):
        """Test that when some images fail and some succeed, only errors are returned (not mixed)."""
        html = f'''
            <img src="https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/111/preview" alt="file1.png" />
            <img src="https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/403334/files/222/preview" alt="file2.jpg" />
        '''
        
        # First parse succeeds, second fails
        mock_parse.side_effect = [
            f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/files/111/download?download_frd=1',
            ValueError('Parse failed for second image'),
        ]
        
        result = extract_images_from_html(
            html,
            self.course_id,
            self.content_type,
            self.content_title,
            self.content_id,
            self.content_parent_id,
        )
        
        # When there are any errors in the for loop, entire result is errors list
        # (This is the behavior shown in the function logic)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]['type'], self.content_type)
        self.assertIn('Parse failed', str(result[0]['error']))

    def test_extract_images_no_src_attribute_skipped_no_exception(self):
        """Test that images without src attribute are safely skipped."""
        html = '<img alt="No Source" /><img src="https://external.com/valid.png" alt="file.png" />'
        
        result = extract_images_from_html(
            html,
            self.course_id,
            self.content_type,
            self.content_title,
            self.content_id,
            self.content_parent_id,
        )
        
        # Should only have the valid image
        self.assertEqual(len(result), 1)
        self.assertIn('https://external.com/valid.png', result)

    def test_extract_images_decorative_presentation_role_skipped(self):
        """Test that images with role='presentation' are safely skipped."""
        html = '<img src="https://external.com/decorative.png" alt="deco.png" role="presentation" /><img src="https://external.com/content.png" alt="content.jpg" />'
        
        result = extract_images_from_html(
            html,
            self.course_id,
            self.content_type,
            self.content_title,
            self.content_id,
            self.content_parent_id,
        )
        
        # Should only have non-decorative image
        self.assertEqual(len(result), 1)
        self.assertIn('https://external.com/content.png', result)
