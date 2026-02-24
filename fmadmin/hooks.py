# flake8: noqa
from flask import request, session, jsonify, redirect, url_for, flash
from modules.translate import t, translate


def register(app):
    @app.before_request
    def require_auth():
        public_routes = [
            '/fmadmin/login',
            '/fmadmin/logout',
            '/dist/',
            '/static/',
            '/uploads/'
        ]

        for route in public_routes:
            if request.path.startswith(route):
                return None

        if request.path.startswith('/fmadmin/'):
            if 'fmadmin_user' not in session:
                if request.is_json:
                    return jsonify({'error': 'Unauthorized', 'redirect': '/fmadmin/login'}), 401
                return redirect(url_for('login'))

            user_role = session['fmadmin_user'].get('rolename')
            if user_role not in ['admin', 'editor']:
                if request.is_json:
                    return jsonify({'error': 'Access denied', 'redirect': '/fmadmin/login'}), 403
                flash(t('admin_error_no_access'), 'danger')
                return redirect(url_for('login'))

        return None

    @app.context_processor
    def inject_translate():
        return {'t': t, 'translate': translate}
