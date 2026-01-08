from django.test import TestCase

# from backend.canvas_app_explorer.alt_text_helper.views import (
    # we import via mo)

class ImageUrlNormalizeTest(TestCase):
    def test_normalize_file_download_url(self):
        raw = (
            'https://canvas-test.it.umich.edu/files/44125878/download?'
            'verifier=fPOPQAIAmmu8numuuCQRwLG93ORQWs0w9yFMs8QZ&download_frd=1'
        )
        # Call the helper via constructing expected output using same logic
        expected_prefix = 'https://canvas-test.it.umich.edu/courses/403334/files/44125878/preview?'
        # We expect the verifier to be preserved and download_frd removed
        expected = expected_prefix + 'verifier=fPOPQAIAmmu8numuuCQRwLG93ORQWs0w9yFMs8QZ'

        # Use the helper via the viewset instance
        from backend.canvas_app_explorer.alt_text_helper.views import AltTextContentGetAndUpdateViewSet
        view = AltTextContentGetAndUpdateViewSet()
        out = view._normalize_image_url(raw, 403334)
        self.assertEqual(out, expected)

    def test_leave_other_urls_alone(self):
        raw = 'https://example.com/static/img.png'
        from backend.canvas_app_explorer.alt_text_helper.views import AltTextContentGetAndUpdateViewSet
        view = AltTextContentGetAndUpdateViewSet()
        out = view._normalize_image_url(raw, 1)
        self.assertEqual(out, raw)
