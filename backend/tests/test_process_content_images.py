from django.test import TestCase
from unittest.mock import patch, MagicMock
from backend.canvas_app_explorer.alt_text_helper.process_content_images import ProcessContentImages
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    retrieve_and_store_alt_text,
    fetch_and_scan_course,
)
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem, CourseScanStatus
from django.contrib.auth.models import User


class TestProcessContentImages(TestCase):
    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.ProcessContentImages.get_image_content_async')
    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.AltTextProcessor.generate_alt_text')
    def test_retrieve_images_with_alt_text_handles_alt_text_exception(self, mock_generate_alt, mock_get_content):
        """Test that exceptions from generate_alt_text are caught and returned as image_process_error."""
        from PIL import Image
        import io

        # Simulate valid image content
        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        mock_get_content.return_value = buf.getvalue()

        # Simulate exception from alt text processor
        mock_generate_alt.side_effect = Exception('alt text failed')

        proc = ProcessContentImages(course_scan_id=self.course_scan.id, course_id=self.course_id)
        results = proc.retrieve_images_with_alt_text()

        # Should return a list of errors
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'image_process_error')
        self.assertIn('alt text failed', str(results[0]['error']))

        # image alt text should still be blank/None
        img = ImageItem.objects.get(id=self.image_item.id)
        self.assertTrue(img.image_alt_text in (None, ''))
    EXPECTED_ALT_TEXT = 'A descriptive alt text'

    def setUp(self):
        # create a CourseScan and related content/image items
        self.course_id = 123456
        self.course_scan = CourseScan.objects.create(course_id=self.course_id)
        content_item = ContentItem.objects.create(course_scan=self.course_scan, content_type='page', content_id=1, content_name='Page 1')
        self.image_item = ImageItem.objects.create(content_item=content_item, image_url='http://example.com/img.jpg')

    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.ProcessContentImages.get_image_content_async')
    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.AltTextProcessor.generate_alt_text')
    def test_retrieve_images_with_alt_text_success_updates_db(self, mock_generate_alt, mock_get_content):
        # create a small in-memory JPEG to simulate a real image response
        from PIL import Image
        import io
        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        mock_get_content.return_value = buf.getvalue()
        mock_generate_alt.return_value = self.EXPECTED_ALT_TEXT

        proc = ProcessContentImages(course_scan_id=self.course_scan.id, course_id=self.course_id)
        results = proc.retrieve_images_with_alt_text()

        # Success path returns True
        self.assertTrue(results)

        # DB record should be updated
        img = ImageItem.objects.get(id=self.image_item.id)
        self.assertEqual(img.image_alt_text, 'A descriptive alt text')

    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.ProcessContentImages.get_image_content_async')
    def test_retrieve_images_with_alt_text_raises_on_fetch_error(self, mock_get_content):
        mock_get_content.return_value = Exception('fetch failed')

        proc = ProcessContentImages(course_scan_id=self.course_scan.id, course_id=self.course_id)
        results = proc.retrieve_images_with_alt_text()

        # Failures are returned as CourseScanError entries (not raised)
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'image_process_error')

        # image alt text should still be blank/None
        img = ImageItem.objects.get(id=self.image_item.id)
        self.assertTrue(img.image_alt_text in (None, ''))

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.ProcessContentImages')
    def test_retrieve_and_store_alt_text_delegates(self, mock_proc_cls):
        # configure the ProcessContentImages mock
        mock_instance = mock_proc_cls.return_value
        mock_instance.retrieve_images_with_alt_text.return_value = {'http://example.com/img.jpg': {'image_alt_text': 'alt'}}

        result = retrieve_and_store_alt_text(self.course_scan.id, self.course_id, bearer_token=None)

        mock_proc_cls.assert_called_once_with(course_scan_id=self.course_scan.id, course_id=self.course_id, bearer_token=None)
        self.assertEqual(result, {'http://example.com/img.jpg': {'image_alt_text': 'alt'}})

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.retrieve_and_store_alt_text')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.unpack_and_store_content_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.get_courses_images')
    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.MANAGER_FACTORY')
    def test_fetch_and_scan_course_handles_image_extraction_exception(
        self, mock_factory, mock_get_images, mock_unpack, mock_retrieve_alt
    ):
        """Test that fetch_and_scan_course sets scan status to FAILED when ImageContentExtractionException is raised."""
        course_id = 999
        user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create initial CourseScan record
        course_scan = CourseScan.objects.create(course_id=course_id, status=CourseScanStatus.PENDING.value)
        
        # Setup mocks
        mock_manager = MagicMock()
        mock_factory.create_manager.return_value = mock_manager
        mock_canvas_api = MagicMock()
        mock_manager.canvas_api = mock_canvas_api
        
        mock_get_images.return_value = ([], [], [])
        mock_unpack.return_value = True

        # Make retrieve_and_store_alt_text return extraction errors
        mock_retrieve_alt.return_value = [
            {
                'type': 'image_process_error',
                'title': 'Course',
                'error': Exception('Image fetch failed'),
                'canvas_url': 'https://example.com/course',
            },
            {
                'type': 'alt_text_process_error',
                'title': 'Course',
                'error': Exception('Processing error'),
                'canvas_url': 'https://example.com/course',
            },
        ]
        
        task = {
            'course_scan_id': course_scan.id,
            'course_id': course_id,
            'user_id': user.id,
            'canvas_callback_url': 'http://localhost/callback'
        }
        
        # Call the function - it should not raise an exception
        fetch_and_scan_course(task)
        
        # Verify that CourseScan status was set to FAILED
        course_scan.refresh_from_db()
        self.assertEqual(course_scan.status, CourseScanStatus.FAILED.value)

    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.ProcessContentImages.get_image_content_async')
    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.AltTextProcessor.generate_alt_text')
    def test_retrieve_images_skips_when_generate_alt_text_returns_none(self, mock_generate_alt, mock_get_content):
        """Test that when generate_alt_text returns None, the image is skipped and not updated in DB."""
        from PIL import Image
        import io
        
        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        mock_get_content.return_value = buf.getvalue()
        mock_generate_alt.return_value = None  # Simulate API failure returning None

        proc = ProcessContentImages(course_scan_id=self.course_scan.id, course_id=self.course_id)
        results = proc.retrieve_images_with_alt_text()

        # No processing errors occurred
        self.assertTrue(results)

        # No alt text persisted for None output
        img_record = ImageItem.objects.get(id=self.image_item.id)
        self.assertIsNone(img_record.image_alt_text)

    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.ProcessContentImages.get_image_content_async')
    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.AltTextProcessor.generate_alt_text')
    def test_process_images_concurrently_converts_none_to_empty_string(self, mock_generate_alt, mock_get_content):
        """Test that _worker_async converts None return to empty string."""
        from PIL import Image
        import io
        from django.conf import settings
        
        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        mock_get_content.return_value = buf.getvalue()
        mock_generate_alt.return_value = None

        proc = ProcessContentImages(course_scan_id=self.course_scan.id, course_id=self.course_id)
        
        # Get the image models
        image_models = list(ImageItem.objects.filter(content_item__course_scan_id=self.course_scan.id))
        
        # Call _process_images_concurrently which calls _worker_async
        results = proc._process_images_concurrently(image_models)
        
        # Should have one result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['image'].id, self.image_item.id)
        # alt_text should be empty string, not None
        self.assertEqual(results[0]['alt_text'], '')

    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.ProcessContentImages.get_image_content_async')
    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.AltTextProcessor.generate_alt_text')
    def test_retrieve_images_handles_mixed_success_and_none_returns(self, mock_generate_alt, mock_get_content):
        """Test that when some images return alt text and some return None, only successful ones are updated."""
        from PIL import Image
        import io
        
        # Add another image
        image_item_2 = ImageItem.objects.create(
            content_item=self.image_item.content_item, image_url='http://example.com/img2.jpg'
        )
        
        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        mock_get_content.return_value = buf.getvalue()
        
        # First image gets alt text, second returns None
        mock_generate_alt.side_effect = ['First image alt text', None]

        proc = ProcessContentImages(course_scan_id=self.course_scan.id, course_id=self.course_id)
        results = proc.retrieve_images_with_alt_text()

        # No processing errors occurred
        self.assertTrue(results)

        # First image should be updated
        img1 = ImageItem.objects.get(id=self.image_item.id)
        self.assertEqual(img1.image_alt_text, 'First image alt text')
        
        # Second image should remain without alt text because generator returned None
        img2 = ImageItem.objects.get(id=image_item_2.id)
        self.assertIsNone(img2.image_alt_text)
