# flake8: noqa
import time
from flask import render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import dbc
from modules.translate import t
from utils.auth import not_auth_only, is_valid_email, is_strong_password


def app__login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('app__login'))

        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('app__login'))

        try:
            _user = dbc.users.get(email=email).exec()
            if _user:
                user = _user[0]

                if user.get('is_blocked'):
                    flash('Your account is blocked. Please contact support.', 'error')
                    return redirect(url_for('app__login'))

                password_valid = False
                stored_pw = user.get('password', '')
                if stored_pw and ('pbkdf2:sha256:' in stored_pw or 'scrypt:' in stored_pw):
                    password_valid = check_password_hash(stored_pw, password)
                elif stored_pw:
                    # Legacy plaintext comparison — migrate to hash immediately
                    password_valid = (stored_pw == password)
                    if password_valid:
                        hashed = generate_password_hash(password)
                        dbc.users.get(id=user['id']).update(password=hashed).exec()
                else:
                    password_valid = False

                if password_valid:
                    session['user'] = user
                    session['user_id'] = user['id']
                    session.permanent = True
                    return redirect(url_for('app__index'))

            flash('Invalid login or password. Try again.', 'error')
            return redirect(url_for('app__login'))

        except Exception:
            flash('System error. Please try again later.', 'error')
            return redirect(url_for('app__login'))

    return render_template('auth/login.html')


def app__register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        accept_terms = request.form.get('accept_terms')

        if not all([name, email, password, password_confirm]):
            flash('All fields are required', 'error')
            return redirect(url_for('app__register'))

        if not accept_terms:
            flash('You must accept the terms and conditions', 'error')
            return redirect(url_for('app__register'))

        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('app__register'))

        if password != password_confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('app__register'))

        valid_password, message = is_strong_password(password)
        if not valid_password:
            flash(message, 'error')
            return redirect(url_for('app__register'))

        try:
            existing_user = dbc.users.get(email=email).exec()
            if existing_user:
                flash('Email already registered', 'error')
                return redirect(url_for('app__register'))

            password_hash = generate_password_hash(password)
            current_time = int(time.time())

            dbc.users.add(
                name=name,
                email=email,
                password=password_hash,
                rolename='user',
                is_blocked=False,
                is_notify=True,
                accept_rules_time=current_time,
                register_time=current_time,
                created_at=current_time,
                last_online=current_time
            ).exec()

            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('app__login'))

        except Exception:
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('app__register'))

    return render_template('auth/register.html')


def app__logout():
    session.pop('user', None)
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('app__index'))


def register(app):
    app.add_url_rule('/login', view_func=not_auth_only(app__login), methods=['GET', 'POST'])
    app.add_url_rule('/register', view_func=not_auth_only(app__register), methods=['GET', 'POST'])
    app.add_url_rule('/logout', view_func=app__logout)
