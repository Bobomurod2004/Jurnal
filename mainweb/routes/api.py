# flake8: noqa
import os
import time
import json
import logging
import secrets
from werkzeug.utils import secure_filename
from flask import request, jsonify, session, url_for
from extensions import dbc
from modules.translate import t, translate, clear_translations_cache
try:
    import mainweb.settings as settings
except ImportError:
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
from utils.private_uploads import build_private_upload_ref, private_upload_abspath, upload_access_url
from utils.roles import hydrate_user_roles, user_has_permission, user_has_role
from utils.uploads import allowed_file
from werkzeug.security import generate_password_hash, check_password_hash
from shared.submission_status import (
    SUBMISSION_STATUSES,
    SUBMISSION_STATUS_KEYS,
    RESUBMITTABLE_STATUSES,
    STATUSES_REQUIRING_ANTIPLAGIARISM_FILE,
    is_resubmittable,
)


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

# Kept under the old name for minimal diff -- now the single canonical
# 11-value status enum (shared/submission_status.py) instead of the
# separate status+workflow_stage combination.
SUBMISSION_WORKFLOW_STAGES = tuple(SUBMISSION_STATUSES)

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
    'anti_plagiarism_uploaded_by_role': 'text',
    'anti_plagiarism_status': "text NOT NULL DEFAULT 'pending'",
    'anti_plagiarism_note': 'text',
    'anti_plagiarism_resubmitted_at': 'bigint',
    'editor_shared_file': 'text',
    'editor_shared_file_note': 'text',
    'editor_shared_file_at': 'bigint',
    'revision_severity': "text NOT NULL DEFAULT 'major'",
    'related_submission_id': 'integer',
    'revision_number': 'integer DEFAULT 1',
    'rejection_origin': 'text',
    'rejected_at': 'bigint',
    'rejected_by': 'integer',
    'revision_allowed': 'boolean DEFAULT true',
    'last_revision_submitted_at': 'bigint'
}

EDITOR_ASSIGNMENT_REVIEWED_STATUS_VALUES = {'reviewed', 'rejected'}

USER_EXTRA_COLUMN_TYPES = {
    'admin_tracks': 'text[]',
    'editor_admin_id': 'integer',
    'roles': 'text[]',
    'ui_language': 'text'
}
PAYMENT_EXTRA_COLUMN_TYPES = {
    'snapshot_duration_days': 'integer',
    'snapshot_start_at': 'bigint',
    'snapshot_end_at': 'bigint',
}
TARIFF_EXTRA_COLUMN_TYPES = {
    'entitlement_scope': "text DEFAULT 'all'",
    'archive_days_threshold': 'integer DEFAULT 365',
    'article_discount_pct': 'double precision DEFAULT 0',
    'issue_discount_pct': 'double precision DEFAULT 0',
    'subscription_discount_pct': 'double precision DEFAULT 0',
    'subscription_discount_start_at': 'bigint',
    'subscription_discount_end_at': 'bigint',
    'monthly_download_limit': 'integer DEFAULT 0',
    'required_academic_positions': "text[] DEFAULT '{}'::text[]",
    'requires_verified_document': 'boolean DEFAULT false',
    'eligibility_note': 'text',
    'feature_permissions': "text[] DEFAULT '{}'::text[]",
    'required_document_types': "text[] DEFAULT '{}'::text[]",
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
LANGUAGE_DEFAULT_CURRENCY = {
    'uz': 'uzs',
    'ru': 'rub',
    'en': 'usd',
}

SUBMISSION_COLUMNS = set()
logger = logging.getLogger(__name__)
TARIFF_ENTITLEMENT_SCOPES = {'all', 'archive'}
DEFAULT_ARCHIVE_DAYS_THRESHOLD = 365
ALLOWED_TARIFF_FEATURE_PERMISSIONS = {
    'access_latest_content',
    'access_archive_content',
    'download_subscription_files',
    'article_discount',
    'issue_discount',
}
ACADEMIC_POSITION_ALIASES = {
    'teacher': 'teacher',
    'student': 'student',
    'master': 'master',
    'masters': 'master',
    'magister': 'master',
    'magistr': 'master',
    'doctoral': 'doctoral',
    'doctor': 'doctor',
    'doctorant': 'doctoral',
    'doktorant': 'doctoral',
    'postgraduate': 'postgraduate',
    'researcher': 'researcher',
    'university_researcher': 'university_researcher',
    'independent_researcher': 'independent_researcher',
}
ALLOWED_ACADEMIC_POSITIONS = {
    'teacher',
    'student',
    'master',
    'doctoral',
    'postgraduate',
    'doctor',
    'researcher',
    'university_researcher',
    'independent_researcher',
}
ACADEMIC_POSITION_LABELS = {
    'teacher': "O'qituvchi",
    'student': 'Talaba',
    'master': 'Magistrant',
    'doctoral': 'Doktorant',
    'postgraduate': 'Aspirant',
    'doctor': 'Fan doktori',
    'researcher': 'Tadqiqotchi',
    'university_researcher': 'Universitet tadqiqotchisi',
    'independent_researcher': 'Mustaqil tadqiqotchi',
}
DOCUMENT_TYPE_ALIASES = {
    'student_id': 'student_id',
    'student_card': 'student_id',
    'enrollment_certificate': 'enrollment_certificate',
    'master_certificate': 'master_certificate',
    'masters_certificate': 'master_certificate',
    'phd_certificate': 'phd_certificate',
    'doctoral_certificate': 'phd_certificate',
    'researcher_certificate': 'researcher_certificate',
    'employment_certificate': 'employment_certificate',
    'other_academic': 'other_academic',
}
ALLOWED_DOCUMENT_TYPES = {
    'student_id',
    'enrollment_certificate',
    'master_certificate',
    'phd_certificate',
    'researcher_certificate',
    'employment_certificate',
    'other_academic',
}
DOCUMENT_TYPE_LABELS = {
    'student_id': 'Talabalik guvohnomasi',
    'enrollment_certificate': "Ta'lim muassasasi ma'lumotnomasi",
    'master_certificate': 'Magistratura tasdiq hujjati',
    'phd_certificate': 'Doktorantura tasdiq hujjati',
    'researcher_certificate': 'Tadqiqotchi status hujjati',
    'employment_certificate': "Ish joyidan ma'lumotnoma",
    'other_academic': 'Boshqa akademik hujjat',
}
DOCUMENT_TYPE_LOCALIZED_LABELS = {
    'uz': {
        'student_id': 'Talabalik guvohnomasi',
        'enrollment_certificate': "Ta'lim muassasasi ma'lumotnomasi",
        'master_certificate': 'Magistratura tasdiq hujjati',
        'phd_certificate': 'Doktorantura tasdiq hujjati',
        'researcher_certificate': 'Tadqiqotchi status hujjati',
        'employment_certificate': "Ish joyidan ma'lumotnoma",
        'other_academic': 'Boshqa akademik hujjat',
    },
    'ru': {
        'student_id': 'Студенческий билет',
        'enrollment_certificate': 'Справка из образовательного учреждения',
        'master_certificate': 'Подтверждающий документ магистратуры',
        'phd_certificate': 'Подтверждающий документ докторантуры',
        'researcher_certificate': 'Документ, подтверждающий статус исследователя',
        'employment_certificate': 'Справка с места работы',
        'other_academic': 'Другой академический документ',
    },
    'en': {
        'student_id': 'Student ID',
        'enrollment_certificate': 'Enrollment Certificate',
        'master_certificate': "Master's Confirmation Document",
        'phd_certificate': 'Doctoral Confirmation Document',
        'researcher_certificate': 'Researcher Status Document',
        'employment_certificate': 'Employment Certificate',
        'other_academic': 'Other Academic Document',
    },
}


def _refresh_submission_columns():
    global SUBMISSION_COLUMNS
    SUBMISSION_COLUMNS = set(dbc.columns.get('submissions', []))


def _ensure_submission_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        _refresh_submission_columns()
        return
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
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
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
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
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


def _ensure_payment_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(dbc.columns.get('payments', []))
        if not existing_columns:
            return

        missing_columns = [name for name in PAYMENT_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        if not missing_columns:
            return

        cursor = dbc.conn.cursor()
        for column_name in missing_columns:
            column_type = PAYMENT_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE payments ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        dbc.conn.commit()
        cursor.close()

        dbc._init_tables()
        dbc._init_columns()
    except Exception as e:
        print(f"Payment columns sync warning: {e}")
        try:
            dbc.conn.rollback()
        except Exception:
            pass


def _ensure_tariff_entitlement_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(dbc.columns.get('tariffs', []))
        if not existing_columns:
            return

        missing_columns = [name for name in TARIFF_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        cursor = dbc.conn.cursor()
        for column_name in missing_columns:
            column_type = TARIFF_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS {column_name} {column_type};")

        cursor.execute(
            "UPDATE tariffs "
            "SET entitlement_scope = COALESCE(NULLIF(TRIM(entitlement_scope), ''), 'all') "
            "WHERE entitlement_scope IS NULL OR NULLIF(TRIM(entitlement_scope), '') IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET archive_days_threshold = COALESCE(archive_days_threshold, %s) "
            "WHERE archive_days_threshold IS NULL;",
            (int(DEFAULT_ARCHIVE_DAYS_THRESHOLD),)
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET article_discount_pct = COALESCE(article_discount_pct, 0) "
            "WHERE article_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET issue_discount_pct = COALESCE(issue_discount_pct, 0) "
            "WHERE issue_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET subscription_discount_pct = COALESCE(subscription_discount_pct, 0) "
            "WHERE subscription_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET monthly_download_limit = COALESCE(monthly_download_limit, 0) "
            "WHERE monthly_download_limit IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET required_academic_positions = COALESCE(required_academic_positions, ARRAY[]::text[]) "
            "WHERE required_academic_positions IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET requires_verified_document = COALESCE(requires_verified_document, false) "
            "WHERE requires_verified_document IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET feature_permissions = COALESCE(feature_permissions, ARRAY[]::text[]) "
            "WHERE feature_permissions IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs "
            "SET required_document_types = COALESCE(required_document_types, ARRAY[]::text[]) "
            "WHERE required_document_types IS NULL;"
        )
        dbc.conn.commit()
        cursor.close()
        dbc._init_tables()
        dbc._init_columns()
    except Exception as e:
        print(f"Tariff entitlement columns sync warning: {e}")
        try:
            dbc.conn.rollback()
        except Exception:
            pass


def _ensure_user_doc_upload_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(dbc.columns.get('user_doc_uploads', []))
        if not existing_columns:
            return
        missing_columns = []
        if 'document_type' not in existing_columns:
            missing_columns.append(('document_type', 'text'))
        if 'document_holder_name' not in existing_columns:
            missing_columns.append(('document_holder_name', 'text'))
        if 'institution_name' not in existing_columns:
            missing_columns.append(('institution_name', 'text'))
        if not missing_columns:
            return

        cursor = dbc.conn.cursor()
        for column_name, column_type in missing_columns:
            cursor.execute(f"ALTER TABLE user_doc_uploads ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        cursor.execute(
            "UPDATE user_doc_uploads "
            "SET document_type = COALESCE(document_type, 'other_academic') "
            "WHERE COALESCE(TRIM(file_path), '') <> '' AND (document_type IS NULL OR TRIM(document_type) = '');"
        )
        dbc.conn.commit()
        cursor.close()
        dbc._init_tables()
        dbc._init_columns()
    except Exception as e:
        print(f"User document columns sync warning: {e}")
        try:
            dbc.conn.rollback()
        except Exception:
            pass


_refresh_submission_columns()


def run_runtime_schema_syncs():
    _refresh_submission_columns()
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    _ensure_submission_columns()
    _ensure_user_columns()
    _ensure_role_notifications_table()
    _ensure_payment_columns()
    _ensure_tariff_entitlement_columns()
    _ensure_user_doc_upload_columns()


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


def _serialize_author_profile(author_profile, include_private=False):
    author = author_profile or {}
    payload = {
        'id': _parse_int(author.get('id')),
        'name': _clean_text(author.get('name')),
        'organization': _clean_text(author.get('organization')),
        'department': _clean_text(author.get('department')),
        'position': _clean_text(author.get('position')),
        'orcid': _clean_text(author.get('orcid')),
    }
    if include_private:
        payload.update({
            'email': _clean_text(author.get('email')),
            'phone': _clean_text(author.get('phone')),
            'address_street': _clean_text(author.get('address_street')),
            'address_city': _clean_text(author.get('address_city')),
            'address_country': _clean_text(author.get('address_country')),
            'address_zip': _clean_text(author.get('address_zip')),
        })
    return payload


def _default_author_name_from_user(user_row):
    user = user_row or {}
    full_name = _clean_text(f"{user.get('name') or ''} {user.get('second_name') or ''}")
    return full_name or _clean_text(user.get('name'))


def _get_or_create_author_profile_for_user(user_id):
    user_id_int = _parse_int(user_id)
    if user_id_int is None:
        return None

    try:
        author_rows = dbc.author_profile.get(user_id=user_id_int).exec()
    except Exception:
        author_rows = []
    if author_rows:
        return author_rows[0]

    try:
        user_rows = dbc.users.get(id=user_id_int).exec()
    except Exception:
        user_rows = []
    if not user_rows:
        return None

    user_row = user_rows[0]
    author_name = _default_author_name_from_user(user_row)
    if not author_name:
        return None

    now_ts = int(time.time())
    profile_payload = {
        'user_id': user_id_int,
        'name': author_name,
        'organization': _clean_text(user_row.get('work')),
        'department': None,
        'position': _clean_text(user_row.get('work_title')),
        'email': _clean_text(user_row.get('email')),
        'phone': _clean_text(user_row.get('phone')),
        'orcid': None,
        'address_street': None,
        'address_city': None,
        'address_country': None,
        'address_zip': None,
        'created_at': now_ts,
        'updated_at': now_ts,
    }
    try:
        created_rows = dbc.author_profile.add(**profile_payload).exec()
    except Exception:
        created_rows = []
    if created_rows:
        return created_rows[0]

    try:
        author_rows = dbc.author_profile.get(user_id=user_id_int).exec()
    except Exception:
        author_rows = []
    return author_rows[0] if author_rows else None


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


def _default_currency_for_language():
    language = (_clean_text(session.get('language')) or 'en').lower()
    return LANGUAGE_DEFAULT_CURRENCY.get(language, 'usd')


def _resolve_tariff_price_and_currency(tariff, currency):
    selected_key = TARIFF_CURRENCY_FIELDS[currency]
    selected_value = tariff.get(selected_key)
    selected_currency = currency

    return _parse_float(selected_value, 0.0), selected_currency


def _resolve_tariff_price(tariff, currency):
    amount, _ = _resolve_tariff_price_and_currency(tariff, currency)
    return amount


def _user_is_verified(user_id):
    if not user_id:
        return False
    user_rows = dbc.users.get(id=user_id).exec()
    user = user_rows[0] if user_rows else {}
    if user.get('is_verified'):
        return True
    user_docs = dbc.user_doc_uploads.get(user_id=user_id).exec()
    for user_doc in user_docs:
        status = _clean_text(user_doc.get('verification_status'))
        if status and status.lower() in {'verified', 'approved'}:
            return True
    return False


def _is_tariff_archived(tariff):
    if not tariff:
        return True
    value = tariff.get('is_archived')
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


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


def _normalize_entitlement_scope(value):
    normalized = (_clean_text(value) or 'all').lower()
    return normalized if normalized in TARIFF_ENTITLEMENT_SCOPES else 'all'


def _normalize_academic_position(value):
    normalized = (_clean_text(value) or '').lower()
    normalized = normalized.replace('’', "'")
    normalized = ACADEMIC_POSITION_ALIASES.get(normalized, normalized)
    return normalized if normalized in ALLOWED_ACADEMIC_POSITIONS else None


def _academic_position_label(value):
    normalized = _normalize_academic_position(value)
    if not normalized:
        return ''
    return ACADEMIC_POSITION_LABELS.get(normalized, normalized.replace('_', ' ').title())


def _parse_required_positions(value):
    raw_items = []
    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        text = str(value or '').strip()
        if text.startswith('{') and text.endswith('}'):
            text = text[1:-1]
        raw_items = [item.strip().strip('"').strip("'") for item in text.split(',') if item.strip()]

    normalized_items = []
    for item in raw_items:
        normalized = _normalize_academic_position(item)
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


def _parse_text_array(value):
    if isinstance(value, (list, tuple, set)):
        return [str(item or '').strip() for item in value if str(item or '').strip()]
    text = str(value or '').strip()
    if text.startswith('{') and text.endswith('}'):
        text = text[1:-1]
    return [item.strip().strip('"').strip("'") for item in text.split(',') if item.strip()]


def _normalize_feature_permission(value):
    normalized = (_clean_text(value) or '').lower()
    return normalized if normalized in ALLOWED_TARIFF_FEATURE_PERMISSIONS else None


def _parse_feature_permissions(value):
    normalized_items = []
    for item in _parse_text_array(value):
        normalized = _normalize_feature_permission(item)
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


def _tariff_feature_permissions(tariff):
    return _parse_feature_permissions((tariff or {}).get('feature_permissions'))


def _tariff_has_feature_permission(tariff, permission_key):
    permission = _normalize_feature_permission(permission_key)
    if not permission:
        return False
    permissions = _tariff_feature_permissions(tariff)
    if permissions:
        return permission in permissions

    # Backward compatibility for old tariffs without explicit permissions matrix.
    scope = _normalize_entitlement_scope((tariff or {}).get('entitlement_scope'))
    if permission in {'access_latest_content', 'access_archive_content'}:
        if scope == 'all':
            return True
        return permission == 'access_archive_content'
    return True


def _normalize_document_type(value):
    normalized = (_clean_text(value) or '').lower()
    normalized = normalized.replace('’', "'")
    normalized = DOCUMENT_TYPE_ALIASES.get(normalized, normalized)
    return normalized if normalized in ALLOWED_DOCUMENT_TYPES else None


def _current_interface_language():
    language = (_clean_text(session.get('language')) or 'en').lower()
    return language if language in DOCUMENT_TYPE_LOCALIZED_LABELS else 'en'


def _document_type_label(value):
    normalized = _normalize_document_type(value)
    if not normalized:
        return ''
    localized_labels = DOCUMENT_TYPE_LOCALIZED_LABELS.get(_current_interface_language(), DOCUMENT_TYPE_LOCALIZED_LABELS['en'])
    return localized_labels.get(normalized, DOCUMENT_TYPE_LABELS.get(normalized, normalized.replace('_', ' ').title()))


def _parse_required_document_types(value):
    normalized_items = []
    for item in _parse_text_array(value):
        normalized = _normalize_document_type(item)
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


def _tariff_required_document_types(tariff):
    return _parse_required_document_types((tariff or {}).get('required_document_types'))


def _position_document_type_candidates(position_key):
    mapping = {
        'student': ['student_id', 'enrollment_certificate'],
        'master': ['master_certificate', 'enrollment_certificate'],
        'doctoral': ['phd_certificate', 'enrollment_certificate'],
        'postgraduate': ['phd_certificate', 'enrollment_certificate'],
        'doctor': ['phd_certificate'],
        'researcher': ['researcher_certificate', 'employment_certificate'],
        'university_researcher': ['researcher_certificate', 'employment_certificate'],
        'independent_researcher': ['researcher_certificate', 'other_academic'],
        'teacher': ['employment_certificate'],
    }
    return mapping.get(position_key, [])


def _tariff_effective_required_document_types(tariff):
    # Explicit-only behavior: document requirement is applied only when admin configured document types.
    return _tariff_required_document_types(tariff)


def _user_doc_record(user_id):
    user_rows = dbc.user_doc_uploads.get(user_id=user_id).exec()
    return user_rows[0] if user_rows else {}


def _user_doc_verified(user_doc):
    status = (_clean_text((user_doc or {}).get('verification_status')) or '').lower()
    return status in {'verified', 'approved'}


def _tariff_required_positions(tariff):
    return _parse_required_positions((tariff or {}).get('required_academic_positions'))


def _tariff_requires_verified_document(tariff):
    return _parse_bool((tariff or {}).get('requires_verified_document'))


def _user_document_type(user_doc):
    return _normalize_document_type((user_doc or {}).get('document_type'))


def _normalize_name_for_match(value):
    return ' '.join((_clean_text(value) or '').lower().split())


def _account_full_name(user_row):
    user = user_row or {}
    return _clean_text(f"{user.get('name') or ''} {user.get('second_name') or ''}")


def _document_holder_matches_user(user_doc, user_row):
    document_holder_name = _normalize_name_for_match((user_doc or {}).get('document_holder_name'))
    account_full_name = _normalize_name_for_match(_account_full_name(user_row))
    if not document_holder_name or not account_full_name:
        return False
    return document_holder_name == account_full_name


def _validate_tariff_eligibility_for_user(tariff, user_id):
    tariff_row = tariff or {}
    user_doc = _user_doc_record(user_id)
    user_rows = dbc.users.get(id=user_id).exec()
    user_row = user_rows[0] if user_rows else {}
    required_document_types = _tariff_effective_required_document_types(tariff_row)
    user_document_type = _user_document_type(user_doc)
    user_document_path = _clean_text(user_doc.get('file_path'))

    if required_document_types:
        if not user_document_path:
            return False, 'Academic supporting document is required for this tariff.'
        if user_document_type not in required_document_types:
            labels = [_document_type_label(item) for item in required_document_types if _document_type_label(item)]
            if labels:
                return False, f"Required document type: {', '.join(labels)}."
            return False, 'Required academic document type is not uploaded.'
        if not _document_holder_matches_user(user_doc, user_row):
            return False, 'Document holder full name must match your account first and last name.'

    if required_document_types and _tariff_requires_verified_document(tariff_row) and not _user_doc_verified(user_doc):
        return False, 'Verified academic document is required for this tariff.'

    if tariff_row.get('is_verified') and not _user_is_verified(user_id):
        msg = t('verification_required_for_tariff')
        if msg == 'verification_required_for_tariff':
            msg = 'Verification required to access this tariff'
        return False, msg

    return True, None


def _normalize_discount_percent(value):
    percent = _parse_float(value, 0.0)
    if percent < 0:
        return 0.0
    if percent > 100:
        return 100.0
    return percent


def _apply_discount_percent(amount, discount_percent):
    base_amount = _parse_float(amount, 0.0)
    percent = _normalize_discount_percent(discount_percent)
    if percent <= 0:
        return round(base_amount, 2)
    if percent >= 100:
        return 0.0
    discounted = base_amount * ((100.0 - percent) / 100.0)
    return round(max(discounted, 0.0), 2)


def _effective_tariff_discount_percent(tariff, field_name):
    permission_map = {
        'article_discount_pct': 'article_discount',
        'issue_discount_pct': 'issue_discount',
    }
    permission = permission_map.get(field_name)
    if permission and not _tariff_has_feature_permission(tariff, permission):
        return 0.0
    return _normalize_discount_percent((tariff or {}).get(field_name))


def _tariff_subscription_discount_context(tariff, now_ts=None):
    tariff_row = tariff or {}
    now_value = _parse_int(now_ts)
    if now_value is None:
        now_value = int(time.time())

    discount_percent = _normalize_discount_percent(tariff_row.get('subscription_discount_pct'))
    start_at = _parse_int(tariff_row.get('subscription_discount_start_at'))
    end_at = _parse_int(tariff_row.get('subscription_discount_end_at'))

    if discount_percent <= 0:
        return {
            'active': False,
            'discount_percent': 0.0,
            'start_at': start_at,
            'end_at': end_at,
        }

    if start_at is not None and now_value < start_at:
        return {
            'active': False,
            'discount_percent': discount_percent,
            'start_at': start_at,
            'end_at': end_at,
        }
    if end_at is not None and now_value > end_at:
        return {
            'active': False,
            'discount_percent': discount_percent,
            'start_at': start_at,
            'end_at': end_at,
        }

    return {
        'active': True,
        'discount_percent': discount_percent,
        'start_at': start_at,
        'end_at': end_at,
    }


def _apply_subscription_discount_to_amount(amount, tariff):
    context = _tariff_subscription_discount_context(tariff)
    if not context.get('active'):
        return round(_parse_float(amount, 0.0), 2), context
    discounted = _apply_discount_percent(amount, context.get('discount_percent'))
    return discounted, context


def _user_subscription_is_active(user_row):
    user = user_row or {}
    end_ts = _parse_int(user.get('subscription_end_date'))
    if end_ts is None:
        return False
    return end_ts > int(time.time())


def _extract_content_timestamp(record, fallback_year_key=None):
    row = record or {}
    for key in ('date_publish', 'published_at', 'created_at', 'created_date'):
        timestamp = _parse_int(row.get(key))
        if timestamp and timestamp > 0:
            return timestamp

    if fallback_year_key:
        year = _parse_int(row.get(fallback_year_key))
        if year and 1970 <= year <= 2100:
            try:
                return int(time.mktime(time.strptime(f'{year}-01-01', '%Y-%m-%d')))
            except Exception:
                return None
    return None


def _record_age_days(timestamp):
    timestamp_int = _parse_int(timestamp)
    if timestamp_int is None:
        return None
    seconds = int(time.time()) - timestamp_int
    if seconds < 0:
        return 0
    return seconds // (24 * 60 * 60)


def _tariff_allows_issue_access(tariff, issue):
    tariff_row = tariff or {}
    permissions = _tariff_feature_permissions(tariff_row)
    threshold_days = _parse_int(tariff_row.get('archive_days_threshold'))
    if threshold_days is None or threshold_days < 1:
        threshold_days = DEFAULT_ARCHIVE_DAYS_THRESHOLD

    if permissions:
        issue_timestamp = _extract_content_timestamp(issue, fallback_year_key='year')
        age_days = _record_age_days(issue_timestamp)
        if age_days is None:
            return False
        if age_days >= threshold_days:
            return 'access_archive_content' in permissions
        return 'access_latest_content' in permissions

    scope = _normalize_entitlement_scope(tariff_row.get('entitlement_scope'))
    if scope == 'all':
        return True

    issue_timestamp = _extract_content_timestamp(issue, fallback_year_key='year')
    age_days = _record_age_days(issue_timestamp)
    if age_days is None:
        return False
    return age_days >= threshold_days


def _tariff_allows_publication_access(tariff, publication):
    tariff_row = tariff or {}
    permissions = _tariff_feature_permissions(tariff_row)
    threshold_days = _parse_int(tariff_row.get('archive_days_threshold'))
    if threshold_days is None or threshold_days < 1:
        threshold_days = DEFAULT_ARCHIVE_DAYS_THRESHOLD

    if permissions:
        publication_timestamp = _extract_content_timestamp(publication)
        if publication_timestamp is None:
            issue_id = _parse_int((publication or {}).get('issue_id'))
            if issue_id is not None:
                issue_rows = dbc.issues.get(id=issue_id).exec()
                if issue_rows:
                    publication_timestamp = _extract_content_timestamp(issue_rows[0], fallback_year_key='year')

        age_days = _record_age_days(publication_timestamp)
        if age_days is None:
            return False
        if age_days >= threshold_days:
            return 'access_archive_content' in permissions
        return 'access_latest_content' in permissions

    scope = _normalize_entitlement_scope(tariff_row.get('entitlement_scope'))
    if scope == 'all':
        return True

    publication_timestamp = _extract_content_timestamp(publication)
    if publication_timestamp is None:
        issue_id = _parse_int((publication or {}).get('issue_id'))
        if issue_id is not None:
            issue_rows = dbc.issues.get(id=issue_id).exec()
            if issue_rows:
                publication_timestamp = _extract_content_timestamp(issue_rows[0], fallback_year_key='year')

    age_days = _record_age_days(publication_timestamp)
    if age_days is None:
        return False
    return age_days >= threshold_days


def _active_subscription_tariff_for_user(user_id):
    user_rows = dbc.users.get(id=user_id).exec()
    user = user_rows[0] if user_rows else {}
    if not _user_subscription_is_active(user):
        return None

    tariff_id = _parse_int(user.get('tariff_id'))
    if tariff_id is None:
        return None
    tariff_rows = dbc.tariffs.get(id=tariff_id).exec()
    return tariff_rows[0] if tariff_rows else None


def _subscription_grants_issue_access(user_id, issue):
    user_rows = dbc.users.get(id=user_id).exec()
    user = user_rows[0] if user_rows else {}
    if not _user_subscription_is_active(user):
        return False

    tariff = _active_subscription_tariff_for_user(user_id)
    if tariff is None:
        # Legacy subscription: active end_date without linked tariff.
        return True
    return _tariff_allows_issue_access(tariff, issue)


def _subscription_grants_article_access(user_id, publication):
    user_rows = dbc.users.get(id=user_id).exec()
    user = user_rows[0] if user_rows else {}
    if not _user_subscription_is_active(user):
        return False

    tariff = _active_subscription_tariff_for_user(user_id)
    if tariff is None:
        # Legacy subscription: active end_date without linked tariff.
        return True
    return _tariff_allows_publication_access(tariff, publication)


def _user_has_paid_access(user_id, payment_type, target_id):
    user_id_int = _parse_int(user_id)
    if user_id_int is None or target_id is None:
        return False

    target_text = str(target_id)
    payments = dbc.payments.get(user_id=user_id_int, status='paid').exec()
    for payment in payments:
        if (_clean_text(payment.get('payment_type')) or '').lower() != payment_type:
            continue
        payment_ids = payment.get('ids') or []
        if not isinstance(payment_ids, (list, tuple)):
            continue
        if target_text in {str(item) for item in payment_ids}:
            return True
    return False


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


def _payment_columns():
    try:
        columns_map = getattr(dbc, 'columns', {}) or {}
        return set(columns_map.get('payments', []))
    except Exception:
        return set()


def _create_or_get_pending_payment(user_id, payment_type, target_id, payment_data):
    lock_name = f"payment:{payment_type}:{user_id}:{target_id}"
    with dbc._lock:
        cursor = dbc.conn.cursor()
        try:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s)::bigint)", (lock_name,))
            cursor.execute(
                "SELECT id, ids FROM payments "
                "WHERE user_id = %s AND payment_type = %s AND status = ANY(%s) "
                "ORDER BY id DESC",
                (user_id, payment_type, ['unpaid', 'pending']),
            )
            for row in cursor.fetchall():
                existing_id = _parse_int(row[0])
                existing_ids = row[1] or []
                if not isinstance(existing_ids, (list, tuple)):
                    continue
                if str(target_id) in {str(item) for item in existing_ids}:
                    dbc.conn.commit()
                    return {'created': False, 'payment_id': existing_id}

            insert_columns = [
                'user_id',
                'status',
                'currency',
                'payment_type',
                'payment_date',
                'amount',
                'ids',
                'proof',
                'note',
                'created_at',
            ]
            insert_values = [
                payment_data.get('user_id'),
                payment_data.get('status'),
                payment_data.get('currency'),
                payment_data.get('payment_type'),
                payment_data.get('payment_date'),
                payment_data.get('amount'),
                payment_data.get('ids'),
                payment_data.get('proof'),
                payment_data.get('note'),
                payment_data.get('created_at'),
            ]

            payment_columns = _payment_columns()
            if 'snapshot_duration_days' in payment_columns:
                insert_columns.append('snapshot_duration_days')
                insert_values.append(_parse_int(payment_data.get('snapshot_duration_days')))

            placeholders = ', '.join(['%s'] * len(insert_columns))
            cursor.execute(
                f"INSERT INTO payments ({', '.join(insert_columns)}) VALUES ({placeholders}) RETURNING id",
                tuple(insert_values),
            )
            inserted_row = cursor.fetchone()
            payment_id = _parse_int(inserted_row[0]) if inserted_row else None
            dbc.conn.commit()
            return {'created': True, 'payment_id': payment_id}
        except Exception:
            dbc.conn.rollback()
            raise
        finally:
            cursor.close()


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


def _resolve_localized_text(value, user_row=None):
    if isinstance(value, dict):
        preferred = normalize_notification_language(
            (user_row or {}).get('ui_language'),
            default=current_notification_language()
        )
        fallback_order = [preferred, 'uz', 'ru', 'en']
        for language in fallback_order:
            text = _clean_text(value.get(language))
            if text:
                return text
        for text in value.values():
            resolved = _clean_text(text)
            if resolved:
                return resolved
        return None
    return _clean_text(value)


def _localized_map_for_email(value, user_row=None):
    if isinstance(value, dict):
        localized = {}
        for language in ('uz', 'ru', 'en'):
            text = _clean_text(value.get(language))
            if text:
                localized[language] = text
        if localized:
            return localized
        fallback_text = _resolve_localized_text(value, user_row=user_row)
        if fallback_text:
            return {'uz': fallback_text}
        return {}

    resolved = _clean_text(value)
    if not resolved:
        return {}
    return {'uz': resolved}


def _format_multilingual_text(value, user_row=None, separator=' | ', include_labels=False):
    localized_map = _localized_map_for_email(value, user_row=user_row)
    if not localized_map:
        return ''

    parts = []
    for language in ('uz', 'ru', 'en'):
        text = _clean_text(localized_map.get(language))
        if not text:
            continue
        if include_labels:
            parts.append(f'[{language.upper()}] {text}')
        else:
            parts.append(text)

    if not parts:
        for text in localized_map.values():
            resolved = _clean_text(text)
            if resolved:
                return resolved
        return ''

    return separator.join(parts)


def _normalize_localized_details(details, user_row=None, multilingual=False):
    normalized = []
    for label, value in details or []:
        if multilingual:
            label_text = _format_multilingual_text(
                label,
                user_row=user_row,
                separator=' / ',
                include_labels=False,
            )
            value_text = _format_multilingual_text(
                value,
                user_row=user_row,
                separator=' / ',
                include_labels=False,
            )
        else:
            label_text = _resolve_localized_text(label, user_row=user_row)
            value_text = _resolve_localized_text(value, user_row=user_row)
        if not label_text or not value_text:
            continue
        normalized.append((label_text, value_text))
    return normalized


def _normalize_localized_body_lines(body_lines, user_row=None, multilingual=False):
    normalized = []
    for line in body_lines or []:
        if multilingual:
            line_text = _format_multilingual_text(
                line,
                user_row=user_row,
                separator=' | ',
                include_labels=True,
            )
        else:
            line_text = _resolve_localized_text(line, user_row=user_row)
        if line_text:
            normalized.append(line_text)
    return normalized


def _send_user_email(user_row, subject, intro, details=None, body_lines=None, cta_url=None, cta_label=None, reply_to=None):
    email = _clean_text((user_row or {}).get('email'))
    if not email or not user_allows_email_notifications(user_row):
        return False
    preferred_language = normalize_notification_language(
        (user_row or {}).get('ui_language'),
        default=current_notification_language()
    )
    subject_text = _format_multilingual_text(
        subject,
        user_row=user_row,
        separator=' | ',
        include_labels=False,
    )
    intro_text = _format_multilingual_text(
        intro,
        user_row=user_row,
        separator=' | ',
        include_labels=True,
    )

    if not subject_text or not intro_text:
        fallback_subject, fallback_intro, _ = prepare_notification_content(
            title=subject,
            message=intro,
            default_language=preferred_language
        )
        subject_text = subject_text or fallback_subject
        intro_text = intro_text or fallback_intro

    details_rows = _normalize_localized_details(
        details,
        user_row=user_row,
        multilingual=True,
    )
    body_rows = _normalize_localized_body_lines(
        body_lines,
        user_row=user_row,
        multilingual=True,
    )
    cta_label_text = _format_multilingual_text(
        cta_label,
        user_row=user_row,
        separator=' / ',
        include_labels=False,
    ) or 'Open'
    return send_notification_email(
        recipients=[email],
        subject=subject_text,
        intro=intro_text,
        details=details_rows,
        body_lines=body_rows,
        cta_url=cta_url,
        cta_label=cta_label_text,
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

    if payment_type == 'subscription':
        subject = localized_texts(
            "Obuna to'lovi uchun so'rov yaratildi",
            'Создан запрос на оплату подписки',
            'Subscription payment request created',
        )
        intro = localized_texts(
            "Akkauntingiz uchun yangi obuna to'lovi so'rovi yaratildi.",
            'Для вашего аккаунта создан новый запрос на оплату подписки.',
            'A new subscription payment request has been created for your account.',
        )
        payment_type_label = localized_texts("Obuna", "Подписка", "Subscription")
    elif payment_type == 'article':
        subject = localized_texts(
            "Maqola xaridi uchun to'lov so'rovi yaratildi",
            'Создан запрос на оплату покупки статьи',
            'Article purchase payment request created',
        )
        intro = localized_texts(
            "Akkauntingiz uchun yangi maqola xaridi to'lovi so'rovi yaratildi.",
            'Для вашего аккаунта создан новый запрос на оплату покупки статьи.',
            'A new article purchase payment request has been created for your account.',
        )
        payment_type_label = localized_texts("Maqola xaridi", "Покупка статьи", "Article purchase")
    else:
        subject = localized_texts(
            "Son xaridi uchun to'lov so'rovi yaratildi",
            'Создан запрос на оплату покупки выпуска',
            'Issue purchase payment request created',
        )
        intro = localized_texts(
            "Akkauntingiz uchun yangi son xaridi to'lovi so'rovi yaratildi.",
            'Для вашего аккаунта создан новый запрос на оплату покупки выпуска.',
            'A new issue purchase payment request has been created for your account.',
        )
        payment_type_label = localized_texts("Son xaridi", "Покупка выпуска", "Issue purchase")
    return _send_user_email(
        user_row,
        subject=subject,
        intro=intro,
        details=[],
        body_lines=[
            localized_texts(
                "Davom ettirish uchun dashboarddagi to'lovlar bo'limiga o'ting.",
                'Чтобы продолжить, откройте раздел оплат в личном кабинете.',
                'To continue, open the payments page in your dashboard.',
            ),
        ],
        cta_url=url_for('app__dashboard_payments'),
        cta_label=localized_texts("To'lovlarni ochish", 'Открыть оплаты', 'Open payments'),
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
            subject=localized_texts(
                'Maqolangiz yuborildi',
                'Ваша статья отправлена',
                'Your article was submitted',
            ),
            intro=localized_texts(
                f'"{title}" nomli maqolangiz Philology Matters tizimiga muvaffaqiyatli yuborildi.',
                f'Ваша статья "{title}" успешно отправлена в систему Philology Matters.',
                f'Your submission "{title}" was successfully sent to Philology Matters.',
            ),
            body_lines=[localized_texts(
                "Ko'rib chiqish jarayonini shaxsiy kabinetdagi dashboard orqali kuzatishingiz mumkin.",
                'Вы можете отслеживать процесс рассмотрения в личном кабинете.',
                'You can follow the review process from your dashboard.',
            )],
            cta_url='/dashboard/articles',
            cta_label=localized_texts("Dashboardga o'tish", 'Перейти в кабинет', 'Go to dashboard'),
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
            subject=localized_texts(
                f'Yangi maqola keldi: {title}',
                f'Поступила новая заявка: {title}',
                f'New submission received: {title}',
            ),
            intro=localized_texts(
                "Tahririyat jarayoniga yangi maqola qo'shildi.",
                'В редакционный процесс поступила новая заявка.',
                'A new submission has entered the editorial workflow.',
            ),
            details=[
                (localized_texts('Muallif', 'Автор', 'Author'), _user_display_name(author_row)),
            ],
            body_lines=[localized_texts(
                "Maqola tafsilotlarini ko'rish uchun admin panelni oching.",
                'Откройте админ-панель, чтобы посмотреть детали заявки.',
                'Open the admin panel to review the submission details.',
            )],
            cta_url=action_url,
            cta_label=localized_texts("Maqolani ochish", 'Открыть заявку', 'Open submission'),
            reply_to=author_email or None,
        )


def _notify_submission_antiplagiarism_uploaded(submission, actor_user_id=None, is_resubmission=False):
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

    if is_resubmission:
        message = localized_texts(
            f'"{title}" uchun muallif TUZATILGAN antiplagiat hujjatini qayta yukladi. Qayta ko\'rib chiqing',
            f'Автор загрузил ИСПРАВЛЕННЫЙ антиплагиат-документ для "{title}". Требуется повторная проверка',
            f'The author re-uploaded a REVISED anti-plagiarism document for "{title}". Needs re-review'
        )
    else:
        message = localized_texts(
            f'"{title}" uchun muallif antiplagiat hujjatini yukladi',
            f'Автор загрузил антиплагиат-документ для "{title}"',
            f'The author uploaded an anti-plagiarism document for "{title}"'
        )
    admin_title = localized_texts(
        "Antiplagiat hujjati qayta yuklandi" if is_resubmission else "Antiplagiat hujjati yuklandi",
        "Антиплагиат-документ загружен повторно" if is_resubmission else "Антиплагиат-документ загружен",
        "Anti-plagiarism document re-uploaded" if is_resubmission else "Anti-plagiarism document uploaded"
    )
    assigned_admin_id = _parse_int((submission or {}).get('assigned_admin_id'))
    if assigned_admin_id is not None:
        _create_role_notification(
            target_user_id=assigned_admin_id,
            target_role='admin',
            title=admin_title,
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
            title=admin_title,
            message=message,
            action_url=action_url,
            level='info',
            event_type='submission_antiplagiarism_uploaded',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id_int
        )

    _notify_role_users(
        'superadmin',
        title=admin_title,
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
            subject=localized_texts(
                f'Antiplagiat hujjati qabul qilindi: {title}',
                f'Антиплагиат-документ получен: {title}',
                f'Anti-plagiarism file received: {title}',
            ),
            intro=localized_texts(
                f'"{title}" uchun yuborgan antiplagiat hujjatingiz qabul qilindi.',
                f'Ваш антиплагиат-документ для "{title}" успешно получен.',
                f'Your anti-plagiarism document for "{title}" has been received.',
            ),
            body_lines=[localized_texts(
                'Endi tahririyat jamoasi ko‘rib chiqish jarayonini davom ettirishi mumkin.',
                'Теперь редакционная команда может продолжить процесс рассмотрения.',
                'The editorial team can now continue the review workflow.',
            )],
            cta_url='/dashboard/articles',
            cta_label=localized_texts("Dashboardga o'tish", 'Перейти в кабинет', 'Go to dashboard'),
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
            subject=localized_texts(
                f'Antiplagiat hujjati yuklandi: {title}',
                f'Загружен антиплагиат-документ: {title}',
                f'Anti-plagiarism file uploaded: {title}',
            ),
            intro=localized_texts(
                f'Muallif "{title}" uchun antiplagiat hujjatini yukladi.',
                f'Автор загрузил антиплагиат-документ для "{title}".',
                f'The author uploaded an anti-plagiarism document for "{title}".',
            ),
            body_lines=[localized_texts(
                "Ko'rib chiqishni davom ettirish uchun admin panelni oching.",
                'Откройте админ-панель, чтобы продолжить рассмотрение.',
                'Open the admin panel to continue the review process.',
            )],
            cta_url=action_url,
            cta_label=localized_texts("Maqolani ochish", 'Открыть заявку', 'Open submission'),
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


def _compute_revision_reentry(existing):
    """Decide where a submission re-enters the pipeline once the author fixes
    it and resubmits, based on its current (resubmittable) status -- the
    status value alone now carries this, no separate rejection_origin needed.
    Returns (status, needs_editor_reactivation)."""
    current_status = str((existing or {}).get('status') or '').strip().lower()
    if current_status == 'revision_required':
        # 'minor' (see submissions.revision_severity, set by whoever opened
        # this revision round): the fix goes straight back to the same
        # admin/editor queue for a quick look, WITHOUT resetting editor
        # assignments to 'pending' -- a full new review round for a small
        # fix is exactly the "feels like starting from zero" complaint this
        # distinction exists to avoid (matches the common "minor revision"
        # vs "major revision" split used by real editorial workflows).
        # 'major' (or missing/legacy) keeps the original full re-review.
        severity = str((existing or {}).get('revision_severity') or 'major').strip().lower()
        return 'under_review', severity != 'minor'
    if current_status == 'antiplagiarism_failed':
        # Author edited the manuscript itself (not just the checked-file
        # re-upload, which has its own path in app__api_article_upload) --
        # a fresh plagiarism check is warranted for the new content.
        return 'plagiarism_check', False
    # 'failed_technical_check' (or any unexpected/legacy value): safest,
    # most conservative re-entry point -- redo the technical check. No need
    # to clear anti_plagiarism_file: the upload flow already supports
    # re-uploading while status=='plagiarism_check'.
    return 'pending', False


def _resolve_latest_revision_round(submission_id, now_ts=None):
    """Close out the open `submission_revision_rounds` entry for this
    submission once the author resubmits -- so the author's history list
    shows it as done instead of still "pending", and so it never gets
    confused with a later, unrelated round (the bug that made the old single
    mutable `editor_shared_file` field look stale after publication)."""
    try:
        rows = dbc.submission_revision_rounds.get(submission_id=submission_id).exec()
    except Exception:
        return
    open_rounds = [row for row in rows if row.get('resolved_at') is None]
    if not open_rounds:
        return
    latest = max(open_rounds, key=lambda row: _parse_int(row.get('round_number')) or 0)
    latest_id = _parse_int(latest.get('id'))
    if latest_id is None:
        return
    dbc.submission_revision_rounds.get(id=latest_id).update(resolved_at=now_ts or int(time.time())).exec()


def _reactivate_editor_assignments_for_revision(submission_id):
    """Reset this submission's already-reviewed editor assignments back to
    'pending' with fresh deadlines, so the SAME reviewer(s) see the revised
    manuscript -- preserving blind-review continuity across revision cycles."""
    now_ts = int(time.time())
    acceptance_deadline_at = now_ts + 24 * 60 * 60
    completion_deadline_at = now_ts + 5 * 24 * 60 * 60

    try:
        assignment_rows = dbc.editor_assignments.get(submission_id=submission_id).any(
            status=list(EDITOR_ASSIGNMENT_REVIEWED_STATUS_VALUES)
        ).exec()
    except Exception:
        logger.exception('Failed to load editor_assignments for revision reactivation, submission_id=%s', submission_id)
        return []

    reactivated_editor_ids = []
    for assignment in assignment_rows:
        assignment_id = _parse_int(assignment.get('id'))
        if assignment_id is None:
            continue
        next_round = (_parse_int(assignment.get('revision_round')) or 1) + 1
        try:
            dbc.editor_assignments.get(id=assignment_id).update(
                status='pending',
                admin_decision='pending',
                reviewed_at=None,
                revision_round=next_round,
                acceptance_deadline_at=acceptance_deadline_at,
                completion_deadline_at=completion_deadline_at,
                accepted_at=None,
                acceptance_reminder_level='',
                completion_reminder_level='',
                updated_at=now_ts
            ).exec()
            editor_id = _parse_int(assignment.get('editor_id'))
            if editor_id is not None:
                reactivated_editor_ids.append(editor_id)
        except Exception:
            logger.exception('Failed to reactivate editor_assignment id=%s for revision', assignment_id)
    return reactivated_editor_ids


def _log_submission_revision(existing, actor_user_id, now_ts):
    """Snapshot the pre-resubmit rejection state into submission_revision_log
    before it gets cleared on the submission row -- this is the durable
    audit trail of "who rejected it, why, and when it was fixed"."""
    submission_id = _parse_int((existing or {}).get('id'))
    if submission_id is None:
        return
    try:
        dbc.submission_revision_log.add(
            submission_id=submission_id,
            revision_number=_parse_int((existing or {}).get('revision_number')) or 1,
            rejection_origin=_clean_text((existing or {}).get('rejection_origin')) or None,
            rejected_by=_parse_int((existing or {}).get('rejected_by')),
            rejected_at=_parse_int((existing or {}).get('rejected_at')),
            rejection_notes=_clean_text((existing or {}).get('notes')) or None,
            resubmitted_at=now_ts,
            resubmitted_by=_parse_int(actor_user_id),
            created_at=now_ts
        ).exec()
    except Exception:
        logger.exception('Failed to write submission_revision_log for submission_id=%s', submission_id)


def _notify_submission_revision_resubmitted(submission, actor_user_id, reactivated_editor_ids):
    submission_id = _parse_int((submission or {}).get('id'))
    if submission_id is None:
        return
    title = _submission_title(submission)
    action_url = f"/fmadmin/submissions/{submission_id}"

    assigned_admin_id = _parse_int((submission or {}).get('assigned_admin_id'))
    if assigned_admin_id is not None:
        _create_role_notification(
            target_user_id=assigned_admin_id,
            target_role='admin',
            title=localized_texts(
                "Maqola tuzatilib qayta yuborildi",
                "Статья исправлена и отправлена повторно",
                "Submission was revised and resubmitted"
            ),
            message=localized_texts(
                f'"{title}" muallif tomonidan tuzatilib qayta yuborildi',
                f'Статья "{title}" исправлена автором и отправлена повторно',
                f'"{title}" was fixed by the author and resubmitted'
            ),
            action_url=action_url,
            level='info',
            event_type='submission_revised',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id
        )

    for editor_id in reactivated_editor_ids:
        _create_role_notification(
            target_user_id=editor_id,
            target_role='editor',
            title=localized_texts(
                "Qayta ko'rib chiqilgan maqola",
                "Пересмотренная статья",
                "Revised submission"
            ),
            message=localized_texts(
                f'"{title}" muallif tomonidan tuzatildi, qayta ko\'rib chiqishingiz kerak',
                f'Статья "{title}" исправлена автором, требуется повторная рецензия',
                f'"{title}" was revised by the author and needs another review'
            ),
            action_url='/fmadmin/editor-assignments',
            level='info',
            event_type='submission_revised',
            related_submission_id=submission_id,
            actor_user_id=actor_user_id
        )

    _notify_role_users(
        'superadmin',
        title=localized_texts(
            "Maqola tuzatilib qayta yuborildi",
            "Статья исправлена и отправлена повторно",
            "Submission was revised and resubmitted"
        ),
        message=localized_texts(
            f'"{title}" muallif tomonidan tuzatilib qayta yuborildi',
            f'Статья "{title}" исправлена автором и отправлена повторно',
            f'"{title}" was fixed by the author and resubmitted'
        ),
        action_url=action_url,
        level='info',
        event_type='submission_revised',
        related_submission_id=submission_id,
        actor_user_id=actor_user_id
    )


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
    keywords = _parse_text_list(_coalesce(data.get('keywords'), existing.get('keywords')))
    word_count_raw = _parse_int(_coalesce(data.get('word_count'), existing.get('word_count')))
    word_count = word_count_raw if word_count_raw is not None else 0

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

    # New rows spell out their workflow defaults instead of leaning on the
    # column DEFAULT.  Development creates these columns through the runtime
    # schema sync (SUBMISSION_EXTRA_COLUMN_TYPES, nullable) while production
    # gets them from the migrations as NOT NULL, so a value missing here is a
    # bug that only ever surfaces on the server.  Keys the database does not
    # have yet are dropped by _filter_submission_payload.
    if is_new:
        payload['revision_number'] = 1
        payload['revision_allowed'] = True
        payload['revision_severity'] = 'major'
        payload['anti_plagiarism_status'] = 'pending'

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

    main_author_id = _parse_int(payload.get('main_author_id'))
    if main_author_id is None:
        errors.append('author')
    else:
        try:
            author_rows = dbc.author_profile.get(id=main_author_id).exec()
        except Exception:
            author_rows = []
        if not author_rows:
            errors.append('author')

    if len(_parse_text_list(payload.get('classifications'))) < 3:
        errors.append('classifications')

    # Both manuscript files are mandatory to submit: the anonymized copy is
    # what blind review runs on (`_can_assign_editors` in fmadmin refuses to
    # assign an editor without it), and the author copy is what gets laid out
    # for publication. Only the drafting step may be missing them -- without
    # this check a submission could reach the admin queue with no manuscript
    # at all and get stuck there, unassignable.
    if not _clean_text(payload.get('file_authors')):
        errors.append('files')
    if not _clean_text(payload.get('file_anonymized')):
        errors.append('files')

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

    return jsonify({
        'success': True,
        'is_found': True,
        'author': _serialize_author_profile(author_profile[0], include_private=False)
    })


def app__api_getcurrentauthor():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    author_profile = _get_or_create_author_profile_for_user(user_id)
    if not author_profile:
        return jsonify({'success': False, 'message': 'No author profile found for current user'})

    return jsonify({
        'success': True,
        'author': _serialize_author_profile(author_profile, include_private=True)
    })


def app__api_getclassifications():
    classifications = dbc.fix_classifications.get().exec()
    return jsonify({'success': True, 'classifications': classifications})


def _status_to_persist_on_save(existing):
    """Status a draft-save must write for this row.

    Saving may never knock a submission that already entered the pipeline back
    to 'draft'. The submit button saves first and submits second, and the
    submit step re-reads this status to decide whether this is a revision
    (`is_resubmittable` -> `_compute_revision_reentry`). Forcing 'draft' here
    made every resubmission look like a brand new submission: the revision
    round stayed open in the author's history ("Kutilmoqda" forever),
    `revision_number` never advanced, and the article re-entered the pipeline
    at 'pending' instead of going back to the editor who asked for the fix.
    """
    existing_status = (_clean_text((existing or {}).get('status')) or '').lower()
    if existing_status in ('', 'draft'):
        return 'draft'
    return existing_status


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
            status=_status_to_persist_on_save(existing),
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

    except Exception:
        logger.exception('Failed to save draft for user_id=%s', user_id)
        # A JSON body alone still defaults to HTTP 200, which hides a real
        # server failure from clients, reverse proxies and Grafana metrics.
        return jsonify({
            'success': False,
            'message': 'Unable to save draft right now. Please try again.'
        }), 500


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
            status='pending',
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

        now_ts = int(time.time())
        is_revision = bool(existing) and is_resubmittable(str(existing.get('status') or '').strip().lower())
        needs_editor_reactivation = False
        if is_revision:
            revision_status, needs_editor_reactivation = _compute_revision_reentry(existing)
            submission_payload['status'] = revision_status
            submission_payload['revision_number'] = (_parse_int(existing.get('revision_number')) or 1) + 1
            submission_payload['rejected_at'] = None
            submission_payload['rejected_by'] = None
            submission_payload['last_revision_submitted_at'] = now_ts

        db_payload = _filter_submission_payload(submission_payload)
        if submission_id:
            updated = dbc.submissions.get(id=submission_id, user_id=user_id).update(**db_payload).exec()
            saved_submission = updated[0] if updated else dbc.submissions.get(id=submission_id, user_id=user_id).exec()[0]
            if is_revision:
                _log_submission_revision(existing, actor_user_id=user_id, now_ts=now_ts)
                if str(existing.get('status') or '').strip().lower() == 'revision_required':
                    _resolve_latest_revision_round(submission_id, now_ts=now_ts)
                reactivated_editor_ids = (
                    _reactivate_editor_assignments_for_revision(submission_id)
                    if needs_editor_reactivation else []
                )
                _notify_submission_revision_resubmitted(saved_submission, actor_user_id=user_id, reactivated_editor_ids=reactivated_editor_ids)
            else:
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

    except Exception:
        logger.exception('Failed to submit article for user_id=%s', user_id)
        return jsonify({
            'success': False,
            'message': 'Unable to submit article right now. Please try again.'
        }), 500


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

        submission_status = (_clean_text((submission or {}).get('status')) or '').lower()
        is_antiplagiarism_resubmission = submission_status == 'antiplagiarism_failed'
        if file_type == 'anti_plagiarism':
            if submission_id is None or submission is None:
                return jsonify({'success': False, 'message': 'Submission not found'})

            if submission_status not in {'plagiarism_check', 'antiplagiarism_failed'}:
                return jsonify({
                    'success': False,
                    'message': 'Anti-plagiarism document can only be uploaded during the plagiarism check stage'
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
            update_payload = {
                'anti_plagiarism_file': file_ref,
                'anti_plagiarism_checked_at': now_ts,
                'anti_plagiarism_checked_by': user_id,
                'anti_plagiarism_uploaded_by_role': 'author',
                'anti_plagiarism_status': 'pending',
                'updated_at': now_ts,
            }
            if is_antiplagiarism_resubmission:
                # Status stays 'antiplagiarism_failed' on purpose -- an admin
                # must manually review the new file and move it forward
                # (mirrors the rest of the pipeline's manual gate points).
                update_payload['anti_plagiarism_resubmitted_at'] = now_ts
            dbc.submissions.get(id=submission_id, user_id=user_id).update(**update_payload).exec()
            updated_rows = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
            if updated_rows:
                _notify_submission_antiplagiarism_uploaded(
                    updated_rows[0], actor_user_id=user_id, is_resubmission=is_antiplagiarism_resubmission
                )

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


def app__api_subscription_cancel():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json() if request.is_json else request.form
    target_payment_id = _parse_int((data or {}).get('payment_id'))
    user_rows = dbc.users.get(id=user_id).exec()
    if not user_rows:
        return jsonify({'success': False, 'message': 'User not found'})

    user_row = user_rows[0]
    now_ts = int(time.time())
    current_end = _parse_int(user_row.get('subscription_end_date'))
    is_active = bool(current_end and current_end > now_ts)

    if target_payment_id is not None:
        payment_rows = dbc.payments.get(id=target_payment_id, user_id=user_id, payment_type='subscription', status='paid').exec()
        if not payment_rows:
            return jsonify({'success': False, 'message': 'Subscription payment not found'})
        payment_row = payment_rows[0]
        target_start = _parse_int(payment_row.get('snapshot_start_at'))
        target_end = _parse_int(payment_row.get('snapshot_end_at'))
        if target_end is not None and target_end <= now_ts:
            return jsonify({'success': False, 'message': "Ushbu obuna allaqachon tugagan"})
        if target_start is not None and target_start > now_ts:
            return jsonify({'success': False, 'message': "Kelajakdagi obunani hozircha bekor qilib bo'lmaydi"})

    dbc.users.get(id=user_id).update(
        tariff_id=None,
        subscription_end_date=now_ts
    ).exec()

    if is_active:
        return jsonify({
            'success': True,
            'message': "Obuna bekor qilindi. Kirish huquqi darhol to'xtatildi."
        })
    return jsonify({
        'success': True,
        'message': "Faol obuna topilmadi."
    })


def app__api_subscription_upload_document():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    _ensure_user_doc_upload_columns()

    tariff_id = _parse_int(request.form.get('tariff_id'))
    if tariff_id is None:
        return jsonify({'success': False, 'message': 'Tariff ID required'})

    tariff_rows = dbc.tariffs.get(id=tariff_id).exec()
    if not tariff_rows:
        return jsonify({'success': False, 'message': 'Tariff not found'})
    tariff = tariff_rows[0]
    if _is_tariff_archived(tariff):
        return jsonify({'success': False, 'message': 'Tariff is no longer available'})

    required_document_types = _tariff_effective_required_document_types(tariff)
    if not required_document_types:
        return jsonify({'success': False, 'message': 'This tariff does not require an activation document'})

    document_type = _normalize_document_type(request.form.get('document_type'))
    if required_document_types and document_type not in required_document_types:
        labels = [_document_type_label(item) for item in required_document_types if _document_type_label(item)]
        if labels:
            return jsonify({'success': False, 'message': 'Allowed document types: ' + ', '.join(labels)})
        return jsonify({'success': False, 'message': 'Invalid document type for this tariff'})
    if document_type is None:
        return jsonify({'success': False, 'message': 'Document type is required'})

    user_rows = dbc.users.get(id=user_id).exec()
    user_row = user_rows[0] if user_rows else {}
    document_holder_name = _clean_text(request.form.get('document_holder_name'))
    if not document_holder_name:
        return jsonify({'success': False, 'message': 'Document holder full name is required'})
    expected_account_name = _account_full_name(user_row)
    if _normalize_name_for_match(document_holder_name) != _normalize_name_for_match(expected_account_name):
        return jsonify({'success': False, 'message': 'Document holder full name must match your account name'})

    institution_name = _clean_text(request.form.get('institution_name'))
    if not institution_name:
        return jsonify({'success': False, 'message': 'University or institution name is required'})

    file = request.files.get('academic_document')
    if file is None or not _clean_text(file.filename):
        return jsonify({'success': False, 'message': 'Document file is required'})
    if not allowed_file(file.filename, {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}):
        return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PDF, DOC, DOCX, JPG, PNG'})

    ext = file.filename.rsplit('.', 1)[1].lower()
    now_ts = int(time.time())
    unique_suffix = secrets.token_hex(3)
    filename = secure_filename(f"subscription_doc_{user_id}_{now_ts}_{unique_suffix}.{ext}")
    documents_folder = os.path.join(settings.SAVE_PATH, 'private_uploads', 'documents')
    os.makedirs(documents_folder, exist_ok=True)
    file_abs_path = os.path.join(documents_folder, filename)
    file.save(file_abs_path)
    file_ref = build_private_upload_ref('documents', filename)

    existing_rows = dbc.user_doc_uploads.get(user_id=user_id).exec()
    existing_doc = existing_rows[0] if existing_rows else None
    if existing_doc:
        old_file_ref = _clean_text(existing_doc.get('file_path'))
        old_abs_path = private_upload_abspath(old_file_ref)
        update_payload = {
            'file_path': file_ref,
            'document_type': document_type,
            'document_holder_name': document_holder_name,
            'institution_name': institution_name,
            'verification_status': 'pending',
            'updated_at': now_ts,
        }
        dbc.user_doc_uploads.get(id=existing_doc.get('id')).update(**update_payload).exec()
        if old_abs_path and old_abs_path != file_abs_path and os.path.exists(old_abs_path):
            try:
                os.remove(old_abs_path)
            except OSError:
                pass
    else:
        dbc.user_doc_uploads.add(
            user_id=user_id,
            work_title=None,
            file_path=file_ref,
            document_type=document_type,
            document_holder_name=document_holder_name,
            institution_name=institution_name,
            verification_status='pending',
            created_at=now_ts,
            updated_at=now_ts
        ).exec()

    return jsonify({
        'success': True,
        'message': 'Activation document uploaded and sent for verification',
        'file_ref': file_ref,
        'download': upload_access_url(file_ref),
        'verification_status': 'pending',
        'requires_verified_document': bool(required_document_types and _tariff_requires_verified_document(tariff)),
    })


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
    if _is_tariff_archived(tariff):
        return jsonify({'success': False, 'message': 'Tariff is no longer available'})
    _ensure_user_doc_upload_columns()
    eligibility_ok, eligibility_message = _validate_tariff_eligibility_for_user(tariff, user_id)
    if not eligibility_ok:
        return jsonify({'success': False, 'message': eligibility_message or 'You are not eligible for this tariff'})

    requested_currency = _normalize_currency(data.get('currency') or _default_currency_for_language())
    base_amount, effective_currency = _resolve_tariff_price_and_currency(tariff, requested_currency)
    if base_amount <= 0:
        return jsonify({'success': False, 'message': 'Tariff price is not configured'})
    amount, discount_context = _apply_subscription_discount_to_amount(base_amount, tariff)
    if amount <= 0:
        amount = 0.0

    payment_data = {
        'user_id': user_id,
        'status': 'unpaid',
        'currency': effective_currency,
        'payment_type': 'subscription',
        'payment_date': None,
        'amount': amount,
        'ids': [tariff_id],
        'snapshot_duration_days': _parse_int(tariff.get('duration_days') or tariff.get('user_limit')),
        'proof': None,
        'note': data.get('note'),
        'created_at': int(time.time())
    }

    payment_result = _create_or_get_pending_payment(user_id, 'subscription', tariff_id, payment_data)
    payment_id = payment_result.get('payment_id')
    if payment_result.get('created') and payment_id is not None:
        _send_payment_created_email(
            user_id=user_id,
            payment_id=payment_id,
            payment_type='subscription',
            source_row=tariff,
            amount=payment_data['amount'],
            currency=effective_currency,
        )
    message = 'Subscription payment created' if payment_result.get('created') else 'Subscription payment already exists'
    return jsonify({
        'success': True,
        'message': message,
        'payment_id': payment_id,
        'amount': amount,
        'base_amount': base_amount,
        'currency': effective_currency,
        'subscription_discount_active': bool(discount_context.get('active')),
        'subscription_discount_pct': discount_context.get('discount_percent') or 0.0,
    })


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
    if not issue.get('is_paid'):
        if issue.get('subscription_enable'):
            if _subscription_grants_issue_access(user_id, issue):
                return jsonify({'success': True, 'message': 'Issue is already available with your subscription'})
            return jsonify({'success': False, 'message': 'Issue is available only via subscription'})
        return jsonify({'success': False, 'message': 'Issue is open access'})

    if _user_has_paid_access(user_id, 'issue', issue_id):
        return jsonify({'success': True, 'message': 'Issue is already purchased'})

    if _subscription_grants_issue_access(user_id, issue):
        return jsonify({'success': True, 'message': 'Issue is already available with your subscription'})

    currency = _normalize_currency(data.get('currency') or _default_currency_for_language())
    active_tariff = _active_subscription_tariff_for_user(user_id)
    issue_discount_pct = _effective_tariff_discount_percent(active_tariff, 'issue_discount_pct')
    base_amount = _resolve_issue_price(issue)
    discounted_amount = _apply_discount_percent(base_amount, issue_discount_pct)

    if discounted_amount <= 0:
        now_ts = int(time.time())
        if not _user_has_paid_access(user_id, 'issue', issue_id):
            dbc.payments.add(
                user_id=user_id,
                status='paid',
                currency=currency,
                payment_type='issue',
                payment_date=now_ts,
                amount=0,
                ids=[issue_id],
                proof=None,
                note='auto-approved by discount',
                created_at=now_ts
            ).exec()
        return jsonify({'success': True, 'message': 'Issue unlocked with subscription discount', 'payment_id': None})

    payment_data = {
        'user_id': user_id,
        'status': 'unpaid',
        'currency': currency,
        'payment_type': 'issue',
        'payment_date': None,
        'amount': discounted_amount,
        'ids': [issue_id],
        'proof': None,
        'note': data.get('note'),
        'created_at': int(time.time())
    }

    payment_result = _create_or_get_pending_payment(user_id, 'issue', issue_id, payment_data)
    payment_id = payment_result.get('payment_id')
    if payment_result.get('created') and payment_id is not None:
        _send_payment_created_email(
            user_id=user_id,
            payment_id=payment_id,
            payment_type='issue',
            source_row=issue,
            amount=payment_data['amount'],
            currency=currency,
        )
    message = 'Issue payment created' if payment_result.get('created') else 'Issue payment already exists'
    return jsonify({'success': True, 'message': message, 'payment_id': payment_id})


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
        if publication.get('subscription_enable'):
            return jsonify({'success': False, 'message': 'Article is available only via subscription'})
        return jsonify({'success': True, 'message': 'Article is open access'})

    if _user_has_paid_access(user_id, 'article', article_id):
        return jsonify({'success': True, 'message': 'Article is already purchased'})

    if _subscription_grants_article_access(user_id, publication):
        return jsonify({'success': True, 'message': 'Article is already available with your subscription'})

    currency = _normalize_currency(data.get('currency') or _default_currency_for_language())
    active_tariff = _active_subscription_tariff_for_user(user_id)
    article_discount_pct = _effective_tariff_discount_percent(active_tariff, 'article_discount_pct')
    base_amount = _resolve_publication_price(publication, currency)
    discounted_amount = _apply_discount_percent(base_amount, article_discount_pct)

    if discounted_amount <= 0:
        now_ts = int(time.time())
        if not _user_has_paid_access(user_id, 'article', article_id):
            dbc.payments.add(
                user_id=user_id,
                status='paid',
                currency=currency,
                payment_type='article',
                payment_date=now_ts,
                amount=0,
                ids=[article_id],
                proof=None,
                note='auto-approved by discount',
                created_at=now_ts
            ).exec()
        return jsonify({'success': True, 'message': 'Article unlocked with subscription discount', 'payment_id': None})

    payment_data = {
        'user_id': user_id,
        'status': 'unpaid',
        'currency': currency,
        'payment_type': 'article',
        'payment_date': None,
        'amount': discounted_amount,
        'ids': [article_id],
        'proof': None,
        'note': data.get('note'),
        'created_at': int(time.time())
    }

    payment_result = _create_or_get_pending_payment(user_id, 'article', article_id, payment_data)
    payment_id = payment_result.get('payment_id')
    if payment_result.get('created') and payment_id is not None:
        _send_payment_created_email(
            user_id=user_id,
            payment_id=payment_id,
            payment_type='article',
            source_row=publication,
            amount=payment_data['amount'],
            currency=currency,
        )
    message = 'Article payment created' if payment_result.get('created') else 'Article payment already exists'
    return jsonify({'success': True, 'message': message, 'payment_id': payment_id})


def app__api_translations_clear_cache():
    provided_token = request.headers.get('X-Translation-Sync-Token', '').strip()
    expected_token = (settings.TRANSLATION_SYNC_TOKEN or '').strip()
    is_authorized_by_token = bool(expected_token) and secrets.compare_digest(provided_token, expected_token)

    is_authorized_by_session = False
    session_user_id = session.get('user_id')
    if session_user_id:
        try:
            user_rows = dbc.users.get(id=session_user_id).exec()
        except Exception:
            user_rows = []
        if user_rows:
            is_authorized_by_session = user_has_permission(hydrate_user_roles(user_rows[0]), 'fmadmin.access')

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

    except Exception:
        logger.exception('Failed to create author profile from API for user_id=%s', session.get('user_id'))
        return jsonify({'success': False, 'message': 'Database error occurred while creating author'})


def register(app):
    app.add_url_rule('/api/getauthor', view_func=author_login_required(app__api_getauthor), methods=['POST'])
    app.add_url_rule('/api/getcurrentauthor', view_func=author_login_required(app__api_getcurrentauthor), methods=['GET'])
    app.add_url_rule('/api/getclassifications', view_func=author_login_required(app__api_getclassifications), methods=['GET'])
    app.add_url_rule('/api/article/save', view_func=author_login_required(app__api_article_save), methods=['POST'])
    app.add_url_rule('/api/article/submit', view_func=author_login_required(app__api_article_submit), methods=['POST'])
    app.add_url_rule('/api/article/upload', view_func=author_login_required(app__api_article_upload), methods=['POST'])
    app.add_url_rule('/api/article/load/<int:submission_id>', view_func=author_login_required(app__api_article_load))
    app.add_url_rule('/api/payment/submit_proof', view_func=login_required(app__api_payment_submit_proof), methods=['POST'])
    app.add_url_rule('/api/payment/delete/<int:payment_id>', view_func=login_required(app__api_payment_delete), methods=['POST'])
    app.add_url_rule('/api/subscription/cancel', view_func=login_required(app__api_subscription_cancel), methods=['POST'])
    app.add_url_rule('/api/subscription/upload_document', view_func=login_required(app__api_subscription_upload_document), methods=['POST'])
    app.add_url_rule('/api/payment/create_subscription', view_func=login_required(app__api_payment_create_subscription), methods=['POST'])
    app.add_url_rule('/api/issue/purchase', view_func=login_required(app__api_issue_purchase), methods=['POST'])
    app.add_url_rule('/api/article/purchase', view_func=login_required(app__api_article_purchase), methods=['POST'])
    app.add_url_rule('/api/translations/clear_cache', view_func=app__api_translations_clear_cache, methods=['POST'])
    app.add_url_rule('/api/profile/change_password', view_func=login_required(app__api_profile_change_password), methods=['POST'])
    app.add_url_rule('/api/createauthor', view_func=author_login_required(app__api_createauthor), methods=['POST'])
