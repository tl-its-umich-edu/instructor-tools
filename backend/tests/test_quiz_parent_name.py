from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from backend.canvas_app_explorer.alt_text_helper.views import AltTextContentGetAndUpdateViewSet
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem


User = get_user_model()


class TestQuizParentName(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='pw')

    def test_quiz_question_includes_parent_name(self):
        """Test that quiz questions include their parent quiz name"""
        # Create course scan
        cs = CourseScan.objects.create(course_id=3333)
        
        # Create a quiz (parent)
        quiz = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_QUIZ,
            content_id=100,
            content_name='Quiz 1',
            content_parent_id=None,
        )
        quiz_img = ImageItem.objects.create(
            course=cs,
            content_item=quiz,
            image_url='https://example.com/quiz1.png'
        )
        
        # Create quiz questions (children of the quiz)
        question1 = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_QUIZ_QUESTION,
            content_id=101,
            content_name='Quiz Question 1',
            content_parent_id=100,  # References the quiz
        )
        q1_img = ImageItem.objects.create(
            course=cs,
            content_item=question1,
            image_url='https://example.com/q1.png'
        )
        
        question2 = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_QUIZ_QUESTION,
            content_id=102,
            content_name='Quiz Question 2',
            content_parent_id=100,  # References the quiz
        )
        q2_img = ImageItem.objects.create(
            course=cs,
            content_item=question2,
            image_url='https://example.com/q2.png'
        )

        # Build request for quiz content type (which includes quiz questions)
        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_QUIZ})
        request.user = self.user
        request.session = {'course_id': cs.course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('content_items', data)
        
        # Should return 3 items: 1 quiz + 2 quiz questions
        self.assertEqual(len(data['content_items']), 3)

        # Find the quiz and quiz questions
        quiz_item = next(item for item in data['content_items'] if item['content_id'] == 100)
        question1_item = next(item for item in data['content_items'] if item['content_id'] == 101)
        question2_item = next(item for item in data['content_items'] if item['content_id'] == 102)

        # Quiz should not have a parent name
        self.assertEqual(quiz_item['content_name'], 'Quiz 1')
        self.assertIsNone(quiz_item['content_parent_id'])
        self.assertIsNone(quiz_item['content_parent_name'])

        # Quiz questions should have parent name
        self.assertEqual(question1_item['content_name'], 'Quiz Question 1')
        self.assertEqual(question1_item['content_parent_id'], 100)
        self.assertEqual(question1_item['content_parent_name'], 'Quiz 1')

        self.assertEqual(question2_item['content_name'], 'Quiz Question 2')
        self.assertEqual(question2_item['content_parent_id'], 100)
        self.assertEqual(question2_item['content_parent_name'], 'Quiz 1')

    def test_quiz_question_without_parent_has_null_parent_name(self):
        """Test that quiz questions without a valid parent have null parent_name"""
        cs = CourseScan.objects.create(course_id=4444)
        
        # Create a quiz question with a parent_id that doesn't exist
        orphan_question = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_QUIZ_QUESTION,
            content_id=201,
            content_name='Orphan Question',
            content_parent_id=999,  # Non-existent parent
        )
        ImageItem.objects.create(
            course=cs,
            content_item=orphan_question,
            image_url='https://example.com/orphan.png'
        )

        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_QUIZ})
        request.user = self.user
        request.session = {'course_id': cs.course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        
        # Should have 1 orphan question
        self.assertEqual(len(data['content_items']), 1)
        
        question_item = data['content_items'][0]
        self.assertEqual(question_item['content_name'], 'Orphan Question')
        self.assertEqual(question_item['content_parent_id'], 999)
        self.assertIsNone(question_item['content_parent_name'])  # Parent doesn't exist
