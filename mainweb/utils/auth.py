import re
from html import unescape
from functools import wraps
from urllib.parse import urlparse
from flask import session, flash, redirect, url_for, request, jsonify
from modules.translate import t
from extensions import dbc
from utils.roles import AUTHOR_ROLE, hydrate_user_roles, user_has_permission

# Paths that must never become a post-login redirect target. Sending the user
# back to /login is what let crawlers walk
# /login?next=/login?next%3D/login?next%253D... forever, each hop re-encoding
# the last, so the auth pages are refused outright.
NEXT_URL_BLOCKED_PATHS = {'/login', '/logout', '/register'}


def sanitize_next_url(next_url):
    """Accept only a safe in-site return path, otherwise None.

    Guards two things at once: an open redirect (anything with a scheme or
    host, or a protocol-relative //evil.com) and the crawl trap above.
    """
    if not next_url:
        return None
    next_url = str(next_url).strip()
    if not next_url:
        return None
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        return None
    if not next_url.startswith('/'):
        return None
    if next_url.startswith('//'):
        return None
    if next_url.split('?', 1)[0] in NEXT_URL_BLOCKED_PATHS:
        return None
    return next_url


PROFILE_REQUIRED_USER_FIELDS = ('name', 'second_name', 'father_name', 'country_id')
PROFILE_REQUIRED_AUTHOR_FIELDS = ()
PROFILE_GUARD_ALLOWED_ENDPOINTS = {
    'app__dashboard_profile',
    'app__dashboard_private_file',
    'app__api_getauthor',
    'app__api_getcurrentauthor',
    'app__api_profile_change_password',
    'app__api_createauthor',
}


def _has_required_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def get_user_profile_completion(user_row=None, user_id=None, author_row=None):
    user_data = user_row or {}
    resolved_user_id = user_id if user_id is not None else user_data.get('id')
    doc_data = {}

    if author_row is None and resolved_user_id:
        try:
            author_rows = dbc.author_profile.get(user_id=resolved_user_id).exec()
        except Exception:
            author_rows = []
        author_data = author_rows[0] if author_rows else {}
    else:
        author_data = author_row or {}

    if resolved_user_id:
        try:
            doc_rows = dbc.user_doc_uploads.get(user_id=resolved_user_id).exec()
        except Exception:
            doc_rows = []
        doc_data = doc_rows[0] if doc_rows else {}

    missing_user_fields = [field for field in PROFILE_REQUIRED_USER_FIELDS if not _has_required_value(user_data.get(field))]
    missing_author_fields = [field for field in PROFILE_REQUIRED_AUTHOR_FIELDS if not _has_required_value(author_data.get(field))]
    missing_extra_fields = []
    if not _has_required_value(doc_data.get('work_title')):
        missing_extra_fields.append('academic_position')

    return {
        'is_complete': len(missing_user_fields) == 0 and len(missing_author_fields) == 0 and len(missing_extra_fields) == 0,
        'missing_user_fields': missing_user_fields,
        'missing_author_fields': missing_author_fields,
        'missing_extra_fields': missing_extra_fields,
    }


def is_user_profile_complete(user_row=None, user_id=None, author_row=None):
    completion = get_user_profile_completion(user_row=user_row, user_id=user_id, author_row=author_row)
    return completion['is_complete']


def _is_profile_guard_exempt():
    endpoint = (request.endpoint or '').strip()
    if endpoint in PROFILE_GUARD_ALLOWED_ENDPOINTS:
        return True
    path = request.path or ''
    if path.startswith('/dashboard/profile'):
        return True
    return False


def _expects_json_response():
    accept = request.headers.get('Accept', '')
    requested_with = request.headers.get('X-Requested-With', '')
    return (
        request.path.startswith('/api/')
        or request.is_json
        or 'application/json' in accept
        or requested_with == 'XMLHttpRequest'
    )


def _normalize_session_user(user_row):
    normalized_row = hydrate_user_roles(user_row)
    normalized_row.pop('password', None)
    normalized = {}
    for key, value in normalized_row.items():
        if isinstance(value, str):
            normalized[key] = decode_html_entities(value)
        else:
            normalized[key] = value
    return normalized


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('app__login'))
        user_id = session.get('user_id')
        try:
            user_data = dbc.users.get(id=user_id).exec()
        except Exception:
            user_data = []
        if not user_data or user_data[0].get('is_blocked') or user_data[0].get('is_hidden'):
            session.pop('user_id', None)
            session.pop('user', None)
            flash('Your account is blocked. Please contact support.', 'error')
            return redirect(url_for('app__login'))

        user_row = hydrate_user_roles(user_data[0])
        session['user'] = _normalize_session_user(user_row)
        should_enforce_profile = user_has_permission(user_row, 'website.dashboard.access')
        if should_enforce_profile and not is_user_profile_complete(user_row=user_row, user_id=user_id) and not _is_profile_guard_exempt():
            message = t('complete_profile_required')
            if not message or message == 'complete_profile_required':
                message = 'Please complete your profile information before continuing.'
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'message': message,
                    'code': 'profile_incomplete',
                    'redirect': url_for('app__dashboard_profile')
                }), 403
            flash(message, 'warning')
            return redirect(url_for('app__dashboard_profile'))
        return f(*args, **kwargs)
    return decorated_function


def author_login_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        try:
            user_rows = dbc.users.get(id=user_id).exec()
        except Exception:
            user_rows = []

        user_row = hydrate_user_roles(user_rows[0] if user_rows else session.get('user') or {})
        session['user'] = _normalize_session_user(user_row)

        if user_has_permission(user_row, 'website.dashboard.access') or user_has_permission(user_row, 'fmadmin.access'):
            return f(*args, **kwargs)

        message = t('author_role_required')
        if not message or message == 'author_role_required':
            message = "Bu akkaunt uchun maqola yuborish roli yoqilmagan."

        if _expects_json_response():
            return jsonify({
                'success': False,
                'message': message,
                'code': 'author_role_required',
                'redirect': url_for('app__index')
            }), 403

        flash(message, 'warning')
        return redirect(url_for('app__index'))

    return decorated_function


def not_auth_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            user_id = session.get('user_id')
            try:
                user_rows = dbc.users.get(id=user_id).exec()
            except Exception:
                user_rows = []
            session_user = hydrate_user_roles(user_rows[0] if user_rows else session.get('user') or {})
            if user_rows and user_has_permission(session_user, 'website.dashboard.access'):
                return redirect(url_for('app__dashboard'))
            return redirect(url_for('app__index'))
        return f(*args, **kwargs)
    return decorated_function


def is_valid_email(email):
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_strong_password(password):
    if not password:
        return False, t('password_required')
    if len(password) < 8:
        return False, t('password_min_length')
    if not re.search(r'[A-Z]', password):
        return False, t('password_uppercase_required')
    if not re.search(r'[a-z]', password):
        return False, t('password_lowercase_required')
    if not re.search(r'[0-9]', password):
        return False, t('password_number_required')
    return True, 'Valid'


def _multi_unescape(value):
    decoded = str(value)
    for _ in range(3):
        next_decoded = unescape(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    return decoded


def sanitize_input(text):
    if text is None:
        return ''
    # Store plain text in DB; rely on template auto-escaping on output.
    normalized = _multi_unescape(text).strip()
    normalized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', normalized)
    return normalized


def decode_html_entities(text):
    if text is None:
        return None
    return _multi_unescape(text)
