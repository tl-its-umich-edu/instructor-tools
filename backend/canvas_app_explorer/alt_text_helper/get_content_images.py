import logging
import base64
import asyncio
import time
import base64
import io
import time
from typing import Any, Dict, List, Tuple, Optional
from datetime import timedelta
from django.conf import settings
from asgiref.sync import async_to_sync
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from PIL import Image
from openai import AzureOpenAI
from canvasapi.file import File
from canvasapi.exceptions import CanvasException
from canvasapi import Canvas

logger = logging.getLogger(__name__)


class GetContentImages:
    def __init__(self, course_id: int, canvas_api: Canvas, images_object: List[Dict[str, Any]]):
        self.course_id = course_id
        self.canvas_api: Canvas = canvas_api
        # images_object may be provided by caller; if not, it can be passed later to get_images_by_course
        self.images_object = images_object
        self.max_dimension: int = settings.IMAGE_MAX_DIMENSION
        self.jpeg_quality: int = settings.IMAGE_JPEG_QUALITY

    # TODO: Delete this method, this is a simple prototype for testing OpenAI integration
    def get_alt_text_from_openai(self, imagedata):
      start_time: float = time.perf_counter()
      client = AzureOpenAI(
          api_key=settings.AZURE_API_KEY,
          api_version=settings.AZURE_API_VERSION,
          azure_endpoint = settings.AZURE_API_BASE,
          organization = settings.AZURE_ORGANIZATION)

      prompt = """
          As an AI tool specialized in image recognition, generate concise and descriptive alt text for this image.
          The description should be suitable for a student with a
          vision impairment taking a quiz. Do not include phrases
          like 'This is an image of...'. Provide only one concise
          option with no further explanation.
          """
      messages=[
              {"role": "system", "content": prompt},
              {"role": "user", "content": [
                  {"type": "image_url", "image_url": {
                      "url": f"data:image/jpeg;base64,{imagedata}"}}
              ]
          }
      ]

      response = client.chat.completions.with_raw_response.create(
          model=settings.AZURE_MODEL,
          messages=messages,
          temperature=0.0,
      )
      end_time: float = time.perf_counter()
      logger.info(f"AI call duration: {end_time - start_time:.2f} seconds")
      completion = response.parse()
      alt_text = completion.choices[0].message.content
      logger.info(f"AI response: {alt_text}")

    def get_images_by_course(self):
        """
        Retrieve all image_url and image_id from the database for the given course_id.

        Optionally, a flattened `images_input` list may be provided. If not provided,
        the instance's `images_object` will be used.
        """
        try:
            start_time = time.perf_counter()
            images_list = self.flatten_images_from_content()
            logger.debug(f"Image List : {images_list}")
            
            logger.info(f"Retrieved {len(images_list)} images for course_id: {self.course_id}")
            images_content = self.get_image_content_from_canvas(images_list)
            end_time = time.perf_counter()
            logger.info(f"Fetching image content and Optimizing took {timedelta(seconds=end_time - start_time)} seconds")


            images_combined: List[Dict[str, Any]] = []
            if isinstance(images_content, list):
                errors = [e for e in images_content if isinstance(e, Exception)]
                # If any task failed, wrap and raise a single custom exception so callers can decide how to handle
                if errors:
                    raise ImageContentExtractionException(errors)

                # Build ordered combined list matching images_list to images_content. 
                # This works since asyncio.gather preserves order.
                for idx, content in enumerate(images_content):
                    meta = images_list[idx] if idx < len(images_list) else {}
                    images_combined.append({
                        'image_id': meta.get('image_id'),
                        'image_url': meta.get('image_url'),
                        'content': content
                    })

            # TODO: This will be replaced with actual alt text generation logic
            for image_meta in images_combined:
                content_bytes = image_meta.get('content')
                logger.info(f"Processing image id {image_meta.get('image_id')} url {image_meta.get('image_url')}")
                b64_image_data = base64.b64encode(content_bytes).decode('utf-8')
                self.get_alt_text_from_openai(b64_image_data)
            return images_combined
        except (Exception) as e:
            logger.error(f"Error retrieving images for course_id {self.course_id}: {e}")
            raise e

    def flatten_images_from_content(self) -> List[Dict[int, str]]:
        """Return a flat list of images from a list of content items.

        Each returned dict contains:
        - image_id: int if parseable, otherwise original value or None
        - image_url: the 'download_url' value or None
        """
        images: List[Dict[str, Any]] = []
        for item in self.images_object:
            for img in item.get('images', []):
                image_id = img.get('image_id')
                try:
                    image_id_cast = int(image_id) if image_id is not None else None
                except (ValueError, TypeError):
                    image_id_cast = image_id
                images.append({
                    'image_id': image_id_cast,
                    'image_url': img.get('download_url')
                })
        return images

    @async_to_sync
    async def get_image_content_from_canvas(self, images_list):
        semaphore = asyncio.Semaphore(10)
        async with semaphore:
            tasks = [self.get_image_content_async(image.get('image_id'), image.get('image_url')) for image in images_list]
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_image_content_async(self, image_id, img_url):
        return await asyncio.to_thread(self.get_image_content_sync, image_id, img_url)
    
    def get_image_content_sync(self, image_id, img_url):
        try:
            file = File(self.canvas_api._Canvas__requester, {
                          'id': image_id,
                          'url': img_url })
            image_content = file.get_contents(binary=True)
            optimized_image_content = self.get_optimized_images(image_content, image_id)
            return optimized_image_content
        except (CanvasException, Exception) as req_err:
            logger.error(f"Error fetching image content for image_id {image_id}: {req_err}")
            return req_err

    # https://www.buildwithmatija.com/blog/reduce-image-sizes-ai-processing-costs#the-smart-optimization-strategy
    def get_optimized_images(self, image_content, image_id):
        original_size = len(image_content)
        try:
            # Open with PIL
            img = Image.open(io.BytesIO(image_content))
            original_dimensions = img.size
            original_format = img.format

            # Calculate optimal dimensions
            new_width, new_height = self._calculate_optimal_size(img.size)

            # Resize if necessary
            if max(img.size) > self.max_dimension:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                was_resized = True
            else:
                was_resized = False

            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Save optimized image to bytes buffer
            output_buffer = io.BytesIO()
            img.save(output_buffer, format='JPEG', quality=self.jpeg_quality, optimize=True)
            optimized_bytes = output_buffer.getvalue()
            optimized_size = len(optimized_bytes)

            # Calculate metrics
            size_reduction_percent = ((original_size - optimized_size) / original_size) * 100

            metrics = {
                'original_size_bytes': original_size,
                'optimized_size_bytes': optimized_size,
                'size_reduction_percent': round(size_reduction_percent, 2),
                'original_dimensions': original_dimensions,
                'optimized_dimensions': (new_width, new_height) if was_resized else original_dimensions,
                'was_resized': was_resized,
                'original_format': original_format,
                'optimized_format': 'JPEG'
            }

            logger.debug(f"Optimization metrics for {image_id}: {metrics}")
            logger.info(
                f"Optimized {image_id}: {original_size} \u2192 {optimized_size} bytes "
                f"({size_reduction_percent:.1f}% reduction)"
            )
            return optimized_bytes

        except Exception as e:
            logger.error(f"Failed to optimize image with ID {image_id} due to {e}")
            raise e
      
    def _calculate_optimal_size(self, original_size: Tuple[int, int]) -> Tuple[int, int]:
      """Calculate optimal dimensions maintaining aspect ratio."""
      width, height = original_size

      if max(width, height) <= self.max_dimension:
          return width, height

      if width > height:
          new_width = self.max_dimension
          new_height = int(height * (self.max_dimension / width))
      else:
          new_height = self.max_dimension
          new_width = int(width * (self.max_dimension / height))

      return new_width, new_height
