from django.test import TestCase
from backend.canvas_app_explorer.serializers import ContentQuerySerializer
from backend.canvas_app_explorer.models import ContentItem


class TestContentQuerySerializer(TestCase):
    def test_valid_content_types(self):
        for content_type, _ in ContentItem.CONTENT_TYPE_CHOICES:
            serializer = ContentQuerySerializer(data={'content_type': content_type})
            self.assertTrue(serializer.is_valid(), msg=f"expected {content_type} to be valid; errors: {serializer.errors}")
            self.assertEqual(serializer.validated_data['content_type'], content_type)

    def test_invalid_content_type(self):
        serializer = ContentQuerySerializer(data={'content_type': 'invalid_type'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('content_type', serializer.errors)
