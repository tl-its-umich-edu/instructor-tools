from typing import List, Optional, TypedDict, Union, NotRequired

class CourseScanError(TypedDict):
    """An image that could not be extracted due to an exception."""
    type: str           # content type where the failure occurred: assignment | page | quiz | question | quiz_question
    title: Optional[str]  # content title/context (e.g., assignment name, quiz name, or Course)
    error: Exception    # the raised exception
    canvas_url: str     # Canvas UI URL pointing to the failing content item


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


class ScanState(TypedDict):
    """Typed response payload for content extraction/persistence state."""
    type: str
    state: str
