import time
import datetime


def number_format(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value


def timestamp_to_date(timestamp):
    if not timestamp:
        return ''
    utc_plus_5_offset = 5 * 60 * 60
    local_timestamp = timestamp + utc_plus_5_offset
    return time.strftime('%d.%m.%Y', time.gmtime(local_timestamp))


def datetimeformat(value):
    if not value:
        return ''
    try:
        if len(str(int(value))) <= 10:
            dt = datetime.datetime.fromtimestamp(int(value))
        else:
            dt = datetime.datetime.fromtimestamp(int(value) / 1000)
        return dt.strftime('%d.%m.%Y')
    except Exception:
        return str(value)


def date_to_form(value):
    if not value:
        return ''
    try:
        return datetime.datetime.fromtimestamp(int(value), datetime.UTC).strftime('%Y-%m-%d')
    except Exception:
        return ''


def date_to_form_full(value):
    if not value:
        return ''
    try:
        return datetime.datetime.fromtimestamp(int(value), datetime.UTC).strftime('%Y-%m-%dT%H:%M')
    except Exception:
        return ''


def register_filters(app):
    app.template_filter('number_format')(number_format)
    app.template_filter('timestamp_to_date')(timestamp_to_date)
    app.template_filter('datetimeformat')(datetimeformat)
    app.template_filter('date_to_form')(date_to_form)
    app.template_filter('date_to_form_full')(date_to_form_full)
