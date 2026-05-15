import logging
import asyncio
import io
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Optional, Union
from django.conf import settings
from constance import config
from asgiref.sync import async_to_sync
from backend.canvas_app_explorer.canvas_lti_manager.exception import AltTextGenerationException
from backend.canvas_app_explorer.alt_text_helper.ai_processor import AltTextProcessor
from backend.canvas_app_explorer.alt_text_helper.background_tasks.types import ImageAltTextResult, CourseScanError
from backend.canvas_app_explorer.decorators import log_execution_time
from backend.canvas_app_explorer.utils import generate_canvas_content_url
from PIL import Image
import httpx
from backend.canvas_app_explorer.models import ImageItem

logger = logging.getLogger(__name__)


class ProcessContentImages:
    def __init__(self, course_scan_id: int, course_id: int, bearer_token: Optional[str] = None, auth_header: Optional[Dict[str, str]] = None):
        """Process images for a course.

        :param course_scan_id: CourseScan ID used to scope ImageItem rows via ContentItem FK.
        :param course_id: Course ID for logging purposes.
        :param bearer_token: Optional bearer token string to use for Authorization header. If provided,
                             it takes precedence over introspecting the Canvas requester.
        :param auth_header: Optional explicit Authorization header dict to use. Takes highest precedence.
        """
        self.course_scan_id = course_scan_id
        self.course_id = course_id
        self.max_dimension: int = config.IMAGE_MAX_DIMENSION
        self.jpeg_quality: int = config.IMAGE_JPEG_QUALITY
        self.use_canvas_token: bool = config.USE_CANVAS_TOKEN
        self.alt_text_processor = AltTextProcessor()
        # Captures per-image processing failures for downstream handling (e.g., persistence/logging).
        self.error_image_results: List[ImageAltTextResult] = []
        # Explicit header or token provided by caller — prefer these over internal discovery
        self._auth_header = auth_header
        if bearer_token and not self._auth_header:
            self._auth_header = {'Authorization': f'Bearer {bearer_token}'}

    def _build_error_result(
        self,
        error_type: str,
        error: Exception,
        image: Optional[ImageItem] = None,
        canvas_url: Optional[str] = None,
    ) -> ImageAltTextResult:
        """Build a normalized ImageAltTextResult for failure cases."""
        resolved_canvas_url = canvas_url
        error_title = image.content_item.content_name if image else 'Course'
        if not resolved_canvas_url:
            if image:
                content_item = image.content_item
                resolved_canvas_url = generate_canvas_content_url(
                    self.course_id,
                    content_item.content_type,
                    content_item.content_id,
                    content_item.content_parent_id,
                )
            else:
                resolved_canvas_url = f"https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}/courses/{self.course_id}"

        return {
            'image': image,
            'alt_text': '',
            'course_scan_error': {
                'type': error_type,
                'title': error_title,
                'error': error,
                'canvas_url': resolved_canvas_url,
            },
        }


    @log_execution_time
    def retrieve_images_with_alt_text(self) -> Union[bool, List[CourseScanError]]:
        """Process ImageItem records for this course concurrently and generate alt text.

        - Reads ImageItem rows for course_scan_id
        - Fetches image content and generates alt text concurrently (bounded to avoid memory/API spikes)
        - Bulk-updates ImageItem.image_alt_text and ImageItem.image_process_state
        - Marks image download/parse failures as failed, while keeping alt-text failures reviewable
        - Returns True on success, or list of CourseScanError objects on failure
        """
        try:
            qs = ImageItem.objects.filter(content_item__course_scan_id=self.course_scan_id).select_related('content_item')
            logger.info(f"Retrieved {qs.count()} ImageItems for course_scan_id: {self.course_scan_id}, course_id: {self.course_id}")

            to_update = []

            # Collect image models
            image_models = list(qs.iterator())

            # Early return if no images to process
            if not image_models:
                return True

            gen_results = self._process_images_concurrently(image_models)

            for res in gen_results:
                img: ImageItem = res['image']
                alt_text = res['alt_text']

                if res.get('course_scan_error'):
                    error_type = res.get('course_scan_error', {}).get('type')
                    if img:
                        if error_type == 'image_process_error':
                            img.image_process_state = ImageItem.IMAGE_STATE_FAILED
                        else:
                            # Alt-text generation failures remain reviewable by users.
                            img.image_process_state = ImageItem.IMAGE_STATE_SUCCESS
                        to_update.append(img)
                    # Add all errors to error_image_results for logging
                    self.error_image_results.append(res)
                    logger.error(
                        "Processing failed for image %s: %s",
                        img.image_url if img else None,
                        res.get('course_scan_error'),
                    )
                    continue

                if not img:
                    logger.error("Success result missing image object: %s", res)
                    continue

                img_url = img.image_url

                # Skip if alt_text is None or empty string
                if not alt_text:
                    img.image_process_state = ImageItem.IMAGE_STATE_SUCCESS
                    to_update.append(img)
                    logger.warning(f"No alt text generated for image {img_url}")
                    continue

                img.image_alt_text = alt_text
                img.image_process_state = ImageItem.IMAGE_STATE_SUCCESS
                to_update.append(img)
                logger.info(f"Generated alt text for image url={img_url}")


            # Persist alt text/status updates in one pass
            if to_update:
                ImageItem.objects.bulk_update(to_update, ['image_alt_text', 'image_process_state'])
                logger.info(
                    "Updated %d ImageItem records with alt text/process status for course_scan_id %s, course_id: %s",
                    len(to_update),
                    self.course_scan_id,
                    self.course_id,
                )

            if self.error_image_results:
                errors_to_log: list[CourseScanError] = [
                    result['course_scan_error']
                    for result in self.error_image_results
                    if result.get('course_scan_error')
                ]
                logger.info(
                    "Captured %d image processing error result(s) for course_scan_id %s",
                    len(self.error_image_results),
                    self.course_scan_id,
                )
                return errors_to_log

            return True
        except Exception as e:
            logger.error(f"Error retrieving images for course_scan_id {self.course_scan_id}, course_id: {self.course_id}: {e}")
            # Build a new system-level error entry.
            error_result: ImageAltTextResult = self._build_error_result('image_process_error', e)
            # Always append the new error to error_image_results (attribute always exists)
            self.error_image_results.append(error_result)
            errors_to_log: list[CourseScanError] = [
                result['course_scan_error']
                for result in self.error_image_results
                if result.get('course_scan_error')
            ]
            return errors_to_log

    async def get_image_content_async(self, img_url):
        logger.info(f"Fetching image content for url: {img_url}")
        if not img_url:
            err = ValueError(f"No image URL provided for image {img_url}")
            logger.error(err)
            return err

        # Determine if we need auth headers based on domain and config
        domain = urlparse(img_url).netloc
        logger.debug(f"Fetching image from img_url: {img_url}, use_canvas_token: {self.use_canvas_token}")
        if settings.CANVAS_OAUTH_CANVAS_DOMAIN in domain and self.use_canvas_token:
            headers = self._auth_header
            if not headers:
                err = ValueError(f"Auth header missing for image {img_url}")
                logger.error(err)
                return err
        else:
            headers = None

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Only pass headers parameter if headers is not None
                if headers:
                    resp = await client.get(img_url, headers=headers)
                else:
                    resp = await client.get(img_url)
                resp.raise_for_status()
                
                # Validate content-type header
                content_type = resp.headers.get('content-type', '')
                if 'image' not in content_type:
                    raise ValueError(f"Invalid content-type header received: {content_type}")
                image_content = resp.content
                optimized_image_content = self.get_optimized_images(image_content, img_url)
                return optimized_image_content
        except httpx.HTTPStatusError as http_err:
            logger.error(f"HTTP error fetching image {img_url}: {http_err}")
            return http_err
        except Exception as req_err:
            logger.error(f"Error fetching image content for image_url {img_url}, course_scan_id {self.course_scan_id}, course_id: {self.course_id}: {req_err}")
            return req_err

    @log_execution_time
    async def _worker_async(self, image_models: List[ImageItem], concurrency: int) -> List[ImageAltTextResult]:
        """Process images concurrently using semaphore for concurrency control.

        - Fetches image content (async) then generates alt text (in thread)
        - Limits concurrent in-flight tasks via asyncio.Semaphore
        - Success result shape: {'image': ImageItem, 'alt_text': str}
        - Error result shape: {'image': ImageItem|None, 'alt_text': '', 'course_scan_error': CourseScanError}
        """
        sem = asyncio.Semaphore(concurrency)

        async def _process_single_image(img: ImageItem) -> ImageAltTextResult:
            async with sem:
                img_url = img.image_url
                try:
                    # Fetch image content
                    contents = await self.get_image_content_async(img_url)
                    if isinstance(contents, Exception):
                        return self._build_error_result('image_process_error', contents, image=img)

                    # Convert to PIL Image and generate alt text
                    pil_image = Image.open(io.BytesIO(contents))
                    logger.info(f"Generating alt text for image {img_url} using Azure OpenAI")
                    alt_text = await asyncio.to_thread(self.alt_text_processor.generate_alt_text, pil_image, img_url)
                    # Handle None return value by providing empty string fallback
                    return {'image': img, 'alt_text': alt_text or ''}
                except AltTextGenerationException as alt_exc:
                    logger.error(f"AltTextGenerationException for image {img_url}: {alt_exc}")
                    return self._build_error_result('alt_text_process_error', alt_exc, image=img)
                except Exception as e:
                    logger.error(f"Processing exception for image {img_url}: {e}")
                    return self._build_error_result('image_process_error', e, image=img)

        tasks = [_process_single_image(img) for img in image_models]
        return await asyncio.gather(*tasks, return_exceptions=False)

    @log_execution_time
    def _process_images_concurrently(self, image_models: List[ImageItem]) -> List[ImageAltTextResult]:
        """Process images concurrently: fetch content and generate alt text for each, bounded.

        - Uses asyncio.Semaphore to limit concurrent in-flight image processing tasks (from settings IMAGE_PROCESSING_CONCURRENCY)
        - Each task fetches image content (async) then generates alt text (in thread)
        - Success result shape: {'image': ImageItem, 'alt_text': str}
        - Error result shape: {'image': ImageItem|None, 'alt_text': '', 'course_scan_error': CourseScanError}
        """
        concurrency = config.IMAGE_PROCESSING_CONCURRENCY
        return async_to_sync(self._worker_async)(image_models, concurrency)

    # https://www.buildwithmatija.com/blog/reduce-image-sizes-ai-processing-costs#the-smart-optimization-strategy
    def get_optimized_images(self, image_content: bytes, image_url: str) -> bytes:
        """Optimize raw image bytes for downstream alt-text processing.

        Opens image bytes with Pillow, resizes while preserving aspect ratio when
        needed, normalizes color mode to RGB, and re-encodes the result as JPEG.

        :param image_content: Raw bytes fetched from the source image URL.
        :type image_content: bytes
        :param image_url: Source URL used for logging context.
        :type image_url: str
        :return: Optimized JPEG bytes.
        :rtype: bytes
        :raises Exception: Re-raises any optimization error after logging.
        """
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

            logger.debug(f"Optimization metrics for {image_url}: {metrics}")
            logger.info(
                f"Optimized {image_url}: {original_size} \u2192 {optimized_size} bytes "
                f"({size_reduction_percent:.1f}% reduction)"
            )
            return optimized_bytes

        except Exception as e:
            logger.error(f"Failed to optimize image with URL {image_url} due to {e}")
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