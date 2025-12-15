import logging
import base64

from django.conf import settings
from django.db import DatabaseError
from backend.canvas_app_explorer.models import ImageItem
import time
from openai import AzureOpenAI
from canvasapi.file import File
from canvasapi.exceptions import CanvasException
from asgiref.sync import async_to_sync
from PIL import Image
import asyncio
import base64

logger = logging.getLogger(__name__)


class GetContentImages:
    def __init__(self, course_id, content_type, canvas_api):
        self.content = content_type
        self.course_id = course_id
        self.canvas_api = canvas_api


    # TODO: Delete this method, this is a simple prototype for testing OpenAI integration
    def get_alt_text_from_openai(self, imagedata):
      start_time: float = time.perf_counter()
      client = AzureOpenAI(
          api_key=settings.OPENAI_API_KEY,
          api_version=settings.API_VERSION,
          azure_endpoint = settings.OPENAI_API_BASE,
          organization = settings.OPENAI_ORGANIZATION)

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
          model=settings.MODEL,
          messages=messages,
          temperature=0.0,
      )
      end_time: float = time.perf_counter()
      logger.info(f"OpenAI call duration: {end_time - start_time:.2f} seconds")
      completion = response.parse()
      alt_text = completion.choices[0].message.content
      logger.info(f"OpenAI response: {alt_text}")

    def get_images_by_course(self):
        """
        Retrieve all image_url and image_id from the database for the given course_id.
        """
        try:
            images = ImageItem.objects.filter(course_id=self.course_id).values('image_id', 'image_url')
            images_list = list(images)
            
            logger.info(f"Retrieved {len(images_list)} images for course_id: {self.course_id}")
            images_content = self.get_image_content_from_canvas(images_list)
            if isinstance(images_content, Exception):
                logger.error(f"Error fetching image content: {images_content}")
                return []
            # b64_image_data = base64.b64encode(results[0]).decode('utf-8')
            # self.get_alt_text_from_openai(b64_image_data)
            return images_list
        except (DatabaseError, Exception) as e:
            logger.error(f"Error retrieving images for course_id {self.course_id}: {e}")
            return []

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
            logger.info(
                f"Fetched image content for image_id: {image_id}, Content-Type:, Size: {len(image_content)} bytes"
            )
            return image_content
        except (CanvasException, Exception) as req_err:
            logger.error(f"Error fetching image content for image_id {image_id}: {req_err}")
            return req_err
    
    def get_optimized_images(self, images_list):
        pass
        