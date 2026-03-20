from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest
from django.core import signing
from constance import config

from .serializers import GlobalsUserSerializer


CAE_COURSE_USER_CONTEXT_SIGNING_SALT = 'cae_course_user_context_payload'


def cae_globals(request: HttpRequest) -> Dict[str, Any]:
    user_data = GlobalsUserSerializer(request.user).data if request.user.is_authenticated else None
    course_id = request.session.get('course_id', None)
    course_name = request.session.get('course_name', None)
    term_id = request.session.get('term_id', None)
    term_name = request.session.get('term_name', None)
    account_id = request.session.get('account_id', None)
    account_name = request.session.get('account_name', None)
    signed_course_user_payload = get_signed_course_user_payload(course_id, user_data)

    return {
        'cae_globals': {
            'user': user_data,
            'course_id': course_id,
            'signed_course_user_payload': signed_course_user_payload,
            'course_name': course_name,
            'term_id': term_id,
            'term_name': term_name,
            'account_id': account_id,
            'account_name': account_name,
            'help_url': config.HELP_URL,
            'ai_services_url': config.AI_SERVICES_URL,
            'google_analytics_id': settings.GOOGLE_ANALYTICS_ID,
            'um_consent_manager_script_domain': settings.UM_CONSENT_MANAGER_SCRIPT_DOMAIN,
        }
    }


def get_signed_course_user_payload(course_id: int | None, user: Dict[str, Any] | None) -> str | None:
    """
    Returns a signed payload containing course and user context.

    If required values are unavailable, returns None.
    """
    if course_id is None or user is None:
        return None

    username = user.get('username') if isinstance(user, dict) else None
    if not username:
        return None

    payload = {
        'course_id': course_id,
        'user': username,
    }
    return signing.dumps(
        payload,
        salt=CAE_COURSE_USER_CONTEXT_SIGNING_SALT,
        key=settings.CAE_COURSE_USER_CONTEXT_SIGNING_KEY,
        compress=True,
    )