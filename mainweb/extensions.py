from modules.connector import PostgreSQLConnector
import settings

dbc = PostgreSQLConnector(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME,
)
