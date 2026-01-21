from django.test import TestCase
from backend.canvas_app_explorer.alt_text_helper.alt_text_update import AltTextUpate

class TestAltTextUpdate(TestCase):
    def setUp(self):
        self.course_id = 12345

    def test_process_payload(self):
        payload = [
          {
            "content_id": 479109,
            "content_name": "Q1",
            "content_parent_id": "null",
            "content_type": "quiz",
            "images": [
              {
                "image_url": "https://example.com/image1.jpg",
                "image_id": "245",
                "action": "approve",
                "approved_alt_text": "Circular diagram with arrows connecting the words \"Experience,\" \"Emotion,\" \"Impression,\" and \"Thought\" in a continuous loop."
              },
              {
                "image_url": "https://example.com/image2.jpg",
                "image_id": "246",
                "action": "skip",
                "approved_alt_text": "Circular design with the words \"Meditation\" and \"Cleaning\" forming the outer ring, and \"Stillness\" and \"Steadiness\" written inside smaller concentric circles."
              }
            ]
          },
          {
            "content_id": 479163,
            "content_name": "Quiz 2 - External Links",
            "content_parent_id": "null",
            "content_type": "quiz",
            "images": [
              {
                "image_url": "https://example.com/image3.jpg",
                "image_id": "247",
                "action": "approve",
                "approved_alt_text": "Two hockey players engaged in a fight on the ice, wearing uniforms from opposing teams, one in blue and white and the other in black and yellow."
              }
            ]
          }
        ]
        
        service = AltTextUpate(self.course_id, payload)
        service.process()
        
        # Since logic was removed, we just ensure it initializes and runs without error.
        self.assertEqual(service.validated_data, payload)
        self.assertEqual(service.course_id, self.course_id)

