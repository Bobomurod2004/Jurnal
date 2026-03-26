import argparse
import datetime
import secrets
import sys
import os

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from extensions import db


def parse_args():
    parser = argparse.ArgumentParser(description='Create or update fmadmin super admin user')
    parser.add_argument('--email', default=os.getenv('SUPERADMIN_EMAIL', 'admin@fmadmin.uz'))
    parser.add_argument('--name', default=os.getenv('SUPERADMIN_NAME', 'Super Admin'))
    parser.add_argument('--password', default=os.getenv('SUPERADMIN_PASSWORD'))
    return parser.parse_args()


def main():
    args = parse_args()
    password = args.password or secrets.token_urlsafe(18)
    hashed_password = generate_password_hash(password)

    print(f"Creating/updating super admin: {args.email}")

    conn = db.conn
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS roles TEXT[]")
        cur.execute("SELECT id FROM users WHERE email = %s", (args.email,))
        user = cur.fetchone()

        if user:
            cur.execute(
                """
                UPDATE users
                   SET name = %s,
                       password = %s,
                       rolename = %s,
                       roles = %s,
                       is_blocked = %s,
                       updated_at = %s
                 WHERE email = %s
                """,
                (args.name, hashed_password, 'superadmin', ['superadmin'], False, int(datetime.datetime.now().timestamp()), args.email),
            )
            print("Existing user updated.")
        else:
            now = int(datetime.datetime.now().timestamp())
            cur.execute(
                """
                INSERT INTO users (name, email, password, rolename, roles, is_blocked, is_notify, created_at, register_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (args.name, args.email, hashed_password, 'superadmin', ['superadmin'], False, True, now, now),
            )
            print("New super admin created.")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    print("Success: super admin is ready.")
    print(f"Login: {args.email}")
    if args.password:
        print("Password source: provided via CLI/ENV")
    else:
        print("Password source: auto-generated for this run")
    print(f"Password: {password}")


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}")
        raise
