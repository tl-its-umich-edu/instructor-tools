import json
from typing import Any, List, TypedDict


class StandardCanvasErrorData(TypedDict):
    message: str


class CanvasHTTPErrorData(TypedDict):
    status_code: int
    message: str


class CanvasHTTPError(Exception):
    """
    Custom exception for HTTP errors originating from Canvas API interactions
    """

    canvas_error_prefix = 'An error occurred while communciating with Canvas. '

    message: str
    status_code: int

    def __init__(self, error_data: Any, status_code: int) -> None:
        if (
            isinstance(error_data, list) and
            all([isinstance(obj, dict) for obj in error_data]) and
            all(['message' in obj for obj in error_data]) and
            all([isinstance(obj['message'], str) for obj in error_data])
        ):
            canvas_error_data: List[StandardCanvasErrorData] = error_data
            joined_error_messages = '; '.join([error['message'] for error in canvas_error_data])
            message_ending = f'"{joined_error_messages}"'
        elif isinstance(error_data, str):
            message_ending = f'"{error_data}"'
        else:
            message_ending = f'Non-standard data shape found: "{json.dumps(error_data)}"'

        self.message = self.canvas_error_prefix + message_ending
        self.status_code = status_code

    def __str__(self) -> str:
        return f'Status code: {self.status_code}; Message: {self.message}'

    def to_dict(self) -> CanvasHTTPErrorData:
        return { 'status_code': self.status_code, 'message': self.message }

class ImageContentExtractionException(Exception):
    """Raised when one or more image content fetch tasks failed.

    Attributes:
        errors (List[Exception]): list of exceptions returned from image fetch tasks
    """
    def __init__(self, errors):
        self.errors = errors
        super().__init__(f"Image content extraction failed with {len(errors)} errors {errors}")

