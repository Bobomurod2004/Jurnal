"""Regression tests for the administrator permission split.

Administrators have full day-to-day journal control with superadmins (journal
content, authors, incoming payments). They may also browse regular accounts to
assign the editor role, while general user administration, site/pricing, and
system sections stay superadmin-only. These tests pin that boundary down at
three levels: the permission table, the route decorators, and the sidebar
template.
"""
import os

from flask import Flask, render_template, session

from fmadmin.routes import web as fmadmin_web
from fmadmin.utils.roles import (
    capabilities_for_user,
    permissions_for_roles,
    user_has_permission,
)


ADMIN = {'rolename': 'admin', 'roles': ['admin']}
SUPERADMIN = {'rolename': 'superadmin', 'roles': ['superadmin']}
EDITOR = {'rolename': 'editor', 'roles': ['editor']}

# What the administrator role holds for full journal operations.
ADMIN_GRANTED_PERMISSIONS = (
    'fmadmin.content.manage',
    'fmadmin.content.delete',
    'fmadmin.authors.manage',
    'fmadmin.editor_roles.manage',
    'fmadmin.payments.manage',
)
# What stays with the superadmin: site content, pricing, user records, and
# system settings.
ADMIN_DENIED_PERMISSIONS = (
    'fmadmin.site.manage',
    'fmadmin.finance.manage',
    'fmadmin.users.manage',
    'fmadmin.system.manage',
)


# --------------------------------------------------------------------------
# Permission table
# --------------------------------------------------------------------------

def test_admin_holds_the_journal_operations_permissions():
    for permission_name in ADMIN_GRANTED_PERMISSIONS:
        assert user_has_permission(ADMIN, permission_name), permission_name


def test_admin_is_denied_the_superadmin_only_permissions():
    # Accepting a payment is operational work; setting the price is not.
    # Author management is operational; general user administration is not.
    for permission_name in ADMIN_DENIED_PERMISSIONS:
        assert not user_has_permission(ADMIN, permission_name), permission_name


def test_superadmin_keeps_every_permission_an_admin_has():
    admin_permissions = set(permissions_for_roles(['admin']))
    superadmin_permissions = set(permissions_for_roles(['superadmin']))
    assert admin_permissions <= superadmin_permissions


def test_editor_gains_nothing_from_the_split():
    # The split moved permissions between admin and superadmin only -- an
    # editor must not pick up content, author, editor-role or payment management.
    for permission_name in ADMIN_GRANTED_PERMISSIONS + ADMIN_DENIED_PERMISSIONS:
        assert not user_has_permission(EDITOR, permission_name), permission_name


def test_new_capabilities_are_exposed_to_templates():
    admin_capabilities = capabilities_for_user(ADMIN)
    assert admin_capabilities['can_manage_content'] is True
    assert admin_capabilities['can_delete_content'] is True
    assert admin_capabilities['can_manage_authors'] is True
    assert admin_capabilities['can_manage_editors'] is False
    assert admin_capabilities['can_assign_editor_roles'] is True
    assert admin_capabilities['can_manage_payments'] is True
    assert admin_capabilities['can_manage_site'] is False
    assert admin_capabilities['can_manage_finance'] is False


# --------------------------------------------------------------------------
# Route decorators
# --------------------------------------------------------------------------

def _endpoint_for(rule_path):
    app = Flask(__name__)
    app.secret_key = 'test'
    fmadmin_web.register(app)
    rule = next(
        rule for rule in app.url_map.iter_rules()
        if rule.rule == rule_path and rule.endpoint.startswith('fmadmin_web.')
    )
    return app, app.view_functions[rule.endpoint]


def _required_permissions(rule_path):
    """Read the permissions the registered view actually demands.

    `permission_required` keeps its permission names in the wrapper's closure,
    so this inspects the real wiring instead of calling the view -- the views
    need a database and several of them swallow the failure into the very same
    redirect the gate uses, which would make a response-based check lie.
    """
    _app, view = _endpoint_for(rule_path)
    for cell in view.__closure__ or ():
        value = cell.cell_contents
        if isinstance(value, tuple) and value and all(isinstance(item, str) for item in value):
            return set(value)
    raise AssertionError('%s is not guarded by permission_required' % rule_path)


def _allows(rule_path, user):
    return any(
        user_has_permission(user, permission_name)
        for permission_name in _required_permissions(rule_path)
    )


ADMIN_REACHABLE_PAGES = (
    '/fmadmin/website/issues',
    '/fmadmin/website/articles',
    '/fmadmin/website/news',
    '/fmadmin/website/announcements',
    '/fmadmin/users/users',
    '/fmadmin/users/authors',
    '/fmadmin/users/authors/<int:author_id>',
    '/fmadmin/users/authors/<int:author_id>/merge',
    '/fmadmin/users/authors/<int:author_id>/link-user',
    '/fmadmin/users/users/<int:user_id>/assign-editor',
    '/fmadmin/finance/payments',
)
ADMIN_BLOCKED_PAGES = (
    '/fmadmin/editors',
    '/fmadmin/users/users/<int:user_id>',
    '/fmadmin/editorial-members',
    '/fmadmin/website/pages',
    '/fmadmin/website/tariffs',
    '/fmadmin/website/translations',
    '/fmadmin/website/email-logs',
    '/fmadmin/website/home-gallery',
)


def test_admin_reaches_the_granted_pages():
    for rule_path in ADMIN_REACHABLE_PAGES:
        assert _allows(rule_path, ADMIN), rule_path


def test_admin_is_blocked_from_superadmin_pages():
    for rule_path in ADMIN_BLOCKED_PAGES:
        assert not _allows(rule_path, ADMIN), rule_path


def test_superadmin_still_reaches_every_page():
    for rule_path in ADMIN_REACHABLE_PAGES + ADMIN_BLOCKED_PAGES:
        assert _allows(rule_path, SUPERADMIN), rule_path


def test_editor_is_blocked_from_admin_pages():
    for rule_path in ADMIN_REACHABLE_PAGES + ADMIN_BLOCKED_PAGES:
        assert not _allows(rule_path, EDITOR), rule_path


def test_admin_has_full_control_of_article_and_issue_delete_routes():
    # Article and issue deletion is part of the admin's full journal-content
    # control.  The routes still use their dedicated permission so future
    # roles can be restricted independently.
    for rule_path in (
        '/fmadmin/website/issues/<int:issue_id>/delete',
        '/fmadmin/website/articles/<int:article_id>/delete',
    ):
        assert _required_permissions(rule_path) == {'fmadmin.content.delete'}
        assert _allows(rule_path, ADMIN), rule_path
        assert _allows(rule_path, SUPERADMIN), rule_path


def test_article_edit_and_delete_keep_separate_permissions():
    # The edit and delete routes retain distinct permissions, even though the
    # administrator role has both of them.
    edit_permissions = _required_permissions('/fmadmin/website/articles/<int:article_id>')
    delete_permissions = _required_permissions('/fmadmin/website/articles/<int:article_id>/delete')
    assert edit_permissions == {'fmadmin.content.manage'}
    assert edit_permissions != delete_permissions


# --------------------------------------------------------------------------
# Privilege-escalation guard on the editors pages
# --------------------------------------------------------------------------

def test_non_superadmin_cannot_manage_a_staff_account_that_also_is_an_editor():
    # The editor routes are superadmin-only, and this helper preserves the
    # same boundary should they be exposed to another role in the future.
    superadmin_editor = {'rolename': 'superadmin', 'roles': ['superadmin', 'editor']}
    admin_editor = {'rolename': 'admin', 'roles': ['admin', 'editor']}
    plain_editor = {'rolename': 'editor', 'roles': ['editor']}

    assert fmadmin_web._actor_may_manage_staff_account(ADMIN, plain_editor) is True
    assert fmadmin_web._actor_may_manage_staff_account(ADMIN, superadmin_editor) is False
    assert fmadmin_web._actor_may_manage_staff_account(ADMIN, admin_editor) is False


def test_admin_can_assign_only_regular_users_to_the_editor_role():
    regular_user = {'rolename': 'user', 'roles': ['user']}
    editor = {'rolename': 'editor', 'roles': ['editor']}
    admin = {'rolename': 'admin', 'roles': ['admin']}
    superadmin = {'rolename': 'superadmin', 'roles': ['superadmin']}

    assert fmadmin_web._may_assign_editor_role(ADMIN, regular_user) is True
    assert fmadmin_web._may_assign_editor_role(ADMIN, editor) is False
    assert fmadmin_web._may_assign_editor_role(ADMIN, admin) is False
    assert fmadmin_web._may_assign_editor_role(ADMIN, superadmin) is False


def test_superadmin_promotion_discards_redundant_lower_staff_roles():
    assert fmadmin_web._roles_for_primary_role(
        'superadmin', ['user', 'editor', 'admin', 'superadmin']
    ) == ['superadmin', 'user']
    assert fmadmin_web._roles_for_primary_role(
        'superadmin', ['admin', 'superadmin']
    ) == ['superadmin']


def test_superadmin_may_still_manage_any_staff_account():
    superadmin_editor = {'rolename': 'superadmin', 'roles': ['superadmin', 'editor']}
    assert fmadmin_web._actor_may_manage_staff_account(SUPERADMIN, superadmin_editor) is True


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

def _render_sidebar_for(user):
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

    with app.test_request_context('/fmadmin/'):
        session['fmadmin_user'] = {
            'id': 1,
            'name': 'Test',
            'rolename': user['rolename'],
            'capabilities': capabilities_for_user(user),
        }
        session['language'] = 'uz'
        return render_template('basic.html')


def _has_nav_link(markup, path):
    # Match the rendered href, not a bare substring: the global-search script
    # embedded in basic.html also mentions '/fmadmin/users/users'.
    return 'href="%s"' % path in markup


ADMIN_SIDEBAR_LINKS = (
    '/fmadmin/website/issues',
    '/fmadmin/website/articles',
    '/fmadmin/website/news',
    '/fmadmin/website/announcements',
    '/fmadmin/users/users',
    '/fmadmin/users/authors',
    '/fmadmin/finance/payments',
)
SUPERADMIN_ONLY_SIDEBAR_LINKS = (
    '/fmadmin/editors',
    '/fmadmin/editorial-members',
    '/fmadmin/website/pages',
    '/fmadmin/website/tariffs',
    '/fmadmin/website/translations',
    '/fmadmin/website/email-logs',
    '/fmadmin/website/home-gallery',
)


def test_admin_sidebar_shows_journal_operations_links():
    markup = _render_sidebar_for(ADMIN)
    for path in ADMIN_SIDEBAR_LINKS:
        assert _has_nav_link(markup, path), path


def test_admin_sidebar_hides_superadmin_links():
    # A visible link that only leads to "access denied" is worse than no link.
    markup = _render_sidebar_for(ADMIN)
    for path in SUPERADMIN_ONLY_SIDEBAR_LINKS:
        assert not _has_nav_link(markup, path), path


def test_superadmin_sidebar_still_shows_everything():
    markup = _render_sidebar_for(SUPERADMIN)
    for path in ADMIN_SIDEBAR_LINKS + SUPERADMIN_ONLY_SIDEBAR_LINKS:
        assert _has_nav_link(markup, path), path


def test_editor_sidebar_shows_no_management_links():
    markup = _render_sidebar_for(EDITOR)
    for path in ADMIN_SIDEBAR_LINKS + SUPERADMIN_ONLY_SIDEBAR_LINKS:
        assert not _has_nav_link(markup, path), path
