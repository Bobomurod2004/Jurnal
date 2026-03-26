# flake8: noqa
import os
import time
import json
from werkzeug.utils import secure_filename
from flask import request, jsonify, session, url_for
from extensions import dbc
from modules.translate import t, translate, clear_translations_cache
import settings
from utils.auth import author_login_required, login_required, is_strong_password, is_valid_email
from utils.emailer import send_notification_email
from utils.notifications import (
    current_notification_language,
    localized_texts,
    normalize_notification_language,
    prepare_notification_content,
    user_allows_email_notifications,
)
from utils.private_uploads import build_private_upload_ref, upload_access_url
from utils.roles import hydrate_user_roles, user_has_role
from utils.uploads import allowed_file
from werkzeug.security import generate_password_hash, check_password_hash


SUBMISSION_TRACK_ABSTRACT_WORD_LIMITS = {
    'masters': (150, 200),
    'phd': (250, 300),
    'teacher': (250, 300)
}

SUBMISSION_TRACK_WORD_COUNT_LIMITS = {
    'masters': (2500, 3000),
    'phd': (4000, 7000),
    'teacher': (4000, 7000)
}

SUBMISSION_WORKFLOW_STAGES = (
    'waiting',
    'technical_check',
    'anti_plagiarism',
    'in_review',
    'recommended',
    'payment',
    'published',
    'rejected'
)

SUBMISSION_EXTRA_COLUMN_TYPES = {
    'submission_track': 'text',
    'title_uz': 'text',
    'title_ru': 'text',
    'title_en': 'text',
    'title_other': 'text',
    'abstract_uz': 'text',
    'abstract_ru': 'text',
    'abstract_en': 'text',
    'abstract_other': 'text',
    'other_language_name': 'text',
    'workflow_stage': 'text',
    'assigned_admin_id': 'integer',
    'anti_plagiarism_file': 'text',
    'anti_plagiarism_checked_at': 'bigint',
    'anti_plagiarism_checked_by': 'integer',
    'related_submission_id': 'integer'
}

USER_EXTRA_COLUMN_TYPES = {
    'admin_tracks': 'text[]',
    'editor_admin_id': 'integer',
    'roles': 'text[]',
    'ui_language': 'text'
}

ADMIN_TRACK_KEYS = ('masters', 'phd', 'teacher')
ADMIN_TRACK_ALIASES = {
    'masters': 'masters',
    'master': 'masters',
    'magister': 'masters',
    'magistr': 'masters',
    'magistratura': 'masters',
    'магистр': 'masters',
    'магистратура': 'masters',
    'phd': 'phd',
    'doctor': 'phd',
    'doctoral': 'phd',
    'doktor': 'phd',
    'doktorant': 'phd',
    'doktorantura': 'phd',
    'doctorant': 'phd',
    'doctorantura': 'phd',
    'докторант': 'phd',
    'докторантура': 'phd',
    'teacher': 'teacher',
    "o'qituvchi": 'teacher',
    'oqituvchi': 'teacher',
    'ustoz': 'teacher',
    'prepodavatel': 'teacher',
    'преподаватель': 'teacher'
}
ROLE_NOTIFICATION_LEVELS = {'info', 'success', 'warning', 'danger'}
TARIFF_CURRENCY_FIELDS = {
    'usd': 'price_usd',
    'uzs': 'price_uzs',
    'rub': 'price_rub'
}

SUBMISSION_COLUMNS = set()


def _refresh_submission_columns():
    global SUBMISSION_COLUMNS
    SUBMISSION_COLUMNS = set(dbc.columns.get('submissions', []))


def _ensure_submission_columns():
    try:
        existing_columns = set(dbc.columns.get('submissions', []))
        if not existing_columns:
            return

        missing_columns = [name for name in SUBMISSION_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        if not missing_columns:
            return

        cursor = dbc.conn.cursor()
        for column_name in missing_columns:
            column_type = SUBMISSION_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE submissions ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        dbc.conn.commit()
        cursor.close()

        dbc._init_tables()
        dbc._init_columns()
    except Exception as e:
        print(f"Submission columns sync warning: {e}")
        try:
            dbc.conn.rollback()
        except Exception:
            pass
    finally:
        _refresh_submission_columns()


def _ensure_user_columns():
    try:
        existing_columns = set(dbc.columns.get('users', []))
        if not existing_columns:
            return

        missing_columns = [name for name in USER_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        cursor = dbc.conn.cursor()
        for column_name in missing_columns:
            column_type = USER_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        if 'roles' in existing_columns or 'roles' in missing_columns:
            cursor.execute(
                "UPDATE users "
                "SET roles = ARRAY[LOWER(COALESCE(NULLIF(TRIM(rolename), ''), 'user'))]::text[] "
                "WHERE roles IS NULL OR COALESCE(array_length(roles, 1), 0) = 0;"
            )
        dbc.conn.commit()
        cursor.close()

        dbc._init_tables()
        dbc._init_columns()
    except Exception as e:
        print(f"User columns sync warning: {e}")
        try:
            dbc.conn.rollback()
        except Exception:
            pass


def _ensure_role_notifications_table():
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS role_notifications (
                id SERIAL PRIMARY KEY,
                target_user_id INTEGER,
                target_role TEXT,
                actor_user_id INTEGER,
                event_type TEXT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                level TEXT DEFAULT 'info',
                action_url TEXT,
                related_submission_id INTEGER,
                related_assignment_id INTEGER,
                metadata_text TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at BIGINT DEFAULT EXTRACT(epoch FROM now()),
                read_at BIGINT
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_target_user ON role_notifications(target_user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_target_role ON role_notifications(target_role);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_unread ON role_notifications(is_read, created_at DESC);")
        dbc.conn.commit()
        cursor.close()
        dbc._init_tables()
        dbc._init_columns()
    except Exception as e:
        print(f"Role notifications table sync warning: {e}")
        try:
            dbc.conn.rollback()
        except Exception:
            pass


def _clean_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _to_submission_file(value):
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get('title') or value.get('download') or value.get('path')
    return _clean_text(value)


def _to_response_file(value):
    title = _to_submission_file(value)
    if not title:
        return None
    return {
        'title': title,
        'download': upload_access_url(title)
    }


def _coalesce(*values):
    for value in values:
        if value is not None:
            return value
    return None


def _parse_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_float(value, default=0.0):
    if value in (None, ''):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_currency(currency):
    normalized = (currency or 'usd').strip().lower()
    return normalized if normalized in TARIFF_CURRENCY_FIELDS else 'usd'


def _resolve_tariff_price(tariff, currency):
    selected_key = TARIFF_CURRENCY_FIELDS[currency]
    selected_value = tariff.get(selected_key)

    if selected_value in (None, ''):
        for fallback_key in ('price_usd', 'price_uzs', 'price_rub'):
            fallback_value = tariff.get(fallback_key)
            if fallback_value not in (None, ''):
                selected_value = fallback_value
                break

    return _parse_float(selected_value, 0.0)


def _user_is_verified(user_id):
    if not user_id:
        return False
    user_rows = dbc.users.get(id=user_id).exec()
    user = user_rows[0] if user_rows else {}
    if user.get('is_verified'):
        return True
    user_docs = dbc.user_doc_uploads.get(user_id=user_id).exec()
    return bool(user_docs)


def _resolve_issue_price(issue):
    return _parse_float(issue.get('price'), 0.0)


def _resolve_publication_price(publication, currency='usd'):
    if not publication:
        return 0.0
    normalized = _normalize_currency(currency)
    if normalized == 'uzs':
        return _parse_float(publication.get('price_uz'), _parse_float(publication.get('price'), 0.0))
    if normalized == 'rub':
        return _parse_float(publication.get('price_ru'), _parse_float(publication.get('price'), 0.0))
    return _parse_float(publication.get('price'), 0.0)


def _password_matches(stored_password, candidate):
    if not stored_password or not candidate:
        return False
    if isinstance(stored_password, str) and stored_password.startswith(('pbkdf2:', 'scrypt:')):
        return check_password_hash(stored_password, candidate)
    return stored_password == candidate


def _find_existing_payment(user_id, payment_type, target_id):
    payments = dbc.payments.get(user_id=user_id, payment_type=payment_type).exec()
    for payment in payments:
        status = (payment.get('status') or '').strip().lower()
        payment_ids = payment.get('ids') or []
        if not isinstance(payment_ids, (list, tuple)):
            continue
        if str(target_id) in {str(item) for item in payment_ids} and status in {'unpaid', 'pending'}:
            return payment
    return None


def _normalize_notification_level(level):
    normalized = _clean_text(level)
    if not normalized:
        return 'info'
    normalized = normalized.lower()
    return normalized if normalized in ROLE_NOTIFICATION_LEVELS else 'info'


def _create_role_notification(
    target_user_id=None,
    target_role=None,
    title=None,
    message=None,
    action_url=None,
    level='info',
    event_type=None,
    related_submission_id=None,
    related_assignment_id=None,
    actor_user_id=None,
    metadata_text=None
):
    title_text, message_text, metadata_text_value = prepare_notification_content(
        title=title,
        message=message,
        metadata_text=metadata_text,
        default_language='en'
    )
    target_user_id_int = _parse_int(target_user_id)
    target_role_text = _clean_text(target_role)
    actor_user_id_int = _parse_int(actor_user_id)

    if not title_text or not message_text:
        return None
    if target_user_id_int is None and not target_role_text:
        return None

    stored_target_role = target_role_text.lower() if target_role_text else None
    if target_user_id_int is not None and stored_target_role != 'all':
        stored_target_role = None

    event_type_text = _clean_text(event_type)
    action_url_text = _clean_text(action_url)
    related_submission_id_int = _parse_int(related_submission_id)
    related_assignment_id_int = _parse_int(related_assignment_id)

    now_ts = int(time.time())
    dedup_query = (
        "SELECT id FROM role_notifications "
        "WHERE COALESCE(target_user_id, -1) = COALESCE(%s, -1) "
        "AND COALESCE(target_role, '') = COALESCE(%s, '') "
        "AND COALESCE(event_type, '') = COALESCE(%s, '') "
        "AND COALESCE(related_submission_id, -1) = COALESCE(%s, -1) "
        "AND COALESCE(related_assignment_id, -1) = COALESCE(%s, -1) "
        "AND COALESCE(action_url, '') = COALESCE(%s, '') "
        "AND title = %s AND message = %s "
        "AND created_at >= %s LIMIT 1"
    )
    dedup_args = (
        target_user_id_int,
        stored_target_role,
        event_type_text,
        related_submission_id_int,
        related_assignment_id_int,
        action_url_text,
        title_text,
        message_text,
        now_ts - 120
    )
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(dedup_query, dedup_args)
        existing_row = cursor.fetchone()
        cursor.close()
        if existing_row:
            return _parse_int(existing_row[0])
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass

    payload = {
        'target_user_id': target_user_id_int,
        'target_role': stored_target_role,
        'actor_user_id': actor_user_id_int,
        'event_type': event_type_text,
        'title': title_text,
        'message': message_text,
        'level': _normalize_notification_level(level),
        'action_url': action_url_text,
        'related_submission_id': related_submission_id_int,
        'related_assignment_id': related_assignment_id_int,
        'metadata_text': metadata_text_value,
        'is_read': False,
        'created_at': now_ts
    }
    created = dbc.role_notifications.add(**payload).exec()
    if isinstance(created, list) and created:
        return created[0].get('id')
    if isinstance(created, dict):
        return created.get('id')
    return None


def _active_users_by_role(role_name):
    return _users_with_role(role_name, include_hidden=False, include_blocked=False)


def _notify_role_users(
    role_name,
    title,
    message,
    action_url=None,
    level='info',
    event_type=None,
    related_submission_id=None,
    related_assignment_id=None,
    actor_user_id=None,
    exclude_user_ids=None
):
    excluded_ids = {_parse_int(item) for item in (exclude_user_ids or []) if _parse_int(item) is not None}
    for user in _active_users_by_role(role_name):
        target_id = _parse_int(user.get('id'))
        if target_id is None or target_id in excluded_ids:
            continue
        _create_role_notification(
            target_user_id=target_id,
            target_role=role_name,
            title=title,
            message=message,
            action_url=action_url,
            level=level,
            event_type=event_type,
            related_submission_id=related_submission_id,
            related_assignment_id=related_assignment_id,
            actor_user_id=actor_user_id
        )


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def _parse_text_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            text = _clean_text(item)
            if text:
                result.append(text)
        return result
    text = _clean_text(value)
    if not text:
        return []
    if text.startswith('[') and text.endswith(']'):
        try:
            parsed_json = json.loads(text)
            if isinstance(parsed_json, list):
                return _parse_text_list(parsed_json)
        except Exception:
            pass
    if text.startswith('{') and text.endswith('}'):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [
            item.strip().strip('"').strip("'")
            for item in inner.split(',')
            if item.strip().strip('"').strip("'")
        ]
    return [item.strip() for item in text.split(',') if item.strip()]


def _parse_int_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            parsed = _parse_int(item)
            if parsed is not None:
                result.append(parsed)
        return result
    text = _clean_text(value)
    if not text:
        return []
    result = []
    for item in text.split(','):
        parsed = _parse_int(item.strip())
        if parsed is not None:
            result.append(parsed)
    return result


def _normalize_submission_track(track):
    if track is None:
        return None
    normalized = str(track).strip().lower()
    normalized = normalized.replace('’', "'")
    normalized = ADMIN_TRACK_ALIASES.get(normalized, normalized)
    return normalized if normalized in SUBMISSION_TRACK_ABSTRACT_WORD_LIMITS else None


def _normalize_workflow_stage(stage):
    if stage is None:
        return None
    normalized = str(stage).strip().lower()
    return normalized if normalized in SUBMISSION_WORKFLOW_STAGES else None


def _normalize_admin_track(track):
    if track is None:
        return None
    normalized = str(track).strip().lower()
    normalized = normalized.replace('’', "'")
    normalized = ADMIN_TRACK_ALIASES.get(normalized, normalized)
    return normalized if normalized in ADMIN_TRACK_KEYS else None


def _parse_admin_tracks(value):
    raw_tracks = _parse_text_list(value)
    normalized = []
    for track in raw_tracks:
        valid_track = _normalize_admin_track(track)
        if valid_track and valid_track not in normalized:
            normalized.append(valid_track)
    return normalized


def _admin_tracks_for_user(user):
    return _parse_admin_tracks((user or {}).get('admin_tracks'))


def _users_with_role(role_name, include_hidden=False, include_blocked=False):
    normalized_role = _clean_text(role_name).lower()
    if not normalized_role:
        return []
    try:
        rows = dbc.users.all().exec()
    except Exception:
        return []

    matched_users = []
    for row in rows or []:
        user = hydrate_user_roles(row)
        if not include_hidden and user.get('is_hidden'):
            continue
        if not include_blocked and user.get('is_blocked'):
            continue
        if user_has_role(user, normalized_role):
            matched_users.append(user)
    return matched_users


def _active_admins():
    return _users_with_role('admin', include_hidden=False, include_blocked=False)


def _admin_can_handle_track(admin_user, track):
    normalized_track = _normalize_submission_track(track)
    if not normalized_track:
        return True
    return normalized_track in _admin_tracks_for_user(admin_user)


def _pick_assigned_admin_id(track, existing_admin_id=None):
    admins = _active_admins()
    if not admins:
        return None

    normalized_track = _normalize_submission_track(track)
    candidate_admins = [admin for admin in admins if _admin_can_handle_track(admin, normalized_track)]
    if not candidate_admins:
        return None

    existing_id = _parse_int(existing_admin_id)
    if existing_id is not None:
        for admin in candidate_admins:
            if admin.get('id') == existing_id:
                return existing_id

    admin_ids = [admin.get('id') for admin in candidate_admins if admin.get('id')]
    if not admin_ids:
        return None

    try:
        submission_rows = dbc.submissions.get().any(assigned_admin_id=admin_ids).unequal(status='draft').exec()
    except Exception:
        submission_rows = []

    loads = {admin_id: 0 for admin_id in admin_ids}
    for submission in submission_rows:
        assigned_id = _parse_int(submission.get('assigned_admin_id'))
        if assigned_id in loads:
            loads[assigned_id] += 1

    picked_id = min(admin_ids, key=lambda admin_id: (loads.get(admin_id, 0), admin_id))
    return picked_id


def _submission_title(submission):
    title = _clean_text((submission or {}).get('title'))
    return title or f"ID: {_parse_int((submission or {}).get('id')) or '-'}"


def _get_user_row(user_id):
    parsed_id = _parse_int(user_id)
    if parsed_id is None:
        return None
    try:
        rows = dbc.users.get(id=parsed_id).exec()
    except Exception:
        return None
    return rows[0] if rows else None


def _get_users_by_role(role_name):
    return _users_with_role(role_name, include_hidden=True, include_blocked=True)


def _user_display_name(user_row):
    if not user_row:
        return ''
    full_name = _clean_text(f"{user_row.get('name') or ''} {user_row.get('second_name') or ''}")
    return full_name or _clean_text(user_row.get('name')) or _clean_text(user_row.get('email'))


def _send_user_email(user_row, subject, intro, details=None, body_lines=None, cta_url=None, cta_label=None, reply_to=None):
    email = _clean_text((user_row or {}).get('email'))
    if not email or not user_allows_email_notifications(user_row):
        return False
    subject_text, intro_text, _ = prepare_notification_content(
        title=subject,
        message=intro,
        default_language=normalize_notification_language(
            (user_row or {}).get('ui_language'),
            default=current_notification_language()
        )
    )
    return send_notification_email(
        recipients=[email],
        subject=subject_text,
        intro=intro_text,
        details=details,
        body_lines=body_lines,
        cta_url=cta_url,
        cta_label=cta_label,
        reply_to=reply_to,
        fail_silently=True,
    )


def _payment_item_label(payment_type, source_row):
    record = source_row or {}
    if payment_type == 'subscription':
        return (
            _clean_text(record.get('name'))
            or _clean_text(record.get('name_uz'))
            or _clean_text(record.get('name_ru'))
            or f"Tariff #{_parse_int(record.get('id')) or '-'}"
        )

    title = (
        _clean_text(record.get('title'))
        or _clean_text(record.get('title_uz'))
        or _clean_text(record.get('title_ru'))
        or _clean_text(record.get('title_en'))
    )
    if title:
        return title

    issue_no = _clean_text(record.get('issue_no'))
    year = _clean_text(record.get('year'))
    if issue_no or year:
        return f'Issue {issue_no or "?"} / {year or "?"}'
    return f"Issue #{_parse_int(record.get('id')) or '-'}"


def _send_payment_created_email(user_id, payment_id, payment_type, source_row, amount, currency):
    user_row = _get_user_row(user_id)
    if not user_row:
        return False

    item_label = _payment_item_label(payment_type, source_row)
    if payment_type == 'subscription':
        payment_type_label = 'Subscription'
    elif payment_type == 'article':
        payment_type_label = 'Article purchase'
    else:
        payment_type_label = 'Issue purchase'
    return _send_user_email(
        user_row,
        subject=f'{payment_type_label} payment request created',
        intro=f'A new {payment_type_label.lower()} request has been created for your account.',
        details=[
            ('Payment ID', payment_id),
            ('Item', item_label),
            ('Amount', f'{amount} {str(currency).upper()}'),
        ],
        body_lines=['Please upload your payment proof from the dashboard after payment.'],
        cta_url=url_for('app__dashboard_payments'),
        cta_label='Open payments',
    )


def _notify_submission_submitted(submission, actor_user_id=None):
    submission_id = _parse_int((submission or {}).get('id'))
    if submission_id is None:
        return

    title = _submission_title(submission)
    action_url = f"/fmadmin/submissions/{submission_id}"
    actor_user_id_int = _parse_int(actor_user_id)

    if actor_user_id_int is not None:
        _create_role_notification(
            target_user_id=actor_user_id_int,
            target_role='user',
            title=localized_texts(
                "Maqolangiz yuborildi",
                "Ваша статья отправлена",
                "Your submission was sent"
            ),
            message=localized_texts(
                f'"{title}" maqolasi muvaffaqiyatli yuborildi',
                f'Статья "{title}" успешно отправлена',
                f'"{title}" was submitted successfully'
            ),
            action_url=f"/dashboard/articles",
            level='success',
            event_type='submission_submitted',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id_int
        )

    assigned_admin_id = _parse_int((submission or {}).get('assigned_admin_id'))

    if assigned_admin_id is not None:
        _create_role_notification(
            target_user_id=assigned_admin_id,
            target_role='admin',
            title=localized_texts(
                "Yangi maqola kelib tushdi",
                "Поступила новая статья",
                "New submission received"
            ),
            message=localized_texts(
                f'"{title}" maqolasi tekshiruvga yuborildi',
                f'Статья "{title}" отправлена на проверку',
                f'"{title}" was submitted for review'
            ),
            action_url=action_url,
            level='info',
            event_type='submission_submitted',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id
        )
    else:
        _notify_role_users(
            'admin',
            title=localized_texts(
                "Yangi maqola kelib tushdi",
                "Поступила новая статья",
                "New submission received"
            ),
            message=localized_texts(
                f'"{title}" maqolasi tekshiruvga yuborildi',
                f'Статья "{title}" отправлена на проверку',
                f'"{title}" was submitted for review'
            ),
            action_url=action_url,
            level='info',
            event_type='submission_submitted',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id
        )

    _notify_role_users(
        'superadmin',
        title=localized_texts(
            "Yangi maqola kelib tushdi",
            "Поступила новая статья",
            "New submission received"
        ),
        message=localized_texts(
            f'"{title}" maqolasi tekshiruvga yuborildi',
            f'Статья "{title}" отправлена на проверку',
            f'"{title}" was submitted for review'
        ),
        action_url=action_url,
        level='info',
        event_type='submission_submitted',
        related_submission_id=submission_id,
        actor_user_id=actor_user_id
    )

    author_row = _get_user_row((submission or {}).get('user_id') or actor_user_id_int)
    author_email = _clean_text((author_row or {}).get('email'))
    if author_email:
        _send_user_email(
            author_row,
            subject=f'Submission received: {title}',
            intro=f'Your submission "{title}" was successfully sent to Philology Matters.',
            details=[('Submission ID', submission_id)],
            body_lines=['You can follow the review process from your dashboard.'],
            cta_url='/dashboard/articles',
            cta_label='Open dashboard',
        )

    admin_targets = []
    if assigned_admin_id is not None:
        assigned_admin = _get_user_row(assigned_admin_id)
        if assigned_admin:
            admin_targets.append(assigned_admin)
    else:
        admin_targets.extend(_get_users_by_role('admin'))
    admin_targets.extend(_get_users_by_role('superadmin'))

    seen_admin_emails = set()
    for admin_user in admin_targets:
        admin_email = _clean_text((admin_user or {}).get('email')).lower()
        if not admin_email or admin_email in seen_admin_emails:
            continue
        seen_admin_emails.add(admin_email)
        _send_user_email(
            admin_user,
            subject=f'New submission received: {title}',
            intro='A new submission has entered the editorial workflow.',
            details=[
                ('Submission ID', submission_id),
                ('Author', _user_display_name(author_row)),
            ],
            body_lines=['Open the admin panel to review the submission details.'],
            cta_url=action_url,
            cta_label='Open submission',
            reply_to=author_email or None,
        )


def _notify_submission_antiplagiarism_uploaded(submission, actor_user_id=None):
    submission_id = _parse_int((submission or {}).get('id'))
    if submission_id is None:
        return

    title = _submission_title(submission)
    actor_user_id_int = _parse_int(actor_user_id)
    action_url = f"/fmadmin/submissions/{submission_id}"

    if actor_user_id_int is not None:
        _create_role_notification(
            target_user_id=actor_user_id_int,
            target_role='user',
            title=localized_texts(
                "Antiplagiat hujjati yuborildi",
                "Антиплагиат-документ отправлен",
                "Anti-plagiarism document uploaded"
            ),
            message=localized_texts(
                f'"{title}" uchun antiplagiat hujjati muvaffaqiyatli yuborildi',
                f'Антиплагиат-документ для "{title}" успешно загружен',
                f'Anti-plagiarism document for "{title}" was uploaded successfully'
            ),
            action_url="/dashboard/articles",
            level='success',
            event_type='submission_antiplagiarism_uploaded',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id_int
        )

    message = localized_texts(
        f'"{title}" uchun muallif antiplagiat hujjatini yukladi',
        f'Автор загрузил антиплагиат-документ для "{title}"',
        f'The author uploaded an anti-plagiarism document for "{title}"'
    )
    assigned_admin_id = _parse_int((submission or {}).get('assigned_admin_id'))
    if assigned_admin_id is not None:
        _create_role_notification(
            target_user_id=assigned_admin_id,
            target_role='admin',
            title=localized_texts(
                "Antiplagiat hujjati yuklandi",
                "Антиплагиат-документ загружен",
                "Anti-plagiarism document uploaded"
            ),
            message=message,
            action_url=action_url,
            level='info',
            event_type='submission_antiplagiarism_uploaded',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id_int
        )
    else:
        _notify_role_users(
            'admin',
            title=localized_texts(
                "Antiplagiat hujjati yuklandi",
                "Антиплагиат-документ загружен",
                "Anti-plagiarism document uploaded"
            ),
            message=message,
            action_url=action_url,
            level='info',
            event_type='submission_antiplagiarism_uploaded',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id_int
        )

    _notify_role_users(
        'superadmin',
        title=localized_texts(
            "Antiplagiat hujjati yuklandi",
            "Антиплагиат-документ загружен",
            "Anti-plagiarism document uploaded"
        ),
        message=message,
        action_url=action_url,
        level='info',
        event_type='submission_antiplagiarism_uploaded',
        related_submission_id=submission_id,
        actor_user_id=actor_user_id_int
    )

    author_row = _get_user_row((submission or {}).get('user_id') or actor_user_id_int)
    if author_row:
        _send_user_email(
            author_row,
            subject=f'Anti-plagiarism file received: {title}',
            intro=f'Your anti-plagiarism document for "{title}" has been received.',
            details=[('Submission ID', submission_id)],
            body_lines=['The editorial team can now continue the review workflow.'],
            cta_url='/dashboard/articles',
            cta_label='Open dashboard',
        )

    reviewer_targets = []
    if assigned_admin_id is not None:
        assigned_admin = _get_user_row(assigned_admin_id)
        if assigned_admin:
            reviewer_targets.append(assigned_admin)
    else:
        reviewer_targets.extend(_get_users_by_role('admin'))
    reviewer_targets.extend(_get_users_by_role('superadmin'))

    seen_target_emails = set()
    author_email = _clean_text((author_row or {}).get('email'))
    for reviewer_user in reviewer_targets:
        reviewer_email = _clean_text((reviewer_user or {}).get('email')).lower()
        if not reviewer_email or reviewer_email in seen_target_emails:
            continue
        seen_target_emails.add(reviewer_email)
        _send_user_email(
            reviewer_user,
            subject=f'Anti-plagiarism file uploaded: {title}',
            intro=f'The author uploaded an anti-plagiarism document for "{title}".',
            details=[('Submission ID', submission_id)],
            body_lines=['Open the admin panel to continue the review process.'],
            cta_url=action_url,
            cta_label='Open submission',
            reply_to=author_email or None,
        )


def _track_abstract_word_limits(track):
    if not track:
        return None
    return SUBMISSION_TRACK_ABSTRACT_WORD_LIMITS.get(track)


def _track_word_count_limits(track):
    if not track:
        return None
    return SUBMISSION_TRACK_WORD_COUNT_LIMITS.get(track)


def _count_words(text):
    normalized = _clean_text(text)
    if not normalized:
        return 0
    return len([part for part in normalized.split() if part.strip()])


def _pick_primary_text(*values):
    for value in values:
        text = _clean_text(value)
        if text:
            return text
    return None


def _filter_submission_payload(payload):
    return {key: value for key, value in payload.items() if key in SUBMISSION_COLUMNS}


def _prepare_submission_payload(data, user_id, status, existing=None, is_new=False):
    existing = existing or {}
    now = int(time.time())

    title_uz = _clean_text(_coalesce(data.get('title_uz'), existing.get('title_uz')))
    title_ru = _clean_text(_coalesce(data.get('title_ru'), existing.get('title_ru')))
    title_en = _clean_text(_coalesce(data.get('title_en'), existing.get('title_en')))
    title_other = _clean_text(_coalesce(data.get('title_other'), existing.get('title_other')))

    abstract_uz = _clean_text(_coalesce(data.get('abstract_uz'), existing.get('abstract_uz')))
    abstract_ru = _clean_text(_coalesce(data.get('abstract_ru'), existing.get('abstract_ru')))
    abstract_en = _clean_text(_coalesce(data.get('abstract_en'), existing.get('abstract_en')))
    abstract_other = _clean_text(_coalesce(data.get('abstract_other'), existing.get('abstract_other')))
    other_language_name = _clean_text(_coalesce(data.get('other_language_name'), existing.get('other_language_name')))

    submission_track = _normalize_submission_track(_coalesce(data.get('submission_track'), existing.get('submission_track')))
    if submission_track is None:
        submission_track = _normalize_submission_track(existing.get('submission_track'))
    workflow_stage = _normalize_workflow_stage(_coalesce(data.get('workflow_stage'), existing.get('workflow_stage')))
    keywords = _parse_text_list(_coalesce(data.get('keywords'), existing.get('keywords')))
    word_count_raw = _parse_int(_coalesce(data.get('word_count'), existing.get('word_count')))
    word_count = word_count_raw if word_count_raw is not None else 0

    if status == 'submitted' and workflow_stage is None:
        workflow_stage = 'waiting'
    elif status == 'published':
        workflow_stage = 'published'
    elif status == 'rejected':
        workflow_stage = 'rejected'

    title = _pick_primary_text(
        _coalesce(data.get('title'), existing.get('title')),
        title_uz,
        title_ru,
        title_en,
        title_other
    )
    abstract = _pick_primary_text(
        _coalesce(data.get('abstract'), existing.get('abstract')),
        abstract_uz,
        abstract_ru,
        abstract_en,
        abstract_other
    )

    payload = {
        'user_id': user_id,
        'status': status,
        'title': title,
        'abstract': abstract,
        'keywords': keywords,
        'classifications': _parse_text_list(_coalesce(data.get('classifications'), existing.get('classifications'))),
        'is_special': _parse_bool(_coalesce(data.get('is_special_issue'), data.get('is_special'), existing.get('is_special'))),
        'is_dataset': _parse_bool(_coalesce(data.get('is_dataset'), existing.get('is_dataset'))),
        'check_copyright': _parse_bool(_coalesce(data.get('is_copyright_accept'), data.get('check_copyright'), existing.get('check_copyright'))),
        'check_ethical': _parse_bool(_coalesce(data.get('is_ethical_accept'), data.get('check_ethical'), existing.get('check_ethical'))),
        'check_consent': _parse_bool(_coalesce(data.get('is_consent_accept'), data.get('check_consent'), existing.get('check_consent'))),
        'check_acknowledgements': _parse_bool(_coalesce(data.get('is_acknowledgements_accept'), data.get('check_acknowledgements'), existing.get('check_acknowledgements'))),
        'is_used_previous': _parse_bool(_coalesce(data.get('is_previously'), data.get('is_used_previous'), existing.get('is_used_previous'))),
        'word_count': word_count,
        'is_corresponding_author': _parse_bool(_coalesce(data.get('is_corresponding_author'), existing.get('is_corresponding_author'))),
        'main_author_id': _parse_int(_coalesce(data.get('main_author_id'), existing.get('main_author_id'))),
        'sub_author_ids': _parse_int_list(_coalesce(data.get('sub_author_ids'), existing.get('sub_author_ids'))),
        'is_competing_interests': _parse_bool(_coalesce(data.get('is_competing'), data.get('is_competing_interests'), existing.get('is_competing_interests'))),
        'notes': _coalesce(data.get('notes'), existing.get('notes')),
        'file_authors': _to_submission_file(_coalesce(data.get('file_authors'), existing.get('file_authors'))),
        'file_anonymized': _to_submission_file(_coalesce(data.get('file_anonymized'), existing.get('file_anonymized'))),
        'updated_at': now,
        'submission_track': submission_track,
        'workflow_stage': workflow_stage,
        'title_uz': title_uz,
        'title_ru': title_ru,
        'title_en': title_en,
        'title_other': title_other,
        'abstract_uz': abstract_uz,
        'abstract_ru': abstract_ru,
        'abstract_en': abstract_en,
        'abstract_other': abstract_other,
        'other_language_name': other_language_name
    }

    if is_new and 'created_date' in SUBMISSION_COLUMNS:
        payload['created_date'] = now

    return payload


def _validate_submission_for_submit(payload):
    errors = []

    title_uz = _clean_text(payload.get('title_uz'))
    title_ru = _clean_text(payload.get('title_ru'))
    title_en = _clean_text(payload.get('title_en'))
    abstract_uz = _clean_text(payload.get('abstract_uz'))
    abstract_ru = _clean_text(payload.get('abstract_ru'))
    abstract_en = _clean_text(payload.get('abstract_en'))
    if not (title_uz and title_ru and title_en):
        errors.append('title_lang_required')
    if not (abstract_uz and abstract_ru and abstract_en):
        errors.append('abstract_lang_required')

    track = _normalize_submission_track(payload.get('submission_track'))
    abstract_limits = _track_abstract_word_limits(track)
    abstract_text = _pick_primary_text(
        payload.get('abstract_uz'),
        payload.get('abstract_ru'),
        payload.get('abstract_en'),
        payload.get('abstract_other'),
        payload.get('abstract')
    )
    abstract_words = _count_words(abstract_text)
    if abstract_limits:
        if abstract_words < abstract_limits[0]:
            errors.append('abstract_words_min')
        elif abstract_words > abstract_limits[1]:
            errors.append('abstract_words_max')

    word_count_limits = _track_word_count_limits(track)
    word_count = _parse_int(payload.get('word_count'))
    if word_count is None:
        word_count = 0
    if word_count_limits:
        if word_count < word_count_limits[0]:
            errors.append('word_count_min')
        elif word_count > word_count_limits[1]:
            errors.append('word_count_max')

    if len(_parse_text_list(payload.get('classifications'))) < 3:
        errors.append('classifications')

    return list(dict.fromkeys(errors))


def _validate_submission_for_draft(payload):
    errors = []
    if not _pick_primary_text(payload.get('title'), payload.get('title_uz'), payload.get('title_ru'), payload.get('title_en'), payload.get('title_other')):
        errors.append('title_lang_required')

    return list(dict.fromkeys(errors))


def _serialize_submission(submission):
    if not submission:
        return {}

    payload = dict(submission)
    if payload.get('title') and not payload.get('title_uz'):
        payload['title_uz'] = payload['title']
    if payload.get('abstract') and not payload.get('abstract_uz'):
        payload['abstract_uz'] = payload['abstract']

    payload['is_special_issue'] = payload.get('is_special')
    payload['file_authors'] = _to_response_file(payload.get('file_authors'))
    payload['file_anonymized'] = _to_response_file(payload.get('file_anonymized'))
    payload['anti_plagiarism_file'] = _to_response_file(payload.get('anti_plagiarism_file'))
    return payload


def _author_profiles_for_submission(submission):
    author_profiles = {}
    if not submission:
        return author_profiles

    author_ids = []
    main_author_id = _parse_int(submission.get('main_author_id'))
    if main_author_id:
        author_ids.append(main_author_id)
    author_ids.extend(_parse_int_list(submission.get('sub_author_ids')))

    for author_id in set(author_ids):
        author = dbc.author_profile.get(id=author_id).exec()
        if author:
            author_profiles[author_id] = author[0]
    return author_profiles


def _submission_response_payload(submission):
    serialized = _serialize_submission(submission)
    submit_errors = _validate_submission_for_submit(serialized)
    return {
        'submission': serialized,
        'is_ready_submit': len(submit_errors) == 0,
        'author_profiles': _author_profiles_for_submission(serialized)
    }


def _merge_submission_for_response(saved_submission, source_payload):
    merged = dict(saved_submission or {})
    for key in (
        'submission_track',
        'workflow_stage',
        'assigned_admin_id',
        'anti_plagiarism_file',
        'anti_plagiarism_checked_at',
        'anti_plagiarism_checked_by',
        'title_uz', 'title_ru', 'title_en', 'title_other',
        'abstract_uz', 'abstract_ru', 'abstract_en', 'abstract_other',
        'other_language_name'
    ):
        if merged.get(key) is None and source_payload.get(key) is not None:
            merged[key] = source_payload.get(key)
    return merged


_ensure_submission_columns()
_ensure_user_columns()
_ensure_role_notifications_table()


def app__api_getauthor():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json() or {}
    search = _clean_text(data.get('search') or data.get('orcid') or data.get('name'))
    search_by_name = _parse_bool(data.get('search_by_name'))

    if not search:
        return jsonify({'success': False, 'message': 'Required field missing: search'})

    if search_by_name:
        author_profile = dbc.author_profile.get().like(name=search).exec()
    elif data.get('orcid'):
        author_profile = dbc.author_profile.get(orcid=search).exec()
    elif search.strip().isdigit():
        author_profile = dbc.author_profile.get(id=int(search)).exec()
    else:
        author_profile = dbc.author_profile.get().like(name=search).exec()

    if not author_profile:
        return jsonify({'success': True, 'is_found': False, 'message': f'No author found for {search}'})

    author_profile = author_profile[0]
    return jsonify({
        'success': True,
        'is_found': True,
        'author': {
            'id': author_profile['id'],
            'name': author_profile['name'],
            'organization': author_profile['organization'],
            'department': author_profile['department'],
            'position': author_profile['position'],
            'email': author_profile['email'],
            'phone': author_profile['phone'],
            'orcid': author_profile['orcid'],
            'address_street': author_profile['address_street'],
            'address_city': author_profile['address_city'],
            'address_country': author_profile['address_country'],
            'address_zip': author_profile['address_zip']
        }
    })


def app__api_getcurrentauthor():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    author_profile = dbc.author_profile.get(user_id=user_id).exec()
    if not author_profile:
        return jsonify({'success': False, 'message': 'No author profile found for current user'})

    author_profile = author_profile[0]
    return jsonify({
        'success': True,
        'author': {
            'id': author_profile['id'],
            'name': author_profile['name'],
            'organization': author_profile['organization'],
            'department': author_profile['department'],
            'position': author_profile['position'],
            'email': author_profile['email'],
            'phone': author_profile['phone'],
            'orcid': author_profile['orcid'],
            'address_street': author_profile['address_street'],
            'address_city': author_profile['address_city'],
            'address_country': author_profile['address_country'],
            'address_zip': author_profile['address_zip']
        }
    })


def app__api_getclassifications():
    classifications = dbc.fix_classifications.get().exec()
    return jsonify({'success': True, 'classifications': classifications})


def app__api_article_save():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json() or {}
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission_id = _parse_int(data.get('submission_id'))

    try:
        existing = {}
        if submission_id:
            existing_rows = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
            if not existing_rows:
                return jsonify({'success': False, 'message': 'Submission not found'})
            existing = existing_rows[0]

        submission_payload = _prepare_submission_payload(
            data=data,
            user_id=user_id,
            status='draft',
            existing=existing,
            is_new=not bool(existing)
        )
        draft_errors = _validate_submission_for_draft(submission_payload)
        if draft_errors:
            return jsonify({'success': False, 'errors': draft_errors, 'message': 'Validation failed'})

        db_payload = _filter_submission_payload(submission_payload)
        if submission_id:
            updated = dbc.submissions.get(id=submission_id, user_id=user_id).update(**db_payload).exec()
            saved_submission = updated[0] if updated else dbc.submissions.get(id=submission_id, user_id=user_id).exec()[0]
            response_payload = _submission_response_payload(_merge_submission_for_response(saved_submission, submission_payload))
            return jsonify({
                'success': True,
                'message': 'Draft updated successfully',
                'submission_id': submission_id,
                **response_payload
            })

        created = dbc.submissions.add(**db_payload).exec()
        if not created:
            return jsonify({'success': False, 'message': 'Failed to save draft'})

        saved_submission = created[0]
        response_payload = _submission_response_payload(_merge_submission_for_response(saved_submission, submission_payload))
        return jsonify({
            'success': True,
            'message': 'Draft saved successfully',
            'submission_id': saved_submission['id'],
            **response_payload
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving draft: {str(e)}'})


def app__api_article_submit():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json() or {}
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission_id = _parse_int(data.get('submission_id'))

    try:
        existing = {}
        if submission_id:
            existing_rows = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
            if not existing_rows:
                return jsonify({'success': False, 'message': 'Submission not found'})
            existing = existing_rows[0]

        submission_payload = _prepare_submission_payload(
            data=data,
            user_id=user_id,
            status='submitted',
            existing=existing,
            is_new=not bool(existing)
        )
        submit_errors = _validate_submission_for_submit(submission_payload)
        if submit_errors:
            return jsonify({
                'success': False,
                'errors': submit_errors,
                'message': 'Validation failed',
                'submission': _serialize_submission(submission_payload),
                'is_ready_submit': False
            })

        if 'assigned_admin_id' in SUBMISSION_COLUMNS:
            assigned_admin_id = _pick_assigned_admin_id(
                submission_payload.get('submission_track'),
                existing.get('assigned_admin_id')
            )
            submission_payload['assigned_admin_id'] = assigned_admin_id

        db_payload = _filter_submission_payload(submission_payload)
        if submission_id:
            updated = dbc.submissions.get(id=submission_id, user_id=user_id).update(**db_payload).exec()
            saved_submission = updated[0] if updated else dbc.submissions.get(id=submission_id, user_id=user_id).exec()[0]
            _notify_submission_submitted(saved_submission, actor_user_id=user_id)
            response_payload = _submission_response_payload(_merge_submission_for_response(saved_submission, submission_payload))
            return jsonify({
                'success': True,
                'message': 'Article submitted successfully',
                'submission_id': submission_id,
                **response_payload
            })

        created = dbc.submissions.add(**db_payload).exec()
        if not created:
            return jsonify({'success': False, 'message': 'Failed to submit article'})

        saved_submission = created[0]
        _notify_submission_submitted(saved_submission, actor_user_id=user_id)
        response_payload = _submission_response_payload(_merge_submission_for_response(saved_submission, submission_payload))
        return jsonify({
            'success': True,
            'message': 'Article submitted successfully',
            'submission_id': saved_submission['id'],
            **response_payload
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error submitting article: {str(e)}'})


def app__api_article_upload():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['file']
    file_type = (request.form.get('file_type') or request.form.get('type') or 'authors').strip().lower()
    if file_type not in {'authors', 'anonymized', 'anti_plagiarism'}:
        file_type = 'authors'

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file and allowed_file(file.filename, {'pdf', 'doc', 'docx'}):
        submission_id = _parse_int(request.form.get('submission_id'))
        submission = None
        if submission_id is not None:
            submission_rows = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
            if submission_rows:
                submission = submission_rows[0]

        if file_type == 'anti_plagiarism':
            if submission_id is None or submission is None:
                return jsonify({'success': False, 'message': 'Submission not found'})

            workflow_stage = _normalize_workflow_stage(submission.get('workflow_stage'))
            if workflow_stage != 'anti_plagiarism':
                return jsonify({
                    'success': False,
                    'message': 'Anti-plagiarism document can only be uploaded in anti_plagiarism stage'
                })

        filename = secure_filename(file.filename)
        filename = f"{file_type}_{user_id}_{int(time.time())}_{filename}"
        filepath = os.path.join(settings.SAVE_PATH, 'private_uploads', 'articles', filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)

        file_ref = build_private_upload_ref('articles', filename)
        download_url = upload_access_url(file_ref)

        if file_type == 'anti_plagiarism':
            now_ts = int(time.time())
            dbc.submissions.get(id=submission_id, user_id=user_id).update(
                anti_plagiarism_file=file_ref,
                anti_plagiarism_checked_at=now_ts,
                anti_plagiarism_checked_by=user_id,
                updated_at=now_ts
            ).exec()
            updated_rows = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
            if updated_rows:
                _notify_submission_antiplagiarism_uploaded(updated_rows[0], actor_user_id=user_id)

        return jsonify({
            'success': True,
            'file_ref': file_ref,
            'file_path': file_ref,
            'filename': file_ref,
            'download': download_url,
            'file_type': file_type
        })

    return jsonify({'success': False, 'message': 'Invalid file type'})


def app__api_article_load(submission_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
    if not submission:
        return jsonify({'success': False, 'message': 'Submission not found'})

    submission = submission[0]
    response_payload = _submission_response_payload(submission)
    return jsonify({'success': True, **response_payload})


def app__api_article_resubmit():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json() or {}
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission_id = _parse_int(data.get('submission_id'))
    if submission_id is None:
        return jsonify({'success': False, 'message': 'Submission not found'})

    submission_rows = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
    if not submission_rows:
        return jsonify({'success': False, 'message': 'Submission not found'})

    submission = submission_rows[0]
    status = _clean_text(submission.get('status'))
    if (status or '').lower() != 'rejected':
        return jsonify({'success': False, 'message': 'Only rejected submissions can be resubmitted'})

    now_ts = int(time.time())
    payload = {
        'user_id': user_id,
        'status': 'draft',
        'title': submission.get('title'),
        'abstract': submission.get('abstract'),
        'keywords': submission.get('keywords'),
        'classifications': submission.get('classifications'),
        'is_special': submission.get('is_special'),
        'is_dataset': submission.get('is_dataset'),
        'check_copyright': submission.get('check_copyright'),
        'check_ethical': submission.get('check_ethical'),
        'check_consent': submission.get('check_consent'),
        'check_acknowledgements': submission.get('check_acknowledgements'),
        'is_used_previous': submission.get('is_used_previous'),
        'word_count': submission.get('word_count'),
        'is_corresponding_author': submission.get('is_corresponding_author'),
        'main_author_id': submission.get('main_author_id'),
        'sub_author_ids': submission.get('sub_author_ids'),
        'is_competing_interests': submission.get('is_competing_interests'),
        'file_authors': submission.get('file_authors'),
        'file_anonymized': submission.get('file_anonymized'),
        'submission_track': submission.get('submission_track'),
        'title_uz': submission.get('title_uz'),
        'title_ru': submission.get('title_ru'),
        'title_en': submission.get('title_en'),
        'title_other': submission.get('title_other'),
        'abstract_uz': submission.get('abstract_uz'),
        'abstract_ru': submission.get('abstract_ru'),
        'abstract_en': submission.get('abstract_en'),
        'abstract_other': submission.get('abstract_other'),
        'other_language_name': submission.get('other_language_name'),
        'notes': None,
        'workflow_stage': None,
        'assigned_admin_id': None,
        'anti_plagiarism_file': None,
        'anti_plagiarism_checked_at': None,
        'anti_plagiarism_checked_by': None,
        'editor_review_status': None,
        'related_submission_id': submission_id,
        'created_date': now_ts,
        'updated_at': now_ts
    }

    db_payload = _filter_submission_payload(payload)
    created = dbc.submissions.add(**db_payload).exec()
    new_submission = created[0] if isinstance(created, list) and created else created
    new_id = _parse_int((new_submission or {}).get('id'))
    if new_id is None:
        return jsonify({'success': False, 'message': 'Failed to create resubmission'})

    return jsonify({'success': True, 'submission_id': new_id})

def app__api_payment_submit_proof():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    payment_id = _parse_int(request.form.get('payment_id'))
    if payment_id is None:
        return jsonify({'success': False, 'message': 'Payment ID required'})

    payment = dbc.payments.get(id=payment_id, user_id=user_id).exec()
    if not payment:
        return jsonify({'success': False, 'message': 'Payment not found'})

    payment = payment[0]
    payment_status = (payment.get('status') or '').strip().lower()
    if payment_status not in {'unpaid', 'pending', 'rejected'}:
        return jsonify({'success': False, 'message': 'Payment proof can no longer be updated'})

    file = request.files.get('payment_proof') or request.files.get('proof')
    if file is None:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file and allowed_file(file.filename, {'pdf', 'jpg', 'jpeg', 'png'}):
        filename = secure_filename(file.filename)
        filename = f"payment_proof_{user_id}_{int(time.time())}.{filename.rsplit('.', 1)[1].lower()}"

        payments_folder = os.path.join(settings.SAVE_PATH, 'private_uploads', 'payments')
        os.makedirs(payments_folder, exist_ok=True)
        filepath = os.path.join(payments_folder, filename)
        file.save(filepath)
        proof_ref = build_private_upload_ref('payments', filename)

        now_ts = int(time.time())
        update_data = {
            'status': 'pending',
            'payment_date': now_ts,
            'proof': proof_ref,
            'note': request.form.get('note')
        }

        dbc.payments.get(id=payment_id, user_id=user_id).update(**update_data).exec()
        return jsonify({
            'success': True,
            'message': 'Payment proof submitted successfully',
            'proof': upload_access_url(update_data['proof']),
            'payment_id': payment_id
        })

    return jsonify({'success': False, 'message': 'Invalid file type'})


def app__api_payment_delete(payment_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    payment = dbc.payments.get(id=payment_id, user_id=user_id).exec()
    if not payment:
        return jsonify({'success': False, 'message': 'Payment not found'})

    payment = payment[0]
    if (payment.get('status') or '').strip().lower() != 'unpaid':
        return jsonify({'success': False, 'message': 'Only unpaid payments can be deleted'})

    dbc.payments.get(id=payment_id, user_id=user_id).delete().exec()
    return jsonify({'success': True, 'message': 'Payment deleted successfully'})


def app__api_payment_create_subscription():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json() if request.is_json else request.form
    tariff_id = _parse_int(data.get('tariff_id'))
    if not tariff_id:
        return jsonify({'success': False, 'message': 'Tariff ID required'})

    tariff = dbc.tariffs.get(id=tariff_id).exec()
    if not tariff:
        return jsonify({'success': False, 'message': 'Tariff not found'})

    tariff = tariff[0]
    if tariff.get('is_verified') and not _user_is_verified(user_id):
        msg = t('verification_required_for_tariff')
        if msg == 'verification_required_for_tariff':
            msg = 'Verification required to access this tariff'
        return jsonify({'success': False, 'message': msg})
    existing_payment = _find_existing_payment(user_id, 'subscription', tariff_id)
    if existing_payment:
        return jsonify({
            'success': True,
            'message': 'Subscription payment already exists',
            'payment_id': existing_payment['id']
        })

    currency = _normalize_currency(data.get('currency', 'usd'))
    payment_data = {
        'user_id': user_id,
        'status': 'unpaid',
        'currency': currency,
        'payment_type': 'subscription',
        'payment_date': None,
        'amount': _resolve_tariff_price(tariff, currency),
        'ids': [tariff_id],
        'proof': None,
        'note': data.get('note'),
        'created_at': int(time.time())
    }

    result = dbc.payments.add(**payment_data).exec()
    payment_id = result[0]['id'] if result else None
    if payment_id is not None:
        _send_payment_created_email(
            user_id=user_id,
            payment_id=payment_id,
            payment_type='subscription',
            source_row=tariff,
            amount=payment_data['amount'],
            currency=currency,
        )
    return jsonify({'success': True, 'message': 'Subscription payment created', 'payment_id': payment_id})


def app__api_issue_purchase():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json() if request.is_json else request.form
    issue_id = _parse_int(data.get('issue_id'))
    if not issue_id:
        return jsonify({'success': False, 'message': 'Issue ID required'})

    issue = dbc.issues.get(id=issue_id).exec()
    if not issue:
        return jsonify({'success': False, 'message': 'Issue not found'})

    issue = issue[0]
    existing_payment = _find_existing_payment(user_id, 'issue', issue_id)
    if existing_payment:
        return jsonify({
            'success': True,
            'message': 'Issue payment already exists',
            'payment_id': existing_payment['id']
        })

    currency = _normalize_currency(data.get('currency', 'usd'))
    payment_data = {
        'user_id': user_id,
        'status': 'unpaid',
        'currency': currency,
        'payment_type': 'issue',
        'payment_date': None,
        'amount': _resolve_issue_price(issue),
        'ids': [issue_id],
        'proof': None,
        'note': data.get('note'),
        'created_at': int(time.time())
    }

    result = dbc.payments.add(**payment_data).exec()
    payment_id = result[0]['id'] if result else None
    if payment_id is not None:
        _send_payment_created_email(
            user_id=user_id,
            payment_id=payment_id,
            payment_type='issue',
            source_row=issue,
            amount=payment_data['amount'],
            currency=currency,
        )
    return jsonify({'success': True, 'message': 'Issue payment created', 'payment_id': payment_id})


def app__api_article_purchase():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json() if request.is_json else request.form
    article_id = _parse_int(data.get('article_id'))
    if not article_id:
        return jsonify({'success': False, 'message': 'Article ID required'})

    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        return jsonify({'success': False, 'message': 'Article not found'})

    publication = publication[0]
    if not publication.get('is_paid'):
        return jsonify({'success': True, 'message': 'Article is open access'})

    existing_payment = _find_existing_payment(user_id, 'article', article_id)
    if existing_payment:
        return jsonify({
            'success': True,
            'message': 'Article payment already exists',
            'payment_id': existing_payment['id']
        })

    currency = _normalize_currency(data.get('currency', 'usd'))
    payment_data = {
        'user_id': user_id,
        'status': 'unpaid',
        'currency': currency,
        'payment_type': 'article',
        'payment_date': None,
        'amount': _resolve_publication_price(publication, currency),
        'ids': [article_id],
        'proof': None,
        'note': data.get('note'),
        'created_at': int(time.time())
    }

    result = dbc.payments.add(**payment_data).exec()
    payment_id = result[0]['id'] if result else None
    if payment_id is not None:
        _send_payment_created_email(
            user_id=user_id,
            payment_id=payment_id,
            payment_type='article',
            source_row=publication,
            amount=payment_data['amount'],
            currency=currency,
        )
    return jsonify({'success': True, 'message': 'Article payment created', 'payment_id': payment_id})


def app__api_translations_clear_cache():
    provided_token = request.headers.get('X-Translation-Sync-Token', '').strip()
    expected_token = (settings.TRANSLATION_SYNC_TOKEN or '').strip()
    is_authorized_by_token = bool(expected_token) and provided_token == expected_token
    is_authorized_by_session = bool(session.get('user_id'))

    if not is_authorized_by_token and not is_authorized_by_session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    clear_translations_cache()
    return jsonify({'success': True, 'message': 'Translation cache cleared'})


def app__api_profile_change_password():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json() if request.is_json else request.form
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([current_password, new_password, confirm_password]):
        return jsonify({'success': False, 'message': 'All fields are required'})

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})

    user = dbc.users.get(id=user_id).exec()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})

    user = user[0]
    if not _password_matches(user.get('password'), current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})

    is_valid, validation_message = is_strong_password(new_password)
    if not is_valid:
        return jsonify({'success': False, 'message': validation_message})

    hashed_password = generate_password_hash(new_password)
    dbc.users.get(id=user_id).update(password=hashed_password).exec()
    return jsonify({'success': True, 'message': 'Password updated successfully'})


def app__api_createauthor():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json()
    orcid = data.get('orcid')
    name = data.get('name')
    without_orcid = data.get('without_orcid', False)

    if not name:
        return jsonify({'success': False, 'message': 'Required field missing: name'})

    if not name.strip() or len(name.strip()) < 2:
        return jsonify({'success': False, 'message': 'Author name must be at least 2 characters long'})

    if without_orcid:
        orcid = 'without-orcid'
    else:
        if not orcid:
            return jsonify({'success': False, 'message': 'Required field missing: ORCID (or check "Author without ORCID")'})
        if not orcid.strip() or len(orcid.strip()) < 10:
            return jsonify({'success': False, 'message': 'Invalid ORCID format. Please enter a valid ORCID (e.g., 0000-0000-0000-0000)'})

    try:
        if orcid != 'without-orcid':
            existing_author = dbc.author_profile.get(orcid=orcid.strip()).exec()
            if existing_author:
                return jsonify({'success': False, 'message': f'Author with ORCID {orcid} already exists in the database'})

        profile_data = {
            'user_id': None,
            'name': name.strip(),
            'organization': data.get('organization', '').strip(),
            'department': data.get('department', '').strip(),
            'position': data.get('position', '').strip(),
            'email': data.get('email', '').strip(),
            'phone': data.get('phone', '').strip(),
            'orcid': orcid.strip(),
            'address_street': data.get('address_street', '').strip(),
            'address_city': data.get('address_city', '').strip(),
            'address_country': data.get('address_country', '').strip(),
            'address_zip': data.get('address_zip', '').strip(),
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }

        result = dbc.author_profile.add(**profile_data).exec()
        if result:
            new_author = result[0]
            return jsonify({
                'success': True,
                'message': f'Author "{name}" created successfully',
                'author': {
                    'id': new_author['id'],
                    'name': new_author['name'],
                    'orcid': new_author['orcid'],
                    'organization': new_author['organization'],
                    'department': new_author['department'],
                    'position': new_author['position'],
                    'email': new_author['email'],
                    'phone': new_author['phone'],
                    'address_street': new_author['address_street'],
                    'address_city': new_author['address_city'],
                    'address_country': new_author['address_country'],
                    'address_zip': new_author['address_zip']
                }
            })
        return jsonify({'success': False, 'message': 'Failed to create author: Database operation returned no results'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error occurred while creating author: {str(e)}'})


def register(app):
    app.add_url_rule('/api/getauthor', view_func=author_login_required(app__api_getauthor), methods=['POST'])
    app.add_url_rule('/api/getcurrentauthor', view_func=author_login_required(app__api_getcurrentauthor), methods=['GET'])
    app.add_url_rule('/api/getclassifications', view_func=author_login_required(app__api_getclassifications), methods=['GET'])
    app.add_url_rule('/api/article/save', view_func=author_login_required(app__api_article_save), methods=['POST'])
    app.add_url_rule('/api/article/submit', view_func=author_login_required(app__api_article_submit), methods=['POST'])
    app.add_url_rule('/api/article/upload', view_func=author_login_required(app__api_article_upload), methods=['POST'])
    app.add_url_rule('/api/article/load/<int:submission_id>', view_func=author_login_required(app__api_article_load))
    app.add_url_rule('/api/article/resubmit', view_func=author_login_required(app__api_article_resubmit), methods=['POST'])
    app.add_url_rule('/api/payment/submit_proof', view_func=login_required(app__api_payment_submit_proof), methods=['POST'])
    app.add_url_rule('/api/payment/delete/<int:payment_id>', view_func=login_required(app__api_payment_delete), methods=['POST'])
    app.add_url_rule('/api/payment/create_subscription', view_func=login_required(app__api_payment_create_subscription), methods=['POST'])
    app.add_url_rule('/api/issue/purchase', view_func=login_required(app__api_issue_purchase), methods=['POST'])
    app.add_url_rule('/api/article/purchase', view_func=login_required(app__api_article_purchase), methods=['POST'])
    app.add_url_rule('/api/translations/clear_cache', view_func=app__api_translations_clear_cache, methods=['POST'])
    app.add_url_rule('/api/profile/change_password', view_func=login_required(app__api_profile_change_password), methods=['POST'])
    app.add_url_rule('/api/createauthor', view_func=author_login_required(app__api_createauthor), methods=['POST'])
