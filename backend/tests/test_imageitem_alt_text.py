from django.test import TestCase
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem


class TestImageItemAltText(TestCase):
    def test_image_alt_text_can_store_long_text(self):
        # create parent CourseScan and ContentItem
        cs = CourseScan.objects.create(course_id=999999)
        content_item = ContentItem.objects.create(
            course_id=cs.course_id,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=1,
            content_name='Test'
        )

        long_text = 'x' * 1500  # longer than 1000 chars
        img = ImageItem.objects.create(
            course_id=cs.course_id,
            content_item=content_item,
            image_id=12345,
            image_url='https://example.com/img.jpg',
            image_alt_text=long_text,
        )

        reloaded = ImageItem.objects.get(pk=img.pk)
        self.assertEqual(reloaded.image_alt_text, long_text)
