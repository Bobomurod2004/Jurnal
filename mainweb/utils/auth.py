import re
from functools import wraps
from markupsafe import escape
from flask import session, flash, redirect, url_for
from modules.translate import t


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('app__login'))
        return f(*args, **kwargs)
    return decorated_function


def not_auth_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('app__dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def is_valid_email(email):
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_strong_password(password):
    if not password:
        return False, t('password_required')
    if len(password) < 8:
        return False, t('password_min_length')
    if not re.search(r'[A-Z]', password):
        return False, t('password_uppercase_required')
    if not re.search(r'[a-z]', password):
        return False, t('password_lowercase_required')
    if not re.search(r'[0-9]', password):
        return False, t('password_number_required')
    return True, 'Valid'


def sanitize_input(text):
    if not text:
        return ''
    return escape(str(text))
