from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest
from constance import config

from .serializers import GlobalsUserSerializer


def cae_globals(request: HttpRequest) -> Dict[str, Any]:
    user_data = GlobalsUserSerializer(request.user).data if request.user.is_authenticated else None
    course_id = request.session.get('course_id', None)
    course_name = request.session.get('course_name', None)
    term_id = request.session.get('term_id', None)
    term_name = request.session.get('term_name', None)
    account_id = request.session.get('account_id', None)
    account_name = request.session.get('account_name', None)
    
    return {
        'cae_globals': {
            'user': user_data,
            'course_id': course_id,
            'course_name': course_name,
            'term_id': term_id,
            'term_name': term_name,
            'account_id': account_id,
            'account_name': account_name,
            'help_url': config.HELP_URL,
            'google_analytics_id': settings.GOOGLE_ANALYTICS_ID,
            'um_consent_manager_script_domain': settings.UM_CONSENT_MANAGER_SCRIPT_DOMAIN,
        }
    }
