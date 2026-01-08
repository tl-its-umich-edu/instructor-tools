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
            course_id=cs.course_id,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=10,
            content_name='A1',
            content_parent_id=None,
        )
        ImageItem.objects.create(
            course_id=cs.course_id,
            content_item=assignment,
            image_id=100,
            image_url='https://example.com/a1.png'
        )
        # image with missing canvas image_id (synthesize from content_id and DB id)
        img_without_id = ImageItem.objects.create(
            course_id=cs.course_id,
            content_item=assignment,
            image_id=None,
            image_url='https://example.com/a1b.png'
        )

        # another content item (different type) should not be returned
        page = ContentItem.objects.create(
            course_id=cs.course_id,
            content_type=ContentItem.CONTENT_TYPE_PAGE,
            content_id=20,
            content_name='P1',
            content_parent_id=None,
        )
        ImageItem.objects.create(
            course_id=cs.course_id,
            content_item=page,
            image_id=200,
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

        # find the image with an explicit canvas image_id
        img_explicit = next(img for img in item['images'] if img['image_url'] == 'https://example.com/a1.png')
        self.assertEqual(img_explicit['image_id'], 100)
        self.assertIsNone(img_explicit['image_alt_text'])

        # find the image that had no canvas image_id and verify the synthesized id
        img_missing = next(img for img in item['images'] if img['image_url'] == 'https://example.com/a1b.png')
        expected_synth = f"{assignment.content_id}-{img_without_id.pk}"
        self.assertEqual(img_missing['image_id'], expected_synth)
        self.assertIsNone(img_missing['image_alt_text'])
