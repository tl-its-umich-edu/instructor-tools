from django.http import HttpRequest
from backend import settings
import time
from backend.canvas_app_explorer.alt_text_helper import tasks
from backend.canvas_app_explorer.canvas_lti_manager.django_factory import DjangoCourseLtiManagerFactory
import logging
from django.test import RequestFactory
from backend.canvas_app_explorer.canvas_lti_manager.exception import CanvasHTTPError
import asyncio
from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from canvasapi.course import Course
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from rest_framework.request import Request
from typing import List, Dict, Any, Union
from urllib.parse import urlparse, parse_qs, urlencode
from django.db import transaction

from backend.canvas_app_explorer.models import CourseScan, ContentItem, ImageItem

logger = logging.getLogger(__name__)

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')

PER_PAGE = 100
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')

def fetch_and_scan_course(task: Dict[str, Any]):
  logger.info(f"Starting fetch_and_scan_course for course_id: {task.get('course_id')}")
  try:
      # mark CourseScan as running (create if missing)
      try:
          canvas_id_val = task.get('course_id')
          canvas_id_int = int(canvas_id_val)
      except Exception:
          canvas_id_int = None

      if canvas_id_int is not None:
          try:
              with transaction.atomic():
                  CourseScan.objects.update_or_create(
                      course_id=canvas_id_int,
                      defaults={
                          'status': 'running',
                      }
                  )
          except Exception:
              logger.exception("Failed to set CourseScan status to 'running' for course_id=%s", canvas_id_int)

      # Fetch course content using the manager
      course_id = task.get('course_id')
      user_id = task.get('user_id')
      req_user: User = get_user_model().objects.get(pk=user_id)
      canvas_callback_url = task.get('canvas_callback_url')
      # Create a request factory and build the request since this is a background task request won't have a user session
      factory = RequestFactory()
      request: Request = factory.get('/oauth/oauth-callback')
      request.user = req_user
      request.build_absolute_uri = lambda path: canvas_callback_url
      # Attach a session to the request and set course_id so manager factory can read it
      # SessionMiddleware requires a get_response callable; use a no-op lambda
      session_mw = SessionMiddleware(lambda req: None)
      session_mw.process_request(request)
      # set the course_id on the session and persist it
      request.session['course_id'] = course_id
      request.session.save()
      manager =  MANAGER_FACTORY.create_manager(request)
    #   course = Course(manager._Canvas__requester, {'id': course_id})

      start_time: float = time.perf_counter()
      result = get_courses_images(manager, course_id)
      end_time: float = time.perf_counter()
      logger.info(f"scanning course {course_id} images tofound {len(result) if result else 0} images took {end_time - start_time:.2f} seconds")
      # replace ContentItem + ImageItem rows for this course with the newly found images
      try:
          if canvas_id_int is not None:
              with transaction.atomic():
                  # delete existing ImageItem rows for this course first (FK -> ContentItem)
                  ImageItem.objects.filter(course_id=canvas_id_int).delete()
                  # delete existing ContentItem rows for this course
                  ContentItem.objects.filter(course_id=canvas_id_int).delete()

                  images_to_create = []
                  # create ContentItem rows and associated ImageItem rows
                  for item in (result or []):
                      content_type = item.get('type')
                      content_id = item.get('id')
                      images = item.get('images') or []
                      try:
                          content_id_int = int(content_id) if content_id is not None else None
                      except Exception:
                          content_id_int = None

                      # create ContentItem
                      content_obj = ContentItem.objects.create(
                          course_id=canvas_id_int,
                          content_type=content_type,
                          content_id=content_id_int,
                      )

                      # prepare ImageItem objects for this content
                      for img in images:
                          raw_img_id = img.get('image_id')
                          try:
                              img_id = int(raw_img_id) if raw_img_id is not None else None
                          except Exception:
                              logger.warning("Non-numeric image_id %r for course %s, skipping", raw_img_id, canvas_id_int)
                              continue
                          url = img.get('download_url') or img.get('image_url')
                          if not url:
                              logger.warning("Missing URL for image %r in course %s, skipping", raw_img_id, canvas_id_int)
                              continue

                          images_to_create.append(ImageItem(
                              course_id=canvas_id_int,
                              content_item=content_obj,
                              image_id=img_id,
                              image_url=url,
                          ))

                  if images_to_create:
                      ImageItem.objects.bulk_create(images_to_create)

                  # mark CourseScan as completed (update timestamp via auto_now)
                  CourseScan.objects.update_or_create(
                      course_id=canvas_id_int,
                      defaults={
                          'status': 'completed',
                      }
                  )
      except Exception:
          logger.exception("Failed to replace ContentItem/ImageItem rows or set CourseScan to 'completed' for course_id=%s", canvas_id_int)
      

  except CanvasHTTPError as error:
      logger.error(f"Error fetching or scanning course {course_id}: {error}")
      # mark CourseScan as failed on HTTP errors
      try:
          if 'canvas_id_int' in locals() and canvas_id_int is not None:
              with transaction.atomic():
                  CourseScan.objects.update_or_create(
                      canvas_id=canvas_id_int,
                      defaults={'status': 'failed'}
                  )
      except Exception:
          logger.exception("Failed to set CourseScan status to 'failed' for course_id=%s", locals().get('canvas_id_int'))
      return None

@async_to_sync
async def get_courses_images(manager, course_id) -> List[Dict[str, Any]]:
    # logger.info(f"Fetching assignments and pages for course {course.id}.")
    try:
        # Await both fetch tasks; the sync helpers guarantee a list (or empty list) on error.
        assignments, pages = await asyncio.gather(
            fetch_assignments_async(manager, course_id),
            fetch_pages_async(manager, course_id),
        )
        logger.info(f"Processing {len(assignments)} assignments and {len(pages)} pages.")

        combined = assignments + pages
        # Keep only items where 'images' is a list with at least one element
        filtered = [
            item for item in combined
            if isinstance(item.get('images'), list) and len(item.get('images')) > 0
        ]

        logger.info("Items before filter: %d; after filter (has images): %d", len(combined), len(filtered))
        logger.info("Filtered items with images: %s", filtered)

        return filtered
 
    except Exception as e:
         logger.error(f"An error occurred during concurrent fetch and extraction for : {e}")
         return []
  
async def fetch_assignments_async(manager, course_id):
  """
  Asynchronously fetches assignments for a given course using canvas_api.get_assignments().
  """
  # Run the synchronous calls to get the course and then its assignments in a separate thread
  try:
      return await asyncio.to_thread(get_assignments, manager, course_id)
  except Exception as e:
      logger.error(f"Error fetching assignments for : {e}")
      return []
  
def get_assignments(manager, course_id):
    """
    Synchronously fetches assignments for a given course using canvas_api.get_assignments().
    """
    try:
        logger.info(f"Fetching assignments for course {course_id}.")
        # materialize PaginatedList into a real list so len() and iteration are safe
        assignments = list(manager.canvas_api.get_course(course_id).get_assignments(per_page=PER_PAGE))
        logger.info(f"Fetched {len(assignments)} assignments.")
        result = []
        for assignment in assignments:
            logger.info(f"Assignment ID: {assignment.id}, Name: {assignment.name}")
            result.append({'id': assignment.id, 'name': assignment.name, 'images': extract_images_from_html(assignment.description), 'type': 'assignment' })
        return result
    except Exception as e:
        logger.error(f"Error fetching assignments for course {course_id}: {e}")
        # Return empty list on error so callers don't need to check for exceptions
        return []
 
async def fetch_pages_async(manager, course_id):
    """
    Asynchronously fetches pages for a given course using canvas_api.get_pages().
    """
    # Run the synchronous calls to get the course and then its pages in a separate thread
    try:
        return await asyncio.to_thread(get_pages, manager, course_id)
    except Exception as e:
        logger.error(f"Error fetching pages for : {e}")
        return []
    
 
def get_pages(manager, course_id):
    """
    Synchronously fetches pages for a given course using canvas_api.get_pages().
    """
    try:
        logger.info(f"Fetching pages for course {course_id}.")
        pages = list(manager.canvas_api.get_course(course_id).get_pages(include=['body'], per_page=PER_PAGE))
        logger.info(f"Fetched {len(pages)} pages.")
        for page in pages:
            logger.info(f"Page ID: {page.page_id}, Title: {page.title}")
        result = []
        for page in pages:
            result.append({'id': page.page_id, 'name': page.title, 'images': extract_images_from_html(page.body), 'type': 'page'})
        return result
    except Exception as e:
        logger.error(f"Errorss fetching pages for course {course_id}: {e}")
        # Return empty list on error so callers don't need to check for exceptions
        return []

def _parse_canvas_file_src(img_src: str):
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
            return None, None

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
    except Exception:
        return None, None

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

