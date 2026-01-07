from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from backend.canvas_app_explorer.alt_text_helper.views import AltTextContentGetAndUpdateViewSet
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem


User = get_user_model()


class TestGetContentImagesQuiz(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser2', password='pw')

    def test_quiz_type_includes_quiz_questions(self):
        cs = CourseScan.objects.create(course_id=3333)
        quiz = ContentItem.objects.create(
            course_id=cs.course_id,
            content_type=ContentItem.CONTENT_TYPE_QUIZ,
            content_id=1000,
            content_name='Quiz1',
            content_parent_id=None,
        )
        ImageItem.objects.create(
            course_id=cs.course_id,
            content_item=quiz,
            image_id=1000,
            image_url='https://example.com/quiz.png'
        )

        quiz_question = ContentItem.objects.create(
            course_id=cs.course_id,
            content_type=ContentItem.CONTENT_TYPE_QUIZ_QUESTION,
            content_id=1001,
            content_name='Q1',
            content_parent_id=quiz.content_id,
        )
        ImageItem.objects.create(
            course_id=cs.course_id,
            content_item=quiz_question,
            image_id=1001,
            image_url='https://example.com/q1.png'
        )

        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_QUIZ})
        request.user = self.user
        request.session = {'course_id': cs.course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('content_items', data)
        # expect both the quiz and the quiz question to be present
        self.assertEqual(len(data['content_items']), 2)
        types = {item['content_type'] for item in data['content_items']}
        self.assertTrue(ContentItem.CONTENT_TYPE_QUIZ in types)
        self.assertTrue(ContentItem.CONTENT_TYPE_QUIZ_QUESTION in types)
