# flake8: noqa
import time
from flask import session

# Global DB connector instance
dbc = None

# Translations cache
_translations_cache = {}
_cache_timestamp = 0
_cache_ttl = 300  # 5 minutes

STATIC_TRANSLATIONS = {
    'uz': {
        'admin_payments_title': "To'lovlar",
        'admin_title_edit_payment': "To'lovni tahrirlash",
        'admin_label_filters': "Filtrlar",
        'admin_label_status': "Holat",
        'admin_label_all_statuses': "Barcha holatlar",
        'admin_label_status_pending': "Kutilmoqda",
        'admin_label_status_paid': "To'lov qilingan",
        'admin_label_status_rejected': "Rad etilgan",
        'admin_label_user': "Foydalanuvchi",
        'admin_label_amount': "To'lov summasi",
        'admin_label_created_at': "Yaratilgan sana",
        'admin_label_updated_at': "Yangilangan sana",
        'admin_label_file': "Fayl",
        'admin_label_actions': "Amallar",
        'admin_label_current_file': "Joriy fayl",
        'admin_label_comment': "Izoh",
        'admin_btn_apply': "Qo'llash",
        'admin_btn_reset': "Tozalash",
        'admin_btn_edit': "Tahrirlash",
        'admin_btn_save_changes': "Saqlash",
        'admin_btn_cancel': "Bekor qilish",
        'admin_btn_view': "Ko'rish",
        'admin_btn_view_current_file': "Joriy faylni ko'rish",
        'admin_msg_no_file': "Fayl yuklanmagan",
        'admin_msg_file_not_uploaded': "Fayl yuklanmagan",
        'admin_msg_error_saving': "Saqlashda xatolik",
        'admin_msg_unknown_error': "Noma'lum xatolik",
        'admin_msg_request_error': "So'rovda xatolik",
        'admin_pagination_showing': "Ko'rsatilmoqda",
        'admin_pagination_of': "dan",
        'admin_pagination_entries': "ta yozuv",
    },
    'ru': {
        'admin_payments_title': "Платежи",
        'admin_title_edit_payment': "Редактировать платеж",
        'admin_label_filters': "Фильтры",
        'admin_label_status': "Статус",
        'admin_label_all_statuses': "Все статусы",
        'admin_label_status_pending': "Ожидается",
        'admin_label_status_paid': "Оплачено",
        'admin_label_status_rejected': "Отклонено",
        'admin_label_user': "Пользователь",
        'admin_label_amount': "Сумма",
        'admin_label_created_at': "Создано",
        'admin_label_updated_at': "Обновлено",
        'admin_label_file': "Файл",
        'admin_label_actions': "Действия",
        'admin_label_current_file': "Текущий файл",
        'admin_label_comment': "Комментарий",
        'admin_btn_apply': "Применить",
        'admin_btn_reset': "Сбросить",
        'admin_btn_edit': "Редактировать",
        'admin_btn_save_changes': "Сохранить",
        'admin_btn_cancel': "Отмена",
        'admin_btn_view': "Просмотр",
        'admin_btn_view_current_file': "Просмотреть файл",
        'admin_msg_no_file': "Файл не загружен",
        'admin_msg_file_not_uploaded': "Файл не загружен",
        'admin_msg_error_saving': "Ошибка сохранения",
        'admin_msg_unknown_error': "Неизвестная ошибка",
        'admin_msg_request_error': "Ошибка запроса",
        'admin_pagination_showing': "Показано",
        'admin_pagination_of': "из",
        'admin_pagination_entries': "записей",
    },
    'en': {
        'admin_payments_title': "Payments",
        'admin_title_edit_payment': "Edit payment",
        'admin_label_filters': "Filters",
        'admin_label_status': "Status",
        'admin_label_all_statuses': "All statuses",
        'admin_label_status_pending': "Pending",
        'admin_label_status_paid': "Paid",
        'admin_label_status_rejected': "Rejected",
        'admin_label_user': "User",
        'admin_label_amount': "Amount",
        'admin_label_created_at': "Created at",
        'admin_label_updated_at': "Updated at",
        'admin_label_file': "File",
        'admin_label_actions': "Actions",
        'admin_label_current_file': "Current file",
        'admin_label_comment': "Comment",
        'admin_btn_apply': "Apply",
        'admin_btn_reset': "Reset",
        'admin_btn_edit': "Edit",
        'admin_btn_save_changes': "Save changes",
        'admin_btn_cancel': "Cancel",
        'admin_btn_view': "View",
        'admin_btn_view_current_file': "View file",
        'admin_msg_no_file': "No file",
        'admin_msg_file_not_uploaded': "File not uploaded",
        'admin_msg_error_saving': "Save error",
        'admin_msg_unknown_error': "Unknown error",
        'admin_msg_request_error': "Request error",
        'admin_pagination_showing': "Showing",
        'admin_pagination_of': "of",
        'admin_pagination_entries': "entries",
    },
}

def init_translations(db_connector):
    """Initialize the translation module with a database connector."""
    global dbc
    dbc = db_connector


def _translation_is_usable(value, key):
    if value is None:
        return False

    normalized = str(value).strip()
    if not normalized:
        return False

    lowered = normalized.lower()
    placeholders = {
        str(key).strip().lower(),
        str(key).replace('_', ' ').strip().lower(),
        str(key).replace('_', '-').strip().lower(),
    }
    return lowered not in placeholders


def _humanize_translation_key(key):
    acronyms = {
        'api': 'API',
        'doi': 'DOI',
        'eissn': 'E-ISSN',
        'en': 'EN',
        'id': 'ID',
        'issn': 'ISSN',
        'orcid': 'ORCID',
        'pdf': 'PDF',
        'ru': 'RU',
        'uz': 'UZ',
    }
    tokens = [token for token in str(key).split('_') if token]
    if tokens and tokens[0].lower() == 'admin':
        tokens = tokens[1:]
    pretty = [acronyms.get(token.lower(), token.capitalize()) for token in tokens]
    return ' '.join(pretty) if pretty else str(key)

def _load_translations_from_db():
    """Loads translations from the database with caching."""
    global _translations_cache, _cache_timestamp

    current_time = time.time()

    # Check if cache needs update
    if current_time - _cache_timestamp > _cache_ttl or not _translations_cache:
        try:
            if not dbc:
                return _get_fallback_translations()

            # Load all translations from DB
            translations = dbc.translations.all().exec()

            # Organize by language
            _translations_cache = {
                'en': {},
                'ru': {},
                'uz': {}
            }

            for trans in translations:
                alias = trans['alias']
                _translations_cache['en'][alias] = trans.get('content', '')
                _translations_cache['ru'][alias] = trans.get('content_ru', '')
                _translations_cache['uz'][alias] = trans.get('content_uz', '')

            _cache_timestamp = current_time

        except Exception as e:
            print(f"Error loading translations from DB: {e}")
            if not _translations_cache:
                _translations_cache = _get_fallback_translations()

    return _translations_cache

def _get_fallback_translations():
    """Returns fallback translations."""
    return {
        'en': {'admin_home': 'Home', 'admin_users': 'Users'},
        'ru': {'admin_home': 'Главная', 'admin_users': 'Пользователи'},
        'uz': {'admin_home': 'Bosh sahifa', 'admin_users': 'Foydalanuvchilar'}
    }

def translate(data):
    """Translates object fields based on current language."""
    current_lang = session.get('language', 'ru') # Default to RU for Admin if not set
    if current_lang == 'en':
        return data

    fields = list(data.keys())
    keys_to_delete = []

    for field in fields:
        if field.endswith('_uz') or field.endswith('_ru'):
            keys_to_delete.append(field)
            continue

        if current_lang == 'uz':
            if f'{field}_uz' in data:
                localized_value = data.get(f'{field}_uz')
                data[field] = '' if localized_value is None else localized_value
                keys_to_delete.append(f'{field}_uz')
        elif current_lang == 'ru':
            if f'{field}_ru' in data:
                localized_value = data.get(f'{field}_ru')
                data[field] = '' if localized_value is None else localized_value
                keys_to_delete.append(f'{field}_ru')

        if current_lang != 'uz' and f'{field}_uz' in data:
            keys_to_delete.append(f'{field}_uz')
        if current_lang != 'ru' and f'{field}_ru' in data:
            keys_to_delete.append(f'{field}_ru')

    for key in keys_to_delete:
        if key in data:
            del data[key]

    return data

def t(key):
    """Returns translation for a key in the current language."""
    current_lang = session.get('language', 'ru') # Default to RU

    translations_cache = _load_translations_from_db()

    if current_lang in translations_cache and key in translations_cache[current_lang]:
        val = translations_cache[current_lang][key]
        if _translation_is_usable(val, key):
            return val

    static_lang = STATIC_TRANSLATIONS.get(current_lang, {})
    if key in static_lang and _translation_is_usable(static_lang[key], key):
        return static_lang[key]

    # Fallback to English (or Russian since this is admin panel)
    # Actually fallback to 'ru' might be better if original keys are english?
    # Usually keys are english aliases.
    if key in translations_cache.get('ru', {}):
        val = translations_cache['ru'][key]
        if _translation_is_usable(val, key):
            return val

    static_ru = STATIC_TRANSLATIONS.get('ru', {})
    if key in static_ru and _translation_is_usable(static_ru[key], key):
        return static_ru[key]

    if key in translations_cache.get('en', {}):
        val = translations_cache['en'][key]
        if _translation_is_usable(val, key):
            return val

    static_en = STATIC_TRANSLATIONS.get('en', {})
    if key in static_en and _translation_is_usable(static_en[key], key):
        return static_en[key]
       
    # Auto-add missing keys
    if dbc and key not in translations_cache.get('en', {}):
        try:
            dbc.translations.add(
                alias=key,
                content=key, # Default EN
                content_ru=key, # Default RU
                content_uz=key, # Default UZ
                created_at=int(time.time())
            ).exec()
            
            # Update cache locally to avoid immediate re-fetch
            if 'en' not in translations_cache: translations_cache['en'] = {}
            if 'ru' not in translations_cache: translations_cache['ru'] = {}
            if 'uz' not in translations_cache: translations_cache['uz'] = {}
            translations_cache['en'][key] = key
            translations_cache['ru'][key] = key
            translations_cache['uz'][key] = key
            
            print(f"Added new translation alias: {key}")
        except Exception as e:
            print(f"Error adding translation alias {key}: {e}")

    return _humanize_translation_key(key)

def clear_translations_cache():
    global _translations_cache, _cache_timestamp
    _translations_cache = {}
    _cache_timestamp = 0
