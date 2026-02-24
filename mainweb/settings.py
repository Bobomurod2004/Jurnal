import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '1')
DB_NAME = os.getenv('DB_NAME', 'journal2')

# File storage
SAVE_PATH = os.getenv('SAVE_PATH', '/var/www/journal/')

# Secret key
SECRET_KEY = os.getenv('SECRET_KEY', 'd2c9cb10-0d85-432d-8c01-d9b0303dedb8')
