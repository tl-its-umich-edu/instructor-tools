import json
from Crypto.PublicKey import RSA
from django.core.management.base import BaseCommand, CommandParser

# https://github.com/dmitry-viskov/pylti1.3/blob/master/pylti1p3/contrib/django/lti1p3_tool_config/models.py
from pylti1p3.contrib.django.lti1p3_tool_config.models import LtiToolKey, LtiTool


CANVAS_DOMAIN_MAP = {
    'prod': {
        'platform': 'canvas.instructure.com',
        'auth_domain': 'sso.canvaslms.com',
    },
    'dev': {
        'platform': 'canvas.instructure.com',
        'auth_domain': 'sso.canvaslms.com',
    },
    'beta': {
        'platform': 'canvas.beta.instructure.com',
        'auth_domain': 'sso.beta.canvaslms.com',
    },
    'test': {
        'platform': 'canvas.test.instructure.com',
        'auth_domain': 'sso.test.canvaslms.com',
    },
}


def _normalize_domain_value(value: str) -> str:
    normalized_value = value.strip().lower()
    if normalized_value.startswith('https://'):
        normalized_value = normalized_value[len('https://'):]
    return normalized_value.rstrip('/')


def _resolve_canvas_urls(domain: str, platform_override: str | None = None, auth_domain_override: str | None = None) -> dict[str, str]:
    domain_config = CANVAS_DOMAIN_MAP[domain]
    platform_host = _normalize_domain_value(platform_override) if platform_override else domain_config['platform']
    auth_domain_host = _normalize_domain_value(auth_domain_override) if auth_domain_override else domain_config['auth_domain']

    issuer = f'https://{platform_host}'
    auth_base = f'https://{auth_domain_host}'

    return {
        'issuer': issuer,
        'auth_login_url': f'{auth_base}/api/lti/authorize_redirect',
        'auth_token_url': f'{auth_base}/login/oauth2/token',
        'key_set_url': f'{auth_base}/api/lti/security/jwks',
    }


class Command(BaseCommand):
    help = """Used to create & update the LTI keys in the database for this application.
    This will generate a key pair named as the "tool_key" arg and add them to the pylti13 database. 
    This command can be re-run with the same Canvas domain selection and "client_id" to update a previous tool. 
    """

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('--domain', dest='domain', choices=sorted(CANVAS_DOMAIN_MAP.keys()),
                            help='Canvas environment shortcut used to generate issuer and auth URLs.',
                            default='prod')
        parser.add_argument('--platform', dest='platform', type=str,
                            help='Optional issuer domain override, with or without https://',
                            default=None)
        parser.add_argument('--auth_domain', dest='auth_domain', type=str,
                            help='Optional auth/jwks domain override, with or without https://',
                            default=None)
        parser.add_argument('--client_id', dest='client_id', type=int, required=True, help="Canvas LTI Client ID")
        parser.add_argument('--title', dest='title', required=True, type=str, help="LTI Title")
        parser.add_argument('--tool_key', '--key', dest='tool_key', required=True, type=str,
                            help="Name of Tool Key to use, will create if new")
        parser.add_argument('--deployment_ids', dest='deployment_ids',
                            nargs='*', type=str, help="List of Deployment ID(s). Can be multiple.", default="")

    def handle(self, *args, **options: dict):
        url_config = _resolve_canvas_urls(
            options['domain'],
            platform_override=options['platform'],
            auth_domain_override=options['auth_domain'],
        )
        issuer = url_config['issuer']
        auth_login_url = url_config['auth_login_url']
        auth_token_url = url_config['auth_token_url']
        key_set_url = url_config['key_set_url']

        # Attempt to retrieve the LtiToolKey, if it doesn't exist create it
        try:
            self.stdout.write(f"Attempting to lookup LTI Tool Key: {options['tool_key']}.")
            lti_key = LtiToolKey.objects.get(name=options['tool_key'])
            self.stdout.write('Exiting LTI Tool Key found!')
        except LtiToolKey.DoesNotExist:
            self.stdout.write('LTI Tool Key not found, generating new keys for LTI Tool Key.')
            key = RSA.generate(4096)
            lti_key = LtiToolKey.objects.create(
                name=options['tool_key'],
                private_key=key.exportKey().decode('utf-8'),
                public_key=key.publickey().exportKey().decode('utf-8')
            )

        self.stdout.write('Creating or updating LTI Tool with supplied values.')
        # Update or create a value based on the client_id and issuer keys
        LtiTool.objects.update_or_create(client_id=options["client_id"],
                                         issuer=issuer,
                                         defaults=dict(title=options["title"],
                                                       is_active=True,
                                                       client_id=options["client_id"],
                                                       issuer=issuer,
                                                       use_by_default=False,
                                                       auth_login_url=auth_login_url,
                                                       auth_token_url=auth_token_url,
                                                       key_set_url=key_set_url,
                                                       tool_key=lti_key,
                                                       deployment_ids=json.dumps(options["deployment_ids"])
                                                       ))
