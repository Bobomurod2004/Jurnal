"""
Database Migration System for Philology Matters
This provides Django-like migration functionality for the Flask application.
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations similar to Django's migrate command.
    """
    
    def __init__(self, host=None, port=None, user=None, password=None, database=None):
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', '')
        self.database = database or os.getenv('DB_NAME', 'journal')
        self.migrations_dir = os.path.join(os.path.dirname(__file__), 'versions')
        
        # Ensure migrations directory exists
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        # Ensure migration tracking table exists
        self._ensure_migration_table()
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
    
    def _ensure_migration_table(self):
        """Create migration tracking table if not exists"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS _schema_migrations (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(255) UNIQUE NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)
                conn.commit()
        finally:
            conn.close()
    
    def get_applied_migrations(self):
        """Get list of already applied migrations"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version FROM _schema_migrations ORDER BY version")
                return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_available_migrations(self):
        """Get list of available migration files"""
        if not os.path.exists(self.migrations_dir):
            return []
        
        migrations = []
        for filename in sorted(os.listdir(self.migrations_dir)):
            if filename.endswith('.sql'):
                version = filename.replace('.sql', '')
                migrations.append(version)
        return migrations
    
    def migrate(self, target=None):
        """
        Apply pending migrations.
        
        Args:
            target: Specific version to migrate to (None = latest)
        """
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        
        pending = [m for m in available if m not in applied]
        
        if target:
            pending = [m for m in pending if m <= target]
        
        if not pending:
            logger.info("No pending migrations")
            return
        
        logger.info(f"Applying {len(pending)} migration(s)...")
        
        for version in pending:
            self._apply_migration(version)
        
        logger.info("Migrations complete!")
    
    def _apply_migration(self, version):
        """Apply a single migration"""
        migration_file = os.path.join(self.migrations_dir, f"{version}.sql")
        
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return
        
        logger.info(f"Applying migration: {version}")
        
        # Read migration SQL
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute migration
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Execute migration as a single script.
                # This preserves PostgreSQL blocks like DO $$ ... $$ that contain semicolons.
                cursor.execute(sql)
                
                # Record migration
                cursor.execute(
                    "INSERT INTO _schema_migrations (version, description) VALUES (%s, %s)",
                    (version, f"Applied migration {version}")
                )
                
                conn.commit()
                logger.info(f"Migration {version} applied successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply migration {version}: {e}")
            raise
        finally:
            conn.close()
    
    def create_migration(self, name):
        """
        Create a new migration file.
        
        Args:
            name: Descriptive name for the migration
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = f"{timestamp}_{name}"
        
        filename = os.path.join(self.migrations_dir, f"{version}.sql")
        
        template = f"""-- Migration: {version}
-- Created: {datetime.now().isoformat()}
-- Description: {name}

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Example:
-- ALTER TABLE users ADD COLUMN new_field VARCHAR(255);

"""
        
        with open(filename, 'w') as f:
            f.write(template)
        
        logger.info(f"Created migration: {filename}")
        return version
    
    def show_status(self):
        """Show migration status"""
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        
        print("\nMigration Status:")
        print("-" * 50)
        
        for version in available:
            status = "[X] Applied" if version in applied else "[ ] Pending"
            print(f"{status} - {version}")
        
        if not available:
            print("No migrations found")
        
        print()


def main():
    """CLI interface for migrations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Manager')
    parser.add_argument('command', choices=['migrate', 'makemigrations', 'status'])
    parser.add_argument('--name', help='Migration name (for makemigrations)')
    parser.add_argument('--target', help='Target version (for migrate)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    manager = MigrationManager()
    
    if args.command == 'migrate':
        manager.migrate(target=args.target)
    elif args.command == 'makemigrations':
        if not args.name:
            print("Error: --name is required for makemigrations")
            sys.exit(1)
        manager.create_migration(args.name)
    elif args.command == 'status':
        manager.show_status()


if __name__ == '__main__':
    main()
