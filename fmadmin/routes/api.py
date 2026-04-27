# flake8: noqa
import os
import time
import uuid
import logging
import requests
from flask import request, jsonify
from werkzeug.utils import secure_filename
from extensions import db
from modules.translate import t, translate, clear_translations_cache
from utils.auth import api_permission_required, api_superadmin_required
import settings

logger = logging.getLogger(__name__)
api_content_required = api_permission_required('fmadmin.content.manage', 'Content management access required')
api_finance_required = api_permission_required('fmadmin.finance.manage', 'Finance management access required')
api_users_required = api_permission_required('fmadmin.users.manage', 'User management access required')
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


def _json_payload():
    return request.get_json(silent=True) or {}


def _first_record(result):
    if isinstance(result, list):
        return result[0] if result else None
    if isinstance(result, dict):
        return result
    return None


def _parse_int(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        text = str(value).strip()
        if text == '':
            return None
        return int(text)
    except (TypeError, ValueError):
        return None


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


def _parse_float(value, default=0.0):
    if value in (None, ''):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_discount_percent(value):
    numeric = _parse_float(value, 0.0)
    if numeric < 0:
        return 0.0
    if numeric > 100:
        return 100.0
    return numeric


def _normalize_entitlement_scope(value):
    normalized = str(value or 'all').strip().lower()
    return normalized if normalized in TARIFF_ENTITLEMENT_SCOPES else 'all'


def _normalize_academic_position(value):
    normalized = str(value or '').strip().lower()
    normalized = normalized.replace('’', "'")
    normalized = ACADEMIC_POSITION_ALIASES.get(normalized, normalized)
    return normalized if normalized in ALLOWED_ACADEMIC_POSITIONS else None


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


def _parse_feature_permissions(value):
    normalized_items = []
    for item in _parse_text_array(value):
        normalized = _normalize_feature_permission(item)
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


def _default_feature_permissions(entitlement_scope):
    scope = _normalize_entitlement_scope(entitlement_scope)
    if scope == 'archive':
        return [
            'access_archive_content',
            'download_subscription_files',
            'article_discount',
            'issue_discount',
        ]
    return [
        'access_latest_content',
        'access_archive_content',
        'download_subscription_files',
        'article_discount',
        'issue_discount',
    ]


def _normalize_document_type(value):
    normalized = str(value or '').strip().lower()
    normalized = normalized.replace('’', "'")
    normalized = DOCUMENT_TYPE_ALIASES.get(normalized, normalized)
    return normalized if normalized in ALLOWED_DOCUMENT_TYPES else None


def _parse_required_document_types(value):
    normalized_items = []
    for item in _parse_text_array(value):
        normalized = _normalize_document_type(item)
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


def _table_columns(table_name):
    try:
        return set(db.columns.get(table_name, []))
    except Exception:
        return set()


def _apply_aliases(payload, columns, alias_pairs):
    if not alias_pairs:
        return payload
    for old_name, new_name in alias_pairs:
        if new_name in payload and new_name not in columns and old_name in columns and old_name not in payload:
            payload[old_name] = payload[new_name]
        if old_name in payload and old_name not in columns and new_name in columns and new_name not in payload:
            payload[new_name] = payload[old_name]
    return payload


def _ensure_tariff_duration_column(default_days=30):
    columns = _table_columns('tariffs')
    if not columns or 'duration_days' in columns:
        return
    cursor = None
    try:
        cursor = db.conn.cursor()
        cursor.execute(f"ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS duration_days integer DEFAULT {int(default_days)};")
        cursor.execute(
            "UPDATE tariffs "
            "SET duration_days = COALESCE(duration_days, user_limit, %s) "
            "WHERE duration_days IS NULL;",
            (int(default_days),)
        )
        db.conn.commit()
        db._init_tables()
        db._init_columns()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to ensure duration_days column for tariffs")
    finally:
        if cursor is not None:
            cursor.close()


def _ensure_tariff_archive_column():
    columns = _table_columns('tariffs')
    if not columns or 'is_archived' in columns:
        return
    cursor = None
    try:
        cursor = db.conn.cursor()
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS is_archived boolean DEFAULT false;")
        cursor.execute("UPDATE tariffs SET is_archived = false WHERE is_archived IS NULL;")
        db.conn.commit()
        db._init_tables()
        db._init_columns()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to ensure is_archived column for tariffs")
    finally:
        if cursor is not None:
            cursor.close()


def _ensure_tariff_entitlement_columns():
    columns = _table_columns('tariffs')
    if not columns:
        return

    missing_columns = {}
    if 'entitlement_scope' not in columns:
        missing_columns['entitlement_scope'] = "text DEFAULT 'all'"
    if 'archive_days_threshold' not in columns:
        missing_columns['archive_days_threshold'] = f"integer DEFAULT {int(DEFAULT_ARCHIVE_DAYS_THRESHOLD)}"
    if 'article_discount_pct' not in columns:
        missing_columns['article_discount_pct'] = "double precision DEFAULT 0"
    if 'issue_discount_pct' not in columns:
        missing_columns['issue_discount_pct'] = "double precision DEFAULT 0"
    if 'subscription_discount_pct' not in columns:
        missing_columns['subscription_discount_pct'] = "double precision DEFAULT 0"
    if 'subscription_discount_start_at' not in columns:
        missing_columns['subscription_discount_start_at'] = "bigint"
    if 'subscription_discount_end_at' not in columns:
        missing_columns['subscription_discount_end_at'] = "bigint"
    if 'monthly_download_limit' not in columns:
        missing_columns['monthly_download_limit'] = "integer DEFAULT 0"
    if 'required_academic_positions' not in columns:
        missing_columns['required_academic_positions'] = "text[] DEFAULT '{}'::text[]"
    if 'requires_verified_document' not in columns:
        missing_columns['requires_verified_document'] = "boolean DEFAULT false"
    if 'eligibility_note' not in columns:
        missing_columns['eligibility_note'] = "text"
    if 'feature_permissions' not in columns:
        missing_columns['feature_permissions'] = "text[] DEFAULT '{}'::text[]"
    if 'required_document_types' not in columns:
        missing_columns['required_document_types'] = "text[] DEFAULT '{}'::text[]"

    cursor = None
    try:
        cursor = db.conn.cursor()
        for column_name, column_type in missing_columns.items():
            cursor.execute(f"ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS {column_name} {column_type};")

        cursor.execute(
            "UPDATE tariffs SET entitlement_scope = COALESCE(NULLIF(TRIM(entitlement_scope), ''), 'all') "
            "WHERE entitlement_scope IS NULL OR NULLIF(TRIM(entitlement_scope), '') IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET archive_days_threshold = COALESCE(archive_days_threshold, %s) "
            "WHERE archive_days_threshold IS NULL;",
            (int(DEFAULT_ARCHIVE_DAYS_THRESHOLD),)
        )
        cursor.execute(
            "UPDATE tariffs SET article_discount_pct = COALESCE(article_discount_pct, 0) "
            "WHERE article_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET issue_discount_pct = COALESCE(issue_discount_pct, 0) "
            "WHERE issue_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET subscription_discount_pct = COALESCE(subscription_discount_pct, 0) "
            "WHERE subscription_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET monthly_download_limit = COALESCE(monthly_download_limit, 0) "
            "WHERE monthly_download_limit IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET required_academic_positions = COALESCE(required_academic_positions, ARRAY[]::text[]) "
            "WHERE required_academic_positions IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET requires_verified_document = COALESCE(requires_verified_document, false) "
            "WHERE requires_verified_document IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET feature_permissions = COALESCE(feature_permissions, ARRAY[]::text[]) "
            "WHERE feature_permissions IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET required_document_types = COALESCE(required_document_types, ARRAY[]::text[]) "
            "WHERE required_document_types IS NULL;"
        )
        db.conn.commit()
        db._init_tables()
        db._init_columns()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to ensure entitlement columns for tariffs")
    finally:
        if cursor is not None:
            cursor.close()


def _count_subscription_payments_for_tariff(tariff_id):
    cursor = None
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM payments WHERE payment_type = 'subscription' AND %s = ANY(ids)",
            (int(tariff_id),)
        )
        row = cursor.fetchone()
        return int(row[0] or 0) if row else 0
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to count subscription payments for tariff_id=%s", tariff_id)
        return 0
    finally:
        if cursor is not None:
            cursor.close()


def _normalize_reference_payload(data):
    payload = dict(data or {})
    payload.pop('reference_id', None)
    article_id = payload.pop('article_id', None)
    if payload.get('publication_id') in (None, '') and article_id not in (None, ''):
        payload['publication_id'] = article_id

    columns = _table_columns('publication_refs')
    alias_pairs = [
        ('wos_link', 'web_of_science_url'),
        ('gscholar_link', 'google_scholar_url'),
        ('web_link', 'url'),
        ('resource', 'source_title'),
    ]
    payload = _apply_aliases(payload, columns, alias_pairs)

    for key in ('publication_id', 'publication_year', 'created_at'):
        if key in payload:
            payload[key] = _parse_int(payload[key])

    if columns:
        payload = {k: v for k, v in payload.items() if k in columns}
    return payload


def _normalize_citation_payload(data):
    payload = dict(data or {})
    payload.pop('citation_id', None)
    article_id = payload.pop('article_id', None)
    if payload.get('publication_id') in (None, '') and article_id not in (None, ''):
        payload['publication_id'] = article_id

    columns = _table_columns('publication_citations')
    alias_pairs = [
        ('wos_link', 'web_of_science_url'),
        ('gscholar_link', 'google_scholar_url'),
    ]
    payload = _apply_aliases(payload, columns, alias_pairs)

    for key in ('publication_id', 'created_at'):
        if key in payload:
            payload[key] = _parse_int(payload[key])

    if columns:
        payload = {k: v for k, v in payload.items() if k in columns}
    return payload


def _sync_mainweb_translation_cache():
    headers = {'Content-Type': 'application/json'}
    sync_token = (settings.TRANSLATION_SYNC_TOKEN or '').strip()
    if sync_token:
        headers['X-Translation-Sync-Token'] = sync_token

    base_urls = []
    primary_url = (settings.MAINWEB_INTERNAL_URL or '').strip().rstrip('/')
    if primary_url:
        base_urls.append(primary_url)
    if 'http://localhost:5000' not in base_urls:
        base_urls.append('http://localhost:5000')

    last_error = 'Mainweb sync failed'
    for base_url in base_urls:
        api_url = f"{base_url}/api/translations/clear_cache"
        try:
            response = requests.post(api_url, headers=headers, timeout=10)
        except requests.exceptions.ConnectionError:
            last_error = f'Cannot connect to mainweb ({base_url})'
            continue
        except requests.exceptions.Timeout:
            last_error = f'Timeout while connecting to mainweb ({base_url})'
            continue
        except Exception as exc:
            logger.exception("Translation sync request failed")
            last_error = f'Unexpected sync error: {exc}'
            continue

        result = {}
        try:
            result = response.json()
        except Exception:
            result = {}

        if response.status_code != 200:
            message = result.get('message') or f'HTTP {response.status_code}'
            last_error = f'Mainweb sync failed: {message}'
            continue

        if not result.get('success'):
            last_error = result.get('message') or 'Mainweb rejected cache clear request'
            continue

        return True, result.get('message') or 'Translation cache cleared on mainweb'

    return False, last_error


@api_superadmin_required
def get_translation(alias):
    safe_alias = (alias or '').strip()
    if not safe_alias:
        return jsonify({'success': False, 'message': 'Alias is required'}), 400

    translation = _first_record(db.translations.get(alias=safe_alias).exec())
    if translation:
        return jsonify({'success': True, 'translation': translation})
    return jsonify({'success': False, 'message': 'Translation not found'}), 404


@api_superadmin_required
def update_translation(alias):
    safe_alias = (alias or '').strip()
    if not safe_alias:
        return jsonify({'success': False, 'message': 'Alias is required'}), 400

    data = _json_payload()
    existing = _first_record(db.translations.get(alias=safe_alias).exec()) or {}

    content = data.get('content', existing.get('content', ''))
    content_ru = data.get('content_ru', existing.get('content_ru', ''))
    content_uz = data.get('content_uz', existing.get('content_uz', ''))
    content = '' if content is None else str(content)
    content_ru = '' if content_ru is None else str(content_ru)
    content_uz = '' if content_uz is None else str(content_uz)

    if existing:
        db.translations.get(alias=safe_alias).update(
            content=content,
            content_ru=content_ru,
            content_uz=content_uz
        ).exec()
    else:
        db.translations.add(
            alias=safe_alias,
            content=content,
            content_ru=content_ru,
            content_uz=content_uz,
            created_at=int(time.time())
        ).exec()

    clear_translations_cache()
    sync_ok, sync_message = _sync_mainweb_translation_cache()
    return jsonify({
        'success': True,
        'synced': sync_ok,
        'sync_message': sync_message
    })


@api_superadmin_required
def sync_translations():
    translations = db.translations.all().exec()
    translations_count = len(translations)
    sync_ok, sync_message = _sync_mainweb_translation_cache()
    if sync_ok:
        return jsonify({
            'success': True,
            'message': f'Synchronized {translations_count} translations. {sync_message}',
            'translations_count': translations_count
        })
    return jsonify({
        'success': False,
        'message': sync_message,
        'translations_count': translations_count
    })


@api_finance_required
def create_tariff():
    _ensure_tariff_duration_column()
    _ensure_tariff_archive_column()
    _ensure_tariff_entitlement_columns()
    data = _json_payload()
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'name is required'}), 400
    duration_days = _parse_int(data.get('duration_days'))
    if duration_days is None:
        duration_days = _parse_int(data.get('user_limit'))
    if duration_days is None:
        duration_days = 30
    entitlement_scope = _normalize_entitlement_scope(data.get('entitlement_scope'))
    archive_days_threshold = _parse_int(data.get('archive_days_threshold'))
    if archive_days_threshold is None or archive_days_threshold < 1:
        archive_days_threshold = DEFAULT_ARCHIVE_DAYS_THRESHOLD
    article_discount_pct = _normalize_discount_percent(data.get('article_discount_pct'))
    issue_discount_pct = _normalize_discount_percent(data.get('issue_discount_pct'))
    subscription_discount_pct = _normalize_discount_percent(data.get('subscription_discount_pct'))
    subscription_discount_start_at = _parse_int(data.get('subscription_discount_start_at'))
    subscription_discount_end_at = _parse_int(data.get('subscription_discount_end_at'))
    monthly_download_limit = _parse_int(data.get('monthly_download_limit'))
    if monthly_download_limit is None or monthly_download_limit < 0:
        monthly_download_limit = 0
    required_academic_positions = _parse_required_positions(data.get('required_academic_positions'))
    requires_verified_document = _parse_bool(data.get('requires_verified_document'))
    eligibility_note = data.get('eligibility_note')
    raw_feature_permissions = data.get('feature_permissions')
    if raw_feature_permissions is None:
        feature_permissions = _default_feature_permissions(entitlement_scope)
    else:
        feature_permissions = _parse_feature_permissions(raw_feature_permissions)
    required_document_types = _parse_required_document_types(data.get('required_document_types'))

    db.tariffs.add(
        name=data.get('name'),
        name_uz=data.get('name_uz'),
        name_ru=data.get('name_ru'),
        description=data.get('description'),
        description_uz=data.get('description_uz'),
        description_ru=data.get('description_ru'),
        price_rub=data.get('price_rub', 0),
        price_uzs=data.get('price_uzs', 0),
        price_usd=data.get('price_usd', 0),
        user_limit=duration_days,
        duration_days=duration_days,
        is_default=data.get('is_default', False),
        is_verified=data.get('is_verified', False),
        is_archived=False,
        entitlement_scope=entitlement_scope,
        archive_days_threshold=archive_days_threshold,
        article_discount_pct=article_discount_pct,
        issue_discount_pct=issue_discount_pct,
        subscription_discount_pct=subscription_discount_pct,
        subscription_discount_start_at=subscription_discount_start_at,
        subscription_discount_end_at=subscription_discount_end_at,
        monthly_download_limit=monthly_download_limit,
        required_academic_positions=required_academic_positions,
        requires_verified_document=requires_verified_document,
        eligibility_note=eligibility_note,
        feature_permissions=feature_permissions,
        required_document_types=required_document_types,
        created_at=data.get('created_at') or int(time.time()),
        updated_at=data.get('updated_at') or int(time.time())
    ).exec()

    return jsonify({'success': True})


@api_finance_required
def update_tariff(tariff_id):
    _ensure_tariff_duration_column()
    _ensure_tariff_archive_column()
    _ensure_tariff_entitlement_columns()
    data = _json_payload()
    duration_days = _parse_int(data.get('duration_days'))
    if duration_days is None:
        duration_days = _parse_int(data.get('user_limit'))
    if duration_days is None:
        duration_days = 30
    entitlement_scope = _normalize_entitlement_scope(data.get('entitlement_scope'))
    archive_days_threshold = _parse_int(data.get('archive_days_threshold'))
    if archive_days_threshold is None or archive_days_threshold < 1:
        archive_days_threshold = DEFAULT_ARCHIVE_DAYS_THRESHOLD
    article_discount_pct = _normalize_discount_percent(data.get('article_discount_pct'))
    issue_discount_pct = _normalize_discount_percent(data.get('issue_discount_pct'))
    subscription_discount_pct = _normalize_discount_percent(data.get('subscription_discount_pct'))
    subscription_discount_start_at = _parse_int(data.get('subscription_discount_start_at'))
    subscription_discount_end_at = _parse_int(data.get('subscription_discount_end_at'))
    monthly_download_limit = _parse_int(data.get('monthly_download_limit'))
    if monthly_download_limit is None or monthly_download_limit < 0:
        monthly_download_limit = 0
    required_academic_positions = _parse_required_positions(data.get('required_academic_positions'))
    requires_verified_document = _parse_bool(data.get('requires_verified_document'))
    eligibility_note = data.get('eligibility_note')
    raw_feature_permissions = data.get('feature_permissions')
    if raw_feature_permissions is None:
        feature_permissions = _default_feature_permissions(entitlement_scope)
    else:
        feature_permissions = _parse_feature_permissions(raw_feature_permissions)
    required_document_types = _parse_required_document_types(data.get('required_document_types'))

    db.tariffs.get(id=tariff_id).update(
        name=data.get('name'),
        name_uz=data.get('name_uz'),
        name_ru=data.get('name_ru'),
        description=data.get('description'),
        description_uz=data.get('description_uz'),
        description_ru=data.get('description_ru'),
        price_rub=data.get('price_rub', 0),
        price_uzs=data.get('price_uzs', 0),
        price_usd=data.get('price_usd', 0),
        user_limit=duration_days,
        duration_days=duration_days,
        is_default=data.get('is_default', False),
        is_verified=data.get('is_verified', False),
        entitlement_scope=entitlement_scope,
        archive_days_threshold=archive_days_threshold,
        article_discount_pct=article_discount_pct,
        issue_discount_pct=issue_discount_pct,
        subscription_discount_pct=subscription_discount_pct,
        subscription_discount_start_at=subscription_discount_start_at,
        subscription_discount_end_at=subscription_discount_end_at,
        monthly_download_limit=monthly_download_limit,
        required_academic_positions=required_academic_positions,
        requires_verified_document=requires_verified_document,
        eligibility_note=eligibility_note,
        feature_permissions=feature_permissions,
        required_document_types=required_document_types,
        updated_at=data.get('updated_at') or int(time.time())
    ).exec()
    return jsonify({'success': True})


@api_finance_required
def delete_tariff(tariff_id):
    try:
        _ensure_tariff_archive_column()
        tariff = db.tariffs.get(id=tariff_id).exec()
        if not tariff:
            return jsonify({'success': False, 'error': 'Тариф не найден'}), 404

        tariff = tariff[0]
        if tariff.get('is_default', False):
            return jsonify({'success': False, 'error': 'Нельзя удалить тариф по умолчанию'}), 400

        users_with_tariff = db.users.get(tariff_id=tariff_id).exec()
        payments_count = _count_subscription_payments_for_tariff(tariff_id)
        db.tariffs.get(id=tariff_id).update(
            is_archived=True,
            is_default=False,
            updated_at=int(time.time())
        ).exec()
        return jsonify({
            'success': True,
            'message': (
                f'Тариф архивирован. Пользователи на тарифе: {len(users_with_tariff)}. '
                f'Связанных подписочных платежей: {payments_count}.'
            )
        })
    except Exception:
        logger.exception('Failed to delete tariff_id=%s', tariff_id)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@api_content_required
def upload_image():
    file = None
    if 'upload' in request.files:
        file = request.files['upload']
    elif 'image' in request.files:
        file = request.files['image']

    if not file:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if request.content_length and request.content_length > 10 * 1024 * 1024:
        return jsonify({'success': False, 'message': 'File too large'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        return jsonify({'success': False, 'message': 'Invalid file type'})

    new_filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(settings.SAVE_PATH, 'static', 'uploads', 'images')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, new_filename)
    file.save(file_path)

    return jsonify({'success': True, 'url': f"/static/uploads/images/{new_filename}"})


@api_content_required
def get_publication_refs():
    refs = db.publication_refs.get().exec()
    return jsonify({'success': True, 'refs': refs})


@api_content_required
def create_publication_ref():
    data = _json_payload()
    result = db.publication_refs.add(**data).exec()
    return jsonify({'success': True, 'ref': result[0] if result else None})


@api_content_required
def get_article_references(article_id):
    refs = db.publication_refs.get(publication_id=article_id).exec()
    return jsonify({'success': True, 'refs': refs})


@api_content_required
def get_article_citations(article_id):
    citations = db.publication_citations.get(publication_id=article_id).exec()
    return jsonify({'success': True, 'citations': citations})


@api_content_required
def create_reference():
    data = _normalize_reference_payload(_json_payload())
    result = db.publication_refs.add(**data).exec()
    return jsonify({'success': True, 'reference': result[0] if result else None})


@api_content_required
def get_reference(reference_id):
    ref = db.publication_refs.get(id=reference_id).exec()
    if not ref:
        return jsonify({'success': False, 'message': 'Reference not found'}), 404
    return jsonify({'success': True, 'reference': ref[0]})


@api_content_required
def update_reference(reference_id):
    data = _normalize_reference_payload(_json_payload())
    if data:
        db.publication_refs.get(id=reference_id).update(**data).exec()
    ref = db.publication_refs.get(id=reference_id).exec()
    return jsonify({'success': True, 'reference': ref[0] if ref else None})


@api_content_required
def delete_reference(reference_id):
    db.publication_refs.get(id=reference_id).delete().exec()
    return jsonify({'success': True})


@api_content_required
def search_references():
    search = request.args.get('search', '').strip() or request.args.get('q', '').strip()
    if not search:
        return jsonify({'success': True, 'references': []})
    article_id = request.args.get('article_id') or request.args.get('publication_id')
    query = db.publication_refs.get()
    if article_id:
        query = query.equal(publication_id=article_id)
    refs = query.like(title=search).exec()
    return jsonify({'success': True, 'references': refs})


@api_content_required
def create_citation():
    data = _normalize_citation_payload(_json_payload())
    result = db.publication_citations.add(**data).exec()
    return jsonify({'success': True, 'citation': result[0] if result else None})


@api_content_required
def get_citation(citation_id):
    citation = db.publication_citations.get(id=citation_id).exec()
    if not citation:
        return jsonify({'success': False, 'message': 'Citation not found'}), 404
    return jsonify({'success': True, 'citation': citation[0]})


@api_content_required
def update_citation(citation_id):
    data = _normalize_citation_payload(_json_payload())
    if data:
        db.publication_citations.get(id=citation_id).update(**data).exec()
    citation = db.publication_citations.get(id=citation_id).exec()
    return jsonify({'success': True, 'citation': citation[0] if citation else None})


@api_content_required
def delete_citation(citation_id):
    db.publication_citations.get(id=citation_id).delete().exec()
    return jsonify({'success': True})


@api_users_required
def api_getauthor():
    data = _json_payload()
    author_id = data.get('author_id')
    orcid = data.get('orcid')
    name = (data.get('name') or '').strip()

    if author_id:
        author_profile = db.author_profile.get(id=author_id).exec()
    elif orcid:
        author_profile = db.author_profile.get(orcid=orcid).exec()
    elif data.get('search_by_name') and name:
        authors = db.author_profile.get().like(name=name).exec()
        return jsonify({'success': True, 'authors': authors, 'is_found': bool(authors)})
    elif name:
        author_profile = db.author_profile.get().like(name=name).exec()
    else:
        return jsonify({'success': False, 'message': 'Search criteria is required'}), 400

    if not author_profile:
        return jsonify({'success': True, 'is_found': False, 'author': None})

    author_profile = author_profile[0]
    return jsonify({'success': True, 'is_found': True, 'author': author_profile})


@api_users_required
def api_createauthor():
    data = _json_payload()
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Name is required'})

    result = db.author_profile.add(
        name=data.get('name'),
        organization=data.get('organization'),
        email=data.get('email'),
        position=data.get('position'),
        address_street=data.get('address_street'),
        address_country=data.get('address_country'),
        address_city=data.get('address_city'),
        address_zip=data.get('address_zip'),
        phone=data.get('phone'),
        orcid=data.get('orcid'),
        created_at=int(time.time())
    ).exec()

    return jsonify({'success': True, 'author': result[0] if result else None})


# ============================================================
# GLOBAL SEARCH API - Tezkor qidiruv funksiyasi
# ============================================================

@api_users_required
def global_search():
    """
    Global search - maqola, foydalanuvchi, muallif bo'yicha qidiruv
    Query parametrlar:
    - q: qidiruv so'zi (majburiy)
    - type: search turi (submissions, users, authors, all)
    - limit: natijalar soni (default: 10)
    """
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all').strip().lower()
    limit = min(_parse_int(request.args.get('limit')) or 10, 50)
    
    if not query:
        return jsonify({'success': False, 'message': 'Qidiruv so\'zi kerak'}), 400
    
    results = {
        'submissions': [],
        'users': [],
        'authors': []
    }
    
    try:
        # 1. Maqolalar bo'yicha qidiruv
        if search_type in ['all', 'submissions']:
            submissions_query = db.submissions.all().unequal(status='draft')
            
            # ID bo'yicha qidiruv (agar raqam bo'lsa)
            if query.isdigit():
                submissions_query = submissions_query.equal(id=int(query))
            else:
                # Sarlavha bo'yicha qidiruv
                submissions_query = submissions_query.like(title=query)
            
            submissions = submissions_query.order_by('id').exec()[:limit]
            
            # Mualliflar ma'lumotlarini qo'shish
            author_ids = {s.get('main_author_id') for s in submissions if s.get('main_author_id')}
            authors_map = {}
            if author_ids:
                authors = db.author_profile.all().any(id=list(author_ids)).exec()
                authors_map = {a['id']: a for a in authors if a.get('id')}
            
            for sub in submissions:
                author = authors_map.get(sub.get('main_author_id'), {})
                results['submissions'].append({
                    'id': sub.get('id'),
                    'title': sub.get('title') or 'Sarlavhasiz',
                    'status': sub.get('status'),
                    'workflow_stage': sub.get('workflow_stage'),
                    'author_name': author.get('name', 'Noma\'lum'),
                    'author_orcid': author.get('orcid', ''),
                    'created_date': sub.get('created_date'),
                    'type': 'submission',
                    'url': f'/fmadmin/submissions/{sub.get("id")}'
                })
        
        # 2. Foydalanuvchilar bo'yicha qidiruv
        if search_type in ['all', 'users']:
            users_query = db.users.all()
            
            # Email yoki ID bo'yicha aniq qidiruv
            if '@' in query:
                users_query = users_query.like(email=query)
            elif query.isdigit():
                users_query = users_query.equal(id=int(query))
            else:
                # Ism bo'yicha qidiruv
                users_query = users_query.like(name=query)
            
            users = users_query.order_by('id').exec()[:limit]
            
            for user in users:
                results['users'].append({
                    'id': user.get('id'),
                    'name': user.get('name', ''),
                    'email': user.get('email', ''),
                    'rolename': user.get('rolename', 'user'),
                    'orcid': user.get('orcid', ''),
                    'is_blocked': user.get('is_blocked', False),
                    'type': 'user',
                    'url': f'/fmadmin/users/users/{user.get("id")}'
                })
        
        # 3. Mualliflar bo'yicha qidiruv
        if search_type in ['all', 'authors']:
            authors_query = db.author_profile.all()
            
            # ORCID yoki ID bo'yicha aniq qidiruv
            if '-' in query and len(query) == 19:  # ORCID formati: 0000-0000-0000-0000
                authors_query = authors_query.equal(orcid=query)
            elif query.isdigit():
                authors_query = authors_query.equal(id=int(query))
            else:
                # Ism bo'yicha qidiruv
                authors_query = authors_query.like(name=query)
            
            authors = authors_query.order_by('id').exec()[:limit]
            
            for author in authors:
                results['authors'].append({
                    'id': author.get('id'),
                    'name': author.get('name', ''),
                    'organization': author.get('organization', ''),
                    'email': author.get('email', ''),
                    'orcid': author.get('orcid', ''),
                    'type': 'author',
                    'url': f'/fmadmin/users/users?orcid={author.get("orcid", "")}'
                })
        
        # Natijalarni sanash
        total_results = sum(len(results[key]) for key in results)
        
        return jsonify({
            'success': True,
            'query': query,
            'type': search_type,
            'total': total_results,
            'results': results
        })
        
    except Exception as e:
        logger.exception("Global search failed")
        return jsonify({'success': False, 'message': f'Qidiruv xatosi: {str(e)}'}), 500


def register(app):
    app.add_url_rule('/fmadmin/api/translation/<path:alias>', view_func=get_translation, methods=['GET'])
    app.add_url_rule('/fmadmin/api/translation/<path:alias>', view_func=update_translation, methods=['POST'])
    app.add_url_rule('/fmadmin/api/sync-translations', view_func=sync_translations, methods=['POST'])
    app.add_url_rule('/fmadmin/api/tariff', view_func=create_tariff, methods=['POST'])
    app.add_url_rule('/fmadmin/api/tariff/<int:tariff_id>', view_func=update_tariff, methods=['POST'])
    app.add_url_rule('/fmadmin/api/tariff/<int:tariff_id>/delete', view_func=delete_tariff, methods=['DELETE'])
    app.add_url_rule('/fmadmin/api/upload_image', view_func=upload_image, methods=['POST'])
    app.add_url_rule('/fmadmin/api/publication_refs', view_func=get_publication_refs)
    app.add_url_rule('/fmadmin/api/publication_refs', view_func=create_publication_ref, methods=['POST'])
    app.add_url_rule('/fmadmin/api/articles/<int:article_id>/references', view_func=get_article_references)
    app.add_url_rule('/fmadmin/api/articles/<int:article_id>/citations', view_func=get_article_citations)
    app.add_url_rule('/fmadmin/api/references', view_func=create_reference, methods=['POST'])
    app.add_url_rule('/fmadmin/api/references/<int:reference_id>', view_func=get_reference, methods=['GET'])
    app.add_url_rule('/fmadmin/api/references/<int:reference_id>', view_func=update_reference, methods=['PUT'])
    app.add_url_rule('/fmadmin/api/references/<int:reference_id>', view_func=delete_reference, methods=['DELETE'])
    app.add_url_rule('/fmadmin/api/references/search', view_func=search_references)
    app.add_url_rule('/fmadmin/api/citations', view_func=create_citation, methods=['POST'])
    app.add_url_rule('/fmadmin/api/citations/<int:citation_id>', view_func=get_citation, methods=['GET'])
    app.add_url_rule('/fmadmin/api/citations/<int:citation_id>', view_func=update_citation, methods=['PUT'])
    app.add_url_rule('/fmadmin/api/citations/<int:citation_id>', view_func=delete_citation, methods=['DELETE'])
    app.add_url_rule('/fmadmin/api/getauthor', view_func=api_getauthor, methods=['POST'])
    app.add_url_rule('/fmadmin/api/createauthor', view_func=api_createauthor, methods=['POST'])
    app.add_url_rule('/fmadmin/api/search', view_func=global_search, methods=['GET'])
