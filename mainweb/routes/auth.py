# flake8: noqa
import json
import logging
import re
import secrets
import time
import traceback
from urllib.parse import urlencode, urlparse

import requests
try:
    import mainweb.settings as settings
except ImportError:
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
ORCID_OAUTH_STATE_TTL = 600
ORCID_PENDING_PROFILE_SESSION_KEY = 'orcid_pending_profile'
ORCID_PENDING_INTENT_SESSION_KEY = 'orcid_pending_intent'
ORCID_PENDING_NEXT_URL_SESSION_KEY = 'orcid_pending_next_url'
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
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 15 * 60
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5
LOGIN_RATE_LIMIT_BASE_LOCK_SECONDS = 60
LOGIN_RATE_LIMIT_MAX_LOCK_SECONDS = 30 * 60
LOGIN_RATE_LIMIT_STATE = {}
LOGIN_RATE_LIMIT_SCOPE = 'mainweb'
LOGIN_RATE_LIMIT_TABLE = 'auth_login_rate_limits'
LOGIN_RATE_LIMIT_STORAGE_READY = False

ORCID_ID_PATTERN = re.compile(r'(\d{4}-\d{4}-\d{4}-[\dX]{4})', re.IGNORECASE)
OAUTH_PLACEHOLDER_MARKERS = (
    'rotate_in_google_console_and_update',
    'rotate_in_orcid_console_and_update',
    'change-this',
    'your-google-client',
    'your-orcid-client',
    'your-client-id',
    'your-client-secret',
    'replace-me',
    'replace_with',
    'example-client',
)


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


def _load_iso_country_code_map():
    country_map = {}
    try:
        with open(ISO3166_TAB_PATH, encoding='utf-8') as iso_file:
            for line in iso_file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                code, country_name = line.split('\t', 1)
                normalized_code = (code or '').strip().upper()
                if normalized_code and normalized_code not in country_map:
                    country_map[normalized_code] = country_name.strip()
    except OSError:
        return {}
    return country_map


ISO_COUNTRY_NAME_MAP = _load_iso_country_name_map()
ISO_COUNTRY_CODE_MAP = _load_iso_country_code_map()


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


def _email_language(preferred=None):
    default_lang = 'en'
    if has_request_context():
        default_lang = normalize_notification_language(session.get('language') or 'en', default='en')
    return normalize_notification_language(preferred, default=default_lang)


def _email_text(lang, uz_text, ru_text, en_text):
    if lang == 'uz':
        return uz_text
    if lang == 'ru':
        return ru_text
    return en_text


def _email_multilingual_text(uz_text, ru_text, en_text, separator=' | ', include_labels=False):
    items = (
        ('UZ', str(uz_text or '').strip()),
        ('RU', str(ru_text or '').strip()),
        ('EN', str(en_text or '').strip()),
    )
    parts = []
    for label, text in items:
        if not text:
            continue
        if include_labels:
            parts.append(f'[{label}] {text}')
        else:
            parts.append(text)
    return separator.join(parts)


def _send_registration_welcome_email(user_row, is_google=False):
    email = (user_row or {}).get('email')
    if not email or not user_allows_email_notifications(user_row):
        return False

    lang = _email_language((user_row or {}).get('ui_language'))
    first_name = (user_row or {}).get('name') or _email_text(lang, 'Muallif', 'Автор', 'Author')
    body_lines = [
        _email_multilingual_text(
            "Endi profilingizni to'ldirib, yangi maqolalar yuborishingiz mumkin.",
            'Теперь вы можете заполнить профиль и отправлять новые статьи.',
            'You can now complete your profile and submit new articles.',
            include_labels=True,
        )
    ]
    if is_google:
        body_lines.append(
            _email_multilingual_text(
                'Google orqali kirish jurnaldagi akkauntingizga bog‘landi.',
                'Вход через Google был привязан к вашему аккаунту журнала.',
                'Google sign-in has been linked to your journal account.',
                include_labels=True,
            )
        )

    return send_notification_email(
        recipients=[email],
        subject=_email_multilingual_text(
            'Philology Matters platformasiga xush kelibsiz',
            'Добро пожаловать в Philology Matters',
            'Welcome to Philology Matters',
            separator=' | ',
        ),
        intro=_email_multilingual_text(
            f"Salom {first_name}, akkauntingiz muvaffaqiyatli faollashtirildi.",
            f"Здравствуйте, {first_name}! Ваш аккаунт успешно активирован.",
            f'Hello {first_name}, your account is now active.',
            include_labels=True,
        ),
        body_lines=body_lines,
        cta_url=url_for('app__dashboard_profile'),
        cta_label=_email_multilingual_text(
            'Dashboardni ochish',
            'Открыть кабинет',
            'Open dashboard',
            separator=' / ',
        ),
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
    return (request.remote_addr or '').strip()


def _login_rate_limit_key(email):
    return f"{_get_request_ip() or 'unknown'}::{(email or '').strip().lower()}"


def _ensure_login_rate_limit_storage():
    global LOGIN_RATE_LIMIT_STORAGE_READY
    if LOGIN_RATE_LIMIT_STORAGE_READY:
        return True

    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {LOGIN_RATE_LIMIT_TABLE} (
                scope TEXT NOT NULL,
                rate_key TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                first_attempt_at DOUBLE PRECISION NOT NULL DEFAULT 0,
                last_attempt_at DOUBLE PRECISION NOT NULL DEFAULT 0,
                locked_until DOUBLE PRECISION NOT NULL DEFAULT 0,
                updated_at BIGINT NOT NULL DEFAULT EXTRACT(epoch FROM now()),
                PRIMARY KEY (scope, rate_key)
            );
            """
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{LOGIN_RATE_LIMIT_TABLE}_cleanup "
            f"ON {LOGIN_RATE_LIMIT_TABLE}(scope, last_attempt_at, locked_until);"
        )
        dbc.conn.commit()
        cursor.close()
        LOGIN_RATE_LIMIT_STORAGE_READY = True
        return True
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return False


def _load_login_rate_limit_state(key):
    state = LOGIN_RATE_LIMIT_STATE.get(key)
    if not _ensure_login_rate_limit_storage():
        return state

    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"SELECT attempt_count, first_attempt_at, last_attempt_at, locked_until "
            f"FROM {LOGIN_RATE_LIMIT_TABLE} WHERE scope = %s AND rate_key = %s",
            (LOGIN_RATE_LIMIT_SCOPE, key),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return state
        return {
            'count': int(row[0] or 0),
            'first_attempt_at': float(row[1] or 0),
            'last_attempt_at': float(row[2] or 0),
            'locked_until': float(row[3] or 0),
        }
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return state


def _save_login_rate_limit_state(key, state):
    LOGIN_RATE_LIMIT_STATE[key] = state
    if not _ensure_login_rate_limit_storage():
        return

    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {LOGIN_RATE_LIMIT_TABLE}
                (scope, rate_key, attempt_count, first_attempt_at, last_attempt_at, locked_until, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scope, rate_key) DO UPDATE
            SET attempt_count = EXCLUDED.attempt_count,
                first_attempt_at = EXCLUDED.first_attempt_at,
                last_attempt_at = EXCLUDED.last_attempt_at,
                locked_until = EXCLUDED.locked_until,
                updated_at = EXCLUDED.updated_at
            """,
            (
                LOGIN_RATE_LIMIT_SCOPE,
                key,
                int(state.get('count') or 0),
                float(state.get('first_attempt_at') or 0),
                float(state.get('last_attempt_at') or 0),
                float(state.get('locked_until') or 0),
                int(time.time()),
            ),
        )
        dbc.conn.commit()
        cursor.close()
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass


def _delete_login_rate_limit_state(key):
    LOGIN_RATE_LIMIT_STATE.pop(key, None)
    if not _ensure_login_rate_limit_storage():
        return

    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            f"DELETE FROM {LOGIN_RATE_LIMIT_TABLE} WHERE scope = %s AND rate_key = %s",
            (LOGIN_RATE_LIMIT_SCOPE, key),
        )
        dbc.conn.commit()
        cursor.close()
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass


def _prune_login_rate_limits(now_ts):
    stale_before_ts = now_ts - LOGIN_RATE_LIMIT_WINDOW_SECONDS
    if _ensure_login_rate_limit_storage():
        try:
            cursor = dbc.conn.cursor()
            cursor.execute(
                f"DELETE FROM {LOGIN_RATE_LIMIT_TABLE} "
                f"WHERE scope = %s AND last_attempt_at < %s AND locked_until <= %s",
                (LOGIN_RATE_LIMIT_SCOPE, float(stale_before_ts), float(now_ts)),
            )
            dbc.conn.commit()
            cursor.close()
        except Exception:
            try:
                dbc.conn.rollback()
            except Exception:
                pass

    stale_keys = []
    for key, state in LOGIN_RATE_LIMIT_STATE.items():
        last_attempt_at = float(state.get('last_attempt_at') or 0)
        locked_until = float(state.get('locked_until') or 0)
        if (now_ts - last_attempt_at) > LOGIN_RATE_LIMIT_WINDOW_SECONDS and locked_until <= now_ts:
            stale_keys.append(key)
    for key in stale_keys:
        LOGIN_RATE_LIMIT_STATE.pop(key, None)


def _remaining_login_lock_seconds(email):
    now_ts = time.time()
    _prune_login_rate_limits(now_ts)
    state = _load_login_rate_limit_state(_login_rate_limit_key(email))
    if not state:
        return 0
    return max(0, int((state.get('locked_until') or 0) - now_ts))


def _record_login_failure(email):
    now_ts = time.time()
    _prune_login_rate_limits(now_ts)
    key = _login_rate_limit_key(email)
    state = _load_login_rate_limit_state(key)
    if not state or (now_ts - float(state.get('first_attempt_at') or 0)) > LOGIN_RATE_LIMIT_WINDOW_SECONDS:
        state = {
            'count': 0,
            'first_attempt_at': now_ts,
            'last_attempt_at': now_ts,
            'locked_until': 0,
        }

    state['count'] = int(state.get('count') or 0) + 1
    state['last_attempt_at'] = now_ts
    if state['count'] >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        lock_step = state['count'] - LOGIN_RATE_LIMIT_MAX_ATTEMPTS
        lock_seconds = min(
            LOGIN_RATE_LIMIT_BASE_LOCK_SECONDS * (2 ** lock_step),
            LOGIN_RATE_LIMIT_MAX_LOCK_SECONDS,
        )
        state['locked_until'] = now_ts + lock_seconds

    _save_login_rate_limit_state(key, state)
    return max(0, int((state.get('locked_until') or 0) - now_ts))


def _clear_login_failures(email):
    _delete_login_rate_limit_state(_login_rate_limit_key(email))


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


def _send_registration_code_email(email, first_name, code, language=None):
    ttl_minutes = _verification_ttl_minutes()
    lang = _email_language(language)
    intro_name = (first_name or '').strip() or _email_text(lang, "foydalanuvchi", "пользователь", "there")
    return send_notification_email(
        recipients=[email],
        subject=_email_multilingual_text(
            'Email manzilingizni tasdiqlang',
            'Подтвердите адрес электронной почты',
            'Verify your email address',
        ),
        intro=_email_multilingual_text(
            f"Salom {intro_name}, Philology Matters akkauntini yakunlash uchun ushbu koddan foydalaning.",
            f"Здравствуйте, {intro_name}! Используйте этот код, чтобы завершить создание аккаунта Philology Matters.",
            f'Hello {intro_name}, use this code to finish creating your Philology Matters account.',
            include_labels=True,
        ),
        details=[
            (
                _email_multilingual_text(
                    'Tasdiqlash kodi',
                    'Код подтверждения',
                    'Verification code',
                    separator=' / ',
                ),
                code,
            ),
            (
                _email_multilingual_text(
                    'Amal qilish muddati',
                    'Срок действия',
                    'Valid for',
                    separator=' / ',
                ),
                _email_multilingual_text(
                    f'{ttl_minutes} daqiqa',
                    f'{ttl_minutes} минут',
                    f'{ttl_minutes} minute(s)',
                    separator=' / ',
                ),
            ),
        ],
        body_lines=[
            _email_multilingual_text(
                "Akkauntingizni faollashtirish uchun ushbu bir martalik kodni tasdiqlash sahifasiga kiriting.",
                'Введите этот одноразовый код на странице подтверждения, чтобы активировать аккаунт.',
                'Enter this one-time code on the verification page to activate your account.',
                include_labels=True,
            ),
            _email_multilingual_text(
                "Agar bu kodni siz so'ramagan bo'lsangiz, ushbu xatni e'tiborsiz qoldirishingiz mumkin.",
                'Если вы не запрашивали этот код, просто проигнорируйте это письмо.',
                'If you did not request this code, you can safely ignore this email.',
                include_labels=True,
            ),
        ],
        cta_url=_registration_verify_url(email=email),
        cta_label=_email_multilingual_text(
            'Tasdiqlash sahifasini ochish',
            'Открыть страницу подтверждения',
            'Open verification page',
            separator=' / ',
        ),
        fail_silently=True,
    )


def _send_password_reset_code_email(email, first_name, code, language=None):
    ttl_minutes = _verification_ttl_minutes()
    lang = _email_language(language)
    intro_name = (first_name or '').strip() or _email_text(lang, "foydalanuvchi", "пользователь", "there")
    return send_notification_email(
        recipients=[email],
        subject=_email_multilingual_text(
            'Parolingizni tiklang',
            'Сбросьте пароль',
            'Reset your password',
        ),
        intro=_email_multilingual_text(
            f"Salom {intro_name}, Philology Matters parolingizni tiklash uchun ushbu koddan foydalaning.",
            f"Здравствуйте, {intro_name}! Используйте этот код для сброса пароля Philology Matters.",
            f'Hello {intro_name}, use this code to reset your Philology Matters password.',
            include_labels=True,
        ),
        details=[
            (
                _email_multilingual_text(
                    'Tasdiqlash kodi',
                    'Код подтверждения',
                    'Verification code',
                    separator=' / ',
                ),
                code,
            ),
            (
                _email_multilingual_text(
                    'Amal qilish muddati',
                    'Срок действия',
                    'Valid for',
                    separator=' / ',
                ),
                _email_multilingual_text(
                    f'{ttl_minutes} daqiqa',
                    f'{ttl_minutes} минут',
                    f'{ttl_minutes} minute(s)',
                    separator=' / ',
                ),
            ),
        ],
        body_lines=[
            _email_multilingual_text(
                'Yangi parol o‘rnatish uchun ushbu bir martalik kodni parolni tiklash sahifasiga kiriting.',
                'Введите этот одноразовый код на странице сброса пароля, чтобы задать новый пароль.',
                'Enter this one-time code on the password reset page to set a new password.',
                include_labels=True,
            ),
            _email_multilingual_text(
                "Agar bu so'rovni siz yubormagan bo'lsangiz, ushbu xatni e'tiborsiz qoldirishingiz mumkin.",
                'Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.',
                'If you did not request this code, you can safely ignore this email.',
                include_labels=True,
            ),
        ],
        cta_url=_password_reset_verify_url(email=email),
        cta_label=_email_multilingual_text(
            'Parolni tiklash sahifasini ochish',
            'Открыть страницу сброса пароля',
            'Open password reset page',
            separator=' / ',
        ),
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

    if not _send_registration_code_email(
        email,
        first_name,
        code,
        language=(registration_payload or {}).get('ui_language'),
    ):
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
        'ui_language': normalize_notification_language((user_row or {}).get('ui_language'), default='en'),
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

    if not _send_password_reset_code_email(
        email,
        first_name,
        code,
        language=(user_row or {}).get('ui_language'),
    ):
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

    if not _send_registration_code_email(
        email,
        first_name,
        code,
        language=(payload or {}).get('ui_language'),
    ):
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

    if not _send_password_reset_code_email(
        email,
        first_name,
        code,
        language=(payload or {}).get('ui_language'),
    ):
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
    first_name = sanitize_input(((registration_payload or {}).get('first_name') or '').strip())
    last_name = sanitize_input(((registration_payload or {}).get('last_name') or '').strip())
    father_name = sanitize_input(((registration_payload or {}).get('father_name') or '').strip())
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
        'accept_rules_time': current_time,
        'register_time': current_time,
        'created_at': current_time,
        'last_online': current_time,
    }
    user_columns = set(dbc.columns.get('users', []))
    if 'ui_language' in user_columns:
        create_data['ui_language'] = ui_language
    if 'is_hidden' in user_columns:
        create_data['is_hidden'] = False
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


def _looks_like_oauth_placeholder(value):
    normalized = str(value or '').strip().lower()
    if not normalized:
        return True
    return any(marker in normalized for marker in OAUTH_PLACEHOLDER_MARKERS)


def _normalized_social_email(value):
    email = str(value or '').strip().lower()
    if not email:
        return ''
    if email.endswith('@orcid.local'):
        return ''
    if not is_valid_email(email):
        return ''
    return email


def _has_same_social_email_identity(user_row, candidate_email):
    existing_email = _normalized_social_email((user_row or {}).get('email'))
    social_email = _normalized_social_email(candidate_email)
    return bool(existing_email and social_email and existing_email == social_email)


def _has_linked_orcid_identity(user_row, author_profile_row, orcid_id):
    normalized_orcid = _normalize_orcid_identifier(orcid_id)
    if not normalized_orcid:
        return False

    provider = str((user_row or {}).get('oauth_provider') or '').strip().lower()
    oauth_sub = _normalize_orcid_identifier((user_row or {}).get('oauth_sub'))
    if provider == 'orcid' and oauth_sub == normalized_orcid:
        return True

    profile_orcid = _normalize_orcid_identifier((author_profile_row or {}).get('orcid'))
    return bool(profile_orcid and profile_orcid == normalized_orcid)


def _normalize_roles_list(value):
    if isinstance(value, (list, tuple)):
        source = [str(item).strip().lower() for item in value]
    else:
        raw = str(value or '').strip()
        if not raw:
            return []
        if raw.startswith('{') and raw.endswith('}'):
            raw = raw[1:-1]
        source = [item.strip().strip('"').lower() for item in raw.split(',')]
    result = []
    for item in source:
        if not item or item in result:
            continue
        result.append(item)
    return result


def _normalize_iso_country_code(value):
    text = str(value or '').strip().upper()
    if len(text) == 2 and text.isalpha():
        return text
    return ''


def _iso_country_name_from_code(country_code):
    normalized_code = _normalize_iso_country_code(country_code)
    if not normalized_code:
        return ''
    return ISO_COUNTRY_CODE_MAP.get(normalized_code, '')


def _resolve_country_id_from_iso_country(country_code='', country_name=''):
    code = _normalize_iso_country_code(country_code)
    name = str(country_name or '').strip()
    if not code and name:
        code = _country_name_to_code(name)
    if not code and not name:
        return None

    normalized_name = _normalize_country_name(name)
    try:
        countries = dbc.fix_country.all().exec() or []
    except Exception:
        return None

    for country in countries:
        country_id = country.get('id')
        if country_id in (None, ''):
            continue
        variants = [
            country.get('name'),
            country.get('name_uz'),
            country.get('name_ru'),
        ]
        for variant in variants:
            variant_text = str(variant or '').strip()
            if not variant_text:
                continue
            if code and _country_name_to_code(variant_text) == code:
                return country_id
            if normalized_name and _normalize_country_name(variant_text) == normalized_name:
                return country_id
    return None


def _is_google_auth_available():
    has_credentials = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    if has_credentials:
        has_credentials = not (
            _looks_like_oauth_placeholder(settings.GOOGLE_CLIENT_ID)
            or _looks_like_oauth_placeholder(settings.GOOGLE_CLIENT_SECRET)
        )
    explicit_enabled = _as_optional_bool(settings.GOOGLE_AUTH_ENABLED)
    if explicit_enabled is None:
        return has_credentials
    return explicit_enabled and has_credentials


def _google_auth_config_issues():
    issues = []
    if not settings.GOOGLE_CLIENT_ID:
        issues.append('GOOGLE_CLIENT_ID')
    elif _looks_like_oauth_placeholder(settings.GOOGLE_CLIENT_ID):
        issues.append('GOOGLE_CLIENT_ID placeholder')
    if not settings.GOOGLE_CLIENT_SECRET:
        issues.append('GOOGLE_CLIENT_SECRET')
    elif _looks_like_oauth_placeholder(settings.GOOGLE_CLIENT_SECRET):
        issues.append('GOOGLE_CLIENT_SECRET placeholder')
    explicit_enabled = _as_optional_bool(settings.GOOGLE_AUTH_ENABLED)
    if explicit_enabled is False:
        issues.append('GOOGLE_AUTH_ENABLED=false')
    return issues


def _is_absolute_http_url(value):
    text = (value or '').strip()
    if not text:
        return False
    try:
        parsed = urlparse(text)
    except Exception:
        return False
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def _strip_inline_env_comment(value):
    text = str(value or '').strip()
    if not text:
        return ''
    # Support ".env" style inline comments like:
    # ORCID_BASE_URL=https://sandbox.orcid.org   # test
    return re.split(r'\s+#', text, maxsplit=1)[0].strip()


def _google_redirect_uri():
    configured = _strip_inline_env_comment(settings.GOOGLE_REDIRECT_URI)
    if configured and _is_absolute_http_url(configured):
        return configured
    if configured:
        logger.warning("Ignoring GOOGLE_REDIRECT_URI because it is not an absolute http(s) URL")

    app_base_url = _strip_inline_env_comment(settings.APP_BASE_URL).rstrip('/')
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
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
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
        # Keep account state flags deterministic for all newly created users.
        if 'is_hidden' in existing_columns or 'is_hidden' in missing_columns:
            cursor.execute("UPDATE users SET is_hidden = FALSE WHERE is_hidden IS NULL;")
            cursor.execute("ALTER TABLE users ALTER COLUMN is_hidden SET DEFAULT FALSE;")
            cursor.execute("ALTER TABLE users ALTER COLUMN is_hidden SET NOT NULL;")
        if 'is_blocked' in existing_columns or 'is_blocked' in missing_columns:
            cursor.execute("UPDATE users SET is_blocked = FALSE WHERE is_blocked IS NULL;")
            cursor.execute("ALTER TABLE users ALTER COLUMN is_blocked SET DEFAULT FALSE;")
            cursor.execute("ALTER TABLE users ALTER COLUMN is_blocked SET NOT NULL;")
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


def run_runtime_schema_syncs():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    _ensure_user_oauth_columns()


def _table_column_exists(cursor, cache, table_name, column_name):
    key = (table_name, column_name)
    if key in cache:
        return cache[key]
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        );
        """,
        (table_name, column_name),
    )
    exists = bool(cursor.fetchone()[0])
    cache[key] = exists
    return exists


def _merge_author_profile_references(cursor, column_cache, source_author_id, target_author_id):
    if not source_author_id or not target_author_id or source_author_id == target_author_id:
        return

    for table_name in ('submissions', 'publications'):
        if _table_column_exists(cursor, column_cache, table_name, 'main_author_id'):
            cursor.execute(
                f"UPDATE {table_name} SET main_author_id = %s WHERE main_author_id = %s",
                (target_author_id, source_author_id),
            )

    array_columns = (
        ('submissions', 'sub_author_ids'),
        ('publications', 'subauthor_ids'),
        ('publications', 'sub_author_ids'),
    )
    for table_name, column_name in array_columns:
        if not _table_column_exists(cursor, column_cache, table_name, column_name):
            continue
        cursor.execute(
            f"""
            UPDATE {table_name}
               SET {column_name} = array_replace({column_name}, %s, %s)
             WHERE {column_name} IS NOT NULL
               AND %s = ANY({column_name})
            """,
            (source_author_id, target_author_id, source_author_id),
        )


def _merge_author_profiles_for_users(cursor, column_cache, primary_user_id, secondary_user_id, now_ts):
    if not _table_column_exists(cursor, column_cache, 'author_profile', 'user_id'):
        return

    cursor.execute("SELECT * FROM author_profile WHERE user_id = %s ORDER BY id ASC", (primary_user_id,))
    primary_cols = [desc[0] for desc in cursor.description]
    primary_rows = [dict(zip(primary_cols, row)) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM author_profile WHERE user_id = %s ORDER BY id ASC", (secondary_user_id,))
    secondary_cols = [desc[0] for desc in cursor.description]
    secondary_rows = [dict(zip(secondary_cols, row)) for row in cursor.fetchall()]
    if not secondary_rows:
        return

    canonical = primary_rows[0] if primary_rows else secondary_rows.pop(0)
    canonical_id = int(canonical.get('id') or 0)
    if not canonical_id:
        return

    if int(canonical.get('user_id') or 0) != int(primary_user_id):
        if _table_column_exists(cursor, column_cache, 'author_profile', 'updated_at'):
            cursor.execute(
                "UPDATE author_profile SET user_id = %s, updated_at = %s WHERE id = %s",
                (primary_user_id, now_ts, canonical_id),
            )
        else:
            cursor.execute(
                "UPDATE author_profile SET user_id = %s WHERE id = %s",
                (primary_user_id, canonical_id),
            )
        canonical['user_id'] = primary_user_id

    merge_fields = (
        'name',
        'organization',
        'email',
        'position',
        'address_street',
        'address_country',
        'address_city',
        'address_zip',
        'phone',
        'orcid',
        'department',
    )

    for row in secondary_rows:
        source_id = int(row.get('id') or 0)
        if not source_id:
            continue

        patch = {}
        for field_name in merge_fields:
            source_value = row.get(field_name)
            source_text = str(source_value or '').strip()
            if not source_text:
                continue

            current_text = str(canonical.get(field_name) or '').strip()
            if field_name == 'email':
                source_email = _normalized_social_email(source_text)
                current_email = _normalized_social_email(current_text)
                if source_email and not current_email:
                    patch[field_name] = source_email
                continue

            if field_name == 'orcid':
                source_orcid = _normalize_orcid_identifier(source_text)
                current_orcid = _normalize_orcid_identifier(current_text)
                if source_orcid and not current_orcid:
                    patch[field_name] = source_orcid
                continue

            if not current_text:
                patch[field_name] = source_value

        if patch:
            if _table_column_exists(cursor, column_cache, 'author_profile', 'updated_at'):
                patch['updated_at'] = now_ts
            set_clause = ', '.join(f"{key} = %s" for key in patch)
            args = list(patch.values()) + [canonical_id]
            cursor.execute(f"UPDATE author_profile SET {set_clause} WHERE id = %s", args)
            canonical.update(patch)

        _merge_author_profile_references(cursor, column_cache, source_id, canonical_id)
        cursor.execute("DELETE FROM author_profile WHERE id = %s", (source_id,))


def _merge_user_accounts(primary_user, secondary_user, reason='account-link'):
    primary_id = int((primary_user or {}).get('id') or 0)
    secondary_id = int((secondary_user or {}).get('id') or 0)
    if not primary_id or not secondary_id or primary_id == secondary_id:
        return primary_user

    def _to_row(cursor, user_id):
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        fetched = cursor.fetchone()
        if not fetched:
            return None
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, fetched))

    column_cache = {}
    now_ts = int(time.time())
    try:
        with dbc._lock:
            cursor = dbc.conn.cursor()
            try:
                lock_first, lock_second = sorted([primary_id, secondary_id])
                cursor.execute(
                    "SELECT id FROM users WHERE id IN (%s, %s) ORDER BY id FOR UPDATE",
                    (lock_first, lock_second),
                )

                primary_row = _to_row(cursor, primary_id)
                secondary_row = _to_row(cursor, secondary_id)
                if not primary_row:
                    dbc.conn.rollback()
                    return secondary_user
                if not secondary_row:
                    dbc.conn.rollback()
                    return primary_row

                _merge_author_profiles_for_users(
                    cursor,
                    column_cache,
                    primary_user_id=primary_id,
                    secondary_user_id=secondary_id,
                    now_ts=now_ts,
                )

                user_ref_columns = (
                    ('author_profile', 'user_id'),
                    ('submissions', 'user_id'),
                    ('payments', 'user_id'),
                    ('user_doc_uploads', 'user_id'),
                    ('files', 'user_id'),
                    ('news', 'author_id'),
                    ('editor_assignments', 'editor_id'),
                    ('editor_assignments', 'assigned_by'),
                    ('editor_notifications', 'editor_id'),
                    ('role_notifications', 'target_user_id'),
                    ('role_notifications', 'actor_user_id'),
                    ('editorial_members', 'created_by'),
                    ('editorial_members', 'updated_by'),
                    ('email_templates', 'created_by'),
                    ('email_templates', 'updated_by'),
                )
                for table_name, column_name in user_ref_columns:
                    if not _table_column_exists(cursor, column_cache, table_name, column_name):
                        continue
                    cursor.execute(
                        f"UPDATE {table_name} SET {column_name} = %s WHERE {column_name} = %s",
                        (primary_id, secondary_id),
                    )

                users_columns = set(primary_row.keys()) | set(secondary_row.keys())
                patch = {}

                if 'email' in users_columns:
                    primary_email_raw = str(primary_row.get('email') or '').strip().lower()
                    secondary_email_raw = str(secondary_row.get('email') or '').strip().lower()
                    primary_email = _normalized_social_email(primary_email_raw)
                    secondary_email = _normalized_social_email(secondary_email_raw)
                    if secondary_email and not primary_email:
                        patch['email'] = secondary_email
                    elif not primary_email_raw and secondary_email_raw:
                        patch['email'] = secondary_email_raw

                for field_name in ('name', 'second_name', 'father_name', 'password', 'country_id', 'region', 'avatar', 'tariff_id', 'editor_specialization', 'ui_language', 'token', 'rolename'):
                    if field_name not in users_columns:
                        continue
                    primary_value = primary_row.get(field_name)
                    secondary_value = secondary_row.get(field_name)
                    if primary_value in (None, '', []) and secondary_value not in (None, '', []):
                        patch[field_name] = secondary_value

                for field_name in ('accept_rules_time', 'register_time', 'created_at'):
                    if field_name not in users_columns:
                        continue
                    primary_value = primary_row.get(field_name)
                    secondary_value = secondary_row.get(field_name)
                    if primary_value in (None, '', 0) and secondary_value not in (None, '', 0):
                        patch[field_name] = secondary_value
                    elif secondary_value not in (None, '', 0) and primary_value not in (None, '', 0):
                        if int(secondary_value) < int(primary_value):
                            patch[field_name] = secondary_value

                for field_name in ('last_online', 'oauth_last_login_at', 'subscription_end_date'):
                    if field_name not in users_columns:
                        continue
                    primary_value = primary_row.get(field_name)
                    secondary_value = secondary_row.get(field_name)
                    if primary_value in (None, '', 0) and secondary_value not in (None, '', 0):
                        patch[field_name] = secondary_value
                    elif secondary_value not in (None, '', 0) and primary_value not in (None, '', 0):
                        if int(secondary_value) > int(primary_value):
                            patch[field_name] = secondary_value

                if 'is_notify' in users_columns and bool(secondary_row.get('is_notify')) and not bool(primary_row.get('is_notify')):
                    patch['is_notify'] = True

                if 'roles' in users_columns:
                    merged_roles = []
                    for role_name in _normalize_roles_list(primary_row.get('roles')) + _normalize_roles_list(secondary_row.get('roles')):
                        if role_name not in merged_roles:
                            merged_roles.append(role_name)
                    if merged_roles and merged_roles != _normalize_roles_list(primary_row.get('roles')):
                        patch['roles'] = merged_roles

                if 'oauth_provider' in users_columns and 'oauth_sub' in users_columns:
                    primary_provider = str(primary_row.get('oauth_provider') or '').strip().lower()
                    secondary_provider = str(secondary_row.get('oauth_provider') or '').strip().lower()
                    primary_sub = str(primary_row.get('oauth_sub') or '').strip()
                    secondary_sub = str(secondary_row.get('oauth_sub') or '').strip()
                    if not primary_provider and secondary_provider:
                        patch['oauth_provider'] = secondary_provider
                        primary_provider = secondary_provider
                    if not primary_sub and secondary_sub and (not primary_provider or primary_provider == secondary_provider):
                        patch['oauth_sub'] = secondary_sub

                if 'oauth_email_verified' in users_columns:
                    if not primary_row.get('oauth_email_verified') and secondary_row.get('oauth_email_verified'):
                        patch['oauth_email_verified'] = True

                if patch:
                    set_clause = ', '.join(f"{key} = %s" for key in patch)
                    args = list(patch.values()) + [primary_id]
                    cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s", args)

                cursor.execute("DELETE FROM users WHERE id = %s", (secondary_id,))
                dbc.conn.commit()

                merged_row = _to_row(cursor, primary_id)
                if merged_row:
                    logger.info(
                        "Merged user accounts primary=%s secondary=%s reason=%s",
                        primary_id,
                        secondary_id,
                        reason,
                    )
                    return merged_row
                return primary_row
            except Exception:
                dbc.conn.rollback()
                raise
            finally:
                cursor.close()
    except Exception:
        logger.exception(
            "Failed to merge user accounts primary=%s secondary=%s reason=%s",
            primary_id,
            secondary_id,
            reason,
        )
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return primary_user


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

    email_rows = dbc.users.get(email=email).exec()
    email_user = email_rows[0] if email_rows else None
    if user and email_user and int(user.get('id') or 0) != int(email_user.get('id') or 0):
        # Prefer the real email account as the canonical identity and merge
        # provider-created duplicates into it.
        user = _merge_user_accounts(
            primary_user=email_user,
            secondary_user=user,
            reason='google-oauth-email-link',
        )
    elif not user and email_user:
        user = email_user

    now_ts = int(time.time())
    user_columns = set(dbc.columns.get('users', []))
    display_name = sanitize_input(profile.get('name', ''))
    first_name = sanitize_input(profile.get('given_name', ''))
    last_name = sanitize_input(profile.get('family_name', ''))
    avatar_url = (profile.get('picture') or '').strip() or None
    created_new_user = False

    if user:
        existing_provider = (user.get('oauth_provider') or '').strip().lower()
        existing_sub = str(user.get('oauth_sub') or '').strip()
        if existing_provider == 'google':
            if existing_sub and existing_sub != google_sub:
                flash('This email is already linked to another Google account.', 'error')
                return None
        elif existing_provider and existing_sub:
            if not _has_same_social_email_identity(user, email):
                flash('This account is already linked to a different sign-in provider.', 'error')
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
            'accept_rules_time': now_ts,
            'register_time': now_ts,
            'created_at': now_ts,
            'last_online': now_ts,
        }
        if 'ui_language' in user_columns:
            create_data['ui_language'] = normalize_notification_language(session.get('language') or 'en', default='en')
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
                created_new_user = True
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

    existing_provider = (user.get('oauth_provider') or '').strip().lower()
    existing_sub = str(user.get('oauth_sub') or '').strip()
    if existing_provider == 'google':
        if existing_sub and existing_sub != google_sub:
            flash('This email is already linked to another Google account.', 'error')
            return None
    elif existing_provider and existing_sub:
        if not _has_same_social_email_identity(user, email):
            flash('This account is already linked to a different sign-in provider.', 'error')
            return None

    update_data = {'last_online': now_ts}
    if 'roles' in user_columns:
        update_data['roles'] = hydrate_user_roles(user).get('roles')
    can_write_google_identity = (
        {'oauth_provider', 'oauth_sub'}.issubset(user_columns)
        and (not existing_provider or existing_provider == 'google')
    )
    if can_write_google_identity:
        update_data['oauth_provider'] = 'google'
        update_data['oauth_sub'] = google_sub
    if 'oauth_email_verified' in user_columns:
        update_data['oauth_email_verified'] = email_verified
    if 'oauth_last_login_at' in user_columns:
        update_data['oauth_last_login_at'] = now_ts
    if 'avatar' in user_columns and avatar_url and not user.get('avatar'):
        update_data['avatar'] = avatar_url
    if 'email' in user_columns and email:
        existing_email = (user.get('email') or '').strip().lower()
        if not existing_email or existing_email.endswith('@orcid.local'):
            update_data['email'] = email
    if 'name' in user_columns and first_name and not user.get('name'):
        update_data['name'] = first_name
    if 'second_name' in user_columns and last_name and not user.get('second_name'):
        update_data['second_name'] = last_name

    dbc.users.get(id=user['id']).update(**update_data).exec()
    reloaded = dbc.users.get(id=user['id']).exec()
    if not reloaded:
        flash('Unable to authorize with Google right now.', 'error')
        return None

    if intent == 'register' and created_new_user:
        _send_registration_welcome_email(reloaded[0], is_google=True)
        flash('Registration successful. You are now signed in with Google.', 'success')
    return reloaded[0]


def app__google_auth_start():
    _clear_google_oauth_session()
    if not _is_google_auth_available():
        issues = ', '.join(_google_auth_config_issues()) or 'unknown'
        current_app.logger.warning("Google auth unavailable: %s", issues)
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
        issues = ', '.join(_google_auth_config_issues()) or 'unknown'
        current_app.logger.warning("Google auth callback blocked: %s", issues)
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


def _is_orcid_auth_available():
    has_credentials = bool(settings.ORCID_CLIENT_ID and settings.ORCID_CLIENT_SECRET)
    if has_credentials:
        has_credentials = not (
            _looks_like_oauth_placeholder(settings.ORCID_CLIENT_ID)
            or _looks_like_oauth_placeholder(settings.ORCID_CLIENT_SECRET)
        )
    explicit_enabled = _as_optional_bool(settings.ORCID_AUTH_ENABLED)
    if explicit_enabled is None:
        return has_credentials
    return explicit_enabled and has_credentials


def _orcid_auth_config_issues():
    issues = []
    if not settings.ORCID_CLIENT_ID:
        issues.append('ORCID_CLIENT_ID')
    elif _looks_like_oauth_placeholder(settings.ORCID_CLIENT_ID):
        issues.append('ORCID_CLIENT_ID placeholder')
    if not settings.ORCID_CLIENT_SECRET:
        issues.append('ORCID_CLIENT_SECRET')
    elif _looks_like_oauth_placeholder(settings.ORCID_CLIENT_SECRET):
        issues.append('ORCID_CLIENT_SECRET placeholder')
    explicit_enabled = _as_optional_bool(settings.ORCID_AUTH_ENABLED)
    if explicit_enabled is False:
        issues.append('ORCID_AUTH_ENABLED=false')
    return issues


def _orcid_base_url():
    configured = _strip_inline_env_comment(settings.ORCID_BASE_URL).rstrip('/')
    if configured and _is_absolute_http_url(configured):
        return configured
    if configured:
        logger.warning("Ignoring ORCID_BASE_URL because it is not an absolute http(s) URL")
    return 'https://orcid.org'


def _orcid_public_api_base_url():
    base_url = _orcid_base_url()
    parsed = urlparse(base_url)
    scheme = parsed.scheme or 'https'
    host = (parsed.netloc or '').lower()
    if not host:
        return 'https://pub.orcid.org'
    if host.startswith('pub.'):
        return f'{scheme}://{host}'
    if host.endswith('sandbox.orcid.org'):
        return f'{scheme}://pub.sandbox.orcid.org'
    if host.endswith('orcid.org'):
        return f'{scheme}://pub.orcid.org'
    return f'{scheme}://{host}'


def _orcid_redirect_uri():
    configured = _strip_inline_env_comment(settings.ORCID_REDIRECT_URI)
    if configured and _is_absolute_http_url(configured):
        return configured
    if configured:
        logger.warning("Ignoring ORCID_REDIRECT_URI because it is not an absolute http(s) URL")

    app_base_url = _strip_inline_env_comment(settings.APP_BASE_URL).rstrip('/')
    if _is_absolute_http_url(app_base_url):
        return f"{app_base_url}/auth/orcid/callback"

    try:
        return url_for('app__orcid_callback', _external=True)
    except Exception:
        return url_for('app__orcid_callback', _external=True)


def _orcid_intent(raw_intent):
    return _google_intent(raw_intent)


def _clear_orcid_oauth_session():
    session.pop('orcid_oauth_state', None)
    session.pop('orcid_oauth_state_ts', None)
    session.pop('orcid_oauth_intent', None)
    session.pop('orcid_oauth_next_url', None)


def _clear_orcid_pending_email_completion():
    session.pop(ORCID_PENDING_PROFILE_SESSION_KEY, None)
    session.pop(ORCID_PENDING_INTENT_SESSION_KEY, None)
    session.pop(ORCID_PENDING_NEXT_URL_SESSION_KEY, None)


def _store_orcid_pending_email_completion(profile, intent, next_url=None):
    profile_payload = profile if isinstance(profile, dict) else {}
    allowed_fields = (
        'orcid',
        'name',
        'given_name',
        'family_name',
        'email',
        'country_code',
        'country_name',
        'organization',
        'department',
        'position',
        'employment_country_code',
        'employment_country_name',
        'employment_city',
    )
    clean_profile = {}
    for key in allowed_fields:
        value = profile_payload.get(key)
        clean_profile[key] = str(value or '').strip()

    session[ORCID_PENDING_PROFILE_SESSION_KEY] = clean_profile
    session[ORCID_PENDING_INTENT_SESSION_KEY] = _orcid_intent(intent)
    session[ORCID_PENDING_NEXT_URL_SESSION_KEY] = _sanitize_next_url(next_url)


def _normalize_orcid_identifier(value):
    if not value:
        return ''
    text = str(value).strip()
    if not text:
        return ''

    pattern_match = ORCID_ID_PATTERN.search(text)
    if pattern_match:
        return pattern_match.group(1).upper()

    compact = re.sub(r'[^0-9Xx]', '', text)
    if len(compact) == 16 and re.match(r'^\d{15}[\dXx]$', compact):
        compact = compact.upper()
        return f'{compact[0:4]}-{compact[4:8]}-{compact[8:12]}-{compact[12:16]}'
    return ''


def _orcid_placeholder_email(orcid_id):
    normalized = re.sub(r'[^0-9x]', '', str(orcid_id).lower())
    if not normalized:
        normalized = secrets.token_hex(8)
    return f'orcid-{normalized}@orcid.local'


def _build_orcid_auth_url(intent):
    state = secrets.token_urlsafe(32)
    session['orcid_oauth_state'] = state
    session['orcid_oauth_state_ts'] = int(time.time())
    session['orcid_oauth_intent'] = intent

    params = {
        'client_id': settings.ORCID_CLIENT_ID,
        'redirect_uri': _orcid_redirect_uri(),
        'response_type': 'code',
        'scope': settings.ORCID_SCOPE or '/authenticate',
        'state': state,
    }
    return f"{_orcid_base_url()}/oauth/authorize?{urlencode(params)}"


def _read_orcid_profile(code):
    timeout = max(settings.ORCID_REQUEST_TIMEOUT, 1)
    token_payload = {
        'code': code,
        'client_id': settings.ORCID_CLIENT_ID,
        'client_secret': settings.ORCID_CLIENT_SECRET,
        'redirect_uri': _orcid_redirect_uri(),
        'grant_type': 'authorization_code',
    }
    token_response = requests.post(
        f"{_orcid_base_url()}/oauth/token",
        data=token_payload,
        headers={'Accept': 'application/json'},
        timeout=timeout,
    )
    if token_response.status_code != 200:
        logger.warning("ORCID token exchange failed with status=%s", token_response.status_code)
        return None

    try:
        token_data = token_response.json()
    except ValueError:
        logger.warning("ORCID token response is not valid JSON")
        return None

    orcid_id = _normalize_orcid_identifier(
        token_data.get('orcid')
        or token_data.get('sub')
        or token_data.get('orcid_id')
    )
    if not orcid_id:
        logger.warning("ORCID token response did not include a valid ORCID iD")
        return None

    access_token = str(token_data.get('access_token') or '').strip()
    profile = {
        'orcid': orcid_id,
        'name': sanitize_input(token_data.get('name', '')),
        'given_name': '',
        'family_name': '',
        'email': '',
        'country_code': '',
        'country_name': '',
        'organization': '',
        'department': '',
        'position': '',
        'employment_country_code': '',
        'employment_country_name': '',
        'employment_city': '',
    }

    person_payload = _fetch_orcid_json_with_public_fallback(
        f'/v3.0/{orcid_id}/person',
        timeout=timeout,
        access_token=access_token,
    )
    if person_payload:
        for key, value in _extract_orcid_person_profile(person_payload).items():
            if value and not profile.get(key):
                profile[key] = value

    employment_payload = _fetch_orcid_json_with_public_fallback(
        f'/v3.0/{orcid_id}/employments',
        timeout=timeout,
        access_token=access_token,
    )
    if employment_payload:
        for key, value in _extract_orcid_employment_profile(employment_payload).items():
            if value and not profile.get(key):
                profile[key] = value

    if not profile.get('country_name'):
        profile['country_name'] = _iso_country_name_from_code(profile.get('country_code'))
    if not profile.get('employment_country_name'):
        profile['employment_country_name'] = _iso_country_name_from_code(profile.get('employment_country_code'))

    if not profile.get('name'):
        fallback_name = ' '.join(
            part for part in [
                profile.get('given_name'),
                profile.get('family_name'),
            ] if part
        ).strip()
        if fallback_name:
            profile['name'] = fallback_name

    return {
        **profile,
    }


def _fetch_orcid_json(url, timeout, access_token=None):
    headers = {'Accept': 'application/json'}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code != 200:
        logger.info('ORCID data request failed url=%s status=%s', url, response.status_code)
        return None
    try:
        return response.json()
    except ValueError:
        logger.warning('ORCID data response is not valid JSON for url=%s', url)
        return None


def _fetch_orcid_json_with_public_fallback(path, timeout, access_token=None):
    base_url = _orcid_base_url().rstrip('/')
    public_url = _orcid_public_api_base_url().rstrip('/')
    path_part = str(path or '').strip()
    if not path_part.startswith('/'):
        path_part = f'/{path_part}'

    candidates = []
    if base_url:
        candidates.append((f'{base_url}{path_part}', access_token))
    if public_url:
        candidates.append((f'{public_url}{path_part}', access_token))
        candidates.append((f'{public_url}{path_part}', None))

    seen = set()
    for candidate_url, candidate_token in candidates:
        key = (candidate_url, bool(candidate_token))
        if key in seen:
            continue
        seen.add(key)
        try:
            payload = _fetch_orcid_json(candidate_url, timeout=timeout, access_token=candidate_token)
        except requests.RequestException:
            logger.info('ORCID data request failed for url=%s', candidate_url)
            continue
        if payload:
            return payload
    return None


def _extract_orcid_person_profile(person_payload):
    payload = person_payload if isinstance(person_payload, dict) else {}
    profile = {
        'name': '',
        'given_name': '',
        'family_name': '',
        'email': '',
        'country_code': '',
        'country_name': '',
    }

    name_data = payload.get('name') if isinstance(payload.get('name'), dict) else {}
    given_name = sanitize_input(((name_data.get('given-names') or {}).get('value')) if isinstance(name_data.get('given-names'), dict) else '')
    family_name = sanitize_input(((name_data.get('family-name') or {}).get('value')) if isinstance(name_data.get('family-name'), dict) else '')
    full_name = sanitize_input(' '.join(part for part in [given_name, family_name] if part).strip())
    if full_name:
        profile['name'] = full_name
    profile['given_name'] = given_name
    profile['family_name'] = family_name

    emails_data = payload.get('emails') if isinstance(payload.get('emails'), dict) else {}
    email_entries = emails_data.get('email') if isinstance(emails_data.get('email'), list) else []
    email_candidates = []
    for item in email_entries:
        if not isinstance(item, dict):
            continue
        value = str(item.get('email') or '').strip().lower()
        if not value:
            continue
        score = (
            1 if item.get('verified') else 0,
            1 if item.get('primary') else 0,
        )
        email_candidates.append((score, value))
    if email_candidates:
        email_candidates.sort(key=lambda pair: pair[0], reverse=True)
        profile['email'] = email_candidates[0][1]

    addresses_data = payload.get('addresses') if isinstance(payload.get('addresses'), dict) else {}
    address_entries = addresses_data.get('address') if isinstance(addresses_data.get('address'), list) else []
    for item in address_entries:
        if not isinstance(item, dict):
            continue
        country_block = item.get('country')
        country_value = ''
        if isinstance(country_block, dict):
            country_value = country_block.get('value') or ''
        else:
            country_value = country_block or ''
        country_code = _normalize_iso_country_code(country_value)
        if country_code:
            profile['country_code'] = country_code
            profile['country_name'] = _iso_country_name_from_code(country_code)
            break

    return profile


def _extract_orcid_employment_profile(employment_payload):
    payload = employment_payload if isinstance(employment_payload, dict) else {}
    result = {
        'organization': '',
        'department': '',
        'position': '',
        'employment_country_code': '',
        'employment_country_name': '',
        'employment_city': '',
    }

    summaries = []
    top_level = payload.get('employment-summary')
    if isinstance(top_level, list):
        summaries.extend(item for item in top_level if isinstance(item, dict))

    if not summaries:
        affiliation_groups = payload.get('affiliation-group')
        if isinstance(affiliation_groups, list):
            for group in affiliation_groups:
                if not isinstance(group, dict):
                    continue
                group_summaries = group.get('summaries') if isinstance(group.get('summaries'), list) else []
                for item in group_summaries:
                    if not isinstance(item, dict):
                        continue
                    summary = item.get('employment-summary')
                    if isinstance(summary, dict):
                        summaries.append(summary)

    if not summaries:
        return result

    first_summary = summaries[0]
    result['department'] = sanitize_input(first_summary.get('department-name', ''))
    result['position'] = sanitize_input(first_summary.get('role-title', ''))

    organization_data = first_summary.get('organization') if isinstance(first_summary.get('organization'), dict) else {}
    result['organization'] = sanitize_input(organization_data.get('name', ''))

    address_data = organization_data.get('address') if isinstance(organization_data.get('address'), dict) else {}
    result['employment_city'] = sanitize_input(address_data.get('city', ''))
    country_code = _normalize_iso_country_code(address_data.get('country'))
    if country_code:
        result['employment_country_code'] = country_code
        result['employment_country_name'] = _iso_country_name_from_code(country_code)

    return result


def _resolve_orcid_user(profile):
    orcid_id = _normalize_orcid_identifier(profile.get('orcid'))
    if not orcid_id:
        return None, None, None, None, ''

    user_columns = set(dbc.columns.get('users', []))
    has_oauth_identity_cols = {'oauth_provider', 'oauth_sub'}.issubset(user_columns)
    # ORCID may omit email depending on scope/privacy. Keep a best-effort
    # resolver so existing profile emails can replace @orcid.local placeholders.
    profile_email = _normalized_social_email(profile.get('email'))

    user = None
    author_profile = None

    if has_oauth_identity_cols:
        by_sub = dbc.users.get(oauth_provider='orcid', oauth_sub=orcid_id).exec()
        if by_sub:
            user = by_sub[0]

    if not user:
        author_matches = dbc.author_profile.get(orcid=orcid_id).exec()
        if author_matches:
            author_profile = next((row for row in author_matches if row.get('user_id')), None) or author_matches[0]
            linked_user_id = author_profile.get('user_id')
            if linked_user_id:
                linked_user = dbc.users.get(id=linked_user_id).exec()
                if linked_user:
                    user = linked_user[0]

    if user and not author_profile:
        by_user_profile = dbc.author_profile.get(user_id=user.get('id')).exec()
        if by_user_profile:
            author_profile = by_user_profile[0]

    author_profile_email = _normalized_social_email(author_profile.get('email')) if author_profile else ''
    if not profile_email and author_profile_email:
        profile_email = author_profile_email

    if not user and profile_email:
        by_email = dbc.users.get(email=profile_email).exec()
        if by_email:
            user = by_email[0]
            if not author_profile:
                by_user_profile = dbc.author_profile.get(user_id=user.get('id')).exec()
                if by_user_profile:
                    author_profile = by_user_profile[0]

    fallback_email = profile_email or _orcid_placeholder_email(orcid_id)
    return user, orcid_id, author_profile, fallback_email, profile_email


def _sync_orcid_author_profile(user_row, orcid_id, display_name='', profile=None):
    if not user_row or not orcid_id:
        return True

    user_id = user_row.get('id')
    if not user_id:
        return True

    now_ts = int(time.time())
    author_columns = set(dbc.columns.get('author_profile', []))
    profile_data = profile if isinstance(profile, dict) else {}
    user_email = _normalized_social_email(user_row.get('email'))
    profile_email = _normalized_social_email(profile_data.get('email'))
    preferred_email = profile_email or user_email

    given_name = sanitize_input(profile_data.get('given_name', ''))
    family_name = sanitize_input(profile_data.get('family_name', ''))
    resolved_display_name = sanitize_input(display_name or profile_data.get('name', ''))
    if not resolved_display_name:
        resolved_display_name = sanitize_input(' '.join(part for part in [given_name, family_name] if part).strip())
    if not resolved_display_name:
        resolved_display_name = sanitize_input(user_row.get('name') or '')

    organization = sanitize_input(profile_data.get('organization', ''))
    department = sanitize_input(profile_data.get('department', ''))
    position = sanitize_input(profile_data.get('position', ''))
    employment_city = sanitize_input(profile_data.get('employment_city', ''))
    employment_country = sanitize_input(
        profile_data.get('employment_country_name')
        or _iso_country_name_from_code(profile_data.get('employment_country_code'))
        or profile_data.get('country_name')
        or _iso_country_name_from_code(profile_data.get('country_code'))
    )

    def _profile_update_payload(existing_row, include_user_id=False):
        payload = {}
        existing_orcid = _normalize_orcid_identifier(existing_row.get('orcid'))
        if existing_orcid and existing_orcid != orcid_id:
            return None
        if not existing_orcid:
            payload['orcid'] = orcid_id
        if include_user_id and not existing_row.get('user_id'):
            payload['user_id'] = user_id
        if resolved_display_name and not existing_row.get('name'):
            payload['name'] = resolved_display_name
        if preferred_email and not existing_row.get('email'):
            payload['email'] = preferred_email
        enrichment_fields = {
            'organization': organization,
            'department': department,
            'position': position,
            'address_city': employment_city,
            'address_country': employment_country,
        }
        for field_name, field_value in enrichment_fields.items():
            if field_name not in author_columns:
                continue
            if field_value and not existing_row.get(field_name):
                payload[field_name] = field_value
        if 'updated_at' in author_columns:
            payload['updated_at'] = now_ts
        return payload

    by_user = dbc.author_profile.get(user_id=user_id).exec()
    if by_user:
        payload = _profile_update_payload(by_user[0], include_user_id=False)
        if payload is None:
            flash('Your profile is linked to a different ORCID iD. Please contact support.', 'error')
            return False
        if payload:
            dbc.author_profile.get(id=by_user[0]['id']).update(**payload).exec()
        return True

    by_orcid = dbc.author_profile.get(orcid=orcid_id).exec()
    if by_orcid:
        candidate = next((row for row in by_orcid if not row.get('user_id') or row.get('user_id') == user_id), by_orcid[0])
        candidate_user_id = candidate.get('user_id')
        if candidate_user_id and candidate_user_id != user_id:
            flash('This ORCID iD is already linked to another account.', 'error')
            return False

        payload = _profile_update_payload(candidate, include_user_id=True)
        if payload is None:
            flash('This ORCID iD is already linked to another account.', 'error')
            return False
        if payload:
            dbc.author_profile.get(id=candidate['id']).update(**payload).exec()
        return True

    create_data = {
        'user_id': user_id,
        'orcid': orcid_id,
        'name': resolved_display_name or f'ORCID {orcid_id}',
        'email': preferred_email or None,
    }
    if 'organization' in author_columns and organization:
        create_data['organization'] = organization
    if 'department' in author_columns and department:
        create_data['department'] = department
    if 'position' in author_columns and position:
        create_data['position'] = position
    if 'address_city' in author_columns and employment_city:
        create_data['address_city'] = employment_city
    if 'address_country' in author_columns and employment_country:
        create_data['address_country'] = employment_country
    if 'created_at' in author_columns:
        create_data['created_at'] = now_ts
    if 'updated_at' in author_columns:
        create_data['updated_at'] = now_ts
    dbc.author_profile.add(**create_data).exec()
    return True


def _create_or_update_orcid_user(profile, intent):
    user, orcid_id, author_profile, fallback_email, profile_email = _resolve_orcid_user(profile)
    if not orcid_id:
        flash('ORCID did not return a valid ORCID iD.', 'error')
        return None

    has_linked_orcid_identity = _has_linked_orcid_identity(user, author_profile, orcid_id)

    now_ts = int(time.time())
    user_columns = set(dbc.columns.get('users', []))
    display_name = sanitize_input(profile.get('name', ''))
    given_name = sanitize_input(profile.get('given_name', ''))
    family_name = sanitize_input(profile.get('family_name', ''))
    if not display_name:
        display_name = sanitize_input(' '.join(part for part in [given_name, family_name] if part).strip())
    if not display_name and author_profile:
        display_name = sanitize_input(author_profile.get('name', ''))
    # Keep oauth_email_verified tied only to ORCID-provided email payload.
    email_verified = bool(_normalized_social_email(profile.get('email')))
    resolved_country_id = _resolve_country_id_from_iso_country(
        country_code=profile.get('employment_country_code') or profile.get('country_code'),
        country_name=profile.get('employment_country_name') or profile.get('country_name'),
    )
    created_new_user = False

    if profile_email:
        email_rows = dbc.users.get(email=profile_email).exec()
        email_user = email_rows[0] if email_rows else None
        if user and email_user and int(user.get('id') or 0) != int(email_user.get('id') or 0):
            user = _merge_user_accounts(
                primary_user=email_user,
                secondary_user=user,
                reason='orcid-oauth-email-link',
            )
        elif not user and email_user:
            user = email_user

    if user:
        existing_provider = (user.get('oauth_provider') or '').strip().lower()
        existing_sub = _normalize_orcid_identifier(user.get('oauth_sub'))
        if existing_provider == 'orcid':
            if existing_sub and existing_sub != orcid_id:
                flash('This account is already linked to another ORCID iD.', 'error')
                return None
        elif existing_provider and existing_sub:
            if not has_linked_orcid_identity and not _has_same_social_email_identity(user, profile_email):
                flash('This account is already linked to a different sign-in provider.', 'error')
                return None

    if user and (user.get('is_blocked') or user.get('is_hidden')):
        flash('Your account is blocked. Please contact support.', 'error')
        return None

    if not user:
        display_tail = orcid_id[-4:] if len(orcid_id) >= 4 else orcid_id
        create_data = {
            'name': given_name or display_name or f'ORCID {display_tail}',
            'second_name': family_name or None,
            'father_name': None,
            'email': fallback_email,
            'password': None,
            'country_id': resolved_country_id,
            'rolename': 'user',
            'is_blocked': False,
            'is_notify': False,
            'accept_rules_time': now_ts,
            'register_time': now_ts,
            'created_at': now_ts,
            'last_online': now_ts,
        }
        if 'ui_language' in user_columns:
            create_data['ui_language'] = normalize_notification_language(session.get('language') or 'en', default='en')
        if 'is_hidden' in user_columns:
            create_data['is_hidden'] = False
        if 'roles' in user_columns:
            create_data['roles'] = build_user_roles(AUTHOR_ROLE, include_author_role=True)
        if {'oauth_provider', 'oauth_sub'}.issubset(user_columns):
            create_data['oauth_provider'] = 'orcid'
            create_data['oauth_sub'] = orcid_id
        if 'oauth_email_verified' in user_columns:
            create_data['oauth_email_verified'] = email_verified or None
        if 'oauth_last_login_at' in user_columns:
            create_data['oauth_last_login_at'] = now_ts

        try:
            created_rows = dbc.users.add(**create_data).exec()
            if created_rows:
                user = created_rows[0]
                created_new_user = True
            else:
                created_lookup = []
                if {'oauth_provider', 'oauth_sub'}.issubset(user_columns):
                    created_lookup = dbc.users.get(oauth_provider='orcid', oauth_sub=orcid_id).exec()
                if not created_lookup and fallback_email:
                    created_lookup = dbc.users.get(email=fallback_email).exec()
                user = created_lookup[0] if created_lookup else None
        except Exception:
            # Race-safe fallback for concurrent ORCID sign-up attempts.
            created_lookup = []
            if {'oauth_provider', 'oauth_sub'}.issubset(user_columns):
                created_lookup = dbc.users.get(oauth_provider='orcid', oauth_sub=orcid_id).exec()
            if not created_lookup and fallback_email:
                created_lookup = dbc.users.get(email=fallback_email).exec()
            user = created_lookup[0] if created_lookup else None

    if not user:
        flash('Unable to authorize with ORCID right now.', 'error')
        return None

    existing_provider = (user.get('oauth_provider') or '').strip().lower()
    existing_sub = _normalize_orcid_identifier(user.get('oauth_sub'))
    if existing_provider == 'orcid':
        if existing_sub and existing_sub != orcid_id:
            flash('This account is already linked to another ORCID iD.', 'error')
            return None
    elif existing_provider and existing_sub:
        if not has_linked_orcid_identity and not _has_same_social_email_identity(user, profile_email):
            flash('This account is already linked to a different sign-in provider.', 'error')
            return None

    update_data = {'last_online': now_ts}
    if 'roles' in user_columns:
        update_data['roles'] = hydrate_user_roles(user).get('roles')
    can_write_orcid_identity = (
        {'oauth_provider', 'oauth_sub'}.issubset(user_columns)
        and (not existing_provider or existing_provider == 'orcid')
    )
    if can_write_orcid_identity:
        update_data['oauth_provider'] = 'orcid'
        update_data['oauth_sub'] = orcid_id
    if 'oauth_email_verified' in user_columns:
        update_data['oauth_email_verified'] = email_verified or None
    if 'oauth_last_login_at' in user_columns:
        update_data['oauth_last_login_at'] = now_ts
    if 'name' in user_columns and (given_name or display_name) and not user.get('name'):
        update_data['name'] = given_name or display_name
    if 'second_name' in user_columns and family_name and not user.get('second_name'):
        update_data['second_name'] = family_name
    if 'email' in user_columns:
        existing_email = (user.get('email') or '').strip().lower()
        if profile_email and (not existing_email or existing_email.endswith('@orcid.local')):
            update_data['email'] = profile_email
    if 'country_id' in user_columns and resolved_country_id and not user.get('country_id'):
        update_data['country_id'] = resolved_country_id

    try:
        dbc.users.get(id=user['id']).update(**update_data).exec()
    except Exception:
        # Some production schemas may enforce stricter email constraints.
        # Retry without email update so ORCID login itself does not fail.
        if 'email' in update_data:
            update_data.pop('email', None)
            dbc.users.get(id=user['id']).update(**update_data).exec()
        else:
            raise
    reloaded = dbc.users.get(id=user['id']).exec()
    if not reloaded:
        flash('Unable to authorize with ORCID right now.', 'error')
        return None

    if not _sync_orcid_author_profile(reloaded[0], orcid_id, display_name=display_name, profile=profile):
        return None

    if intent == 'register' and created_new_user:
        _send_registration_welcome_email(reloaded[0], is_google=False)
        flash('Registration successful. You are now signed in with ORCID.', 'success')
    return reloaded[0]


def app__orcid_auth_start():
    _clear_orcid_oauth_session()
    _clear_orcid_pending_email_completion()
    intent = _orcid_intent(request.args.get('intent'))
    fallback = _oauth_fallback_endpoint(intent)
    if not _is_orcid_auth_available():
        issues = ', '.join(_orcid_auth_config_issues()) or 'unknown'
        current_app.logger.warning("ORCID auth unavailable: %s", issues)
        flash('ORCID authentication is not configured yet.', 'error')
        return redirect(url_for(fallback))

    next_url = _sanitize_next_url(request.args.get('next'))
    if next_url:
        session['orcid_oauth_next_url'] = next_url
    auth_url = _build_orcid_auth_url(intent)
    return redirect(auth_url)


def app__orcid_callback():
    intent = _orcid_intent(session.get('orcid_oauth_intent'))
    fallback = _oauth_fallback_endpoint(intent)

    expected_state = session.get('orcid_oauth_state')
    state_ts = int(session.get('orcid_oauth_state_ts') or 0)
    next_url = _sanitize_next_url(session.get('orcid_oauth_next_url'))
    _clear_orcid_oauth_session()

    if not _is_orcid_auth_available():
        issues = ', '.join(_orcid_auth_config_issues()) or 'unknown'
        current_app.logger.warning("ORCID auth callback blocked: %s", issues)
        flash('ORCID authentication is not configured yet.', 'error')
        return redirect(url_for(fallback))

    oauth_error = request.args.get('error')
    if oauth_error:
        oauth_error_description = (request.args.get('error_description') or '').strip()
        if oauth_error_description:
            flash(f'ORCID authorization failed: {oauth_error} ({oauth_error_description})', 'error')
        else:
            flash(f'ORCID authorization failed: {oauth_error}', 'error')
        return redirect(url_for(fallback))

    state = request.args.get('state', '')
    if not expected_state or state != expected_state:
        flash('Invalid ORCID authorization state. Please try again.', 'error')
        return redirect(url_for(fallback))

    if state_ts and (int(time.time()) - state_ts > ORCID_OAUTH_STATE_TTL):
        flash('ORCID authorization timed out. Please try again.', 'error')
        return redirect(url_for(fallback))

    code = request.args.get('code', '')
    if not code:
        flash('ORCID authorization code was not received.', 'error')
        return redirect(url_for(fallback))

    try:
        profile = _read_orcid_profile(code)
        if not profile:
            flash('ORCID sign-in failed. Please try again.', 'error')
            return redirect(url_for(fallback))

        _, _, _, _, resolved_profile_email = _resolve_orcid_user(profile)
        if not resolved_profile_email:
            _clear_orcid_pending_email_completion()
            _store_orcid_pending_email_completion(profile, intent, next_url=next_url)
            flash(
                'ORCID email is not public for this account. Please enter your email to continue.',
                'warning'
            )
            return redirect(url_for('app__orcid_complete_email'))

        user = _create_or_update_orcid_user(profile, intent)
        if not user:
            return redirect(url_for(fallback))

        _clear_orcid_pending_email_completion()
        _set_user_session(user)
        return _post_auth_redirect(user, next_url=next_url)
    except requests.RequestException:
        flash('ORCID service is temporarily unavailable. Please try again.', 'error')
        return redirect(url_for(fallback))
    except Exception:
        current_app.logger.error("ORCID OAuth callback error: %s", traceback.format_exc())
        flash('System error. Please try again later.', 'error')
        return redirect(url_for(fallback))


def app__orcid_complete_email():
    pending_profile = session.get(ORCID_PENDING_PROFILE_SESSION_KEY)
    intent = _orcid_intent(session.get(ORCID_PENDING_INTENT_SESSION_KEY))
    next_url = _sanitize_next_url(session.get(ORCID_PENDING_NEXT_URL_SESSION_KEY))
    fallback = _oauth_fallback_endpoint(intent)

    if not isinstance(pending_profile, dict) or not _normalize_orcid_identifier(pending_profile.get('orcid')):
        _clear_orcid_pending_email_completion()
        flash('ORCID session expired. Please sign in again.', 'error')
        return redirect(url_for(fallback))

    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', '')).strip().lower()
        if not email or not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template(
                'auth/orcid_email.html',
                pending_email=email,
                pending_orcid=_normalize_orcid_identifier(pending_profile.get('orcid')),
            )

        profile = dict(pending_profile)
        profile['email'] = email
        user = _create_or_update_orcid_user(profile, intent)
        if not user:
            return render_template(
                'auth/orcid_email.html',
                pending_email=email,
                pending_orcid=_normalize_orcid_identifier(pending_profile.get('orcid')),
            )

        _clear_orcid_pending_email_completion()
        _set_user_session(user)
        return _post_auth_redirect(user, next_url=next_url)

    return render_template(
        'auth/orcid_email.html',
        pending_email='',
        pending_orcid=_normalize_orcid_identifier(pending_profile.get('orcid')),
    )


def app__login():
    if request.method == 'POST':
        next_url = _sanitize_next_url(request.form.get('next') or request.args.get('next'))
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        login_redirect = url_for('app__login', next=next_url) if next_url else url_for('app__login')

        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(login_redirect)

        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(login_redirect)

        remaining_lock = _remaining_login_lock_seconds(email)
        if remaining_lock > 0:
            flash(f'Too many failed attempts. Please try again in {remaining_lock} seconds.', 'error')
            return redirect(login_redirect)

        try:
            _user = dbc.users.get(email=email).exec()
            if _user:
                user = _normalize_user_for_session(_user[0])

                if user.get('is_blocked') or user.get('is_hidden'):
                    _record_login_failure(email)
                    flash('Your account is blocked. Please contact support.', 'error')
                    return redirect(login_redirect)

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
                    _clear_login_failures(email)
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

            remaining_lock = _record_login_failure(email)
            if remaining_lock > 0:
                flash(f'Too many failed attempts. Please try again in {remaining_lock} seconds.', 'error')
                return redirect(login_redirect)
            flash('Invalid login or password. Try again.', 'error')
            return redirect(login_redirect)

        except Exception:
            logger.exception('Login failed for email=%s', email)
            flash('System error. Please try again later.', 'error')
            return redirect(login_redirect)

    next_url = _sanitize_next_url(request.args.get('next'))
    return render_template(
        'auth/login.html',
        google_auth_enabled=_is_google_auth_available(),
        orcid_auth_enabled=_is_orcid_auth_available(),
        next_url=next_url,
    )


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
    return render_template(
        'auth/register.html',
        fix_country=countries,
        google_auth_enabled=_is_google_auth_available(),
        orcid_auth_enabled=_is_orcid_auth_available(),
    )


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

        try:
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
        except Exception:
            current_app.logger.error(f"Registration verification error: {traceback.format_exc()}")
            flash(
                t('registration_failed')
                if t('registration_failed') != 'registration_failed'
                else 'Registration failed. Please try again.',
                'error'
            )
            return redirect(url_for('app__register_verify', email=pending_email))

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
    _clear_orcid_oauth_session()
    _clear_orcid_pending_email_completion()
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
    app.add_url_rule('/auth/orcid', view_func=not_auth_only(app__orcid_auth_start), methods=['GET'])
    app.add_url_rule('/api/auth/orcid', endpoint='app__orcid_auth_start_api', view_func=not_auth_only(app__orcid_auth_start), methods=['GET'])
    app.add_url_rule('/auth/orcid/callback', view_func=not_auth_only(app__orcid_callback), methods=['GET'])
    app.add_url_rule('/auth/orcid/callback/', endpoint='app__orcid_callback_slash', view_func=not_auth_only(app__orcid_callback), methods=['GET'])
    app.add_url_rule('/api/auth/orcid/callback', endpoint='app__orcid_callback_api', view_func=not_auth_only(app__orcid_callback), methods=['GET'])
    app.add_url_rule('/api/auth/orcid/callback/', endpoint='app__orcid_callback_api_slash', view_func=not_auth_only(app__orcid_callback), methods=['GET'])
    app.add_url_rule('/auth/orcid/complete-email', view_func=not_auth_only(app__orcid_complete_email), methods=['GET', 'POST'])
    app.add_url_rule('/logout', view_func=app__logout, methods=['POST'])
