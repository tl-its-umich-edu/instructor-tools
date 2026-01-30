from collections.abc import Callable
import logging
import asyncio 
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from canvasapi import Canvas
from canvasapi.course import Course
from canvasapi.page import Page
from canvasapi.assignment import Assignment
from canvasapi.quiz import Quiz
from canvasapi.quiz import QuizQuestion
from canvasapi.exceptions import CanvasException
from asgiref.sync import async_to_sync
from django.db.utils import DatabaseError
from typing import Any, Dict, List, Literal, NotRequired, TypedDict, Union
from bs4 import BeautifulSoup

from django.conf import settings
from backend.canvas_app_explorer.models import ImageItem, ContentItem

logger = logging.getLogger(__name__)

class ImagePayload(TypedDict):
    image_url: str
    image_id: str
    action: Literal["approve", "skip"]
    approved_alt_text: str
    image_url_for_update: str
    is_alt_text_updated: NotRequired[bool | None]
    alt_text_failed_error_message: NotRequired[str | None]

class ContentPayload(TypedDict):
    content_id: int
    content_name: str
    content_parent_id: str | None
    content_type: Literal["assignment", "quiz", "page", "quiz_question"]
    images: List[ImagePayload]
    
PER_PAGE = 100
class AltTextUpdate:
    def __init__(self, course_id: int, canvas_api: Canvas, content_with_alt_text: List[Dict[str, Any]], content_types: List[str]) -> None:
        self.course: Course = Course(canvas_api._Canvas__requester, {'id': course_id})
        self.canvas_api = canvas_api
        self.content_with_alt_text: List[ContentPayload] = self._enrich_content_with_ui_urls(content_with_alt_text)
        self.content_alt_text_update_report: List[ContentPayload] = self.content_with_alt_text
        self.content_types: List[str] = content_types
        self.semaphore = asyncio.Semaphore(10)
    
    def process_alt_text_update(self) -> bool|List[ContentPayload]:
        """
        Process the validated alt text review data.
        Returns True if all updates succeeded, otherwise returns the report with failure details.
        Checks for failures by looking for is_alt_text_updated=False or alt_text_failed_error_message set.
        """
        quiz_types = [t for t in self.content_types if t in ["quiz", "quiz_question"]]

        logger.info(f'self.content_with_alt_text: {self.content_with_alt_text}')
        try:
            if "page" in self.content_types:
                self._process_page()
            elif "assignment" in self.content_types:
                self._process_assignment()
            elif quiz_types:
                self._process_quiz_and_questions(quiz_types)
            else: 
                logger.warning("No valid content types found for alt text update")
        except Exception as e:
            logger.error(f"Error processing alt text update for course ID {self.course.id}: {e}")
        
        # Check if there are any failures in the report
        # A failure is indicated by either is_alt_text_updated=False or alt_text_failed_error_message being set
        has_failures = any(
            img.get('is_alt_text_updated') == False or img.get('alt_text_failed_error_message') is not None
            for content in self.content_alt_text_update_report 
            for img in content['images']
        )

        self.delete_successfully_updated_items()
        
        return self.content_alt_text_update_report if has_failures else True


    def _process_page(self) -> None:
        logger.info("Processing page alt text update for course_id %s", self.course.id)
        approved_content = self._get_approved_content_ids()
        page_ids = {item["content_id"] for item in approved_content}
        
        if not page_ids:
            logger.info("No approved pages to process for course_id %s", self.course.id)
            return
        
        try:
            pages: Page = list(self.course.get_pages(include=['body'], per_page=PER_PAGE))
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to fetch pages for course ID {self.course.id}: {e}")
            # Mark all approved page images as failed due to fetch error
            page_errors = [{"content_id": pid, "error_message": str(e)} for pid in page_ids]
            self._mark_content_images_failed(page_errors, "page")
            raise e
        # this filters Content: pages from API call to only those with approved images content IDs. 
        approved_pages: Page = [p for p in pages if getattr(p, "page_id", None) in page_ids]
        page_alt_text_update_results = self._update_page_alt_text(approved_pages)
        
        # Track failed pages by preparing error list with content_id and error message
        page_errors = []
        for page, result in zip(approved_pages, page_alt_text_update_results):
            if isinstance(result, Exception):
                page_errors.append({
                    "content_id": page.page_id,
                    "error_message": str(result)
                })
        
        # Mark all failed pages in report
        if page_errors:
            self._mark_content_images_failed(page_errors, "page")
            raise Exception(f"Error updating page alt text for course ID {self.course.id}")

    def _process_assignment(self) -> None:
        logger.info("Processing assignment alt text update for course_id %s", self.course.id)
        approved_content = self._get_approved_content_ids()
        assignment_ids = {item["content_id"] for item in approved_content}
        
        if not assignment_ids:
            logger.info("No approved assignments to process for course_id %s", self.course.id)
            return
        
        # making api calls for fetching assignments
        try:
            assignments: Assignment = list(self.course.get_assignments(per_page=PER_PAGE))
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to fetch assignments for course ID {self.course.id}: {e}")
            # Mark all approved assignment images as failed due to fetch error
            assignment_errors = [{"content_id": aid, "error_message": str(e)} for aid in assignment_ids]
            self._mark_content_images_failed(assignment_errors, "assignment")
            raise e
        
        # this filters Content: assignments from API call to only those with approved images content IDs.
        approved_assignment: Assignment = [a for a in assignments if a.id in assignment_ids]
        assign_alt_text_update_results = self._update_assignment_alt_text(approved_assignment)
        
        # Track failed assignments by preparing error list with content_id and error message
        assignment_errors = []
        for assignment, result in zip(approved_assignment, assign_alt_text_update_results):
            if isinstance(result, Exception):
                assignment_errors.append({
                    "content_id": assignment.id,
                    "error_message": str(result)
                })
        
        # Mark all failed assignments in report
        if assignment_errors:
            self._mark_content_images_failed(assignment_errors, "assignment")
            raise Exception(f"Error updating assignment alt text for course ID {self.course.id}")
    
    def _process_quiz_and_questions(self, quiz_types: List[str]) -> None:
        logger.info("Processing quiz alt text update for course_id %s with quiz types %s", self.course.id, quiz_types)
        approved_content = self._get_approved_content_ids()
        
        # 1. Process Quizzes (Description)
        approved_quizzes = {c['content_id'] for c in approved_content if c['content_type'] == 'quiz'}
        approved_quiz_questions = [c for c in approved_content if c['content_type'] == 'quiz_question']

        # it is not important to fetch quizzes if there are no approved quizzes to update
        if approved_quizzes:
            error_quizzes_fetch = False
            try: 
                quizzes_result = list(self.course.get_quizzes(per_page=PER_PAGE))
            except (CanvasException, Exception) as e:
                logger.error(f"Failed to fetch quizzes : {e}")
                # Mark all approved quiz images as failed due to fetch error
                quiz_errors = [{"content_id": qid, "error_message": str(e)} for qid in approved_quizzes]
                self._mark_content_images_failed(quiz_errors, "quiz")
                error_quizzes_fetch = True

            if not error_quizzes_fetch:
                quizzes_to_update = self._filter_approved_quizzes_for_update(quizzes_result, approved_quizzes)
                for q in quizzes_to_update: logger.info(f"Quiz to Update Id {q.id} Name: {q.title}")
                quizzes_alt_text_update_results = self._update_quiz_alt_text(quizzes_to_update)
                
                # Track failed quizzes by preparing error list with content_id and error message
                quiz_errors = []
                for quiz, result in zip(quizzes_to_update, quizzes_alt_text_update_results):
                    if isinstance(result, Exception):
                        quiz_errors.append({
                            "content_id": quiz.id,
                            "error_message": str(result)
                        })
                
                # Mark all failed quizzes in report
                if quiz_errors:
                    self._mark_content_images_failed(quiz_errors, "quiz")
        
        # 2. Process Quiz Questions Results if there are approved quiz questions
        if approved_quiz_questions:
            approved_question_ids = {c['content_id'] for c in approved_quiz_questions}
            quiz_ids_list = [c['content_parent_id'] for c in approved_quiz_questions if c.get('content_parent_id')]
            
            result_quiz_questions = self.get_quiz_questions(approved_quiz_questions)
            # Flatten the results using zip - result_quiz_questions is a list of lists or exceptions
            all_questions = []
            failed_quiz_batches = []
            for quiz_id, res in zip(quiz_ids_list, result_quiz_questions):
                if isinstance(res, Exception):
                    logger.error(f"Failed to fetch questions for quiz {quiz_id}: {res}")
                    failed_quiz_batches.append(res)
                else:
                    all_questions.extend(res if res else [])
            
            # If there are any fetch errors, mark all questions as failed and skip update
            if failed_quiz_batches:
                question_errors = [{"content_id": qid, "error_message": str(failed_quiz_batches[0])} for qid in approved_question_ids]
                self._mark_content_images_failed(question_errors, "quiz_question")
            else:
                questions_to_update = self._filter_approved_questions_for_update(all_questions, approved_question_ids)
                
                for q in questions_to_update:
                    logger.info(f"Question Id {q.id} quiz id: {q.quiz_id}: Name: {q.question_name}")
                questions_alt_text_update_results = self._update_quiz_question_alt_text(questions_to_update)
                
                # Track failed questions by preparing error list with content_id and error message
                question_errors = []
                question_successes = []
                for question, result in zip(questions_to_update, questions_alt_text_update_results):
                    if isinstance(result, Exception):
                        question_errors.append({
                            "content_id": question.id,
                            "error_message": str(result)
                        })
                    else:
                        question_successes.append(question.id)
                
                # Mark all failed and successful questions in report
                if question_errors:
                    self._mark_content_images_failed(question_errors, "quiz_question")
        
       
    def _mark_content_images_failed(self, content_errors: List[Dict[str, Any]], content_type: str) -> None:
        """
        Mark all approved images in given content IDs as failed with their error messages.
        Only marks images with action 'approve', skipped images remain unchanged.
        
        :param content_errors: List of dicts with 'content_id' and 'error_message' keys
        :param content_type: Type of content ('page', 'assignment', 'quiz', 'quiz_question')
        """
        for error_dict in content_errors:
            content_id = error_dict['content_id']
            error_message = error_dict['error_message']
            
            for content in self.content_alt_text_update_report:
                if content['content_id'] == content_id and content['content_type'] == content_type:
                    for image in content['images']:
                        if image.get('action') == 'approve':
                            image['is_alt_text_updated'] = False
                            image['alt_text_failed_error_message'] = error_message
                    break
    
    def delete_successfully_updated_items(self) -> None:
        """
        Delete ImageItem and ContentItem records for successfully updated images.
        
        Logic:
        - Delete ImageItem records for images with action 'approve' or 'skip' that were successfully updated
          (i.e., no is_alt_text_updated field or is_alt_text_updated is True/not False)
        - After deleting images, check if any ContentItem has no remaining ImageItems
        - If a ContentItem has no remaining images, delete that ContentItem as well
        
        Note: is_alt_text_updated field only appears when there's a failure (is_alt_text_updated=False).
              If the field is absent or is True, the update was successful.
        """
        images_to_delete = []
        content_ids_to_check = set()
        
        # Collect image IDs to delete
        for content in self.content_alt_text_update_report:
            content_id = content['content_id']
            for image in content['images']:
                action = image.get('action')
                is_failed = image.get('is_alt_text_updated') == False
                
                # Delete if action is approve/skip AND NOT failed
                if action in ['approve', 'skip'] and not is_failed:
                    images_to_delete.append(image.get('image_id'))
                    content_ids_to_check.add(content_id)
        
        if not images_to_delete:
            logger.info("No successfully updated images to delete")
            return
        
        try:
            # Delete ImageItems by image_id
            deleted_count, _ = ImageItem.objects.filter(id__in=images_to_delete).delete()
            logger.info(f"Deleted {deleted_count} successfully updated ImageItem records")
            
            # Check for orphaned ContentItems and delete them
            for content_id in content_ids_to_check:
                # Check if this content still has any images
                remaining_images = ImageItem.objects.filter(content_item__content_id=content_id).count()
                
                if remaining_images == 0:
                    # No images left, safe to delete the ContentItem
                    deleted_count, _ = ContentItem.objects.filter(content_id=content_id).delete()
                    logger.info(f"Deleted orphaned ContentItem with content_id={content_id}")
                else:
                    logger.info(f"ContentItem with content_id={content_id} still has {remaining_images} images, keeping it")
        
        except (DatabaseError, Exception) as e:
            logger.error(f"Error deleting content items from Database: {e}")

    
    
    def _filter_approved_quizzes_for_update(self, quizzes: List[Quiz], approved_quiz_ids: set) -> List[Quiz]:
        return [q for q in quizzes if q.id in approved_quiz_ids]

    def _filter_approved_questions_for_update(self, questions: List[QuizQuestion], approved_question_ids: set) -> List[QuizQuestion]:
        return [q for q in questions if q.id in approved_question_ids]
    
        
    
    @async_to_sync
    async def get_quiz_questions(self, quiz_questions: List[dict]) -> None:
        async with self.semaphore:
            # Extract unique quiz IDs and fetch questions for each
            quiz_ids = {c['content_parent_id'] for c in quiz_questions if c.get('content_parent_id')}
            tasks = [
                self.update_content_items_async(
                    self._get_quiz_questions_sync, 
                    Quiz(self.canvas_api._Canvas__requester, {'id': quiz_id, 'course_id': self.course.id})
                )
                for quiz_id in quiz_ids
            ]
            logger.info(f"Fetching quiz questions for quiz IDs: {len(quiz_ids)}")
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _get_quiz_questions_sync(self, quiz: Quiz) -> List[QuizQuestion]:
        try:
            return list(quiz.get_questions(per_page=PER_PAGE))
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to fetch questions for quiz ID {quiz.id}: {e}")
            raise e
    
    def _get_quizzes_sync(self, course: Course) -> List[Quiz]:
        try:
            return list(course.get_quizzes(per_page=PER_PAGE))
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to fetch quizzes for course ID {course.id}: {e}")
            raise e
    
    @async_to_sync
    async def _update_quiz_alt_text(self, approved_quizzes: List[Quiz]) -> None:
        async with self.semaphore:
            quiz_update_tasks = [self.update_content_items_async(self._update_quiz_alt_text_sync, quiz) 
                                 for quiz in approved_quizzes]
            return await asyncio.gather(*quiz_update_tasks, return_exceptions=True)
        
    def _update_quiz_alt_text_sync(self, approved_quiz: Quiz) -> None:
        try:
            updated_description = self._update_alt_text_html(approved_quiz.id, approved_quiz.description)
            return approved_quiz.edit(quiz={'description': updated_description})
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to update quiz ID {approved_quiz.id}: {e}")
            raise e
        
    @async_to_sync
    async def _update_quiz_question_alt_text(self, approved_quiz_questions: List[QuizQuestion]) -> None:
        async with self.semaphore:
            question_update_tasks = [self.update_content_items_async(self._update_quiz_question_alt_text_sync, question) 
                                     for question in approved_quiz_questions]
            return await asyncio.gather(*question_update_tasks, return_exceptions=True)
    
    def _update_quiz_question_alt_text_sync(self, approved_question: QuizQuestion) -> None:
        try:
            updated_text = self._update_alt_text_html(approved_question.id, approved_question.question_text)
            return approved_question.edit(question={'question_text': updated_text})
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to update quiz question ID {approved_question.id}: {e}")
            raise e
        
    @async_to_sync
    async def _update_assignment_alt_text(self, approved_assignments: List[Assignment]) -> None:
        async with self.semaphore:
            assign_update_tasks = [self.update_content_items_async(self._update_assignment_alt_text_sync, assignment) 
                                   for assignment in approved_assignments]
            return await asyncio.gather(*assign_update_tasks, return_exceptions=True)
    

    def _update_assignment_alt_text_sync(self, approved_assignment: Assignment) -> None:
        try:
            updated_description = self._update_alt_text_html(approved_assignment.id, approved_assignment.description)
            return approved_assignment.edit(assignment={'description': updated_description})
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to update assignment ID {approved_assignment.id}: {e}")
            raise e

    async def update_content_items_async[T, R](self, fn: Callable[[T], R], ctx: T) -> Union[R, Exception]:
        """
        Generic async wrapper that runs the synchronous `fn(course|quiz)` in a thread and
        returns a list (or empty list on error). `fn` should be a callable like
        `get_assignments`, `get_pages`,  `get_quizzes`, `get_quiz_questions` that 
        accepts a Course or Quiz and returns a list.
        """
        try:
            return await asyncio.to_thread(fn, ctx)
        except (CanvasException, Exception) as e:
            logger.error("Error updating content items using %s: %s", getattr(fn, '__name__', str(fn)), e)
            return e
    
    @async_to_sync
    async def _update_page_alt_text(self, approved_pages: List[Page]) -> None:
        async with self.semaphore:
            page_update_tasks = [self.update_content_items_async(self._update_page_alt_text_sync, page) 
                                 for page in approved_pages]
            return await asyncio.gather(*page_update_tasks, return_exceptions=True)
    
    def _update_page_alt_text_sync(self, page: Page) -> None:
        try:
            updated_body = self._update_alt_text_html(page.page_id, page.body)
            return page.edit(wiki_page={'body': updated_body})
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to update page ID {page.page_id}: {e}")
            raise e

    
    def _update_alt_text_html(self, content_id, content_html: str) -> str:
        """
        Return HTML content updated with alt text changes for images that have been approved.
        
        Matching logic:
        - For Canvas file URLs (image_url_for_update is a file_id): checks if file_id is contained in img src
        - For public Canvas images and external URLs: exact match on full URL
        
        :param content_html: Original HTML string for the content item to be processed.
        :param content_id: Identifier of the content item whose HTML is being updated; used to
            look up the corresponding image approval data in ``self.content_with_alt_text``.
        :return: The updated HTML string with ``alt`` attributes set for approved images.
        :rtype: str
        """
        soup = BeautifulSoup(content_html, 'html.parser')
        images = soup.find_all('img')
        for img in images:
            img_src = img.get('src', '')
            for image_payload in next(c for c in self.content_with_alt_text if c['content_id'] == content_id)['images']:
                url_for_update = image_payload['image_url_for_update']
                
                # Determine if url_for_update is a file_id (numeric string) or full URL
                is_file_id = url_for_update and url_for_update.isdigit()
                
                matched = False
                if is_file_id:
                    # For file_id, check if it's contained in the img src
                    # Matches /files/{file_id}/ pattern in any variation
                    if f'/files/{url_for_update}/' in img_src or f'/files/{url_for_update}?' in img_src:
                        matched = True
                        logger.debug(f"Matched file_id {url_for_update} in img src {img_src}")
                else:
                    # For full URLs (public images, external images), exact match
                    if img_src == url_for_update:
                        matched = True
                        logger.debug(f"Exact matched URL {url_for_update}")
                
                if matched and image_payload['action'] == 'approve':
                    img['alt'] = image_payload['approved_alt_text']
                    logger.info(f"Updated alt text for image in content {content_id}")
                    
        updated_description = str(soup)
        return updated_description
    
    
    def _get_approved_content_ids(self) -> List[dict]:
        """
        This will only return content IDs where at least one image has been approved. A content can have multiple images,
        but if there is a mix of approved and skipped images, we still want to process the content to update the approved ones.
        Further along the update will only update the images that were approved.
        
        :param self: Description
        :return: List of dicts containing content_id, content_parent_id and content_type
        :rtype: List[dict]
        """
        approved_contents = [
            {
                "content_id": c["content_id"],
                "content_parent_id": c.get("content_parent_id"),
                "content_type": c["content_type"]
            }
            for c in self.content_with_alt_text
            if any(img["action"] == "approve" for img in c["images"])
        ]
        logger.info(f"Approved content IDs: {approved_contents}")
        return approved_contents
    
    def _enrich_content_with_ui_urls(self, content_list: List[ContentPayload]) -> List[ContentPayload]:
        """
        this method enriches each image in the content list with a URL that mimics how Canvas UI would display it.
        If the image is approved it transforms the URL to a format suitable for Canvas UI preview. otherwise, it sets the original URL (doesn't matter what URL is it's skipped ).
        
        :param self: Description
        :param content_list: Description
        :type content_list: List[ContentPayload]
        :return: Description
        :rtype: List[ContentPayload]
        """
        for content in content_list:
            for image in content['images']:
                image['image_url_for_update'] = None
                
                parsed = None
                # Check domain type
                try:
                    parsed = urlparse(image['image_url'])
                    if parsed.netloc == settings.CANVAS_OAUTH_CANVAS_DOMAIN:
                        if image.get('action') == 'approve':
                            image['image_url_for_update'] = self._transform_image_url(parsed)
                        else:
                            # If action is skip, retain original URL for reference
                            image['image_url_for_update'] = image['image_url']
                    else:
                        # External image when we update we always image_url_for_update to match and update alt text there
                        image['image_url_for_update'] = image['image_url']
                except Exception as e:
                    logger.error(f"Failed to parse image URL {image['image_url']}: {e}")
                    raise e

        return content_list
    
    def _transform_image_url(self, parsed) -> str | None:
        """
        Transforms Canvas file URLs to extract just the file_id.
        
        For file URLs (e.g., /files/{id}/download, /courses/{id}/files/{id}/preview, /users/{id}/files/{id}/preview):
        Returns just the file_id as a string (e.g., "44125891")
        
        For public Canvas images (e.g., /images/play_overlay.png):
        Returns the full URL as-is for exact matching
        
        For other URLs:
        Returns the full URL as-is
        """
        try:
            parts = parsed.path.split('/')
            # Remove empty strings from split
            parts = [p for p in parts if p]
            
            # Check if it's a file URL pattern
            if 'files' in parts:
                # Find the file_id (comes right after 'files')
                files_idx = parts.index('files')
                if files_idx + 1 < len(parts):
                    file_id = parts[files_idx + 1]
                    # Return just the file_id for matching
                    logger.debug(f"Extracted file_id {file_id} from URL {parsed.geturl()}")
                    return file_id
            
            # For public Canvas images or other URLs, return full URL
            return parsed.geturl()
        except Exception as e:
            logger.error(f"Failed to transform image URL {parsed.geturl()}: {e}")
            raise e
        
