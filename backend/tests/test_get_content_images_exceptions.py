from backend.canvas_app_explorer.alt_text_helper.process_content_images import ProcessContentImages
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem
from django.test import TestCase


class DummyProcessImages(ProcessContentImages):
    def __init__(self, course_id):
        # don't need canvas_api parameter anymore
        super().__init__(course_id=course_id)

    async def get_image_content_async(self, img_url):
        # Mock the async fetch for testing
        # Fail on the first image, succeed on the second
        if img_url == 'https://example.com/1':
            return Exception('fetch failed')
        from PIL import Image
        import io
        img = Image.new('RGB', (5, 5), color=(0, 255, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return buf.getvalue()

class TestGetContentImages(TestCase):
    def setUp(self):
        # Create CourseScan and ContentItem necessary for FK constraints
        self.course_scan = CourseScan.objects.create(course_id=1)
        self.content_item = ContentItem.objects.create(course=self.course_scan, content_type='page', content_id=10, content_name='C')

        self.image_item_1 = ImageItem.objects.create(course=self.course_scan, content_item=self.content_item, image_url='https://example.com/1')
        self.image_item_2 = ImageItem.objects.create(course=self.course_scan, content_item=self.content_item, image_url='https://example.com/2')

    def test_retrieve_images_updates_successful_and_raises_on_errors(self):
        proc = DummyProcessImages(course_id=1)
        # stub alt_text_generator to deterministic value
        # The generate_alt_text receives a PIL Image object, not bytes
        proc.alt_text_processor.generate_alt_text = lambda img: 'GENERATED'

        with self.assertRaises(ImageContentExtractionException) as cm:
            proc.retrieve_images_with_alt_text()

        exc = cm.exception
        # Debugging output to inspect why multiple errors are present
        print("DEBUG: exc.errors repr:", repr(exc.errors))
        print("DEBUG: exc.errors types:", [type(e) for e in exc.errors])
        print("DEBUG: exc.errors contents:", exc.errors)
        self.assertIsInstance(exc.errors, list)
        self.assertEqual(len(exc.errors), 1)

        # the second ImageItem should be updated with the generated alt text
        img2 = ImageItem.objects.get(id=self.image_item_2.id)
        self.assertEqual(img2.image_alt_text, 'GENERATED')
