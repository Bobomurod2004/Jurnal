from types import SimpleNamespace

import pytest
from flask import Flask
from werkzeug.exceptions import NotFound

from mainweb.routes import public as public_routes
from shared import special_issues


class _Query:
    def __init__(self, rows):
        self._rows = [dict(row) for row in rows]

    def equal(self, **values):
        return _Query([
            row for row in self._rows
            if all(row.get(key) == value for key, value in values.items())
        ])

    def exec(self):
        return [dict(row) for row in self._rows]


class _Table:
    def __init__(self, rows):
        self._rows = rows

    def get(self, **values):
        query = _Query(self._rows)
        return query.equal(**values) if values else query


def test_special_metadata_is_electronic_and_ignores_legacy_venue():
    metadata = special_issues.metadata_from_form({
        'special_description_uz': 'Elektron nashr tavsifi',
        'special_organizer_uz': 'Tahririyat',
        'special_publication_languages_uz': "O'zbekcha, inglizcha",
        'special_venue_uz': 'Legacy physical location',
        'special_event_date': '2026-10-02',
    })

    assert special_issues.is_special_issue({'category': 'special'})
    assert metadata['description']['uz'] == 'Elektron nashr tavsifi'
    assert metadata['organizer']['uz'] == 'Tahririyat'
    assert 'venue' not in metadata
    assert special_issues.public_details({'venue': {'uz': 'Hidden'}}, 'uz').get('venue') is None


def test_special_overview_includes_every_special_category(monkeypatch):
    issues = [
        {'id': 1, 'year': 2026, 'created_at': 1, 'category': 'special', 'title': 'General', 'shortinfo': '', 'price': ''},
        {'id': 2, 'year': 2026, 'created_at': 2, 'category': 'special_masters', 'title': 'Masters', 'shortinfo': '', 'price': ''},
        {'id': 3, 'year': 2025, 'created_at': 3, 'category': 'special_phd', 'title': 'PhD', 'shortinfo': '', 'price': ''},
        {'id': 4, 'year': 2026, 'created_at': 4, 'category': 'teacher', 'title': 'Regular', 'shortinfo': '', 'price': ''},
    ]
    fake_dbc = SimpleNamespace(
        issues=_Table(issues),
        fix_issue_categories=_Table([{'alias': 'special', 'name': 'Special Issue'}]),
    )
    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)
    monkeypatch.setattr(public_routes, 'translate', lambda item: item)
    monkeypatch.setattr(public_routes, '_apply_localized_content', lambda *_args, **_kwargs: None)
    monkeypatch.setattr(public_routes, 'render_template', lambda _template, **context: context)

    app = Flask(__name__)
    app.secret_key = 'test'
    with app.test_request_context('/issues?category=special'):
        context = public_routes.app__issues()

    assert [issue['id'] for issue in context['issues']] == [3, 2, 1]
    assert context['available_years'] == [2026, 2025]


def test_public_special_document_download_is_limited_to_saved_document(monkeypatch, tmp_path):
    document_id = 'b' * 32
    relative_path = f'/static/uploads/special_issues/{"a" * 32}.pdf'
    document_path = tmp_path / relative_path.lstrip('/')
    document_path.parent.mkdir(parents=True)
    document_path.write_bytes(b'%PDF-1.4\nexample')

    fake_dbc = SimpleNamespace(
        issues=_Table([{'id': 7, 'category': 'special'}]),
        conn=object(),
    )
    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)
    monkeypatch.setattr(public_routes.settings, 'SAVE_PATH', str(tmp_path))
    monkeypatch.setattr(special_issues, 'load_details', lambda _conn, _issue_id: {
        'documents': [{
            'id': document_id,
            'filepath': relative_path,
            'filename': 'information-letter.pdf',
            'format': 'PDF',
        }],
    })

    app = Flask(__name__)
    app.secret_key = 'test'
    with app.test_request_context(f'/issue/7/document/{document_id}'):
        response = public_routes.app__download_special_issue_document(7, document_id)
        response.direct_passthrough = False
        assert response.status_code == 200
        assert response.mimetype == 'application/pdf'
        assert 'filename=information-letter.pdf' in response.headers['Content-Disposition']
        assert response.get_data().startswith(b'%PDF-1.4')

    with app.test_request_context('/issue/7/document/not-present'):
        with pytest.raises(NotFound):
            public_routes.app__download_special_issue_document(7, 'not-present')
