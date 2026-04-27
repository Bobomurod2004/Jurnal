# flake8: noqa
import json
import secrets
import time
import uuid
from flask import current_app, g, request, session, jsonify, redirect, url_for, flash
from modules.translate import t, translate
from extensions import db
import settings
from utils.notifications import apply_localized_notification_content, role_notification_access_clause as build_role_notification_access_clause
from utils.private_uploads import upload_access_url
from utils.roles import hydrate_user_roles, primary_role, staff_roles_for_user, user_has_permission


def _parse_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _fmadmin_session_payload(user_row):
    hydrated_user = hydrate_user_roles(user_row)
    return {
        'id': hydrated_user.get('id'),
        'name': hydrated_user.get('name'),
        'email': hydrated_user.get('email'),
        'rolename': hydrated_user.get('rolename'),
        'roles': hydrated_user.get('roles'),
        'permissions': hydrated_user.get('permissions'),
        'capabilities': hydrated_user.get('capabilities'),
        'editor_specialization': hydrated_user.get('editor_specialization'),
        'admin_tracks': hydrated_user.get('admin_tracks'),
        'editor_admin_id': hydrated_user.get('editor_admin_id'),
    }


def _role_notification_access_clause(current_user):
    return build_role_notification_access_clause(current_user)


def _role_notifications_overview():
    current_user = _fmadmin_session_payload(session.get('fmadmin_user') or {})
    if not user_has_permission(current_user, 'fmadmin.access'):
        return {'count': 0, 'preview': []}

    access_clause, access_args = _role_notification_access_clause(current_user)
    if not access_clause:
        return {'count': 0, 'preview': []}

    query = (
        "SELECT id, title, message, level, action_url, is_read, created_at, metadata_text "
        "FROM role_notifications "
        f"WHERE {access_clause} "
        "ORDER BY created_at DESC, id DESC LIMIT 6"
    )
    count_query = (
        "SELECT COUNT(*) FROM role_notifications "
        "WHERE is_read = FALSE "
        f"AND {access_clause}"
    )
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, access_args)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        preview = [apply_localized_notification_content(dict(zip(cols, row))) for row in rows]
        cursor.execute(count_query, access_args)
        unread_row = cursor.fetchone()
        cursor.close()
        return {'count': int(unread_row[0] or 0) if unread_row else 0, 'preview': preview}
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return {'count': 0, 'preview': []}


def register(app):
    def _expects_json():
        if request.path.startswith('/fmadmin/api/'):
            return True
        accept = request.headers.get('Accept', '')
        return request.is_json or 'application/json' in accept

    def _is_public_path():
        public_routes = [
            '/fmadmin/login',
            '/fmadmin/logout',
            '/dist/',
            '/static/',
            '/uploads/'
        ]
        return any(request.path.startswith(route) for route in public_routes)

    def _should_run_assignment_automation():
        if request.method != 'GET':
            return False
        ignored_prefixes = (
            '/fmadmin/api/',
            '/fmadmin/files/',
            '/fmadmin/healthz',
        )
        return request.path.startswith('/fmadmin/') and not any(
            request.path.startswith(prefix) for prefix in ignored_prefixes
        )

    def _ensure_csrf_token():
        token = session.get('csrf_token')
        if not token:
            token = secrets.token_urlsafe(32)
            session['csrf_token'] = token
        return token

    def _validate_csrf():
        expected_token = session.get('csrf_token')
        if not expected_token:
            return False

        token = (
            request.form.get('csrf_token')
            or request.headers.get('X-CSRF-Token')
            or request.headers.get('X-CSRFToken')
        )
        if not token and request.is_json:
            json_data = request.get_json(silent=True) or {}
            token = json_data.get('csrf_token')

        if not token:
            return False
        return secrets.compare_digest(str(token), str(expected_token))

    @app.before_request
    def require_auth():
        if not hasattr(g, 'request_start'):
            g.request_start = time.time()
        if not hasattr(g, 'request_id'):
            g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex

        _ensure_csrf_token()

        if request.path.startswith('/fmadmin/') and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            if not _validate_csrf():
                if _expects_json():
                    return jsonify({'success': False, 'message': 'Invalid CSRF token'}), 400
                flash('Invalid request', 'danger')
                return redirect(request.referrer or url_for('login'))

        if _is_public_path():
            return None

        if request.path.startswith('/fmadmin/'):
            if 'fmadmin_user' not in session:
                if _expects_json():
                    return jsonify({'error': 'Unauthorized', 'redirect': '/fmadmin/login'}), 401
                return redirect(url_for('login'))

            session_user = _fmadmin_session_payload(session.get('fmadmin_user') or {})
            if not user_has_permission(session_user, 'fmadmin.access'):
                if _expects_json():
                    return jsonify({'error': 'Access denied', 'redirect': '/fmadmin/login'}), 403
                flash(t('admin_error_no_access'), 'danger')
                return redirect(url_for('login'))

            user_id = session_user.get('id')
            if user_id:
                try:
                    user_data = db.users.all().equal(id=user_id).exec()
                except Exception:
                    user_data = []
                if user_data and (user_data[0].get('is_blocked') or user_data[0].get('is_hidden')):
                    session.pop('fmadmin_user', None)
                    if _expects_json():
                        return jsonify({'error': 'Account is blocked', 'redirect': '/fmadmin/login'}), 403
                    flash(t('admin_error_no_access'), 'danger')
                    return redirect(url_for('login'))
                if user_data:
                    session_user = _fmadmin_session_payload(user_data[0])

            session['fmadmin_user'] = session_user

            if _should_run_assignment_automation():
                try:
                    from routes.web import run_editor_assignment_automation
                    run_editor_assignment_automation(actor_user_id=_parse_int(user_id))
                except Exception:
                    pass

        return None

    @app.context_processor
    def inject_translate():
        notifications = _role_notifications_overview()
        return {
            't': t,
            'translate': translate,
            'csrf_token': session.get('csrf_token', ''),
            'upload_access_url': upload_access_url,
            'role_notifications_unread_count': notifications['count'],
            'role_notifications_preview': notifications['preview'],
            'app_version': settings.APP_VERSION
        }

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        if request.is_secure:
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        response.headers.setdefault('X-Request-ID', getattr(g, 'request_id', ''))
        return response

    @app.after_request
    def log_request(response):
        start_time = getattr(g, 'request_start', None)
        duration_ms = None
        if isinstance(start_time, (int, float)):
            duration_ms = int((time.time() - start_time) * 1000)
        session_user = session.get('fmadmin_user') or {}
        payload = {
            'service': 'fmadmin',
            'version': settings.APP_VERSION,
            'request_id': getattr(g, 'request_id', ''),
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': duration_ms,
            'remote_addr': request.remote_addr or '',
            'user_agent': request.headers.get('User-Agent', ''),
            'user_id': session_user.get('id'),
            'role': session_user.get('rolename'),
        }
        current_app.logger.info(json.dumps(payload, ensure_ascii=False))
        return response
