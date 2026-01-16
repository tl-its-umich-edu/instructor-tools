from django.test import TestCase
from unittest.mock import patch, MagicMock
from backend.canvas_app_explorer.alt_text_helper.process_content_images import ProcessContentImages
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    retrieve_and_store_alt_text,
    fetch_and_scan_course,
)
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem, CourseScanStatus
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from django.contrib.auth.models import User


class TestProcessContentImages(TestCase):
    EXPECTED_ALT_TEXT = 'A descriptive alt text'

    def setUp(self):
        # create a CourseScan and related content/image items
        self.course_id = 123456
        CourseScan.objects.create(course_id=self.course_id)
        ContentItem.objects.create(course_id=self.course_id, content_type='page', content_id=1, content_name='Page 1')
        ImageItem.objects.create(course_id=self.course_id, content_item_id=1, image_id=111, image_url='http://example.com/img.jpg')

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

        proc = ProcessContentImages(course_id=self.course_id)
        results = proc.retrieve_images_with_alt_text()

        # ensure results contain our image_url and generated alt text
        self.assertIn('http://example.com/img.jpg', results)
        self.assertEqual(results['http://example.com/img.jpg']['image_alt_text'], self.EXPECTED_ALT_TEXT)

        # DB record should be updated
        img = ImageItem.objects.get(course_id=self.course_id, image_id=111)
        self.assertEqual(img.image_alt_text, 'A descriptive alt text')

    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.ProcessContentImages.get_image_content_async')
    def test_retrieve_images_with_alt_text_raises_on_fetch_error(self, mock_get_content):
        mock_get_content.return_value = Exception('fetch failed')

        proc = ProcessContentImages(course_id=self.course_id)
        with self.assertRaises(ImageContentExtractionException) as ctx:
            proc.retrieve_images_with_alt_text()

        # ensure the underlying errors were captured
        self.assertTrue(len(ctx.exception.errors) >= 1)

        # image alt text should still be blank/None
        img = ImageItem.objects.get(course_id=self.course_id, image_id=111)
        self.assertTrue(img.image_alt_text in (None, ''))

    @patch('backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.ProcessContentImages')
    def test_retrieve_and_store_alt_text_delegates(self, mock_proc_cls):
        # configure the ProcessContentImages mock
        mock_instance = mock_proc_cls.return_value
        mock_instance.retrieve_images_with_alt_text.return_value = {'http://example.com/img.jpg': {'image_alt_text': 'alt'}}

        from canvasapi.course import Course
        dummy_course = Course(None, {'id': self.course_id})

        result = retrieve_and_store_alt_text(dummy_course, bearer_token=None)

        mock_proc_cls.assert_called_once_with(course_id=self.course_id, bearer_token=None)
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
        mock_unpack.return_value = None
        
        # Make retrieve_and_store_alt_text raise ImageContentExtractionException
        mock_retrieve_alt.side_effect = ImageContentExtractionException(
            errors=['Image fetch failed', 'Processing error']
        )
        
        task = {
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

        proc = ProcessContentImages(course_id=self.course_id)
        results = proc.retrieve_images_with_alt_text()

        # Results should be empty since the image was skipped
        self.assertEqual(results, {})

        # DB record should NOT be updated (should still be None)
        img_record = ImageItem.objects.get(course_id=self.course_id, image_id=111)
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

        proc = ProcessContentImages(course_id=self.course_id)
        
        # Get the image models
        image_models = list(ImageItem.objects.filter(course_id=self.course_id))
        
        # Call _process_images_concurrently which calls _worker_async
        results = proc._process_images_concurrently(image_models)
        
        # Should have one result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['img'].image_id, 111)
        # alt_text should be empty string, not None
        self.assertEqual(results[0]['alt_text'], '')

    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.ProcessContentImages.get_image_content_async')
    @patch('backend.canvas_app_explorer.alt_text_helper.process_content_images.AltTextProcessor.generate_alt_text')
    def test_retrieve_images_handles_mixed_success_and_none_returns(self, mock_generate_alt, mock_get_content):
        """Test that when some images return alt text and some return None, only successful ones are updated."""
        from PIL import Image
        import io
        
        # Add another image
        ImageItem.objects.create(
            course_id=self.course_id, content_item_id=1, image_id=222, image_url='http://example.com/img2.jpg'
        )
        
        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        mock_get_content.return_value = buf.getvalue()
        
        # First image gets alt text, second returns None
        mock_generate_alt.side_effect = ['First image alt text', None]

        proc = ProcessContentImages(course_id=self.course_id)
        results = proc.retrieve_images_with_alt_text()

        # Only the first image should be in results
        self.assertEqual(len(results), 1)
        self.assertIn('http://example.com/img.jpg', results)
        self.assertEqual(results['http://example.com/img.jpg']['image_alt_text'], 'First image alt text')

        # First image should be updated
        img1 = ImageItem.objects.get(image_id=111)
        self.assertEqual(img1.image_alt_text, 'First image alt text')
        
        # Second image should NOT be updated (remain None)
        img2 = ImageItem.objects.get(image_id=222)
        self.assertIsNone(img2.image_alt_text)
