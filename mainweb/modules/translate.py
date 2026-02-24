# flake8: noqa
from flask import session
from .connector import PostgreSQLConnector
from config import *
import time
import threading
try:
    from .translations import EN as STATIC_EN, RU as STATIC_RU, UZ as STATIC_UZ
except Exception:
    STATIC_EN, STATIC_RU, STATIC_UZ = {}, {}, {}

dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

# Кеш для переводов
_translations_cache = {}
_cache_timestamp = 0
_cache_ttl = 300  # 5 минут
_cache_lock = threading.Lock()  # Thread safety for cache

_static_translations = {
    'en': {k: v for k, v in STATIC_EN.items() if k != 'alias'},
    'ru': {k: v for k, v in STATIC_RU.items() if k != 'alias'},
    'uz': {k: v for k, v in STATIC_UZ.items() if k != 'alias'},
}

def _load_translations_from_db():
    """Загружает переводы из базы данных с кешированием"""
    global _translations_cache, _cache_timestamp

    current_time = time.time()

    # Thread-safe cache check and update
    with _cache_lock:
        # Проверяем, нужно ли обновить кеш
        if current_time - _cache_timestamp > _cache_ttl or not _translations_cache:
            try:
                # Загружаем все переводы из БД
                translations = dbc.translations.all().exec()

                # Организуем переводы по языкам
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
                print(f"Ошибка загрузки переводов из БД: {e}")
                # В случае ошибки используем fallback переводы
                if not _translations_cache:
                    _translations_cache = _get_fallback_translations()

        return _translations_cache

def _get_fallback_translations():
    """Возвращает базовые переводы в случае недоступности БД"""
    return {
        'en': {
            'website_title': 'Philology Matters',
            'login': 'Login',
            'register': 'Register',
            'my_articles': 'My Articles',
            'submit_article': 'Submit Article',
            'logout': 'Logout',
            'home': 'Home',
            'error': 'Error occurred'
        },
        'ru': {
            'website_title': 'Филологические задачи',
            'login': 'Вход',
            'register': 'Регистрация',
            'my_articles': 'Мои статьи',
            'submit_article': 'Подать статью',
            'logout': 'Выйти',
            'home': 'Главная',
            'error': 'Произошла ошибка'
        },
        'uz': {
            'website_title': 'Filologiya masalalari',
            'login': 'Kirish',
            'register': 'Ro\'yxatdan o\'tish',
            'my_articles': 'Mening maqolalarim',
            'submit_article': 'Maqola yuborish',
            'logout': 'Chiqish',
            'home': 'Bosh sahifa',
            'error': 'Xatolik yuz berdi'
        }
    }

def translate(data):
    """Переводит поля объекта на текущий язык"""
    current_lang = session.get('language', 'en')
    if current_lang == 'en':
        return data

    # Create a list of keys to avoid dictionary size change during iteration
    fields = list(data.keys())
    keys_to_delete = []

    for field in fields:
        # Skip if this is already a language-specific field
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

        # Always add unused language keys for deletion
        if current_lang != 'uz' and f'{field}_uz' in data:
            keys_to_delete.append(f'{field}_uz')
        if current_lang != 'ru' and f'{field}_ru' in data:
            keys_to_delete.append(f'{field}_ru')

    # Delete language-specific keys after iteration
    for key in keys_to_delete:
        if key in data:
            del data[key]

    return data

def t(key):
    """Возвращает перевод для ключа на текущем языке"""
    # Get current language from session, default to English
    current_lang = session.get('language', 'en')

    # Load translations from database
    translations_cache = _load_translations_from_db()

    # Get translation for current language
    if current_lang in translations_cache and key in translations_cache[current_lang]:
        translation = translations_cache[current_lang][key]
        if translation:  # Проверяем, что перевод не пустой
            return translation

    # Static fallback from local dictionaries for missing/incomplete DB entries
    static_lang = _static_translations.get(current_lang, {})
    if key in static_lang and static_lang[key]:
        return static_lang[key]

    # Fallback to English if translation not found
    if key in translations_cache['en']:
        translation = translations_cache['en'][key]
        if translation:
            return translation

    static_en = _static_translations.get('en', {})
    if key in static_en and static_en[key]:
        return static_en[key]

    # If key not found anywhere, add it to database with content=alias
    if key not in translations_cache['en']:
        try:
            # Add new translation with alias as content
            dbc.translations.add(
                alias=key,
                content=key,
                content_ru='',
                content_uz='',
                created_at=int(time.time())
            ).exec()
            
            # Update cache
            translations_cache['en'][key] = key
            translations_cache['ru'][key] = ''
            translations_cache['uz'][key] = ''
            
            print(f"Добавлен новый алиас перевода: {key}")
            
        except Exception as e:
            print(f"Ошибка добавления алиаса перевода {key}: {e}")

    # Return key itself if no translation found
    return key

def clear_translations_cache():
    """Очищает кеш переводов (для принудительного обновления)"""
    global _translations_cache, _cache_timestamp
    with _cache_lock:
        _translations_cache = {}
        _cache_timestamp = 0
        print(f"Translation cache cleared at {time.time()}")
