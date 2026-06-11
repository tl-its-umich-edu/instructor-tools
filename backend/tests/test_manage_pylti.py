from django.test import SimpleTestCase

from backend.canvas_app_explorer.management.commands.manage_pylti import _resolve_canvas_urls


class TestResolveCanvasUrls(SimpleTestCase):
    def test_prod_and_dev_use_prod_canvas_and_sso_domains(self):
        prod_urls = _resolve_canvas_urls('prod')
        dev_urls = _resolve_canvas_urls('dev')

        self.assertEqual(prod_urls['issuer'], 'https://canvas.instructure.com')
        self.assertEqual(prod_urls['auth_login_url'], 'https://sso.canvaslms.com/api/lti/authorize_redirect')
        self.assertEqual(prod_urls['auth_token_url'], 'https://sso.canvaslms.com/login/oauth2/token')
        self.assertEqual(prod_urls['key_set_url'], 'https://sso.canvaslms.com/api/lti/security/jwks')
        self.assertEqual(dev_urls, prod_urls)

    def test_beta_uses_beta_canvas_and_sso_domains(self):
        urls = _resolve_canvas_urls('beta')

        self.assertEqual(urls['issuer'], 'https://canvas.beta.instructure.com')
        self.assertEqual(urls['auth_login_url'], 'https://sso.beta.canvaslms.com/api/lti/authorize_redirect')
        self.assertEqual(urls['auth_token_url'], 'https://sso.beta.canvaslms.com/login/oauth2/token')
        self.assertEqual(urls['key_set_url'], 'https://sso.beta.canvaslms.com/api/lti/security/jwks')

    def test_test_uses_test_canvas_and_sso_domains(self):
        urls = _resolve_canvas_urls('test')

        self.assertEqual(urls['issuer'], 'https://canvas.test.instructure.com')
        self.assertEqual(urls['auth_login_url'], 'https://sso.test.canvaslms.com/api/lti/authorize_redirect')
        self.assertEqual(urls['auth_token_url'], 'https://sso.test.canvaslms.com/login/oauth2/token')
        self.assertEqual(urls['key_set_url'], 'https://sso.test.canvaslms.com/api/lti/security/jwks')

    def test_overrides_are_normalized_without_protocol_or_trailing_slash(self):
        urls = _resolve_canvas_urls(
            'prod',
            platform_override='https://custom.canvas.example.com/',
            auth_domain_override='custom-sso.example.com/',
        )

        self.assertEqual(urls['issuer'], 'https://custom.canvas.example.com')
        self.assertEqual(urls['auth_login_url'], 'https://custom-sso.example.com/api/lti/authorize_redirect')
        self.assertEqual(urls['auth_token_url'], 'https://custom-sso.example.com/login/oauth2/token')
        self.assertEqual(urls['key_set_url'], 'https://custom-sso.example.com/api/lti/security/jwks')