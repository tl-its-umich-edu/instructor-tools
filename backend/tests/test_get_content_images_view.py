from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from backend.canvas_app_explorer.alt_text_helper.views import AltTextContentGetAndUpdateViewSet
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem


User = get_user_model()


class TestGetContentImagesView(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='pw')

    def test_get_content_images_returns_expected_json(self):
        # create course scan and content items with images
        cs = CourseScan.objects.create(course_id=2222)
        assignment = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=10,
            content_name='A1',
            content_parent_id=None,
        )
        img_explicit = ImageItem.objects.create(
            course=cs,
            content_item=assignment,
            image_url='https://example.com/a1.png'
        )
        # image for comparison
        img_without_id = ImageItem.objects.create(
            course=cs,
            content_item=assignment,
            image_url='https://example.com/a1b.png'
        )

        # another content item (different type) should not be returned
        page = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_PAGE,
            content_id=20,
            content_name='P1',
            content_parent_id=None,
        )
        ImageItem.objects.create(
            course=cs,
            content_item=page,
            image_url='https://example.com/p1.png'
        )

        # build request with session course_id and query param
        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_ASSIGNMENT})
        request.user = self.user
        # django test RequestFactory uses a dict-like session we can attach for tests
        request.session = {'course_id': cs.course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('content_items', data)
        self.assertEqual(len(data['content_items']), 1)

        item = data['content_items'][0]
        self.assertEqual(item['content_id'], 10)
        self.assertEqual(item['content_parent_id'], None)
        self.assertEqual(item['content_type'], ContentItem.CONTENT_TYPE_ASSIGNMENT)
        self.assertEqual(len(item['images']), 2)

        # find the image we created first
        img_explicit_resp = next(img for img in item['images'] if img['image_url'] == 'https://example.com/a1.png')
        self.assertEqual(img_explicit_resp['image_id'], img_explicit.id)
        self.assertIsNone(img_explicit_resp['image_alt_text'])

        # find the other image we created
        img_missing_resp = next(img for img in item['images'] if img['image_url'] == 'https://example.com/a1b.png')
        self.assertEqual(img_missing_resp['image_id'], img_without_id.id)
        self.assertIsNone(img_missing_resp['image_alt_text'])

    def test_get_content_images_returns_untitled_when_content_name_is_none(self):
        # create course scan and content item with no name
        cs = CourseScan.objects.create(course_id=3333)
        assignment = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=30,
            content_name=None,  # Explicitly None
            content_parent_id=None,
        )
        ImageItem.objects.create(
            course=cs,
            content_item=assignment,
            image_url='https://example.com/a2.png'
        )

        # build request with session course_id and query param
        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_ASSIGNMENT})
        request.user = self.user
        request.session = {'course_id': cs.course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('content_items', data)
        self.assertEqual(len(data['content_items']), 1)

        item = data['content_items'][0]
        self.assertEqual(item['content_id'], 30)
        self.assertEqual(item['content_type'], ContentItem.CONTENT_TYPE_ASSIGNMENT)
        # Verify content_name defaults to "Untitled : Assignment"
        self.assertEqual(item['content_name'], 'Untitled : Assignment')
