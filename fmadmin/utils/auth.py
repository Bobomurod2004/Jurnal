from functools import wraps
from flask import session, redirect, url_for, flash
from modules.translate import t


def is_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'fmadmin_user' not in session:
            return redirect(url_for('login'))

        if session['fmadmin_user'].get('rolename') != 'admin':
            flash(t('admin_error_admin_required'), 'danger')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


def is_editor_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'fmadmin_user' not in session:
            return redirect(url_for('login'))

        if session['fmadmin_user'].get('rolename') not in ['admin', 'editor']:
            flash(t('admin_error_editor_required'), 'danger')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


def is_admin_or_editor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'fmadmin_user' not in session:
            return redirect(url_for('login'))

        if session['fmadmin_user'].get('rolename') not in ['admin', 'editor']:
            flash(t('admin_error_admin_or_editor_required'), 'danger')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function
