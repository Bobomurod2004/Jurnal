# flake8: noqa
import os
from flask import Flask
from flasgger import Swagger
import settings
from utils.filters import register_filters
from utils.uploads import init_uploads
from routes import auth, public, dashboard, api, context


def create_app():
    app = Flask(__name__)
    app.secret_key = settings.SECRET_KEY

    # Session security
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

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
            "version": "1.0.0",
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
    context.register_context_processors(app)

    auth.register(app)
    public.register(app)
    dashboard.register(app)
    api.register(app)

    return app
