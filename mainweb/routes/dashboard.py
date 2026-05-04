# flake8: noqa
import os
import re
import time
from urllib.parse import urlparse
try:
    import mainweb.settings as settings
except ImportError:
    import settings
from flask import render_template, session, request, jsonify, flash, redirect, url_for, current_app, send_file, abort
from extensions import dbc
from modules.translate import t, translate
from utils.auth import (
    author_login_required,
    sanitize_input,
    decode_html_entities,
    is_valid_email,
    get_user_profile_completion,
)
from utils.notifications import apply_localized_notification_content, dashboard_notification_access_clause
from utils.private_uploads import build_private_upload_ref, extract_private_upload_key, private_upload_abspath, upload_access_url
from utils.uploads import allowed_file


SUBMISSION_TRACKS = {
    'masters': {
        'title_key': 'track_masters_title',
        'desc_key': 'track_masters_desc',
        'fallback_title': 'Magistr',
        'fallback_desc': 'Magistrlar uchun maqola yuborish formasi',
        'icon': 'solar:document-add-bold-duotone'
    },
    'phd': {
        'title_key': 'track_phd_title',
        'desc_key': 'track_phd_desc',
        'fallback_title': 'Doktorant',
        'fallback_desc': 'Doktorantlar uchun maqola yuborish formasi',
        'icon': 'solar:book-2-bold-duotone'
    },
    'teacher': {
        'title_key': 'track_teacher_title',
        'desc_key': 'track_teacher_desc',
        'fallback_title': "O'qituvchi",
        'fallback_desc': "O'qituvchilar uchun maqola yuborish formasi",
        'icon': 'solar:user-check-bold-duotone'
    }
}

SUBMISSION_WORKFLOW_STEPS = [
    ('waiting', 'workflow_stage_waiting', "Kutilmoqda"),
    ('technical_check', 'workflow_stage_technical_check', "Texnik talablarga mos"),
    ('anti_plagiarism', 'workflow_stage_anti_plagiarism', "Antiplagiatga tekshirish"),
    ('in_review', 'workflow_stage_in_review', "Taqrizda"),
    ('recommended', 'workflow_stage_recommended', "Nashrga tavsiya etildi"),
    ('payment', 'workflow_stage_payment', "To'lov"),
    ('published', 'workflow_stage_published', "Nashr qilindi")
]
SUBMISSION_WORKFLOW_KEYS = {key for key, _, _ in SUBMISSION_WORKFLOW_STEPS}
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
ACADEMIC_POSITION_CHOICES = {
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
ALLOWED_TARIFF_FEATURE_PERMISSIONS = {
    'access_latest_content',
    'access_archive_content',
    'download_subscription_files',
    'article_discount',
    'issue_discount',
}
FEATURE_PERMISSION_LABELS = {
    'access_latest_content': 'Yangi sonlar va maqolalar',
    'access_archive_content': 'Arxiv materiallari',
    'download_subscription_files': 'PDF yuklab olish',
    'article_discount': 'Maqola xarid chegirmasi',
    'issue_discount': 'Son xarid chegirmasi',
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
DOCUMENT_TYPE_ORDER = [
    'student_id',
    'enrollment_certificate',
    'master_certificate',
    'phd_certificate',
    'researcher_certificate',
    'employment_certificate',
    'other_academic',
]
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
PROFILE_DOCUMENT_UI_LABELS = {
    'uz': {
        'supporting_document': "Qo'shimcha hujjat",
        'document_type': 'Hujjat turi',
        'document_holder_name': 'Hujjat egasi F.I.Sh',
        'institution_name': 'Universitet / muassasa nomi',
        'not_specified': 'Tanlanmagan',
    },
    'ru': {
        'supporting_document': 'Сопроводительный документ',
        'document_type': 'Тип документа',
        'document_holder_name': 'Ф.И.О. владельца документа',
        'institution_name': 'Название университета / учреждения',
        'not_specified': 'Не указано',
    },
    'en': {
        'supporting_document': 'Supporting document',
        'document_type': 'Document Type',
        'document_holder_name': 'Document Holder Name',
        'institution_name': 'Institution Name',
        'not_specified': 'Not specified',
    },
}
ORCID_REGEX = re.compile(r'^\d{4}-\d{4}-\d{4}-\d{3}[0-9Xx]$')


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


def _tariff_subscription_discount_context(tariff, now_ts=None):
    tariff_row = tariff or {}
    now_value = _parse_int(now_ts)
    if now_value is None:
        now_value = int(time.time())

    discount_percent = _normalize_discount_percent(tariff_row.get('subscription_discount_pct'))
    start_at = _parse_int(tariff_row.get('subscription_discount_start_at'))
    end_at = _parse_int(tariff_row.get('subscription_discount_end_at'))

    active = discount_percent > 0
    if active and start_at is not None and now_value < start_at:
        active = False
    if active and end_at is not None and now_value > end_at:
        active = False

    return {
        'active': active,
        'discount_percent': discount_percent,
        'start_at': start_at,
        'end_at': end_at,
    }


def _normalize_academic_position(value):
    normalized = str(value or '').strip().lower()
    normalized = normalized.replace('’', "'")
    normalized = ACADEMIC_POSITION_ALIASES.get(normalized, normalized)
    return normalized if normalized in ACADEMIC_POSITION_CHOICES else None


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
    normalized = str(value or '').strip().lower()
    return normalized if normalized in ALLOWED_TARIFF_FEATURE_PERMISSIONS else None


def _feature_permission_label(value):
    normalized = _normalize_feature_permission(value)
    if not normalized:
        return ''
    return FEATURE_PERMISSION_LABELS.get(normalized, normalized.replace('_', ' ').title())


def _parse_feature_permissions(value):
    normalized_items = []
    for item in _parse_text_array(value):
        normalized = _normalize_feature_permission(item)
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


def _normalize_document_type(value):
    normalized = str(value or '').strip().lower()
    normalized = normalized.replace('’', "'")
    normalized = DOCUMENT_TYPE_ALIASES.get(normalized, normalized)
    return normalized if normalized in ALLOWED_DOCUMENT_TYPES else None


def _current_interface_language():
    language = (session.get('language') or 'en').strip().lower()
    return language if language in DOCUMENT_TYPE_LOCALIZED_LABELS else 'en'


def _profile_document_ui_labels():
    return PROFILE_DOCUMENT_UI_LABELS.get(_current_interface_language(), PROFILE_DOCUMENT_UI_LABELS['en'])


def _document_type_label(value):
    normalized = _normalize_document_type(value)
    if not normalized:
        return ''
    localized_labels = DOCUMENT_TYPE_LOCALIZED_LABELS.get(_current_interface_language(), DOCUMENT_TYPE_LOCALIZED_LABELS['en'])
    return localized_labels.get(normalized, DOCUMENT_TYPE_LABELS.get(normalized, normalized.replace('_', ' ').title()))


def _document_type_choices():
    return [(value, _document_type_label(value)) for value in DOCUMENT_TYPE_ORDER]


def _parse_required_document_types(value):
    normalized_items = []
    for item in _parse_text_array(value):
        normalized = _normalize_document_type(item)
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


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
    return _parse_required_document_types((tariff or {}).get('required_document_types'))


def _default_document_type_for_position(position):
    normalized = _normalize_academic_position(position)
    mapping = {
        'student': 'student_id',
        'master': 'master_certificate',
        'doctoral': 'phd_certificate',
        'postgraduate': 'phd_certificate',
        'doctor': 'phd_certificate',
        'teacher': 'employment_certificate',
        'researcher': 'researcher_certificate',
        'university_researcher': 'researcher_certificate',
        'independent_researcher': 'researcher_certificate',
    }
    return mapping.get(normalized, 'other_academic')


def _normalize_name_for_match(value):
    return ' '.join(str(value or '').strip().lower().split())


def _account_full_name(user_row):
    user = user_row or {}
    return str(f"{user.get('name') or ''} {user.get('second_name') or ''}").strip()


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
            "SET document_type = 'other_academic' "
            "WHERE document_type IS NULL AND COALESCE(TRIM(file_path), '') <> '';"
        )
        dbc.conn.commit()
        cursor.close()
        dbc._init_tables()
        dbc._init_columns()
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass


def _user_doc_is_verified(user_doc):
    status = str((user_doc or {}).get('verification_status') or '').strip().lower()
    return status in {'verified', 'approved'}


def _safe_internal_redirect(target, fallback_endpoint):
    fallback_url = url_for(fallback_endpoint)
    target_text = (target or '').strip()
    if not target_text:
        return fallback_url

    parsed = urlparse(target_text)
    if parsed.scheme or parsed.netloc:
        request_host = (request.host or '').split(':')[0]
        parsed_host = (parsed.hostname or '').split(':')[0] if parsed.hostname else ''
        if parsed_host != request_host:
            return fallback_url
        path = parsed.path or '/'
        query = f"?{parsed.query}" if parsed.query else ''
        return f"{path}{query}"

    if not target_text.startswith('/') or target_text.startswith('//'):
        return fallback_url
    return target_text


def _resolve_publication_timestamp(publication):
    if not publication:
        return None
    for key in ('date_publish', 'created_at', 'created_date'):
        timestamp = _parse_int(publication.get(key))
        if timestamp:
            return timestamp
    return None


def _format_publication_year(publication):
    timestamp = _resolve_publication_timestamp(publication)
    if not timestamp:
        return 'N/A'
    return time.strftime('%Y', time.gmtime(timestamp + 5 * 60 * 60))


def _decode_row_strings(row):
    if not row:
        return row
    decoded = {}
    for key, value in row.items():
        if isinstance(value, str):
            decoded[key] = decode_html_entities(value)
        else:
            decoded[key] = value
    return decoded


def _submission_track_list():
    return [{'key': key, **value} for key, value in SUBMISSION_TRACKS.items()]


def _resolve_submission_track(track):
    if not track:
        return None
    normalized = track.strip().lower()
    return normalized if normalized in SUBMISSION_TRACKS else None


def _resolve_submission_workflow_stage(submission):
    explicit_stage = (submission.get('workflow_stage') or '').strip().lower()
    if explicit_stage in SUBMISSION_WORKFLOW_KEYS or explicit_stage == 'rejected':
        return explicit_stage

    status = (submission.get('status') or '').strip().lower()
    editor_status = (submission.get('editor_review_status') or '').strip().lower()

    if status == 'published':
        return 'published'
    if status == 'rejected':
        return 'rejected'
    if status in ('submitted', 'pending'):
        return 'waiting'
    if status in ('in_process', 'under_review'):
        if editor_status in ('approved', 'reviewed'):
            return 'recommended'
        if editor_status in ('in_review', 'assigned'):
            return 'in_review'
        return 'technical_check'
    if status == 'paid':
        return 'payment'
    if status == 'accepted':
        return 'recommended'
    return 'waiting'


def _workflow_step_label(key, title_key, fallback):
    translated = t(title_key)
    if translated and translated != title_key:
        return translated
    return fallback


def _decorate_submission_with_workflow(submission):
    stage_key = _resolve_submission_workflow_stage(submission)
    step_index = {key: idx for idx, (key, _, _) in enumerate(SUBMISSION_WORKFLOW_STEPS)}
    current_index = step_index.get(stage_key, -1)

    steps = []
    for idx, (key, title_key, fallback) in enumerate(SUBMISSION_WORKFLOW_STEPS):
        label = _workflow_step_label(key, title_key, fallback)
        if stage_key == 'rejected':
            state = 'pending'
        elif idx < current_index:
            state = 'done'
        elif idx == current_index:
            state = 'current'
        else:
            state = 'pending'
        steps.append({
            'key': key,
            'label': label,
            'state': state
        })

    if stage_key == 'rejected':
        stage_label = t('workflow_stage_rejected')
        if stage_label == 'workflow_stage_rejected':
            stage_label = 'Rad etilgan'
    else:
        stage_info = next((item for item in SUBMISSION_WORKFLOW_STEPS if item[0] == stage_key), None)
        if stage_info:
            stage_label = _workflow_step_label(*stage_info)
        else:
            stage_label = _workflow_step_label(*SUBMISSION_WORKFLOW_STEPS[0])

    submission['workflow_stage_key'] = stage_key
    submission['workflow_stage_label'] = stage_label
    submission['workflow_steps'] = steps
    return submission


def _normalize_currency(currency):
    normalized = (currency or 'usd').strip().lower()
    return normalized if normalized in TARIFF_CURRENCY_FIELDS else 'usd'


def _default_currency_for_language():
    language = (session.get('language') or 'en').strip().lower()
    return LANGUAGE_DEFAULT_CURRENCY.get(language, 'usd')


def _resolve_upload_file_path(file_url):
    if not file_url:
        return None
    private_path = private_upload_abspath(file_url)
    if private_path:
        return private_path

    normalized_url = str(file_url).strip()
    prefix = '/static/uploads/'
    if not normalized_url.startswith(prefix):
        return None

    relative_path = normalized_url[len(prefix):].lstrip('/')
    base_dir = os.path.abspath(current_app.config.get('UPLOAD_FOLDER', ''))
    if not base_dir:
        return None

    candidate_path = os.path.abspath(os.path.join(base_dir, relative_path))
    try:
        if os.path.commonpath([candidate_path, base_dir]) != base_dir:
            return None
    except ValueError:
        return None
    return candidate_path


def _submission_has_private_file(submission, storage_key):
    for field_name in ('file_authors', 'file_anonymized', 'anti_plagiarism_file'):
        if extract_private_upload_key((submission or {}).get(field_name)) == storage_key:
            return True
    return False


def _user_matches_private_upload_pattern(user_id, storage_key):
    if not user_id or not storage_key:
        return False

    filename = storage_key.rsplit('/', 1)[-1]
    user_marker = f'_{user_id}_'

    if storage_key.startswith('documents/'):
        return filename.startswith(f'academic_doc_{user_id}_')
    if storage_key.startswith('payments/'):
        return filename.startswith(f'payment_proof_{user_id}_')
    if storage_key.startswith('articles/'):
        return (
            filename.startswith(f'authors_{user_id}_')
            or filename.startswith(f'anonymized_{user_id}_')
            or filename.startswith(f'anti_plagiarism_{user_id}_')
            or user_marker in filename
        )
    return False


def _user_has_private_upload_record(user_id, storage_key):
    if not user_id or not storage_key:
        return False

    if storage_key.startswith('documents/'):
        rows = dbc.user_doc_uploads.get(user_id=user_id).exec()
        return any(extract_private_upload_key(row.get('file_path')) == storage_key for row in rows)

    if storage_key.startswith('payments/'):
        rows = dbc.payments.get(user_id=user_id).exec()
        return any(
            extract_private_upload_key(row.get('proof')) == storage_key
            or extract_private_upload_key(row.get('confirmation_file')) == storage_key
            for row in rows
        )

    if storage_key.startswith('articles/'):
        rows = dbc.submissions.get(user_id=user_id).exec()
        return any(_submission_has_private_file(row, storage_key) for row in rows)

    return False


def _resolve_tariff_price_and_currency(tariff, currency):
    selected_key = TARIFF_CURRENCY_FIELDS[currency]
    selected_value = tariff.get(selected_key)
    selected_currency = currency

    try:
        return float(selected_value or 0), selected_currency
    except (TypeError, ValueError):
        return 0.0, selected_currency


def _resolve_tariff_price(tariff, currency):
    price, _ = _resolve_tariff_price_and_currency(tariff, currency)
    return price


def _is_tariff_archived(tariff):
    value = (tariff or {}).get('is_archived')
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def _is_user_verified_for_tariff(user, user_docs):
    if (user or {}).get('is_verified'):
        return True
    for user_doc in user_docs or []:
        status = str(user_doc.get('verification_status') or '').strip().lower()
        if status in {'verified', 'approved'}:
            return True
    return False


def _is_valid_orcid(orcid):
    normalized = (orcid or '').strip()
    if not normalized:
        return False
    return ORCID_REGEX.match(normalized) is not None


def _fetch_dashboard_notifications(user_id, limit=200):
    safe_limit = max(1, min(_parse_int(limit) or 200, 500))
    return _fetch_dashboard_notifications_page(user_id, page=1, per_page=safe_limit)


def _fetch_dashboard_notifications_page(user_id, page=1, per_page=20):
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if not access_clause:
        return []

    safe_page = max(_parse_int(page) or 1, 1)
    safe_per_page = max(1, min(_parse_int(per_page) or 20, 100))
    safe_offset = (safe_page - 1) * safe_per_page
    query = (
        "SELECT id, title, message, level, action_url, is_read, created_at, read_at, event_type, metadata_text "
        "FROM role_notifications "
        f"WHERE {access_clause} "
        "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    )
    args = tuple(access_args) + (safe_per_page, safe_offset)
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, args)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        return [apply_localized_notification_content(dict(zip(columns, row))) for row in rows]
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return []


def _count_dashboard_notifications(user_id):
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if not access_clause:
        return 0

    query = (
        "SELECT COUNT(*) FROM role_notifications "
        f"WHERE {access_clause}"
    )
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, tuple(access_args))
        row = cursor.fetchone()
        cursor.close()
        return int(row[0] or 0) if row else 0
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return 0


def _count_dashboard_unread_notifications(user_id):
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if not access_clause:
        return 0

    query = (
        "SELECT COUNT(*) FROM role_notifications "
        "WHERE is_read = FALSE "
        f"AND {access_clause}"
    )
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, tuple(access_args))
        row = cursor.fetchone()
        cursor.close()
        return int(row[0] or 0) if row else 0
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return 0


def _mark_dashboard_notification_read(notification_id, user_id):
    notification_id_int = _parse_int(notification_id)
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if notification_id_int is None or not access_clause:
        return False

    query = (
        "UPDATE role_notifications SET is_read = TRUE, read_at = %s "
        "WHERE id = %s AND is_read = FALSE "
        f"AND {access_clause}"
    )
    args = (int(time.time()), notification_id_int, *access_args)
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, args)
        changed = cursor.rowcount
        dbc.conn.commit()
        cursor.close()
        return changed > 0
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return False


def _mark_dashboard_notifications_read_all(user_id):
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if not access_clause:
        return 0

    query = (
        "UPDATE role_notifications SET is_read = TRUE, read_at = %s "
        "WHERE is_read = FALSE "
        f"AND {access_clause}"
    )
    args = (int(time.time()), *access_args)
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, args)
        changed = cursor.rowcount
        dbc.conn.commit()
        cursor.close()
        return changed
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return 0


def app__dashboard_private_file(storage_key):
    user_id = session.get('user_id')
    resolved_key = extract_private_upload_key(storage_key)
    if not user_id or not resolved_key:
        abort(404)

    if not (_user_matches_private_upload_pattern(user_id, resolved_key) or _user_has_private_upload_record(user_id, resolved_key)):
        abort(404)

    file_path = private_upload_abspath(resolved_key)
    if not file_path or not os.path.exists(file_path):
        abort(404)

    return send_file(file_path, as_attachment=False, download_name=os.path.basename(file_path))


def _get_dashboard_notification(notification_id, user_id):
    notification_id_int = _parse_int(notification_id)
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if notification_id_int is None or not access_clause:
        return None

    query = (
        "SELECT id, title, message, level, action_url, is_read, created_at, read_at, event_type, metadata_text "
        "FROM role_notifications "
        f"WHERE id = %s AND {access_clause} "
        "LIMIT 1"
    )
    args = (notification_id_int, *access_args)
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, args)
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        if not row:
            return None
        return apply_localized_notification_content(dict(zip(columns, row)))
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return None


def app__dashboard():
    user_id = session['user_id']
    all_submissions = dbc.submissions.get().equal(user_id=user_id).order_by('id').exec()

    drafts_count = 0
    visible_submissions = []
    for submission in all_submissions:
        translate(submission)
        status = (submission.get('status') or '').strip().lower()
        if status == 'draft':
            drafts_count += 1
            continue
        _decorate_submission_with_workflow(submission)
        visible_submissions.append(submission)

    visible_submissions.sort(key=lambda item: _parse_int(item.get('created_date')) or 0, reverse=True)
    recent_submissions = visible_submissions[:4]

    published_count = 0
    rejected_count = 0
    in_progress_count = 0
    payment_count = 0
    for submission in visible_submissions:
        stage = submission.get('workflow_stage_key') or _resolve_submission_workflow_stage(submission)
        if stage == 'published':
            published_count += 1
        elif stage == 'rejected':
            rejected_count += 1
        elif stage == 'payment':
            payment_count += 1
            in_progress_count += 1
        else:
            in_progress_count += 1

    dashboard_stats = {
        'total': len(visible_submissions),
        'in_progress': in_progress_count,
        'published': published_count,
        'drafts': drafts_count,
        'rejected': rejected_count,
        'payment': payment_count,
        'unread_notifications': _count_dashboard_unread_notifications(user_id)
    }

    return render_template(
        'dashboard/index.html',
        submissions=recent_submissions,
        dashboard_stats=dashboard_stats
    )


def app__dashboard_articles():
    submissions = dbc.submissions.get().equal(user_id=session['user_id']).unequal(status='draft').order_by('id').exec()
    author_profiles = {}

    # Collect unique author IDs first to avoid repeated DB lookups in template rendering.
    author_ids = set()
    for submission in submissions:
        translate(submission)
        _decorate_submission_with_workflow(submission)
        if submission.get('main_author_id'):
            author_ids.add(submission['main_author_id'])

        co_author_ids = submission.get('sub_author_ids') or submission.get('subauthor_ids') or []
        for author_id in co_author_ids:
            author_ids.add(author_id)

    for author_id in author_ids:
        author = dbc.author_profile.get(id=author_id).exec()
        if author:
            author_profiles[author_id] = translate(author[0])

    return render_template('dashboard/articles.html', submissions=submissions, author_profiles=author_profiles)


def app__dashboard_articles_delete(submission_id):
    expects_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json
    submission = dbc.submissions.get(id=submission_id, user_id=session['user_id']).exec()
    if not submission:
        if expects_json:
            return jsonify({'success': False, 'message': t('submission_not_found')}), 404
        flash('Submission not found', 'error')
        return redirect(url_for('app__dashboard_articles'))

    dbc.submissions.get(id=submission_id, user_id=session['user_id']).delete().exec()
    if expects_json:
        return jsonify({'success': True, 'message': t('submission_deleted_successfully')})
    flash('Submission deleted successfully', 'success')
    return redirect(url_for('app__dashboard_articles'))


def app__dashboard_purchases():
    _ensure_user_doc_upload_columns()
    now_ts = int(time.time())
    payments = dbc.payments.get(user_id=session['user_id']).order_by('id').exec()
    for payment in payments:
        payment = translate(payment)
        if payment['payment_type'] == 'article' and payment['ids']:
            articles = []
            for article_id in payment['ids']:
                publication = dbc.publications.get(id=article_id).exec()
                if publication:
                    translated_article = translate(publication[0])
                    main_author = None
                    if translated_article['main_author_id']:
                        author = dbc.author_profile.get(id=translated_article['main_author_id']).exec()
                        if author:
                            main_author = translate(author[0])
                    articles.append({
                        'id': translated_article['id'],
                        'title': translated_article['title'],
                        'author': main_author['name'] if main_author else 'Unknown',
                        'volume': translated_article.get('volume', 'N/A'),
                        'issue': translated_article.get('issue', 'N/A'),
                        'year': _format_publication_year(translated_article)
                    })
            payment['articles'] = articles
        elif payment['payment_type'] == 'subscription' and payment['ids']:
            tariff_id = payment['ids'][0]
            tariff = dbc.tariffs.get(id=tariff_id).exec()
            if tariff:
                tariff_data = translate(tariff[0])
                payment['tariff'] = tariff_data

        if payment.get('payment_type') == 'subscription':
            subscription_start_at = _parse_int(payment.get('snapshot_start_at'))
            subscription_end_at = _parse_int(payment.get('snapshot_end_at'))
            snapshot_days = _parse_int(payment.get('snapshot_duration_days'))
            paid_at = _parse_int(payment.get('payment_date')) or _parse_int(payment.get('created_at'))
            if subscription_start_at is None and paid_at is not None:
                subscription_start_at = paid_at
            if subscription_end_at is None and subscription_start_at is not None and snapshot_days:
                subscription_end_at = subscription_start_at + (snapshot_days * 24 * 60 * 60)

            is_paid = (str(payment.get('status') or '').strip().lower() == 'paid')
            payment['subscription_start_at'] = subscription_start_at
            payment['subscription_end_at'] = subscription_end_at
            payment['subscription_days_total'] = snapshot_days
            payment['subscription_active_item'] = bool(
                is_paid
                and subscription_end_at is not None
                and subscription_end_at > now_ts
                and (subscription_start_at is None or subscription_start_at <= now_ts)
            )
            payment['subscription_upcoming_item'] = bool(
                is_paid
                and subscription_start_at is not None
                and subscription_start_at > now_ts
            )
            payment['subscription_expired_item'] = bool(
                is_paid
                and subscription_end_at is not None
                and subscription_end_at <= now_ts
            )
            payment['subscription_days_left'] = (
                max(0, (subscription_end_at - now_ts) // (24 * 60 * 60))
                if payment['subscription_active_item'] and subscription_end_at is not None else None
            )
            payment['subscription_days_until_start'] = (
                max(0, (subscription_start_at - now_ts) // (24 * 60 * 60))
                if payment['subscription_upcoming_item'] and subscription_start_at is not None else None
            )

    payments.sort(key=lambda item: _parse_int(item.get('created_at')) or 0, reverse=True)

    active_subscription_items = [
        item for item in payments
        if item.get('payment_type') == 'subscription' and item.get('subscription_active_item')
    ]
    active_subscription_payment_id = active_subscription_items[0]['id'] if active_subscription_items else None

    subscription_active = False
    subscription_end_date = None
    days_left = None
    user = dbc.users.get(id=session['user_id']).exec()[0]
    user_subscription_end = _parse_int(user.get('subscription_end_date'))
    if user_subscription_end and user_subscription_end > now_ts:
        subscription_active = True
        subscription_end_date = user_subscription_end
    if active_subscription_items:
        max_active_end = max(
            (_parse_int(item.get('subscription_end_at')) or 0) for item in active_subscription_items
        ) or None
        if max_active_end and (subscription_end_date is None or max_active_end > subscription_end_date):
            subscription_end_date = max_active_end
        subscription_active = True
    if subscription_active and subscription_end_date:
        days_left = max(0, (subscription_end_date - now_ts) // (24 * 60 * 60))

    requested_currency = request.args.get('currency') or _default_currency_for_language()
    currency = _normalize_currency(requested_currency)
    user_docs = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()
    user_doc = user_docs[0] if user_docs else {}
    user_position = _normalize_academic_position((user_doc or {}).get('work_title'))
    user_position_label = _academic_position_label(user_position)
    user_document_type = _normalize_document_type((user_doc or {}).get('document_type'))
    user_document_holder_name = str((user_doc or {}).get('document_holder_name') or '').strip()
    user_document_institution_name = str((user_doc or {}).get('institution_name') or '').strip()
    user_doc_verified = _user_doc_is_verified(user_doc)
    is_verified = _is_user_verified_for_tariff(user, user_docs)
    user_full_name = _account_full_name(user)
    name_match_ok = _normalize_name_for_match(user_document_holder_name) == _normalize_name_for_match(user_full_name)

    tariffs = dbc.tariffs.get().exec()
    processed_tariffs = []
    for tariff in tariffs:
        if _is_tariff_archived(tariff):
            continue
        tariff = translate(tariff)
        tariff['entitlement_scope'] = (str(tariff.get('entitlement_scope') or 'all').strip().lower() or 'all')
        tariff['archive_days_threshold'] = _parse_int(tariff.get('archive_days_threshold')) or 365
        tariff['article_discount_pct'] = max(0.0, min(_parse_float(tariff.get('article_discount_pct'), 0.0), 100.0))
        tariff['issue_discount_pct'] = max(0.0, min(_parse_float(tariff.get('issue_discount_pct'), 0.0), 100.0))
        tariff['subscription_discount_pct'] = _normalize_discount_percent(tariff.get('subscription_discount_pct'))
        tariff['subscription_discount_start_at'] = _parse_int(tariff.get('subscription_discount_start_at'))
        tariff['subscription_discount_end_at'] = _parse_int(tariff.get('subscription_discount_end_at'))
        tariff['monthly_download_limit'] = max(0, _parse_int(tariff.get('monthly_download_limit')) or 0)
        feature_permissions = _parse_feature_permissions(tariff.get('feature_permissions'))
        if not feature_permissions:
            if tariff['entitlement_scope'] == 'archive':
                feature_permissions = ['access_archive_content', 'download_subscription_files', 'article_discount', 'issue_discount']
            else:
                feature_permissions = ['access_latest_content', 'access_archive_content', 'download_subscription_files', 'article_discount', 'issue_discount']
        tariff['feature_permissions'] = feature_permissions
        tariff['feature_permission_labels'] = [_feature_permission_label(item) for item in feature_permissions if _feature_permission_label(item)]
        required_positions = _parse_required_positions(tariff.get('required_academic_positions'))
        tariff['required_academic_positions'] = required_positions
        tariff['required_academic_position_labels'] = [_academic_position_label(item) for item in required_positions]
        required_document_types = _tariff_effective_required_document_types(tariff)
        tariff['required_document_types'] = required_document_types
        tariff['required_document_type_labels'] = [_document_type_label(item) for item in required_document_types if _document_type_label(item)]
        tariff['requires_verified_document'] = _parse_bool(tariff.get('requires_verified_document'))
        tariff['eligibility_note'] = str(tariff.get('eligibility_note') or '').strip()
        eligibility_reasons = []
        if tariff.get('is_verified') and not is_verified:
            eligibility_reasons.append("Profil tasdiqlovi talab qilinadi")
        if required_document_types:
            labels = [item for item in tariff['required_document_type_labels'] if item]
            if not (user_doc or {}).get('file_path'):
                if labels:
                    eligibility_reasons.append("Faollashtirish uchun hujjat yuklash talab qilinadi: " + ', '.join(labels))
                else:
                    eligibility_reasons.append("Faollashtirish uchun akademik hujjat yuklash talab qilinadi")
            elif user_document_type not in required_document_types:
                if labels:
                    eligibility_reasons.append("Mos hujjat turi: " + ', '.join(labels))
                else:
                    eligibility_reasons.append("Mos akademik hujjat turi talab qilinadi")
            elif not name_match_ok:
                eligibility_reasons.append("Hujjat egasi F.I.Sh akkauntdagi ism-familiyaga mos bo'lishi kerak")
        if required_document_types and tariff['requires_verified_document'] and not user_doc_verified:
            eligibility_reasons.append("Tasdiqlangan akademik hujjat talab qilinadi")
        document_required_for_activation = bool(required_document_types)
        needs_upload = False
        if document_required_for_activation and not (user_doc or {}).get('file_path'):
            needs_upload = True
        if required_document_types and (user_doc or {}).get('file_path') and user_document_type not in required_document_types:
            needs_upload = True
        if document_required_for_activation and (user_doc or {}).get('file_path') and not name_match_ok:
            needs_upload = True
        tariff['needs_document_upload'] = needs_upload
        tariff['needs_document_verification'] = bool(
            required_document_types and tariff['requires_verified_document']
            and not tariff['needs_document_upload']
            and not user_doc_verified
        )
        tariff['eligible_for_user'] = len(eligibility_reasons) == 0
        tariff['eligibility_reasons'] = eligibility_reasons
        base_selected_price, selected_currency = _resolve_tariff_price_and_currency(tariff, currency)
        discount_context = _tariff_subscription_discount_context(tariff)
        discounted_selected_price = base_selected_price
        if discount_context.get('active'):
            discounted_selected_price = _apply_discount_percent(base_selected_price, discount_context.get('discount_percent'))
        tariff['base_selected_price'] = base_selected_price
        tariff['selected_price'] = discounted_selected_price
        tariff['subscription_discount_active'] = bool(discount_context.get('active'))
        tariff['subscription_discount_percent'] = discount_context.get('discount_percent') or 0.0
        tariff['selected_currency'] = selected_currency
        tariff['can_select'] = (
            discounted_selected_price > 0
            and (tariff['eligible_for_user'] or tariff['needs_document_upload'])
            and not tariff['needs_document_verification']
        )
        processed_tariffs.append(tariff)

    return render_template(
        'dashboard/payments.html',
        payments=payments,
        subscription_active=subscription_active,
        subscription_end_date=subscription_end_date,
        days_left=days_left,
        now_ts=now_ts,
        active_subscription_payment_id=active_subscription_payment_id,
        tariffs=processed_tariffs,
        currency=currency,
        is_verified=is_verified,
        user_doc=user_doc,
        user_position=user_position,
        user_position_label=user_position_label,
        user_doc_verified=user_doc_verified,
        user_full_name=user_full_name,
        user_document_holder_name=user_document_holder_name,
        user_document_institution_name=user_document_institution_name
    )


def app__dashboard_new_article():
    submission_id = request.args.get('id', type=int)
    track = _resolve_submission_track(request.args.get('track'))

    if not submission_id and track is None and request.args.get('track'):
        flash(
            t('invalid_submission_track') if t('invalid_submission_track') != 'invalid_submission_track' else 'Please select a valid submission track',
            'error'
        )
        return redirect(url_for('app__dashboard_new_article'))

    if not submission_id and not track:
        return render_template('dashboard/new_article_type.html', submission_tracks=_submission_track_list())

    translations = dbc.translations.get().exec()
    authors = dbc.author_profile.get().exec()
    classifications = dbc.fix_classifications.get().exec()
    countries = dbc.fix_country.get().exec()

    for author in authors:
        author = translate(author)
    for classification in classifications:
        classification = translate(classification)
    for country in countries:
        country = translate(country)

    return render_template('dashboard/new_article.html',
                         translations=translations,
                         authors=authors,
                         classifications=classifications,
                         countries=countries,
                         selected_track=track,
                         selected_track_info=SUBMISSION_TRACKS.get(track))


def app__dashboard_new_article_track(track):
    resolved_track = _resolve_submission_track(track)
    if not resolved_track:
        flash(
            t('invalid_submission_track') if t('invalid_submission_track') != 'invalid_submission_track' else 'Please select a valid submission track',
            'error'
        )
        return redirect(url_for('app__dashboard_new_article'))
    return redirect(url_for('app__dashboard_new_article', track=resolved_track))


def app__dashboard_payments():
    return app__dashboard_purchases()


def app__dashboard_guides():
    return render_template('dashboard/guides.html')


def app__dashboard_notifications():
    user_id = session.get('user_id')
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = 20

    total_notifications = _count_dashboard_notifications(user_id)
    total_pages = (total_notifications + per_page - 1) // per_page if total_notifications else 1
    notifications = _fetch_dashboard_notifications_page(user_id, page=page, per_page=per_page)
    unread_count = _count_dashboard_unread_notifications(user_id)

    return render_template(
        'dashboard/notifications.html',
        notifications=notifications,
        page=page,
        total_pages=total_pages,
        total_notifications=total_notifications,
        unread_count=unread_count
    )


def app__dashboard_notification_read(notification_id):
    _mark_dashboard_notification_read(notification_id, session.get('user_id'))
    redirect_url = _safe_internal_redirect(
        request.form.get('redirect_url') or request.referrer,
        'app__dashboard_notifications',
    )
    return redirect(redirect_url)


def app__dashboard_notification_open(notification_id):
    fallback_url = _safe_internal_redirect(
        request.form.get('redirect_url') or request.referrer,
        'app__dashboard_notifications',
    )
    notification = _get_dashboard_notification(notification_id, session.get('user_id'))
    if not notification:
        flash(
            t('notification_not_found') if t('notification_not_found') != 'notification_not_found' else 'Notification not found',
            'error'
        )
        return redirect(fallback_url)

    _mark_dashboard_notification_read(notification_id, session.get('user_id'))
    action_url = (notification.get('action_url') or '').strip()
    if action_url:
        return redirect(_safe_internal_redirect(action_url, 'app__dashboard_notifications'))
    return redirect(fallback_url)


def app__dashboard_notification_read_all():
    changed = _mark_dashboard_notifications_read_all(session.get('user_id'))
    if changed:
        flash(
            t('notifications_marked_read') if t('notifications_marked_read') != 'notifications_marked_read' else f'Marked as read: {changed}',
            'success'
        )
    redirect_url = _safe_internal_redirect(
        request.form.get('redirect_url') or request.referrer,
        'app__dashboard_notifications',
    )
    return redirect(redirect_url)


def app__dashboard_profile():
    _ensure_user_doc_upload_columns()
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_photo':
            if 'photo' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})

            file = request.files['photo']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})

            if file and allowed_file(file.filename):
                try:
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"avatar_{session['user_id']}_{int(time.time())}.{extension}"
                    avatars_folder = current_app.config['AVATARS_FOLDER']
                    os.makedirs(avatars_folder, exist_ok=True)
                    filepath = os.path.join(avatars_folder, filename)

                    user_rows = dbc.users.get(id=session['user_id']).exec()
                    user = user_rows[0] if user_rows else {}
                    old_avatar_path = _resolve_upload_file_path(user.get('avatar'))
                    if old_avatar_path and os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)

                    file.save(filepath)
                    avatar_url = f"/static/uploads/avatars/{filename}"

                    dbc.users.get(id=session['user_id']).update(avatar=avatar_url).exec()

                    session_user = session.get('user') or {}
                    if session_user:
                        session_user['avatar'] = avatar_url
                        session['user'] = session_user

                    return jsonify({'success': True, 'avatar_url': avatar_url})
                except Exception:
                    current_app.logger.exception('Failed to update profile avatar')
                    return jsonify({'success': False, 'message': 'Failed to upload profile photo'})

            return jsonify({'success': False, 'message': 'Invalid file type'})

        if action == 'delete_photo':
            try:
                user_rows = dbc.users.get(id=session['user_id']).exec()
                user = user_rows[0] if user_rows else {}
                old_avatar_path = _resolve_upload_file_path(user.get('avatar'))
                if old_avatar_path and os.path.exists(old_avatar_path):
                    os.remove(old_avatar_path)

                dbc.users.get(id=session['user_id']).update(avatar=None).exec()

                session_user = session.get('user') or {}
                if session_user:
                    session_user['avatar'] = None
                    session['user'] = session_user

                return jsonify({'success': True, 'avatar_url': '/static/default_avatar.png'})
            except Exception:
                current_app.logger.exception('Failed to delete profile avatar')
                return jsonify({'success': False, 'message': 'Failed to delete profile photo'})

        if action == 'save_profile':
            country_id_raw = request.form.get('country_id')
            country_id = _parse_int(country_id_raw)
            if country_id_raw and country_id is None:
                flash('Invalid country selected', 'error')
                return redirect(url_for('app__dashboard_profile'))
            if country_id is None:
                flash('Country is required', 'error')
                return redirect(url_for('app__dashboard_profile'))
            if country_id is not None:
                country = dbc.fix_country.get(id=country_id).exec()
                if not country:
                    flash('Invalid country selected', 'error')
                    return redirect(url_for('app__dashboard_profile'))

            first_name = sanitize_input(request.form.get('name'))
            second_name = sanitize_input(request.form.get('second_name'))
            father_name = sanitize_input(request.form.get('father_name')) or None
            if not first_name or not second_name or not father_name:
                flash("Ism, familiya va sharif maydonlari majburiy", 'error')
                return redirect(url_for('app__dashboard_profile'))

            dbc.users.get(id=session['user_id']).update(
                name=first_name,
                second_name=second_name,
                father_name=father_name,
                country_id=country_id
            ).exec()

            academic_position = (request.form.get('academic_position') or '').strip().lower()
            if not academic_position:
                flash("Ilmiy daraja yoki faoliyat turini tanlash majburiy", 'error')
                return redirect(url_for('app__dashboard_profile'))
            if academic_position not in ACADEMIC_POSITION_CHOICES:
                flash('Invalid academic position selected', 'error')
                return redirect(url_for('app__dashboard_profile'))

            submitted_doc_path = sanitize_input(request.form.get('document_path')) or None
            if submitted_doc_path and not _resolve_upload_file_path(submitted_doc_path):
                flash('Invalid document path', 'error')
                return redirect(url_for('app__dashboard_profile'))
            submitted_document_type = _normalize_document_type(request.form.get('document_type'))
            submitted_document_holder_name = sanitize_input(request.form.get('document_holder_name')) or None
            submitted_institution_name = sanitize_input(request.form.get('institution_name')) or None

            existing_doc_rows = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()
            existing_doc = existing_doc_rows[0] if existing_doc_rows else None
            effective_doc_path = submitted_doc_path or (existing_doc.get('file_path') if existing_doc else None)
            now_ts = int(time.time())

            if existing_doc:
                old_doc_path = existing_doc.get('file_path')
                doc_changed = old_doc_path != effective_doc_path
                title_changed = (existing_doc.get('work_title') or '').strip().lower() != academic_position
                old_document_type = _normalize_document_type(existing_doc.get('document_type'))
                effective_document_type = submitted_document_type or old_document_type
                if effective_doc_path and not effective_document_type:
                    effective_document_type = _default_document_type_for_position(academic_position)
                doc_type_changed = old_document_type != effective_document_type
                old_document_holder_name = sanitize_input(existing_doc.get('document_holder_name')) or None
                old_institution_name = sanitize_input(existing_doc.get('institution_name')) or None
                effective_document_holder_name = submitted_document_holder_name or old_document_holder_name
                if effective_doc_path and not effective_document_holder_name:
                    effective_document_holder_name = _account_full_name(user)
                effective_institution_name = submitted_institution_name or old_institution_name
                holder_name_changed = old_document_holder_name != effective_document_holder_name
                institution_changed = old_institution_name != effective_institution_name

                update_payload = {
                    'work_title': academic_position,
                    'file_path': effective_doc_path,
                    'document_type': effective_document_type,
                    'document_holder_name': effective_document_holder_name,
                    'institution_name': effective_institution_name,
                    'updated_at': now_ts
                }
                if effective_doc_path and (
                    doc_changed
                    or title_changed
                    or doc_type_changed
                    or holder_name_changed
                    or institution_changed
                    or not existing_doc.get('verification_status')
                ):
                    update_payload['verification_status'] = 'pending'

                dbc.user_doc_uploads.get(id=existing_doc['id']).update(**update_payload).exec()

                if doc_changed and old_doc_path and submitted_doc_path:
                    old_doc_abs = _resolve_upload_file_path(old_doc_path)
                    if old_doc_abs and os.path.exists(old_doc_abs):
                        try:
                            os.remove(old_doc_abs)
                        except OSError:
                            pass
            else:
                effective_document_type = submitted_document_type
                if effective_doc_path and not effective_document_type:
                    effective_document_type = _default_document_type_for_position(academic_position)
                effective_document_holder_name = submitted_document_holder_name
                if effective_doc_path and not effective_document_holder_name:
                    effective_document_holder_name = _account_full_name(user)
                dbc.user_doc_uploads.add(
                    user_id=session['user_id'],
                    work_title=academic_position,
                    file_path=effective_doc_path,
                    document_type=effective_document_type,
                    document_holder_name=effective_document_holder_name,
                    institution_name=submitted_institution_name,
                    verification_status='pending' if effective_doc_path else None,
                    created_at=now_ts,
                    updated_at=now_ts
                ).exec()

            session_user = session.get('user') or {}
            if session_user:
                session_user.update({
                    'name': first_name,
                    'second_name': second_name,
                    'father_name': father_name,
                    'country_id': country_id
                })
                session['user'] = _decode_row_strings(session_user)

            flash('Profile updated successfully', 'success')
            return redirect(url_for('app__dashboard_profile'))

        if action == 'save_author_profile':
            orcid = sanitize_input(request.form.get('orcid')) or None
            author_email = sanitize_input(request.form.get('email')).lower()
            profile_data = {
                'name': sanitize_input(request.form.get('name')),
                'organization': sanitize_input(request.form.get('organization')),
                'department': sanitize_input(request.form.get('department')),
                'position': sanitize_input(request.form.get('position')),
                'email': author_email,
                'phone': sanitize_input(request.form.get('phone')),
                'orcid': orcid,
                'address_street': sanitize_input(request.form.get('address_street')),
                'address_city': sanitize_input(request.form.get('address_city')),
                'address_country': sanitize_input(request.form.get('address_country')),
                'address_zip': sanitize_input(request.form.get('address_zip')),
                'updated_at': int(time.time())
            }

            required_fields = (
                'name',
                'organization',
                'department',
                'position',
                'email',
                'phone',
                'address_street',
                'address_city',
                'address_country',
                'address_zip',
            )
            if not all(profile_data[field] for field in required_fields):
                flash('Please fill in all required author profile fields', 'error')
                return redirect(url_for('app__dashboard_profile'))
            if orcid and not _is_valid_orcid(orcid):
                flash('ORCID format is invalid. Example: 0000-0000-0000-0000', 'error')
                return redirect(url_for('app__dashboard_profile'))
            if not is_valid_email(profile_data['email']):
                flash('Invalid email format', 'error')
                return redirect(url_for('app__dashboard_profile'))

            author_profile = dbc.author_profile.get(user_id=session['user_id']).exec()
            if author_profile:
                dbc.author_profile.get(user_id=session['user_id']).update(**profile_data).exec()
            else:
                profile_data['user_id'] = session['user_id']
                profile_data['created_at'] = int(time.time())
                dbc.author_profile.add(**profile_data).exec()

            # Auto-heal ORCID placeholder emails once the author provides
            # a real contact email in profile settings.
            user_columns = set(dbc.columns.get('users', []))
            if 'email' in user_columns:
                user_rows = dbc.users.get(id=session['user_id']).exec()
                if user_rows:
                    user_row = user_rows[0]
                    existing_email = (user_row.get('email') or '').strip().lower()
                    if not existing_email or existing_email.endswith('@orcid.local'):
                        try:
                            dbc.users.get(id=session['user_id']).update(email=author_email).exec()
                            session_user = session.get('user') or {}
                            if session_user:
                                session_user['email'] = author_email
                                session['user'] = _decode_row_strings(session_user)
                        except Exception:
                            try:
                                dbc.conn.rollback()
                            except Exception:
                                pass
                            flash(
                                'Author profile saved, but account email could not be updated (possibly already used).',
                                'warning'
                            )

            flash('Author profile updated successfully', 'success')
            return redirect(url_for('app__dashboard_profile'))

        if action == 'upload_academic_document':
            if 'academic_document' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})

            file = request.files['academic_document']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})

            if file and allowed_file(file.filename, {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}):
                timestamp = int(time.time())
                filename = f"academic_doc_{session['user_id']}_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}"

                documents_folder = os.path.join(settings.SAVE_PATH, 'private_uploads', 'documents')
                os.makedirs(documents_folder, exist_ok=True)

                filepath = os.path.join(documents_folder, filename)

                file.save(filepath)
                file_ref = build_private_upload_ref('documents', filename)

                return jsonify({
                    'success': True,
                    'file_ref': file_ref,
                    'file_path': file_ref,
                    'download': upload_access_url(file_ref),
                    'filename': filename
                })

            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PDF, DOC, DOCX, JPG, PNG'})

    user = _decode_row_strings(dbc.users.get(id=session['user_id']).exec()[0])
    author_profile = dbc.author_profile.get(user_id=session['user_id']).exec()
    author_profile_row = _decode_row_strings(author_profile[0]) if author_profile else None
    user_doc_upload = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()
    fix_country = dbc.fix_country.get().exec()
    profile_completion = get_user_profile_completion(user_row=user, user_id=session['user_id'], author_row=author_profile_row)

    # Keep sidebar session info readable for already logged-in users.
    session_user = session.get('user') or {}
    if session_user:
        session['user'] = _decode_row_strings(session_user)

    return render_template('dashboard/profile.html',
                         user=user,
                         author_profile=author_profile_row,
                         user_doc_upload=user_doc_upload[0] if user_doc_upload else None,
                         document_type_choices=_document_type_choices(),
                         document_ui_labels=_profile_document_ui_labels(),
                         fix_country=fix_country,
                         profile_completion=profile_completion)


def register(app):
    app.add_url_rule('/dashboard', view_func=author_login_required(app__dashboard))
    app.add_url_rule('/dashboard/articles', view_func=author_login_required(app__dashboard_articles))
    app.add_url_rule('/dashboard/articles/delete/<int:submission_id>', view_func=author_login_required(app__dashboard_articles_delete), methods=['POST'])
    app.add_url_rule('/dashboard/purchases', view_func=author_login_required(app__dashboard_purchases))
    app.add_url_rule('/dashboard/new_article', view_func=author_login_required(app__dashboard_new_article))
    app.add_url_rule('/dashboard/new_article/<track>', view_func=author_login_required(app__dashboard_new_article_track))
    app.add_url_rule('/dashboard/payments', view_func=author_login_required(app__dashboard_payments))
    app.add_url_rule('/dashboard/guides', view_func=author_login_required(app__dashboard_guides))
    app.add_url_rule('/dashboard/notifications', view_func=author_login_required(app__dashboard_notifications))
    app.add_url_rule('/dashboard/notifications/open/<int:notification_id>', view_func=author_login_required(app__dashboard_notification_open), methods=['POST'])
    app.add_url_rule('/dashboard/notifications/read/<int:notification_id>', view_func=author_login_required(app__dashboard_notification_read), methods=['POST'])
    app.add_url_rule('/dashboard/notifications/read-all', view_func=author_login_required(app__dashboard_notification_read_all), methods=['POST'])
    app.add_url_rule('/dashboard/profile', view_func=author_login_required(app__dashboard_profile), methods=['GET', 'POST'])
    app.add_url_rule('/dashboard/files/<path:storage_key>', endpoint='app__dashboard_private_file', view_func=author_login_required(app__dashboard_private_file))
