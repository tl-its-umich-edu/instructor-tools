from django.test import TestCase
from backend.canvas_app_explorer.alt_text_helper.process_content_images import GetContentImages


class TestFlattenImagesFromContent(TestCase):
    def test_flatten_images_from_content_parses_and_extracts(self):
        items = [
            {
                'id': 1509690,
                'name': 'New Assignment',
                'images': [
                    {
                        'image_id': '44125878',
                        'download_url': 'https://canvas-test.it.umich.edu/files/44125878/download?verifier=fPOPQAIAmmu8numuuCQRwLG93ORQWs0w9yFMs8QZ&download_frd=1'
                    }
                ],
                'type': 'assignment',
                'content_parent_id': None,
            },
            {
                'id': 1692426,
                'name': 'Page1',
                'images': [
                    {
                        'image_id': '44125879',
                        'download_url': 'https://canvas-test.it.umich.edu/files/44125879/download?verifier=P3aM1GgYSqQugpGYOHgmiVw84Vt0xaw5Nofvgrpp&download_frd=1'
                    }
                ],
                'type': 'page',
                'content_parent_id': None,
            },
            {
                'id': 470678,
                'name': 'GQ',
                'images': [
                    {
                        'image_id': '44125882',
                        'download_url': 'https://canvas-test.it.umich.edu/files/44125882/download?verifier=n0zb6AyIuBlbgwskCO2p18f4Dx7pQmqtZ6KirTcW&download_frd=1'
                    }
                ],
                'type': 'quiz',
                'content_parent_id': None,
            },
            {
                'id': 4891780,
                'name': 'GQ-Q1',
                'images': [
                    {
                        'image_id': '44125883',
                        'download_url': 'https://canvas-test.it.umich.edu/files/44125883/download?verifier=mGiQl2PLgJGm1gkhhXNzDHzWligy5SkUEXamICAn&download_frd=1'
                    }
                ],
                'type': 'quiz_question',
                'content_parent_id': 470678,
            },
        ]

        expected = [
            {
                'image_id': 44125878,
                'image_url': 'https://canvas-test.it.umich.edu/files/44125878/download?verifier=fPOPQAIAmmu8numuuCQRwLG93ORQWs0w9yFMs8QZ&download_frd=1'
            },
            {
                'image_id': 44125879,
                'image_url': 'https://canvas-test.it.umich.edu/files/44125879/download?verifier=P3aM1GgYSqQugpGYOHgmiVw84Vt0xaw5Nofvgrpp&download_frd=1'
            },
            {
                'image_id': 44125882,
                'image_url': 'https://canvas-test.it.umich.edu/files/44125882/download?verifier=n0zb6AyIuBlbgwskCO2p18f4Dx7pQmqtZ6KirTcW&download_frd=1'
            },
            {
                'image_id': 44125883,
                'image_url': 'https://canvas-test.it.umich.edu/files/44125883/download?verifier=mGiQl2PLgJGm1gkhhXNzDHzWligy5SkUEXamICAn&download_frd=1'
            },
        ]

        g = GetContentImages(course_id=1, canvas_api=None, images_object=items)
        result = g.flatten_images_from_content()
        self.assertEqual(result, expected)
