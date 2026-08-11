"""Regression tests for per-user display timezones (shared/user_timezone.py).

Every deadline/notification timestamp used to render in a single hardcoded
Tashkent offset -- confusing (and, for editors, risky: a missed deadline
auto-removes their assignment) for anyone outside Uzbekistan. These tests
guard the fallback (unset preference still reads as Tashkent, unchanged) and
the actual personalisation, including a DST-observing zone, which a plain
fixed-offset addition would have gotten wrong.
"""
import datetime as dt

from shared.user_timezone import (
    DEFAULT_ZONE_NAME,
    format_for_user,
    is_valid_timezone_name,
    resolve_zone,
    zone_for_user,
)


def _utc_epoch(year, month, day, hour, minute=0):
    moment = dt.datetime(year, month, day, hour, minute, tzinfo=dt.timezone.utc)
    return int(moment.timestamp())


def test_default_zone_is_tashkent():
    assert DEFAULT_ZONE_NAME == 'Asia/Tashkent'


def test_resolve_zone_falls_back_for_missing_or_invalid_name():
    assert resolve_zone(None).key == DEFAULT_ZONE_NAME
    assert resolve_zone('').key == DEFAULT_ZONE_NAME
    assert resolve_zone('Not/AZone').key == DEFAULT_ZONE_NAME


def test_resolve_zone_accepts_a_valid_iana_name():
    assert resolve_zone('Europe/Berlin').key == 'Europe/Berlin'


def test_is_valid_timezone_name():
    assert is_valid_timezone_name('Europe/Berlin') is True
    assert is_valid_timezone_name('Asia/Tashkent') is True
    assert is_valid_timezone_name('Not/AZone') is False
    assert is_valid_timezone_name('') is False
    assert is_valid_timezone_name(None) is False


def test_zone_for_user_reads_the_stored_preference():
    assert zone_for_user({'timezone_name': 'Europe/Berlin'}).key == 'Europe/Berlin'
    assert zone_for_user({'timezone_name': None}).key == DEFAULT_ZONE_NAME
    assert zone_for_user({}).key == DEFAULT_ZONE_NAME
    assert zone_for_user(None).key == DEFAULT_ZONE_NAME


def test_format_for_user_with_no_preference_matches_the_tashkent_default():
    # Tashkent is a fixed UTC+5 with no DST, so this is exact and stable --
    # a user who never gets auto-detected must see exactly what they saw
    # before this feature existed.
    ts = _utc_epoch(2026, 8, 10, 9, 0)
    assert format_for_user(ts, None, '%d.%m.%Y %H:%M') == '10.08.2026 14:00'
    assert format_for_user(ts, {}, '%d.%m.%Y %H:%M') == '10.08.2026 14:00'


def test_format_for_user_localises_to_a_foreign_editors_own_timezone():
    # Berlin observes DST: UTC+2 in August, UTC+1 in January -- exactly the
    # class of error a fixed offset addition (unlike zoneinfo) gets wrong.
    berlin_user = {'timezone_name': 'Europe/Berlin'}
    summer_ts = _utc_epoch(2026, 8, 10, 9, 0)
    winter_ts = _utc_epoch(2026, 1, 10, 9, 0)
    assert format_for_user(summer_ts, berlin_user, '%d.%m.%Y %H:%M') == '10.08.2026 11:00'
    assert format_for_user(winter_ts, berlin_user, '%d.%m.%Y %H:%M') == '10.01.2026 10:00'


def test_format_for_user_falls_back_for_a_corrupted_stored_value():
    ts = _utc_epoch(2026, 8, 10, 9, 0)
    bad_user = {'timezone_name': 'not-a-real-zone'}
    assert format_for_user(ts, bad_user, '%d.%m.%Y %H:%M') == '10.08.2026 14:00'
