import json


ROLE_PRIORITY = ('superadmin', 'admin', 'editor', 'user')
PRIVILEGED_ROLES = {'superadmin', 'admin', 'editor'}
AUTHOR_ROLE = 'user'
ROLE_PERMISSIONS = {
    'user': {
        'website.dashboard.access',
        'website.submissions.create',
    },
    'editor': {
        'fmadmin.access',
        'fmadmin.dashboard.editor',
        'fmadmin.assignments.view',
        'fmadmin.assignments.review',
        'fmadmin.notifications.view',
    },
    'admin': {
        'fmadmin.access',
        'fmadmin.dashboard.admin',
        'fmadmin.submissions.manage',
        'fmadmin.assignments.view',
        'fmadmin.assignments.manage',
        'fmadmin.notifications.view',
        # Day-to-day journal operations: issues, articles, news, announcements.
        'fmadmin.content.manage',
        # Adding and maintaining the editors an admin assigns work to.
        'fmadmin.editors.manage',
        # Confirming/rejecting incoming payments. Pricing (tariffs, payment
        # guide) stays with superadmin via `fmadmin.finance.manage`.
        'fmadmin.payments.manage',
    },
    'superadmin': {
        'fmadmin.access',
        'fmadmin.dashboard.admin',
        'fmadmin.submissions.manage',
        'fmadmin.assignments.view',
        'fmadmin.assignments.manage',
        'fmadmin.notifications.view',
        'fmadmin.users.manage',
        'fmadmin.content.manage',
        'fmadmin.content.delete',
        'fmadmin.editors.manage',
        'fmadmin.site.manage',
        'fmadmin.finance.manage',
        'fmadmin.payments.manage',
        'fmadmin.system.manage',
    },
}
CAPABILITY_PERMISSION_MAP = {
    'can_access_author_dashboard': 'website.dashboard.access',
    'can_submit_articles': 'website.submissions.create',
    'can_access_fmadmin': 'fmadmin.access',
    'can_access_editor_dashboard': 'fmadmin.dashboard.editor',
    'can_access_admin_dashboard': 'fmadmin.dashboard.admin',
    'can_manage_submissions': 'fmadmin.submissions.manage',
    'can_view_assignments': 'fmadmin.assignments.view',
    'can_manage_assignments': 'fmadmin.assignments.manage',
    'can_review_assignments': 'fmadmin.assignments.review',
    'can_view_notifications': 'fmadmin.notifications.view',
    'can_manage_users': 'fmadmin.users.manage',
    'can_manage_content': 'fmadmin.content.manage',
    'can_delete_content': 'fmadmin.content.delete',
    'can_manage_editors': 'fmadmin.editors.manage',
    'can_manage_site': 'fmadmin.site.manage',
    'can_manage_finance': 'fmadmin.finance.manage',
    'can_manage_payments': 'fmadmin.payments.manage',
    'can_manage_system': 'fmadmin.system.manage',
}


def _clean_role_name(value):
    if value is None:
        return ''
    return str(value).strip().lower()


def _split_role_string(value):
    text = _clean_role_name(value)
    if not text:
        return []

    if text.startswith('[') and text.endswith(']'):
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = None
        if isinstance(parsed, list):
            return parsed

    if text.startswith('{') and text.endswith('}'):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [
            item.strip().strip('"').strip("'")
            for item in inner.split(',')
            if item.strip().strip('"').strip("'")
        ]

    return [item.strip() for item in text.split(',') if item.strip()]


def parse_role_names(value):
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        raw_roles = list(value)
    else:
        raw_roles = _split_role_string(value)

    roles = []
    for raw_role in raw_roles:
        role_name = _clean_role_name(raw_role)
        if role_name and role_name not in roles:
            roles.append(role_name)
    return roles


def build_user_roles(primary_role, include_author_role=False, extra_roles=None):
    normalized_primary_role = _clean_role_name(primary_role) or AUTHOR_ROLE
    roles = []

    if normalized_primary_role:
        roles.append(normalized_primary_role)

    for role_name in parse_role_names(extra_roles):
        if role_name not in roles:
            roles.append(role_name)

    if include_author_role or normalized_primary_role == AUTHOR_ROLE:
        if AUTHOR_ROLE not in roles:
            roles.append(AUTHOR_ROLE)

    if not roles:
        roles.append(AUTHOR_ROLE)

    return roles


def roles_for_user(user_row, default_role=AUTHOR_ROLE):
    user_data = user_row or {}
    primary = _clean_role_name(user_data.get('rolename'))
    roles = parse_role_names(user_data.get('roles'))

    if primary and primary not in roles:
        roles.append(primary)

    if not roles:
        roles = [default_role]

    return roles


def primary_role(user_row, default_role=AUTHOR_ROLE):
    user_data = user_row or {}
    explicit_primary_role = _clean_role_name(user_data.get('rolename'))
    roles = roles_for_user(user_data, default_role=default_role)

    if explicit_primary_role and explicit_primary_role in roles:
        return explicit_primary_role

    for role_name in ROLE_PRIORITY:
        if role_name in roles:
            return role_name

    return roles[0] if roles else default_role


def staff_roles_for_user(user_row):
    return [role_name for role_name in roles_for_user(user_row) if role_name in PRIVILEGED_ROLES]


def user_has_role(user_row, role_name):
    normalized_role_name = _clean_role_name(role_name)
    if not normalized_role_name:
        return False
    return normalized_role_name in roles_for_user(user_row)


def user_has_any_role(user_row, role_names):
    for role_name in role_names or []:
        if user_has_role(user_row, role_name):
            return True
    return False


def permissions_for_roles(role_names):
    permissions = []
    seen = set()
    for role_name in parse_role_names(role_names):
        for permission_name in ROLE_PERMISSIONS.get(role_name, set()):
            if permission_name not in seen:
                seen.add(permission_name)
                permissions.append(permission_name)
    return permissions


def permissions_for_user(user_row):
    return permissions_for_roles(roles_for_user(user_row))


def user_has_permission(user_row, permission_name):
    normalized_permission_name = str(permission_name or '').strip().lower()
    if not normalized_permission_name:
        return False
    return normalized_permission_name in permissions_for_user(user_row)


def user_has_any_permission(user_row, permission_names):
    for permission_name in permission_names or []:
        if user_has_permission(user_row, permission_name):
            return True
    return False


def capabilities_for_user(user_row):
    return {
        capability_name: user_has_permission(user_row, permission_name)
        for capability_name, permission_name in CAPABILITY_PERMISSION_MAP.items()
    }


def hydrate_user_roles(user_row, default_role=AUTHOR_ROLE):
    hydrated_user = dict(user_row or {})
    hydrated_user['roles'] = roles_for_user(hydrated_user, default_role=default_role)
    hydrated_user['rolename'] = primary_role(hydrated_user, default_role=default_role)
    hydrated_user['permissions'] = permissions_for_roles(hydrated_user.get('roles'))
    hydrated_user['capabilities'] = capabilities_for_user(hydrated_user)
    return hydrated_user
