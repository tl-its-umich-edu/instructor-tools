import logging
import time
import base64
import io
from typing import Optional
from django.conf import settings
from constance import config
from openai import OpenAI
from PIL import Image
from backend.canvas_app_explorer.decorators import log_execution_time
from backend.canvas_app_explorer.canvas_lti_manager.exception import AltTextGenerationException

logger = logging.getLogger(__name__)


class AltTextProcessor:
    """Handles AI-based alt text generation through an OpenAI-compatible gateway."""
    
    def __init__(self):
        """Initialize the AltTextProcessor with generic AI gateway configuration."""
        self.client = OpenAI(
            api_key=config.AI_API_KEY,
            base_url=config.AI_API_BASE,
        )
        self.model = config.AI_MODEL
    
    @log_execution_time
    def generate_alt_text(self, image: Image.Image, image_url: str) -> Optional[str]:
        """
        Generate alt text for an image using an OpenAI-compatible gateway.
        
        Args:
            image: PIL Image object (will be converted to JPEG)
            
        Returns:
            Generated alt text string, or None if generation fails
        """
        logger.info(f"Starting alt text generation for image: {image_url}")
        try:
            # Encode image to base64 (converts to JPEG if needed)
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG')
            imagedata = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            prompt = config.AI_ALT_TEXT_PROMPT
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{imagedata}"}}
                ]}
            ]
            
            response = self.client.chat.completions.with_raw_response.create(
                model=self.model,
                messages=messages,
                temperature=config.AI_ALT_TEXT_TEMPERATURE,
            )
            
            completion = response.parse()
            
            # Validate that completion and choices exist before accessing
            if not completion or not completion.choices or len(completion.choices) == 0:
                error_msg = (
                    f"Invalid API response: completion={completion}, "
                    f"choices={completion.choices if completion else 'completion is None'}, "
                    f"parsed_response={completion}"
                )
                logger.error(error_msg)
                raise AltTextGenerationException(ValueError(error_msg))
            
            alt_text = completion.choices[0].message.content
            logger.info(f"AI response: {alt_text}")
            
            return alt_text
        except Exception as e:
            logger.error(f"Alt text generation failed for image '{image_url}': {e}")
            raise AltTextGenerationException(e) from e
