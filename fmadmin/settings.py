import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

FLASK_ENV = os.getenv('FLASK_ENV', '').strip().lower()
IS_PRODUCTION = FLASK_ENV == 'production'


def _get_env(name, default=None, production_required=False):
    value = os.getenv(name)
    if value is not None and str(value).strip() != '':
        return value
    if production_required and IS_PRODUCTION:
        raise RuntimeError(f'{name} environment variable must be set in production')
    return default


def _get_env_bool(name, default=False):
    value = os.getenv(name)
    if value is None or str(value).strip() == '':
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _get_env_list(name, default=None):
    value = os.getenv(name)
    if value is None or str(value).strip() == '':
        return list(default or [])
    return [item.strip() for item in str(value).split(',') if item.strip()]


DB_HOST = _get_env('DB_HOST', '127.0.0.1')
DB_PORT = _get_env('DB_PORT', '5432')
DB_USER = _get_env('DB_USER', 'postgres')
DB_PASSWORD = _get_env('DB_PASSWORD', '1', production_required=True)
DB_NAME = _get_env('DB_NAME', 'journal2')
APP_HOST = _get_env('APP_HOST', 'localhost:8080')

SAVE_PATH = _get_env('SAVE_PATH', '/var/www/journal/')
SECRET_KEY = (
    _get_env('FMADMIN_SECRET_KEY')
    or _get_env('SECRET_KEY', production_required=True)
    or 'dev-fmadmin-secret-key-change-me'
)
MAINWEB_INTERNAL_URL = _get_env(
    'MAINWEB_INTERNAL_URL',
    _get_env('MAINWEB_URL', 'http://mainweb:5000')
).rstrip('/')
_sync_default = 'local-translation-sync-token' if not IS_PRODUCTION else SECRET_KEY
TRANSLATION_SYNC_TOKEN = os.getenv(
    'TRANSLATION_SYNC_TOKEN',
    _sync_default
)

APP_BASE_URL = _get_env(
    'APP_BASE_URL',
    f"{'https' if IS_PRODUCTION else 'http'}://{APP_HOST}"
).rstrip('/')

APP_VERSION = _get_env('APP_VERSION', '0.0.0')
LOG_LEVEL = _get_env('LOG_LEVEL', 'INFO')
RUNTIME_SCHEMA_SYNC_ENABLED = _get_env_bool('RUNTIME_SCHEMA_SYNC_ENABLED', not IS_PRODUCTION)


def _ensure_production_secret(name, value, disallowed):
    if not IS_PRODUCTION:
        return
    normalized = str(value or '').strip()
    if not normalized:
        raise RuntimeError(f'{name} environment variable must be set in production')
    if normalized in disallowed:
        raise RuntimeError(f'{name} uses an insecure default value in production; set a strong unique value')


_ensure_production_secret(
    'DB_PASSWORD',
    DB_PASSWORD,
    {'1', 'postgres', 'password', 'change-this-db-password'},
)
_ensure_production_secret(
    'SECRET_KEY',
    SECRET_KEY,
    {'dev-fmadmin-secret-key-change-me', 'change-this-fmadmin-secret'},
)
_ensure_production_secret(
    'TRANSLATION_SYNC_TOKEN',
    TRANSLATION_SYNC_TOKEN,
    {'local-translation-sync-token', 'change-this-sync-token'},
)

if IS_PRODUCTION and len(str(SECRET_KEY)) < 32:
    raise RuntimeError('SECRET_KEY must be at least 32 characters in production')
if IS_PRODUCTION and len(str(TRANSLATION_SYNC_TOKEN)) < 16:
    raise RuntimeError('TRANSLATION_SYNC_TOKEN must be at least 16 characters in production')
if IS_PRODUCTION and str(TRANSLATION_SYNC_TOKEN) == str(SECRET_KEY):
    raise RuntimeError('TRANSLATION_SYNC_TOKEN must differ from SECRET_KEY in production')

MAIL_ENABLED = _get_env_bool('MAIL_ENABLED', True)
MAIL_HOST = _get_env('MAIL_HOST', '')
MAIL_PORT = int(_get_env('MAIL_PORT', '587'))
MAIL_USERNAME = _get_env('MAIL_USERNAME', '')
MAIL_PASSWORD = _get_env('MAIL_PASSWORD', '')
MAIL_USE_TLS = _get_env_bool('MAIL_USE_TLS', True)
MAIL_USE_SSL = _get_env_bool('MAIL_USE_SSL', False)
MAIL_TIMEOUT = int(_get_env('MAIL_TIMEOUT', '15'))
MAIL_SUPPRESS_SEND = _get_env_bool('MAIL_SUPPRESS_SEND', False)
MAIL_FROM_EMAIL = _get_env('MAIL_FROM_EMAIL', 'philologymatters@uzswlu.uz')
MAIL_FROM_NAME = _get_env('MAIL_FROM_NAME', 'Philology Matters')
MAIL_REPLY_TO = _get_env('MAIL_REPLY_TO', MAIL_FROM_EMAIL)
MAIL_CONTACT_RECIPIENTS = _get_env_list(
    'MAIL_CONTACT_RECIPIENTS',
    ['philologymatters@uzswlu.uz', 'philolm.uz@gmail.com']
)
