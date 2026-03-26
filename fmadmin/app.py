import os
import logging
from datetime import timedelta
from flask import Flask, jsonify
from werkzeug.security import generate_password_hash
import settings
from extensions import db
from modules.translate import init_translations
from hooks import register as register_hooks
from utils.filters import register_filters
from routes import api, web

logger = logging.getLogger(__name__)

def _configure_logging(app):
    level_name = (settings.LOG_LEVEL or 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    app.logger.handlers = []
    app.logger.addHandler(handler)
    app.logger.setLevel(level)
    app.logger.propagate = False


def _migrate_legacy_password_hashes():
    try:
        users = db.users.all().exec()
    except Exception:
        logger.exception('Unable to inspect existing fmadmin users for password migration')
        return

    migrated = 0
    for user in users:
        stored_password = user.get('password')
        if not stored_password or not isinstance(stored_password, str):
            continue
        if stored_password.startswith(('pbkdf2:', 'scrypt:')):
            continue
        try:
            db.users.all().equal(id=user['id']).update(
                password=generate_password_hash(stored_password)
            ).exec()
            migrated += 1
        except Exception:
            logger.exception('Failed to migrate fmadmin password hash for user_id=%s', user.get('id'))

    if migrated:
        logger.warning('Migrated %s legacy plaintext password(s) in fmadmin', migrated)


def create_app():
    app = Flask(__name__, static_folder='./dist/', static_url_path='/dist')
    _configure_logging(app)
    app.secret_key = settings.SECRET_KEY
    app.config['SESSION_COOKIE_NAME'] = 'fmadmin_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

    @app.get('/healthz')
    @app.get('/fmadmin/healthz')
    def healthz():
        return jsonify({'status': 'ok', 'service': 'fmadmin', 'version': settings.APP_VERSION}), 200

    init_translations(db)
    register_hooks(app)
    register_filters(app)
    _migrate_legacy_password_hashes()

    web.register(app)
    api.register(app)

    return app
