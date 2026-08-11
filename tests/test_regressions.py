import importlib.util
import os
import re
import threading

import pytest
from flask import Flask, flash, render_template, session

from mainweb.modules import connector as mainweb_connector
from fmadmin import connector as fmadmin_connector
from mainweb.routes import api as api_routes
from mainweb.routes import auth as auth_routes
from mainweb.routes import context as context_routes
from mainweb.routes import dashboard as dashboard_routes
from mainweb.routes import public as public_routes
from fmadmin.routes import web as fmadmin_web


def _load_scholar_readiness_audit_module():
    script_path = os.path.join(
        os.path.dirname(__file__), '..', 'mainweb', 'scripts', 'scholar_readiness_audit.py'
    )
    spec = importlib.util.spec_from_file_location('scholar_readiness_audit_test', script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_publication_recent_sort_key_prefers_publish_date_then_id():
    publications = [
        {'id': 18, 'date_publish': 1765584000},  # 2025-12-12
        {'id': 17, 'date_publish': 1797033600},  # 2026-12-12
        {'id': 21, 'date_publish': 1797033600},  # Same date as id=17, higher id should win
    ]

    ordered = sorted(publications, key=public_routes._publication_recent_sort_key, reverse=True)

    assert [row['id'] for row in ordered] == [21, 17, 18]


def test_publication_recent_sort_key_uses_id_for_same_publish_date():
    # created_at is editable in the fmadmin article form and unreliable; the
    # immutable id (insertion order) must decide ties within the same day.
    publications = [
        {'id': 200, 'date_publish': 1797033600, 'created_at': 1700000000},
        {'id': 150, 'date_publish': 1797033600, 'created_at': 1800000000},
    ]

    ordered = sorted(publications, key=public_routes._publication_recent_sort_key, reverse=True)

    assert [row['id'] for row in ordered] == [200, 150]


def test_publication_recent_sort_key_survives_corrupted_created_at():
    # Production regression: the newest article (highest id) fell out of the
    # homepage "latest" list because its created_at was wiped on edit while
    # older same-day articles kept larger created_at values.
    publications = [
        {'id': 132, 'date_publish': 1779994800, 'created_at': None},
        {'id': 102, 'date_publish': 1779994800, 'created_at': 1779999000},
        {'id': 104, 'date_publish': 1779994800, 'created_at': 1779998000},
    ]

    ordered = sorted(publications, key=public_routes._publication_recent_sort_key, reverse=True)

    assert [row['id'] for row in ordered] == [132, 104, 102]


def test_publication_recent_sort_key_ignores_legacy_publish_time_within_same_day():
    publications = [
        {'id': 121, 'date_publish': 1773852960, 'created_at': 1772970840},
        {'id': 122, 'date_publish': 1773792000, 'created_at': 1773889200},
    ]

    ordered = sorted(publications, key=public_routes._publication_recent_sort_key, reverse=True)

    assert [row['id'] for row in ordered] == [122, 121]


def test_publication_author_ids_supports_main_and_legacy_coauthor_storage():
    assert public_routes._publication_author_ids(
        {'main_author_id': '12', 'subauthor_ids': ['13', 14]}
    ) == [12, 13, 14]
    assert public_routes._publication_author_ids(
        {'main_author_id': 12, 'sub_author_ids': '{13,14,12}'}
    ) == [12, 13, 14]


def test_dashboard_publication_author_ids_support_main_and_legacy_coauthor_storage():
    assert dashboard_routes._publication_author_profile_ids(
        {'main_author_id': '12', 'subauthor_ids': ['13', 14]}
    ) == [12, 13, 14]
    assert dashboard_routes._publication_author_profile_ids(
        {'main_author_id': 12, 'sub_author_ids': '{13,14,12}'}
    ) == [12, 13, 14]


def test_dashboard_articles_exposes_only_publications_linked_to_current_author(monkeypatch):
    fake_dbc = type('FakeDBC', (), {
        'submissions': _FakeTable([{
            'id': 1,
            'user_id': 7,
            'status': 'under_review',
            'title': 'Dashboard submission',
            'main_author_id': 10,
            'subauthor_ids': [],
        }]),
        'author_profile': _FakeTable([
            {'id': 10, 'user_id': 7, 'name': 'Current Author'},
            {'id': 11, 'user_id': None, 'name': 'Other Author'},
            {'id': 12, 'user_id': 8, 'name': 'Unrelated User'},
        ]),
        'publications': _FakeTable([
            {'id': 101, 'title': 'Current author publication', 'main_author_id': 10, 'subauthor_ids': [], 'date_publish': 100},
            {'id': 102, 'title': 'Current co-author publication', 'main_author_id': 11, 'subauthor_ids': [10], 'date_publish': 200},
            {'id': 103, 'title': 'Unrelated publication', 'main_author_id': 12, 'subauthor_ids': [], 'date_publish': 300},
        ]),
    })()
    monkeypatch.setattr(dashboard_routes, 'dbc', fake_dbc)
    monkeypatch.setattr(dashboard_routes, 'translate', lambda row: row)
    monkeypatch.setattr(dashboard_routes, '_decorate_submission_with_workflow', lambda row: row)
    monkeypatch.setattr(dashboard_routes, '_load_revision_rounds', lambda _submission_id: [])
    monkeypatch.setattr(dashboard_routes, '_get_payment_guide_html_for_lang', lambda _lang: '')
    monkeypatch.setattr(dashboard_routes, '_get_payment_guide_qr_image', lambda: '')
    monkeypatch.setattr(dashboard_routes, 'render_template', lambda _template, **context: context)

    app = Flask(__name__)
    app.secret_key = 'test'
    with app.test_request_context('/dashboard/articles'):
        session['user_id'] = 7
        session['language'] = 'en'

        context = dashboard_routes.app__dashboard_articles()

    assert [submission['id'] for submission in context['submissions']] == [1]
    assert [publication['id'] for publication in context['publications']] == [102, 101]
    assert context['publications'][0]['viewer_author_role'] == 'coauthor'
    assert context['publications'][1]['viewer_author_role'] == 'main'
    assert context['author_profiles'][10]['name'] == 'Current Author'
    assert context['author_profiles'][11]['name'] == 'Other Author'


def test_dashboard_articles_template_includes_registered_publication_cards():
    template_path = os.path.join(
        os.path.dirname(__file__), '..', 'mainweb', 'templates', 'dashboard', 'articles.html'
    )
    with open(template_path, encoding='utf-8') as template_file:
        template = template_file.read()

    assert "{% if submissions or publications %}" in template
    assert "registered_publications_title" in template
    assert "url_for('app__article', article_id=publication.id)" in template
    assert "registered_publications_admin_note" in template


def test_author_tooltip_names_link_to_the_author_article_filter():
    template_path = os.path.join(
        os.path.dirname(__file__), '..', 'mainweb', 'templates', 'components', 'author_tooltip_macros.html'
    )
    with open(template_path, encoding='utf-8') as template_file:
        template = template_file.read()

    assert "url_for('app__articles', author_id=author.id)" in template


def test_new_submission_payload_sets_workflow_defaults_explicitly():
    """New drafts carry a value for every NOT NULL submissions column.

    Development creates these columns through the runtime schema sync
    (nullable) while production creates them from the migrations as NOT NULL,
    so a value missing here fails on the server only -- which is exactly how
    anti_plagiarism_status broke every new draft after 20260727_000001.
    """
    payload = api_routes._prepare_submission_payload(
        data={}, user_id=42, status='draft', is_new=True
    )

    assert payload['revision_number'] == 1
    assert payload['revision_allowed'] is True
    assert payload['revision_severity'] == 'major'
    assert payload['revision_requires_antiplagiarism_recheck'] is False
    assert payload['anti_plagiarism_status'] == 'pending'


class _FakeDbConnection:
    """Just enough of PostgreSQLConnector for ConnectorQuery to build SQL."""

    def __init__(self, tablename, columns, primary_column='id'):
        self.conn = None
        self.columns = {tablename: list(columns)}
        self.primary_columns = {tablename: primary_column}


def _captured_insert(connector_module, columns, rows):
    query = connector_module.ConnectorQuery(
        _FakeDbConnection('submissions', columns), 'submissions'
    )
    captured = {}

    def fake_sql(sql, arguments, colnames=[]):
        captured['sql'] = sql
        captured['arguments'] = arguments
        return []

    query._sql = fake_sql
    for row in rows:
        query.add(**row)
    query.exec()
    return captured


@pytest.mark.parametrize('connector_module', [mainweb_connector, fmadmin_connector])
def test_insert_omits_unset_columns_so_defaults_apply(connector_module):
    """Production regression: no new submission could be created at all.

    The INSERT used to name every table column and pass NULL for the ones the
    caller left out.  PostgreSQL honours a column DEFAULT only when the column
    is absent from the INSERT, so anti_plagiarism_status (NOT NULL DEFAULT
    'pending') was handed a NULL and rejected the row.
    """
    captured = _captured_insert(
        connector_module,
        columns=['id', 'user_id', 'status', 'anti_plagiarism_status'],
        rows=[{'user_id': 85, 'status': 'draft'}],
    )

    assert captured['sql'].startswith(
        'INSERT INTO submissions (user_id, status) VALUES (%s, %s)'
    )
    assert 'anti_plagiarism_status' not in captured['sql'].split(' VALUES ')[0]
    assert captured['arguments'] == (85, 'draft')


@pytest.mark.parametrize('connector_module', [mainweb_connector, fmadmin_connector])
def test_insert_never_writes_the_primary_key(connector_module):
    captured = _captured_insert(
        connector_module,
        columns=['id', 'user_id'],
        rows=[{'id': 999, 'user_id': 85}],
    )

    assert captured['sql'].startswith('INSERT INTO submissions (user_id) VALUES (%s)')
    assert captured['arguments'] == (85,)


@pytest.mark.parametrize('connector_module', [mainweb_connector, fmadmin_connector])
def test_bulk_insert_defaults_columns_a_row_leaves_out(connector_module):
    # Rows of one batch may set different columns; the ones a row omits have
    # to keep their database DEFAULT instead of shifting the placeholders.
    captured = _captured_insert(
        connector_module,
        columns=['id', 'user_id', 'status'],
        rows=[{'user_id': 85, 'status': 'draft'}, {'user_id': 86}],
    )

    assert 'VALUES (%s, %s), (%s, DEFAULT)' in captured['sql']
    assert captured['arguments'] == (85, 'draft', 86)


@pytest.mark.parametrize('connector_module', [mainweb_connector, fmadmin_connector])
def test_insert_rejects_unknown_columns(connector_module):
    query = connector_module.ConnectorQuery(
        _FakeDbConnection('submissions', ['id', 'user_id']), 'submissions'
    )

    with pytest.raises(ValueError):
        query.add(user_id=85, no_such_column=1)


def test_orcid_data_fetch_asks_the_rest_host_before_the_website(monkeypatch):
    # ORCID_BASE_URL points at the website because the OAuth screens live
    # there, but orcid.org answers /v3.0/... with HTML -- asking it first cost
    # a round trip per login and logged a bogus "not valid JSON" warning.
    monkeypatch.setattr(auth_routes.settings, 'ORCID_BASE_URL', 'https://orcid.org')
    requested = []

    def fake_fetch(url, timeout, access_token=None):
        requested.append(url)
        return None

    monkeypatch.setattr(auth_routes, '_fetch_orcid_json', fake_fetch)

    assert auth_routes._fetch_orcid_json_with_public_fallback(
        '/v3.0/0000-0002-1825-0097/person', timeout=5
    ) is None
    assert requested[0] == 'https://pub.orcid.org/v3.0/0000-0002-1825-0097/person'
    assert requested[-1] == 'https://orcid.org/v3.0/0000-0002-1825-0097/person'


def test_orcid_data_fetch_keeps_a_configured_api_host_first(monkeypatch):
    # A member API deployment configures an api.* base on purpose -- that one
    # really does serve the REST data and must stay the first choice.
    monkeypatch.setattr(auth_routes.settings, 'ORCID_BASE_URL', 'https://api.orcid.org')
    requested = []

    def fake_fetch(url, timeout, access_token=None):
        requested.append(url)
        return None

    monkeypatch.setattr(auth_routes, '_fetch_orcid_json', fake_fetch)

    auth_routes._fetch_orcid_json_with_public_fallback('/v3.0/0000/person', timeout=5)

    assert requested[0] == 'https://api.orcid.org/v3.0/0000/person'


def test_load_public_editorial_members_does_not_fallback_to_editor_users(monkeypatch):
    monkeypatch.setattr(public_routes, '_load_editorial_members', lambda: [])

    fake_dbc = type('FakeDBC', (), {
        'users': _FakeTable([
            {
                'id': 7,
                'email': 'editor@example.com',
                'roles': ['editor'],
            }
        ]),
    })()
    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)
    monkeypatch.setattr(public_routes, 'hydrate_user_roles', lambda user: user)
    monkeypatch.setattr(public_routes, 'user_has_role', lambda user, role: role in (user.get('roles') or []))

    assert public_routes._load_public_editorial_members() == []


class _FakeQuery:
    def __init__(self, rows):
        self._rows = [dict(row) for row in rows]

    def equal(self, **kwargs):
        filtered = self._rows
        for key, value in kwargs.items():
            filtered = [row for row in filtered if row.get(key) == value]
        return _FakeQuery(filtered)

    def unequal(self, **kwargs):
        filtered = self._rows
        for key, value in kwargs.items():
            filtered = [row for row in filtered if row.get(key) != value]
        return _FakeQuery(filtered)

    def any(self, **kwargs):
        filtered = self._rows
        for key, values in kwargs.items():
            allowed_values = set(values if isinstance(values, (list, tuple, set)) else [values])
            filtered = [row for row in filtered if row.get(key) in allowed_values]
        return _FakeQuery(filtered)

    def contains(self, **kwargs):
        filtered = self._rows
        for key, value in kwargs.items():
            filtered = [
                row for row in filtered
                if value in (row.get(key) or [])
            ]
        return _FakeQuery(filtered)

    def order_by(self, *_args):
        return self

    def exec(self):
        return [dict(row) for row in self._rows]


class _FakeTable:
    def __init__(self, rows):
        self._rows = rows

    def get(self, **kwargs):
        query = _FakeQuery(self._rows)
        if kwargs:
            return query.equal(**kwargs)
        return query


class _FakeMutableQuery:
    def __init__(self, rows, filters):
        self._rows = rows
        self._filters = filters
        self._update_payload = None

    def update(self, **kwargs):
        self._update_payload = dict(kwargs)
        return self

    def exec(self):
        matched_rows = [
            row for row in self._rows
            if all(row.get(key) == value for key, value in self._filters.items())
        ]
        if self._update_payload is not None:
            for row in matched_rows:
                row.update(self._update_payload)
        return [dict(row) for row in matched_rows]


class _FakeMutableTable:
    def __init__(self, rows):
        self._rows = [dict(row) for row in rows]

    def get(self, **kwargs):
        return _FakeMutableQuery(self._rows, kwargs)

    def add(self, **kwargs):
        row = dict(kwargs)
        self._rows.append(row)

        class _AddResult:
            def exec(self_inner):
                return [dict(row)]

        return _AddResult()


class _DummyCursor:
    def execute(self, _query, _args=None):
        return None

    def fetchall(self):
        return []

    def fetchone(self):
        return None

    def close(self):
        return None


class _DummyConn:
    def cursor(self):
        return _DummyCursor()

    def commit(self):
        return None

    def rollback(self):
        return None


class _FakeContextDBC:
    def __init__(self, issues):
        self.issues = _FakeTable(issues)
        self.conn = _DummyConn()

    def _init_tables(self):
        return None

    def _init_columns(self):
        return None


class _FakePaymentCursor:
    def __init__(self, conn):
        self._conn = conn
        self._rows = []
        self._one = None

    def execute(self, query, args=None):
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("select pg_advisory_xact_lock"):
            self._rows = []
            self._one = None
            return

        if normalized.startswith("select id, ids from payments"):
            user_id, payment_type, statuses = args
            self._rows = [
                (row['id'], row['ids'])
                for row in sorted(self._conn.payments, key=lambda item: item['id'], reverse=True)
                if row.get('user_id') == user_id
                and row.get('payment_type') == payment_type
                and row.get('status') in statuses
            ]
            self._one = None
            return

        if normalized.startswith("insert into payments"):
            new_id = self._conn.next_id
            self._conn.next_id += 1
            self._conn.payments.append({
                'id': new_id,
                'user_id': args[0],
                'status': args[1],
                'currency': args[2],
                'payment_type': args[3],
                'payment_date': args[4],
                'amount': args[5],
                'ids': args[6],
                'proof': args[7],
                'note': args[8],
                'created_at': args[9],
            })
            self._rows = []
            self._one = (new_id,)
            return

        raise AssertionError(f"Unexpected query: {query}")

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        if self._one is not None:
            value = self._one
            self._one = None
            return value
        if self._rows:
            return self._rows.pop(0)
        return None

    def close(self):
        return None


class _FakePaymentConn:
    def __init__(self, payments):
        self.payments = [dict(item) for item in payments]
        self.next_id = (max([item['id'] for item in self.payments]) + 1) if self.payments else 1
        self.commit_calls = 0
        self.rollback_calls = 0

    def cursor(self):
        return _FakePaymentCursor(self)

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1


class _FakePaymentDBC:
    def __init__(self, payments):
        self.conn = _FakePaymentConn(payments)
        self._lock = threading.RLock()


def test_app_issues_ignores_invalid_year_filter(monkeypatch):
    issues = [
        {'id': 1, 'year': 2024, 'issue_no': 1, 'title': 'A', 'shortinfo': '', 'price': '', 'category': 'regular', 'is_paid': False, 'subscription_enable': True},
        {'id': 2, 'year': 2025, 'issue_no': 2, 'title': 'B', 'shortinfo': '', 'price': '', 'category': 'regular', 'is_paid': True, 'subscription_enable': False},
    ]
    categories = [{'id': 1, 'name': 'Regular'}]
    fake_dbc = type('FakeDBC', (), {
        'issues': _FakeTable(issues),
        'fix_issue_categories': _FakeTable(categories),
    })()

    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)
    monkeypatch.setattr(public_routes, 'translate', lambda item: item)
    monkeypatch.setattr(public_routes, '_apply_localized_content', lambda *_args, **_kwargs: None)
    monkeypatch.setattr(public_routes, 'render_template', lambda _template, **context: context)

    app = Flask(__name__)
    app.secret_key = 'test'
    with app.test_request_context('/issues?year=invalid-year'):
        response_context = public_routes.app__issues()

    assert response_context['current_filters']['year'] == ''
    assert len(response_context['issues']) == 2


def test_app_issues_normalizes_category_aliases(monkeypatch):
    issues = [
        {'id': 1, 'year': 2026, 'issue_no': 1, 'title': 'Masters A', 'shortinfo': '', 'price': '', 'category': 'masters', 'is_paid': False, 'subscription_enable': True},
        {'id': 2, 'year': 2026, 'issue_no': 2, 'title': 'PhD B', 'shortinfo': '', 'price': '', 'category': 'phd', 'is_paid': True, 'subscription_enable': False},
    ]
    categories = [
        {'id': 1, 'alias': 'masters', 'name': "Series: Master's", 'name_uz': 'Seriya: Magistratura', 'name_ru': 'Серия: Магистратура'},
        {'id': 2, 'alias': 'phd', 'name': 'Series: Doctoral', 'name_uz': 'Seriya: Doktorantura', 'name_ru': 'Серия: Докторантура'},
        {'id': 3, 'alias': 'teacher', 'name': 'Series: Professors & Teachers', 'name_uz': "Seriya: Professor-o'qituvchilar", 'name_ru': 'Серия: Профессора-преподаватели'},
        {'id': 4, 'alias': 'special', 'name': 'Special Issue', 'name_uz': 'Maxsus son', 'name_ru': 'Специальный выпуск'},
    ]
    fake_dbc = type('FakeDBC', (), {
        'issues': _FakeTable(issues),
        'fix_issue_categories': _FakeTable(categories),
    })()

    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)
    monkeypatch.setattr(public_routes, 'translate', lambda item: item)
    monkeypatch.setattr(public_routes, '_apply_localized_content', lambda *_args, **_kwargs: None)
    monkeypatch.setattr(public_routes, 'render_template', lambda _template, **context: context)

    app = Flask(__name__)
    app.secret_key = 'test'

    with app.test_request_context('/issues?category=fm%20magistratura'):
        response_context = public_routes.app__issues()

    assert response_context['current_filters']['category'] == 'masters'
    assert len(response_context['issues']) == 1
    assert response_context['issues'][0]['category'] == 'masters'

    with app.test_request_context('/issues?category=fm%20magituradi'):
        response_context_typo = public_routes.app__issues()

    assert response_context_typo['current_filters']['category'] == 'masters'
    assert len(response_context_typo['issues']) == 1
    assert response_context_typo['issues'][0]['category'] == 'masters'


def test_context_inject_latest_issue_uses_year_and_issue_number(monkeypatch):
    issues = [
        {'id': 1, 'year': 2025, 'issue_no': 12, 'title': 'Older', 'shortinfo': '', 'price': ''},
        {'id': 2, 'year': 2026, 'issue_no': 2, 'title': 'Not Latest', 'shortinfo': '', 'price': ''},
        {'id': 3, 'year': 2026, 'issue_no': 4, 'title': 'Latest', 'shortinfo': '', 'price': ''},
    ]
    monkeypatch.setattr(context_routes, 'dbc', _FakeContextDBC(issues))

    app = Flask(__name__)
    app.secret_key = 'test'
    context_routes.register_context_processors(app)

    with app.test_request_context('/'):
        session['language'] = 'en'
        template_context = {}
        for processor in app.template_context_processors[None]:
            template_context.update(processor())

    assert template_context['latest_issue']['id'] == 3


def test_create_or_get_pending_payment_returns_existing_record(monkeypatch):
    fake_dbc = _FakePaymentDBC([
        {'id': 8, 'user_id': 44, 'payment_type': 'issue', 'status': 'pending', 'ids': [101]},
    ])
    monkeypatch.setattr(api_routes, 'dbc', fake_dbc)

    payment_data = {
        'user_id': 44,
        'status': 'unpaid',
        'currency': 'usd',
        'payment_type': 'issue',
        'payment_date': None,
        'amount': 10.0,
        'ids': [101],
        'proof': None,
        'note': None,
        'created_at': 123456,
    }
    result = api_routes._create_or_get_pending_payment(44, 'issue', 101, payment_data)

    assert result == {'created': False, 'payment_id': 8}
    assert len(fake_dbc.conn.payments) == 1


def test_create_or_get_pending_payment_creates_new_record(monkeypatch):
    fake_dbc = _FakePaymentDBC([])
    monkeypatch.setattr(api_routes, 'dbc', fake_dbc)

    payment_data = {
        'user_id': 99,
        'status': 'unpaid',
        'currency': 'usd',
        'payment_type': 'article',
        'payment_date': None,
        'amount': 12.5,
        'ids': [501],
        'proof': None,
        'note': 'test',
        'created_at': 654321,
    }
    result = api_routes._create_or_get_pending_payment(99, 'article', 501, payment_data)

    assert result == {'created': True, 'payment_id': 1}
    assert len(fake_dbc.conn.payments) == 1
    assert fake_dbc.conn.payments[0]['ids'] == [501]


def test_article_html_sanitizer_removes_unsafe_and_noisy_markup():
    from fmadmin.routes import web as fm_web

    raw = (
        '<p class="MsoNormal" style="margin:0" onclick="evil()">Salom <span style="color:red">dunyo</span></p>'
        '<script>alert(1)</script>'
        '<a href="javascript:alert(1)">x</a>'
        '<a href="https://example.com" target="_blank">ok</a>'
    )
    cleaned = fm_web._sanitize_article_block_html(raw)

    assert '<script' not in cleaned
    assert 'onclick=' not in cleaned
    assert 'style=' not in cleaned
    assert 'class=' not in cleaned
    assert 'javascript:' not in cleaned
    assert '<p>Salom dunyo</p>' in cleaned
    assert 'target="_blank"' in cleaned
    assert 'rel="noopener noreferrer"' in cleaned


def test_article_html_sanitizer_formats_plain_text_as_paragraphs():
    from fmadmin.routes import web as fm_web

    raw = 'Birinchi satr\nIkkinchi satr\n\nUchinchi satr'
    cleaned = fm_web._sanitize_article_block_html(raw)

    assert cleaned == '<p>Birinchi satr<br>Ikkinchi satr</p><p>Uchinchi satr</p>'


def test_page_html_sanitizer_keeps_layout_markup_but_strips_unsafe():
    from fmadmin.routes import web as fm_web

    raw = (
        '<section class="mb-8"><h4 class="text-lg font-semibold mb-3">Hi</h4>'
        '<p class="mb-4">Text <strong>bold</strong></p>'
        '<div class="grid" onclick="evil()">d</div>'
        '<script>alert(1)</script>'
        '<a href="javascript:alert(1)">x</a></section>'
    )
    cleaned = fm_web._sanitize_page_html(raw)

    # Layout markup the public templates rely on is preserved.
    assert '<section class="mb-8">' in cleaned
    assert 'class="text-lg font-semibold mb-3"' in cleaned
    assert '<div class="grid">' in cleaned
    # Unsafe markup is stripped.
    assert '<script' not in cleaned
    assert 'onclick=' not in cleaned
    assert 'javascript:' not in cleaned


def test_article_html_sanitizer_still_strips_class_and_layout_tags():
    from fmadmin.routes import web as fm_web

    cleaned = fm_web._sanitize_article_block_html('<section class="x"><p class="y">hi</p></section>')

    assert 'class=' not in cleaned
    assert '<section' not in cleaned
    assert '<p>hi</p>' in cleaned


def test_ensure_issue_columns_force_syncs_toc_column_when_runtime_sync_disabled(monkeypatch):
    from fmadmin.routes import web as fm_web

    class _IssueSchemaCursor:
        def __init__(self, fake_db):
            self._db = fake_db

        def execute(self, query, _args=None):
            self._db.executed_queries.append(str(query))
            if 'ALTER TABLE issues ADD COLUMN IF NOT EXISTS table_of_contents_file text;' in str(query):
                self._db.alter_issues_called = True

        def close(self):
            return None

    class _IssueSchemaConn:
        def __init__(self, fake_db):
            self._db = fake_db
            self.commit_calls = 0
            self.rollback_calls = 0

        def cursor(self):
            return _IssueSchemaCursor(self._db)

        def commit(self):
            self.commit_calls += 1

        def rollback(self):
            self.rollback_calls += 1

    class _IssueSchemaDB:
        def __init__(self):
            self.columns = {'issues': ['id', 'title']}
            self.executed_queries = []
            self.alter_issues_called = False
            self.conn = _IssueSchemaConn(self)

        def _init_tables(self):
            return None

        def _init_columns(self):
            if self.alter_issues_called:
                self.columns['issues'] = ['id', 'title', 'table_of_contents_file']

    fake_db = _IssueSchemaDB()
    monkeypatch.setattr(fm_web.settings, 'RUNTIME_SCHEMA_SYNC_ENABLED', False)
    monkeypatch.setattr(fm_web, 'db', fake_db)

    assert fm_web._ensure_issue_columns(force=False) is False
    assert fake_db.executed_queries == []

    assert fm_web._ensure_issue_columns(force=True) is True
    assert any('ALTER TABLE issues ADD COLUMN IF NOT EXISTS table_of_contents_file text;' in query for query in fake_db.executed_queries)
    assert fake_db.conn.commit_calls == 1


def test_ensure_seed_page_backfills_localized_fields_from_seed(monkeypatch):
    alias = 'submission_guidelines'
    seed_payload = public_routes._seed_page_payload(alias)
    existing_row = {
        'alias': alias,
        'title': seed_payload['title'],
        'content': seed_payload['content'],
        'title_uz': seed_payload['title'],
        'title_ru': '',
        'content_uz': seed_payload['content'],
        'content_ru': '',
        'last_update': 1,
    }
    fake_dbc = type('FakeDBC', (), {
        'pages': _FakeMutableTable([existing_row]),
        'columns': {'pages': set(existing_row.keys())},
        'conn': _DummyConn(),
    })()
    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)

    page = public_routes._ensure_seed_page(alias)

    assert page['title_uz'] == seed_payload['title_uz']
    assert page['title_ru'] == seed_payload['title_ru']
    assert page['content_uz'] == seed_payload['content_uz']
    assert page['content_ru'] == seed_payload['content_ru']


def test_ensure_seed_page_backfills_ru_when_old_ru_matches_uz_seed(monkeypatch):
    alias = 'submission_guidelines'
    seed_payload = public_routes._seed_page_payload(alias)
    existing_row = {
        'alias': alias,
        'title': seed_payload['title'],
        'content': seed_payload['content'],
        'title_uz': seed_payload['title_uz'],
        'title_ru': seed_payload['title_uz'],
        'content_uz': seed_payload['content_uz'],
        'content_ru': seed_payload['content_uz'],
        'last_update': 1,
    }
    fake_dbc = type('FakeDBC', (), {
        'pages': _FakeMutableTable([existing_row]),
        'columns': {'pages': set(existing_row.keys())},
        'conn': _DummyConn(),
    })()
    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)

    page = public_routes._ensure_seed_page(alias)

    assert page['title_ru'] == seed_payload['title_ru']
    assert page['content_ru'] == seed_payload['content_ru']


def test_ensure_seed_page_backfills_base_content_when_old_base_matches_localized_seed(monkeypatch):
    alias = 'editorial_policy'
    seed_payload = public_routes._seed_page_payload(alias)
    existing_row = {
        'alias': alias,
        'title': seed_payload['title_uz'],
        'content': seed_payload['content_uz'],
        'title_uz': seed_payload['title_uz'],
        'title_ru': seed_payload['title_ru'],
        'content_uz': seed_payload['content_uz'],
        'content_ru': seed_payload['content_ru'],
        'last_update': 1,
    }
    fake_dbc = type('FakeDBC', (), {
        'pages': _FakeMutableTable([existing_row]),
        'columns': {'pages': set(existing_row.keys())},
        'conn': _DummyConn(),
    })()
    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)

    page = public_routes._ensure_seed_page(alias)

    assert page['title'] == seed_payload['title']
    assert page['content'] == seed_payload['content']


def test_ensure_seed_page_keeps_custom_localized_fields(monkeypatch):
    alias = 'submission_guidelines'
    seed_payload = public_routes._seed_page_payload(alias)
    existing_row = {
        'alias': alias,
        'title': seed_payload['title'],
        'content': seed_payload['content'],
        'title_uz': 'Maxsus mahalliy sarlavha',
        'title_ru': 'Пользовательский заголовок',
        'content_uz': '<section><h4>Maxsus</h4><p>Admin tahriri</p></section>',
        'content_ru': '<section><h4>Пользовательский</h4><p>Редакторский текст</p></section>',
        'last_update': 1,
    }
    fake_dbc = type('FakeDBC', (), {
        'pages': _FakeMutableTable([existing_row]),
        'columns': {'pages': set(existing_row.keys())},
        'conn': _DummyConn(),
    })()
    monkeypatch.setattr(public_routes, 'dbc', fake_dbc)

    page = public_routes._ensure_seed_page(alias)

    assert page['title_uz'] == existing_row['title_uz']
    assert page['title_ru'] == existing_row['title_ru']
    assert page['content_uz'] == existing_row['content_uz']
    assert page['content_ru'] == existing_row['content_ru']


def test_editorial_policy_seed_content_is_english():
    seed_payload = public_routes._seed_page_payload('editorial_policy')

    assert 'Affiliations' in seed_payload['content']
    assert 'Peer review' in seed_payload['content']
    assert 'Аффилиации' in seed_payload['content_ru']
    assert 'Рецензирование' in seed_payload['content_ru']


def test_dashboard_profile_document_labels_follow_selected_language(monkeypatch):
    fake_dbc = type('FakeDBC', (), {
        'users': _FakeTable([{
            'id': 1,
            'name': 'Ali',
            'second_name': 'Valiyev',
            'father_name': 'Vali o\'g\'li',
            'email': 'ali@example.com',
            'avatar': None,
            'country_id': None,
        }]),
        'author_profile': _FakeTable([]),
        'user_doc_uploads': _FakeTable([]),
        'fix_country': _FakeTable([]),
    })()
    monkeypatch.setattr(dashboard_routes, 'dbc', fake_dbc)
    monkeypatch.setattr(dashboard_routes, 'render_template', lambda _template, **context: context)
    monkeypatch.setattr(
        dashboard_routes,
        'get_user_profile_completion',
        lambda **_kwargs: type('ProfileCompletion', (), {'is_complete': True})(),
    )

    app = Flask(__name__)
    app.secret_key = 'test'

    with app.test_request_context('/dashboard/profile'):
        session['user_id'] = 1
        session['user'] = {}
        session['language'] = 'ru'

        response_context = dashboard_routes.app__dashboard_profile()

    assert response_context['document_ui_labels']['document_type'] == 'Тип документа'
    assert response_context['document_ui_labels']['document_holder_name'] == 'Ф.И.О. владельца документа'
    assert response_context['document_ui_labels']['institution_name'] == 'Название университета / учреждения'
    assert response_context['document_type_choices'][0] == ('student_id', 'Студенческий билет')
    assert response_context['document_type_choices'][-1] == ('other_academic', 'Другой академический документ')


def test_api_document_type_label_follows_selected_language():
    app = Flask(__name__)
    app.secret_key = 'test'

    with app.test_request_context('/api/user-doc-upload'):
        session['language'] = 'en'
        assert api_routes._document_type_label('student_id') == 'Student ID'

        session['language'] = 'ru'
        assert api_routes._document_type_label('employment_certificate') == 'Справка с места работы'


def test_build_scholar_meta_for_open_article_includes_pdf_url(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'test'
    public_routes.register(app)
    monkeypatch.setattr(public_routes, 't', lambda key: 'Philology Matters' if key == 'website_title' else key)

    publication = {
        'title': 'Testing Google Scholar Metadata',
        'date_publish': 1735689600,  # 2025-01-01 UTC
        'page_range': '12-19',
        'doi': '10.1000/example-doi',
        'is_paid': False,
        'subscription_enable': False,
    }
    issue = {'vol_no': '3', 'issue_no': '1', 'year': 2025}

    with app.test_request_context('/article/15', base_url='https://journal.example'):
        meta = public_routes._build_scholar_meta(
            publication=publication,
            issue=issue,
            author_names=['Author One', 'Author Two'],
            article_id=15,
            current_lang='en',
        )

    assert meta['title'] == 'Testing Google Scholar Metadata'
    assert meta['authors'] == ['Author One', 'Author Two']
    assert meta['publication_date'] == '2025/1/1'
    assert meta['volume'] == '3'
    assert meta['issue'] == '1'
    assert meta['first_page'] == '12'
    assert meta['last_page'] == '19'
    assert meta['doi'] == '10.1000/example-doi'
    assert meta['issn'] == '1994-4233'
    assert meta['is_world_readable'] is True
    assert meta['fulltext_html_url'] == 'https://journal.example/article/15'
    assert meta['pdf_url'] == 'https://journal.example/article/download/15'


def test_build_scholar_meta_for_paid_article_hides_pdf_url(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'test'
    public_routes.register(app)
    monkeypatch.setattr(public_routes, 't', lambda key: 'Philology Matters' if key == 'website_title' else key)

    publication = {
        'title': 'Paid Article',
        'date_publish': 1735689600,
        'page_range': '55',
        'doi': '',
        'is_paid': True,
        'subscription_enable': False,
    }
    issue = {'vol_no': '4', 'issue_no': '2', 'year': 2025}

    with app.test_request_context('/article/99', base_url='https://journal.example'):
        meta = public_routes._build_scholar_meta(
            publication=publication,
            issue=issue,
            author_names=['Author A'],
            article_id=99,
            current_lang='uz',
        )

    assert meta['first_page'] == '55'
    assert meta['last_page'] == '55'
    assert meta['is_world_readable'] is False
    assert meta['fulltext_html_url'] == ''
    assert meta['pdf_url'] == ''
    assert meta['language'] == 'uz'


def test_scholar_article_template_uses_issn_and_hides_paid_fulltext_url():
    template_path = os.path.join(
        os.path.dirname(__file__), '..', 'mainweb', 'templates', 'mainweb', 'article.html'
    )
    with open(template_path, encoding='utf-8') as template_file:
        template = template_file.read()

    assert 'name="citation_issn"' in template
    assert 'scholar_meta.fulltext_html_url' in template
    assert 'citation_fulltext_html_url" content="{{ scholar_meta.fulltext_html_url }}"' in template


def test_scholar_publication_validation_requires_public_metadata_and_open_pdf():
    missing = fmadmin_web._scholar_publication_missing_fields(
        abstract='<p>&nbsp;</p>',
        main_author_id=None,
        issue_id='',
        date_publish=None,
        file_ids=[],
        is_paid=False,
        subscription_enable=False,
    )

    assert missing == ['abstract', 'main_author', 'issue', 'publication_date', 'open_access_pdf']
    assert fmadmin_web._scholar_publication_missing_fields(
        abstract='<p>Complete author-written abstract.</p>',
        main_author_id='12',
        issue_id='4',
        date_publish=1735689600,
        file_ids=['91'],
        is_paid=False,
        subscription_enable=False,
    ) == []
    assert fmadmin_web._scholar_publication_missing_fields(
        abstract='Paid article abstract',
        main_author_id=12,
        issue_id=4,
        date_publish=1735689600,
        file_ids=[],
        is_paid=True,
        subscription_enable=False,
    ) == []


def test_scholar_readiness_audit_checks_abstract_page_range_and_pdf_record():
    scholar_audit = _load_scholar_readiness_audit_module()
    issue = {'id': 4, 'vol_no': '56', 'issue_no': '2', 'year': 2026}

    incomplete = scholar_audit._publication_report_item(
        {
            'id': 80,
            'title': 'Incomplete publication',
            'abstract': '<p>&nbsp;</p>',
            'issue_id': 4,
            'date_publish': 1760000000,
            'page_range': '',
            'file_ids': [77],
            'is_paid': False,
            'subscription_enable': False,
        },
        issue,
        ['Author One'],
        file_map={},
    )

    assert 'missing_abstract' in incomplete['blockers']
    assert 'missing_page_range' in incomplete['blockers']
    assert 'missing_pdf_file_record' in incomplete['blockers']

    complete = scholar_audit._publication_report_item(
        {
            'id': 81,
            'title': 'Complete publication',
            'abstract': '<p>A complete abstract.</p>',
            'issue_id': 4,
            'date_publish': 1760000000,
            'page_range': '3-18',
            'file_ids': [78],
            'is_paid': False,
            'subscription_enable': False,
        },
        issue,
        ['Author One'],
        file_map={78: {'id': 78, 'name': 'article.pdf', 'filepath': '/static/uploads/articles/article.pdf'}},
    )

    assert complete['ready'] is True
    assert complete['pdf_reference_status'] == 'ok'
    assert scholar_audit._publication_pdf_reference_status(
        {'file_ids': [78]},
        {78: {'id': 78, 'name': 'article.pdf', 'filepath': '/static/uploads/articles/article.pdf'}},
        verify_files=True,
        save_path='/tmp/nonexistent-scholar-upload-root',
    ) == 'missing_pdf_on_disk'
    # The public download endpoint prefers the newest attachment.  A stale
    # file record must therefore not hide a newer usable PDF in the audit.
    assert scholar_audit._publication_pdf_reference_status(
        {'file_ids': [77, 78]},
        {
            77: {'id': 77, 'name': 'old.pdf', 'filepath': '/static/uploads/articles/old.pdf'},
            78: {'id': 78, 'name': 'new.pdf', 'filepath': '/static/uploads/articles/new.pdf'},
        },
    ) == 'ok'


def test_sitemap_excludes_masters_content_when_series_mode_disabled(monkeypatch):
    class _SimpleFakeDBC:
        def __init__(self):
            self.issues = _FakeTable([
                {'id': 1, 'year': 2025, 'category': 'phd', 'vol_no': '3', 'issue_no': '1', 'created_at': 1735689600},
                {'id': 2, 'year': 2025, 'category': 'masters', 'vol_no': '3', 'issue_no': '2', 'created_at': 1735689600},
            ])
            self.publications = _FakeTable([
                {'id': 101, 'issue_id': 1, 'title': 'Regular article', 'date_publish': 1735776000, 'is_paid': False, 'subscription_enable': False},
                {'id': 102, 'issue_id': 2, 'title': 'Masters article', 'date_publish': 1735776000, 'is_paid': False, 'subscription_enable': False},
            ])
            self.news = _FakeTable([
                {'id': 20, 'status': 'published', 'published_at': 1735862400},
            ])
            self.pages = _FakeTable([
                {'alias': 'custom-page'},
            ])
            self.conn = _DummyConn()

    app = Flask(__name__)
    app.secret_key = 'test'
    public_routes.register(app)

    monkeypatch.setattr(public_routes, 'dbc', _SimpleFakeDBC())
    monkeypatch.setattr(public_routes, '_seed_pages_data', lambda: {'submission_guidelines': {'title': 'Submission'}})
    monkeypatch.setattr(
        public_routes,
        'render_template',
        lambda _template, **context: '\n'.join(item['loc'] for item in context.get('urls', [])),
    )

    with app.test_request_context('/sitemap.xml', base_url='https://journal.example'):
        response = public_routes.app__sitemap_xml()
        body = response.get_data(as_text=True)

    assert response.mimetype == 'application/xml'
    assert 'https://journal.example/issue/1' in body
    assert 'https://journal.example/article/101' in body
    assert 'https://journal.example/issue/2' not in body
    assert 'https://journal.example/article/102' not in body


def test_extract_selected_roles_allows_superadmin_demotion():
    data = {'rolename': 'user', 'roles': ['user', 'admin', 'superadmin']}

    selection = fmadmin_web._extract_selected_roles(data, 'user', allowed_roles=['user', 'admin', 'editor'])

    assert selection['primary_role'] == 'user'
    assert selection['roles'] == ['user', 'admin']


def test_extract_selected_roles_promotes_an_allowed_superadmin_checkbox():
    # A user may choose Super Admin from the checkbox list before the primary
    # role select is synchronised. The backend must not silently turn that
    # authorised promotion back into a normal user role.
    data = {'rolename': 'user', 'roles': ['user', 'superadmin']}

    selection = fmadmin_web._extract_selected_roles(
        data,
        'user',
        allowed_roles=['user', 'admin', 'editor', 'superadmin'],
    )

    assert selection['primary_role'] == 'superadmin'
    assert fmadmin_web._roles_for_primary_role(
        selection['primary_role'], selection['roles']
    ) == ['superadmin', 'user']


def test_public_editorial_groups_follow_new_role_order_and_legacy_aliases():
    editors = [
        {'id': 1, 'member_type': 'reviewer', 'full_name': 'Legacy Reviewer'},
        {'id': 2, 'member_type': 'international_editorial_council', 'full_name': 'Council Member'},
        {'id': 3, 'member_type': 'executive_secretary', 'full_name': 'Secretary'},
        {'id': 4, 'member_type': 'editor_in_chief', 'full_name': 'Chief Editor'},
    ]

    groups = public_routes._prepare_editorial_groups(editors)

    assert [group['key'] for group in groups] == [
        'editor_in_chief',
        'executive_secretary',
        'editorial_board',
        'international_editorial_council',
    ]
    assert groups[2]['members'][0]['full_name'] == 'Legacy Reviewer'


def test_public_editorial_labels_are_localized_for_new_roles():
    app = Flask(__name__)
    app.secret_key = 'test'

    with app.test_request_context('/editorial'):
        session['language'] = 'uz'
        assert public_routes._editorial_member_type_label('deputy_editor_in_chief') == "Bosh muharrir o'rinbosari"
        assert public_routes._normalize_editorial_member_type('Ответственный секретарь') == 'executive_secretary'

    with app.test_request_context('/editorial'):
        session['language'] = 'ru'
        assert public_routes._editorial_member_type_label('international_editorial_council') == "Международный редакционный совет"


def test_fmadmin_editorial_type_options_use_new_role_list():
    from fmadmin.routes import web as fm_web

    options = fm_web._editorial_member_type_options('en')

    assert [item['value'] for item in options] == [
        'editor_in_chief',
        'deputy_editor_in_chief',
        'executive_secretary',
        'editorial_board',
        'international_editorial_board',
        'editorial_council',
        'international_editorial_council',
    ]
    assert fm_web._normalize_editorial_member_type('Главный редактор') == 'editor_in_chief'
    assert fm_web._normalize_editorial_member_type('deputy_editor') == 'executive_secretary'


def test_country_iso_lookup_handles_apostrophe_variants():
    assert public_routes._country_iso_for_name("O'zbekiston") == 'uz'
    assert public_routes._country_iso_for_name("Oʻzbekiston") == 'uz'  # official Uzbek Latin ʻ
    assert public_routes._country_iso_for_name("O’zbekiston") == 'uz'  # typographic ’
    assert public_routes._country_iso_for_name('Узбекистан') == 'uz'
    assert public_routes._country_iso_for_name('Uzbekistan') == 'uz'


def test_country_catalog_resolves_flags_for_countries_outside_legacy_name_map(monkeypatch):
    class FakeCountryQuery:
        def get(self):
            return self

        def exec(self):
            return [
                {
                    'name': 'Angola',
                    'name_uz': 'Angola',
                    'name_ru': 'Ангола',
                    'country_code': 'ao',
                },
            ]

    class FakeDatabase:
        fix_country = FakeCountryQuery()

    monkeypatch.setattr(public_routes, 'dbc', FakeDatabase())
    monkeypatch.setattr(
        public_routes,
        '_country_catalog_cache',
        {'lookup': {}, 'localized_names': {}},
    )
    monkeypatch.setattr(public_routes, '_country_catalog_cache_timestamp', 0.0)

    assert public_routes._country_iso_for_name('Angola') == 'ao'
    assert public_routes._country_localized_names_by_iso()['ao']['ru'] == 'Ангола'


def test_bot_requests_do_not_increment_view_or_download_counters():
    app = Flask(__name__)
    app.secret_key = 'test'

    bot_headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    with app.test_request_context('/article/5', headers=bot_headers):
        assert public_routes._should_increment_article_view(5) is False
        assert public_routes._should_increment_download('download', 5) is False

    # Missing user agent is treated as a bot as well
    with app.test_request_context('/article/5'):
        assert public_routes._should_increment_article_view(5) is False


def test_download_counter_deduplicates_within_session():
    app = Flask(__name__)
    app.secret_key = 'test'

    browser_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'}
    with app.test_request_context('/article/download/7', headers=browser_headers):
        assert public_routes._should_increment_download('download', 7) is True
        assert public_routes._should_increment_download('download', 7) is False
        # A different object or kind still counts
        assert public_routes._should_increment_download('download', 8) is True
        assert public_routes._should_increment_download('issue_download', 7) is True


def test_activity_marks_session_is_pruned_and_capped():
    app = Flask(__name__)
    app.secret_key = 'test'

    browser_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'}
    with app.test_request_context('/', headers=browser_headers):
        for object_id in range(1, 150):
            assert public_routes._should_count_activity('view', object_id) is True
        marks = session[public_routes.ACTIVITY_SESSION_MARKS_KEY]
        assert len(marks) <= public_routes.ACTIVITY_SESSION_MARKS_LIMIT


def test_request_country_resolution_prefers_cdn_header_then_geoip(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'test'

    with app.test_request_context('/', headers={'CF-IPCountry': 'JP'}):
        assert public_routes._resolve_request_country_name() == 'Japan'

    class _FakeReader:
        def get(self, ip_address):
            assert ip_address == '203.0.113.5'
            return {'country': {'iso_code': 'CA'}}

    monkeypatch.setattr(public_routes, '_get_geoip_reader', lambda: _FakeReader())
    with app.test_request_context('/', environ_base={'REMOTE_ADDR': '203.0.113.5'}):
        assert public_routes._resolve_request_country_name() == 'Canada'


def test_recent_issues_sidebar_shows_latest_three_in_order(monkeypatch):
    issues = [
        {'id': 4, 'year': 2024, 'vol_no': 1, 'issue_no': 1, 'category': 'phd'},
        {'id': 9, 'year': 2025, 'vol_no': 2, 'issue_no': 1, 'category': 'phd'},
        {'id': 12, 'year': 2025, 'vol_no': 2, 'issue_no': 3, 'category': 'phd'},
        {'id': 11, 'year': 2025, 'vol_no': 2, 'issue_no': 2, 'category': 'phd'},
        {'id': 13, 'year': 2026, 'vol_no': 3, 'issue_no': 1, 'category': 'masters'},
    ]

    visible = [issue for issue in issues if issue.get('category') != 'masters']
    ordered = sorted(
        visible,
        key=lambda issue: (
            issue.get('year') or 0,
            issue.get('vol_no') or 0,
            issue.get('issue_no') or 0,
            issue.get('created_at') or 0,
            issue.get('id') or 0,
        ),
        reverse=True,
    )[:3]

    assert [issue['id'] for issue in ordered] == [12, 11, 9]


def _registration_payload():
    return {
        'first_name': 'Ali',
        'last_name': 'Valiyev',
        # Stored as NULL in the pending-verification payload when the field is
        # left blank; .get('father_name', '') then returns None, which crashed
        # user creation with AttributeError before the `or ''` guard.
        'father_name': None,
        'email': 'ali@example.com',
        'country_id': 1,
        'password_hash': 'pbkdf2:fake-hash',
        'is_notify': True,
        'ui_language': 'uz',
    }


def test_registration_create_data_omits_ui_language_when_column_missing(monkeypatch):
    # Production regression: users.ui_language is created only by the runtime
    # schema sync (disabled in production), so inserting it unconditionally
    # made dbc.users.add() raise and /register/verify respond with 500.
    app = Flask(__name__)
    app.secret_key = 'test'

    legacy_columns = [
        'id', 'name', 'second_name', 'father_name', 'email', 'password',
        'country_id', 'rolename', 'is_blocked', 'is_notify',
        'accept_rules_time', 'register_time', 'created_at', 'last_online',
    ]
    fake_dbc = type('FakeDBC', (), {'columns': {'users': legacy_columns}})()
    monkeypatch.setattr(auth_routes, 'dbc', fake_dbc)

    with app.test_request_context('/register/verify'):
        create_data = auth_routes._build_user_create_data_from_registration(_registration_payload())

    assert create_data is not None
    assert 'ui_language' not in create_data
    assert 'roles' not in create_data


def test_registration_create_data_includes_ui_language_when_column_exists(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'test'

    columns = [
        'id', 'name', 'second_name', 'father_name', 'email', 'password',
        'country_id', 'rolename', 'is_blocked', 'is_notify',
        'accept_rules_time', 'register_time', 'created_at', 'last_online',
        'ui_language',
    ]
    fake_dbc = type('FakeDBC', (), {'columns': {'users': columns}})()
    monkeypatch.setattr(auth_routes, 'dbc', fake_dbc)

    with app.test_request_context('/register/verify'):
        create_data = auth_routes._build_user_create_data_from_registration(_registration_payload())

    assert create_data is not None
    assert create_data['ui_language'] == 'uz'


def test_compute_revision_reentry_failed_technical_check_goes_to_pending():
    # A submission that failed the technical check re-enters at 'pending',
    # not all the way back to a blank draft.
    existing = {'status': 'failed_technical_check'}
    status, needs_editor = api_routes._compute_revision_reentry(existing)
    assert (status, needs_editor) == ('pending', False)


def test_compute_revision_reentry_revision_required_returns_to_admin_triage():
    # A revision requested after peer review returns to the admin-visible
    # review stage. The admin chooses whether the same reviewer receives a
    # fresh invitation; a completed assignment must not be silently reopened.
    existing = {'status': 'revision_required'}
    status, needs_editor = api_routes._compute_revision_reentry(existing)
    assert (status, needs_editor) == ('under_review', False)


def test_compute_revision_reentry_missing_or_unknown_status_falls_back_conservatively():
    # Legacy rows resubmitted before this feature existed have no reliable
    # status -- the safest default is the earliest re-entry point, not
    # skipping straight back into review.
    status, needs_editor = api_routes._compute_revision_reentry({})
    assert (status, needs_editor) == ('pending', False)

    status, needs_editor = api_routes._compute_revision_reentry({'status': 'not_a_real_status'})
    assert (status, needs_editor) == ('pending', False)


def test_revision_snapshot_keeps_the_replaced_manuscript_files(monkeypatch):
    class RevisionLogTable:
        def __init__(self):
            self.added = []

        def get(self, **_filters):
            return self

        def add(self, **payload):
            self.added.append(payload)
            return self

        def exec(self):
            return []

    revision_log = RevisionLogTable()
    monkeypatch.setattr(
        api_routes,
        'dbc',
        type('FakeDBC', (), {'submission_revision_log': revision_log})(),
    )

    api_routes._log_submission_revision(
        {
            'id': 44,
            'revision_number': 1,
            'file_authors': 'private://articles/authors_old.docx',
            'file_anonymized': 'private://articles/anonymized_old.docx',
        },
        actor_user_id=7,
        now_ts=123456,
        is_resubmitted=False,
    )

    assert revision_log.added == [{
        'submission_id': 44,
        'revision_number': 1,
        'rejection_origin': None,
        'rejected_by': None,
        'rejected_at': None,
        'rejection_notes': None,
        'resubmitted_at': None,
        'resubmitted_by': None,
        'file_authors': 'private://articles/authors_old.docx',
        'file_anonymized': 'private://articles/anonymized_old.docx',
        'created_at': 123456,
    }]


def test_revision_file_change_flags_compare_the_current_and_previous_versions():
    flags = fmadmin_web._submission_file_change_flags(
        {
            'revision_number': 2,
            'file_authors': 'private://articles/authors_new.docx',
            'file_anonymized': 'private://articles/anonymized_new.docx',
        },
        [{
            'revision_number': 1,
            'file_authors': 'private://articles/authors_old.docx',
            'file_anonymized': 'private://articles/anonymized_old.docx',
        }],
    )

    assert flags == {'authors_changed': True, 'anonymized_changed': True}


def test_requesting_revision_archives_the_current_manuscript_files(monkeypatch):
    class RevisionLogTable:
        def __init__(self):
            self.added = []

        def all(self):
            return self

        def equal(self, **_filters):
            return self

        def add(self, **payload):
            self.added.append(payload)
            return self

        def exec(self):
            return []

    revision_log = RevisionLogTable()
    monkeypatch.setattr(
        fmadmin_web,
        'db',
        type('FakeDB', (), {'submission_revision_log': revision_log})(),
    )

    fmadmin_web._archive_submission_revision_files(
        {
            'id': 44,
            'revision_number': 1,
            'file_authors': 'private://articles/authors_old.docx',
            'file_anonymized': 'private://articles/anonymized_old.docx',
        },
        opened_by=7,
        reason='Xulosani to‘g‘rilang',
        opened_at=123456,
    )

    assert revision_log.added[0]['revision_number'] == 1
    assert revision_log.added[0]['file_authors'] == 'private://articles/authors_old.docx'
    assert revision_log.added[0]['file_anonymized'] == 'private://articles/anonymized_old.docx'
    assert revision_log.added[0]['rejection_notes'] == 'Xulosani to‘g‘rilang'


def test_is_resubmittable_excludes_final_rejection():
    assert api_routes.is_resubmittable('failed_technical_check') is True
    assert api_routes.is_resubmittable('revision_required') is True
    assert api_routes.is_resubmittable('rejected') is False
    assert api_routes.is_resubmittable('published') is False


def test_article_resubmit_route_was_removed_in_favor_of_in_place_revision():
    # The old /api/article/resubmit endpoint used to create a brand-new,
    # disconnected submission row on every resubmit, discarding all review
    # history. It must stay gone -- resubmission now flows entirely through
    # /api/article/submit (see _compute_revision_reentry above).
    app = Flask(__name__)
    app.secret_key = 'test'

    api_routes.register(app)

    resubmit_rules = [rule for rule in app.url_map.iter_rules() if rule.rule == '/api/article/resubmit']
    assert resubmit_rules == []

    submit_rule = next(rule for rule in app.url_map.iter_rules() if rule.rule == '/api/article/submit')
    assert 'POST' in submit_rule.methods


def _assignable_submission(**overrides):
    submission = {
        'id': 42,
        'file_anonymized': 'uploads/anon-42.docx',
        'anti_plagiarism_status': 'passed',
        'status': 'plagiarism_check',
    }
    submission.update(overrides)
    return submission


def test_can_assign_editors_allows_under_review_so_a_replacement_editor_can_be_picked():
    # Production regression: assigning the first editor flips the submission to
    # `under_review`, and if that editor never opened the task the acceptance
    # deadline expiry DELETES the assignment row while the submission stays
    # `under_review`. The assign buttons used to be gated on the pre-review
    # statuses only, so such submissions were stuck with zero editors and no
    # way to assign anyone else.
    assert fmadmin_web._can_assign_editors(_assignable_submission(status='under_review')) is True
    assert fmadmin_web._can_assign_editors(_assignable_submission(status='pending')) is True
    assert fmadmin_web._can_assign_editors(_assignable_submission(status='passed_technical_check')) is True
    assert fmadmin_web._can_assign_editors(_assignable_submission(status='plagiarism_check')) is True


def test_can_assign_editors_blocks_post_review_and_terminal_statuses():
    for status in ('revision_required', 'recommended', 'payment_pending', 'in_layout', 'published', 'rejected'):
        assert fmadmin_web._can_assign_editors(_assignable_submission(status=status)) is False, status


def test_can_assign_editors_requires_anonymized_file_and_passed_antiplagiarism():
    # Mirrors the server-side gate in the assign_editors POST handler, so the
    # button never leads to a form that will immediately reject the admin.
    assert fmadmin_web._can_assign_editors(_assignable_submission(file_anonymized='')) is False
    assert fmadmin_web._can_assign_editors(_assignable_submission(file_anonymized=None)) is False
    assert fmadmin_web._can_assign_editors(_assignable_submission(anti_plagiarism_status='pending')) is False
    assert fmadmin_web._can_assign_editors(_assignable_submission(anti_plagiarism_status='failed')) is False
    assert fmadmin_web._can_assign_editors({}) is False
    assert fmadmin_web._can_assign_editors(None) is False


def test_refresh_review_status_maps_no_assignments_to_no_status_change():
    # `not_assigned` must not roll the submission back down the pipeline: the
    # author's view would jump backwards every time an unopened assignment
    # expired. `_can_assign_editors` covers the reassignment instead.
    review_statuses_that_move_the_submission = {'assigned', 'in_review', 'reviewed', 'approved'}
    assert 'not_assigned' not in review_statuses_that_move_the_submission


def test_acceptance_deadline_ceiling_is_one_month():
    # The admin picks the acceptance window (it is not a fixed 24h rule), but
    # it may not exceed one month -- otherwise a submission sits in
    # `under_review` for a whole cycle before expiry frees it for reassignment.
    assert fmadmin_web.EDITOR_ASSIGNMENT_MAX_ACCEPTANCE_SECONDS == 30 * 24 * 60 * 60
    assert fmadmin_web.EDITOR_ASSIGNMENT_DEFAULT_ACCEPTANCE_SECONDS < fmadmin_web.EDITOR_ASSIGNMENT_MAX_ACCEPTANCE_SECONDS
    # Defaults must not collide -- acceptance and completion may never be equal.
    assert (
        fmadmin_web.EDITOR_ASSIGNMENT_DEFAULT_COMPLETION_SECONDS
        > fmadmin_web.EDITOR_ASSIGNMENT_DEFAULT_ACCEPTANCE_SECONDS
    )


def test_cancel_editor_assignment_route_is_registered_as_post_only():
    # Without this route an admin has to wait out the acceptance deadline --
    # up to a month, now that the admin sets it -- before reassigning.
    app = Flask(__name__)
    app.secret_key = 'test'

    fmadmin_web.register(app)

    rule = next(
        rule for rule in app.url_map.iter_rules()
        if rule.rule == '/fmadmin/editor-assignments/<int:assignment_id>/cancel'
    )
    assert 'POST' in rule.methods
    assert 'GET' not in rule.methods


def test_rereview_route_is_registered_as_post_only():
    app = Flask(__name__)
    app.secret_key = 'test'

    fmadmin_web.register(app)

    rule = next(
        rule for rule in app.url_map.iter_rules()
        if rule.rule == '/fmadmin/submissions/<int:submission_id>/revision/re-review'
    )
    assert 'POST' in rule.methods
    assert 'GET' not in rule.methods


def _fmadmin_template_app():
    """Minimal app able to render fmadmin templates (no DB, stubbed globals)."""
    from fmadmin.utils.filters import register_filters

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(root_dir, 'fmadmin', 'templates')
    )
    app.secret_key = 'test'
    register_filters(app)
    fmadmin_web.register(app)

    @app.context_processor
    def _stub_template_globals():
        return {
            't': lambda key, *args, **kwargs: key,
            'csrf_token': 'test-token',
            'role_notifications_unread_count': 0,
            'role_notifications_preview': [],
            'upload_access_url': lambda path: '/files/%s' % path,
            'submission_status_label': lambda status, *args: str(status),
            'submission_status_badge_tone': lambda status: 'blue',
            'anti_plagiarism_status_label': lambda status: str(status),
            'anti_plagiarism_status_badge_tone': lambda status: 'green',
        }

    return app


def _render_users_directory(path='/fmadmin/users/users', **overrides):
    user = {
        'id': 8,
        'name': 'Dilnoza',
        'second_name': 'Yoqubova',
        'father_name': '',
        'email': 'dilnoza@example.com',
        'roles': ['editor'],
        'rolename': 'editor',
        'is_hidden': False,
        'is_blocked': False,
        'tariff_id': 3,
        'subscription_end_date': None,
        'editor_admin_id': None,
        'admin_tracks_labels': [],
        'directory_url': '/fmadmin/users/users/8',
        'avatar_url': '/static/uploads/avatars/avatar_8_123.png',
    }
    context = {
        'users': [user],
        'page': 1,
        'total_users': 21,
        'total_pages': 2,
        'search_name': 'Dilnoza',
        'search_email': '',
        'directory_filter': 'active',
        'role_filter': 'editor',
        'user_summary': {'total': 21, 'active': 19, 'blocked': 2, 'staff': 5, 'hidden': 1},
        'tariffs_map': {3: {'id': 3, 'name': 'Premium'}},
        'current_user': {'id': 1, 'rolename': 'superadmin'},
        'can_manage_users': True,
        'can_assign_editor_roles': True,
        'uncovered_tracks': [],
        'untracked_submission_count': 0,
    }
    context.update(overrides)

    app = _fmadmin_template_app()
    with app.test_request_context(path):
        session['fmadmin_user'] = {
            'id': 1,
            'name': 'Admin',
            'rolename': 'superadmin',
            'capabilities': ADMIN_CAPABILITIES,
        }
        return render_template('users/users/users.html', **context)


def test_user_directory_filters_and_summary_prioritize_hidden_users():
    users = [
        {'id': 1, 'name': 'Active', 'roles': ['user'], 'is_hidden': False, 'is_blocked': False},
        {'id': 2, 'name': 'Blocked', 'roles': ['user'], 'is_hidden': False, 'is_blocked': True},
        {'id': 3, 'name': 'Hidden editor', 'roles': ['editor'], 'is_hidden': True, 'is_blocked': True},
        {'id': 4, 'name': 'Admin', 'roles': ['admin'], 'is_hidden': False, 'is_blocked': False},
        {'id': 5, 'name': 'Editor', 'roles': ['editor'], 'is_hidden': False, 'is_blocked': False},
    ]

    summary = fmadmin_web._build_user_directory_summary(users)

    assert summary == {'total': 4, 'active': 3, 'blocked': 1, 'staff': 2, 'hidden': 1}
    assert [row['id'] for row in fmadmin_web._filter_user_directory_users(users)] == [1, 2, 4, 5]
    assert [row['id'] for row in fmadmin_web._filter_user_directory_users(users, directory_filter='active')] == [1, 4, 5]
    assert [row['id'] for row in fmadmin_web._filter_user_directory_users(users, directory_filter='blocked')] == [2]
    assert [row['id'] for row in fmadmin_web._filter_user_directory_users(users, directory_filter='hidden')] == [3]
    assert [row['id'] for row in fmadmin_web._filter_user_directory_users(users, directory_filter='staff')] == [4, 5]
    assert [row['id'] for row in fmadmin_web._filter_user_directory_users(users, role_filter='editor')] == [5]


def test_user_avatar_url_accepts_shared_uploads_and_oauth_urls_only():
    assert fmadmin_web._user_avatar_url({
        'avatar': '/static/uploads/avatars/avatar_18_1775454319.webp'
    }) == '/static/uploads/avatars/avatar_18_1775454319.webp'
    assert fmadmin_web._user_avatar_url({
        'avatar': 'https://lh3.googleusercontent.com/a/profile-photo'
    }) == 'https://lh3.googleusercontent.com/a/profile-photo'
    assert fmadmin_web._user_avatar_url({
        'avatar': '/static/uploads/avatars/../../private.png'
    }) == ''
    assert fmadmin_web._user_avatar_url({'avatar': 'javascript:alert(1)'}) == ''


def test_user_directory_searches_full_name_and_keeps_the_admin_scope_safe():
    users = [
        {'id': 1, 'name': 'Dilnoza', 'second_name': 'Yoqubova', 'roles': ['user'], 'is_hidden': False, 'is_blocked': False},
        {'id': 2, 'name': 'Editor', 'roles': ['editor'], 'is_hidden': False, 'is_blocked': False},
        {'id': 3, 'name': 'Admin', 'roles': ['admin'], 'is_hidden': False, 'is_blocked': False},
        {'id': 4, 'name': 'Super', 'roles': ['superadmin'], 'is_hidden': False, 'is_blocked': False},
        {'id': 5, 'name': 'Hidden', 'roles': ['user'], 'is_hidden': True, 'is_blocked': False},
    ]

    scoped_for_admin = fmadmin_web._user_directory_scope_users(
        users, can_manage_users=False, current_role='admin'
    )
    searched = fmadmin_web._filter_user_directory_users(
        scoped_for_admin, search_name='dilnoza yoqubova'
    )

    assert [row['id'] for row in scoped_for_admin] == [1, 2]
    assert [row['id'] for row in searched] == [1]


def test_users_directory_template_renders_kpis_filters_and_safe_row_navigation():
    html = _render_users_directory()

    assert 'href="/fmadmin/users/users?filter=active"' in html
    assert 'href="/fmadmin/users/users?filter=staff"' in html
    assert 'href="/fmadmin/users/users?filter=hidden"' in html
    assert 'name="role"' in html
    assert 'data-user-url="/fmadmin/users/users/8"' in html
    assert 'src="/static/uploads/avatars/avatar_8_123.png"' in html
    assert 'role="link" tabindex="0"' in html
    assert 'name="orcid"' not in html
    assert 'admin_users_primary_role' not in html
    assert 'admin_users_assigned_admin' not in html
    assert 'filter=active&amp;role=editor' in html


def _render_user_edit_template():
    context = {
        'user': {
            'id': 8,
            'name': 'Dilnoza',
            'second_name': 'Yoqubova',
            'father_name': '',
            'email': 'dilnoza@example.com',
            'country_id': None,
            'region': 'Toshkent',
            'roles': ['user'],
            'rolename': 'user',
            'is_blocked': False,
            'is_hidden': False,
            'is_notify': True,
            'accept_rules_time': None,
            'last_online': None,
            'created_at': None,
            'register_time': None,
            'tariff_id': None,
            'subscription_end_date': None,
            'admin_tracks': [],
            'editor_admin_id': None,
            'avatar_url': '/static/uploads/avatars/avatar_8_123.png',
        },
        'countries': [],
        'tariffs': [],
        'current_user': {'id': 1, 'rolename': 'superadmin'},
        'active_admins': [],
        'admin_track_choices': [],
        'role_choices': [
            ('user', 'Muallif / Author'),
            ('superadmin', 'Super Admin'),
        ],
        'user_360': None,
    }
    app = _fmadmin_template_app()
    with app.test_request_context('/fmadmin/users/users/8'):
        session['fmadmin_user'] = {
            'id': 1,
            'name': 'Admin',
            'rolename': 'superadmin',
            'capabilities': ADMIN_CAPABILITIES,
        }
        return render_template('users/users/edit.html', **context)


def test_user_edit_template_groups_fields_into_visual_tabs_without_changing_form_inputs():
    html = _render_user_edit_template()

    assert 'class="fm-user-hero' in html
    assert 'src="/static/uploads/avatars/avatar_8_123.png"' in html
    assert 'class="nav-link active" id="user-details-tab"' in html
    assert 'data-bs-target="#user-activity-pane"' in html
    assert 'class="card fm-edit-card"' in html
    assert 'name="name" value="Dilnoza"' in html
    assert 'name="email" value="dilnoza@example.com"' in html
    assert 'name="roles" value="user"' in html
    assert 'name="roles" value="superadmin"' in html
    assert "this.checked && this.value === 'superadmin'" in html
    assert 'name="tariff_id"' in html
    assert 'id="save-user-btn-top"' in html
    assert 'id="save-user-btn"' in html
    assert 'data-fm-save-feedback' in html
    assert 'id="fm-user-save-overlay"' in html


def _render_fmadmin_feedback(category, message):
    app = _fmadmin_template_app()
    with app.test_request_context('/fmadmin/users/users/8'):
        session['fmadmin_user'] = {
            'id': 1,
            'name': 'Admin',
            'rolename': 'superadmin',
            'capabilities': ADMIN_CAPABILITIES,
        }
        flash(message, category)
        return render_template('basic.html')


def test_fmadmin_feedback_modal_uses_lottie_success_and_shows_error_reason():
    success_html = _render_fmadmin_feedback('success', 'User saved successfully')
    error_html = _render_fmadmin_feedback('danger', 'Password must contain at least 6 characters')

    assert 'id="fmadmin-feedback-modal"' in success_html
    assert 'data-feedback-kind="success"' in success_html
    assert 'User saved successfully' in success_html
    assert '@lottiefiles/dotlottie-web/+esm' in success_html
    assert 'assets10.lottiefiles.com/packages/lf20_jbrw3hcz.json' in success_html
    assert 'window.showFmadminFeedback = function' in success_html
    assert 'alert alert-success' not in success_html

    assert 'data-feedback-kind="danger"' in error_html
    assert 'admin_feedback_error_reason' in error_html
    assert 'Password must contain at least 6 characters' in error_html


def test_fmadmin_feedback_texts_exist_in_uzbek_russian_and_english():
    from fmadmin.modules.translate import STATIC_TRANSLATIONS

    expected_titles = {
        'uz': 'Muvaffaqiyatli saqlandi',
        'ru': 'Успешно сохранено',
        'en': 'Saved successfully',
    }
    for language, success_title in expected_titles.items():
        texts = STATIC_TRANSLATIONS[language]
        assert texts['admin_feedback_success_title'] == success_title
        assert texts['admin_feedback_error_reason']
        assert texts['admin_feedback_saving_title']


def test_submission_save_feedback_reports_the_localized_new_status():
    app = Flask(__name__)
    app.secret_key = 'test'

    with app.test_request_context('/'):
        session['language'] = 'en'
        feedback = fmadmin_web._submission_save_feedback('published', status_changed=True)
        assert feedback == {
            'category': 'success',
            'title': 'Submission saved',
            'message': 'Submission saved. New status: Published.',
            'status_label': 'Published',
            'status_changed': True,
        }

        session['language'] = 'ru'
        unchanged_feedback = fmadmin_web._submission_save_feedback('under_review', status_changed=False)
        assert unchanged_feedback['title'] == 'Статья сохранена'
        assert unchanged_feedback['status_label'] == 'На рецензировании'
        assert 'Текущий статус' in unchanged_feedback['message']


def test_submission_detail_uses_the_shared_centered_feedback_for_ajax_saves():
    app = _fmadmin_template_app()
    app.jinja_env.get_template('submissions/detail.html')

    template_path = os.path.join(
        os.path.dirname(__file__), '..', 'fmadmin', 'templates', 'submissions', 'detail.html'
    )
    with open(template_path, encoding='utf-8') as template_file:
        template = template_file.read()

    assert 'window.showFmadminFeedback' in template
    assert 'data.feedback' in template
    assert 'onHidden: function () { window.location.reload(); }' in template
    assert "alert(\"{{ t('admin_js_error_saving') }}" not in template


# Stands in for a superadmin: every sidebar group must render for them.
# The per-role split itself lives in tests/test_role_permissions.py.
ADMIN_CAPABILITIES = {
    'can_manage_users': True,
    'can_manage_submissions': True,
    'can_view_assignments': True,
    'can_manage_content': True,
    'can_delete_content': True,
    'can_manage_editors': True,
    'can_manage_site': True,
    'can_manage_finance': True,
    'can_manage_payments': True,
    'can_access_admin_dashboard': True,
}
EDITOR_CAPABILITIES = {
    'can_access_fmadmin': True,
    'can_access_editor_dashboard': True,
    'can_view_assignments': True,
    'can_review_assignments': True,
    'can_view_notifications': True,
}


def _render_sidebar(path, capabilities=None):
    app = _fmadmin_template_app()
    with app.test_request_context(path):
        session['fmadmin_user'] = {
            'id': 1,
            'name': 'Admin',
            'rolename': 'superadmin',
            'capabilities': dict(ADMIN_CAPABILITIES if capabilities is None else capabilities),
        }
        session['language'] = 'uz'
        return render_template('basic.html')


def test_sidebar_opens_the_group_of_the_current_page():
    # request.endpoint always carries the blueprint prefix ('fmadmin_web.x'),
    # while the sidebar's active_endpoints lists hold bare endpoint names.
    # Comparing them unstripped left every collapsible group closed, so the
    # admin landed on a page with no idea where in the menu they were.
    html = _render_sidebar('/fmadmin/submissions')

    assert 'class="collapse show" id="sidebar-group-submissions"' in html
    # The other groups still render, just collapsed.
    assert 'id="sidebar-group-finance"' in html
    assert 'class="collapse show" id="sidebar-group-finance"' not in html


def test_dashboard_status_labels_cover_every_status_in_three_languages():
    # The donut chart used to label statuses from a hardcoded Uzbek map in the
    # template that still listed pre-consolidation keys, so newer statuses
    # (failed_technical_check, payment_pending, in_layout, ...) rendered as
    # raw codes. Labels now come from shared/submission_status.py -- which
    # therefore has to stay complete in all three languages.
    from fmadmin.services import stats as fmadmin_stats
    from shared.submission_status import SUBMISSION_STATUSES, SUBMISSION_STATUS_LABELS

    for status in SUBMISSION_STATUSES:
        labels = SUBMISSION_STATUS_LABELS.get(status)
        assert labels, f'{status} has no labels at all'
        for lang in ('uz', 'ru', 'en'):
            assert labels.get(lang), f'{status} is missing the {lang} label'
            # No label may fall through to the raw status key.
            assert fmadmin_stats._status_label(status, lang) != status


def test_dashboard_status_colours_match_the_terminal_status_meaning():
    from shared.submission_status import SUBMISSION_STATUSES, SUBMISSION_STATUS_CHART_COLOR

    assert set(SUBMISSION_STATUS_CHART_COLOR) == set(SUBMISSION_STATUSES)
    assert SUBMISSION_STATUS_CHART_COLOR['published'] == '#22C55E'
    assert SUBMISSION_STATUS_CHART_COLOR['rejected'] == '#EF4444'


def test_dashboard_status_label_falls_back_instead_of_showing_the_code():
    from fmadmin.services import stats as fmadmin_stats

    assert fmadmin_stats._status_label('published', 'ru') == 'Опубликовано'
    # Unknown language falls back to Uzbek rather than to the bare code.
    assert fmadmin_stats._status_label('published', 'de') == 'Nashr etildi'
    # A legacy/unknown code still has to render something.
    assert fmadmin_stats._status_label('legacy_code', 'en') == 'legacy_code'


def test_dashboard_status_cards_link_to_the_matching_submission_filter():
    app = _fmadmin_template_app()
    with app.test_request_context('/fmadmin/'):
        session['fmadmin_user'] = {
            'id': 1,
            'name': 'Admin',
            'rolename': 'superadmin',
            'capabilities': ADMIN_CAPABILITIES,
        }
        html = render_template(
            'index.html',
            stats={
                'generated_at': 0,
                'stalled_submissions': 0,
                'total_articles': 0,
                'active_submissions': 0,
                'published_submissions': 0,
                'rejected_submissions': 0,
                'acceptance_rate': 0,
                'avg_decision_days': 0,
                'total_views': 0,
                'total_users': 0,
                'new_articles_30d': 0,
                'new_submissions_30d': 0,
            },
            status_chart={'codes': [], 'labels': [], 'data': [], 'colors': [], 'total': 0},
            timeline_chart={'labels': [], 'submissions': [], 'published': []},
            workflow_cards=[{
                'key': 'under_review',
                'label': 'Taqrizda',
                'count': 3,
                'tone': 'orange',
            }],
            attention_submissions=[],
            recent_submissions=[],
            top_articles=[],
            can_run_assignment_automation=False,
        )

    assert 'href="/fmadmin/submissions?status=under_review"' in html
    assert 'class="stage-card-link"' in html


def test_saving_keeps_a_submission_that_already_left_draft():
    # Production regression: the submit button saves first and submits second,
    # and saving forced status='draft'. The submit step then re-read 'draft',
    # decided this was not a revision at all, and the whole revision loop was
    # skipped -- the round stayed "Kutilmoqda" in the author's history,
    # revision_number never advanced, and the article re-entered at 'pending'
    # instead of returning to the editor who asked for the fix.
    assert api_routes._status_to_persist_on_save({'status': 'revision_required'}) == 'revision_required'
    assert api_routes._status_to_persist_on_save({'status': 'under_review'}) == 'under_review'
    assert api_routes._status_to_persist_on_save({'status': 'published'}) == 'published'


def test_saving_a_real_draft_still_saves_as_draft():
    assert api_routes._status_to_persist_on_save({'status': 'draft'}) == 'draft'
    assert api_routes._status_to_persist_on_save({'status': ''}) == 'draft'
    assert api_routes._status_to_persist_on_save({}) == 'draft'
    # A brand new submission has no row at all yet.
    assert api_routes._status_to_persist_on_save(None) == 'draft'


def test_revision_reentry_still_reads_revision_required_after_a_save():
    # The pair that broke together: save preserves the status, so submit can
    # still recognise the revision and automatically open fresh R2 tasks for
    # the prior reviewer panel. Only an explicit material-change flag sends
    # the corrected text through anti-plagiarism again first.
    assert api_routes._compute_revision_reentry({'status': 'revision_required'}) == ('under_review', True)
    assert api_routes._compute_revision_reentry({
        'status': 'revision_required',
        'revision_requires_antiplagiarism_recheck': True,
    }) == ('plagiarism_check', False)
    # 'draft' is what the bug fed in -- it is not resubmittable at all, which
    # is exactly why the revision branch never ran.
    from shared.submission_status import is_resubmittable
    assert is_resubmittable('draft') is False
    assert is_resubmittable('revision_required') is True


def test_rereview_candidates_are_latest_completed_round_only_and_keep_one_row_per_editor():
    submission = {'revision_number': 3}
    assignments = [
        {'id': 1, 'editor_id': 10, 'revision_round': 1, 'status': 'reviewed', 'assigned_at': 100},
        {'id': 2, 'editor_id': 10, 'revision_round': 2, 'status': 'reviewed', 'assigned_at': 200},
        {'id': 3, 'editor_id': 11, 'revision_round': 2, 'status': 'rejected', 'assigned_at': 210},
        {'id': 4, 'editor_id': 12, 'revision_round': 2, 'status': 'pending', 'assigned_at': 220},
    ]

    candidates = fmadmin_web._revision_rereview_candidates(submission, assignments)

    assert [item['id'] for item in candidates] == [3, 2]


def test_rereview_candidates_fall_back_to_last_completed_panel_after_antiplagiarism_failure():
    # Revision #2 did not reach reviewers because anti-plagiarism failed.
    # When the author fixes that failure and submits version #3, the R1 panel
    # still needs a new task; an empty R2 must not break the review loop.
    submission = {'revision_number': 3}
    assignments = [
        {'id': 21, 'editor_id': 10, 'revision_round': 1, 'status': 'reviewed', 'assigned_at': 100},
        {'id': 22, 'editor_id': 11, 'revision_round': 1, 'status': 'rejected', 'assigned_at': 101},
    ]

    candidates = fmadmin_web._revision_rereview_candidates(submission, assignments)

    assert [item['id'] for item in candidates] == [22, 21]


def test_author_revision_instruction_never_contains_internal_reviewer_feedback():
    legacy_combined_instruction = (
        "Admin izohi:\nFaqat adabiyotlar ro'yxatini tuzating."
        "\n\nMuharrirlar izohi:\nTaqriz #1: <p>Ichki tahrir izohi</p>"
    )

    assert dashboard_routes._author_visible_revision_instruction(legacy_combined_instruction) == (
        "Faqat adabiyotlar ro'yxatini tuzating."
    )


def test_review_comment_display_decodes_rich_text_without_changing_stored_value():
    assert fmadmin_web._plain_review_comment('<p>bo&#39;ldi</p><p>Ikkinchi qator</p>') == (
        "bo'ldi\nIkkinchi qator"
    )
    assert fmadmin_web._localized_assignment_note(
        'Revision #4: corrected manuscript re-review', 4, lang='uz'
    ) == "Tuzatilgan maqolani qayta ko'rib chiqish"
    assert fmadmin_web._localized_revision_round_label(4, lang='uz') == 'Taqriz #4'
    assert fmadmin_web._localized_revision_round_label(4, lang='ru') == 'Рецензия #4'
    assert fmadmin_web._localized_revision_round_label(4, lang='en') == 'Review #4'


def _submit_errors(**overrides):
    payload = {'file_authors': 'author.pdf', 'file_anonymized': 'blind.pdf'}
    payload.update(overrides)
    return api_routes._validate_submission_for_submit(payload)


def test_submit_requires_both_manuscript_files():
    # Neither file was checked on submit, so an article could land in the
    # admin queue with no manuscript at all -- and with no anonymized copy it
    # could never be assigned to an editor either (see _can_assign_editors),
    # leaving it stuck with no way forward.
    assert 'files' in _submit_errors(file_authors='')
    assert 'files' in _submit_errors(file_anonymized='')
    assert 'files' in _submit_errors(file_authors=None, file_anonymized=None)
    assert 'files' in _submit_errors(file_authors='   ')


def test_submit_accepts_a_submission_that_has_both_files():
    assert 'files' not in _submit_errors()


def test_draft_saving_still_works_without_files():
    # Drafts are work in progress -- forcing the files there would block the
    # author from saving anything before the manuscript is ready.
    assert 'files' not in api_routes._validate_submission_for_draft({'title': 'Ish jarayonida'})


class _FakeRoundsQuery:
    def __init__(self, rows, filters):
        self._rows = rows
        self._filters = filters

    def equal(self, **kwargs):
        merged = dict(self._filters)
        merged.update(kwargs)
        return _FakeRoundsQuery(self._rows, merged)

    def update(self, **kwargs):
        for row in self._matched():
            row.update(kwargs)
        return self

    def _matched(self):
        return [
            row for row in self._rows
            if all(row.get(key) == value for key, value in self._filters.items())
        ]

    def exec(self):
        return self._matched()


class _FakeRoundsTable:
    def __init__(self, rows):
        self.rows = [dict(row) for row in rows]

    def all(self):
        return _FakeRoundsQuery(self.rows, {})


def _rounds_db(rows):
    return type('FakeDB', (), {'submission_revision_rounds': _FakeRoundsTable(rows)})()


def test_open_revision_rounds_close_when_the_submission_leaves_revision(monkeypatch):
    # Production regression: only the author's resubmit endpoint ever set
    # resolved_at, so an admin moving the submission on by hand (the normal
    # move once the fix arrives over chat) left the round "pending" in the
    # author's history forever -- still showing next to a submission that had
    # already reached payment_pending.
    fake_db = _rounds_db([
        {'id': 1, 'submission_id': 44, 'round_number': 1, 'resolved_at': None},
        {'id': 2, 'submission_id': 44, 'round_number': 2, 'resolved_at': None},
        {'id': 3, 'submission_id': 99, 'round_number': 1, 'resolved_at': None},
    ])
    monkeypatch.setattr(fmadmin_web, 'db', fake_db)

    closed = fmadmin_web._resolve_open_revision_rounds(44, resolved_at=1785492723)

    assert closed == 2
    by_id = {row['id']: row for row in fake_db.submission_revision_rounds.rows}
    assert by_id[1]['resolved_at'] == 1785492723
    assert by_id[2]['resolved_at'] == 1785492723
    # Another submission's round must not be touched.
    assert by_id[3]['resolved_at'] is None


def test_resolving_revision_rounds_leaves_already_closed_ones_alone(monkeypatch):
    fake_db = _rounds_db([
        {'id': 1, 'submission_id': 44, 'round_number': 1, 'resolved_at': 1700000000},
    ])
    monkeypatch.setattr(fmadmin_web, 'db', fake_db)

    assert fmadmin_web._resolve_open_revision_rounds(44, resolved_at=1785492723) == 0
    assert fake_db.submission_revision_rounds.rows[0]['resolved_at'] == 1700000000


def _step_states(status):
    steps = fmadmin_web._submission_workflow_steps({'status': status})
    return {step['key']: step['state'] for step in steps}


def test_workflow_steps_mark_everything_before_the_current_status_done():
    states = _step_states('under_review')

    assert states['pending'] == 'done'
    assert states['passed_technical_check'] == 'done'
    assert states['plagiarism_check'] == 'done'
    assert states['under_review'] == 'current'
    assert states['recommended'] == 'todo'
    assert states['published'] == 'todo'


def test_workflow_steps_flag_a_failed_check_instead_of_showing_progress():
    # A failed technical check still *reached* the technical-check milestone --
    # dropping it off the strip would make the page look like nothing happened.
    states = _step_states('failed_technical_check')

    assert states['pending'] == 'done'
    assert states['passed_technical_check'] == 'halted'
    assert states['plagiarism_check'] == 'todo'

    # The connector line must not turn green past a halted step.
    steps = fmadmin_web._submission_workflow_steps({'status': 'failed_technical_check'})
    assert all(step['line_done'] is False for step in steps)


def test_workflow_steps_keep_revision_required_on_the_review_milestone():
    # `revision_required` is a loop back into review, not a stage of its own.
    assert _step_states('revision_required')['under_review'] == 'current'


def test_workflow_steps_claim_nothing_for_rejected_submissions():
    # Rejection can happen at any point, so no milestone may be claimed as
    # reached -- the status badge in the header carries that news instead.
    assert set(_step_states('rejected').values()) == {'todo'}
    assert set(_step_states('').values()) == {'todo'}


def test_workflow_steps_cover_every_submission_status_or_leave_it_stageless():
    # Guard against a new status silently disappearing from the strip: every
    # status must either own a milestone or be a deliberate dead end.
    from shared.submission_status import SUBMISSION_STATUSES

    owned = set()
    for _key, statuses in fmadmin_web.SUBMISSION_WORKFLOW_MILESTONES:
        owned.update(statuses)

    unmapped = set(SUBMISSION_STATUSES) - owned
    assert unmapped == {'rejected'}


def test_sidebar_links_are_highlighted_on_their_own_page():
    html = _render_sidebar('/fmadmin/submissions')
    assert 'aria-current="page"' in html

    # The dashboard belongs to no group -- nothing should be expanded there.
    home_html = _render_sidebar('/fmadmin/')
    assert 'aria-current="page"' in home_html
    assert 'class="collapse show"' not in home_html


def _render_submissions_list(path, **overrides):
    context = {
        'submissions_list': [],
        'page': 1,
        'total_submissions': 0,
        'total_pages': 1,
        'pagination_query_string': '',
        'submission_id_filter': None,
        'status_filter': '',
        'user_id_filter': '',
        'title_filter': '',
        'track_filter': '',
        'assigned_admin_filter': None,
        'editor_id_filter': None,
        'author_filter': '',
        'created_from': '',
        'created_to': '',
        'users_map': {},
        'authors_map': {},
        'admin_options': [],
        'admin_track_choices': [],
        'editor_options': [],
        'current_user': {'id': 1},
        'workflow_stage_choices': [
            ('pending', 'Kutilmoqda'),
            ('under_review', 'Taqrizda'),
            ('published', 'Nashr etilgan'),
        ],
        'workflow_stage_labels': {},
        'status_counts': {},
        'status_counts_total': 0,
    }
    context.update(overrides)

    app = _fmadmin_template_app()
    with app.test_request_context(path):
        session['fmadmin_user'] = {'id': 1, 'name': 'Admin', 'rolename': 'superadmin', 'capabilities': {}}
        return render_template('submissions/list.html', **context)


def _status_pills(html):
    """(href, label, count) for each rendered status pill.

    Scoped on purpose: the same status labels also appear in the bulk-action
    select and the edit modal, so a plain substring check proves nothing.
    """
    pattern = (
        r'<a href="([^"]+)" class="btn btn-sm fm-status-pill[^"]*">\s*'
        r'(.*?)\s*<span class="fm-pill-count">(\d+)</span>'
    )
    return [
        (href, label.strip(), int(count))
        for href, label, count in re.findall(pattern, html, re.S)
    ]


def test_status_pills_only_show_statuses_that_actually_occur():
    # All twelve statuses at once was the crowding this list is meant to fix;
    # an empty status is noise the admin can never click into usefully.
    pills = _status_pills(_render_submissions_list(
        '/fmadmin/submissions',
        status_counts={'pending': 3},
        status_counts_total=3,
    ))

    labels = [label for _href, label, _count in pills]
    assert labels == ['admin_option_all_statuses', 'Kutilmoqda']
    assert pills[1][2] == 3


def test_status_pills_keep_the_selected_status_even_at_zero():
    # Otherwise picking a status whose only row was just moved away makes the
    # active pill vanish and the admin cannot see what is filtering the list.
    pills = _status_pills(_render_submissions_list(
        '/fmadmin/submissions?status=published',
        status_filter='published',
        status_counts={'pending': 3},
        status_counts_total=3,
    ))

    assert ('Nashr etilgan', 0) in [(label, count) for _href, label, count in pills]


def test_status_pills_carry_the_other_filters_over():
    pills = _status_pills(_render_submissions_list(
        '/fmadmin/submissions?author=Aliyev&page=2',
        author_filter='Aliyev',
        status_counts={'pending': 1},
        status_counts_total=1,
    ))

    hrefs = [href for href, _label, _count in pills]
    assert 'status=pending&amp;author=Aliyev' in hrefs[1]
    # Paging must reset when the status changes -- page 2 of the old filter
    # is meaningless for the new one.
    assert all('page=' not in href for href in hrefs)


def _promoted_editor(user_id=85):
    """Author account later granted the editor role in fmadmin.

    The promotion only appended 'editor' to roles, so the stored primary role
    stayed 'user' -- exactly the shape that broke review acceptance.
    """
    return {'id': user_id, 'rolename': 'user', 'roles': ['user', 'editor']}


def test_promoted_editor_counts_as_the_assigned_editor():
    # Production regression: opening the task left accepted_at NULL, the
    # review form never appeared, and the assignment expired unaccepted.
    user = _promoted_editor()

    assert fmadmin_web._role_of(user) == 'user'
    assert fmadmin_web._is_assigned_editor(user, {'editor_id': 85}) is True


def test_assigned_editor_check_rejects_other_peoples_assignments():
    user = _promoted_editor()

    assert fmadmin_web._is_assigned_editor(user, {'editor_id': 86}) is False
    assert fmadmin_web._is_assigned_editor(user, {}) is False
    assert fmadmin_web._is_assigned_editor(user, None) is False
    # An account without the editor role never reviews, even its own row.
    assert fmadmin_web._is_assigned_editor(
        {'id': 85, 'rolename': 'user', 'roles': ['user']}, {'editor_id': 85}
    ) is False


def test_assigned_editor_check_accepts_a_plain_editor_account():
    editor = {'id': 7, 'rolename': 'editor', 'roles': ['editor']}

    assert fmadmin_web._is_assigned_editor(editor, {'editor_id': 7}) is True
    assert fmadmin_web._is_assigned_editor(editor, {'editor_id': 8}) is False


def test_admin_role_check_covers_both_admin_levels():
    assert fmadmin_web._is_admin_role('admin') is True
    assert fmadmin_web._is_admin_role('superadmin') is True
    # Editors and promoted authors must stay scoped to their own assignments.
    assert fmadmin_web._is_admin_role('editor') is False
    assert fmadmin_web._is_admin_role('user') is False


def test_global_search_is_hidden_from_users_who_cannot_use_it():
    # /fmadmin/api/search spans the whole journal (every submission with its
    # status, every user, every author) and requires fmadmin.users.manage.
    # Rendering the trigger for an editor only produced an "access denied"
    # popup -- and advertised data they are not allowed to reach.
    editor_view = _render_sidebar('/fmadmin/editor/dashboard', capabilities=EDITOR_CAPABILITIES)

    assert 'id="global-search-trigger"' not in editor_view
    assert 'id="globalSearchModal"' not in editor_view

    admin_view = _render_sidebar('/fmadmin/submissions')
    assert 'id="global-search-trigger"' in admin_view
    assert 'id="globalSearchModal"' in admin_view


def test_sidebar_home_link_follows_the_dashboard_permission():
    # Not the stored rolename: a promoted author (rolename='user') carries the
    # editor permissions but used to get a Home link into the admin overview
    # of every submission in the journal.
    editor_view = _render_sidebar('/fmadmin/editor/dashboard', capabilities=EDITOR_CAPABILITIES)

    assert '/fmadmin/editor/dashboard' in editor_view
    assert 'href="/fmadmin/"' not in editor_view


def _render_editor_assignments(is_admin_viewer, capabilities=None):
    assignment = {
        'id': 5,
        'submission_id': 21,
        'editor_id': 1,
        'assigned_by': 2,
        'status': 'reviewed',
        'admin_decision': 'revision_requested',
        'assigned_at': 1785000000,
        'reviewed_at': 1785200000,
        'acceptance_deadline_at': 1785100000,
        'completion_deadline_at': 1785500000,
        'acceptance_remaining_seconds': None,
        'acceptance_remaining_label': '',
        'completion_remaining_seconds': None,
        'completion_remaining_label': '',
    }
    context = {
        'assignments': [assignment],
        'page': 1,
        'total_assignments': 1,
        'total_pages': 1,
        'status_filter': '',
        'editor_filter': '',
        'submission_id_filter': '',
        'submission_title_filter': '',
        'submissions_map': {21: {'id': 21, 'title': 'Test article'}},
        'editors_map': {1: {'id': 1, 'name': 'Editor', 'second_name': ''}},
        'users_map': {2: {'id': 2, 'name': 'Admin', 'second_name': ''}},
        'editors': [{'id': 1, 'name': 'Editor', 'second_name': ''}],
        'current_user': {'id': 1, 'rolename': 'editor'},
        'is_admin_viewer': is_admin_viewer,
    }

    app = _fmadmin_template_app()
    with app.test_request_context('/fmadmin/editor-assignments'):
        session['fmadmin_user'] = {
            'id': 1,
            'name': 'Editor',
            'rolename': 'editor',
            'capabilities': dict(
                (ADMIN_CAPABILITIES if is_admin_viewer else EDITOR_CAPABILITIES)
                if capabilities is None else capabilities
            ),
        }
        session['language'] = 'uz'
        return render_template('editors/assignments.html', **context)


def test_assignments_list_hides_administration_columns_from_editors():
    # The admin decision is the administration's verdict on the review, and
    # the editor/assigned-by columns describe staffing -- none of it is the
    # editor's own task data.  "Admin qarori" had no permission gate at all.
    html = _render_editor_assignments(is_admin_viewer=False)

    assert 'Admin qarori' not in html
    assert 'Qayta ishlash so\'ralgan' not in html
    assert 'admin_label_editor' not in html
    assert 'admin_option_all_editors' not in html
    # Their own task data stays.
    assert 'Test article' in html
    assert 'admin_col_reviewed_at' in html


def test_assignments_list_keeps_administration_columns_for_admins():
    html = _render_editor_assignments(is_admin_viewer=True)

    assert 'Admin qarori' in html
    assert 'Qayta ishlash so\'ralgan' in html
    assert 'admin_label_editor' in html
    assert 'admin_option_all_editors' in html
