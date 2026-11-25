import os

import pytest
from flask import Flask, session

from fmadmin.routes import messages as fmadmin_messages
from fmadmin.routes import web as fmadmin_web
from mainweb.routes import api as mainweb_api
from mainweb.routes import auth as mainweb_auth
from mainweb.routes import public as mainweb_public


class _EmptyTable:
    def all(self):
        return self

    def exec(self):
        return []


class _FakeMutableQuery:
    def __init__(self, rows, filters):
        self._rows = rows
        self._filters = filters
        self._update_payload = None

    def update(self, **kwargs):
        self._update_payload = dict(kwargs)
        return self

    def exec(self):
        matched = [
            row for row in self._rows
            if all(row.get(key) == value for key, value in self._filters.items())
        ]
        if self._update_payload is not None:
            for row in matched:
                row.update(self._update_payload)
        return [dict(row) for row in matched]


class _FakeMutableTable:
    def __init__(self, rows):
        self._rows = [dict(row) for row in rows]

    def get(self, **kwargs):
        return _FakeMutableQuery(self._rows, kwargs)

    @property
    def rows(self):
        return self._rows


def test_mainweb_login_rate_limit_key_uses_remote_addr():
    app = Flask(__name__)
    app.secret_key = 'test'

    with app.test_request_context(
        '/login',
        headers={'X-Forwarded-For': '198.51.100.77'},
        environ_base={'REMOTE_ADDR': '10.10.10.10'},
    ):
        rate_key = mainweb_auth._login_rate_limit_key('User@Example.com')

    assert rate_key == '10.10.10.10::user@example.com'


def test_fmadmin_login_rate_limit_key_uses_remote_addr():
    app = Flask(__name__)
    app.secret_key = 'test'

    with app.test_request_context(
        '/fmadmin/login',
        headers={'X-Forwarded-For': '198.51.100.88'},
        environ_base={'REMOTE_ADDR': '10.20.30.40'},
    ):
        rate_key = fmadmin_web._login_rate_limit_key('Admin@Example.com')

    assert rate_key == '10.20.30.40::admin@example.com'


def test_google_auth_start_clears_stale_next_url(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'test'

    monkeypatch.setattr(mainweb_auth, '_is_google_auth_available', lambda: True)
    monkeypatch.setattr(mainweb_auth, '_build_google_auth_url', lambda _intent: '/oauth/google')

    with app.test_request_context('/auth/google?intent=login'):
        session['google_oauth_next_url'] = '/stale'
        response = mainweb_auth.app__google_auth_start()

        assert session.get('google_oauth_next_url') is None
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/oauth/google')


def test_orcid_auth_start_replaces_stale_next_url(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'test'

    monkeypatch.setattr(mainweb_auth, '_is_orcid_auth_available', lambda: True)
    monkeypatch.setattr(mainweb_auth, '_build_orcid_auth_url', lambda _intent: '/oauth/orcid')

    with app.test_request_context('/auth/orcid?intent=register&next=/dashboard'):
        session['orcid_oauth_next_url'] = '/stale'
        response = mainweb_auth.app__orcid_auth_start()

        assert session.get('orcid_oauth_next_url') == '/dashboard'
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/oauth/orcid')


def test_google_auth_availability_rejects_placeholder_secret(monkeypatch):
    monkeypatch.setattr(mainweb_auth.settings, 'GOOGLE_AUTH_ENABLED', '1')
    monkeypatch.setattr(mainweb_auth.settings, 'GOOGLE_CLIENT_ID', 'real-client-id.apps.googleusercontent.com')
    monkeypatch.setattr(mainweb_auth.settings, 'GOOGLE_CLIENT_SECRET', 'ROTATE_IN_GOOGLE_CONSOLE_AND_UPDATE')

    assert mainweb_auth._is_google_auth_available() is False
    assert 'GOOGLE_CLIENT_SECRET placeholder' in mainweb_auth._google_auth_config_issues()


def test_orcid_auth_availability_rejects_placeholder_secret(monkeypatch):
    monkeypatch.setattr(mainweb_auth.settings, 'ORCID_AUTH_ENABLED', '1')
    monkeypatch.setattr(mainweb_auth.settings, 'ORCID_CLIENT_ID', 'APP-REALCLIENT123')
    monkeypatch.setattr(mainweb_auth.settings, 'ORCID_CLIENT_SECRET', 'rotate_in_orcid_console_and_update')

    assert mainweb_auth._is_orcid_auth_available() is False
    assert 'ORCID_CLIENT_SECRET placeholder' in mainweb_auth._orcid_auth_config_issues()


def test_normalized_social_email_drops_orcid_local_alias():
    assert mainweb_auth._normalized_social_email('person@example.com') == 'person@example.com'
    assert mainweb_auth._normalized_social_email('ORCID-1234@orcid.local') == ''


def test_public_upload_resolver_confines_to_static_uploads(monkeypatch):
    monkeypatch.setattr(mainweb_public.settings, 'SAVE_PATH', '/srv/journal')

    safe_path = mainweb_public._resolve_public_upload_abspath('/static/uploads/articles/2026/04/file.pdf')

    assert safe_path == os.path.abspath('/srv/journal/static/uploads/articles/2026/04/file.pdf')
    assert mainweb_public._resolve_public_upload_abspath('/static/uploads/../../etc/passwd') is None
    assert mainweb_public._resolve_public_upload_abspath('/etc/passwd') is None


def test_mainweb_logout_route_is_post_only():
    app = Flask(__name__)
    app.secret_key = 'test'

    mainweb_auth.register(app)
    rule = next(item for item in app.url_map.iter_rules() if item.rule == '/logout')

    assert 'POST' in rule.methods
    assert 'GET' not in rule.methods


def test_fmadmin_logout_route_is_post_only():
    app = Flask(__name__)
    app.secret_key = 'test'

    app.register_blueprint(fmadmin_web.bp)
    rule = next(item for item in app.url_map.iter_rules() if item.rule == '/fmadmin/logout')

    assert 'POST' in rule.methods
    assert 'GET' not in rule.methods


def test_register_view_exposes_orcid_flag(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'test'

    fake_dbc = type('FakeDBC', (), {'fix_country': _EmptyTable()})()
    monkeypatch.setattr(mainweb_auth, 'dbc', fake_dbc)
    monkeypatch.setattr(mainweb_auth, 'translate', lambda item: item)
    monkeypatch.setattr(mainweb_auth, '_is_google_auth_available', lambda: False)
    monkeypatch.setattr(mainweb_auth, '_is_orcid_auth_available', lambda: True)
    monkeypatch.setattr(mainweb_auth, 'render_template', lambda _template, **context: context)

    with app.test_request_context('/register'):
        response_context = mainweb_auth.app__register()

    assert response_context['google_auth_enabled'] is False
    assert response_context['orcid_auth_enabled'] is True


def test_runtime_schema_sync_helpers_skip_when_disabled(monkeypatch):
    auth_calls = []
    api_calls = []
    admin_calls = []

    monkeypatch.setattr(mainweb_auth.settings, 'RUNTIME_SCHEMA_SYNC_ENABLED', False)
    monkeypatch.setattr(mainweb_api.settings, 'RUNTIME_SCHEMA_SYNC_ENABLED', False)
    monkeypatch.setattr(fmadmin_web.settings, 'RUNTIME_SCHEMA_SYNC_ENABLED', False)

    monkeypatch.setattr(mainweb_auth, '_ensure_user_oauth_columns', lambda: auth_calls.append('auth'))
    monkeypatch.setattr(mainweb_api, '_ensure_submission_columns', lambda: api_calls.append('api'))
    monkeypatch.setattr(fmadmin_web, '_ensure_submission_columns', lambda: admin_calls.append('admin'))

    mainweb_auth.run_runtime_schema_syncs()
    mainweb_api.run_runtime_schema_syncs()
    fmadmin_web.run_runtime_schema_syncs()

    assert auth_calls == []
    assert api_calls == []
    assert admin_calls == []


def test_orcid_login_allows_existing_user_linked_via_author_profile(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'test'

    users_table = _FakeMutableTable([
        {
            'id': 10,
            'email': 'google-user@example.com',
            'name': 'Google',
            'second_name': 'User',
            'country_id': None,
            'roles': ['author'],
            'is_blocked': False,
            'is_hidden': False,
            'oauth_provider': 'google',
            'oauth_sub': 'google-sub-123',
            'oauth_email_verified': True,
            'oauth_last_login_at': None,
            'last_online': None,
        }
    ])

    fake_dbc = type('FakeDBC', (), {
        'users': users_table,
        'columns': {
            'users': [
                'id', 'email', 'name', 'second_name', 'country_id', 'roles',
                'is_blocked', 'is_hidden', 'oauth_provider', 'oauth_sub',
                'oauth_email_verified', 'oauth_last_login_at', 'last_online',
            ],
            'author_profile': ['id', 'user_id', 'orcid', 'email'],
        },
        'fix_country': _EmptyTable(),
    })()

    monkeypatch.setattr(mainweb_auth, 'dbc', fake_dbc)
    monkeypatch.setattr(mainweb_auth, 'hydrate_user_roles', lambda user: {'roles': user.get('roles') or []})
    monkeypatch.setattr(mainweb_auth, '_sync_orcid_author_profile', lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        mainweb_auth,
        '_resolve_orcid_user',
        lambda _profile: (
            dict(users_table.rows[0]),
            '0000-0001-2345-6789',
            {'id': 5, 'user_id': 10, 'orcid': '0000-0001-2345-6789'},
            'orcid-user@example.org',
            'orcid-user@example.org',
        ),
    )

    profile = {
        'orcid': '0000-0001-2345-6789',
        'email': 'orcid-user@example.org',
        'name': 'ORCID User',
    }

    with app.test_request_context('/auth/orcid/callback'):
        result = mainweb_auth._create_or_update_orcid_user(profile, intent='login')

    assert result is not None
    assert result['id'] == 10
    assert result['oauth_provider'] == 'google'
    assert result['oauth_sub'] == 'google-sub-123'


def test_registration_create_data_sets_is_hidden_false(monkeypatch):
    """Regression: users.is_hidden is NOT NULL, but the connector inserts every
    column explicitly (unset -> NULL). The email/password registration payload
    must set is_hidden=False so the insert does not violate the constraint."""
    app = Flask(__name__)
    app.secret_key = 'test'

    fake_dbc = type('FakeDBC', (), {
        'columns': {
            'users': [
                'id', 'name', 'second_name', 'father_name', 'email', 'password',
                'country_id', 'rolename', 'is_blocked', 'is_hidden', 'is_notify',
                'ui_language', 'accept_rules_time', 'register_time', 'created_at',
                'last_online', 'oauth_provider', 'oauth_sub', 'oauth_email_verified',
                'oauth_last_login_at', 'roles',
            ],
        },
    })()

    monkeypatch.setattr(mainweb_auth, 'dbc', fake_dbc)

    payload = {
        'first_name': 'Karijon',
        'last_name': 'Abdurasulov',
        'father_name': "Sadir o'g'li",
        'email': 'karimov@example.com',
        'password_hash': 'scrypt:hash',
        'country_id': 267,
        'is_notify': True,
        'ui_language': 'uz',
    }

    with app.test_request_context('/register/verify'):
        create_data = mainweb_auth._build_user_create_data_from_registration(payload)

    assert create_data is not None
    assert create_data['is_hidden'] is False
    assert create_data['is_blocked'] is False


# --- submission chat thread isolation (blind peer review boundary) --------
#
# Stream A ('author_admin') and Stream B ('admin_editor') must never bleed
# into each other. This is a security boundary, not just a UI filter: an
# editor must never be able to read the author-facing thread, and one
# editor must never read another editor's internal thread with the admin.

_ASSIGNED_ADMIN_ID = 501
_SUBMISSION_ID = 42
_ASSIGNMENT_ID = 900
_ASSIGNED_EDITOR_ID = 700
_OTHER_EDITOR_ID = 701

_SUPERADMIN = {'id': 1, 'rolename': 'superadmin'}
_ASSIGNED_ADMIN = {'id': _ASSIGNED_ADMIN_ID, 'rolename': 'admin'}
_OTHER_ADMIN = {'id': 502, 'rolename': 'admin'}
_ASSIGNED_EDITOR = {'id': _ASSIGNED_EDITOR_ID, 'rolename': 'editor'}
_OTHER_EDITOR = {'id': _OTHER_EDITOR_ID, 'rolename': 'editor'}
_SUBMISSION = {'id': _SUBMISSION_ID, 'user_id': 999, 'assigned_admin_id': _ASSIGNED_ADMIN_ID}
_ASSIGNMENT = {'id': _ASSIGNMENT_ID, 'submission_id': _SUBMISSION_ID, 'editor_id': _ASSIGNED_EDITOR_ID}


def test_editor_cannot_view_author_admin_thread():
    assert fmadmin_messages._can_view_message_thread(_ASSIGNED_EDITOR, _SUBMISSION, 'author_admin') is False


def test_unassigned_admin_cannot_view_author_admin_thread():
    assert fmadmin_messages._can_view_message_thread(_OTHER_ADMIN, _SUBMISSION, 'author_admin') is False


def test_assigned_admin_can_view_author_admin_thread():
    assert fmadmin_messages._can_view_message_thread(_ASSIGNED_ADMIN, _SUBMISSION, 'author_admin') is True


def test_editor_cannot_view_another_editors_internal_thread():
    assert fmadmin_messages._can_view_message_thread(
        _OTHER_EDITOR, _SUBMISSION, 'admin_editor', assignment=_ASSIGNMENT
    ) is False


def test_assigned_editor_can_view_own_internal_thread():
    assert fmadmin_messages._can_view_message_thread(
        _ASSIGNED_EDITOR, _SUBMISSION, 'admin_editor', assignment=_ASSIGNMENT
    ) is True


def test_assigned_admin_can_view_internal_thread():
    assert fmadmin_messages._can_view_message_thread(
        _ASSIGNED_ADMIN, _SUBMISSION, 'admin_editor', assignment=_ASSIGNMENT
    ) is True


def test_superadmin_can_view_both_threads_unconditionally():
    assert fmadmin_messages._can_view_message_thread(_SUPERADMIN, _SUBMISSION, 'author_admin') is True
    assert fmadmin_messages._can_view_message_thread(
        _SUPERADMIN, _SUBMISSION, 'admin_editor', assignment=_ASSIGNMENT
    ) is True


def test_stream_b_notification_never_targets_the_author():
    # The submission dict carries a real user_id (999), but an editor's
    # message must ping the assigned admin -- never the author.
    target_user_id, target_role = fmadmin_messages._stream_b_notification_target(
        'editor', _SUBMISSION, _ASSIGNMENT
    )
    assert target_user_id == _ASSIGNED_ADMIN_ID
    assert target_role == 'admin'
    assert target_user_id != _SUBMISSION['user_id']


def test_stream_b_notification_admin_message_targets_the_editor():
    target_user_id, target_role = fmadmin_messages._stream_b_notification_target(
        'admin', _SUBMISSION, _ASSIGNMENT
    )
    assert target_user_id == _ASSIGNED_EDITOR_ID
    assert target_role == 'editor'
    assert target_user_id != _SUBMISSION['user_id']


# ---------------------------------------------------------------------------
# Security audit 2026-11-25 #1 -- workflow-integrity guard.
#
# The author-facing save/submit endpoints accept any submission_id the caller
# owns. Without a server-side status check, an author could POST to
# /api/article/save or /api/article/submit with a submission that has already
# left their hands (under review, published, rejected) and silently overwrite
# the manuscript or reset it to 'pending', bypassing the fixed workflow order.
# ---------------------------------------------------------------------------

from shared.submission_status import is_author_editable


def test_is_author_editable_allows_only_author_owned_states():
    for allowed in ('', 'draft', 'pending', 'failed_technical_check',
                    'revision_required', 'antiplagiarism_failed'):
        assert is_author_editable(allowed) is True, allowed
    for locked in ('passed_technical_check', 'plagiarism_check', 'under_review',
                   'recommended', 'payment_pending', 'in_layout',
                   'published', 'rejected'):
        assert is_author_editable(locked) is False, locked


def _invoke_author_write(monkeypatch, status, handler_name):
    app = Flask(__name__)
    app.secret_key = 'test'

    table = _FakeMutableTable([
        {'id': 7, 'user_id': 42, 'status': status, 'title': 'original'},
    ])

    class _Dbc:
        submissions = table

    monkeypatch.setattr(mainweb_api, 'dbc', _Dbc)
    # Keep the assertion independent of the translation backend / DB.
    monkeypatch.setattr(mainweb_api, 't', lambda key, *a, **k: key)

    handler = getattr(mainweb_api, handler_name)
    with app.test_request_context(
        '/api/article/save',
        method='POST',
        json={'submission_id': 7, 'title_en': 'tampered'},
    ):
        session['user_id'] = 42
        result = handler()

    response = result[0] if isinstance(result, tuple) else result
    status_code = result[1] if isinstance(result, tuple) else 200
    return response.get_json(), status_code, table


@pytest.mark.parametrize('handler_name',
                         ['app__api_article_submit', 'app__api_article_save'])
@pytest.mark.parametrize('locked_status', ['published', 'under_review', 'rejected',
                                           'plagiarism_check', 'in_layout'])
def test_author_cannot_write_to_a_submission_that_left_their_hands(
        monkeypatch, handler_name, locked_status):
    body, status_code, table = _invoke_author_write(
        monkeypatch, locked_status, handler_name)

    assert status_code == 409
    assert body['success'] is False
    assert body['message'] == 'submission_not_editable'
    # The stored row is untouched: no reset to 'pending', no overwritten title.
    assert table.rows[0]['status'] == locked_status
    assert table.rows[0]['title'] == 'original'


# ---------------------------------------------------------------------------
# Security audit 2026-11-25 #2 -- stored XSS via news/announcement bodies.
#
# News and announcement bodies render with |safe on the public site and share
# one origin with /fmadmin/, so unsanitized HTML from a content editor is a
# stored XSS that can reach an admin's session. The save handlers must run the
# bodies through the same sanitizer as CMS pages.
# ---------------------------------------------------------------------------

import fmadmin.utils.auth as fmadmin_auth


def _capture_news_add(monkeypatch, form):
    app = Flask(__name__)
    app.secret_key = 'test'
    fmadmin_web.register(app)

    monkeypatch.setattr(fmadmin_auth, 'user_has_permission', lambda *a, **k: True)

    captured = {}

    class _AddQuery:
        def __init__(self, kwargs):
            captured.update(kwargs)

        def exec(self):
            return [{'id': 1}]

    class _FakeNews:
        def add(self, **kwargs):
            return _AddQuery(kwargs)

    # The real connector intercepts attribute access (__getattr__ raises for
    # unknown tables), so replace the whole `db` handle rather than one table.
    class _FakeDb:
        news = _FakeNews()

    monkeypatch.setattr(fmadmin_web, 'db', _FakeDb())

    with app.test_request_context(
        '/fmadmin/website/news/edit/0', method='POST', data=form):
        session['fmadmin_user'] = {'id': 1, 'rolename': 'admin', 'capabilities': {}}
        fmadmin_web.news_edit(0)

    return captured


def test_news_edit_sanitizes_body_against_stored_xss(monkeypatch):
    captured = _capture_news_add(monkeypatch, {
        'title_en': 'Headline',
        'content_en': '<p>safe body</p><script>alert(document.cookie)</script>',
        'content_uz': '<img src=x onerror="steal()">',
        'content_ru': '<a href="javascript:evil()">x</a>',
        'status': 'draft',
    })

    assert '<script' not in captured['content']
    assert '<p>safe body</p>' in captured['content']
    assert 'onerror' not in captured['content_uz']
    assert 'javascript:' not in captured['content_ru']


def test_payment_guide_sanitizes_body_against_stored_xss(monkeypatch):
    # The payment-guide body renders with |safe on public and dashboard pages,
    # so the finance-settings save must sanitize it (audit 2026-11-25 #2).
    app = Flask(__name__)
    app.secret_key = 'test'
    fmadmin_web.register(app)

    monkeypatch.setattr(fmadmin_auth, 'user_has_permission', lambda *a, **k: True)

    stored = {}
    monkeypatch.setattr(fmadmin_web, '_set_site_setting',
                        lambda key, value: stored.__setitem__(key, value) or True)

    form = {
        'payment_guide_uz': '<p>To’lov</p><script>alert(1)</script>',
        'payment_guide_ru': '<img src=x onerror="evil()">',
        'payment_guide_en': '<a href="javascript:evil()">x</a>',
    }
    with app.test_request_context(
            '/fmadmin/website/payment-guide', method='POST', data=form):
        session['fmadmin_user'] = {'id': 1, 'rolename': 'admin', 'capabilities': {}}
        fmadmin_web.payment_guide_settings()

    assert '<script' not in stored['payment_guide_html_uz']
    assert '<p>' in stored['payment_guide_html_uz']
    assert 'onerror' not in stored['payment_guide_html_ru']
    assert 'javascript:' not in stored['payment_guide_html_en']
