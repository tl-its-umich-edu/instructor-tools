from typing import List, Dict, Any
from backend.canvas_app_explorer.models import ImageItem

class AltTextUpate:
    def __init__(self, course_id: int, validated_data: List[Dict[str, Any]]):
        self.course_id = course_id
        self.validated_data = validated_data

    def process(self) -> None:
        """
        Process the validated alt text review data.
        """
        pass
