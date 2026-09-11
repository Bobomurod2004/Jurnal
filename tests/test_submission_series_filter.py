"""Special issues must be filtered by both track and the stored special flag."""
import inspect
from types import SimpleNamespace
from urllib.parse import parse_qs

import pytest
from flask import Flask

from fmadmin.routes import web


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self

    def unequal(self, **values):
        return _Query([
            row for row in self.rows
            if all(row.get(key) != value for key, value in values.items())
        ])

    def order_by(self, *args):
        return self

    def any(self, **values):
        return self

    def exec(self):
        return [dict(row) for row in self.rows]


@pytest.fixture
def list_submissions(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(web, '_active_admins', lambda: [])
    monkeypatch.setattr(web, 'get_editors', lambda **kwargs: [])
    monkeypatch.setattr(web, '_admin_language', lambda: 'uz')
    monkeypatch.setattr(web, '_classification_catalog_lookup', lambda lang: {})
    monkeypatch.setattr(web, '_can_assign_editors', lambda row: False)
    monkeypatch.setattr(web, 't', lambda key: key)
    monkeypatch.setattr(web, 'render_template', lambda template, **context: context)

    def render(rows, query='', role='superadmin'):
        monkeypatch.setattr(web, 'get_current_user', lambda: {'id': 1, 'rolename': role})
        monkeypatch.setattr(web, 'db', SimpleNamespace(
            submissions=_Query(rows), users=_Query([]), author_profile=_Query([]),
            editor_assignments=_Query([]),
        ))
        with app.test_request_context('/fmadmin/submissions' + query):
            return inspect.unwrap(web.submissions)()

    return render


@pytest.mark.parametrize('track', ['masters', 'phd', 'teacher'])
@pytest.mark.parametrize('special', [False, True])
def test_series_choices_separate_regular_and_special_submissions(list_submissions, track, special):
    rows = [
        dict(id=index, submission_track=key, is_special=flag, status='pending')
        for index, (key, flag) in enumerate(
            ((key, flag) for key in ('masters', 'phd', 'teacher') for flag in (False, True)), 1
        )
    ]
    selected = f'special_{track}' if special else track
    context = list_submissions(rows, f'?track={selected}')
    assert context['total_submissions'] == 1
    row = context['submissions_list'][0]
    assert row['submission_track'] == track
    assert row['is_special'] is special
    assert row['submission_track_label'] == dict(context['admin_track_choices'])[selected]
    assert context['track_filter'] == selected


def test_special_series_counts_pagination_and_access(list_submissions):
    rows = [dict(id=i, title='Science', submission_track='masters', is_special=True,
                 status='pending', assigned_admin_id=1) for i in range(1, 22)]
    rows.extend([
        dict(id=22, title='Science', submission_track='masters', is_special=True,
             status='under_review', assigned_admin_id=1),
        dict(id=23, title='Science', submission_track='masters', is_special=False, status='pending'),
        dict(id=24, title='Other', submission_track='masters', is_special=True, status='pending'),
        dict(id=25, title='Science', submission_track='masters', is_special=True,
             status='pending', assigned_admin_id=2),
        dict(id=26, title='Science', submission_track='masters', is_special=True, status='draft'),
    ])
    context = list_submissions(
        rows, '?track=special_masters&status=pending&title=Science&page=2', role='admin',
    )
    assert context['status_counts'] == {'pending': 21, 'under_review': 1}
    assert context['status_counts_total'] == 22
    assert context['total_submissions'] == 21
    assert [row['id'] for row in context['submissions_list']] == [21]
    assert parse_qs(context['pagination_query_string'].lstrip('&')) == {
        'track': ['special_masters'], 'status': ['pending'], 'title': ['Science'],
    }
    assert list_submissions(rows)['total_submissions'] == 25
    assert list_submissions(rows, '?track=special_phd')['total_submissions'] == 0


@pytest.mark.parametrize('flag', [None, False, 0, '0', 'false'])
def test_legacy_empty_and_false_flags_are_regular(list_submissions, flag):
    rows = [dict(id=1, submission_track='magistratura', is_special=flag, status='pending')]
    assert list_submissions(rows, '?track=masters')['total_submissions'] == 1
    assert list_submissions(rows, '?track=special_masters')['total_submissions'] == 0
