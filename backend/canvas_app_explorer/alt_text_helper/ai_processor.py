import logging
import time
import base64
import io
from typing import Optional
from django.conf import settings
from constance import config
from openai import AzureOpenAI
from PIL import Image
from backend.canvas_app_explorer.decorators import log_execution_time

logger = logging.getLogger(__name__)


class AltTextProcessor:
    """Handles AI-based alt text generation for images using Azure OpenAI."""
    
    def __init__(self):
        """Initialize the AltTextProcessor with Azure OpenAI client configuration."""
        self.client = AzureOpenAI(
            api_key=config.AZURE_API_KEY,
            api_version=config.AZURE_API_VERSION,
            azure_endpoint=config.AZURE_API_BASE,
            organization=config.AZURE_ORGANIZATION
        )
        self.model = config.AZURE_MODEL
    
    @log_execution_time
    def generate_alt_text(self, image: Image.Image) -> Optional[str]:
        """
        Generate alt text for an image using Azure OpenAI.
        
        Args:
            image: PIL Image object (will be converted to JPEG)
            
        Returns:
            Generated alt text string, or None if generation fails
        """
        # Encode image to base64 (converts to JPEG if needed)
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='JPEG')
        imagedata = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        prompt = config.AZURE_ALT_TEXT_PROMPT
        
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
            temperature=config.AZURE_ALT_TEXT_TEMPERATURE,
        )
        
        completion = response.parse()
        
        # Validate that completion and choices exist before accessing
        if not completion or not completion.choices or len(completion.choices) == 0:
            logger.error(
                f"Invalid API response: completion={completion}, "
                f"choices={completion.choices if completion else 'completion is None'}, "
                f"parsed_response={completion}"
            )
            return None
        
        alt_text = completion.choices[0].message.content
        logger.info(f"AI response: {alt_text}")
        
        return alt_text
