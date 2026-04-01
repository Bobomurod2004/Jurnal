# flake8: noqa
import json
import logging
import re
import secrets
import time
import traceback
from urllib.parse import urlencode, urlparse

import requests
import settings
from flask import current_app, flash, has_request_context, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import dbc
from modules.translate import t, translate
from utils.emailer import send_notification_email
from utils.notifications import normalize_notification_language, user_allows_email_notifications
from utils.auth import (
    decode_html_entities,
    is_strong_password,
    is_user_profile_complete,
    is_valid_email,
    not_auth_only,
    sanitize_input,
)
from utils.roles import AUTHOR_ROLE, build_user_roles, hydrate_user_roles, user_has_permission


logger = logging.getLogger(__name__)

ISO3166_TAB_PATH = '/usr/share/zoneinfo/iso3166.tab'
COUNTRY_CODE_OVERRIDES = {
    'central african republic': 'CF',
    'congo': 'CG',
    'eswatini': 'SZ',
    'myanmar': 'MM',
    'north korea': 'KP',
    'saint kitts and nevis': 'KN',
    'saint lucia': 'LC',
    'saint vincent and the grenadines': 'VC',
    'samoa': 'WS',
    'south korea': 'KR',
    'united kingdom': 'GB',
}

GOOGLE_OAUTH_AUTHORIZE_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_OAUTH_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_OAUTH_USERINFO_URL = 'https://openidconnect.googleapis.com/v1/userinfo'
GOOGLE_OAUTH_STATE_TTL = 600
USER_OAUTH_EXTRA_COLUMN_TYPES = {
    'oauth_provider': 'text',
    'oauth_sub': 'text',
    'oauth_email_verified': 'boolean',
    'oauth_last_login_at': 'bigint',
    'roles': 'text[]',
    'ui_language': 'text',
}

EMAIL_VERIFICATION_TABLE = 'auth_email_verifications'
REGISTER_EMAIL_VERIFICATION_PURPOSE = 'register'
PENDING_REGISTRATION_SESSION_KEY = 'pending_registration_email'
RESET_PASSWORD_VERIFICATION_PURPOSE = 'password_reset'
PENDING_PASSWORD_RESET_SESSION_KEY = 'pending_password_reset_email'
EMAIL_VERIFICATION_STORAGE_READY = False


def _normalize_country_name(name):
    if not name:
        return ''
    normalized = name.strip().lower()
    normalized = normalized.replace('&', ' and ')
    normalized = normalized.replace('(', ' ').replace(')', ' ')
    normalized = normalized.replace('-', ' ')
    normalized = normalized.replace("'", '').replace('’', '')
    normalized = re.sub(r'[^a-z0-9 ]', ' ', normalized)
    return ' '.join(normalized.split())


def _load_iso_country_name_map():
    country_map = {}
    try:
        with open(ISO3166_TAB_PATH, encoding='utf-8') as iso_file:
            for line in iso_file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                code, country_name = line.split('\t', 1)
                country_map[_normalize_country_name(country_name)] = code.upper()
    except OSError:
        return {}
    return country_map


ISO_COUNTRY_NAME_MAP = _load_iso_country_name_map()


def _country_name_to_code(country_name):
    normalized_name = _normalize_country_name(country_name)
    if not normalized_name:
        return ''
    return COUNTRY_CODE_OVERRIDES.get(normalized_name) or ISO_COUNTRY_NAME_MAP.get(normalized_name, '')


def _country_code_to_flag(country_code):
    if not country_code or len(country_code) != 2 or not country_code.isalpha():
        return '🏳'
    code = country_code.upper()
    return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)


def _normalize_user_for_session(user_row):
    if not user_row:
        return {}
    hydrated_user = hydrate_user_roles(user_row)
    normalized = {}
    for key, value in hydrated_user.items():
        if isinstance(value, str):
            normalized[key] = decode_html_entities(value)
        else:
            normalized[key] = value
    normalized['ui_language'] = normalize_notification_language(
        normalized.get('ui_language'),
        default=session.get('language') or 'en'
    )
    return normalized


def _set_user_session(user_row):
    user = _normalize_user_for_session(user_row)
    session['user'] = user
    session['user_id'] = user['id']
    session['language'] = normalize_notification_language(user.get('ui_language'), default=session.get('language') or 'en')
    session.permanent = True


def _sanitize_next_url(next_url):
    if not next_url:
        return None
    next_url = str(next_url).strip()
    if not next_url:
        return None
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        return None
    if not next_url.startswith('/'):
        return None
    if next_url.startswith('//'):
        return None
    blocked_paths = {'/login', '/logout', '/register'}
    if next_url.split('?', 1)[0] in blocked_paths:
        return None
    return next_url


def _post_auth_redirect(user_row, next_url=None):
    hydrated_user = hydrate_user_roles(user_row)
    if user_has_permission(hydrated_user, 'website.dashboard.access') and not is_user_profile_complete(user_row=hydrated_user, user_id=hydrated_user.get('id')):
        completion_notice = t('complete_profile_required')
        if not completion_notice or completion_notice == 'complete_profile_required':
            completion_notice = 'Please complete your profile information before continuing.'
        flash(completion_notice, 'warning')
        return redirect(url_for('app__dashboard_profile'))
    if next_url:
        return redirect(next_url)
    return redirect(url_for('app__index'))


def _send_registration_welcome_email(user_row, is_google=False):
    email = (user_row or {}).get('email')
    if not email or not user_allows_email_notifications(user_row):
        return False

    first_name = (user_row or {}).get('name') or 'Author'
    body_lines = ['You can now complete your profile and submit new articles.']
    if is_google:
        body_lines.append('Google sign-in has been linked to your journal account.')

    return send_notification_email(
        recipients=[email],
        subject='Welcome to Philology Matters',
        intro=f'Hello {first_name}, your account is now active.',
        body_lines=body_lines,
        cta_url=url_for('app__dashboard_profile'),
        cta_label='Open dashboard',
        fail_silently=True,
    )


def _now_ts():
    return int(time.time())


def _verification_code_length():
    return max(4, int(settings.AUTH_EMAIL_CODE_LENGTH))


def _verification_ttl_seconds():
    return max(60, int(settings.AUTH_EMAIL_CODE_TTL_SECONDS))


def _verification_ttl_minutes():
    ttl_seconds = _verification_ttl_seconds()
    return max(1, (ttl_seconds + 59) // 60)


def _verification_resend_seconds():
    return max(15, int(settings.AUTH_EMAIL_CODE_RESEND_SECONDS))


def _verification_max_attempts():
    return max(1, int(settings.AUTH_EMAIL_CODE_MAX_ATTEMPTS))


def _verification_max_sends():
    return max(1, int(settings.AUTH_EMAIL_CODE_MAX_SENDS))


def _mask_email(value):
    email = (value or '').strip()
    if '@' not in email:
        return email
    local_part, domain = email.split('@', 1)
    if len(local_part) <= 2:
        masked_local = (local_part[:1] or '*') + '*'
    else:
        masked_local = local_part[:2] + ('*' * max(1, len(local_part) - 2))
    return f'{masked_local}@{domain}'


def _get_request_ip():
    forwarded_for = request.headers.get('X-Forwarded-For', '').strip()
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return (request.remote_addr or '').strip()


def _cursor_fetchone_dict(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        cursor.description[index][0]: row[index]
        for index in range(len(cursor.description))
    }


def _registration_verify_url(email=None):
    kwargs = {'_external': True}
    if email:
        kwargs['email'] = email
    return url_for('app__register_verify', **kwargs)


def _password_reset_verify_url(email=None):
    kwargs = {'_external': True}
    if email:
        kwargs['email'] = email
    return url_for('app__forgot_password_verify', **kwargs)


def _ensure_email_verification_table():
    global EMAIL_VERIFICATION_STORAGE_READY
    if EMAIL_VERIFICATION_STORAGE_READY:
        return True

    cursor = None
    try:
        dbc.users.precheck()
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {EMAIL_VERIFICATION_TABLE} (
                id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                purpose TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                payload TEXT,
                expires_at BIGINT NOT NULL,
                created_at BIGINT NOT NULL,
                updated_at BIGINT NOT NULL,
                consumed_at BIGINT,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                sent_count INTEGER NOT NULL DEFAULT 1,
                last_sent_at BIGINT NOT NULL,
                ip_address TEXT,
                user_agent TEXT
            );
            """
        )
        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{EMAIL_VERIFICATION_TABLE}_lookup
            ON {EMAIL_VERIFICATION_TABLE} (email, purpose, consumed_at, expires_at);
            """
        )
        dbc.conn.commit()
        EMAIL_VERIFICATION_STORAGE_READY = True
        return True
    except Exception:
        logger.exception("Unable to prepare email verification storage")
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return False
    finally:
        if cursor is not None:
            cursor.close()


def _load_pending_email_verification(email, purpose=REGISTER_EMAIL_VERIFICATION_PURPOSE):
    if not email or not _ensure_email_verification_table():
        return None

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"""
            SELECT
                id,
                email,
                purpose,
                code_hash,
                payload,
                expires_at,
                created_at,
                updated_at,
                consumed_at,
                failed_attempts,
                sent_count,
                last_sent_at,
                ip_address,
                user_agent
            FROM {EMAIL_VERIFICATION_TABLE}
            WHERE email = %s
              AND purpose = %s
              AND consumed_at IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (email, purpose),
        )
        record = _cursor_fetchone_dict(cursor)
        dbc.conn.commit()
        return record
    except Exception:
        logger.exception("Unable to load pending email verification for email=%s purpose=%s", email, purpose)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return None
    finally:
        if cursor is not None:
            cursor.close()


def _restore_email_verification_state(previous_record, current_record_id):
    if not _ensure_email_verification_table():
        return

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        if previous_record:
            cursor.execute(
                f"""
                UPDATE {EMAIL_VERIFICATION_TABLE}
                SET
                    code_hash = %s,
                    payload = %s,
                    expires_at = %s,
                    created_at = %s,
                    updated_at = %s,
                    consumed_at = %s,
                    failed_attempts = %s,
                    sent_count = %s,
                    last_sent_at = %s,
                    ip_address = %s,
                    user_agent = %s
                WHERE id = %s
                """,
                (
                    previous_record.get('code_hash'),
                    previous_record.get('payload'),
                    previous_record.get('expires_at'),
                    previous_record.get('created_at'),
                    previous_record.get('updated_at'),
                    previous_record.get('consumed_at'),
                    previous_record.get('failed_attempts') or 0,
                    previous_record.get('sent_count') or 1,
                    previous_record.get('last_sent_at') or previous_record.get('created_at') or _now_ts(),
                    previous_record.get('ip_address'),
                    previous_record.get('user_agent'),
                    previous_record.get('id'),
                ),
            )
        elif current_record_id:
            cursor.execute(
                f"DELETE FROM {EMAIL_VERIFICATION_TABLE} WHERE id = %s",
                (current_record_id,),
            )
        dbc.conn.commit()
    except Exception:
        logger.exception("Unable to restore email verification state for record_id=%s", current_record_id)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
    finally:
        if cursor is not None:
            cursor.close()


def _send_registration_code_email(email, first_name, code):
    ttl_minutes = _verification_ttl_minutes()
    intro_name = (first_name or '').strip() or 'there'
    return send_notification_email(
        recipients=[email],
        subject='Verify your email address',
        intro=f'Hello {intro_name}, use this code to finish creating your Philology Matters account.',
        details=[
            ('Verification code', code),
            ('Valid for', f'{ttl_minutes} minute(s)'),
        ],
        body_lines=[
            'Enter this one-time code on the verification page to activate your account.',
            'If you did not request this code, you can safely ignore this email.',
        ],
        cta_url=_registration_verify_url(email=email),
        cta_label='Open verification page',
        fail_silently=True,
    )


def _send_password_reset_code_email(email, first_name, code):
    ttl_minutes = _verification_ttl_minutes()
    intro_name = (first_name or '').strip() or 'there'
    return send_notification_email(
        recipients=[email],
        subject='Reset your password',
        intro=f'Hello {intro_name}, use this code to reset your Philology Matters password.',
        details=[
            ('Verification code', code),
            ('Valid for', f'{ttl_minutes} minute(s)'),
        ],
        body_lines=[
            'Enter this one-time code on the password reset page to set a new password.',
            'If you did not request this code, you can safely ignore this email.',
        ],
        cta_url=_password_reset_verify_url(email=email),
        cta_label='Open password reset page',
        fail_silently=True,
    )


def _generate_email_verification_code():
    length = _verification_code_length()
    return f"{secrets.randbelow(10 ** length):0{length}d}"


def _create_or_refresh_registration_verification(registration_payload):
    if not _ensure_email_verification_table():
        return False, 'System error. Please try again later.'

    email = (registration_payload or {}).get('email', '').strip().lower()
    if not email:
        return False, 'Email address is required.'

    payload_text = json.dumps(registration_payload, ensure_ascii=True)
    first_name = (registration_payload or {}).get('first_name', '')
    now_ts = _now_ts()
    expires_at = now_ts + _verification_ttl_seconds()
    code = _generate_email_verification_code()
    code_hash = generate_password_hash(code)
    request_ip = _get_request_ip()[:255]
    user_agent = (request.headers.get('User-Agent') or '')[:500]
    previous_record = _load_pending_email_verification(email)

    cursor = None
    current_record_id = None
    try:
        cursor = dbc.conn.cursor()
        if previous_record:
            cursor.execute(
                f"""
                UPDATE {EMAIL_VERIFICATION_TABLE}
                SET
                    code_hash = %s,
                    payload = %s,
                    expires_at = %s,
                    updated_at = %s,
                    consumed_at = NULL,
                    failed_attempts = 0,
                    sent_count = 1,
                    last_sent_at = %s,
                    ip_address = %s,
                    user_agent = %s
                WHERE id = %s
                RETURNING id
                """,
                (
                    code_hash,
                    payload_text,
                    expires_at,
                    now_ts,
                    now_ts,
                    request_ip,
                    user_agent,
                    previous_record['id'],
                ),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {EMAIL_VERIFICATION_TABLE} (
                    email,
                    purpose,
                    code_hash,
                    payload,
                    expires_at,
                    created_at,
                    updated_at,
                    last_sent_at,
                    ip_address,
                    user_agent
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    email,
                    REGISTER_EMAIL_VERIFICATION_PURPOSE,
                    code_hash,
                    payload_text,
                    expires_at,
                    now_ts,
                    now_ts,
                    now_ts,
                    request_ip,
                    user_agent,
                ),
            )
        current_record_id = cursor.fetchone()[0]
        dbc.conn.commit()
    except Exception:
        logger.exception("Unable to create registration verification for email=%s", email)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return False, 'System error. Please try again later.'
    finally:
        if cursor is not None:
            cursor.close()

    if not _send_registration_code_email(email, first_name, code):
        _restore_email_verification_state(previous_record, current_record_id)
        return False, 'Verification email could not be sent. Please try again.'

    session[PENDING_REGISTRATION_SESSION_KEY] = email
    return True, 'Verification code sent. Check your email to continue.'


def _create_or_refresh_password_reset_verification(user_row):
    if not _ensure_email_verification_table():
        return False, 'System error. Please try again later.'

    email = (user_row or {}).get('email', '').strip().lower()
    if not email:
        return False, 'Email address is required.'

    payload_text = json.dumps({
        'user_id': (user_row or {}).get('id'),
        'email': email,
        'name': (user_row or {}).get('name', ''),
    }, ensure_ascii=True)
    first_name = (user_row or {}).get('name', '')
    now_ts = _now_ts()
    expires_at = now_ts + _verification_ttl_seconds()
    code = _generate_email_verification_code()
    code_hash = generate_password_hash(code)
    request_ip = _get_request_ip()[:255]
    user_agent = (request.headers.get('User-Agent') or '')[:500]
    previous_record = _load_pending_email_verification(email, purpose=RESET_PASSWORD_VERIFICATION_PURPOSE)

    cursor = None
    current_record_id = None
    try:
        cursor = dbc.conn.cursor()
        if previous_record:
            cursor.execute(
                f"""
                UPDATE {EMAIL_VERIFICATION_TABLE}
                SET
                    code_hash = %s,
                    payload = %s,
                    expires_at = %s,
                    updated_at = %s,
                    consumed_at = NULL,
                    failed_attempts = 0,
                    sent_count = 1,
                    last_sent_at = %s,
                    ip_address = %s,
                    user_agent = %s
                WHERE id = %s
                RETURNING id
                """,
                (
                    code_hash,
                    payload_text,
                    expires_at,
                    now_ts,
                    now_ts,
                    request_ip,
                    user_agent,
                    previous_record['id'],
                ),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {EMAIL_VERIFICATION_TABLE} (
                    email,
                    purpose,
                    code_hash,
                    payload,
                    expires_at,
                    created_at,
                    updated_at,
                    last_sent_at,
                    ip_address,
                    user_agent
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    email,
                    RESET_PASSWORD_VERIFICATION_PURPOSE,
                    code_hash,
                    payload_text,
                    expires_at,
                    now_ts,
                    now_ts,
                    now_ts,
                    request_ip,
                    user_agent,
                ),
            )
        current_record_id = cursor.fetchone()[0]
        dbc.conn.commit()
    except Exception:
        logger.exception("Unable to create password reset verification for email=%s", email)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return False, 'System error. Please try again later.'
    finally:
        if cursor is not None:
            cursor.close()

    if not _send_password_reset_code_email(email, first_name, code):
        _restore_email_verification_state(previous_record, current_record_id)
        return False, 'Verification email could not be sent. Please try again.'

    session[PENDING_PASSWORD_RESET_SESSION_KEY] = email
    return True, 'Verification code sent. Check your email to continue.'


def _resend_registration_verification(email):
    email = (email or '').strip().lower()
    pending_record = _load_pending_email_verification(email)
    if not pending_record or not pending_record.get('payload'):
        return False, 'Registration session expired. Please start again.', 'error'

    now_ts = _now_ts()
    last_sent_at = int(pending_record.get('last_sent_at') or 0)
    wait_seconds = _verification_resend_seconds() - max(0, now_ts - last_sent_at)
    if wait_seconds > 0:
        return False, f'Please wait {wait_seconds} seconds before requesting a new code.', 'warning'

    sent_count = int(pending_record.get('sent_count') or 0)
    if sent_count >= _verification_max_sends():
        return False, 'You have reached the resend limit. Please start registration again.', 'error'

    try:
        payload = json.loads(pending_record.get('payload') or '{}')
    except (TypeError, ValueError):
        payload = {}

    first_name = (payload or {}).get('first_name', '')
    code = _generate_email_verification_code()
    code_hash = generate_password_hash(code)
    expires_at = now_ts + _verification_ttl_seconds()
    request_ip = _get_request_ip()[:255]
    user_agent = (request.headers.get('User-Agent') or '')[:500]

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"""
            UPDATE {EMAIL_VERIFICATION_TABLE}
            SET
                code_hash = %s,
                expires_at = %s,
                updated_at = %s,
                failed_attempts = 0,
                sent_count = %s,
                last_sent_at = %s,
                ip_address = %s,
                user_agent = %s
            WHERE id = %s
            """,
            (
                code_hash,
                expires_at,
                now_ts,
                sent_count + 1,
                now_ts,
                request_ip,
                user_agent,
                pending_record['id'],
            ),
        )
        dbc.conn.commit()
    except Exception:
        logger.exception("Unable to resend registration verification for email=%s", email)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return False, 'System error. Please try again later.', 'error'
    finally:
        if cursor is not None:
            cursor.close()

    if not _send_registration_code_email(email, first_name, code):
        _restore_email_verification_state(pending_record, pending_record['id'])
        return False, 'Verification email could not be sent. Please try again.', 'error'

    session[PENDING_REGISTRATION_SESSION_KEY] = email
    return True, 'A new verification code was sent to your email.', 'success'


def _resend_password_reset_verification(email):
    email = (email or '').strip().lower()
    pending_record = _load_pending_email_verification(email, purpose=RESET_PASSWORD_VERIFICATION_PURPOSE)
    if not pending_record or not pending_record.get('payload'):
        return False, 'Password reset session expired. Please start again.', 'error'

    now_ts = _now_ts()
    last_sent_at = int(pending_record.get('last_sent_at') or 0)
    wait_seconds = _verification_resend_seconds() - max(0, now_ts - last_sent_at)
    if wait_seconds > 0:
        return False, f'Please wait {wait_seconds} seconds before requesting a new code.', 'warning'

    sent_count = int(pending_record.get('sent_count') or 0)
    if sent_count >= _verification_max_sends():
        return False, 'You have reached the resend limit. Please start again.', 'error'

    try:
        payload = json.loads(pending_record.get('payload') or '{}')
    except (TypeError, ValueError):
        payload = {}

    first_name = (payload or {}).get('name', '')
    code = _generate_email_verification_code()
    code_hash = generate_password_hash(code)
    expires_at = now_ts + _verification_ttl_seconds()
    request_ip = _get_request_ip()[:255]
    user_agent = (request.headers.get('User-Agent') or '')[:500]

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"""
            UPDATE {EMAIL_VERIFICATION_TABLE}
            SET
                code_hash = %s,
                expires_at = %s,
                updated_at = %s,
                failed_attempts = 0,
                sent_count = %s,
                last_sent_at = %s,
                ip_address = %s,
                user_agent = %s
            WHERE id = %s
            """,
            (
                code_hash,
                expires_at,
                now_ts,
                sent_count + 1,
                now_ts,
                request_ip,
                user_agent,
                pending_record['id'],
            ),
        )
        dbc.conn.commit()
    except Exception:
        logger.exception("Unable to resend password reset verification for email=%s", email)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return False, 'System error. Please try again later.', 'error'
    finally:
        if cursor is not None:
            cursor.close()

    if not _send_password_reset_code_email(email, first_name, code):
        _restore_email_verification_state(pending_record, pending_record['id'])
        return False, 'Verification email could not be sent. Please try again.', 'error'

    session[PENDING_PASSWORD_RESET_SESSION_KEY] = email
    return True, 'A new verification code was sent to your email.', 'success'


def _update_email_verification_attempt(record_id, failed_attempts):
    if not record_id or not _ensure_email_verification_table():
        return

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"""
            UPDATE {EMAIL_VERIFICATION_TABLE}
            SET failed_attempts = %s, updated_at = %s
            WHERE id = %s
            """,
            (failed_attempts, _now_ts(), record_id),
        )
        dbc.conn.commit()
    except Exception:
        logger.exception("Unable to update failed attempts for verification_id=%s", record_id)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
    finally:
        if cursor is not None:
            cursor.close()


def _consume_email_verification(record_id):
    if not record_id or not _ensure_email_verification_table():
        return

    now_ts = _now_ts()
    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"""
            UPDATE {EMAIL_VERIFICATION_TABLE}
            SET consumed_at = %s, updated_at = %s
            WHERE id = %s
            """,
            (now_ts, now_ts, record_id),
        )
        dbc.conn.commit()
    except Exception:
        logger.exception("Unable to consume email verification record_id=%s", record_id)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
    finally:
        if cursor is not None:
            cursor.close()


def _build_user_create_data_from_registration(registration_payload):
    first_name = sanitize_input((registration_payload or {}).get('first_name', '').strip())
    last_name = sanitize_input((registration_payload or {}).get('last_name', '').strip())
    father_name = sanitize_input((registration_payload or {}).get('father_name', '').strip())
    email = ((registration_payload or {}).get('email') or '').strip().lower()
    password_hash = (registration_payload or {}).get('password_hash') or ''
    country_id = (registration_payload or {}).get('country_id')
    is_notify = bool((registration_payload or {}).get('is_notify'))
    ui_language = normalize_notification_language(
        (registration_payload or {}).get('ui_language'),
        default=session.get('language') or 'en'
    )

    try:
        country_id = int(country_id)
    except (TypeError, ValueError):
        country_id = None

    if not all([first_name, last_name, email, password_hash, country_id]):
        return None

    current_time = _now_ts()
    create_data = {
        'name': first_name,
        'second_name': last_name,
        'father_name': father_name if father_name else None,
        'email': email,
        'password': password_hash,
        'country_id': country_id,
        'rolename': 'user',
        'is_blocked': False,
        'is_notify': is_notify,
        'ui_language': ui_language,
        'accept_rules_time': current_time,
        'register_time': current_time,
        'created_at': current_time,
        'last_online': current_time,
    }
    user_columns = set(dbc.columns.get('users', []))
    if 'oauth_provider' in user_columns:
        create_data['oauth_provider'] = None
    if 'oauth_sub' in user_columns:
        create_data['oauth_sub'] = None
    if 'oauth_email_verified' in user_columns:
        create_data['oauth_email_verified'] = None
    if 'oauth_last_login_at' in user_columns:
        create_data['oauth_last_login_at'] = None
    if 'roles' in user_columns:
        create_data['roles'] = build_user_roles(AUTHOR_ROLE, include_author_role=True)
    return create_data


def _create_user_from_registration_payload(registration_payload):
    create_data = _build_user_create_data_from_registration(registration_payload)
    if not create_data:
        return None, False

    existing_user = dbc.users.get(email=create_data['email']).exec()
    if existing_user:
        return existing_user[0], False

    created_rows = dbc.users.add(**create_data).exec()
    if created_rows:
        return created_rows[0], True

    fallback_rows = dbc.users.get(email=create_data['email']).exec()
    if fallback_rows:
        return fallback_rows[0], False
    return None, False


def _verify_registration_code(email, code):
    email = (email or '').strip().lower()
    normalized_code = re.sub(r'\D', '', code or '')
    pending_record = _load_pending_email_verification(email)
    if not pending_record or not pending_record.get('payload'):
        return {
            'ok': False,
            'message': 'Registration session expired. Please start again.',
            'category': 'error',
        }

    now_ts = _now_ts()
    if int(pending_record.get('expires_at') or 0) <= now_ts:
        return {
            'ok': False,
            'message': 'Verification code expired. Request a new one to continue.',
            'category': 'error',
        }

    failed_attempts = int(pending_record.get('failed_attempts') or 0)
    if failed_attempts >= _verification_max_attempts():
        return {
            'ok': False,
            'message': 'Too many incorrect attempts. Request a new code to continue.',
            'category': 'error',
        }

    if len(normalized_code) != _verification_code_length() or not check_password_hash(pending_record['code_hash'], normalized_code):
        _update_email_verification_attempt(pending_record['id'], failed_attempts + 1)
        if failed_attempts + 1 >= _verification_max_attempts():
            return {
                'ok': False,
                'message': 'Too many incorrect attempts. Request a new code to continue.',
                'category': 'error',
            }
        return {
            'ok': False,
            'message': 'Invalid verification code. Please try again.',
            'category': 'error',
        }

    try:
        payload = json.loads(pending_record.get('payload') or '{}')
    except (TypeError, ValueError):
        payload = {}

    user, is_new_user = _create_user_from_registration_payload(payload)
    if not user:
        return {
            'ok': False,
            'message': 'Registration failed. Please try again.',
            'category': 'error',
        }

    _consume_email_verification(pending_record['id'])
    return {
        'ok': True,
        'user': user,
        'is_new_user': is_new_user,
        'message': 'Email verified successfully. Your account is now active.',
        'category': 'success',
    }


def _verify_password_reset_code(email, code):
    email = (email or '').strip().lower()
    normalized_code = re.sub(r'\D', '', code or '')
    pending_record = _load_pending_email_verification(email, purpose=RESET_PASSWORD_VERIFICATION_PURPOSE)
    if not pending_record or not pending_record.get('payload'):
        return {
            'ok': False,
            'message': 'Password reset session expired. Please start again.',
            'category': 'error',
        }

    now_ts = _now_ts()
    if int(pending_record.get('expires_at') or 0) <= now_ts:
        return {
            'ok': False,
            'message': 'Verification code expired. Request a new one to continue.',
            'category': 'error',
        }

    failed_attempts = int(pending_record.get('failed_attempts') or 0)
    if failed_attempts >= _verification_max_attempts():
        return {
            'ok': False,
            'message': 'Too many incorrect attempts. Request a new code to continue.',
            'category': 'error',
        }

    if len(normalized_code) != _verification_code_length() or not check_password_hash(pending_record['code_hash'], normalized_code):
        _update_email_verification_attempt(pending_record['id'], failed_attempts + 1)
        if failed_attempts + 1 >= _verification_max_attempts():
            return {
                'ok': False,
                'message': 'Too many incorrect attempts. Request a new code to continue.',
                'category': 'error',
            }
        return {
            'ok': False,
            'message': 'Invalid verification code. Please try again.',
            'category': 'error',
        }

    try:
        payload = json.loads(pending_record.get('payload') or '{}')
    except (TypeError, ValueError):
        payload = {}

    user_id = payload.get('user_id')
    user = None
    if user_id:
        user_rows = dbc.users.get(id=user_id).exec()
        if user_rows:
            user = user_rows[0]
    if not user:
        user_rows = dbc.users.get(email=email).exec()
        if user_rows:
            user = user_rows[0]

    if not user:
        return {
            'ok': False,
            'message': 'Account not found. Please try again.',
            'category': 'error',
        }

    return {
        'ok': True,
        'user': user,
        'record_id': pending_record['id'],
        'message': 'Verification code accepted.',
        'category': 'success',
    }


def _as_optional_bool(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    return text in {'1', 'true', 'yes', 'on'}


def _is_google_auth_available():
    has_credentials = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    explicit_enabled = _as_optional_bool(settings.GOOGLE_AUTH_ENABLED)
    if explicit_enabled is None:
        return has_credentials
    return explicit_enabled and has_credentials


def _is_absolute_http_url(value):
    text = (value or '').strip()
    if not text:
        return False
    try:
        parsed = urlparse(text)
    except Exception:
        return False
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def _google_redirect_uri():
    configured = (settings.GOOGLE_REDIRECT_URI or '').strip()
    if configured and _is_absolute_http_url(configured):
        return configured
    if configured:
        logger.warning("Ignoring GOOGLE_REDIRECT_URI because it is not an absolute http(s) URL")

    app_base_url = (settings.APP_BASE_URL or '').strip().rstrip('/')
    if _is_absolute_http_url(app_base_url):
        return f"{app_base_url}/auth/google/callback"

    try:
        return url_for('app__google_callback', _external=True)
    except Exception:
        return url_for('app__google_callback', _external=True)


def _google_intent(raw_intent):
    intent = (raw_intent or '').strip().lower()
    if intent in {'login', 'register'}:
        return intent
    return 'login'


def _clear_google_oauth_session():
    session.pop('google_oauth_state', None)
    session.pop('google_oauth_state_ts', None)
    session.pop('google_oauth_intent', None)
    session.pop('google_oauth_next_url', None)


def _oauth_fallback_endpoint(intent):
    if intent == 'register':
        return 'app__register'
    return 'app__login'


def _ensure_user_oauth_columns():
    cursor = None
    try:
        existing_columns = set(dbc.columns.get('users', []))
        if not existing_columns:
            return

        missing_columns = [name for name in USER_OAUTH_EXTRA_COLUMN_TYPES if name not in existing_columns]
        cursor = dbc.conn.cursor()
        for column_name in missing_columns:
            column_type = USER_OAUTH_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        if 'roles' in existing_columns or 'roles' in missing_columns:
            cursor.execute(
                "UPDATE users "
                "SET roles = ARRAY[LOWER(COALESCE(NULLIF(TRIM(rolename), ''), 'user'))]::text[] "
                "WHERE roles IS NULL OR COALESCE(array_length(roles, 1), 0) = 0;"
            )
        dbc.conn.commit()

        users_columns = dbc.columns.setdefault('users', [])
        for column_name in missing_columns:
            if column_name not in users_columns:
                users_columns.append(column_name)
    except Exception as exc:
        logger.warning("OAuth users column sync warning: %s", exc)
        try:
            dbc.conn.rollback()
        except Exception:
            pass
    finally:
        if cursor is not None:
            cursor.close()


_ensure_user_oauth_columns()


def _build_google_auth_url(intent):
    state = secrets.token_urlsafe(32)
    session['google_oauth_state'] = state
    session['google_oauth_state_ts'] = int(time.time())
    session['google_oauth_intent'] = intent

    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': _google_redirect_uri(),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'include_granted_scopes': 'true',
        'prompt': 'select_account',
    }
    return f"{GOOGLE_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


def _read_google_userinfo(code):
    timeout = max(settings.GOOGLE_REQUEST_TIMEOUT, 1)
    token_payload = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': _google_redirect_uri(),
        'grant_type': 'authorization_code',
    }
    token_response = requests.post(GOOGLE_OAUTH_TOKEN_URL, data=token_payload, timeout=timeout)
    if token_response.status_code != 200:
        logger.warning("Google token exchange failed: %s", token_response.text)
        return None

    token_data = token_response.json()
    access_token = token_data.get('access_token')
    if not access_token:
        logger.warning("Google token response has no access_token")
        return None

    userinfo_response = requests.get(
        GOOGLE_OAUTH_USERINFO_URL,
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=timeout,
    )
    if userinfo_response.status_code != 200:
        logger.warning("Google userinfo request failed: %s", userinfo_response.text)
        return None

    return userinfo_response.json()


def _resolve_google_user(profile):
    email = (profile.get('email') or '').strip().lower()
    google_sub = str(profile.get('sub') or '').strip()
    if not email or not google_sub:
        return None, email, google_sub

    user_columns = set(dbc.columns.get('users', []))
    has_oauth_identity_cols = {'oauth_provider', 'oauth_sub'}.issubset(user_columns)

    user = None
    if has_oauth_identity_cols:
        by_sub = dbc.users.get(oauth_provider='google', oauth_sub=google_sub).exec()
        if by_sub:
            user = by_sub[0]

    if not user:
        by_email = dbc.users.get(email=email).exec()
        if by_email:
            user = by_email[0]

    return user, email, google_sub


def _create_or_update_google_user(profile, intent):
    email_verified = bool(profile.get('email_verified'))
    if not email_verified:
        flash('Google account email is not verified.', 'error')
        return None

    user, email, google_sub = _resolve_google_user(profile)
    if not email or not google_sub:
        flash('Google did not return a valid email.', 'error')
        return None

    now_ts = int(time.time())
    user_columns = set(dbc.columns.get('users', []))
    display_name = sanitize_input(profile.get('name', ''))
    first_name = sanitize_input(profile.get('given_name', ''))
    last_name = sanitize_input(profile.get('family_name', ''))
    avatar_url = (profile.get('picture') or '').strip() or None

    if user:
        existing_provider = (user.get('oauth_provider') or '').strip().lower()
        existing_sub = str(user.get('oauth_sub') or '').strip()
        if existing_provider == 'google' and existing_sub and existing_sub != google_sub:
            flash('This email is already linked to another Google account.', 'error')
            return None

    if user and (user.get('is_blocked') or user.get('is_hidden')):
        flash('Your account is blocked. Please contact support.', 'error')
        return None

    if not user:
        name_fallback = first_name or display_name or email.split('@')[0]
        create_data = {
            'name': name_fallback,
            'second_name': last_name or None,
            'father_name': None,
            'email': email,
            'password': None,
            'country_id': None,
            'rolename': 'user',
            'is_blocked': False,
            'is_notify': False,
            'ui_language': normalize_notification_language(session.get('language') or 'en', default='en'),
            'accept_rules_time': now_ts,
            'register_time': now_ts,
            'created_at': now_ts,
            'last_online': now_ts,
        }
        if avatar_url and 'avatar' in user_columns:
            create_data['avatar'] = avatar_url
        if 'is_hidden' in user_columns:
            create_data['is_hidden'] = False
        if 'roles' in user_columns:
            create_data['roles'] = build_user_roles(AUTHOR_ROLE, include_author_role=True)
        if {'oauth_provider', 'oauth_sub'}.issubset(user_columns):
            create_data['oauth_provider'] = 'google'
            create_data['oauth_sub'] = google_sub
        if 'oauth_email_verified' in user_columns:
            create_data['oauth_email_verified'] = email_verified
        if 'oauth_last_login_at' in user_columns:
            create_data['oauth_last_login_at'] = now_ts

        try:
            created_rows = dbc.users.add(**create_data).exec()
            if created_rows:
                user = created_rows[0]
            else:
                created_lookup = dbc.users.get(email=email).exec()
                user = created_lookup[0] if created_lookup else None
        except Exception:
            # Race-safe fallback for duplicated email creation attempts.
            created_lookup = dbc.users.get(email=email).exec()
            user = created_lookup[0] if created_lookup else None

    if not user:
        flash('Unable to authorize with Google right now.', 'error')
        return None

    update_data = {'last_online': now_ts}
    if 'roles' in user_columns:
        update_data['roles'] = hydrate_user_roles(user).get('roles')
    if {'oauth_provider', 'oauth_sub'}.issubset(user_columns):
        update_data['oauth_provider'] = 'google'
        update_data['oauth_sub'] = google_sub
    if 'oauth_email_verified' in user_columns:
        update_data['oauth_email_verified'] = email_verified
    if 'oauth_last_login_at' in user_columns:
        update_data['oauth_last_login_at'] = now_ts
    if 'avatar' in user_columns and avatar_url and not user.get('avatar'):
        update_data['avatar'] = avatar_url
    if 'name' in user_columns and first_name and not user.get('name'):
        update_data['name'] = first_name
    if 'second_name' in user_columns and last_name and not user.get('second_name'):
        update_data['second_name'] = last_name

    dbc.users.get(id=user['id']).update(**update_data).exec()
    reloaded = dbc.users.get(id=user['id']).exec()
    if not reloaded:
        flash('Unable to authorize with Google right now.', 'error')
        return None

    if intent == 'register' and not user.get('register_time'):
        _send_registration_welcome_email(reloaded[0], is_google=True)
        flash('Registration successful. You are now signed in with Google.', 'success')
    return reloaded[0]


def app__google_auth_start():
    if not _is_google_auth_available():
        flash('Google authentication is not configured yet.', 'error')
        return redirect(url_for('app__login'))

    intent = _google_intent(request.args.get('intent'))
    next_url = _sanitize_next_url(request.args.get('next'))
    if next_url:
        session['google_oauth_next_url'] = next_url
    auth_url = _build_google_auth_url(intent)
    return redirect(auth_url)


def app__google_callback():
    intent = _google_intent(session.get('google_oauth_intent'))
    fallback = _oauth_fallback_endpoint(intent)

    expected_state = session.get('google_oauth_state')
    state_ts = int(session.get('google_oauth_state_ts') or 0)
    next_url = _sanitize_next_url(session.get('google_oauth_next_url'))
    _clear_google_oauth_session()

    if not _is_google_auth_available():
        flash('Google authentication is not configured yet.', 'error')
        return redirect(url_for(fallback))

    oauth_error = request.args.get('error')
    if oauth_error:
        oauth_error_description = (request.args.get('error_description') or '').strip()
        if oauth_error_description:
            flash(f'Google authorization failed: {oauth_error} ({oauth_error_description})', 'error')
        else:
            flash(f'Google authorization failed: {oauth_error}', 'error')
        return redirect(url_for(fallback))

    state = request.args.get('state', '')
    if not expected_state or state != expected_state:
        flash('Invalid Google authorization state. Please try again.', 'error')
        return redirect(url_for(fallback))

    if state_ts and (int(time.time()) - state_ts > GOOGLE_OAUTH_STATE_TTL):
        flash('Google authorization timed out. Please try again.', 'error')
        return redirect(url_for(fallback))

    code = request.args.get('code', '')
    if not code:
        flash('Google authorization code was not received.', 'error')
        return redirect(url_for(fallback))

    try:
        profile = _read_google_userinfo(code)
        if not profile:
            flash('Google sign-in failed. Please try again.', 'error')
            return redirect(url_for(fallback))

        user = _create_or_update_google_user(profile, intent)
        if not user:
            return redirect(url_for(fallback))

        _set_user_session(user)
        return _post_auth_redirect(user, next_url=next_url)
    except requests.RequestException:
        flash('Google service is temporarily unavailable. Please try again.', 'error')
        return redirect(url_for(fallback))
    except Exception:
        current_app.logger.error("Google OAuth callback error: %s", traceback.format_exc())
        flash('System error. Please try again later.', 'error')
        return redirect(url_for(fallback))


def app__login():
    if request.method == 'POST':
        next_url = _sanitize_next_url(request.form.get('next') or request.args.get('next'))
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('app__login', next=next_url) if next_url else url_for('app__login'))

        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('app__login', next=next_url) if next_url else url_for('app__login'))

        try:
            _user = dbc.users.get(email=email).exec()
            if _user:
                user = _normalize_user_for_session(_user[0])

                if user.get('is_blocked') or user.get('is_hidden'):
                    flash('Your account is blocked. Please contact support.', 'error')
                    return redirect(url_for('app__login', next=next_url) if next_url else url_for('app__login'))

                password_valid = False
                stored_pw = user.get('password', '')
                if stored_pw and stored_pw.startswith(('pbkdf2:', 'scrypt:')):
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
                    _set_user_session(user)
                    return _post_auth_redirect(user, next_url=next_url)
            else:
                pending_record = _load_pending_email_verification(email)
                if pending_record:
                    session[PENDING_REGISTRATION_SESSION_KEY] = email
                    flash(
                        t('verification_required_before_login')
                        if t('verification_required_before_login') != 'verification_required_before_login'
                        else 'Please verify the code sent to your email to finish registration.',
                        'warning'
                    )
                    return redirect(url_for('app__register_verify', email=email))

            flash('Invalid login or password. Try again.', 'error')
            return redirect(url_for('app__login', next=next_url) if next_url else url_for('app__login'))

        except Exception:
            flash('System error. Please try again later.', 'error')
            return redirect(url_for('app__login', next=next_url) if next_url else url_for('app__login'))

    next_url = _sanitize_next_url(request.args.get('next'))
    return render_template('auth/login.html', google_auth_enabled=_is_google_auth_available(), next_url=next_url)


def app__register():
    if request.method == 'POST':
        first_name = sanitize_input(request.form.get('first_name', '').strip())
        last_name = sanitize_input(request.form.get('last_name', '').strip())
        father_name = sanitize_input(request.form.get('father_name', '').strip())
        country = request.form.get('country', '').strip()
        email = request.form.get('email', '').strip().lower()
        email_confirm = request.form.get('email_confirm', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        agree_terms = request.form.get('agree_terms')
        is_notify = request.form.get('is_notify')

        # Validate required fields
        if not all([first_name, last_name, email, email_confirm, password, password_confirm, country]):
            flash(t('all_fields_required') if t('all_fields_required') != 'all_fields_required' else 'All fields are required', 'error')
            return redirect(url_for('app__register'))

        # Validate terms acceptance
        if not agree_terms:
            flash(t('accept_terms_required') if t('accept_terms_required') != 'accept_terms_required' else 'You must accept the terms and conditions', 'error')
            return redirect(url_for('app__register'))

        # Validate email format
        if not is_valid_email(email):
            flash(t('invalid_email') if t('invalid_email') != 'invalid_email' else 'Invalid email format', 'error')
            return redirect(url_for('app__register'))

        # Validate email confirmation
        if email != email_confirm:
            flash(t('emails_do_not_match') if t('emails_do_not_match') != 'emails_do_not_match' else 'Emails do not match', 'error')
            return redirect(url_for('app__register'))

        # Validate password match
        if password != password_confirm:
            flash(t('passwords_do_not_match') if t('passwords_do_not_match') != 'passwords_do_not_match' else 'Passwords do not match', 'error')
            return redirect(url_for('app__register'))

        # Validate password strength
        valid_password, message = is_strong_password(password)
        if not valid_password:
            flash(message, 'error')
            return redirect(url_for('app__register'))

        # Validate country_id is a valid integer
        try:
            country_id = int(country)
        except (ValueError, TypeError):
            flash(t('invalid_country') if t('invalid_country') != 'invalid_country' else 'Please select a valid country', 'error')
            return redirect(url_for('app__register'))

        try:
            existing_user = dbc.users.get(email=email).exec()
            if existing_user:
                flash(t('email_already_registered') if t('email_already_registered') != 'email_already_registered' else 'Email already registered', 'error')
                return redirect(url_for('app__register'))

            registration_payload = {
                'first_name': first_name,
                'last_name': last_name,
                'father_name': father_name if father_name else None,
                'email': email,
                'country_id': country_id,
                'password_hash': generate_password_hash(password),
                'is_notify': bool(is_notify),
                'ui_language': normalize_notification_language(session.get('language') or 'en', default='en'),
            }
            verification_sent, feedback_message = _create_or_refresh_registration_verification(registration_payload)
            flash(
                t('verification_code_sent')
                if verification_sent and t('verification_code_sent') != 'verification_code_sent'
                else feedback_message,
                'success' if verification_sent else 'error'
            )
            if verification_sent:
                return redirect(url_for('app__register_verify', email=email))
            return redirect(url_for('app__register'))

        except Exception:
            current_app.logger.error(f"Registration error: {traceback.format_exc()}")
            flash(t('registration_failed') if t('registration_failed') != 'registration_failed' else 'Registration failed. Please try again.', 'error')
            return redirect(url_for('app__register'))

    countries_raw = dbc.fix_country.all().exec() or []
    countries = []
    for country in countries_raw:
        country_data = dict(country)
        country_name_en = country_data.get('name', '')
        country_code = _country_name_to_code(country_name_en)
        country_data['name_en'] = country_name_en
        country_data['country_code'] = country_code
        country_data['country_flag'] = _country_code_to_flag(country_code)
        countries.append(translate(country_data))
    return render_template('auth/register.html', fix_country=countries, google_auth_enabled=_is_google_auth_available())


def app__register_verify():
    requested_email = request.args.get('email', '').strip().lower()
    if requested_email and is_valid_email(requested_email):
        session[PENDING_REGISTRATION_SESSION_KEY] = requested_email

    pending_email = (session.get(PENDING_REGISTRATION_SESSION_KEY) or '').strip().lower()

    if request.method == 'POST':
        action = (request.form.get('action') or 'verify').strip().lower()
        posted_email = request.form.get('email', '').strip().lower()
        pending_email = posted_email or pending_email

        if pending_email and is_valid_email(pending_email):
            session[PENDING_REGISTRATION_SESSION_KEY] = pending_email

        if not pending_email or not is_valid_email(pending_email):
            session.pop(PENDING_REGISTRATION_SESSION_KEY, None)
            flash(
                t('registration_session_expired')
                if t('registration_session_expired') != 'registration_session_expired'
                else 'Registration session expired. Please start again.',
                'error'
            )
            return redirect(url_for('app__register'))

        if action == 'resend':
            resend_ok, resend_message, resend_category = _resend_registration_verification(pending_email)
            flash(
                t('verification_code_resent')
                if resend_ok and t('verification_code_resent') != 'verification_code_resent'
                else resend_message,
                resend_category
            )
            return redirect(url_for('app__register_verify', email=pending_email))

        verification_result = _verify_registration_code(
            pending_email,
            request.form.get('code', ''),
        )
        flash(
            t('email_verification_success')
            if verification_result['ok'] and t('email_verification_success') != 'email_verification_success'
            else verification_result['message'],
            verification_result.get('category', 'error')
        )
        if not verification_result['ok']:
            return redirect(url_for('app__register_verify', email=pending_email))

        session.pop(PENDING_REGISTRATION_SESSION_KEY, None)
        verified_user = verification_result['user']
        _set_user_session(verified_user)
        if verification_result.get('is_new_user'):
            _send_registration_welcome_email(verified_user, is_google=False)
        return redirect(url_for('app__dashboard_profile'))

    if not pending_email or not is_valid_email(pending_email):
        session.pop(PENDING_REGISTRATION_SESSION_KEY, None)
        flash(
            t('registration_session_expired')
            if t('registration_session_expired') != 'registration_session_expired'
            else 'Registration session expired. Please start again.',
            'error'
        )
        return redirect(url_for('app__register'))

    pending_record = _load_pending_email_verification(pending_email)
    if not pending_record or not pending_record.get('payload'):
        session.pop(PENDING_REGISTRATION_SESSION_KEY, None)
        flash(
            t('registration_session_expired')
            if t('registration_session_expired') != 'registration_session_expired'
            else 'Registration session expired. Please start again.',
            'error'
        )
        return redirect(url_for('app__register'))

    now_ts = _now_ts()
    resend_available_in = max(
        0,
        _verification_resend_seconds() - max(0, now_ts - int(pending_record.get('last_sent_at') or 0))
    )
    attempts_left = max(
        0,
        _verification_max_attempts() - int(pending_record.get('failed_attempts') or 0)
    )

    return render_template(
        'auth/register_verify.html',
        pending_email=pending_email,
        masked_email=_mask_email(pending_email),
        code_length=_verification_code_length(),
        expires_minutes=_verification_ttl_minutes(),
        resend_available_in=resend_available_in,
        attempts_left=attempts_left,
        code_expired=int(pending_record.get('expires_at') or 0) <= now_ts,
    )


def app__forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email or not is_valid_email(email):
            flash(
                t('invalid_email') if t('invalid_email') != 'invalid_email' else 'Invalid email format',
                'error'
            )
            return redirect(url_for('app__forgot_password'))

        try:
            user_rows = dbc.users.get(email=email).exec()
            if not user_rows:
                flash(
                    t('reset_code_sent')
                    if t('reset_code_sent') != 'reset_code_sent'
                    else 'If the account exists, a verification code has been sent to your email.',
                    'success'
                )
                return redirect(url_for('app__forgot_password'))

            user = user_rows[0]
            sent, message = _create_or_refresh_password_reset_verification(user)
            flash(
                t('reset_code_sent')
                if sent and t('reset_code_sent') != 'reset_code_sent'
                else message,
                'success' if sent else 'error'
            )
            if sent:
                return redirect(url_for('app__forgot_password_verify', email=email))
            return redirect(url_for('app__forgot_password'))
        except Exception:
            current_app.logger.error("Forgot password error: %s", traceback.format_exc())
            flash(
                t('reset_password_failed') if t('reset_password_failed') != 'reset_password_failed' else 'Unable to send reset code. Please try again.',
                'error'
            )
            return redirect(url_for('app__forgot_password'))

    return render_template('auth/forgot_password.html')


def app__forgot_password_verify():
    requested_email = request.args.get('email', '').strip().lower()
    if requested_email and is_valid_email(requested_email):
        session[PENDING_PASSWORD_RESET_SESSION_KEY] = requested_email

    pending_email = (session.get(PENDING_PASSWORD_RESET_SESSION_KEY) or '').strip().lower()

    if request.method == 'POST':
        action = (request.form.get('action') or 'verify').strip().lower()
        posted_email = request.form.get('email', '').strip().lower()
        pending_email = posted_email or pending_email

        if pending_email and is_valid_email(pending_email):
            session[PENDING_PASSWORD_RESET_SESSION_KEY] = pending_email

        if not pending_email or not is_valid_email(pending_email):
            session.pop(PENDING_PASSWORD_RESET_SESSION_KEY, None)
            flash(
                t('reset_session_expired')
                if t('reset_session_expired') != 'reset_session_expired'
                else 'Password reset session expired. Please start again.',
                'error'
            )
            return redirect(url_for('app__forgot_password'))

        if action == 'resend':
            resend_ok, resend_message, resend_category = _resend_password_reset_verification(pending_email)
            flash(
                t('reset_code_resent')
                if resend_ok and t('reset_code_resent') != 'reset_code_resent'
                else resend_message,
                resend_category
            )
            return redirect(url_for('app__forgot_password_verify', email=pending_email))

        code = request.form.get('code', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or not confirm_password:
            flash(
                t('password_required') if t('password_required') != 'password_required' else 'Password is required',
                'error'
            )
            return redirect(url_for('app__forgot_password_verify', email=pending_email))

        if new_password != confirm_password:
            flash(
                t('passwords_do_not_match') if t('passwords_do_not_match') != 'passwords_do_not_match' else 'Passwords do not match',
                'error'
            )
            return redirect(url_for('app__forgot_password_verify', email=pending_email))

        is_valid, validation_message = is_strong_password(new_password)
        if not is_valid:
            flash(validation_message, 'error')
            return redirect(url_for('app__forgot_password_verify', email=pending_email))

        verification_result = _verify_password_reset_code(pending_email, code)
        if not verification_result['ok']:
            flash(
                t('reset_password_failed')
                if t('reset_password_failed') != 'reset_password_failed'
                else verification_result['message'],
                'error'
            )
            return redirect(url_for('app__forgot_password_verify', email=pending_email))

        user = verification_result['user']
        hashed_password = generate_password_hash(new_password)
        dbc.users.get(id=user['id']).update(password=hashed_password).exec()
        _consume_email_verification(verification_result['record_id'])
        session.pop(PENDING_PASSWORD_RESET_SESSION_KEY, None)
        flash(
            t('reset_password_success')
            if t('reset_password_success') != 'reset_password_success'
            else 'Password updated successfully. Please log in.',
            'success'
        )
        return redirect(url_for('app__login'))

    if not pending_email or not is_valid_email(pending_email):
        session.pop(PENDING_PASSWORD_RESET_SESSION_KEY, None)
        flash(
            t('reset_session_expired')
            if t('reset_session_expired') != 'reset_session_expired'
            else 'Password reset session expired. Please start again.',
            'error'
        )
        return redirect(url_for('app__forgot_password'))

    pending_record = _load_pending_email_verification(pending_email, purpose=RESET_PASSWORD_VERIFICATION_PURPOSE)
    if not pending_record or not pending_record.get('payload'):
        session.pop(PENDING_PASSWORD_RESET_SESSION_KEY, None)
        flash(
            t('reset_session_expired')
            if t('reset_session_expired') != 'reset_session_expired'
            else 'Password reset session expired. Please start again.',
            'error'
        )
        return redirect(url_for('app__forgot_password'))

    now_ts = _now_ts()
    resend_available_in = max(
        0,
        _verification_resend_seconds() - max(0, now_ts - int(pending_record.get('last_sent_at') or 0))
    )
    attempts_left = max(
        0,
        _verification_max_attempts() - int(pending_record.get('failed_attempts') or 0)
    )

    return render_template(
        'auth/forgot_password_verify.html',
        pending_email=pending_email,
        masked_email=_mask_email(pending_email),
        code_length=_verification_code_length(),
        expires_minutes=_verification_ttl_minutes(),
        resend_available_in=resend_available_in,
        attempts_left=attempts_left,
        code_expired=int(pending_record.get('expires_at') or 0) <= now_ts,
    )


def app__logout():
    _clear_google_oauth_session()
    session.pop(PENDING_REGISTRATION_SESSION_KEY, None)
    session.pop(PENDING_PASSWORD_RESET_SESSION_KEY, None)
    session.pop('user', None)
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('app__index'))


def register(app):
    app.add_url_rule('/login', view_func=not_auth_only(app__login), methods=['GET', 'POST'])
    app.add_url_rule('/register', view_func=not_auth_only(app__register), methods=['GET', 'POST'])
    app.add_url_rule('/register/verify', view_func=not_auth_only(app__register_verify), methods=['GET', 'POST'])
    app.add_url_rule('/forgot-password', view_func=not_auth_only(app__forgot_password), methods=['GET', 'POST'])
    app.add_url_rule('/forgot-password/verify', view_func=not_auth_only(app__forgot_password_verify), methods=['GET', 'POST'])
    app.add_url_rule('/auth/google', view_func=not_auth_only(app__google_auth_start), methods=['GET'])
    app.add_url_rule('/api/auth/google', endpoint='app__google_auth_start_api', view_func=not_auth_only(app__google_auth_start), methods=['GET'])
    app.add_url_rule('/auth/google/callback', view_func=not_auth_only(app__google_callback), methods=['GET'])
    app.add_url_rule('/auth/google/callback/', endpoint='app__google_callback_slash', view_func=not_auth_only(app__google_callback), methods=['GET'])
    app.add_url_rule('/api/auth/google/callback', endpoint='app__google_callback_api', view_func=not_auth_only(app__google_callback), methods=['GET'])
    app.add_url_rule('/api/auth/google/callback/', endpoint='app__google_callback_api_slash', view_func=not_auth_only(app__google_callback), methods=['GET'])
    app.add_url_rule('/logout', view_func=app__logout)
