import time
import asyncio
import logging
from urllib.parse import urlparse, parse_qs, urlencode
from typing import List, Dict, Any, Optional, Tuple
from asgiref.sync import async_to_sync
from django.http import HttpRequest
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.db import SessionStore
from django.db import transaction
from bs4 import BeautifulSoup
from rest_framework.request import Request
from canvasapi.exceptions import CanvasException
from canvasapi.course import Course
from canvasapi import Canvas

from backend import settings
from backend.canvas_app_explorer.canvas_lti_manager.django_factory import DjangoCourseLtiManagerFactory
from backend.canvas_app_explorer.canvas_lti_manager.exception import CanvasHTTPError
from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem

logger = logging.getLogger(__name__)

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')

PER_PAGE = 100
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')

def fetch_and_scan_course(task: Dict[str, Any]):
    logger.info(f"Starting fetch_and_scan_course for course_id: {task.get('course_id')}")
      # mark CourseScan as running (create if missing)
    course_id = int(task.get('course_id'))

    obj, created = CourseScan.objects.update_or_create(
        course_id=course_id,
        defaults={
            'status': 'running',
        }
    )
    logger.info(f"{obj} created: {created}")

    # Fetch course content using the manager
    user_id = task.get('user_id')
    req_user: User = get_user_model().objects.get(pk=user_id)
    canvas_callback_url = task.get('canvas_callback_url')
    logger.info(f"canvas_callback_url: {canvas_callback_url}")
    # Create a request factory and build the request since this is a background task request won't have a user session
    factory = RequestFactory()
    request: Request = factory.get('/oauth/oauth-callback')
    request.user = req_user
    request.build_absolute_uri = lambda path: canvas_callback_url
    session = SessionStore()
    session['course_id'] = course_id
    session.save()
    request.session = session
    # Create the manager
    canvas_api: Canvas =  MANAGER_FACTORY.create_manager(request).canvas_api
    # Fetch full course details to ensure attributes like course_code are present for logging
    course: Course = Course(canvas_api._Canvas__requester, {'id': course_id})

    start_time: float = time.perf_counter()
    get_courses_images(course)
    end_time: float = time.perf_counter()
    logger.info(f"scanning course {course_id} images took {end_time - start_time:.2f} seconds")
    


@async_to_sync
async def get_courses_images(course: Course):
    try:
        results = await asyncio.gather(
            fetch_content_items_async(get_assignments, course),
            fetch_content_items_async(get_pages, course),
            return_exceptions=True,
        )
        logger.info("raw results from gather: %s", results)
        # unpack results (assignments, pages) and handle exceptions returned by gather. gather maintain call order
        assignments, pages = results

        error_when_fetching_images = False
        if isinstance(assignments, Exception):
            logger.error("Error occurred fetching assignments: %s", assignments)
            error_when_fetching_images = True
            assignments = []
        if isinstance(pages, Exception):
            logger.error("Error occurred fetching pages: %s", pages)
            error_when_fetching_images = True
            pages = []
        
        if error_when_fetching_images:
            # DB call would be needed to update CourseScan status to 'failed' here
            return

        combined = assignments + pages
        logger.info("Combined items count: %s", combined)
        filtered = [
            item for item in combined
            if isinstance(item.get('images'), list) and len(item.get('images')) > 0
        ]

        logger.info("Items before filter: %d; after filter (has images): %d", len(combined), len(filtered))
        logger.info("Filtered items with images: %s", filtered)

        # DB call to persist ContentItem and ImageItem records

 
    except Exception as e:
         logger.error(f"An error occurred during concurrent fetch and extraction for : {e}")
         #DB call would be needed to update CourseScan status to 'failed' here
  
async def fetch_content_items_async(fn, course: Course):
    """
    Generic async wrapper that runs the synchronous `fn(course)` in a thread and
    returns a list (or empty list on error). `fn` should be a callable like
    `get_assignments` or `get_pages` that accepts a Course and returns a list.
    """
    try:
        return await asyncio.to_thread(fn, course)
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
        logger.info(f"Fetched {len(assignments)} assignments.")
        images_from_assignments = []
        for assignment in assignments:
            logger.info(f"Assignment ID: {assignment.id}, Name: {assignment.name}")
            images_from_assignments.append(
                {'id': assignment.id, 
                 'name': assignment.name, 
                 'images': extract_images_from_html(assignment.description), 
                 'type': 'assignment' })
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

        logger.info(f"Fetched {len(pages)} pages.")
        for page in pages:
            logger.info(f"Page ID: {page.page_id}, Title: {page.title}")
        images_from_pages = []
        for page in pages:
            images_from_pages.append(
                {'id': page.page_id, 
                 'name': page.title, 
                 'images': extract_images_from_html(page.body), 
                 'type': 'page'})
        return images_from_pages
    except (CanvasException, Exception) as e:
        logger.error(f"Errorss fetching pages for course {course.id}: {e}")
        raise e

def _parse_canvas_file_src(img_src: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse Canvas file preview URL like:
    https://canvas-test.it.umich.edu/courses/403334/files/42932047/preview?verifier=...
    Return (file_id, download_url) or (None, None) if not parseable.
    """
    if not img_src:
        return None, None
    try:
        parsed = urlparse(img_src)
        # Path segments: ['', 'courses', '403334', 'files', '42932047', 'preview']
        parts = [p for p in parsed.path.split('/') if p]
        file_id = None
        for i, part in enumerate(parts):
            if part == 'files' and i + 1 < len(parts):
                file_id = parts[i + 1]
                break
        if not file_id:
            raise ValueError("File ID not found in URL path")

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
        return file_id, download_url
    except Exception as e:
        logger.error(f"Error parsing img src URL '{img_src}': {e}")
        raise e

def extract_images_from_html(html_content: str) -> List[Dict[str, Any]]:
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

        if img_src:
            file_id, download_url = _parse_canvas_file_src(img_src)

            images_found.append({
                "image_id": file_id,
                "download_url": download_url
            })
    logger.info(images_found)
    return images_found

