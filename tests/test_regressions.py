import threading

from flask import Flask, session

from mainweb.routes import api as api_routes
from mainweb.routes import context as context_routes
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
