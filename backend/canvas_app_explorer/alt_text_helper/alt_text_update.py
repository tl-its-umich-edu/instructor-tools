import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from canvasapi import Canvas
from canvasapi.course import Course
from canvasapi.page import Page
from canvasapi.assignment import Assignment
from typing import List, Literal, TypedDict
from bs4 import BeautifulSoup

from django.conf import settings

logger = logging.getLogger(__name__)

class ImagePayload(TypedDict):
    image_url: str
    image_id: str
    action: Literal["approve", "skip"]
    approved_alt_text: str
    image_url_like_canvas_UI: str | None
    domain_type: Literal["internal", "external"]

class ContentPayload(TypedDict):
    content_id: int
    content_name: str
    content_parent_id: str | None
    content_type: Literal["assignment", "quiz", "page", "quiz_question"]
    images: List[ImagePayload]
    
PER_PAGE = 100
class AltTextUpate:
    def __init__(self, course: Course, content_with_alt_text: List[ContentPayload], content_types: List[str], canvas_api: Canvas) -> None:
        self.course = course
        self.content_with_alt_text: List[ContentPayload] = self._enrich_content_with_ui_urls(content_with_alt_text)
        self.content_types: List[str] = content_types
        self.canvas_api = canvas_api
    
    def process_alt_text_update(self) -> None:
        """
        Process the validated alt text review data.
        """
        quiz_types = [t for t in self.content_types if t in ["quiz", "quiz_question"]]

        logger.info(f'self.content_with_alt_text: {self.content_with_alt_text}')

        if "page" in self.content_types:
            self._process_page()
        elif "assignment" in self.content_types:
            self._process_assignment()
        elif quiz_types:
            self._process_quiz(quiz_types)
        else: 
            logger.warning("No valid content types found for alt text update")


    def _process_page(self) -> None:
        logger.info("Processing page alt text update for course_id %s", self.course.id)
        page_ids = self._get_approved_content_ids()
        pages: Page = list(self.course.get_pages(include=['body'], per_page=PER_PAGE))
        # this filters Content: pages from API call to only those with approved images content IDs. 
        pages_filtered: Page = [p for p in pages if getattr(p, "page_id", None) in page_ids]
        
        extracted_pages = []
        for page in pages_filtered:
            extracted_pages.append({
                "id": page.page_id,
                "name": page.title,
                "html": page.body
            })
            logger.info(f"Page ID: {page.page_id}, Title: {page.title}, html: {page.body}")
        
        self._process_extracted_content(extracted_pages)

    def _process_assignment(self) -> None:
        logger.info("Processing assignment alt text update for course_id %s", self.course.id)
        assignment_ids = self._get_approved_content_ids()
        assignments: Assignment = list(self.course.get_assignments(per_page=PER_PAGE))
        # this filters Content: assignments from API call to only those with approved images content IDs.
        assignments_filtered: Assignment = [a for a in assignments if a.id in assignment_ids]
        
        extracted_assignments = []
        for assignment in assignments_filtered:
            extracted_assignments.append({
                "id": assignment.id,
                "name": assignment.name,
                "html": assignment.description
            })
            logger.info(f"Assignment ID: {assignment.id}, Name: {assignment.name}, html: {assignment.description}")
            
        self._process_extracted_content(extracted_assignments)

    def _process_extracted_content(self, content_list: List[dict]) -> None:
        """
        Process the extracted content items (pages, assignments, etc.) to update alt text.
        """
        for content in content_list:
            html_content = content.get("html")
            if not html_content:
                continue
            
            soup = BeautifulSoup(html_content, "html.parser")
            logger.info(soup)
            for img in soup.find_all("img"):
                logger.info(f"Found image tag: {img}")

    def _process_quiz(self, quiz_types: List[str]) -> None:
        logger.info("Processing quiz alt text update for course_id %s with quiz types %s", self.course.id, quiz_types)
    
    def _get_approved_content_ids(self) -> set[int]:
        """
        This will only return content IDs where at least one image has been approved. A content can have multiple images,
        but if there is a mix of approved and skipped images, we still want to process the content to update the approved ones.
        Further along the update will only update the images that were approved.
        
        :param self: Description
        :return: Description
        :rtype: set[int]
        """
        return {
            c["content_id"]
            for c in self.content_with_alt_text
            if any(img["action"] == "approve" for img in c["images"])
        }
    
    def _enrich_content_with_ui_urls(self, content_list: List[ContentPayload]) -> List[ContentPayload]:
        """
        this method enriches each image in the content list with a URL that mimics how Canvas UI would display it.
        It adds new variable to indicate if the image URL is internal (hosted on the same domain as the Canvas instance) or external.
        If the image is approved and internal, it transforms the URL to a format suitable for Canvas UI preview. otherwise, it sets the URL to None.
        
        :param self: Description
        :param content_list: Description
        :type content_list: List[ContentPayload]
        :return: Description
        :rtype: List[ContentPayload]
        """
        for content in content_list:
            for image in content['images']:
                image['image_url_like_canvas_UI'] = None
                image['domain_type'] = 'external'
                
                parsed = None
                # Check domain type
                try:
                    parsed = urlparse(image['image_url'])
                    if parsed.netloc == settings.CANVAS_OAUTH_CANVAS_DOMAIN:
                        image['domain_type'] = 'internal'
                        if image.get('action') == 'approve':
                            image['image_url_like_canvas_UI'] = self._transform_image_url(parsed)
                except Exception as e:
                    logger.error(f"Failed to parse image URL {image['image_url']}: {e}")
                    raise e

        return content_list
    
    def _transform_image_url(self, parsed) -> str | None:
        """
        Transforms URL like:
        https://domain/files/44125891/download?verifier=...&download_frd=1
        to:
        https://domain/courses/{course_id}/files/44125891/preview?verifier=...
        """
        try:
            if '/files/' in parsed.path:
                parts = parsed.path.split('/')
                # parts example: ['', 'files', '44125891', 'download']
                if len(parts) >= 3 and parts[1] == 'files':
                    file_id = parts[2]
                    new_path = f"/courses/{self.course.id}/files/{file_id}/preview"
                    
                    # Handle query params
                    query_params = parse_qs(parsed.query)
                    # Keep verifier, remove download_frd
                    new_query = {}
                    if 'verifier' in query_params:
                        new_query['verifier'] = query_params['verifier']
                    
                    return urlunparse((
                        parsed.scheme,
                        parsed.netloc,
                        new_path,
                        parsed.params,
                        urlencode(new_query, doseq=True),
                        parsed.fragment
                    ))
            return None
        except Exception as e:
            logger.error(f"Failed to transform image URL {parsed.geturl()}: {e}")
            raise e
        
