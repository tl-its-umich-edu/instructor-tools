from enum import Enum

from constance import config


class CanvasRole(Enum):
    ACCOUNT_ADMIN = 'Account Admin'
    SUB_ACCOUNT_ADMIN = 'Sub-Account Admin'
    TEACHER = 'TeacherEnrollment'


STAFF_COURSE_ROLES = [CanvasRole.ACCOUNT_ADMIN, CanvasRole.SUB_ACCOUNT_ADMIN, CanvasRole.TEACHER]


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

    parsed_roles = [normalize_role_value(str(role)) for role in candidate_roles]
    parsed_roles = [role for role in parsed_roles if role]

    # Preserve order while removing duplicates in configured values.
    return list(dict.fromkeys(parsed_roles))


def get_additional_staff_course_role_values() -> list[str]:
    configured_roles = getattr(config, 'ADDITIONAL_STAFF_COURSE_ROLES', '')
    return _parse_configured_roles(configured_roles)


def get_effective_staff_course_role_values() -> list[str]:
    default_roles = get_default_staff_course_role_values()
    additional_roles = get_additional_staff_course_role_values()

    effective_roles = list(default_roles)
    for role in additional_roles:
        if role not in effective_roles:
            effective_roles.append(role)

    return effective_roles
