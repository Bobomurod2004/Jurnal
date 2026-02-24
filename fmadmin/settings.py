import os
import secrets
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '1')
DB_NAME = os.getenv('DB_NAME', 'journal2')

SAVE_PATH = os.getenv('SAVE_PATH', '/var/www/journal/')
SECRET_KEY = os.getenv('FMADMIN_SECRET_KEY', secrets.token_hex(24))
