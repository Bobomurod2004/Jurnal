# flake8: noqa
import time
from flask import session

# Global DB connector instance
dbc = None

# Translations cache
_translations_cache = {}
_cache_timestamp = 0
_cache_ttl = 300  # 5 minutes

def init_translations(db_connector):
    """Initialize the translation module with a database connector."""
    global dbc
    dbc = db_connector

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
                data[field] = data.get(f'{field}_uz') or data.get(field) or ''
                keys_to_delete.append(f'{field}_uz')
        elif current_lang == 'ru':
            if f'{field}_ru' in data:
                data[field] = data.get(f'{field}_ru') or data.get(field) or ''
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
        if val: return val

    # Fallback to English (or Russian since this is admin panel)
    # Actually fallback to 'ru' might be better if original keys are english?
    # Usually keys are english aliases.
    if key in translations_cache.get('ru', {}):
       val = translations_cache['ru'][key]
       if val: return val
       
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

    return key

def clear_translations_cache():
    global _translations_cache, _cache_timestamp
    _translations_cache = {}
    _cache_timestamp = 0
