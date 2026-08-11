"""Per-user display timezone resolution, shared by mainweb and fmadmin.

Timestamps are stored as Unix epoch seconds everywhere and compared in UTC
without exception -- this module only changes how a moment is *displayed* to
a specific person, never what "now" or a deadline comparison means.
"""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

DEFAULT_ZONE_NAME = 'Asia/Tashkent'

# Zone names outside this shape are legacy aliases zoneinfo mixes in
# alongside the real ones (right/* leap-second variants, posix/* aliases,
# Etc/GMT+N with its famously inverted sign) -- not real choices for a
# person picking their own city.
_EXCLUDED_ZONE_PREFIXES = ('posix/', 'right/', 'Etc/')

_AVAILABLE_ZONE_NAMES = available_timezones()
_DEFAULT_ZONE = ZoneInfo(DEFAULT_ZONE_NAME)

# Sorted once at import time for <select> options -- the IANA database
# doesn't change during the process lifetime.
TIMEZONE_CHOICES = sorted(
    name for name in _AVAILABLE_ZONE_NAMES
    if '/' in name and not name.startswith(_EXCLUDED_ZONE_PREFIXES)
)


def is_valid_timezone_name(timezone_name):
    return bool(timezone_name) and timezone_name in _AVAILABLE_ZONE_NAMES


def resolve_zone(timezone_name):
    """IANA name -> ZoneInfo.

    Falls back to the Tashkent default for a missing, unrecognised, or
    otherwise invalid name -- a bad stored value must never turn into a 500
    on a notification or page render.
    """
    if not timezone_name:
        return _DEFAULT_ZONE
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        return _DEFAULT_ZONE


def zone_for_user(user_row):
    return resolve_zone((user_row or {}).get('timezone_name'))


def format_for_user(epoch_ts, user_row, fmt):
    """Localise epoch_ts into user_row's own timezone and format it.

    Callers keep owning their own empty-value fallback (e.g. `'-'` vs `''`)
    exactly as before -- this only replaces the offset math.
    """
    zone = zone_for_user(user_row)
    return datetime.fromtimestamp(int(epoch_ts), tz=zone).strftime(fmt)
