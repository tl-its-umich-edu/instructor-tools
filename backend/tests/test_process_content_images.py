from django.test import TestCase
from unittest.mock import patch
from backend.canvas_app_explorer.alt_text_helper.process_content_images import ProcessContentImages
from backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan import (
    retrieve_and_store_alt_text,
)
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException


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

        proc = ProcessContentImages(course_id=self.course_id, canvas_api=object())
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

        proc = ProcessContentImages(course_id=self.course_id, canvas_api=object())
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

        canvas_api_obj = object()
        result = retrieve_and_store_alt_text(dummy_course, canvas_api=canvas_api_obj, bearer_token=None)

        mock_proc_cls.assert_called_once_with(course_id=self.course_id, canvas_api=canvas_api_obj, bearer_token=None)
        self.assertEqual(result, {'http://example.com/img.jpg': {'image_alt_text': 'alt'}})
