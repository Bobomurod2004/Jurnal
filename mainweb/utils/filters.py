import os
import time
from html import unescape
from flask import url_for
import settings

DEFAULT_ISSUE_COVER = 'uploads/issues/2025/07/db14cd28777c448b9a7079c568448f9b.jpg'
LOCAL_STATIC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))


def _static_url(path):
    if not path:
        return url_for('static', filename=DEFAULT_ISSUE_COVER)
    if path.startswith('/static/'):
        return path
    return url_for('static', filename=path.lstrip('/'))


def _public_static_path_exists(public_path):
    if not public_path or not public_path.startswith('/static/'):
        return False

    normalized_path = public_path.lstrip('/')
    candidate_paths = [os.path.join(settings.SAVE_PATH, normalized_path)]

    if normalized_path.startswith('static/'):
        candidate_paths.append(os.path.join(LOCAL_STATIC_ROOT, normalized_path[len('static/'):]))

    return any(os.path.exists(path) for path in candidate_paths)


def cover_or_default(public_path, default=DEFAULT_ISSUE_COVER):
    default_url = _static_url(default)
    if not public_path:
        return default_url
    if public_path.startswith('/static/') and not _public_static_path_exists(public_path):
        return default_url
    return public_path


def timestamp_to_date(timestamp):
    if not timestamp:
        return ''
    utc_plus_5_offset = 5 * 60 * 60
    local_timestamp = timestamp + utc_plus_5_offset
    return time.strftime('%d.%m.%Y', time.gmtime(local_timestamp))


def status_color(status):
    colors = {
        'declined': 'red',
        'unpaid': 'blue',
        'paid': 'green',
        'pending': 'blue'
    }
    return colors.get(status, 'gray')


def status_text(status):
    texts = {
        'declined': 'Declined',
        'unpaid': 'Waiting payment',
        'paid': 'Activated',
        'pending': 'Under review'
    }
    return texts.get(status, status.title())


def format_currency(value, currency='usd'):
    try:
        value = float(value)
        if currency == 'uzs':
            return f"{value:,.0f} UZS"
        if currency == 'rub':
            return f"{value:,.0f} ₽"
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def _multi_unescape(value):
    decoded = str(value)
    for _ in range(3):
        next_decoded = unescape(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    return decoded


def decode_html(value):
    if value is None:
        return ''
    return _multi_unescape(value)


def register_filters(app):
    app.template_filter('cover_or_default')(cover_or_default)
    app.template_filter('timestamp_to_date')(timestamp_to_date)
    app.template_filter('status_color')(status_color)
    app.template_filter('status_text')(status_text)
    app.template_filter('format_currency')(format_currency)
    app.template_filter('decode_html')(decode_html)
