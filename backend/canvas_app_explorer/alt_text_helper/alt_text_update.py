import logging
from canvasapi import Canvas
from canvasapi.course import Course
from typing import List, Literal, TypedDict

from django.conf import settings

logger = logging.getLogger(__name__)

class ImagePayload(TypedDict):
    image_url: str
    image_id: str
    action: Literal["approve", "skip"]
    approved_alt_text: str

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
        self.content_with_alt_text: List[ContentPayload] = content_with_alt_text
        self.content_types: List[str] = content_types
        self.canvas_api = canvas_api

    def process_alt_text_update(self) -> None:
        """
        Process the validated alt text review data.
        """
        quiz_types = [t for t in self.content_types if t in ["quiz", "quiz_question"]]

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
        page_ids = {c["content_id"] for c in self.content_with_alt_text if c["content_type"] == "page"}
        pages = list(self.course.get_pages(include=['body'], per_page=PER_PAGE))
        pages_filtered = [p for p in pages if getattr(p, "page_id", None) in page_ids]
        for page in pages_filtered:
            logger.info(f"Page ID: {page.page_id}, Title: {page.title}")

    def _process_assignment(self) -> None:
        logger.info("Processing assignment alt text update for course_id %s", self.course.id)
        assignment_ids = {c["content_id"] for c in self.content_with_alt_text if c["content_type"] == "assignment"}
        assignments = list(self.course.get_assignments(per_page=PER_PAGE))
        assignments_filtered = [a for a in assignments if a.id in assignment_ids]
        for assignment in assignments_filtered:
            logger.info(f"Assignment ID: {assignment.id}, Name: {assignment.name}")

    def _process_quiz(self, quiz_types: List[str]) -> None:
        logger.info("Processing quiz alt text update for course_id %s with quiz types %s", self.course.id, quiz_types)

        
