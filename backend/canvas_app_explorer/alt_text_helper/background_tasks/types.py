from typing import List, Optional, TypedDict, Union


class ImageEntry(TypedDict, total=False):
    """Represents an extracted image URL with its processing status."""
    url: str  # Image URL
    content_type: str  # assignment, page, quiz, question
    status: str  # 'success' or 'error'
    error: Optional[Exception]  # Exception object when status is 'error'
    error_type: Optional[str]  # e.g. question_type_error


class ContentItemWithImages(TypedDict):
    """Represents content item with extracted images and their processing results."""
    id: int
    name: str
    images: List[ImageEntry]
    type: str
    content_parent_id: Optional[int]


class QuizQuestionFetchError(TypedDict):
    """Represents a quiz question fetch failure with associated quiz metadata."""
    type: str
    quiz_id: Optional[int]
    quiz_title: str
    error: Exception


class CourseFetchError(TypedDict):
    """Represents a course-level content fetch failure with associated metadata."""
    type: str
    course_id: Optional[int]
    error: Exception


class CanvasManagerSetupError(TypedDict):
    """Represents a failure to create the Canvas API manager (e.g., OAuth error)."""
    type: str
    course_id: Optional[int]
    course_scan_id: Optional[int]
    error: Exception


class ImageAltTextResult(TypedDict):
    """Represents the result of processing a single image for alt text generation.

    The 'type' field discriminates the outcome:
      - 'success'        — alt text was generated; alt_text is a str
      - 'image_error'    — image fetch or Pillow processing failed; alt_text is an Exception
      - 'alt_text_error' — Azure OpenAI call failed; alt_text is an Exception
    """
    type: str  # 'success' | 'image_error' | 'alt_text_error'
    img: Optional[object]  # ImageItem — avoid circular import by using object; None for system-level errors
    alt_text: Union[str, Exception]
