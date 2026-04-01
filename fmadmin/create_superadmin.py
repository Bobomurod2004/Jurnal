import argparse
import datetime
import secrets
import sys
import os

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from extensions import db


def _fetch_users_columns(cur):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users'
        """
    )
    return {row[0] for row in cur.fetchall()}


def _filter_existing_columns(payload, existing_columns):
    return {key: value for key, value in payload.items() if key in existing_columns}


def _execute_update(cur, table_name, payload, where_clause, where_params):
    if not payload:
        return
    set_clause = ", ".join([f"{column} = %s" for column in payload.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
    params = list(payload.values()) + list(where_params)
    cur.execute(query, params)


def _execute_insert(cur, table_name, payload):
    if not payload:
        raise ValueError(f"{table_name} insert payload is empty")
    columns = list(payload.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    cur.execute(query, [payload[column] for column in columns])


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
        columns = _fetch_users_columns(cur)
        if 'roles' not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS roles TEXT[]")
            columns = _fetch_users_columns(cur)

        cur.execute("SELECT id FROM users WHERE email = %s", (args.email,))
        user = cur.fetchone()
        now_ts = int(datetime.datetime.now().timestamp())

        common_payload = {
            'name': args.name,
            'password': hashed_password,
            'rolename': 'superadmin',
            'roles': ['superadmin'],
            'is_blocked': False,
            'is_notify': True,
            'last_online': now_ts,
        }

        if user:
            update_payload = dict(common_payload)
            if 'updated_at' in columns:
                update_payload['updated_at'] = now_ts
            update_payload = _filter_existing_columns(update_payload, columns)
            _execute_update(cur, 'users', update_payload, "email = %s", (args.email,))
            print("Existing user updated.")
        else:
            insert_payload = {
                'name': args.name,
                'email': args.email,
                'password': hashed_password,
                'rolename': 'superadmin',
                'roles': ['superadmin'],
                'is_blocked': False,
                'is_notify': True,
                'created_at': now_ts,
                'register_time': now_ts,
                'last_online': now_ts,
            }
            insert_payload = _filter_existing_columns(insert_payload, columns)
            _execute_insert(cur, 'users', insert_payload)
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
