from typing import Optional
from rest_framework.views import exception_handler
from backend import settings


# https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if 'detail' in response.data:
            # Move contents of detail to message
            response.data['message'] = response.data['detail']
            del response.data['detail']
        # Add status code
        response.data['status_code'] = response.status_code
    return response


def generate_canvas_content_url(course_id: int, content_type: str, content_id: int, content_parent_id: Optional[int] = None) -> str:
    """
    Generate a Canvas URL pointing to the source content (assignment, page, or quiz).
    
    :param course_id: Canvas course ID
    :param content_type: Type of content (assignment, page, quiz, quiz_question)
    :param content_id: ID of the content
    :param content_parent_id: Parent quiz ID for quiz questions
    :return: Full Canvas URL to the content
    """
    canvas_domain = settings.CANVAS_OAUTH_CANVAS_DOMAIN
    
    if content_type == 'assignment':
        return f'https://{canvas_domain}/courses/{course_id}/assignments/{content_id}'
    elif content_type == 'page':
        # Canvas page URLs use URL-safe slugs, but we can use the page ID with /pages/
        return f'https://{canvas_domain}/courses/{course_id}/pages/{content_id}'
    elif content_type == 'quiz':
        return f'https://{canvas_domain}/courses/{course_id}/quizzes/{content_id}'
    elif content_type == 'quiz_question':
        # Quiz question URLs point to the quiz edit page's question tab
        return f'https://{canvas_domain}/courses/{course_id}/quizzes/{content_parent_id}/edit/#questions_tab'
    else:
        # Fallback to course overview
        return f'https://{canvas_domain}/courses/{course_id}'
