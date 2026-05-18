from unittest.mock import MagicMock, patch

from django.test import TestCase
from PIL import Image

from backend.canvas_app_explorer.alt_text_helper.ai_processor import AltTextProcessor
from backend.canvas_app_explorer.canvas_lti_manager.exception import AltTextGenerationException


class TestAltTextProcessor(TestCase):
    @patch('backend.canvas_app_explorer.alt_text_helper.ai_processor.AzureOpenAI')
    def test_generate_alt_text_raises_alt_text_generation_exception_on_client_error(self, mock_azure_openai):
        """generate_alt_text should raise AltTextGenerationException when Azure client fails."""
        mock_client = MagicMock()
        mock_azure_openai.return_value = mock_client
        mock_client.chat.completions.with_raw_response.create.side_effect = RuntimeError('azure request failed')

        processor = AltTextProcessor()
        image = Image.new('RGB', (5, 5), color=(255, 255, 255))

        with self.assertRaises(AltTextGenerationException) as ctx:
            processor.generate_alt_text(image, 'https://example.com/img.jpg')

        self.assertIsInstance(ctx.exception.cause, RuntimeError)
        self.assertIn('azure request failed', str(ctx.exception.cause))

    @patch('backend.canvas_app_explorer.alt_text_helper.ai_processor.AzureOpenAI')
    def test_generate_alt_text_raises_alt_text_generation_exception_on_empty_choices(self, mock_azure_openai):
        """generate_alt_text should raise AltTextGenerationException when parsed completion has no choices."""
        mock_client = MagicMock()
        mock_azure_openai.return_value = mock_client

        mock_raw_response = MagicMock()
        mock_raw_response.parse.return_value = MagicMock(choices=[])
        mock_client.chat.completions.with_raw_response.create.return_value = mock_raw_response

        processor = AltTextProcessor()
        image = Image.new('RGB', (5, 5), color=(255, 255, 255))

        with self.assertRaises(AltTextGenerationException) as ctx:
            processor.generate_alt_text(image, 'https://example.com/img.jpg')

        self.assertIn('Invalid API response', str(ctx.exception))
