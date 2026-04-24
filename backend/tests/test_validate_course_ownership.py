from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from backend.canvas_app_explorer.alt_text_helper.views import AltTextContentGetAndUpdateViewSet
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem

User = get_user_model()

COURSE_ID = 1001
OTHER_COURSE_ID = 9999


class TestValidateCourseOwnership(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='pw')
        self.view = AltTextContentGetAndUpdateViewSet()

        self.scan = CourseScan.objects.create(course_id=COURSE_ID)
        self.other_scan = CourseScan.objects.create(course_id=OTHER_COURSE_ID)

        self.content_item = ContentItem.objects.create(
            course_scan=self.scan,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=100,
            content_name='Assignment 1',
        )
        self.image_item = ImageItem.objects.create(
            content_item=self.content_item,
            image_url='https://example.com/img.png',
        )

        self.other_content_item = ContentItem.objects.create(
            course_scan=self.other_scan,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=200,
            content_name='Other Course Assignment',
        )
        self.other_image_item = ImageItem.objects.create(
            content_item=self.other_content_item,
            image_url='https://example.com/other.png',
        )

    def _make_payload(self, content_item, image_item):
        return [{
            'id': content_item.id,
            'content_id': content_item.content_id,
            'content_name': content_item.content_name,
            'content_parent_id': None,
            'content_type': content_item.content_type,
            'images': [{'image_id': image_item.id, 'image_url': image_item.image_url, 'action': 'approve'}],
        }]

    # --- pass cases ---

    def test_valid_content_and_images_returns_none(self):
        """Valid content and image IDs belonging to the course return None (no error)."""
        payload = self._make_payload(self.content_item, self.image_item)
        result = self.view._validate_course_ownership(payload, COURSE_ID, [ContentItem.CONTENT_TYPE_ASSIGNMENT])
        self.assertIsNone(result)

    def test_empty_payload_returns_none(self):
        """Empty payload with no IDs returns None."""
        result = self.view._validate_course_ownership([], COURSE_ID, [ContentItem.CONTENT_TYPE_ASSIGNMENT])
        self.assertIsNone(result)

    def test_payload_with_no_images_returns_none(self):
        """Content item with no images returns None."""
        payload = [{
            'id': self.content_item.id,
            'content_id': self.content_item.content_id,
            'content_name': self.content_item.content_name,
            'content_parent_id': None,
            'content_type': ContentItem.CONTENT_TYPE_ASSIGNMENT,
            'images': [],
        }]
        result = self.view._validate_course_ownership(payload, COURSE_ID, [ContentItem.CONTENT_TYPE_ASSIGNMENT])
        self.assertIsNone(result)

    # --- failure cases ---

    def test_content_id_from_other_course_returns_400(self):
        """Content ID belonging to a different course returns a 400 response."""
        payload = self._make_payload(self.other_content_item, self.image_item)
        result = self.view._validate_course_ownership(payload, COURSE_ID, [ContentItem.CONTENT_TYPE_ASSIGNMENT])
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)
        self.assertIn('Content IDs', result.data['message'])

    def test_image_id_from_other_course_returns_400(self):
        """Image ID belonging to a different course returns a 400 response."""
        payload = [{
            'id': self.content_item.id,
            'content_id': self.content_item.content_id,
            'content_name': self.content_item.content_name,
            'content_parent_id': None,
            'content_type': ContentItem.CONTENT_TYPE_ASSIGNMENT,
            'images': [{'image_id': self.other_image_item.id, 'image_url': self.other_image_item.image_url, 'action': 'approve'}],
        }]
        result = self.view._validate_course_ownership(payload, COURSE_ID, [ContentItem.CONTENT_TYPE_ASSIGNMENT])
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)
        self.assertIn('Image IDs', result.data['message'])

    def test_content_id_with_wrong_content_type_returns_400(self):
        """Content ID that exists but under a different content type returns 400."""
        # content_item is ASSIGNMENT; querying with PAGE type should treat it as invalid
        payload = self._make_payload(self.content_item, self.image_item)
        result = self.view._validate_course_ownership(payload, COURSE_ID, [ContentItem.CONTENT_TYPE_PAGE])
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)
        self.assertIn('Content IDs', result.data['message'])

    def test_nonexistent_content_id_returns_400(self):
        """A content ID that does not exist in the DB returns 400."""
        payload = [{
            'id': 999999,
            'content_id': 999999,
            'content_name': 'Ghost',
            'content_parent_id': None,
            'content_type': ContentItem.CONTENT_TYPE_ASSIGNMENT,
            'images': [],
        }]
        result = self.view._validate_course_ownership(payload, COURSE_ID, [ContentItem.CONTENT_TYPE_ASSIGNMENT])
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)
        self.assertIn('Content IDs', result.data['message'])

    def test_nonexistent_image_id_returns_400(self):
        """An image ID that does not exist in the DB returns 400."""
        payload = [{
            'id': self.content_item.id,
            'content_id': self.content_item.content_id,
            'content_name': self.content_item.content_name,
            'content_parent_id': None,
            'content_type': ContentItem.CONTENT_TYPE_ASSIGNMENT,
            'images': [{'image_id': 999999, 'image_url': 'https://example.com/ghost.png', 'action': 'approve'}],
        }]
        result = self.view._validate_course_ownership(payload, COURSE_ID, [ContentItem.CONTENT_TYPE_ASSIGNMENT])
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)
        self.assertIn('Image IDs', result.data['message'])
