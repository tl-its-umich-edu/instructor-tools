import asyncio
import logging
from django.db import transaction
from urllib.parse import urlparse, parse_qs, urlencode
from typing import List, Dict, Any, Optional, TypeVar, Callable, Union
from asgiref.sync import async_to_sync
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
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

logger = logging.getLogger(__name__)
T = TypeVar("T")
R = TypeVar("R")

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')
PER_PAGE = 100
IMAGE_EXTENSIONS = tuple(Image.registered_extensions().keys())
semaphore = asyncio.Semaphore(10)



@log_execution_time
def fetch_and_scan_course(task: Dict[str, Any]):
    logger.info(f"Starting fetch_and_scan_course for course_id: {task.get('course_id')}")
      # mark CourseScan as running (create if missing)
    course_id = int(task.get('course_id'))

    # adding a status before start of the scan, if this DB action failed no need to stop next steps of fetching content images
    update_course_scan(course_id, CourseScanStatus.RUNNING)

    try:
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
            update_course_scan(course_id, CourseScanStatus.FAILED, f"Error creating Canvas API for course_id {course_id}: {e}")
            CanvasOAuth2Token.objects.filter(user=request.user).delete()
            return

        # Fetch full course details to ensure attributes like course_code are present for logging
        course: Course = Course(canvas_api._Canvas__requester, {'id': course_id})

        results = async_to_sync(get_courses_images)(course)
        state_of_content_fetch: bool = unpack_and_store_content_images(results, course)

        # this check is helping not to move to alt text retrieval if there was an error in fetching content images
        if not state_of_content_fetch:
            update_course_scan(course_id, CourseScanStatus.FAILED, f"Failed to fetch content images for course_id {course_id}. Marking scan as FAILED.")
            return
        
        try:
            retrieve_and_store_alt_text(course, bearer_token=bearer_token)
        except ImageContentExtractionException as e:
            update_course_scan(course_id, CourseScanStatus.FAILED, f"ImageContentExtractionException while processing alt text for course_id {course_id}: {e}")
            return

        # Update that the course scan is completed
        update_course_scan(course_id, CourseScanStatus.COMPLETED)
    except Exception as e:
        update_course_scan(course_id, CourseScanStatus.FAILED, f"Unexpected error in fetch_and_scan_course for course_id {course_id}: {e}")


    

def _create_background_request(req_user: User, canvas_callback_url: str, course_id: int) -> Request:
    logger.info(f"Creating background request - User: {req_user}, Course ID: {course_id}, Callback URL: {canvas_callback_url}")
    # Create a request factory and build the request since this is a background task request won't have a user session
    factory = RequestFactory()
    request: Request = factory.get('/oauth/oauth-callback')
    request.user = req_user
    request.build_absolute_uri = lambda path: canvas_callback_url
    session = SessionStore()
    session['course_id'] = course_id
    session.save()
    request.session = session
    return request

async def get_courses_images(course: Course):
    results = await asyncio.gather(
        fetch_content_items_async(get_assignments, course),
        fetch_content_items_async(get_pages, course),
        fetch_content_items_async(get_quizzes, course),
        return_exceptions=True,
    )
    logger.info("raw results from gather course images: %s", results)
    return results
    
def retrieve_and_store_alt_text(course: Course, bearer_token: Optional[str] = None):
    """
    Retrieve alt text for images in the given course using AI processor.
    The images for the course need to have been processed first to get the image URLs.

    :param course: Course object
    :type course: Course
    :param bearer_token: Optional bearer token to pass directly to the image fetcher for Authorization
    """
    process_content_images = ProcessContentImages(
        course_id=course.id,
        bearer_token=bearer_token,
    )
    images_with_alt_text = process_content_images.retrieve_images_with_alt_text()
    return images_with_alt_text

def unpack_and_store_content_images(results, course: Course) -> bool:
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
        return False

    error_when_fetching_images = any(_has_fetch_error(r) for r in (assignments, pages, quizzes))

    if error_when_fetching_images:
        update_course_scan(course.id, CourseScanStatus.FAILED)
        return False
    
    combined = assignments + pages + quizzes
    logger.debug("Combined items count: %s", combined)
    # Filter to only those content with images with alt text
    filtered_content_with_images = [
        item for item in combined
        if isinstance(item.get('images'), list) and len(item.get('images')) > 0
    ]

    logger.debug("Items before filter: %d; after filter (has images): %d", len(combined), len(filtered_content_with_images))
    logger.info(f"Course {course.id} items with images: {filtered_content_with_images}")

    # DB call to persist initial ContentItem and ImageItem records
    save_scan_results(course.id, filtered_content_with_images)
    return True

def update_course_scan(course_id: int, status: CourseScanStatus, error_message: Optional[str] = None) -> None:
    """
    Update or create a CourseScan record with the given status and log accordingly.
    
    :param course_id: Course ID
    :param status: status of the scan (CourseScanStatus enum)
    :param error_message: Optional error message to log when status is FAILED
    """
    try:
        obj, created = CourseScan.objects.update_or_create(
            course_id=course_id,
            defaults={'status': status.value}
        )
        if status == CourseScanStatus.FAILED:
            logger.error(error_message or f"Scan marked as FAILED for course_id {course_id}")
        elif status == CourseScanStatus.COMPLETED:
            logger.info(f"Scan completed successfully for course_id {course_id}")
        else:
            logger.debug(f"Scan status updated to {status.value} for course_id {course_id}")
    except (DatabaseError, Exception) as e:
        logger.error(f"Error updating CourseScan for course_id {course_id} to status {status.value}: {e}")
    
def save_scan_results(course_id: int, items: List[Dict[str, Any]]):
    """
    Save the scan results into the database within a transaction.
    Deletes previous ContentItem and ImageItem records for the course_id, then creates new records.
    
    :param course_id: Course ID
    :type course_id: int
    :param items: List of content items with images
    :type items: List[Dict[str, Any]]
    """
    try:
        with transaction.atomic():
            # 1. Delete previous items based on course_id if exists
            ContentItem.objects.filter(course_id=course_id).delete()
            ImageItem.objects.filter(course_id=course_id).delete()
            
            # 2. Create ContentItem and ImageItem
            for item in items:
                content_item = ContentItem.objects.create(
                    course_id=course_id,
                    content_type=item.get('type'),
                    content_id=item.get('id'),
                    content_name=item.get('name'),
                    content_parent_id=item.get('content_parent_id')
                )
                
                for img in item['images']:
                    ImageItem.objects.create(
                        course_id=course_id,
                        content_item=content_item,
                        image_url=img
                    )

    except (DatabaseError, Exception) as e:
        logger.error(f"Error in save_scan_results transaction for course_id {course_id}: {e}")
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
        logger.error("Error fetching content items using %s: %s", getattr(fn, '__name__', str(fn)), e)
        return e


def get_assignments(course: Course):
    """
    Synchronously fetches assignments for a given course using canvas_api.get_assignments().
    """
    try:
        logger.info(f"Fetching assignments for course {course.id}.")
        assignments = list(course.get_assignments(per_page=PER_PAGE))
        logger.debug(f"Fetched {len(assignments)} assignments.")
        images_from_assignments = []
        for assignment in assignments:
            # Use getattr to safely check for quiz_id attribute
            quiz_id = getattr(assignment, 'quiz_id', None)
            if quiz_id:
                # skip quiz assignments since quizzes are fetched separately
                logger.debug(f"Skipping quiz assignment ID: {assignment.id}")
                continue
            logger.info(f"Assignment ID: {assignment.id}, Name: {assignment.name}")

            # Extract images from assignment description
            images_from_assignments = append_image_items(
                images_from_assignments,
                assignment.id,
                assignment.name,
                extract_images_from_html(assignment.description, course.id),
                'assignment',
                None)
        return images_from_assignments
    except (CanvasException, Exception) as e:
        logger.error(f"Error fetching assignments for course {course.id}: {e}")
        raise e
 
def get_pages(course: Course):
    """
    Synchronously fetches pages for a given course using canvas_api.get_pages().
    """
    try:
        logger.info(f"Fetching pages for course {course.id}.")
        pages = list(course.get_pages(include=['body'], per_page=PER_PAGE))

        logger.debug(f"Fetched {len(pages)} pages.")
        images_from_pages = []
        for page in pages:
            logger.info(f"Processing Page ID: {page.page_id}, Title: {page.title}")
            # Extract images from page body
            images_from_pages = append_image_items(
                images_from_pages,
                page.page_id,
                page.title,
                extract_images_from_html(page.body, course.id),
                'page',
                None)
        return images_from_pages
    except (CanvasException, Exception) as e:
        logger.error(f"Error fetching pages for course {course.id}: {e}")
        raise e


def get_quizzes(course: Course):
    """
    Synchronously fetches quizzes for a given course using canvas_api.get_quizzes().
    """
    try:
        logger.info(f"Fetching quizzes for course {course.id}.")
        quizzes: List[Quiz] = list(course.get_quizzes(per_page=PER_PAGE))

        images_from_quizzes = []
        for quiz in quizzes:
            # Extract images from quiz description
            images_from_quizzes = append_image_items(
                images_from_quizzes,
                quiz.id,
                quiz.title,
                extract_images_from_html(getattr(quiz, 'description', ''), course.id),
                'quiz',
                None)

        quiz_question_results = async_to_sync(get_quiz_questions)(quizzes)
        return process_quiz_with_questions(images_from_quizzes, quiz_question_results)
    except (CanvasException, Exception) as e:
        logger.error(f"Errors fetching Quizzes for course {course.id}: {e}")
        raise e

def process_quiz_with_questions(quiz: List[Dict[str, Any]], questions: List[Dict[str, Any]]):
    """
    Process a quiz and its questions to extract images from the quiz description and questions.
    """
    exceptions = []
    valid_question_lists = []
    for item in questions:
        if isinstance(item, list):
            valid_question_lists.append(item)
        elif isinstance(item, Exception):
            exceptions.append(item)
    if not exceptions:
        flattened_questions = [q for sublist in valid_question_lists for q in sublist]
        return quiz + flattened_questions
    else:
        return exceptions[0]

async def get_quiz_questions(quizzes: List[Quiz]):
    async with semaphore:
        quiz_q_tasks = [fetch_content_items_async(get_quiz_questions_sync, quiz) for quiz in quizzes]
        return await asyncio.gather(*quiz_q_tasks, return_exceptions=True)

def get_quiz_questions_sync(quiz: Quiz):
    logger.info(f"Fetching questions for quiz ID: {quiz.id}, Title: {quiz.title}")
    images_from_questions = []
    try:
        question = quiz.get_questions(per_page=PER_PAGE)
        for question in question:
            # Extract images from quiz question text
            images_from_questions = append_image_items(
                images_from_questions,
                question.id,
                question.question_name,
                extract_images_from_html(getattr(question, 'question_text', ''), quiz.course_id),
                'quiz_question',
                quiz.id)

        return images_from_questions
    except (CanvasException, Exception) as e:
        logger.error(f"Errors fetching quiz {quiz.id}:{quiz.title} questions due {e}")
        raise e

def _is_image_from_current_course(img_src: str, current_course_id: int) -> bool:
    """
    Check if a Canvas image URL belongs to the current course.
    
    Always includes:
    - Public Canvas images (e.g., /images/play_overlay.png, /images/book_stro/icon.png)
    - User files (e.g., /users/{id}/files/{file_id})
    - External images
    
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
            logger.debug(f"Including public Canvas image: {img_src}")
            return True
        
        # User files (e.g., /users/{id}/files/{file_id}) - always include
        if 'users' in parts and 'files' in parts:
            logger.debug(f"Including user file: {img_src}")
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
        return True  # Include image if we can't parse, to avoid losing valid images

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
            raise ValueError(f"File ID not found in URL path: {img_src}")

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
        logger.error(f"Error parsing img src URL '{img_src}': {e}")
        raise e

def extract_images_from_html(html_content: str, course_id: int) -> List[str]:
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, "html.parser")
    images_found = []
    image_extensions = IMAGE_EXTENSIONS
    for img in soup.find_all("img"):
        logger.info(f"Processing img tag: {img}")
        img_src = img.get("src")
        img_alt = (img.get("alt") or "").strip()
        img_role = (img.get("role") or "").strip().lower()

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
        images_found.append(download_url)
    
    if images_found:
        logger.info(images_found)
    return images_found

# Helper function to append image items if images exist
def append_image_items(
        images_list: List[str],
        content_id: int,
        content_name: str,
        images: List[str],
        content_type: str,
        content_parent_id: Optional[int]) -> List[Dict[str, Any]]:

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


