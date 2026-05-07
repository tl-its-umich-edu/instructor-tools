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


def generate_canvas_content_url(
    course_id: int, 
    content_type: str, 
    content_id: Optional[int] = None, 
    content_parent_id: Optional[int] = None
) -> str:
    """
    Generate a Canvas URL pointing to the source content (assignment, page, quiz, or quiz question).
    
    Handles both required content_id (for specific content) and optional content_id (for content type overviews).
    Supports both 'quiz_question' and 'question' as content type names.
    
    :param course_id: Canvas course ID
    :param content_type: Type of content (assignment, page, quiz, quiz_question, or question)
    :param content_id: ID of the content (optional for type overviews)
    :param content_parent_id: Parent quiz ID for quiz questions
    :return: Full Canvas URL to the content
    """
    canvas_domain = settings.CANVAS_OAUTH_CANVAS_DOMAIN
    base = f'https://{canvas_domain}/courses/{course_id}'
    
    if content_type == 'assignment':
        if content_id:
            return f'{base}/assignments/{content_id}'
        return f'{base}/assignments'
    elif content_type == 'page':
        if content_id:
            # Canvas page URLs use URL-safe slugs, but we can use the page ID with /pages/
            return f'{base}/pages/{content_id}'
        return f'{base}/pages'
    elif content_type == 'quiz':
        if content_id:
            return f'{base}/quizzes/{content_id}'
        return f'{base}/quizzes'
    elif content_type == 'question' or content_type == 'quiz_question':
        # Quiz question URLs point to the quiz edit page's question tab for accurate navigation
        # Supports both 'question' and 'quiz_question' as content type names
        if content_parent_id:
            return f'{base}/quizzes/{content_parent_id}/edit/#questions_tab'
        return f'{base}/quizzes'
    else:
        # Fallback to course overview for unknown types
        return base
