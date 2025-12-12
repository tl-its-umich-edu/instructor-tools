import logging
import base64

from django.conf import settings
from django.db import DatabaseError
from backend.canvas_app_explorer.models import ImageItem
import time
import openai
from openai import AzureOpenAI
import os
import io
from PIL import Image
import base64
import re

logger = logging.getLogger(__name__)


class GetContentImages:
    def __init__(self, course_id, content_type, canvas_api):
        self.content = content_type
        self.course_id = course_id
        self.canvas_api = canvas_api
    
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
            for idx, image in enumerate(images_list, 1):
                img_url = image.get('image_url')
                logger.info(f"[{idx}] image_id: {image['image_id']}, image_url: {img_url}")
                try:
                    # Use the canvas requester to fetch the binary content for the image
                    requester = self.canvas_api._Canvas__requester
                    # Pass the absolute URL using the `_url` kwarg so the Requester doesn't prefix the base api path
                    response = requester.request('GET', _url=img_url, _raw_response=True)
                    response.raise_for_status()
                    image_content = response.content
                    image_content_type = response.headers.get('Content-Type')
                    b64_image_data = base64.b64encode(image_content).decode('utf-8')
                    self.get_alt_text_from_openai(b64_image_data)

                    logger.info(
                        f"Fetched image content for image_id: {image['image_id']}, Content-Type: {image_content_type}, Size: {len(image_content)} bytes"
                    )
                except Exception as req_err:
                    logger.error(f"Error fetching image content for image_id {image['image_id']}: {req_err}")
                    # Continue to next image
                    continue
            return images_list
        except (DatabaseError, Exception) as e:
            logger.error(f"Error retrieving images for course_id {self.course_id}: {e}")
            return []

    def extract_images(self):
        pass