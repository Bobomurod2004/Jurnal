import os
from flask import Flask
import settings
from extensions import db
from modules.translate import init_translations
from hooks import register as register_hooks
from utils.filters import register_filters
from routes import api, web


def create_app():
    app = Flask(__name__, static_folder='./dist/', static_url_path='/dist')
    app.secret_key = settings.SECRET_KEY
    app.config['SESSION_COOKIE_NAME'] = 'fmadmin_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400

    init_translations(db)
    register_hooks(app)
    register_filters(app)

    web.register(app)
    api.register(app)

    return app
