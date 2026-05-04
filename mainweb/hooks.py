import json
import os
import secrets
import time
import uuid

try:
    import mainweb.settings as settings
except ImportError:
    import settings
from flask import current_app, flash, g, jsonify, redirect, request, session, url_for
from utils.private_uploads import upload_access_url


def register(app):
    def _static_asset_version(filename):
        normalized = str(filename or '').lstrip('/')
        static_root = app.static_folder or ''
        if not normalized or not static_root:
            return settings.APP_VERSION
        candidate_path = os.path.abspath(os.path.join(static_root, normalized))
        try:
            static_root_abs = os.path.abspath(static_root)
        except Exception:
            static_root_abs = static_root
        if not candidate_path.startswith(static_root_abs):
            return settings.APP_VERSION
        try:
            return int(os.path.getmtime(candidate_path))
        except OSError:
            return settings.APP_VERSION

    def _asset_url(filename):
        return url_for(
            'static',
            filename=str(filename or '').lstrip('/'),
            v=_static_asset_version(filename),
        )

    def _expects_json():
        accept = request.headers.get('Accept', '')
        requested_with = request.headers.get('X-Requested-With', '')
        return (
            request.path.startswith('/api/')
            or request.is_json
            or 'application/json' in accept
            or requested_with == 'XMLHttpRequest'
        )

    def _ensure_csrf_token():
        token = session.get('csrf_token')
        if not token:
            token = secrets.token_urlsafe(32)
            session['csrf_token'] = token
        return token

    def _has_translation_sync_authorization():
        provided_token = request.headers.get('X-Translation-Sync-Token', '').strip()
        expected_token = (settings.TRANSLATION_SYNC_TOKEN or '').strip()
        return bool(expected_token) and secrets.compare_digest(provided_token, expected_token)

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
    def protect_requests():
        if not hasattr(g, 'request_start'):
            g.request_start = time.time()
        if not hasattr(g, 'request_id'):
            g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex

        _ensure_csrf_token()

        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return None

        # Only allow token-based bypass for the dedicated translation sync endpoint.
        if request.path.rstrip('/') == '/api/translations/clear_cache' and _has_translation_sync_authorization():
            return None

        if _validate_csrf():
            return None

        if _expects_json():
            return jsonify({'success': False, 'message': 'Invalid CSRF token'}), 400

        flash('Invalid request', 'error')
        return redirect(request.referrer or url_for('app__index'))

    @app.context_processor
    def inject_csrf():
        return {
            'csrf_token': session.get('csrf_token', ''),
            'upload_access_url': upload_access_url,
            'asset_url': _asset_url,
            'asset_version': _static_asset_version,
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
        payload = {
            'service': 'mainweb',
            'version': settings.APP_VERSION,
            'request_id': getattr(g, 'request_id', ''),
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': duration_ms,
            'remote_addr': request.remote_addr or '',
            'user_agent': request.headers.get('User-Agent', ''),
            'user_id': session.get('user_id'),
        }
        current_app.logger.info(json.dumps(payload, ensure_ascii=False))
        return response
