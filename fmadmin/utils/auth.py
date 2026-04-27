from functools import wraps
from flask import session, redirect, url_for, flash, jsonify
from modules.translate import t
from utils.roles import primary_role, user_has_permission, user_has_role


def _current_role():
    user = session.get('fmadmin_user') or {}
    return primary_role(user)


def is_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'fmadmin_user' not in session:
            return redirect(url_for('login'))

        if not user_has_permission(session.get('fmadmin_user') or {}, 'fmadmin.submissions.manage'):
            flash(t('admin_error_admin_required'), 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function


def is_editor_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'fmadmin_user' not in session:
            return redirect(url_for('login'))

        if not user_has_permission(session.get('fmadmin_user') or {}, 'fmadmin.assignments.view'):
            flash(t('admin_error_editor_required'), 'danger')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


def is_admin_or_editor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'fmadmin_user' not in session:
            return redirect(url_for('login'))

        if not user_has_permission(session.get('fmadmin_user') or {}, 'fmadmin.access'):
            flash(t('admin_error_admin_or_editor_required'), 'danger')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


def api_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('fmadmin_user')
        if not user:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        if not user_has_permission(user, 'fmadmin.submissions.manage'):
            return jsonify({'success': False, 'message': 'Admin access required'}), 403

        return f(*args, **kwargs)
    return decorated_function


def api_permission_required(permission_name, message='Permission required'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = session.get('fmadmin_user')
            if not user:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 401

            if not user_has_permission(user, permission_name):
                return jsonify({'success': False, 'message': message}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('fmadmin_user')
        if not user:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        if not user_has_role(user, 'superadmin'):
            return jsonify({'success': False, 'message': 'Superadmin access required'}), 403

        return f(*args, **kwargs)
    return decorated_function


def is_superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'fmadmin_user' not in session:
            return redirect(url_for('login'))

        if not user_has_role(session.get('fmadmin_user') or {}, 'superadmin'):
            flash(t('admin_error_no_access'), 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function
