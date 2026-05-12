import threading

from flask import Flask, session

from mainweb.routes import api as api_routes
from mainweb.routes import context as context_routes
from mainweb.routes import dashboard as dashboard_routes
from mainweb.routes import public as public_routes


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

    assert 'Editorial Policy Overview' in seed_payload['content']
    assert 'Double-Blind Peer Review' in seed_payload['content']
    assert 'Обзор редакционной политики' in seed_payload['content_ru']


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
