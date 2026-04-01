"""
Database migration utilities for Flask-Migrate.
Provides easy migration management similar to Django's migrate command.
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate as migrate_cmd, upgrade as upgrade_cmd

logger = logging.getLogger(__name__)

# Global instances
db = SQLAlchemy()
migrate = Migrate()


def init_migrations(app: Flask, db_instance: SQLAlchemy = None):
    """
    Initialize Flask-Migrate with the application.
    
    Args:
        app: Flask application instance
        db_instance: SQLAlchemy instance (optional, uses global if not provided)
    """
    global db, migrate
    
    if db_instance:
        db = db_instance
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    logger.info("Flask-Migrate initialized")


def get_database_url() -> str:
    """Build database URL from environment variables"""
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '')
    database = os.getenv('DB_NAME', 'journal')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def create_migration(app: Flask, message: str = None):
    """
    Create a new migration (like Django's makemigrations).
    
    Usage:
        create_migration(app, "add user table")
    """
    with app.app_context():
        migrate_cmd(message=message)
        logger.info(f"Migration created: {message}")


def apply_migrations(app: Flask):
    """
    Apply all pending migrations (like Django's migrate).
    
    Usage:
        apply_migrations(app)
    """
    with app.app_context():
        upgrade_cmd()
        logger.info("Migrations applied")


def init_migration_repo(app: Flask, directory: str = 'migrations'):
    """
    Initialize migration repository.
    Run this once at the beginning.
    
    Usage:
        init_migration_repo(app)
    """
    with app.app_context():
        init(directory=directory)
        logger.info(f"Migration repository initialized at {directory}")


# Convenience functions for CLI usage
def migrate(app: Flask, message: str = None):
    """Alias for create_migration"""
    create_migration(app, message)


def upgrade(app: Flask):
    """Alias for apply_migrations"""
    apply_migrations(app)
