from collections.abc import Callable
import logging
import asyncio
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

from backend.canvas_app_explorer.models import ImageItem, ContentItem

logger = logging.getLogger(__name__)

class ImagePayload(TypedDict):
    image_url: str
    image_id: str
    action: Literal["approve", "skip", "decorative"]
    approved_alt_text: str
    is_alt_text_updated: NotRequired[bool | None]
    alt_text_failed_error_message: NotRequired[str | None]

class ContentPayload(TypedDict):
    id: int
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
        self.content_with_alt_text: List[ContentPayload] = content_with_alt_text
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
        content_to_modify = self._get_approved_decorative_content_ids()
        page_ids = {item["content_id"] for item in content_to_modify}
        
        if not page_ids:
            logger.info("No approved or decorative pages to process for course_id %s", self.course.id)
            return
        
        try:
            pages: Page = list(self.course.get_pages(include=['body'], per_page=PER_PAGE))
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to fetch pages for course ID {self.course.id}: {e}")
            # Mark all approved/decorative page images as failed due to fetch error
            page_errors = [{"content_id": pid, "error_message": str(e)} for pid in page_ids]
            self._mark_content_images_failed(page_errors, "page")
            raise e
        # this filters Content: pages from API call to only those with approved/decorative images content IDs. 
        pages_to_update: Page = [p for p in pages if getattr(p, "page_id", None) in page_ids]
        page_alt_text_update_results = self._update_page_alt_text(pages_to_update)
        
        # Track failed pages by preparing error list with content_id and error message
        page_errors = []
        for page, result in zip(pages_to_update, page_alt_text_update_results):
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
        content_to_modify = self._get_approved_decorative_content_ids()
        assignment_ids = {item["content_id"] for item in content_to_modify}
        
        if not assignment_ids:
            logger.info("No approved or deorative assignments to process for course_id %s", self.course.id)
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
        assignments_to_modify: Assignment = [a for a in assignments if a.id in assignment_ids]
        assign_alt_text_update_results = self._update_assignment_alt_text(assignments_to_modify)
        
        # Track failed assignments by preparing error list with content_id and error message
        assignment_errors = []
        for assignment, result in zip(assignments_to_modify, assign_alt_text_update_results):
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
        content_to_modify = self._get_approved_decorative_content_ids()
        
        # 1. Process Quizzes (Description)
        quizzes_to_modify = {c['content_id'] for c in content_to_modify if c['content_type'] == 'quiz'}
        quiz_questions_to_modify = [c for c in content_to_modify if c['content_type'] == 'quiz_question']

        # it is not important to fetch quizzes if there are no approved/decorative quizzes to update
        if quizzes_to_modify:
            error_quizzes_fetch = False
            try: 
                quizzes_result = list(self.course.get_quizzes(per_page=PER_PAGE))
            except (CanvasException, Exception) as e:
                logger.error(f"Failed to fetch quizzes : {e}")
                # Mark all approved/decorative quiz images as failed due to fetch error
                quiz_errors = [{"content_id": qid, "error_message": str(e)} for qid in quizzes_to_modify]
                self._mark_content_images_failed(quiz_errors, "quiz")
                error_quizzes_fetch = True

            if not error_quizzes_fetch:
                quizzes_to_update = self._filter_quizzes_to_modify_for_update(quizzes_result, quizzes_to_modify)
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
        
        # 2. Process Quiz Questions Results if there are approved/decorative quiz questions
        if quiz_questions_to_modify:
            questions_to_modify_ids = {c['content_id'] for c in quiz_questions_to_modify}
            quiz_ids_list = [c['content_parent_id'] for c in quiz_questions_to_modify if c.get('content_parent_id')]
            
            result_quiz_questions = self.get_quiz_questions(quiz_questions_to_modify)
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
                question_errors = [{"content_id": qid, "error_message": str(failed_quiz_batches[0])} for qid in questions_to_modify_ids]
                self._mark_content_images_failed(question_errors, "quiz_question")
            else:
                questions_to_update = self._filter_questions_to_modify_for_update(all_questions, questions_to_modify_ids)
                
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
        Mark all approved (or marked as decorative) images in given content IDs as failed with their error messages.
        Only marks images with action 'approve'/'decorative', skipped images remain unchanged.
        
        :param content_errors: List of dicts with 'content_id' and 'error_message' keys
        :param content_type: Type of content ('page', 'assignment', 'quiz', 'quiz_question')
        """
        for error_dict in content_errors:
            content_id = error_dict['content_id']
            error_message = error_dict['error_message']
            
            for content in self.content_alt_text_update_report:
                if content['content_id'] == content_id and content['content_type'] == content_type:
                    for image in content['images']:
                        if image.get('action') == 'approve' or image.get('action') == 'decorative':
                            image['is_alt_text_updated'] = False
                            image['alt_text_failed_error_message'] = error_message
                    break
    
    def delete_successfully_updated_items(self) -> None:
        """
        Delete ImageItem and ContentItem records for successfully updated images.
        
        Logic:
        - Delete ImageItem records for images with action 'approve'/'skip'/'decorative' that were successfully updated
          (i.e., no is_alt_text_updated field or is_alt_text_updated is True/not False)
        - After deleting images, check if any ContentItem has no remaining ImageItems
        - If a ContentItem has no remaining images, delete that ContentItem as well
        
        Note: is_alt_text_updated field only appears when there's a failure (is_alt_text_updated=False).
              If the field is absent or is True, the update was successful.
        """
        images_to_delete = []
        content_item_ids_to_check = set()
        
        # Collect image IDs to delete
        for content in self.content_alt_text_update_report:
            content_item_id = content['id']
            for image in content['images']:
                action = image.get('action')
                is_failed = image.get('is_alt_text_updated') == False
                
                if action in ['approve', 'skip', 'decorative'] and not is_failed:
                    images_to_delete.append(image.get('image_id'))
                    content_item_ids_to_check.add(content_item_id)
        
        if not images_to_delete:
            logger.info("No successfully updated images to delete")
            return
        
        try:
            # Delete ImageItems by image_id
            deleted_count, _ = ImageItem.objects.filter(id__in=images_to_delete).delete()
            logger.info(f"Deleted {deleted_count} successfully updated ImageItem records")
            
            # Check for orphaned ContentItems and delete them
            for content_item_id in content_item_ids_to_check:
                # Check if this content still has any images
                remaining_images = ImageItem.objects.filter(content_item_id=content_item_id).count()
                
                if remaining_images == 0:
                    # No images left, safe to delete the ContentItem
                    deleted_count, _ = ContentItem.objects.filter(id=content_item_id).delete()
                    logger.info(f"Deleted orphaned ContentItem with id={content_item_id}")
                else:
                    logger.info(f"ContentItem with id={content_item_id} still has {remaining_images} images, keeping it")
        
        except (DatabaseError, Exception) as e:
            logger.error(f"Error deleting content items from Database: {e}")

    
    
    def _filter_quizzes_to_modify_for_update(self, quizzes: List[Quiz], quiz_ids: set) -> List[Quiz]:
        return [q for q in quizzes if q.id in quiz_ids]

    def _filter_questions_to_modify_for_update(self, questions: List[QuizQuestion], question_ids: set) -> List[QuizQuestion]:
        return [q for q in questions if q.id in question_ids]
    
        
    
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
    async def _update_quiz_alt_text(self, quizzes_to_modify: List[Quiz]) -> None:
        async with self.semaphore:
            quiz_update_tasks = [self.update_content_items_async(self._update_quiz_alt_text_sync, quiz) 
                                 for quiz in quizzes_to_modify]
            return await asyncio.gather(*quiz_update_tasks, return_exceptions=True)
        
    def _update_quiz_alt_text_sync(self, quiz_to_modify: Quiz) -> None:
        try:
            updated_description = self._update_alt_text_html(quiz_to_modify.id, quiz_to_modify.description)
            return quiz_to_modify.edit(quiz={'description': updated_description})
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to update quiz ID {quiz_to_modify.id}: {e}")
            raise e
        
    @async_to_sync
    async def _update_quiz_question_alt_text(self, quiz_questions_to_modify: List[QuizQuestion]) -> None:
        async with self.semaphore:
            question_update_tasks = [self.update_content_items_async(self._update_quiz_question_alt_text_sync, question) 
                                     for question in quiz_questions_to_modify]
            return await asyncio.gather(*question_update_tasks, return_exceptions=True)
    
    def _update_quiz_question_alt_text_sync(self, question_to_modify: QuizQuestion) -> None:
        try:
            updated_text = self._update_alt_text_html(question_to_modify.id, question_to_modify.question_text)
            return question_to_modify.edit(question={'question_text': updated_text})
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to update quiz question ID {question_to_modify.id}: {e}")
            raise e
        
    @async_to_sync
    async def _update_assignment_alt_text(self, assignments_to_modify: List[Assignment]) -> None:
        async with self.semaphore:
            assign_update_tasks = [self.update_content_items_async(self._update_assignment_alt_text_sync, assignment) 
                                   for assignment in assignments_to_modify]
            return await asyncio.gather(*assign_update_tasks, return_exceptions=True)
    

    def _update_assignment_alt_text_sync(self, assignment_to_modify: Assignment) -> None:
        try:
            updated_description = self._update_alt_text_html(assignment_to_modify.id, assignment_to_modify.description)
            return assignment_to_modify.edit(assignment={'description': updated_description})
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to update assignment ID {assignment_to_modify.id}: {e}")
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
    async def _update_page_alt_text(self, pages_to_update: List[Page]) -> None:
        async with self.semaphore:
            page_update_tasks = [self.update_content_items_async(self._update_page_alt_text_sync, page) 
                                 for page in pages_to_update]
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
        Return HTML content updated with alt text changes for images that have been approved or marked as decorative.

        Matching logic: exact string comparison between the ``src`` on the Canvas ``img`` tag and
        the ``image_url`` echoed back by the frontend. The scan stores ``img src`` verbatim (no URL
        rewriting), and the review payload returns that same value, so Canvas file URLs, public
        Canvas images, and external URLs are all matched identically.

        :param content_html: Original HTML string for the content item to be processed.
        :param content_id: Identifier of the content item whose HTML is being updated; used to
            look up the corresponding image approval data in ``self.content_with_alt_text``.
        :return: The updated HTML string with ``alt`` attributes set for approved/decorative images.
        :rtype: str
        """
        soup = BeautifulSoup(content_html, 'html.parser')
        images = soup.find_all('img')
        if not images:
            return str(soup)

        # Looked up once per content item rather than per img tag; the payload for this
        # content_id is guaranteed present by the caller's approved/decorative filtering.
        image_payloads = next(c for c in self.content_with_alt_text if c['content_id'] == content_id)['images']

        for img in images:
            img_src = img.get('src', '')
            for image_payload in image_payloads:
                if img_src != image_payload['image_url']:
                    continue

                logger.debug(f"Matched image URL {img_src} in content {content_id}")
                if image_payload['action'] == 'approve':
                    img['alt'] = image_payload['approved_alt_text']
                    logger.info(f"Updated alt text for image in content {content_id}")
                elif image_payload['action'] == 'decorative':
                    # Decorative images should be marked presentation with empty alt
                    img['alt'] = ''
                    img['role'] = 'presentation'
                    logger.info(f"Marked decorative image in content {content_id}")
                # skip action does nothing here
        return str(soup)
    
    
    def _get_approved_decorative_content_ids(self) -> List[dict]:
        """
        This will only return content IDs where at least one image has been approved or marked as decorative. 
        A content can have multiple images, but if there is a mix of approved and skipped images, we still want to process the content to update the approved ones.
        Further along the update will only update the images that were approved/decorative.
        
        :param self: Description
        :return: List of dicts containing content_id, content_parent_id and content_type
        :rtype: List[dict]
        """
        approved_decorative_content_ids = [
            {
                "id": c["id"],
                "content_id": c["content_id"],
                "content_parent_id": c.get("content_parent_id"),
                "content_type": c["content_type"]
            }
            for c in self.content_with_alt_text
            if any(img["action"] in ("approve", "decorative") for img in c["images"])
        ]
        logger.info(f"Approved or Decorative content IDs: {approved_decorative_content_ids}")
        return approved_decorative_content_ids
