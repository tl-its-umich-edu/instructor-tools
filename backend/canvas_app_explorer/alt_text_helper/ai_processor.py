import logging
import time
from django.conf import settings
from openai import AzureOpenAI
from backend.canvas_app_explorer.decorators import log_execution_time

logger = logging.getLogger(__name__)


class AltTextProcessor:
    """Handles AI-based alt text generation for images using Azure OpenAI."""
    
    def __init__(self):
        """Initialize the AltTextProcessor with Azure OpenAI client configuration."""
        self.client = AzureOpenAI(
            api_key=settings.AZURE_API_KEY,
            api_version=settings.AZURE_API_VERSION,
            azure_endpoint=settings.AZURE_API_BASE,
            organization=settings.AZURE_ORGANIZATION
        )
        self.model = settings.AZURE_MODEL
    
    @log_execution_time
    def generate_alt_text(self, imagedata: str) -> str:
        """
        Generate alt text for an image using Azure OpenAI.
        
        Args:
            imagedata: Base64-encoded image data
            
        Returns:
            Generated alt text string
        """
        prompt = settings.AZURE_ALT_TEXT_PROMPT
        
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
            temperature=settings.AZURE_ALT_TEXT_TEMPERATURE,
        )
        
        completion = response.parse()
        alt_text = completion.choices[0].message.content
        logger.info(f"AI response: {alt_text}")
        
        return alt_text
