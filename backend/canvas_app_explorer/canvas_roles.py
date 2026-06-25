from enum import Enum
from constance import config


class CanvasRole(Enum):
    ACCOUNT_ADMIN = 'Account Admin'
    TEACHER = 'TeacherEnrollment'


STAFF_COURSE_ROLES = [CanvasRole.ACCOUNT_ADMIN, CanvasRole.TEACHER]


def normalize_role_value(role_value: str) -> str:
    return role_value.strip().lower()


def get_default_staff_course_role_values() -> list[str]:
    return [normalize_role_value(role.value) for role in STAFF_COURSE_ROLES]


def _parse_configured_roles(configured_roles: object) -> list[str]:
    if configured_roles is None:
        return []

    if isinstance(configured_roles, str):
        candidate_roles = configured_roles.split(',')
    elif isinstance(configured_roles, (list, tuple, set)):
        candidate_roles = list(configured_roles)
    else:
        candidate_roles = [str(configured_roles)]

    # Normalize roles and filter out empty strings that result from whitespace-only values.
    non_empty_roles = list(filter(None, (normalize_role_value(str(role)) for role in candidate_roles)))

    # Remove duplicates from configured values.
    return list(set(non_empty_roles))


def get_additional_staff_course_role_values() -> list[str]:
    configured_roles = config.ADDITIONAL_STAFF_COURSE_ROLES
    return _parse_configured_roles(configured_roles)


def get_effective_staff_course_role_values() -> list[str]:
    default_roles = get_default_staff_course_role_values()
    additional_roles = get_additional_staff_course_role_values()

    # Keep default roles first, then append new configured roles without duplicates.
    return list(dict.fromkeys(default_roles + additional_roles))
