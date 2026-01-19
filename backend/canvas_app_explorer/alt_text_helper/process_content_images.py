import logging
import asyncio
import io
from typing import Any, Dict, List, Tuple, Optional
from django.conf import settings
from constance import config
from asgiref.sync import async_to_sync
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from backend.canvas_app_explorer.alt_text_helper.ai_processor import AltTextProcessor
from backend.canvas_app_explorer.decorators import log_execution_time
from PIL import Image
import httpx
from backend.canvas_app_explorer.models import ImageItem

logger = logging.getLogger(__name__)


class ProcessContentImages:
    def __init__(self, course_id: int, bearer_token: Optional[str] = None, auth_header: Optional[Dict[str, str]] = None):
        """Process images for a course.

        :param bearer_token: Optional bearer token string to use for Authorization header. If provided,
                             it takes precedence over introspecting the Canvas requester.
        :param auth_header: Optional explicit Authorization header dict to use. Takes highest precedence.
        """
        self.course_id = course_id
        self.max_dimension: int = config.IMAGE_MAX_DIMENSION
        self.jpeg_quality: int = config.IMAGE_JPEG_QUALITY
        self.alt_text_processor = AltTextProcessor()
        # Explicit header or token provided by caller — prefer these over internal discovery
        self._auth_header = auth_header
        if bearer_token and not self._auth_header:
            self._auth_header = {'Authorization': f'Bearer {bearer_token}'}

    @log_execution_time
    def get_images_by_course(self):
        """Compatibility wrapper — now delegates to `retrieve_images_with_alt_text` which is DB-backed."""
        return self.retrieve_images_with_alt_text()

    @log_execution_time
    def retrieve_images_with_alt_text(self) -> Dict[str, Dict[str, Any]]:
        """Process ImageItem records for this course concurrently and generate alt text.

        - Reads ImageItem rows for course_id
        - Fetches image content and generates alt text concurrently (bounded to avoid memory/API spikes)
        - Bulk-updates ImageItem.image_alt_text for successful ones
        - If any fetch/generation failed, raises ImageContentExtractionException with list of errors

        Returns a dict mapping image_url -> {image_url, image_alt_text}
        """
        try:
            qs = ImageItem.objects.filter(course_id=self.course_id)
            logger.info(f"Retrieved {qs.count()} ImageItems for course_id: {self.course_id}")

            results: Dict[str, Dict[str, Any]] = {}
            errors = []
            to_update = []

            # Collect image models
            image_models = list(qs.iterator())

            # Process images concurrently: fetch content and generate alt text for each, bounded
            if image_models:
                gen_results = self._process_images_concurrently(image_models)

                for res in gen_results:
                    img = res['img']
                    alt_or_exc = res['alt_text']
                    img_url = img.image_url

                    if isinstance(alt_or_exc, Exception):
                        logger.error(f"Processing failed for image {img_url}: {alt_or_exc}")
                        errors.append(alt_or_exc)
                        continue

                    # Skip if alt_text is None or empty string
                    if not alt_or_exc:
                        logger.warning(f"No alt text generated for image {img_url}")
                        continue

                    img.image_alt_text = alt_or_exc
                    to_update.append(img)
                    results[img_url] = {
                        'image_url': img_url,
                        'image_alt_text': alt_or_exc
                    }
                    logger.info(f"Generated alt text for image url={img_url}")


            # Bulk update successful alt texts
            if to_update:
                ImageItem.objects.bulk_update(to_update, ['image_alt_text'])
                logger.info(f"Updated {len(to_update)} ImageItem records with alt text for course {self.course_id}")

            if errors:
                # Return successful results but raise to let caller handle failures
                raise ImageContentExtractionException(errors)

            return results
        except Exception as e:
            logger.error(f"Error retrieving images for course_id {self.course_id}: {e}")
            raise e

    async def get_image_content_async(self, img_url):
        headers = self._auth_header
        if not headers:
            err = ValueError(f"Auth header missing for image {img_url}")
            logger.error(err)
            return err

        if not img_url:
            err = ValueError(f"No image URL provided for image {img_url}")
            logger.error(err)
            return err

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(img_url, headers=headers)
                resp.raise_for_status()
                image_content = resp.content
                optimized_image_content = self.get_optimized_images(image_content, img_url)
                return optimized_image_content
        except httpx.HTTPStatusError as http_err:
            logger.error(f"HTTP error fetching image {img_url}: {http_err}")
            return http_err
        except Exception as req_err:
            logger.error(f"Error fetching image content for image_id {img_url}: {req_err}")
            return req_err

    @async_to_sync
    @log_execution_time
    async def _worker_async(self, image_models: List[ImageItem], concurrency: int) -> List[Dict[str, Any]]:
        """Process images concurrently using semaphore for concurrency control.

        - Fetches image content (async) then generates alt text (in thread)
        - Limits concurrent in-flight tasks via asyncio.Semaphore
        - Returns a list of dicts: {'img': ImageItem, 'alt_text': str|Exception}
        """
        sem = asyncio.Semaphore(concurrency)

        async def _process_single_image(img: ImageItem) -> Dict[str, Any]:
            async with sem:
                img_url = img.image_url
                try:
                    # Fetch image content
                    contents = await self.get_image_content_async(img_url)
                    if isinstance(contents, Exception):
                        return {'img': img, 'alt_text': contents}

                    # Convert to PIL Image and generate alt text
                    pil_image = Image.open(io.BytesIO(contents))
                    alt_text = await asyncio.to_thread(self.alt_text_processor.generate_alt_text, pil_image)
                    # Handle None return value by providing empty string fallback
                    return {'img': img, 'alt_text': alt_text or ''}
                except Exception as e:
                    logger.error(f"Processing exception for image {img_url}: {e}")
                    return {'img': img, 'alt_text': e}

        tasks = [_process_single_image(img) for img in image_models]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def _process_images_concurrently(self, image_models: List[ImageItem]) -> List[Dict[str, Any]]:
        """Process images concurrently: fetch content and generate alt text for each, bounded.

        - Uses asyncio.Semaphore to limit concurrent in-flight image processing tasks (from settings IMAGE_PROCESSING_CONCURRENCY)
        - Each task fetches image content (async) then generates alt text (in thread)
        - Returns a list of dicts: {'img': ImageItem, 'alt_text': str|Exception}
        """
        concurrency = config.IMAGE_PROCESSING_CONCURRENCY
        return self._worker_async(image_models, concurrency)

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