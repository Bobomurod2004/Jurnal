import os

from flask import Flask, session

from fmadmin.routes import web as fmadmin_web
from mainweb.routes import api as mainweb_api
from mainweb.routes import auth as mainweb_auth
from mainweb.routes import public as mainweb_public


class _EmptyTable:
    def all(self):
        return self

    def exec(self):
        return []


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
