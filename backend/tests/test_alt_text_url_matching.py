"""
Test suite for URL matching in AltTextUpdate._update_alt_text_html.

The scan stores the raw ``img src`` and the review payload echoes that same value back, so
matching an approved image to its tag in the re-fetched Canvas HTML is a plain exact string
comparison. These tests pin that contract down, including the cases where a near-miss URL
must NOT be updated.
"""

from django.test import TestCase

from backend.canvas_app_explorer.alt_text_helper.alt_text_update import AltTextUpdate


class DummyCanvasAPI:
    """Minimal stand-in for Canvas API used by the AltTextUpdate constructor."""
    _Canvas__requester = None


CANVAS_FILE_URL = 'https://umich.instructure.com/courses/403334/files/42932047/preview'
EXTERNAL_URL = 'https://external.example.com/assets/chart.png'


def build_updater(images, content_id=42):
    payload = [{
        'id': 1,
        'content_id': content_id,
        'content_type': 'page',
        'images': images,
    }]
    return AltTextUpdate(
        course_id=1,
        canvas_api=DummyCanvasAPI(),
        content_with_alt_text=payload,
        content_types=['page'],
    )


class TestAltTextUrlMatching(TestCase):

    def test_canvas_file_url_matched_exactly_and_alt_updated(self):
        updater = build_updater([{
            'image_id': '100',
            'image_url': CANVAS_FILE_URL,
            'action': 'approve',
            'approved_alt_text': 'A bar chart of enrollment by term',
        }])
        html = f'<p><img src="{CANVAS_FILE_URL}" alt="chart.png"></p>'

        updated = updater._update_alt_text_html(42, html)

        self.assertIn('alt="A bar chart of enrollment by term"', updated)
        self.assertNotIn('alt="chart.png"', updated)

    def test_external_url_matched_exactly_and_alt_updated(self):
        updater = build_updater([{
            'image_id': '101',
            'image_url': EXTERNAL_URL,
            'action': 'approve',
            'approved_alt_text': 'External diagram',
        }])
        html = f'<p><img src="{EXTERNAL_URL}" alt=""></p>'

        updated = updater._update_alt_text_html(42, html)

        self.assertIn('alt="External diagram"', updated)

    def test_url_differing_only_by_query_string_is_not_matched(self):
        """A src whose query string drifted from the stored URL must be left untouched.

        Exact matching is strictly stronger than the file_id containment match it replaced:
        same file, different verifier means no update.
        """
        updater = build_updater([{
            'image_id': '102',
            'image_url': f'{CANVAS_FILE_URL}?verifier=STORED',
            'action': 'approve',
            'approved_alt_text': 'Should not be applied',
        }])
        html = f'<p><img src="{CANVAS_FILE_URL}?verifier=DIFFERENT" alt="original.png"></p>'

        updated = updater._update_alt_text_html(42, html)

        self.assertIn('alt="original.png"', updated)
        self.assertNotIn('Should not be applied', updated)

    def test_query_string_preserved_when_matched(self):
        """An exact match including query params updates alt and keeps the src intact."""
        url = f'{CANVAS_FILE_URL}?verifier=abc123&wrap=1'
        updater = build_updater([{
            'image_id': '103',
            'image_url': url,
            'action': 'approve',
            'approved_alt_text': 'Matched with query',
        }])
        # Canvas serves & entity-encoded inside attributes; BeautifulSoup decodes on read
        # and re-encodes on write, so the round trip is byte-stable.
        html = f'<p><img src="{CANVAS_FILE_URL}?verifier=abc123&amp;wrap=1" alt="x.png"></p>'

        updated = updater._update_alt_text_html(42, html)

        self.assertIn('alt="Matched with query"', updated)
        self.assertIn('verifier=abc123&amp;wrap=1', updated)

    def test_only_the_approved_image_is_updated_among_several(self):
        other_url = 'https://umich.instructure.com/courses/403334/files/99999999/preview'
        updater = build_updater([
            {
                'image_id': '104',
                'image_url': CANVAS_FILE_URL,
                'action': 'approve',
                'approved_alt_text': 'Approved alt',
            },
            {
                'image_id': '105',
                'image_url': other_url,
                'action': 'skip',
                'approved_alt_text': 'ignored',
            },
        ])
        html = (
            f'<p><img src="{CANVAS_FILE_URL}" alt="first.png">'
            f'<img src="{other_url}" alt="second.png"></p>'
        )

        updated = updater._update_alt_text_html(42, html)

        self.assertIn('alt="Approved alt"', updated)
        # the skipped image keeps its original alt
        self.assertIn('alt="second.png"', updated)

    def test_repeated_src_updates_every_occurrence(self):
        """The same image used twice in one document gets updated in both places."""
        updater = build_updater([{
            'image_id': '106',
            'image_url': CANVAS_FILE_URL,
            'action': 'approve',
            'approved_alt_text': 'Shared image',
        }])
        html = (
            f'<p><img src="{CANVAS_FILE_URL}" alt="a.png"></p>'
            f'<p><img src="{CANVAS_FILE_URL}" alt="b.png"></p>'
        )

        updated = updater._update_alt_text_html(42, html)

        self.assertEqual(updated.count('alt="Shared image"'), 2)

    def test_decorative_action_sets_presentation_role_on_exact_match(self):
        updater = build_updater([{
            'image_id': '107',
            'image_url': CANVAS_FILE_URL,
            'action': 'decorative',
            'approved_alt_text': 'ignored',
        }])
        html = f'<p><img src="{CANVAS_FILE_URL}" alt="old"></p>'

        updated = updater._update_alt_text_html(42, html)

        self.assertIn('role="presentation"', updated)
        self.assertIn('alt=""', updated)

    def test_html_without_images_returned_unchanged(self):
        updater = build_updater([{
            'image_id': '108',
            'image_url': CANVAS_FILE_URL,
            'action': 'approve',
            'approved_alt_text': 'unused',
        }])
        html = '<p>No images in this body.</p>'

        self.assertEqual(updater._update_alt_text_html(42, html), html)

    def test_img_without_src_is_skipped(self):
        updater = build_updater([{
            'image_id': '109',
            'image_url': CANVAS_FILE_URL,
            'action': 'approve',
            'approved_alt_text': 'Approved alt',
        }])
        html = f'<p><img alt="no source"><img src="{CANVAS_FILE_URL}" alt="real.png"></p>'

        updated = updater._update_alt_text_html(42, html)

        self.assertIn('alt="no source"', updated)
        self.assertIn('alt="Approved alt"', updated)
