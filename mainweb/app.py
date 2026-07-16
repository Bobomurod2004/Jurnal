# flake8: noqa
import os
import sys
import logging
from flask import Flask, jsonify
from flasgger import Swagger
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.observability import (
    attach_metrics_and_health,
    bootstrap_telemetry_libraries,
    configure_logging,
    configure_tracing,
    legacy_postgres_healthcheck,
)

bootstrap_telemetry_libraries()

try:
    import mainweb.settings as settings
except ImportError:
    import settings
import hooks
from extensions import dbc
from utils.filters import register_filters
from utils.uploads import init_uploads
from routes import auth, public, dashboard, api, context

logger = logging.getLogger(__name__)


def _migrate_legacy_password_hashes():
    try:
        users = dbc.users.get().exec()
    except Exception:
        logger.exception('Unable to inspect existing mainweb users for password migration')
        return

    migrated = 0
    for user in users:
        stored_password = user.get('password')
        if not stored_password or not isinstance(stored_password, str):
            continue
        if stored_password.startswith(('pbkdf2:', 'scrypt:')):
            continue
        try:
            dbc.users.get(id=user['id']).update(
                password=generate_password_hash(stored_password)
            ).exec()
            migrated += 1
        except Exception:
            logger.exception('Failed to migrate password hash for user_id=%s', user.get('id'))

    if migrated:
        logger.warning('Migrated %s legacy plaintext password(s) in mainweb', migrated)


def create_app():
    app = Flask(__name__)
    configure_logging(
        app,
        service_name='mainweb',
        version=settings.APP_VERSION,
        level_name=settings.LOG_LEVEL,
    )
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    app.secret_key = settings.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

    # Session security
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = bool(settings.IS_PRODUCTION)
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

    attach_metrics_and_health(
        app,
        service_name='mainweb',
        version=settings.APP_VERSION,
        db_healthcheck=lambda: legacy_postgres_healthcheck(dbc),
    )
    configure_tracing(app, service_name='mainweb', version=settings.APP_VERSION)

    @app.get('/healthz')
    def healthz():
        return jsonify({'status': 'ok', 'service': 'mainweb', 'version': settings.APP_VERSION}), 200

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Philology Matters Journal API",
            "description": "API documentation for journal management system. **Note:** Most endpoints require authentication. Please login first at `/login` endpoint.",
            "version": "1.0.1",
            "contact": {
                "name": "API Support",
                "email": "support@journal.com"
            }
        },
        "host": os.getenv('APP_HOST', 'localhost:8080'),
        "basePath": "/",
        "schemes": ["https", "http"],
        "securityDefinitions": {
            "SessionAuth": {
                "type": "apiKey",
                "name": "session",
                "in": "cookie",
                "description": "Session-based authentication. Login first at /login with email and password."
            }
        },
        "tags": [
            {"name": "Authors", "description": "Author management endpoints"},
            {"name": "Articles", "description": "Article submission and management"},
            {"name": "Payments", "description": "Payment and subscription management"},
            {"name": "Utilities", "description": "Utility endpoints"}
        ]
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    init_uploads(app)
    register_filters(app)
    hooks.register(app)
    context.register_context_processors(app)
    auth.run_runtime_schema_syncs()
    api.run_runtime_schema_syncs()
    _migrate_legacy_password_hashes()

    auth.register(app)
    public.register(app)
    dashboard.register(app)
    api.register(app)

    return app
