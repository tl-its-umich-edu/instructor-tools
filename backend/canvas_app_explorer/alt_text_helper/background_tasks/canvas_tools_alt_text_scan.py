import asyncio
import logging
from urllib import request
from django.db import transaction
from urllib.parse import urlparse, parse_qs, urlencode
from typing import List, Dict, Any, Optional, TypeVar, Callable, Union
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
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem, CourseScanStatus
from backend.canvas_app_explorer.alt_text_helper.process_content_images import ProcessContentImages
from backend.canvas_app_explorer.decorators import log_execution_time
from backend.canvas_app_explorer.alt_text_helper.background_tasks.types import (
    CanvasManagerSetupError,
    ContentItemWithImages,
    CourseFetchError,
    ImageEntry,
    QuizQuestionFetchError,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")
R = TypeVar("R")

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')
PER_PAGE = 100
IMAGE_EXTENSIONS = tuple(Image.registered_extensions().keys())
semaphore = asyncio.Semaphore(10)


@log_execution_time
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
        
        try:
            manager = MANAGER_FACTORY.create_manager(request)
            canvas_api: Canvas = manager.canvas_api
            bearer_token = manager.api_key
        except (InvalidOAuthReturnError, Exception) as e:
            setup_error: CanvasManagerSetupError = {
                'type': 'canvas_manager_setup_error',
                'course_id': course_id,
                'course_scan_id': course_scan_id,
                'error': e,
            }
            logger.error(f"Error creating Canvas API for course_id {setup_error['course_id']}: {setup_error['error']}:{setup_error}")
            update_course_scan(course_scan_id, CourseScanStatus.FAILED, f"Error creating Canvas API for course_id {course_id}: {e}", course_id=course_id)
            CanvasOAuth2Token.objects.filter(user=request.user).delete()
            return

        # Fetch full course details to ensure attributes like course_code are present for logging
        course: Course = Course(canvas_api._Canvas__requester, {'id': course_id})

        results = async_to_sync(get_courses_images)(course)
        state_of_content_fetch: bool = unpack_and_store_content_images(results, course, course_scan_id, course_id)

        # this check is helping not to move to alt text retrieval if there was an error in fetching content images
        if not state_of_content_fetch:
            update_course_scan(course_scan_id, CourseScanStatus.FAILED, f"Failed to fetch content images for course_id {course_id}. Marking scan as FAILED.", course_id=course_id)
            return
        
        try:
            retrieve_and_store_alt_text(course_scan_id, course_id, bearer_token=bearer_token)
        except ImageContentExtractionException as e:
            logger.error(f"ImageContentExtractionException while processing alt text for course_id {course_id}: {e}")
            update_course_scan(course_scan_id, CourseScanStatus.FAILED, f"ImageContentExtractionException while processing alt text for course_id {course_id}: {e}", course_id=course_id)
            return

        # Update that the course scan is completed
        update_course_scan(course_scan_id, CourseScanStatus.COMPLETED, course_id=course_id)
    except Exception as e:
        logger.error(f"Unexpected error in fetch_and_scan_course for course_id {course_id}: {e}")
        update_course_scan(course_scan_id, CourseScanStatus.FAILED, f"Unexpected error in fetch_and_scan_course for course_id {course_id}: {e}", course_id=course_id)


    

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

async def get_courses_images(course: Course) -> List[
    Union[
        List[Union[ContentItemWithImages, CourseFetchError]],
        List[Union[ContentItemWithImages, CourseFetchError]],
        List[Union[ContentItemWithImages, QuizQuestionFetchError, CourseFetchError]],
        Exception,
    ]
]:
    results = await asyncio.gather(
        fetch_content_items_async(get_assignments, course),
        fetch_content_items_async(get_pages, course),
        fetch_content_items_async(get_quizzes, course),
        return_exceptions=True,
    )
    logger.info("raw results from gather course images: %s", results)
    return results
    
def retrieve_and_store_alt_text(course_scan_id: int, course_id: int, bearer_token: Optional[str] = None):
    """
    Retrieve alt text for images in the given course scan using AI processor.
    The images for the course need to have been processed first to get the image URLs.

    :param course_scan_id: CourseScan ID to scope images via ContentItem FK
    :type course_scan_id: int
    :param bearer_token: Optional bearer token to pass directly to the image fetcher for Authorization
    """
    process_content_images = ProcessContentImages(
        course_scan_id=course_scan_id,
        course_id=course_id,
        bearer_token=bearer_token,
    )
    images_with_alt_text = process_content_images.retrieve_images_with_alt_text()
    return images_with_alt_text

def unpack_and_store_content_images(
    results: List[
        Union[
            List[Union[ContentItemWithImages, CourseFetchError]],
            List[Union[ContentItemWithImages, CourseFetchError]],
            List[Union[ContentItemWithImages, QuizQuestionFetchError, CourseFetchError]],
            Exception,
        ]
    ],
    course: Course,
    course_scan_id: int,
    course_id: int) -> bool:
     # unpack results (assignments, pages) and handle exceptions returned by gather. gather maintain call order
    assignments, pages, quizzes = results

    # Simple error check: return True if result is an Exception or contains any Exception entries
    def _has_fetch_error(result) -> bool:
        if isinstance(result, Exception):
            return True
        if isinstance(result, list):
            for item in result:
                if isinstance(item, Exception):
                    return True
                if isinstance(item, dict) and item.get('type') in {
                    'assignment_fetch_error',
                    'page_fetch_error',
                    'quiz_fetch_error',
                    'quiz_question_error',
                }:
                    return True
        return False

    error_when_fetching_images = any(_has_fetch_error(r) for r in (assignments, pages, quizzes))

    if error_when_fetching_images:
        update_course_scan(course_scan_id, CourseScanStatus.FAILED, course_id=course_id)
        return False
    
    combined = assignments + pages + quizzes
    logger.debug("Combined items count: %s", combined)
    # Filter to only those content with images with alt text
    filtered_content_with_images = [
        item for item in combined
        if isinstance(item.get('images'), list) and len(item.get('images')) > 0
    ]

    logger.debug("Items before filter: %d; after filter (has images): %d", len(combined), len(filtered_content_with_images))
    logger.info(f"course_scan_id: {course_scan_id}, course_id: {course.id} items with images: {filtered_content_with_images}")

    # DB call to persist initial ContentItem and ImageItem records
    save_scan_results(course_scan_id, course.id, filtered_content_with_images)
    return True

def update_course_scan(course_scan_id: int, status: CourseScanStatus, error_message: Optional[str] = None, course_id: Optional[int] = None) -> None:
    """
    Update a CourseScan record with the given status and log accordingly.
    
    :param course_scan_id: CourseScan ID
    :param status: status of the scan (CourseScanStatus enum)
    :param error_message: Optional error message to log when status is FAILED
    :param course_id: Optional course ID for logging purposes
    """
    try:
        obj = CourseScan.objects.get(id=course_scan_id)
        obj.status = status.value
        obj.save()
        log_context = f"course_scan_id={course_scan_id}, course_id={obj.course_id}"
        if status == CourseScanStatus.FAILED:
            logger.error(error_message or f"Scan marked as FAILED for {log_context}")
        elif status == CourseScanStatus.COMPLETED:
            logger.info(f"Scan completed successfully for {log_context}")
        else:
            logger.debug(f"Scan status updated to {status.value} for {log_context}")
    except (DatabaseError, Exception) as e:
        log_context = f"course_scan_id={course_scan_id}"
        logger.error(f"Error updating CourseScan {log_context} to status {status.value}: {e}")
    
def save_scan_results(course_scan_id: int, course_id: int, items: List[ContentItemWithImages]):
    """
    Save the scan results into the database within a transaction.
    Creates ContentItem and ImageItem records scoped to the provided course_scan_id
    without deleting records from prior scans for the course.
    
    :param course_scan_id: CourseScan ID
    :type course_scan_id: int
    :param course_id: Course ID
    :type course_id: int
    :param items: List of content items with images
    :type items: List[ContentItemWithImages]
    """
    try:
        with transaction.atomic():
            
            for item in items:
                content_item = ContentItem.objects.create(
                    course_scan_id=course_scan_id,
                    content_type=item.get('type'),
                    content_id=item.get('id'),
                    content_name=item.get('name'),
                    content_parent_id=item.get('content_parent_id')
                )
                
                for img in item['images']:
                    # img is an ImageEntry dict with 'url', 'status', and optional 'error'
                    image_url = img.get('url')
                    error_obj = img.get('error') if img.get('status') == 'error' else None
                    logger.debug(f"Saving ImageItem - URL: {image_url}, Status: {img.get('status')}, Error: {error_obj}")
                    
                    ImageItem.objects.create(
                        content_item=content_item,
                        image_url=image_url
                    )

    except (DatabaseError, Exception) as e:
        logger.error(f"Error in save_scan_results transaction for course_scan_id {course_scan_id}, course_id {course_id}: {e}")
        return
  
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
        logger.error("Step CIErr: Error fetching content items using %s: %s", getattr(fn, '__name__', str(fn)), e)
        return e


def get_assignments(course: Course) -> List[Union[ContentItemWithImages, CourseFetchError]]:
    """
    Synchronously fetches assignments for a given course using canvas_api.get_assignments().
    """
    # user_id = 1
    # req_user: User = get_user_model().objects.get(pk=user_id)
    # canvas_callback_url = '/oauth/oauth-callback'
    # request = _create_background_request(req_user, canvas_callback_url, 1111111111111)
    # manager = MANAGER_FACTORY.create_manager(request)
    # canvas_api: Canvas = manager.canvas_api
    # course: Course = Course(canvas_api._Canvas__requester, {'id': 1111111111111111})

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
                extract_images_from_html(assignment.description, course.id, 'assignment'),
                'assignment',
                None)
        return images_from_assignments
    except (CanvasException, Exception) as e:
        logger.error(f"Step A1: Error fetching assignments for course {course.id}: {e}")
        return [{
            'type': 'assignment_fetch_error',
            'course_id': getattr(course, 'id', None),
            'error': e,
        }]
 
def get_pages(course: Course) -> List[Union[ContentItemWithImages, CourseFetchError]]:
    """
    Synchronously fetches pages for a given course using canvas_api.get_pages().
    """
    # user_id = 1
    # req_user: User = get_user_model().objects.get(pk=user_id)
    # canvas_callback_url = '/oauth/oauth-callback'
    # request = _create_background_request(req_user, canvas_callback_url, 1111111111111)
    # manager = MANAGER_FACTORY.create_manager(request)
    # canvas_api: Canvas = manager.canvas_api
    # course: Course = Course(canvas_api._Canvas__requester, {'id': 1111111111111111})

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
                extract_images_from_html(page.body, course.id, 'page'),
                'page',
                None)
        return images_from_pages
    except (CanvasException, Exception) as e:
        logger.error(f"Step PageErr: Error fetching pages for course {course.id}: {e}")
        return [{
            'type': 'page_fetch_error',
            'course_id': getattr(course, 'id', None),
            'error': e,
        }]


def get_quizzes(course: Course) -> List[Union[ContentItemWithImages, QuizQuestionFetchError, CourseFetchError]]:
    """
    Synchronously fetches quizzes for a given course using canvas_api.get_quizzes().
    """
    # user_id = 1
    # req_user: User = get_user_model().objects.get(pk=user_id)
    # canvas_callback_url = '/oauth/oauth-callback'
    # request = _create_background_request(req_user, canvas_callback_url, 1111111111111)
    # manager = MANAGER_FACTORY.create_manager(request)
    # canvas_api: Canvas = manager.canvas_api
    # course: Course = Course(canvas_api._Canvas__requester, {'id': 1111111111111111})

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
                extract_images_from_html(getattr(quiz, 'description', ''), course.id, 'quiz'),
                'quiz',
                None)
        logger.info(f"Fetched {len(quizzes)} quizzes. Now fetching questions for quizzes.")
        quiz_question_results = async_to_sync(get_quiz_questions)(quizzes)

        mapped_quiz_question_results: List[Union[List[ContentItemWithImages], QuizQuestionFetchError]] = []
        for quiz_obj, result in zip(quizzes, quiz_question_results):
            if isinstance(result, Exception):
                mapped_quiz_question_results.append({
                    'type': 'quiz_question_error',
                    'quiz_id': getattr(quiz_obj, 'id', None),
                    'quiz_title': getattr(quiz_obj, 'title', ''),
                    'error': result,
                })
            else:
                mapped_quiz_question_results.append(result)

        return process_quiz_with_questions(images_from_quizzes, mapped_quiz_question_results)
    except (CanvasException, Exception) as e:
        logger.error(f"Step QuizErr: Errors fetching Quizzes for course {course.id}: {e}")
        return [{
            'type': 'quiz_fetch_error',
            'course_id': getattr(course, 'id', None),
            'error': e,
        }]

def process_quiz_with_questions(
    quiz: List[ContentItemWithImages],
    questions: List[Union[List[ContentItemWithImages], QuizQuestionFetchError]]) -> List[Union[ContentItemWithImages, QuizQuestionFetchError]]:
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
    # Temporary debugging behavior: force a non-existent quiz id to trigger Canvas API error.
    import random

    def _build_debug_quiz(source_quiz: Quiz) -> Quiz:
        return Quiz(source_quiz._requester, {
            'id': random.randint(100000000, 999999999),
            'title': random.choice(['Ghost Quiz', 'Phantom Exam', 'Broken Test', 'Mystery Quiz', 'Fake Assessment']),
            'course_id': getattr(source_quiz, 'course_id', None),
            'description': getattr(source_quiz, 'description', ''),
        })

    if quiz.id == 485512:  # specific quiz ID to trigger error for testing
        quiz = _build_debug_quiz(quiz)

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
                extract_images_from_html(getattr(question, 'question_text', ''), quiz.course_id, 'question'),
                'quiz_question',
                quiz.id)

        return images_from_questions
    except (CanvasException, Exception) as e:
        logger.error(f"Step QuizQErr: Errors fetching quiz {quiz.id}:{quiz.title} questions due {e}")
        raise e

def _is_image_from_current_course(img_src: str, current_course_id: int) -> bool:
    """
    Check if a Canvas image URL belongs to the current course.
    
    Always includes:
    - Public Canvas images (e.g., /images/play_overlay.png, /images/book_stro/icon.png)
    - User files (e.g., /users/{id}/files/{file_id})
    
    Only validates course_id for URLs with /courses/{course_id}/ pattern.
    
    :param img_src: The image source URL
    :param current_course_id: The ID of the current course being processed
    :return: True if the image belongs to the current course or is a public/user file, False otherwise
    """
    try:
        parsed = urlparse(img_src)
        parts = [p for p in parsed.path.split('/') if p]
        
        # Public Canvas images with any subdirectory depth - always include
        # e.g., /images/play_overlay.png, /images/book_stro/icon.png, /images/foo/poo/bar.png
        if 'images' in parts and 'courses' not in parts:
            logger.info(f"Including public Canvas image: {img_src}")
            return True
        
        # User files (e.g., /users/{id}/files/{file_id}) - always include
        if 'users' in parts and 'files' in parts:
            logger.info(f"Including user file: {img_src}")
            return True
        
        # Look for /courses/{course_id}/ pattern and validate
        if 'courses' in parts:
            courses_idx = parts.index('courses')
            if courses_idx + 1 < len(parts):
                url_course_id = int(parts[courses_idx + 1])
                if url_course_id != current_course_id:
                    logger.info(f"Skipping image from different course: URL has course_id={url_course_id}, current course_id={current_course_id}")
                    return False
        return True
    except (ValueError, IndexError) as e:
        logger.warning(f"Could not parse course_id from URL {img_src}: {e}")
        raise e  

def _parse_canvas_file_src(img_src: str) ->  Optional[str]:
    """
    Parse Canvas file preview URLs and convert to download URLs.
    
    Handles:
    - Course files: /courses/{id}/files/{file_id}/preview
    - User files: /users/{id}/files/{file_id}/preview
    - Public images: /images/play_overlay.png (returned as-is)
    
    Extracts file_id and constructs download URL with verifier params preserved.
    Returns download_url or original URL if not parseable.
    """
    if not img_src:
        return None
    try:
        parsed = urlparse(img_src)
        # Path segments: ['', 'courses', '403334', 'files', '42932047', 'preview']
        parts = [p for p in parsed.path.split('/') if p]
        
        # Public Canvas images - return as-is without parsing
        if 'images' in parts and 'courses' not in parts:
            logger.debug(f"Using public Canvas image URL as-is: {img_src}")
            return img_src
        
        file_id = None
        for i, part in enumerate(parts):
            if part == 'files' and i + 1 < len(parts):
                file_id = parts[i + 1]
                break
        if not file_id:
            logger.error(f"Could not find file_id in Canvas file URL path: {img_src}")
            raise ValueError(f"Step PErr File_id: File ID not found in URL path: {img_src}")

        # preserve original query params (verifier, etc.)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        # flatten qs back to query string (parse_qs gives lists)
        flat_qs = {}
        for k, v in qs.items():
            # preserve first value
            if isinstance(v, list) and v:
                flat_qs[k] = v[0]
            else:
                flat_qs[k] = v

        # ensure download_frd=1 is appended
        flat_qs['download_frd'] = '1'

        download_path = f"/files/{file_id}/download"
        download_url = f"{parsed.scheme}://{parsed.netloc}{download_path}?{urlencode(flat_qs)}"
        return download_url
    except Exception as e:
        logger.error(f"Step PErr: Error parsing img src URL '{img_src}': {e}")
        raise e

def extract_images_from_html(html_content: str, course_id: int, content_type: str = 'unknown') -> List[ImageEntry]:
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, "html.parser")
    extracted_image_urls: List[ImageEntry] = []
    image_extensions = IMAGE_EXTENSIONS
    for img in soup.find_all("img"):
        try:
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
            # Skip when alt appears to be a filename (ends with an image extension)
            if img_alt and not img_alt.lower().endswith(image_extensions):
                continue

            domain = urlparse(img_src).netloc
            if settings.CANVAS_OAUTH_CANVAS_DOMAIN in domain:
                # Check if the image belongs to the current course
                if not _is_image_from_current_course(img_src, course_id):
                    continue

                logger.info(f"Parsing Canvas file URL: {img_src}")
                download_url = _parse_canvas_file_src(img_src)
            else:
                logger.info(f"Non-Canvas image URL found: {img_src}")
                download_url = img_src
            extracted_image_urls.append({
                "url": download_url,
                "content_type": content_type,
                "status": "success",
            })
        except Exception as e:
            img_src_for_log = img_src if 'img_src' in locals() else "unknown_url"
            logger.error(f"Error processing image tag for course_id {course_id}: {e}")
            extracted_image_urls.append({
                "url": img_src_for_log,
                "content_type": content_type,
                "status": "error",
                "error": e,
                "error_type": f"{content_type}_type_error",
            })

    if extracted_image_urls:
        logger.info(extracted_image_urls)
    return extracted_image_urls

# Helper function to append image items if images exist
def append_image_items(
        images_list: List[ContentItemWithImages],
        content_id: int,
        content_name: str,
        images: List[ImageEntry],
        content_type: str,
        content_parent_id: Optional[int]) -> List[ContentItemWithImages]:
    """
    Append a content item with extracted images to the images list.
    
    :param images_list: Accumulating list of content items with images
    :param content_id: Content item ID (assignment/page/quiz/question ID)
    :param content_name: Content item name (title/description)
    :param images: List of extracted ImageEntry objects with URLs and error details
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


