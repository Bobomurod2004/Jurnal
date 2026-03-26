import os

from flask import url_for

import settings


PRIVATE_UPLOAD_PREFIX = 'private://'
PRIVATE_UPLOAD_ROOT = 'private_uploads'
PRIVATE_UPLOAD_CATEGORIES = {'articles', 'documents', 'payments'}


def _clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def extract_private_upload_key(value):
    text = _clean_text(value)
    if not text:
        return None

    if text.startswith(PRIVATE_UPLOAD_PREFIX):
        key = text[len(PRIVATE_UPLOAD_PREFIX):].lstrip('/')
    elif text.startswith('/static/uploads/'):
        key = text[len('/static/uploads/'):].lstrip('/')
    else:
        key = text.lstrip('/')

    category, _, remainder = key.partition('/')
    if category not in PRIVATE_UPLOAD_CATEGORIES or not remainder:
        return None
    return f'{category}/{remainder}'


def is_private_upload_ref(value):
    return extract_private_upload_key(value) is not None


def private_upload_abspath(value):
    key = extract_private_upload_key(value)
    if not key:
        return None

    base_dir = os.path.abspath(os.path.join(settings.SAVE_PATH, PRIVATE_UPLOAD_ROOT))
    candidate_path = os.path.abspath(os.path.join(base_dir, key))
    try:
        if os.path.commonpath([candidate_path, base_dir]) != base_dir:
            return None
    except ValueError:
        return None
    return candidate_path


def upload_access_url(value):
    key = extract_private_upload_key(value)
    if not key:
        return value
    return url_for('fmadmin_web.serve_private_file', storage_key=key)
