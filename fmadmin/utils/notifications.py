import json

from flask import session

from utils.roles import staff_roles_for_user


SUPPORTED_NOTIFICATION_LANGUAGES = ('uz', 'ru', 'en')


def clean_notification_text(value):
    if value is None:
        return ''
    return str(value).strip()


def parse_notification_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_notification_language(value, default='uz'):
    language = clean_notification_text(value or default).lower()
    return language if language in SUPPORTED_NOTIFICATION_LANGUAGES else default


def current_notification_language():
    return normalize_notification_language(session.get('language') or 'uz', default='uz')


def localized_texts(uz_text, ru_text=None, en_text=None):
    texts = {}
    for lang, value in (
        ('uz', uz_text),
        ('ru', ru_text if ru_text is not None else uz_text),
        ('en', en_text if en_text is not None else uz_text),
    ):
        text = clean_notification_text(value)
        if text:
            texts[lang] = text
    return texts


def user_allows_email_notifications(user_row):
    if not user_row:
        return False
    value = user_row.get('is_notify')
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return clean_notification_text(value).lower() in {'1', 'true', 'yes', 'on'}


def role_notification_access_clause(current_user):
    user_id = parse_notification_int((current_user or {}).get('id'))
    target_roles = staff_roles_for_user(current_user)
    clauses = []
    args = []

    if user_id is not None:
        clauses.append("target_user_id = %s")
        args.append(user_id)

    if target_roles:
        role_clause = " OR ".join(["target_role = %s"] * len(target_roles))
        clauses.append(f"(target_user_id IS NULL AND (({role_clause}) OR target_role = 'all'))")
        args.extend(target_roles)

    if not clauses:
        return '', []

    return "(" + " OR ".join(clauses) + ")", args


def _normalize_localized_map(value):
    if not isinstance(value, dict):
        return {}

    result = {}
    for lang in SUPPORTED_NOTIFICATION_LANGUAGES:
        text = clean_notification_text(value.get(lang))
        if text:
            result[lang] = text
    return result


def _pick_localized_value(values, preferred_language='uz'):
    if not values:
        return ''

    ordered_languages = [preferred_language] + [lang for lang in SUPPORTED_NOTIFICATION_LANGUAGES if lang != preferred_language]
    for lang in ordered_languages:
        text = clean_notification_text(values.get(lang))
        if text:
            return text

    for value in values.values():
        text = clean_notification_text(value)
        if text:
            return text
    return ''


def _load_notification_metadata(metadata_text):
    metadata_value = clean_notification_text(metadata_text)
    if not metadata_value:
        return {}
    try:
        parsed = json.loads(metadata_value)
    except Exception:
        return {'legacy_metadata_text': metadata_value}
    return parsed if isinstance(parsed, dict) else {'legacy_metadata_text': metadata_value}


def prepare_notification_content(title, message, metadata_text=None, default_language='uz'):
    title_map = _normalize_localized_map(title)
    message_map = _normalize_localized_map(message)

    title_text = clean_notification_text(title)
    if title_map:
        title_text = _pick_localized_value(title_map, preferred_language=default_language)

    message_text = clean_notification_text(message)
    if message_map:
        message_text = _pick_localized_value(message_map, preferred_language=default_language)

    metadata = _load_notification_metadata(metadata_text)
    if title_map:
        metadata['localized_title'] = title_map
    if message_map:
        metadata['localized_message'] = message_map

    metadata_value = clean_notification_text(metadata_text)
    if metadata:
        metadata_value = json.dumps(metadata, ensure_ascii=True, separators=(',', ':'))

    return title_text, message_text, metadata_value


def apply_localized_notification_content(notification_row, language=None):
    if not notification_row:
        return notification_row

    resolved = dict(notification_row)
    lang = clean_notification_text(language or current_notification_language()).lower()
    if lang not in SUPPORTED_NOTIFICATION_LANGUAGES:
        lang = 'uz'

    metadata = _load_notification_metadata(resolved.get('metadata_text'))
    title_map = _normalize_localized_map(metadata.get('localized_title'))
    message_map = _normalize_localized_map(metadata.get('localized_message'))

    if title_map:
        resolved['title'] = _pick_localized_value(title_map, preferred_language=lang)
    if message_map:
        resolved['message'] = _pick_localized_value(message_map, preferred_language=lang)

    return resolved
