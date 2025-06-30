from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest

from .serializers import GlobalsUserSerializer


def cae_globals(request: HttpRequest) -> Dict[str, Any]:
    user_data = GlobalsUserSerializer(request.user).data if request.user.is_authenticated else None
    course_id = request.session.get('course_id', None)
    
    return {
        'cae_globals': {
            'user': user_data,
            'course_id': course_id,
            'help_url': settings.HELP_URL,
            'google_analytics_id': settings.GOOGLE_ANALYTICS_ID,
            'um_consent_manager_script_domain': settings.UM_CONSENT_MANAGER_SCRIPT_DOMAIN,
        }
    }
