import calendar
import os
import time
import datetime


def _configured_offset_seconds():
    """Admin-facing timezone offset, in seconds east of UTC.

    Defaults to Tashkent (UTC+5).  Timestamps are stored as UTC epochs,
    while every date the admin reads or types is wall-clock time here.
    """
    raw = str(os.getenv('UI_TZ_OFFSET_HOURS', '') or '').strip()
    if not raw:
        return 5 * 60 * 60
    try:
        return int(float(raw) * 3600)
    except (TypeError, ValueError):
        return 5 * 60 * 60


UI_TZ_OFFSET_SECONDS = _configured_offset_seconds()

# Accepted layouts for a value coming back from an <input type="datetime-local">
# or <input type="date">.
UI_DATETIME_INPUT_FORMATS = ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d')


def _ui_datetime_from_timestamp(value):
    ts = int(value)
    return datetime.datetime.fromtimestamp(ts + UI_TZ_OFFSET_SECONDS, datetime.UTC)


def ui_datetime_input_value(timestamp):
    """UTC epoch -> 'YYYY-MM-DDTHH:MM' on the admin's wall clock."""
    return _ui_datetime_from_timestamp(timestamp).strftime('%Y-%m-%dT%H:%M')


def parse_ui_datetime(value, end_of_day=False):
    """'YYYY-MM-DDTHH:MM' typed by the admin -> UTC epoch.

    The naive value is read as wall-clock time in the admin's zone, not in the
    server's.  Servers run on UTC, so parsing with `datetime.timestamp()` used
    to shift every deadline by the offset -- the admin picked 14:00 and the
    system stored 19:00 Tashkent time.
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
        # `timegm` reads the naive value as UTC; subtracting the offset turns
        # that wall-clock reading into the matching UTC epoch.
        return calendar.timegm(dt.timetuple()) - UI_TZ_OFFSET_SECONDS
    return None


def parse_ui_date(value, end_of_day=False):
    """'YYYY-MM-DD' typed by the admin -> UTC epoch."""
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
    local_timestamp = timestamp + UI_TZ_OFFSET_SECONDS
    return time.strftime('%d.%m.%Y', time.gmtime(local_timestamp))


def timestamp_to_datetime(timestamp):
    if not timestamp:
        return ''
    local_timestamp = timestamp + UI_TZ_OFFSET_SECONDS
    return time.strftime('%d.%m.%Y %H:%M', time.gmtime(local_timestamp))


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
