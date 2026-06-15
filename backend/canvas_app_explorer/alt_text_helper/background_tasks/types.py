from typing import List, Optional, TypedDict, Union, NotRequired

class CourseScanError(TypedDict):
    """An image that could not be extracted due to an exception.
    type: 
    The error type occurs when performing scan at API level, storing in DB.
    Content Type Fetch failed — this could be when fetching content (assignment | page | quiz | quiz_question) 
    Image Processing Error — this could be when processing an image for alt text generation. (image_process_error | alt_text_process_error)
    DB Failure — this could be when saving content scan results  (content_database_save)
    Token Error - this could be when OAuth token is revoked/bad during start of scan (token_error)
    Any unexpected - this could be any unexpected error that occurs during scan (unexpected_error)
    type_values_all: assignment | page | quiz | question | quiz_question | image_process_error | alt_text_process_error | 
        token_error | content_database_save | course_scan_update_error
    
   title: this is the name of content if error occured when fetching an assignment, a page, a quiz, or a quiz question. This 
   is to show user with page title, assignment name, quiz name, or quiz question text where the error occurred. 
   For errors that are not tied to a specific content item, this can be set to 'Course' this course be when. 
   If error fetching all the content items for assignment, the title would be assignments
   title values: <assignment_name> | <page_name> | <quiz_name> | <quiz_question_name> | Course | assignments | pages | quizzes 

    error: the actual exception object that was raised. 

    canvas_url: the Canvas UI URL that points to the content item that caused the error. 
    This is used and shown to user for reference when they report the error. 
    Look at generate_canvas_content_url in utils.py for what are the URL we are generating.
    """
    type: str          
    title: Optional[str] 
    error: Exception  
    canvas_url: str    


ExtractedImageResult = Union[List[str], List[CourseScanError]]

class ContentItemWithImages(TypedDict):
    """Represents content item with extracted images and their processing results."""
    id: int
    name: str
    images: ExtractedImageResult
    type: str
    content_parent_id: Optional[int]

class ImageAltTextResult(TypedDict):
    """Represents result of processing one image for alt text generation.

    Success shape:
        - {'image': ImageItem, 'alt_text': str}

    Error shape:
        - {'image': ImageItem | None, 'alt_text': '', 'course_scan_error': CourseScanError}
    """
    image: Optional[object]  # ImageItem — avoid circular import by using object
    alt_text: str
    course_scan_error: NotRequired[CourseScanError]  # Present only for error cases

ScanExtractionResult = tuple[List[ContentItemWithImages], List[CourseScanError]]