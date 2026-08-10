"""Regression tests for the production issues found in the server logs.

* the header's sign-in link generated an endless chain of crawlable URLs
  (/login?next=/login?next%3D/login?next%253D...), which also happens to be
  where an open redirect would live;
* the editorial board was re-read from the database on every homepage hit;
* health probes and metric scrapes drowned out real traffic in the logs.
"""
from flask import Flask

from mainweb.hooks import LOG_EXEMPT_PATHS as MAINWEB_LOG_EXEMPT_PATHS
from mainweb.routes import public as public_routes
from mainweb.utils.auth import sanitize_next_url


# --------------------------------------------------------------------------
# next= : crawl trap and open redirect
# --------------------------------------------------------------------------

def test_auth_paths_are_refused_as_a_return_target():
    # The chain starts when /login is allowed to point back at /login.
    for path in ('/login', '/logout', '/register'):
        assert sanitize_next_url(path) is None
        assert sanitize_next_url(path + '?next=/issue/19') is None


def test_an_absolute_url_is_refused():
    # Same check guards against an open redirect to another host.
    for value in (
        'https://evil.example/steal',
        'http://evil.example',
        '//evil.example/steal',
        'javascript:alert(1)',
    ):
        assert sanitize_next_url(value) is None, value


def test_a_relative_path_without_a_leading_slash_is_refused():
    assert sanitize_next_url('issue/19') is None
    assert sanitize_next_url('  ') is None
    assert sanitize_next_url(None) is None


def test_an_ordinary_page_is_accepted():
    assert sanitize_next_url('/issue/19') == '/issue/19'
    assert sanitize_next_url('/articles?page=2') == '/articles?page=2'


def _context_value(path):
    from mainweb.routes.context import register_context_processors

    app = Flask(__name__)
    app.secret_key = 'test'

    captured = {}

    # Only the processor under test matters here; the others need a database.
    class _Recorder:
        def context_processor(self, func):
            if func.__name__ == 'inject_login_next_url':
                captured['func'] = func
            return func

    recorder = _Recorder()
    try:
        register_context_processors(recorder)
    except Exception:
        # Registration touches the database for other processors; the one we
        # want is captured before that matters.
        pass

    with app.test_request_context(path):
        return captured['func']()['login_next_url']


def test_header_offers_no_return_path_on_the_login_page():
    # This is the fix: nothing to append, so no new URL to crawl.
    assert _context_value('/login') is None
    assert _context_value('/login?next=%2Fissue%2F19') is None


def test_header_keeps_the_return_path_on_a_normal_page():
    assert _context_value('/issue/19') == '/issue/19'
    # `full_path` appends a bare '?' that must not leak into the link.
    assert not str(_context_value('/issue/19')).endswith('?')


def test_query_string_survives_in_the_return_path():
    assert _context_value('/articles?page=3') == '/articles?page=3'


# --------------------------------------------------------------------------
# Editorial board caching
# --------------------------------------------------------------------------

def test_editorial_board_is_read_once_per_ttl(monkeypatch):
    calls = []

    def _load():
        calls.append(1)
        return [{'id': 1, 'full_name': 'Someone'}]

    monkeypatch.setattr(public_routes, '_load_editorial_members', _load)
    public_routes._invalidate_editorial_members_cache()

    first = public_routes._load_public_editorial_members()
    second = public_routes._load_public_editorial_members()

    assert first == second
    # The homepage and /editorial both render the whole board; one read is all
    # it should take.
    assert len(calls) == 1


def test_editorial_cache_can_be_invalidated(monkeypatch):
    board = [{'id': 1}]

    monkeypatch.setattr(public_routes, '_load_editorial_members', lambda: list(board))
    public_routes._invalidate_editorial_members_cache()

    assert len(public_routes._load_public_editorial_members()) == 1

    board.append({'id': 2})
    assert len(public_routes._load_public_editorial_members()) == 1, 'still cached'

    public_routes._invalidate_editorial_members_cache()
    assert len(public_routes._load_public_editorial_members()) == 2


def test_a_missing_board_caches_an_empty_list(monkeypatch):
    monkeypatch.setattr(public_routes, '_load_editorial_members', lambda: None)
    public_routes._invalidate_editorial_members_cache()

    assert public_routes._load_public_editorial_members() == []

    # Clean up so later tests do not inherit the empty board.
    public_routes._invalidate_editorial_members_cache()


# --------------------------------------------------------------------------
# Log noise
# --------------------------------------------------------------------------

def test_probe_paths_are_exempt_from_request_logging():
    from fmadmin.hooks import LOG_EXEMPT_PATHS as FMADMIN_LOG_EXEMPT_PATHS

    for path in ('/healthz', '/readyz', '/metrics'):
        assert path in MAINWEB_LOG_EXEMPT_PATHS, path
        assert path in FMADMIN_LOG_EXEMPT_PATHS, path


def test_real_pages_are_still_logged():
    for path in ('/', '/issue/19', '/fmadmin/submissions'):
        assert path not in MAINWEB_LOG_EXEMPT_PATHS, path
