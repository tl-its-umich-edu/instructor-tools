import json

from Crypto.PublicKey import RSA
from django.core.management import call_command
from django.test import TestCase, SimpleTestCase
from pylti1p3.contrib.django.lti1p3_tool_config.models import LtiTool, LtiToolKey

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

    def test_overrides_strip_both_http_and_https_schemes(self):
        """Test that both http:// and https:// prefixes are stripped from override URLs."""
        urls_https = _resolve_canvas_urls(
            'beta',
            platform_override='https://canvas.beta.instructure.com/',
            auth_domain_override='https://sso.beta.canvaslms.com',
        )
        urls_http = _resolve_canvas_urls(
            'beta',
            platform_override='http://canvas.beta.instructure.com/',
            auth_domain_override='http://sso.beta.canvaslms.com',
        )

        self.assertEqual(urls_https['issuer'], 'https://canvas.beta.instructure.com')
        self.assertEqual(urls_http['issuer'], 'https://canvas.beta.instructure.com')
        self.assertEqual(urls_https['auth_login_url'], 'https://sso.beta.canvaslms.com/api/lti/authorize_redirect')
        self.assertEqual(urls_http['auth_login_url'], 'https://sso.beta.canvaslms.com/api/lti/authorize_redirect')


class TestManagePyltiCommandDatabaseUpdate(TestCase):
    def test_cli_input_creates_and_updates_ltitool_in_db(self):
        key = RSA.generate(1024)
        existing_key = LtiToolKey.objects.create(
            name='ipt-test-key',
            private_key=key.export_key().decode('utf-8'),
            public_key=key.publickey().export_key().decode('utf-8'),
        )

        call_command(
            'manage_pylti',
            '--domain=beta',
            '--client_id=98765',
            '--title=First Title',
            '--tool_key=ipt-test-key',
            '--deployment_ids',
            'dep-1',
            'dep-2',
        )

        created_tool = LtiTool.objects.get(client_id=98765, issuer='https://canvas.beta.instructure.com')
        self.assertEqual(created_tool.title, 'First Title')
        self.assertEqual(created_tool.tool_key_id, existing_key.id)
        self.assertEqual(created_tool.auth_login_url, 'https://sso.beta.canvaslms.com/api/lti/authorize_redirect')
        self.assertEqual(created_tool.auth_token_url, 'https://sso.beta.canvaslms.com/login/oauth2/token')
        self.assertEqual(created_tool.key_set_url, 'https://sso.beta.canvaslms.com/api/lti/security/jwks')
        self.assertEqual(created_tool.deployment_ids, json.dumps(['dep-1', 'dep-2']))

        call_command(
            'manage_pylti',
            '--domain=beta',
            '--client_id=98765',
            '--title=Updated Title',
            '--tool_key=ipt-test-key',
            '--deployment_ids',
            'dep-updated',
        )

        updated_tool = LtiTool.objects.get(client_id=98765, issuer='https://canvas.beta.instructure.com')
        self.assertEqual(updated_tool.id, created_tool.id)
        self.assertEqual(updated_tool.title, 'Updated Title')
        self.assertEqual(updated_tool.deployment_ids, json.dumps(['dep-updated']))