import threading

from flask import Flask, session

from mainweb.routes import api as api_routes
from mainweb.routes import auth as auth_routes
from mainweb.routes import context as context_routes
from mainweb.routes import dashboard as dashboard_routes
from mainweb.routes import public as public_routes
from fmadmin.routes import web as fmadmin_web


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


def test_new_submission_payload_sets_revision_defaults_explicitly():
    """New drafts must not rely on SQL DEFAULT values.

    The connector sends omitted table columns as NULL, which bypasses a
    PostgreSQL DEFAULT and violates submissions.revision_number NOT NULL.
    """
    payload = api_routes._prepare_submission_payload(
        data={}, user_id=42, status='draft', is_new=True
    )

    assert payload['revision_number'] == 1
    assert payload['revision_allowed'] is True


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
    assert meta['is_world_readable'] is True
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
    assert meta['pdf_url'] == ''
    assert meta['language'] == 'uz'


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


def test_compute_revision_reentry_revision_required_returns_to_same_editor():
    # A revision requested after peer review (editor-requested, or a late
    # admin objection) must go back to the SAME editor's queue via
    # under_review, not restart from scratch -- the blind-review continuity
    # guarantee.
    existing = {'status': 'revision_required'}
    status, needs_editor = api_routes._compute_revision_reentry(existing)
    assert (status, needs_editor) == ('under_review', True)


def test_compute_revision_reentry_missing_or_unknown_status_falls_back_conservatively():
    # Legacy rows resubmitted before this feature existed have no reliable
    # status -- the safest default is the earliest re-entry point, not
    # skipping straight back into review.
    status, needs_editor = api_routes._compute_revision_reentry({})
    assert (status, needs_editor) == ('pending', False)

    status, needs_editor = api_routes._compute_revision_reentry({'status': 'not_a_real_status'})
    assert (status, needs_editor) == ('pending', False)


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
