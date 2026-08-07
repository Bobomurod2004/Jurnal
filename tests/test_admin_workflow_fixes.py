"""Regression tests for the admin timezone and track-coverage fixes.

Two separate defects, both invisible until someone noticed the result was
wrong:

* deadlines were read back on the server's clock (UTC) while every date shown
  to the admin is Tashkent wall-clock time, so a picked deadline drifted by the
  offset;
* submissions whose track no admin covers are quietly left unassigned, with
  nothing anywhere saying so.
"""
import datetime

from fmadmin.routes import web as fmadmin_web
from fmadmin.utils.filters import (
    UI_TZ_OFFSET_SECONDS,
    parse_ui_date,
    parse_ui_datetime,
    timestamp_to_datetime,
    ui_datetime_input_value,
)


# --------------------------------------------------------------------------
# Admin timezone
# --------------------------------------------------------------------------

def test_ui_offset_defaults_to_tashkent():
    assert UI_TZ_OFFSET_SECONDS == 5 * 60 * 60


def test_picked_deadline_reads_back_as_the_same_wall_clock_time():
    # The heart of the bug: the admin picked 14:00 and the saved deadline came
    # back as 19:00, because the naive value was parsed on the server's UTC
    # clock while the display filter adds the +5 offset.
    stored = parse_ui_datetime('2026-08-10T14:00')

    assert timestamp_to_datetime(stored) == '10.08.2026 14:00'
    assert ui_datetime_input_value(stored) == '2026-08-10T14:00'


def test_parsed_deadline_is_stored_as_a_utc_epoch():
    stored = parse_ui_datetime('2026-08-10T14:00')
    as_utc = datetime.datetime.fromtimestamp(stored, datetime.UTC)

    # 14:00 in Tashkent is 09:00 UTC; the database keeps UTC epochs.
    assert as_utc.strftime('%Y-%m-%d %H:%M') == '2026-08-10 09:00'


def test_parsing_is_the_exact_inverse_of_rendering():
    for timestamp in (0, 1_600_000_000, 1_786_352_400, 2_000_000_000):
        rendered = ui_datetime_input_value(timestamp)
        # Round-trips to the same minute (the input has no seconds field).
        assert parse_ui_datetime(rendered) == timestamp - (timestamp % 60)


def test_date_only_filters_use_the_admin_day_boundaries():
    start = parse_ui_date('2026-08-10')
    end = parse_ui_date('2026-08-10', end_of_day=True)

    assert ui_datetime_input_value(start) == '2026-08-10T00:00'
    assert ui_datetime_input_value(end) == '2026-08-10T23:59'
    assert end - start == 24 * 60 * 60 - 1


def test_blank_and_malformed_values_stay_none():
    for value in ('', '   ', None, 'not-a-date', '10.08.2026'):
        assert parse_ui_datetime(value) is None
        assert parse_ui_date(value) is None


def test_route_helpers_delegate_to_the_admin_timezone():
    # The route-level wrappers must not fall back to the server clock.
    assert fmadmin_web._parse_datetime_to_timestamp('2026-08-10T14:00') == (
        parse_ui_datetime('2026-08-10T14:00')
    )
    assert fmadmin_web._parse_date_to_timestamp('2026-08-10', end_of_day=True) == (
        parse_ui_date('2026-08-10', end_of_day=True)
    )


def test_a_bare_date_deadline_means_the_end_of_that_day():
    # The deadline pickers accept a date without a time; treating it as
    # midnight would expire the assignment a day early.
    stored = fmadmin_web._parse_datetime_to_timestamp('2026-08-10')
    assert ui_datetime_input_value(stored) == '2026-08-10T23:59'


# --------------------------------------------------------------------------
# Admin track coverage
# --------------------------------------------------------------------------

def _admin(admin_id, tracks):
    return {'id': admin_id, 'rolename': 'admin', 'roles': ['admin'], 'admin_tracks': tracks}


class _StubQuery:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self

    def unequal(self, **kwargs):
        return self

    def exec(self):
        return self._rows


class _StubDb:
    """Stands in for the connector: it rejects unknown table names."""

    def __init__(self, submissions):
        self.submissions = _StubQuery(submissions)


def _patch_track_sources(monkeypatch, admins, submissions):
    monkeypatch.setattr(fmadmin_web, '_active_admins', lambda: admins)
    monkeypatch.setattr(fmadmin_web, 'db', _StubDb(submissions))


def test_track_with_no_admin_is_reported_with_a_count(monkeypatch):
    _patch_track_sources(
        monkeypatch,
        admins=[_admin(12, ['masters'])],
        submissions=[
            {'submission_track': 'masters'},
            {'submission_track': 'phd'},
            {'submission_track': 'phd'},
            {'submission_track': 'teacher'},
        ],
    )

    uncovered = fmadmin_web._uncovered_admin_tracks()

    assert [item['track'] for item in uncovered] == ['phd', 'teacher']
    assert {item['track']: item['count'] for item in uncovered} == {'phd': 2, 'teacher': 1}
    # The label is what the warning shows, so it must be filled in.
    assert all(item['label'] for item in uncovered)


def test_nothing_is_reported_once_every_track_is_covered(monkeypatch):
    _patch_track_sources(
        monkeypatch,
        admins=[_admin(12, ['masters']), _admin(13, ['phd', 'teacher'])],
        submissions=[
            {'submission_track': 'masters'},
            {'submission_track': 'phd'},
            {'submission_track': 'teacher'},
        ],
    )

    assert fmadmin_web._uncovered_admin_tracks() == []


def test_submissions_without_a_track_are_not_reported_as_uncovered(monkeypatch):
    # A missing track is a different problem -- it is not routed by track at
    # all, so listing it under "no admin for this track" would be noise.
    _patch_track_sources(
        monkeypatch,
        admins=[_admin(12, ['masters'])],
        submissions=[{'submission_track': None}, {'submission_track': ''}],
    )

    assert fmadmin_web._uncovered_admin_tracks() == []


def test_track_aliases_count_towards_coverage(monkeypatch):
    # Older rows spell the track differently ('magistr', 'doktorant'); they
    # must not show up as a separate uncovered track.
    _patch_track_sources(
        monkeypatch,
        admins=[_admin(12, ['masters'])],
        submissions=[{'submission_track': 'magistr'}, {'submission_track': 'doktorant'}],
    )

    uncovered = fmadmin_web._uncovered_admin_tracks()

    assert [item['track'] for item in uncovered] == ['phd']


def test_admin_without_any_track_covers_nothing(monkeypatch):
    _patch_track_sources(
        monkeypatch,
        admins=[_admin(12, [])],
        submissions=[{'submission_track': 'masters'}],
    )

    assert [item['track'] for item in fmadmin_web._uncovered_admin_tracks()] == ['masters']


def test_a_database_failure_does_not_break_the_users_page(monkeypatch):
    # The warning is a nicety; it must never take the page down with it.
    def _boom():
        raise RuntimeError('database is down')

    monkeypatch.setattr(fmadmin_web, '_active_admins', _boom)

    assert fmadmin_web._uncovered_admin_tracks() == []


# --------------------------------------------------------------------------
# Track isolation: an admin sees their own track and nothing else
# --------------------------------------------------------------------------

PHD_ADMIN = {'id': 999, 'rolename': 'admin', 'roles': ['admin'], 'admin_tracks': ['phd']}
SUPERADMIN = {'id': 1, 'rolename': 'superadmin', 'roles': ['superadmin']}


def test_admin_sees_an_unassigned_submission_from_their_own_track():
    submission = {'id': 5, 'submission_track': 'phd', 'assigned_admin_id': None}
    assert fmadmin_web._can_access_submission(PHD_ADMIN, submission) is True


def test_admin_does_not_see_another_track():
    for track in ('masters', 'teacher'):
        submission = {'id': 5, 'submission_track': track, 'assigned_admin_id': None}
        assert fmadmin_web._can_access_submission(PHD_ADMIN, submission) is False, track


def test_admin_does_not_see_untracked_submissions():
    # The regression: a submission with no track used to pass the fallback for
    # every admin, so a Doktorantura admin also saw unrelated work.
    for track in (None, '', '   '):
        submission = {'id': 5, 'submission_track': track, 'assigned_admin_id': None}
        assert fmadmin_web._can_access_submission(PHD_ADMIN, submission) is False


def test_untracked_submission_still_reaches_the_superadmin():
    submission = {'id': 5, 'submission_track': None, 'assigned_admin_id': None}
    assert fmadmin_web._can_access_submission(SUPERADMIN, submission) is True


def test_an_explicit_owner_beats_the_track_fallback():
    # Once a submission has an owner, ownership decides -- including when the
    # track later moves out of that admin's list.
    mine = {'id': 5, 'submission_track': 'masters', 'assigned_admin_id': 999}
    someone_elses = {'id': 6, 'submission_track': 'phd', 'assigned_admin_id': 1000}

    assert fmadmin_web._can_access_submission(PHD_ADMIN, mine) is True
    assert fmadmin_web._can_access_submission(PHD_ADMIN, someone_elses) is False


def test_editors_never_reach_submissions_through_this_gate():
    editor = {'id': 7, 'rolename': 'editor', 'roles': ['editor'], 'admin_tracks': ['phd']}
    submission = {'id': 5, 'submission_track': 'phd', 'assigned_admin_id': None}

    assert fmadmin_web._can_access_submission(editor, submission) is False


def test_untracked_and_unowned_submissions_are_counted_for_the_superadmin(monkeypatch):
    _patch_track_sources(
        monkeypatch,
        admins=[_admin(12, ['masters'])],
        submissions=[
            {'submission_track': None, 'assigned_admin_id': None},
            {'submission_track': '', 'assigned_admin_id': None},
            # Has an owner, so somebody sees it -- not counted.
            {'submission_track': None, 'assigned_admin_id': 12},
            # Has a track, so a track admin sees it -- not counted.
            {'submission_track': 'phd', 'assigned_admin_id': None},
        ],
    )

    assert fmadmin_web._untracked_submission_count() == 2


def test_untracked_count_survives_a_database_failure(monkeypatch):
    class _Boom:
        @property
        def submissions(self):
            raise RuntimeError('database is down')

    monkeypatch.setattr(fmadmin_web, 'db', _Boom())

    assert fmadmin_web._untracked_submission_count() == 0
