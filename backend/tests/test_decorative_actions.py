from django.test import TestCase

from backend.canvas_app_explorer.serializers import ReviewImageItemSerializer
from backend.canvas_app_explorer.alt_text_helper.alt_text_update import AltTextUpdate
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem


class DummyCanvasAPI:
    """Minimal stand-in for Canvas API used by AltTextUpdate constructor."""
    _Canvas__requester = None


class TestDecorativeActions(TestCase):
    def test_serializer_allows_decorative(self):
        """Review serializer should accept the new 'decorative' action.

        This test drives development: it will fail until the choice list is updated.
        """
        serializer = ReviewImageItemSerializer(data={
            'image_id': 1,
            'image_url': 'http://example.com/img.png',
            'action': 'decorative',
        })
        self.assertTrue(serializer.is_valid(), msg=f"errors: {serializer.errors}")

    def test_serializer_already_valid_for_approve_and_skip(self):
        for action in ('approve', 'skip'):
            serializer = ReviewImageItemSerializer(data={
                'image_id': 2,
                'image_url': 'http://example.com/x.jpg',
                'action': action,
            })
            self.assertTrue(serializer.is_valid(), msg=f"{action} should be valid")

    def test_update_alt_text_html_handles_decorative(self):
        """When an image is marked decorative the HTML should get role and empty alt."""
        payload = [{
            'content_id': 42,
            'content_type': 'page',
            'images': [
                {
                    'image_id': '100',
                    'image_url': 'http://example.com/img',
                    'action': 'decorative',
                    'approved_alt_text': 'ignored',
                    'image_url_for_update': 'http://example.com/img',
                }
            ]
        }]
        updater = AltTextUpdate(course_id=1, canvas_api=DummyCanvasAPI(), content_with_alt_text=payload, content_types=[])
        original = '<p><img src="http://example.com/img" alt="old"></p>'
        updated = updater._update_alt_text_html(42, original)

        # a decorative image should have role="presentation" and an empty alt attribute
        self.assertIn('role="presentation"', updated)
        self.assertIn('alt=""', updated)

    def test_delete_successfully_updated_items_deletes_decorative(self):
        """Images marked decorative should be removed just like approved items."""
        cs = CourseScan.objects.create(course_id=1)
        ci = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=1,
            content_name='Test'
        )
        img = ImageItem.objects.create(
            course=cs,
            content_item=ci,
            image_url='https://example.com/img.jpg',
            image_alt_text='foo',
        )

        updater = AltTextUpdate(course_id=1, canvas_api=DummyCanvasAPI(), content_with_alt_text=[], content_types=[])
        updater.content_alt_text_update_report = [{
            'content_id': ci.content_id,
            'content_type': ci.content_type,
            'images': [
                {'image_id': img.id, 'action': 'decorative'}
            ]
        }]

        updater.delete_successfully_updated_items()

        self.assertFalse(ImageItem.objects.filter(pk=img.pk).exists())
        self.assertFalse(ContentItem.objects.filter(pk=ci.pk).exists())

    def test_mark_content_images_failed_marks_approved_as_failed(self):
        """_mark_content_images_failed should set is_alt_text_updated=False and error message for approved images."""
        payload = [{
            'content_id': 42,
            'content_type': 'page',
            'images': [
                {
                    'image_id': '100',
                    'image_url': 'http://example.com/img',
                    'action': 'approve',
                    'approved_alt_text': 'alt text',
                    'image_url_for_update': 'http://example.com/img',
                }
            ]
        }]
        updater = AltTextUpdate(course_id=1, canvas_api=DummyCanvasAPI(), content_with_alt_text=payload, content_types=[])
        
        # Mark the image as failed
        updater._mark_content_images_failed(
            [{'content_id': 42, 'error_message': 'Canvas API error'}],
            'page'
        )

        # Verify the image was marked as failed with error message
        image = updater.content_alt_text_update_report[0]['images'][0]
        self.assertEqual(image.get('is_alt_text_updated'), False)
        self.assertEqual(image.get('alt_text_failed_error_message'), 'Canvas API error')

    def test_mark_content_images_failed_marks_decorative_as_failed(self):
        """_mark_content_images_failed should also mark decorative images as failed with error message."""
        payload = [{
            'content_id': 42,
            'content_type': 'page',
            'images': [
                {
                    'image_id': '100',
                    'image_url': 'http://example.com/img',
                    'action': 'decorative',
                    'approved_alt_text': 'ignored',
                    'image_url_for_update': 'http://example.com/img',
                }
            ]
        }]
        updater = AltTextUpdate(course_id=1, canvas_api=DummyCanvasAPI(), content_with_alt_text=payload, content_types=[])
        
        # Mark the decorative image as failed
        updater._mark_content_images_failed(
            [{'content_id': 42, 'error_message': 'Fetch failed'}],
            'page'
        )

        # Verify the decorative image was marked as failed with error message
        image = updater.content_alt_text_update_report[0]['images'][0]
        self.assertEqual(image.get('is_alt_text_updated'), False)
        self.assertEqual(image.get('alt_text_failed_error_message'), 'Fetch failed')

    def test_mark_content_images_failed_skips_skipped_images(self):
        """_mark_content_images_failed should not mark images with action='skip' as failed."""
        payload = [{
            'content_id': 42,
            'content_type': 'page',
            'images': [
                {
                    'image_id': '100',
                    'image_url': 'http://example.com/img1',
                    'action': 'skip',
                    'approved_alt_text': 'ignored',
                    'image_url_for_update': 'http://example.com/img1',
                },
                {
                    'image_id': '101',
                    'image_url': 'http://example.com/img2',
                    'action': 'approve',
                    'approved_alt_text': 'alt text',
                    'image_url_for_update': 'http://example.com/img2',
                }
            ]
        }]
        updater = AltTextUpdate(course_id=1, canvas_api=DummyCanvasAPI(), content_with_alt_text=payload, content_types=[])
        
        # Mark content as failed
        updater._mark_content_images_failed(
            [{'content_id': 42, 'error_message': 'Process error'}],
            'page'
        )

        # Verify skipped image is unchanged
        skipped_img = updater.content_alt_text_update_report[0]['images'][0]
        self.assertNotIn('is_alt_text_updated', skipped_img)
        self.assertNotIn('alt_text_failed_error_message', skipped_img)

        # Verify approved image was marked as failed
        approved_img = updater.content_alt_text_update_report[0]['images'][1]
        self.assertEqual(approved_img.get('is_alt_text_updated'), False)
        self.assertEqual(approved_img.get('alt_text_failed_error_message'), 'Process error')
