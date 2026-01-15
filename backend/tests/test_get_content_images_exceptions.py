from backend.canvas_app_explorer.alt_text_helper.process_content_images import ProcessContentImages
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem
from django.test import TestCase


class DummyProcessImages(ProcessContentImages):
    def __init__(self, course_id):
        # don't need canvas_api parameter anymore
        super().__init__(course_id=course_id)

    def get_image_content_from_canvas(self, images_list):
        # images_list is a list with a single dict per our new implementation
        image_id = images_list[0].get('image_id')
        if image_id == 1:
            return [Exception('fetch failed')]
        # return a real small JPEG byte stream
        from PIL import Image
        import io
        img = Image.new('RGB', (5, 5), color=(0, 255, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return [buf.getvalue()]

    async def get_image_content_async(self, image_id, img_url):
        # Mirror the synchronous get_image_content_from_canvas behavior for the
        # concurrent codepath used by ProcessContentImages._process_images_concurrently
        if image_id == 1:
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

        ImageItem.objects.create(course=self.course_scan, content_item=self.content_item, image_id=1, image_url='https://example.com/1')
        ImageItem.objects.create(course=self.course_scan, content_item=self.content_item, image_id=2, image_url='https://example.com/2')

    def test_retrieve_images_updates_successful_and_raises_on_errors(self):
        proc = DummyProcessImages(course_id=1)
        # stub alt_text_generator to deterministic value
        proc.alt_text_processor.generate_alt_text = lambda b64: 'GENERATED'

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
        img2 = ImageItem.objects.get(image_id=2)
        self.assertEqual(img2.image_alt_text, 'GENERATED')
