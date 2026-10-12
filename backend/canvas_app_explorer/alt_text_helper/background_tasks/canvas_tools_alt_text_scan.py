import asyncio
import logging
from django.db import transaction
from typing import List, Dict, Any, Optional, TypeVar, Callable, Union, TypeGuard
from asgiref.sync import async_to_sync
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.utils import DatabaseError
from bs4 import BeautifulSoup
from PIL import Image
from rest_framework.request import Request
from canvasapi.exceptions import CanvasException
from canvasapi.course import Course
from canvasapi.quiz import Quiz
from canvasapi import Canvas
from canvas_oauth.exceptions import InvalidOAuthReturnError
from canvas_oauth.models import CanvasOAuth2Token

from backend import settings
from backend.canvas_app_explorer.canvas_lti_manager.django_factory import DjangoCourseLtiManagerFactory
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem, CourseScanStatus
from backend.canvas_app_explorer.alt_text_helper.process_content_images import ProcessContentImages
from backend.canvas_app_explorer.alt_text_helper.background_tasks.error_logging import log_course_scan_errors
from backend.canvas_app_explorer.utils import generate_canvas_content_url
from backend.canvas_app_explorer.alt_text_helper.background_tasks.types import (
    ContentItemWithImages,
    CourseScanError,
    ScanExtractionResult,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")
R = TypeVar("R")

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')
PER_PAGE = 100
IMAGE_EXTENSIONS = tuple(Image.registered_extensions().keys())
semaphore = asyncio.Semaphore(10)

CONTENT_FETCH_STATE_SUCCESS = 'success'
CONTENT_FETCH_STATE_MIXED = 'mixed'
CONTENT_FETCH_STATE_ERROR = 'error'


def fetch_and_scan_course(task: Dict[str, Any]):
    """Run the end-to-end background scan for a course.

    This task orchestrates Canvas client setup, content/image discovery,
    persistence of scan results, AI alt-text generation, and final scan status
    updates (COMPLETED or FAILED).
    """
    logger.info(f"Starting fetch_and_scan_course for course_id: {task.get('course_id')}")

    try:
        course_scan_id = int(task.get('course_scan_id'))
        course_id = int(task.get('course_id'))
        update_course_scan(course_scan_id, CourseScanStatus.RUNNING, course_id=course_id)
        # Fetch course content using the manager
        user_id = task.get('user_id')
        req_user: User = get_user_model().objects.get(pk=user_id)
        canvas_callback_url = task.get('canvas_callback_url')
        request = _create_background_request(req_user, canvas_callback_url, course_id)
        
        canvas_api, bearer_token = canvas_setup(course_scan_id, course_id, request)

        # Fetch full course details to ensure attributes like course_code are present for logging
        course: Course = Course(canvas_api._Canvas__requester, {'id': course_id})

        results = async_to_sync(get_courses_images)(course)
        success_content_with_images, content_errors = unpack_content_images(
            results,
            course_scan_id,
            course_id,
        )
        save_results_status: bool | CourseScanError = save_scan_content_fetch_items(
            course_scan_id,
            course_id,
            success_content_with_images,
        )

        if _is_course_scan_error(save_results_status):
            content_errors.append(save_results_status)

        content_fetch_result: bool | list[CourseScanError] = content_errors if content_errors else True

        image_process_result: bool | list[CourseScanError] = retrieve_and_store_alt_text(course_scan_id, course_id, bearer_token=bearer_token)

        # Determine final status: FAILED if either stage had errors, else COMPLETED
        if content_fetch_result is not True or image_process_result is not True:
            merged_errors = _merge_error_results(content_fetch_result, image_process_result)
            update_course_scan(
                course_scan_id,
                CourseScanStatus.FAILED,
                course_id=course_id,
                errors=merged_errors
            )
        else:
            update_course_scan(course_scan_id, CourseScanStatus.COMPLETED, course_id=course_id)
    except InvalidOAuthReturnError as e:
        logger.error(f"OAuth token error in fetch_and_scan_course for course_id {course_id}: {e}")
        oauth_error: CourseScanError = {
            'type': 'token_error',
            'title': 'Course',
            'error': e,
            'canvas_url': generate_canvas_content_url(course_id, 'course'),
        }
        update_course_scan(course_scan_id, CourseScanStatus.FAILED, course_id=course_id, errors=[oauth_error])
    except Exception as e:
        logger.error(f"Unexpected error in fetch_and_scan_course for course_id {course_id}: {e}")
        unexpected_error: CourseScanError = {
            'type': 'unexpected_error',
            'title': 'Course',
            'error': e,
            'canvas_url': generate_canvas_content_url(course_id, 'course'),
        }
        update_course_scan(course_scan_id, CourseScanStatus.FAILED, course_id=course_id, errors=[unexpected_error])

def canvas_setup(course_scan_id, course_id, request):
    try:
        manager = MANAGER_FACTORY.create_manager(request)
        canvas_api: Canvas = manager.canvas_api
        bearer_token = manager.api_key
        return canvas_api, bearer_token
    except InvalidOAuthReturnError as e:
        logger.error(f"Error creating Canvas API for course_scan_id {course_scan_id}, course_id {course_id}: {e}")
        CanvasOAuth2Token.objects.filter(user=request.user).delete()
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during Canvas API setup for course_scan_id {course_scan_id}, course_id {course_id}: {e}")
        raise e

def _merge_error_results(*results: Union[bool, List[CourseScanError]]) -> List[CourseScanError]:
    """
    Merge multiple error results into a single list of CourseScanError.
    
    Handles both list and single error formats, extracting errors from each result.
    :param results: Variable args of Union[bool, List[CourseScanError]] to merge
    :return: Flattened list of all errors
    """
    merged = []
    for result in results:
        if isinstance(result, list):
            merged.extend(result)
        elif result is not True:
            merged.append(result)
    return merged


def _is_course_scan_error(obj: Any) -> TypeGuard[CourseScanError]:
    return (
        isinstance(obj, dict)
        and isinstance(obj.get('type'), str)
        and isinstance(obj.get('title'), str)
        and isinstance(obj.get('error'), Exception)
        and isinstance(obj.get('canvas_url'), str)
    )


def _create_background_request(req_user: User, canvas_callback_url: str, course_id: int) -> Request:
    logger.info(f"Creating background request - User: {req_user}, Course ID: {course_id}, Callback URL: {canvas_callback_url}")
    # Create a request factory and build the request for background task usage.
    # course_id is passed via request.course_id (not session).
    factory = RequestFactory()
    request: Request = factory.get('/oauth/oauth-callback')
    request.user = req_user
    request.course_id = course_id
    request.build_absolute_uri = lambda path: canvas_callback_url
    logger.info("Background request object: %s", request)
    return request

async def get_courses_images(course: Course) -> List[List[Union[ContentItemWithImages, CourseScanError]]]:
    results = await asyncio.gather(
        fetch_content_items_async(get_assignments, course),
        fetch_content_items_async(get_pages, course),
        fetch_content_items_async(get_quizzes, course),
        return_exceptions=True,
    )
    logger.info("raw results from gather course images: %s", results)
    return results
    
def retrieve_and_store_alt_text(course_scan_id: int, course_id: int, bearer_token: Optional[str] = None) -> Union[bool, List[CourseScanError]]:
    """
    Retrieve alt text for images in the given course scan using AI processor.
    The images for the course need to have been processed first to get the image URLs.

    :param course_scan_id: CourseScan ID to scope images via ContentItem FK
    :type course_scan_id: int
    :param bearer_token: Optional bearer token to pass directly to the image fetcher for Authorization
    :return: True if alt text retrieval succeeded, or list of CourseScanError objects if failed
    :rtype: Union[bool, List[CourseScanError]]
    """
    process_content_images = ProcessContentImages(
        course_scan_id=course_scan_id,
        course_id=course_id,
        bearer_token=bearer_token,
    )
    image_process_state = process_content_images.retrieve_images_with_alt_text()
    return image_process_state

def unpack_content_images(
    results: list[list[ContentItemWithImages | CourseScanError]],
    course_scan_id: int,
    course_id: int
) -> ScanExtractionResult:
    """
    Unpack async results, filter success and errors.
    
    """
    assignments, pages, quizzes = results
    combined: list[ContentItemWithImages | CourseScanError] = assignments + pages + quizzes
    logger.info("Combined items count: %s", len(combined))

    success_content_with_images: list[ContentItemWithImages] = []
    errors_to_log: list[CourseScanError] = []

    for item in combined:

        # Handle complete fetch failures first (e.g., assignment/page/quiz endpoint failures)
        # returned directly as CourseScanError-like dicts.
        if _is_course_scan_error(item):
            errors_to_log.append(item)
            continue

        images = item.get('images')
        if not isinstance(images, list) or len(images) == 0:
            continue

        nested_errors = [img for img in images if _is_course_scan_error(img)]
        if nested_errors:
            for img_error in nested_errors:
                errors_to_log.append(img_error)
            continue

        if all(isinstance(img, str) for img in images):
            success_content_with_images.append(item)

    logger.info(
        "course_scan_id: %s, course_id: %s success content: %s, errors to log: %s",
        course_scan_id,
        course_id,
        len(success_content_with_images),
        len(errors_to_log),
    )
    return success_content_with_images, errors_to_log


def update_course_scan(course_scan_id: int, status: CourseScanStatus, course_id: int = None, errors: Optional[List[CourseScanError]] = None) -> bool:
    """
    Update a CourseScan record with the given status and log accordingly.
    
    When status is FAILED, persists any provided errors to the database via centralized logging.
    Error message is automatically constructed from the errors list when provided.
    
    :param course_scan_id: CourseScan ID
    :param status: status of the scan (CourseScanStatus enum)
    :param course_id: Course ID for logging purposes (required)
    :param errors: Optional list of CourseScanError objects to persist when status is FAILED
    :return: True if update succeeded, False otherwise
    """
    try:
        obj = CourseScan.objects.get(id=course_scan_id)
        obj.status = status.value
        obj.save()
        log_context = f"course_scan_id={course_scan_id}, course_id={course_id}"
        if status == CourseScanStatus.FAILED:
            # Construct error message from errors list
            if errors:
                error_summary = "; ".join([f"{e.get('type')}: {str(e.get('error'))}" for e in errors])
                logger.error(f"Scan marked as FAILED for {log_context}. Errors: {error_summary}")
                # Centralized error logging: persist errors to database
                log_course_scan_errors(course_scan_id, errors)
            else:
                logger.error(f"Scan marked as FAILED for {log_context}")
        elif status == CourseScanStatus.COMPLETED:
            logger.info(f"Scan completed successfully for {log_context}")
        else:
            logger.warning(f"Scan status updated to {status.value} for {log_context}")
        return True
    except (DatabaseError, Exception) as e:
        log_context = f"course_scan_id={course_scan_id}, course_id={course_id}"
        logger.error(f"Error updating CourseScan {log_context} to status {status.value}: {e}")
        # Log the update error to database
        update_error: CourseScanError = {
            'type': 'course_scan_update_error',
            'title': 'Course',
            'error': e,
            'canvas_url': generate_canvas_content_url(course_id, 'course') if course_id else 'N/A',
        }
        log_course_scan_errors(course_scan_id, [update_error])
        return False

def save_scan_content_fetch_items(course_scan_id: int, course_id: int, items: List[ContentItemWithImages]) -> bool | CourseScanError:
    """
    Save the scan results into the database within a transaction.
    Creates ContentItem and ImageItem records scoped to the provided course_scan_id
    without deleting records from prior scans for the course.
    Also updates the CourseScan.total_image_count with the total number of images found.
    Expects success-only content items (image payloads as URL strings), and persists
    ContentItem/ImageItem records for those entries.
    
    :param course_scan_id: CourseScan ID
    :type course_scan_id: int
    :param course_id: Course ID
    :type course_id: int
    :param items: List of content items with images
    :type items: List[ContentItemWithImages]
    :return: True if successful, CourseScanError dict if failed
    :rtype: Union[bool, CourseScanError]
    """
    try:
        with transaction.atomic():
            valid_items = items

            # Calculate total image count across valid items only.
            total_image_count = sum(
                len(item.get('images', []))
                for item in valid_items
            )
            
            for item in valid_items:
                content_item = ContentItem.objects.create(
                    course_scan_id=course_scan_id,
                    content_type=item.get('type'),
                    content_id=item.get('id'),
                    content_name=item.get('name'),
                    content_parent_id=item.get('content_parent_id')
                )
                
                for img in item['images']:
                    image_url = img
                    logger.debug(f"Saving ImageItem - URL: {image_url}")
                    ImageItem.objects.create(
                        content_item=content_item,
                        image_url=image_url
                    )
            
            # Update the CourseScan with the total image count
            course_scan = CourseScan.objects.get(id=course_scan_id)
            course_scan.total_image_count = total_image_count
            course_scan.save()
            logger.info(f"Updated course_scan_id {course_scan_id} with total_image_count: {total_image_count}")
            return True

    except (DatabaseError, Exception) as e:
        error_msg = f"Error in save_scan_results transaction for course_scan_id {course_scan_id}, course_id {course_id}: {e}"
        logger.error(error_msg)
        # Return CourseScanError to propagate failure state to caller
        error_result: CourseScanError = {
            'type': 'content_database_save',
            'title': 'Course',
            'error': e,
            'canvas_url': generate_canvas_content_url(course_id, 'course'),
        }
        return error_result
  
async def fetch_content_items_async(fn: Callable[[T], R], ctx: T) -> Union[R, Exception]:
    """
   Generic async wrapper that runs the synchronous `fn(course|quiz)` in a thread and
   returns a list (or empty list on error). `fn` should be a callable like
   `get_assignments`, `get_pages`,  `get_quizzes`, `get_quiz_questions` that 
   accepts a Course or Quiz and returns a list.
    """
    try:
        return await asyncio.to_thread(fn, ctx)
    except (CanvasException, Exception) as e:
        logger.error("Error fetching content items using %s: %s", getattr(fn, '__name__', str(fn)), e)
        return e


def get_assignments(course: Course) -> List[Union[ContentItemWithImages, CourseScanError]]:
    """
    Synchronously fetches assignments for a given course using canvas_api.get_assignments().
    """
    try:
        logger.info(f"Fetching assignments for course {course.id}.")
        assignments = list(course.get_assignments(per_page=PER_PAGE))
        logger.info(f"Processing {len(assignments)} assignments after fetching.")
        images_from_assignments: List[ContentItemWithImages] = []
        for assignment in assignments:
            # Use getattr to safely check for quiz_id attribute
            quiz_id = getattr(assignment, 'quiz_id', None)
            if quiz_id:
                # skip quiz assignments since quizzes are fetched separately
                logger.info(f"Skipping quiz assignment ID: {assignment.id}, Title: {assignment.name}, quiz_id: {quiz_id}")
                continue
            logger.info(f"Assignment ID: {assignment.id}, Name: {assignment.name}")

            # Extract images from assignment description
            images_from_assignments = append_image_items(
                images_from_assignments,
                assignment.id,
                assignment.name,
                extract_images_from_html(assignment.description),
                'assignment',
                None)
        return images_from_assignments
    except (CanvasException, Exception) as e:
        logger.error(f"Error fetching assignments for course {course.id}: {e}")
        fetch_error: CourseScanError = {
            'type': 'assignment',
            'title': 'assignments',
            'error': e,
            'canvas_url': generate_canvas_content_url(course.id, 'assignment'),
        }
        return [fetch_error]
 
def get_pages(course: Course) -> List[Union[ContentItemWithImages, CourseScanError]]:
    """
    Synchronously fetches pages for a given course using canvas_api.get_pages().
    """

    try:
        logger.info(f"Fetching pages for course {course.id}.")
        pages = list(course.get_pages(include=['body'], per_page=PER_PAGE))

        logger.info(f" Processing {len(pages)} pages after fetching.")
        images_from_pages: List[ContentItemWithImages] = []
        for page in pages:
            logger.info(f"Processing Page ID: {page.page_id}, Title: {page.title}")
            # Extract images from page body
            images_from_pages = append_image_items(
                images_from_pages,
                page.page_id,
                page.title,
                extract_images_from_html(page.body),
                'page',
                None)
        return images_from_pages
    except (CanvasException, Exception) as e:
        logger.error(f"Error fetching pages for course {course.id}: {e}")
        fetch_error: CourseScanError = {
            'type': 'page',
            'title': 'pages',
            'error': e,
            'canvas_url': generate_canvas_content_url(course.id, 'page'),
        }
        return [fetch_error]


def get_quizzes(course: Course) -> List[Union[ContentItemWithImages, CourseScanError]]:
    """
    Synchronously fetches quizzes for a given course using canvas_api.get_quizzes().
    """

    try:
        logger.info(f"Fetching quizzes for course {course.id}.")
        quizzes: List[Quiz] = list(course.get_quizzes(per_page=PER_PAGE))

        images_from_quizzes: List[ContentItemWithImages] = []
        for quiz in quizzes:
            # Extract images from quiz description
            images_from_quizzes = append_image_items(
                images_from_quizzes,
                quiz.id,
                quiz.title,
                extract_images_from_html(getattr(quiz, 'description', '')),
                'quiz',
                None)
        logger.info(f"Fetched {len(quizzes)} quizzes. Now fetching questions for quizzes.")
        quiz_question_results = async_to_sync(get_quiz_questions)(quizzes)

        mapped_quiz_question_results: List[List[Union[ContentItemWithImages, CourseScanError]]] = []
        for quiz_obj, result in zip(quizzes, quiz_question_results):
            if isinstance(result, Exception):
                mapped_quiz_question_results.append([
                    {
                        'type': 'quiz_question',
                        'title': getattr(quiz_obj, 'title', 'Quiz'),
                        'error': result,
                        'canvas_url': generate_canvas_content_url(
                            course.id,
                            'quiz_question',
                            content_id=None,
                            content_parent_id=getattr(quiz_obj, 'id', None),
                        ),
                    }
                ])
            else:
                mapped_quiz_question_results.append(result)

        return process_quiz_with_questions(images_from_quizzes, mapped_quiz_question_results)
    except (CanvasException, Exception) as e:
        logger.error(f"Errors fetching Quizzes for course {course.id}: {e}")
        fetch_error: CourseScanError = {
            'type': 'quiz',
            'title': 'quizzes',
            'error': e,
            'canvas_url': generate_canvas_content_url(course.id, 'quiz'),
        }
        return [fetch_error]

def process_quiz_with_questions(
    quiz: List[ContentItemWithImages],
    questions: List[List[Union[ContentItemWithImages, CourseScanError]]]) -> List[Union[ContentItemWithImages, CourseScanError]]:
    """
    Process a quiz and its questions to extract images from the quiz description and questions.
    """
    merged_question_items = [
        item
        for group in questions
        for item in (group if isinstance(group, list) else [group])
    ]
    return quiz + merged_question_items

async def get_quiz_questions(quizzes: List[Quiz]) -> List[Union[List[ContentItemWithImages], Exception]]:
    async with semaphore:
        quiz_q_tasks = [fetch_content_items_async(get_quiz_questions_sync, quiz) for quiz in quizzes]
        return await asyncio.gather(*quiz_q_tasks, return_exceptions=True)

def get_quiz_questions_sync(quiz: Quiz) -> List[ContentItemWithImages]:

    logger.info(f"Fetching questions for quiz ID: {quiz.id}, Title: {quiz.title}")
    images_from_questions: List[ContentItemWithImages] = []
    try:
        questions = list(quiz.get_questions(per_page=PER_PAGE))
        logger.info(f"Fetched {len(questions)} questions for quiz ID: {quiz.id}. Processing questions for images.")
        for question in questions:
            # Extract images from quiz question text
            images_from_questions = append_image_items(
                images_from_questions,
                question.id,
                question.question_name,
                extract_images_from_html(getattr(question, 'question_text', '')),
                'quiz_question',
                quiz.id)

        return images_from_questions
    except (CanvasException, Exception) as e:
        logger.error(f"Errors fetching quiz {quiz.id}:{quiz.title} questions due {e}")
        raise e


def extract_images_from_html(html_content: str) -> List[str]:
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, "html.parser")
    extracted_image_urls: List[str] = []
    image_extensions = IMAGE_EXTENSIONS
    for img in soup.find_all("img"):
        logger.info(f"Processing img tag: {img}")
        img_src = img.get("src")
        img_alt = (img.get("alt") or "").strip()
        img_role = (img.get("role") or "").strip().lower()

        # ignore images without src
        if not img_src:
            logger.info("Skipping img tag without src attribute.")
            continue
        # Skip decorative/presentation images
        if img_role == "presentation":
            continue
        # Skip images that already have descriptive alt text (non-empty alt that doesn't look like a filename)
        if img_alt and not img_alt.lower().endswith(image_extensions):
            continue

        extracted_image_urls.append(img_src)

    if extracted_image_urls:
        logger.info(extracted_image_urls)
    return extracted_image_urls

# Helper function to append image items if images exist
def append_image_items(
        images_list: List[ContentItemWithImages],
        content_id: int,
        content_name: str,
        images: List[str],
        content_type: str,
        content_parent_id: Optional[int]) -> List[ContentItemWithImages]:
    """
    Append a content item with extracted images to the images list.
    
    :param images_list: Accumulating list of content items with images
    :param content_id: Content item ID (assignment/page/quiz/question ID)
    :param content_name: Content item name (title/description)
    :param images: List[str]
    :param content_type: Type of content ('assignment', 'page', 'quiz', 'quiz_question')
    :param content_parent_id: Optional parent content ID (e.g., quiz_id for quiz_question)
    :return: Updated images_list with new content item appended if images non-empty
    """
    # check if images list is not empty before appending
    if len(images) > 0:
        images_list.append({
            'id': content_id,
            'name': content_name,
            'images': images,
            'type': content_type,
            'content_parent_id': content_parent_id
            })
    return images_list


