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
from typing import List, Literal, TypeVar, TypedDict, Union
from bs4 import BeautifulSoup

from django.conf import settings

logger = logging.getLogger(__name__)
T = TypeVar("T")
R = TypeVar("R")

class ImagePayload(TypedDict):
    image_url: str
    image_id: str
    action: Literal["approve", "skip"]
    approved_alt_text: str
    image_url_for_update: str 

class ContentPayload(TypedDict):
    content_id: int
    content_name: str
    content_parent_id: str | None
    content_type: Literal["assignment", "quiz", "page", "quiz_question"]
    images: List[ImagePayload]
    
PER_PAGE = 100
class AltTextUpate:
    def __init__(self, course_id: int, canvas_api: Canvas, content_with_alt_text: List[ContentPayload], content_types: List[str]) -> None:
        self.course: Course = Course(canvas_api._Canvas__requester, {'id': course_id})
        self.canvas_api = canvas_api
        self.content_with_alt_text: List[ContentPayload] = self._enrich_content_with_ui_urls(content_with_alt_text)
        self.content_types: List[str] = content_types
    
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
            self._process_quiz_and_questions(quiz_types)
        else: 
            logger.warning("No valid content types found for alt text update")


    def _process_page(self) -> None:
        logger.info("Processing page alt text update for course_id %s", self.course.id)
        approved_content = self._get_approved_content_ids()
        page_ids = {item["content_id"] for item in approved_content}
        try:
            pages: Page = list(self.course.get_pages(include=['body'], per_page=PER_PAGE))
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to fetch pages for course ID {self.course.id}: {e}")
            raise e
        # this filters Content: pages from API call to only those with approved images content IDs. 
        approved_pages: Page = [p for p in pages if getattr(p, "page_id", None) in page_ids]
        page_alt_text_update_results = self._update_page_alt_text(approved_pages)
        
        exceptions = []
        for page, result in zip(approved_pages, page_alt_text_update_results):
            if isinstance(result, Exception):
                exceptions.append(f"Page {page.page_id} with name {page.title} failed due to {result}") 
        if exceptions:
            all_errors = "; ".join(exceptions)
            logger.error(f"Error updating page alt text: {all_errors}")
            raise Exception(all_errors)

    def _process_assignment(self) -> None:
        approved_content = self._get_approved_content_ids()
        assignment_ids = {item["content_id"] for item in approved_content}
        # making api calls for fetching assignments
        try:
            assignments: Assignment = list(self.course.get_assignments(per_page=PER_PAGE))
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to fetch assignments for course ID {self.course.id}: {e}")
            raise e
        
        # this filters Content: assignments from API call to only those with approved images content IDs.
        approved_assignment: Assignment = [a for a in assignments if a.id in assignment_ids]
        assign_alt_text_update_results = self._update_assignment_alt_text(approved_assignment)
        
        exceptions = []
        for assignment, result in zip(approved_assignment, assign_alt_text_update_results):
            if isinstance(result, Exception):
                exceptions.append(f"Assignment {assignment.id} with name {assignment.name} failed due to {result}")
        
        if exceptions:
            all_errors = "; ".join(exceptions)
            logger.error(f"Error updating assignment alt text: {all_errors}")
            raise Exception(all_errors)
    
    def _process_quiz_and_questions(self, quiz_types: List[str]) -> None:
        logger.info("Processing quiz alt text update for course_id %s with quiz types %s", self.course.id, quiz_types)
        approved_content = self._get_approved_content_ids()
        
        # 1. Process Quizzes (Description)
        approved_quizzes = {c['content_id'] for c in approved_content if c['content_type'] == 'quiz'}
        approved_quiz_questions = [c for c in approved_content if c['content_type'] == 'quiz_question']

        # it is not impoertant to fetch quizzes if there are no approved quizzes to update
        if approved_quizzes:
            quizzes_result = self._get_quizzes()
            if isinstance(quizzes_result, Exception):
                logger.error(f"Failed to fetch quizzes: {quizzes_result}")
            else:
                quizzes_to_update = self._filter_approved_quizzes_for_update(quizzes_result, approved_quizzes)
                for q in quizzes_to_update: logger.info(f"Quiz to Update Id {q.id} Name: {q.title}")
                quizzes_alt_text_update_results = self._update_quiz_alt_text_new(quizzes_to_update)
        
        # 2. Process Quiz Questions Results if there are approved quiz questions
        if approved_quiz_questions:
            result_quiz_questions = self.get_quiz_questions(approved_quiz_questions)
            if isinstance(result_quiz_questions, Exception):
                logger.error(f"Failed to fetch quiz questions: {result_quiz_questions}")
            else:
                # Flatten the results - result_quiz_questions is a list of lists or exceptions
                all_questions = []
                for res in result_quiz_questions:
                    if isinstance(res, Exception):
                        logger.error(f"Failed to fetch a batch of quiz questions: {res}")
                    else:
                        all_questions.extend(res if res else [])
                
                approved_question_ids = {c['content_id'] for c in approved_quiz_questions}
                questions_to_update = self._filter_approved_questions_for_update(all_questions, approved_question_ids)
                
                for q in questions_to_update:
                    logger.info(f"Question Id {q.id} quiz id: {q.quiz_id}: Name: {q.question_name}")
                questions_alt_text_update_results = self._update_quiz_question_alt_text_new(questions_to_update)
        
       
    def _filter_approved_quizzes_for_update(self, quizzes: List[Quiz], approved_quiz_ids: set) -> List[Quiz]:
        return [q for q in quizzes if q.id in approved_quiz_ids]

    def _filter_approved_questions_for_update(self, questions: List[QuizQuestion], approved_question_ids: set) -> List[QuizQuestion]:
        return [q for q in questions if q.id in approved_question_ids]
    
    def _get_quizzes(self) -> List[Quiz]:
        try:
            return list(self.course.get_quizzes(per_page=PER_PAGE))
        except (CanvasException, Exception) as e:
            logger.error(f"Failed to fetch quizzes for course ID {self.course.id}: {e}")
            raise e
        
    
    def process_quiz(self, quiz_types: List[str]) -> None:
        logger.info("Processing quiz alt text update for course_id %s with quiz types %s", self.course.id, quiz_types)
        approved_content = self._get_approved_content_ids()
        
        # 1. Process Quizzes (Description)
        quiz_items_for_update = {c['content_id'] for c in approved_content if c['content_type'] == 'quiz'}
        question_items_for_update = [c for c in approved_content if c['content_type'] == 'quiz_question']

        results_get_quiz_and_questions = self.get_quiz_questions(quiz_items_for_update, question_items_for_update)
        
        if quiz_items_for_update:
            quizzes: Quiz = list(self.course.get_quizzes(per_page=PER_PAGE))
            quizzes_filtered: Quiz = [q for q in quizzes if q.id in quiz_items_for_update]
            
            extracted_quizzes = []
            for quiz in quizzes_filtered:
                extracted_quizzes.append({
                    "id": quiz.id,
                    "name": quiz.title,
                    "html": quiz.description
                })
                logger.info(f"Quiz ID: {quiz.id}, Title: {quiz.title}")
            self._update_quiz_alt_text(extracted_quizzes)

        # 2. Process Quiz Questions

        if not question_items_for_update:
            return
        # Group by parent_id (quiz_id)
        quiz_parent_ids = {c['content_parent_id'] for c in question_items_for_update if c.get('content_parent_id')}
        
        for quiz_id in quiz_parent_ids:
            # Mock Quiz Object using the user provided logic
            made_quiz = Quiz(self.canvas_api._Canvas__requester, {'id': quiz_id, 'course_id': self.course.id})
            
            # Real API call for questions
            questions = list(made_quiz.get_questions(per_page=PER_PAGE))
            
            # Filter questions belonging to this quiz that need updates
            target_question_ids = {c['content_id'] for c in question_items_for_update if str(c.get('content_parent_id')) == str(quiz_id)}
            # Note: ensure type matching for IDs (str vs int). Canvas IDs are ints, content_parent_id might be str from TypedDict
            
            questions_filtered = [q for q in questions if q.id in target_question_ids]
            logger.info(f"Found {len(questions_filtered)} questions to update for Quiz Questions: {questions_filtered}")
            
            extracted_questions = []
            for question in questions_filtered:
                extracted_questions.append({
                    "id": question.id,
                    "quiz_id": quiz_id,
                    "name": question.question_name,
                    "html": question.question_text
                })
                logger.info(f"Quiz Question ID: {question.id}, Name: {question.question_name}")
            
            self._update_quiz_question_alt_text(extracted_questions)
    
    
    def _update_quiz_alt_text(self, content_list: List[dict]) -> None:
        logger.info("Updating quiz alt text for course_id %s %s", self.course.id, content_list)
        for content in content_list:
            logger.info(f"Updating Quiz ID: {content['id']}")
            updated_description = self._update_alt_text_html(content)
            quiz = Quiz(self.canvas_api._Canvas__requester, {'id': content['id'], 'course_id': self.course.id})
            quiz.edit(quiz={'description': updated_description})

    def _update_quiz_question_alt_text(self, content_list: List[dict]) -> None:
        logger.info("Updating quiz question alt text for quiz_id %s", content_list)
        for content in content_list:
            logger.info(f"Updating Quiz Question ID: {content['id']}")
            updated_text = self._update_alt_text_html(content)
            # quiz = Quiz(self.canvas_api._Canvas__requester, {'id': content['quiz_id'], 'course_id': self.course.id})
            quiz_question = QuizQuestion(self.canvas_api._Canvas__requester, {'id': content['id'], 'quiz_id': content['quiz_id'], 
                                                                              'course_id': self.course.id, 'question_name': 'place_holder'})
            # Use edit_question on the quiz object
            quiz_question.edit(question={'question_text': updated_text})
    
    @async_to_sync
    async def get_quiz_questions(self, quiz_questions: List[dict]) -> None:
        async with asyncio.Semaphore(10):
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
    async def _update_quiz_alt_text_new(self, approved_quizzes: List[Quiz]) -> None:
        async with asyncio.Semaphore(10):
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
    async def _update_quiz_question_alt_text_new(self, approved_quiz_questions: List[QuizQuestion]) -> None:
        async with asyncio.Semaphore(10):
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
        async with asyncio.Semaphore(10):
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

    async def update_content_items_async(self, fn: Callable[[T], R], ctx: T) -> Union[R, Exception]:
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
        async with asyncio.Semaphore(10):
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
        This returns updated HTML content with  alt text changes for images that are approved only.
        
        :param self: Description
        :param content: Description
        :return: Description
        :rtype: Any
        """
        soup = BeautifulSoup(content_html, 'html.parser')
        images = soup.find_all('img')
        for img in images:
            for image_payload in next(c for c in self.content_with_alt_text if c['content_id'] == content_id)['images']:
                if img.get('src') == image_payload['image_url_for_update']:
                    if image_payload['action'] == 'approve':
                        img['alt'] = image_payload['approved_alt_text']
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
        
