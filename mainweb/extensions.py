"""
Flask extensions initialization with improved database connector.
"""
import sys
import os

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.connector import PostgreSQLConnector
try:
    import mainweb.settings as settings
except ImportError:
    import settings

# Initialize database connector with connection pooling
dbc = PostgreSQLConnector(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME,
)
