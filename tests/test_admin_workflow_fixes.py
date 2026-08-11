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

from flask import Flask

from fmadmin.routes import web as fmadmin_web
from fmadmin.utils.filters import (
    parse_ui_date,
    parse_ui_datetime,
    timestamp_to_datetime,
    ui_datetime_input_value,
)
from shared.user_timezone import DEFAULT_ZONE_NAME


# --------------------------------------------------------------------------
# Admin timezone
#
# These filters now resolve the *viewer's own* stored timezone (see
# shared/user_timezone.py) instead of a single hardcoded offset, so a
# foreign editor/author sees their own local time. Every test below calls
# the filters with no active Flask session, which is exactly the "no
# preference set yet" case -- they must keep behaving exactly as before,
# falling back to the shared Tashkent default.
# --------------------------------------------------------------------------

def test_ui_offset_defaults_to_tashkent():
    assert DEFAULT_ZONE_NAME == 'Asia/Tashkent'


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


# --------------------------------------------------------------------------
# Assignment deadlines: the admin's chosen window survives the next round
# --------------------------------------------------------------------------

HOUR = 60 * 60
DAY = 24 * HOUR

ACCEPTANCE_DEFAULT = fmadmin_web.EDITOR_ASSIGNMENT_DEFAULT_ACCEPTANCE_SECONDS
COMPLETION_DEFAULT = fmadmin_web.EDITOR_ASSIGNMENT_DEFAULT_COMPLETION_SECONDS


def _previous(assigned_at=1_000_000, acceptance=None, completion=None, **extra):
    row = {'assigned_at': assigned_at}
    if acceptance is not None:
        row['acceptance_deadline_at'] = assigned_at + acceptance
    if completion is not None:
        row['completion_deadline_at'] = assigned_at + completion
    row.update(extra)
    return row


def test_ten_day_acceptance_window_is_carried_into_the_next_round():
    # The reported bug: an admin allowed ten days to accept, the next round
    # silently reset it to 24h and the invitation was deleted after one day.
    previous = _previous(acceptance=10 * DAY, completion=20 * DAY)

    acceptance, completion = fmadmin_web._assignment_windows_from(previous)

    assert acceptance == 10 * DAY
    assert completion == 20 * DAY


def test_defaults_apply_only_when_there_is_nothing_to_inherit():
    for previous in (None, {}, {'acceptance_deadline_at': 123}):
        acceptance, completion = fmadmin_web._assignment_windows_from(previous)
        assert (acceptance, completion) == (ACCEPTANCE_DEFAULT, COMPLETION_DEFAULT)


def test_created_at_stands_in_when_assigned_at_is_missing():
    previous = {'created_at': 1_000_000, 'acceptance_deadline_at': 1_000_000 + 3 * DAY}

    acceptance, _completion = fmadmin_web._assignment_windows_from(previous)

    assert acceptance == 3 * DAY


def test_legacy_deadline_at_is_used_when_completion_is_absent():
    previous = {'assigned_at': 1_000_000, 'deadline_at': 1_000_000 + 7 * DAY}

    _acceptance, completion = fmadmin_web._assignment_windows_from(previous)

    assert completion == 7 * DAY


def test_acceptance_window_never_exceeds_the_one_month_ceiling():
    previous = _previous(acceptance=90 * DAY, completion=120 * DAY)

    acceptance, _completion = fmadmin_web._assignment_windows_from(previous)

    assert acceptance == fmadmin_web.EDITOR_ASSIGNMENT_MAX_ACCEPTANCE_SECONDS


def test_a_review_is_never_due_before_the_invitation_may_be_accepted():
    # A row where completion landed before acceptance would create an
    # assignment that expires the moment it is made.
    previous = _previous(acceptance=10 * DAY, completion=2 * DAY)

    acceptance, completion = fmadmin_web._assignment_windows_from(previous)

    assert completion > acceptance


def test_a_corrupted_span_falls_back_instead_of_expiring_immediately():
    # Deadline before the assignment start: intent unrecoverable.
    previous = _previous(acceptance=-5 * DAY, completion=-1 * DAY)

    acceptance, completion = fmadmin_web._assignment_windows_from(previous)

    assert acceptance == ACCEPTANCE_DEFAULT
    assert completion > acceptance


def test_latest_assignment_wins_when_a_submission_has_several(monkeypatch):
    rows = [
        {'id': 1, 'assigned_at': 100, 'acceptance_deadline_at': 100 + DAY},
        {'id': 2, 'assigned_at': 500, 'acceptance_deadline_at': 500 + 10 * DAY},
        {'id': 3, 'assigned_at': 300, 'acceptance_deadline_at': 300 + 2 * DAY},
    ]

    class _Db:
        class editor_assignments:
            @staticmethod
            def all():
                return _Db.editor_assignments

            @staticmethod
            def equal(**kwargs):
                return _Db.editor_assignments

            @staticmethod
            def exec():
                return rows

    monkeypatch.setattr(fmadmin_web, 'db', _Db())

    latest = fmadmin_web._latest_assignment_for_submission(42)

    assert latest['id'] == 2
    acceptance, _completion = fmadmin_web._assignment_windows_from(latest)
    assert acceptance == 10 * DAY


def test_no_previous_assignment_is_not_an_error(monkeypatch):
    class _Db:
        class editor_assignments:
            @staticmethod
            def all():
                return _Db.editor_assignments

            @staticmethod
            def equal(**kwargs):
                return _Db.editor_assignments

            @staticmethod
            def exec():
                return []

    monkeypatch.setattr(fmadmin_web, 'db', _Db())

    assert fmadmin_web._latest_assignment_for_submission(42) is None
    assert fmadmin_web._latest_assignment_for_submission(None) is None


def test_default_window_reads_hours_from_the_environment(monkeypatch):
    monkeypatch.setenv('EDITOR_ACCEPTANCE_DEFAULT_HOURS', '72')
    assert fmadmin_web._default_window_seconds('EDITOR_ACCEPTANCE_DEFAULT_HOURS', 24) == 72 * HOUR

    # Nonsense and non-positive values keep the built-in fallback.
    for bad in ('', '   ', 'abc', '0', '-5'):
        monkeypatch.setenv('EDITOR_ACCEPTANCE_DEFAULT_HOURS', bad)
        assert fmadmin_web._default_window_seconds('EDITOR_ACCEPTANCE_DEFAULT_HOURS', 24) == 24 * HOUR


# --------------------------------------------------------------------------
# A missed deadline parks the assignment instead of deleting it
# --------------------------------------------------------------------------

def test_expired_is_a_known_status():
    # `_normalize_assignment_status` maps anything unknown back to 'pending'.
    # If 'expired' were not registered, the automation would keep re-expiring
    # the same row and re-notifying everyone forever.
    assert fmadmin_web.EDITOR_ASSIGNMENT_EXPIRED_STATUS in fmadmin_web.EDITOR_ASSIGNMENT_STATUS_VALUES
    assert fmadmin_web._normalize_assignment_status('expired') == 'expired'


def test_expired_counts_as_neither_active_nor_reviewed():
    expired = fmadmin_web.EDITOR_ASSIGNMENT_EXPIRED_STATUS
    assert expired not in fmadmin_web.EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES
    assert expired not in fmadmin_web.EDITOR_ASSIGNMENT_REVIEWED_STATUS_VALUES


def test_expired_assignments_do_not_count_as_pending_work():
    stats = fmadmin_web._assignment_stats([
        {'status': 'expired'},
        {'status': 'expired'},
        {'status': 'pending'},
    ])

    assert stats['pending'] == 1
    assert stats['reviewed'] == 0
    assert stats['rejected'] == 0
    # The expired rows are still part of the history.
    assert stats['total'] == 3


def test_automation_only_loads_live_assignments():
    # The expiry pass queries by active status, so a parked row is never
    # picked up a second time.
    assert 'expired' not in fmadmin_web.EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES


def test_an_expired_round_reads_as_unassigned_so_a_replacement_can_be_invited(monkeypatch):
    # Dropping the expired rows has to leave the round empty, the same state
    # the old hard delete produced -- otherwise the submission would sit in
    # `under_review` with nobody reviewing it.
    captured = {}

    class _Table:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self

        def equal(self, **kwargs):
            return self

        def update(self, **kwargs):
            captured.update(kwargs)
            return self

        def exec(self):
            return self._rows

    class _Db:
        submissions = _Table([{'id': 7, 'status': 'under_review', 'revision_number': 1}])
        editor_assignments = _Table([
            {'id': 1, 'status': 'expired', 'revision_round': 1, 'admin_decision': 'pending'},
            {'id': 2, 'status': 'expired', 'revision_round': 1, 'admin_decision': 'pending'},
        ])

    monkeypatch.setattr(fmadmin_web, 'db', _Db())

    review_status = fmadmin_web._refresh_submission_editor_review_status(7)

    assert review_status == 'not_assigned'
    # `not_assigned` must not push the submission backwards down the pipeline.
    assert 'status' not in captured


def test_a_live_assignment_alongside_an_expired_one_still_counts(monkeypatch):
    class _Table:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self

        def equal(self, **kwargs):
            return self

        def update(self, **kwargs):
            return self

        def exec(self):
            return self._rows

    class _Db:
        submissions = _Table([{'id': 7, 'status': 'under_review', 'revision_number': 1}])
        editor_assignments = _Table([
            {'id': 1, 'status': 'expired', 'revision_round': 1, 'admin_decision': 'pending'},
            {'id': 2, 'status': 'pending', 'revision_round': 1, 'admin_decision': 'pending'},
        ])

    monkeypatch.setattr(fmadmin_web, 'db', _Db())

    # Decorating a live assignment reaches for translations, which need a
    # request context.
    app = Flask(__name__)
    app.secret_key = 'test'
    with app.test_request_context('/fmadmin/'):
        assert fmadmin_web._refresh_submission_editor_review_status(7) == 'assigned'
