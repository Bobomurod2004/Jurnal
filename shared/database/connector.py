"""
Enhanced PostgreSQL Database Connector with Connection Pooling and Transaction Support
This replaces the old custom connector with proper connection management.
"""

import os
import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    Thread-safe database connector with connection pooling.
    Replaces the old PostgreSQLConnector with proper connection management.
    """
    
    _instance = None
    _connection_pool = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure single connection pool"""
        if cls._instance is None:
            cls._instance = super(DatabaseConnector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, host: str = None, port: int = None, user: str = None, 
                 password: str = None, database: str = None, 
                 min_connections: int = 1, max_connections: int = 20):
        """
        Initialize the database connector with connection pooling.
        
        Args:
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        if self._initialized:
            return
            
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', '')
        self.database = database or os.getenv('DB_NAME', 'journal')
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        self._init_pool()
        self._initialized = True
        logger.info(f"Database connector initialized with pool (min={min_connections}, max={max_connections})")
    
    def _init_pool(self):
        """Initialize the connection pool"""
        try:
            self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursor_factory=RealDictCursor
            )
            logger.info("Connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Automatically returns connection to pool after use.
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        conn = None
        try:
            conn = self._connection_pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                self._connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        """
        Context manager for database cursors.
        
        Args:
            commit: Whether to commit after the operation
        
        Usage:
            with db.get_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO users ...")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database query error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute(self, query: str, params: Tuple = None, fetch: bool = False) -> Optional[List[Dict]]:
        """
        Execute a SQL query with proper parameterization.
        
        Args:
            query: SQL query string (use %s for parameters)
            params: Query parameters (tuple)
            fetch: Whether to fetch results
            
        Returns:
            List of dictionaries if fetch=True, None otherwise
        """
        with self.get_cursor(commit=not fetch) as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def fetch_one(self, query: str, params: Tuple = None) -> Optional[Dict]:
        """Fetch a single row"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: Tuple = None) -> List[Dict]:
        """Fetch all rows"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def insert(self, table: str, data: Dict[str, Any], returning: str = 'id') -> Any:
        """
        Insert a row and return the specified column value.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
            returning: Column to return (default: 'id')
            
        Returns:
            The value of the returning column
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['%s'] * len(columns))
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, values)
            if returning:
                result = cursor.fetchone()
                return result[returning] if result else None
            return None
    
    def update(self, table: str, data: Dict[str, Any], where: str, 
               where_params: Tuple = None) -> int:
        """
        Update rows and return affected row count.
        
        Args:
            table: Table name
            data: Dictionary of column names and values to update
            where: WHERE clause (use %s for parameters)
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of affected rows
        """
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        values = list(data.values())
        if where_params:
            values.extend(where_params)
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, values)
            return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: Tuple = None) -> int:
        """
        Delete rows and return affected row count.
        
        Args:
            table: Table name
            where: WHERE clause (use %s for parameters)
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of deleted rows
        """
        query = f"DELETE FROM {table} WHERE {where}"
        
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, where_params)
            return cursor.rowcount
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def close_all(self):
        """Close all connections in the pool"""
        if self._connection_pool:
            self._connection_pool.closeall()
            logger.info("All database connections closed")


# Global instance
db = None


def init_db(host: str = None, port: int = None, user: str = None, 
            password: str = None, database: str = None):
    """Initialize the global database connector"""
    global db
    db = DatabaseConnector(host, port, user, password, database)
    return db


def get_db() -> DatabaseConnector:
    """Get the global database connector instance"""
    global db
    if db is None:
        db = DatabaseConnector()
    return db


@contextmanager
def transaction():
    """
    Context manager for database transactions.
    Automatically commits on success, rolls back on exception.
    
    Usage:
        with transaction():
            db.insert('users', {'email': 'test@test.com'})
            db.insert('profiles', {'user_id': 1})
    """
    conn = None
    try:
        conn = get_db()._connection_pool.getconn()
        yield conn
        conn.commit()
        logger.debug("Transaction committed")
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise
    finally:
        if conn:
            get_db()._connection_pool.putconn(conn)


# Backward compatibility with old connector
class PostgreSQLConnector(DatabaseConnector):
    """
    Backward-compatible wrapper for the old PostgreSQLConnector.
    Allows gradual migration from old code.
    """
    
    def __init__(self, host: str = None, port: int = None, user: str = None, 
                 password: str = None, database: str = None):
        super().__init__(host, port, user, password, database)
        self.conn = None
        self.columns = {}
        self.primary_columns = {}
        self._load_schema()
    
    def _load_schema(self):
        """Load table schema for backward compatibility"""
        try:
            with self.get_cursor() as cursor:
                # Load columns
                cursor.execute("""
                    SELECT table_name, column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public'
                """)
                for row in cursor.fetchall():
                    table = row['table_name']
                    column = row['column_name']
                    if table not in self.columns:
                        self.columns[table] = []
                    self.columns[table].append(column)
                
                # Load primary keys
                cursor.execute("""
                    SELECT tc.table_name, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
                """)
                for row in cursor.fetchall():
                    self.primary_columns[row['table_name']] = row['column_name']
                    
        except Exception as e:
            logger.warning(f"Could not load schema: {e}")
    
    def __call__(self, tablename: str):
        """Backward compatibility: dbc('table_name')"""
        from .legacy_query import LegacyQuery
        return LegacyQuery(self, tablename)
    
    def _connect(self):
        """Backward compatibility - no-op since we use pooling"""
        pass
    
    def close(self):
        """Backward compatibility"""
        pass
