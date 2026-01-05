from backend.canvas_app_explorer.alt_text_helper.get_content_images import GetContentImages
from backend.canvas_app_explorer.canvas_lti_manager.exception import ImageContentExtractionException
from django.test import TestCase


class DummyGetContentImages(GetContentImages):
    def __init__(self, images_object):
        # don't need a real canvas_api for this test
        self.course_id = 1
        self.canvas_api = None
        self.images_object = images_object

    def get_image_content_from_canvas(self, images_list):
        # simulate ordered results with a failing first task
        return [Exception('fetch failed'), b'binarydata']

class TestGetContentImages(TestCase):
    def test_get_images_by_course_raises_on_errors(self):
        items = [
            {'id': 1, 'name': 'A', 'images': [{'image_id': '1', 'download_url': 'u1'}]},
            {'id': 2, 'name': 'B', 'images': [{'image_id': '2', 'download_url': 'u2'}]}
        ]
        g = DummyGetContentImages(items)

        with self.assertRaises(ImageContentExtractionException) as cm:
            g.get_images_by_course()

        exc = cm.exception
        self.assertIsInstance(exc.errors, list)
        self.assertEqual(len(exc.errors), 1)
