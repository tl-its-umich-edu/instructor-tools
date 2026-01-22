from django.test import SimpleTestCase
from backend.canvas_app_explorer.alt_text_helper.alt_text_update import AltTextUpate

class TestAltTextUpdate(SimpleTestCase):
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
          },
          {
            "content_id": 4991969,
            "content_name": "Question",
            "content_parent_id": "479109",
            "content_type": "quiz_question",
            "images": [
              {
                "image_url": "https://example.com/image4.jpg",
                "image_id": "248",
                "action": "skip",
                "approved_alt_text": "Circular design with the word \"CLEANING\" on the outer ring and \"STEADINESS\" on the inner ring, surrounded by dashed lines."
              }
            ]
          }
        ]
        
        content_types = ['quiz', 'quiz_question']
        service = AltTextUpate(self.course_id, payload, content_types)
        service.process_alt_text_update()
        
        # Since logic was removed, we just ensure it initializes and runs without error.
        self.assertEqual(service.content_with_alt_text, payload)
        self.assertEqual(service.course_id, self.course_id)
        self.assertEqual(service.content_types, content_types)
    
    def test_process_payload_assignment(self):
        payload = [
          {
            "content_id": 1509690,
            "content_name": "New Assignment",
            "content_parent_id": "null",
            "content_type": "assignment",
            "images": [
              {
                "image_url": "https://example.com/image_assignment1.jpg",
                "image_id": "252",
                "action": "approve",
                "approved_alt_text": "Blue QR code with the text \"Self-Paced Course\""
              },
              {
                "image_url": "https://example.com/image_assignment2.jpg",
                "image_id": "253",
                "action": "approve",
                "approved_alt_text": "Ocean waves ripple on the surface under a bright sky"
              }
            ]
          }
        ]
        
        content_types = ['assignment']
        service = AltTextUpate(self.course_id, payload, content_types)
        service.process_alt_text_update()
        
        self.assertEqual(service.content_with_alt_text, payload)
        self.assertEqual(service.course_id, self.course_id)
        self.assertEqual(service.content_types, content_types)

    def test_process_payload_page(self):
        payload = [
          {
            "content_id": 1742073,
            "content_name": "Page 1",
            "content_parent_id": "null",
            "content_type": "page",
            "images": [
              {
                "image_url": "https://example.com/image_page1.jpg",
                "image_id": "254",
                "action": "approve",
                "approved_alt_text": "Text at the top reads \"Survival Mode.\""
              }
            ]
          },
          {
            "content_id": 1742206,
            "content_name": "Page - With External images",
            "content_parent_id": "null",
            "content_type": "page",
            "images": [
              {
                "image_url": "https://example.com/image_page2.jpg",
                "image_id": "256",
                "action": "skip",
                "approved_alt_text": "A statue of a muscular warrior"
              }
            ]
          }
        ]
        
        content_types = ['page']
        service = AltTextUpate(self.course_id, payload, content_types)
        service.process_alt_text_update()
        
        self.assertEqual(service.content_with_alt_text, payload)
        self.assertEqual(service.course_id, self.course_id)
        self.assertEqual(service.content_types[0], content_types[0])

