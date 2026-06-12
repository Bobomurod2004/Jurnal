import os

from app import create_app

app = create_app()
# Trigger Gunicorn reload



def _env_flag(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {'1', 'true', 'yes', 'on'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=_env_flag('FLASK_DEBUG'))
