import datetime

from flask import has_request_context, session

from shared.user_timezone import resolve_zone

# Accepted layouts for a value coming back from an
# <input type="datetime-local"> or <input type="date">.
UI_DATETIME_INPUT_FORMATS = ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d')


def _session_user_row():
    # Outside a request (e.g. a plain unit test calling these filters
    # directly) there is no viewer to personalise for -- fall back to the
    # shared default (Tashkent) exactly like before this existed.
    if not has_request_context():
        return {}
    return session.get('fmadmin_user') or {}


def _viewer_zone():
    return resolve_zone(_session_user_row().get('timezone_name'))


def _ui_datetime_from_timestamp(value):
    ts = int(value)
    return datetime.datetime.fromtimestamp(ts, tz=_viewer_zone())


def ui_datetime_input_value(timestamp):
    """UTC epoch -> 'YYYY-MM-DDTHH:MM' on the viewer's own wall clock."""
    return _ui_datetime_from_timestamp(timestamp).strftime('%Y-%m-%dT%H:%M')


def parse_ui_datetime(value, end_of_day=False):
    """'YYYY-MM-DDTHH:MM' typed by the viewer -> UTC epoch.

    The naive value is read as wall-clock time in the viewer's own timezone
    (their stored preference, defaulting to Tashkent) -- not the server's.
    Servers run on UTC, so parsing this on the server's clock used to shift
    every deadline by the offset -- the admin picked 14:00 and the system
    stored 19:00 Tashkent time.
    """
    cleaned = '' if value is None else str(value).strip()
    if not cleaned:
        return None

    for fmt in UI_DATETIME_INPUT_FORMATS:
        try:
            dt = datetime.datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
        if fmt == '%Y-%m-%d' and end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59)
        # The naive value is wall-clock time in the viewer's zone; attaching
        # that tzinfo directly gives the matching UTC epoch, DST included.
        return int(dt.replace(tzinfo=_viewer_zone()).timestamp())
    return None


def parse_ui_date(value, end_of_day=False):
    """'YYYY-MM-DD' typed by the viewer -> UTC epoch."""
    cleaned = '' if value is None else str(value).strip()
    if not cleaned:
        return None
    try:
        datetime.datetime.strptime(cleaned, '%Y-%m-%d')
    except ValueError:
        return None
    return parse_ui_datetime(cleaned, end_of_day=end_of_day)


def number_format(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value


def timestamp_to_date(timestamp):
    if not timestamp:
        return ''
    zone = _viewer_zone()
    localized = datetime.datetime.fromtimestamp(int(timestamp), tz=zone)
    return localized.strftime('%d.%m.%Y')


def timestamp_to_datetime(timestamp):
    if not timestamp:
        return ''
    zone = _viewer_zone()
    localized = datetime.datetime.fromtimestamp(int(timestamp), tz=zone)
    return localized.strftime('%d.%m.%Y %H:%M')


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
        return _ui_datetime_from_timestamp(value).strftime('%Y-%m-%d')
    except Exception:
        return ''


def date_to_form_full(value):
    if not value:
        return ''
    try:
        return _ui_datetime_from_timestamp(value).strftime('%Y-%m-%dT%H:%M')
    except Exception:
        return ''


def register_filters(app):
    app.template_filter('number_format')(number_format)
    app.template_filter('timestamp_to_date')(timestamp_to_date)
    app.template_filter('timestamp_to_datetime')(timestamp_to_datetime)
    app.template_filter('datetimeformat')(datetimeformat)
    app.template_filter('date_to_form')(date_to_form)
    app.template_filter('date_to_form_full')(date_to_form_full)
