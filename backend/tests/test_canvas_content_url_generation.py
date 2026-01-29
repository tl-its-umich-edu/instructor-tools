from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from unittest.mock import patch
from backend.canvas_app_explorer.utils import generate_canvas_content_url
from backend.canvas_app_explorer.alt_text_helper.views import AltTextContentGetAndUpdateViewSet
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem
from backend import settings


User = get_user_model()


class TestGenerateCanvasContentUrl(TestCase):
    """
    Test the generate_canvas_content_url helper function.
    Tests URL generation for all content types.
    """

    def setUp(self):
        """Set up test data"""
        self.course_id = 12345
        self.canvas_domain = settings.CANVAS_OAUTH_CANVAS_DOMAIN

    def test_generate_assignment_url(self):
        """Test URL generation for assignments"""
        content_id = 100
        url = generate_canvas_content_url(
            course_id=self.course_id,
            content_type='assignment',
            content_id=content_id,
            content_parent_id=None
        )
        expected = f'https://{self.canvas_domain}/courses/{self.course_id}/assignments/{content_id}'
        self.assertEqual(url, expected)

    def test_generate_page_url(self):
        """Test URL generation for pages"""
        content_id = 200
        url = generate_canvas_content_url(
            course_id=self.course_id,
            content_type='page',
            content_id=content_id,
            content_parent_id=None
        )
        expected = f'https://{self.canvas_domain}/courses/{self.course_id}/pages/{content_id}'
        self.assertEqual(url, expected)

    def test_generate_quiz_url(self):
        """Test URL generation for quizzes"""
        content_id = 300
        url = generate_canvas_content_url(
            course_id=self.course_id,
            content_type='quiz',
            content_id=content_id,
            content_parent_id=None
        )
        expected = f'https://{self.canvas_domain}/courses/{self.course_id}/quizzes/{content_id}'
        self.assertEqual(url, expected)

    def test_generate_quiz_question_url(self):
        """Test URL generation for quiz questions"""
        quiz_id = 400
        question_id = 401
        url = generate_canvas_content_url(
            course_id=self.course_id,
            content_type='quiz_question',
            content_id=question_id,
            content_parent_id=quiz_id
        )
        expected = f'https://{self.canvas_domain}/courses/{self.course_id}/quizzes/{quiz_id}/edit/#questions_tab'
        self.assertEqual(url, expected)

    def test_generate_unknown_content_type_url(self):
        """Test URL generation with unknown content type defaults to course overview"""
        content_id = 500
        url = generate_canvas_content_url(
            course_id=self.course_id,
            content_type='unknown_type',
            content_id=content_id,
            content_parent_id=None
        )
        expected = f'https://{self.canvas_domain}/courses/{self.course_id}'
        self.assertEqual(url, expected)

    def test_generate_url_with_large_ids(self):
        """Test URL generation with large ID values"""
        large_course_id = 999999999
        large_content_id = 888888888
        url = generate_canvas_content_url(
            course_id=large_course_id,
            content_type='assignment',
            content_id=large_content_id,
            content_parent_id=None
        )
        expected = f'https://{self.canvas_domain}/courses/{large_course_id}/assignments/{large_content_id}'
        self.assertEqual(url, expected)

    def test_generate_url_with_different_canvas_domain(self):
        """Test URL generation respects the configured Canvas domain"""
        with patch('backend.canvas_app_explorer.utils.settings') as mock_settings:
            mock_settings.CANVAS_OAUTH_CANVAS_DOMAIN = 'custom-canvas.example.edu'
            content_id = 600
            url = generate_canvas_content_url(
                course_id=self.course_id,
                content_type='quiz',
                content_id=content_id,
                content_parent_id=None
            )
            expected = f'https://custom-canvas.example.edu/courses/{self.course_id}/quizzes/{content_id}'
            self.assertEqual(url, expected)


class TestGetContentImagesWithCanvasLinks(TestCase):
    """
    Integration tests for get_content_images view to verify canvas_link_url
    is properly generated and returned in the response.
    """

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='pw')
        self.canvas_domain = settings.CANVAS_OAUTH_CANVAS_DOMAIN

    def test_get_content_images_includes_canvas_link_url_for_assignments(self):
        """Test that canvas_link_url is included for assignment content"""
        course_id = 5000
        content_id = 100
        cs = CourseScan.objects.create(course_id=course_id)
        assignment = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=content_id,
            content_name='Test Assignment',
            content_parent_id=None,
        )
        ImageItem.objects.create(
            course=cs,
            content_item=assignment,
            image_url='https://example.com/image.png'
        )

        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_ASSIGNMENT})
        request.user = self.user
        request.session = {'course_id': course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['content_items']), 1)

        item = data['content_items'][0]
        self.assertEqual(len(item['images']), 1)

        image = item['images'][0]
        expected_url = f'https://{self.canvas_domain}/courses/{course_id}/assignments/{content_id}'
        self.assertEqual(image['canvas_link_url'], expected_url)

    def test_get_content_images_includes_canvas_link_url_for_pages(self):
        """Test that canvas_link_url is included for page content"""
        course_id = 5001
        content_id = 200
        cs = CourseScan.objects.create(course_id=course_id)
        page = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_PAGE,
            content_id=content_id,
            content_name='Test Page',
            content_parent_id=None,
        )
        ImageItem.objects.create(
            course=cs,
            content_item=page,
            image_url='https://example.com/image.png'
        )

        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_PAGE})
        request.user = self.user
        request.session = {'course_id': course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['content_items']), 1)

        item = data['content_items'][0]
        self.assertEqual(len(item['images']), 1)

        image = item['images'][0]
        expected_url = f'https://{self.canvas_domain}/courses/{course_id}/pages/{content_id}'
        self.assertEqual(image['canvas_link_url'], expected_url)

    def test_get_content_images_includes_canvas_link_url_for_quizzes(self):
        """Test that canvas_link_url is included for quiz content"""
        course_id = 5002
        content_id = 300
        cs = CourseScan.objects.create(course_id=course_id)
        quiz = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_QUIZ,
            content_id=content_id,
            content_name='Test Quiz',
            content_parent_id=None,
        )
        ImageItem.objects.create(
            course=cs,
            content_item=quiz,
            image_url='https://example.com/image.png'
        )

        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_QUIZ})
        request.user = self.user
        request.session = {'course_id': course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['content_items']), 1)

        item = data['content_items'][0]
        self.assertEqual(len(item['images']), 1)

        image = item['images'][0]
        expected_url = f'https://{self.canvas_domain}/courses/{course_id}/quizzes/{content_id}'
        self.assertEqual(image['canvas_link_url'], expected_url)

    def test_get_content_images_includes_canvas_link_url_for_quiz_questions(self):
        """Test that canvas_link_url is included for quiz question content"""
        course_id = 5003
        quiz_id = 400
        question_id = 401
        cs = CourseScan.objects.create(course_id=course_id)
        question = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_QUIZ_QUESTION,
            content_id=question_id,
            content_name='Test Question',
            content_parent_id=quiz_id,
        )
        ImageItem.objects.create(
            course=cs,
            content_item=question,
            image_url='https://example.com/image.png'
        )

        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_QUIZ})
        request.user = self.user
        request.session = {'course_id': course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        # When requesting quiz type, both quizzes and quiz_questions are returned
        self.assertEqual(len(data['content_items']), 1)

        item = data['content_items'][0]
        self.assertEqual(len(item['images']), 1)

        image = item['images'][0]
        expected_url = f'https://{self.canvas_domain}/courses/{course_id}/quizzes/{quiz_id}/edit/#questions_tab'
        self.assertEqual(image['canvas_link_url'], expected_url)

    def test_get_content_images_multiple_images_same_content(self):
        """Test that canvas_link_url is the same for multiple images from same content"""
        course_id = 5004
        content_id = 500
        cs = CourseScan.objects.create(course_id=course_id)
        assignment = ContentItem.objects.create(
            course=cs,
            content_type=ContentItem.CONTENT_TYPE_ASSIGNMENT,
            content_id=content_id,
            content_name='Multi-Image Assignment',
            content_parent_id=None,
        )
        # Create multiple images for the same content
        ImageItem.objects.create(
            course=cs,
            content_item=assignment,
            image_url='https://example.com/image1.png'
        )
        ImageItem.objects.create(
            course=cs,
            content_item=assignment,
            image_url='https://example.com/image2.png'
        )

        request = self.factory.get('/alt-text/content-images', {'content_type': ContentItem.CONTENT_TYPE_ASSIGNMENT})
        request.user = self.user
        request.session = {'course_id': course_id}

        view = AltTextContentGetAndUpdateViewSet()
        response = view.get_content_images(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['content_items']), 1)

        item = data['content_items'][0]
        self.assertEqual(len(item['images']), 2)

        expected_url = f'https://{self.canvas_domain}/courses/{course_id}/assignments/{content_id}'
        # Both images should have the same canvas_link_url pointing to the same content
        for image in item['images']:
            self.assertEqual(image['canvas_link_url'], expected_url)
