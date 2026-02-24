import os
import time
from flask import url_for
import settings


def cover_or_default(public_path, default='obl.jpg'):
    if not public_path:
        return url_for('static', filename=default)
    if public_path.startswith('/static/uploads/'):
        fs_path = os.path.join(settings.SAVE_PATH, public_path.lstrip('/'))
        if os.path.exists(fs_path):
            return public_path
        return url_for('static', filename=default)
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


def register_filters(app):
    app.template_filter('cover_or_default')(cover_or_default)
    app.template_filter('timestamp_to_date')(timestamp_to_date)
    app.template_filter('status_color')(status_color)
    app.template_filter('status_text')(status_text)
    app.template_filter('format_currency')(format_currency)
