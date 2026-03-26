import os

# Disable DB init for unit tests.
os.environ.setdefault('SKIP_DB_INIT', '1')
os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('APP_VERSION', 'test')
