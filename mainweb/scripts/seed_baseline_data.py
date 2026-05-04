#!/usr/bin/env python3
import argparse
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAINWEB_DIR = os.path.dirname(SCRIPT_DIR)
if MAINWEB_DIR not in sys.path:
    sys.path.append(MAINWEB_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from modules.connector import PostgreSQLConnector
from add_all_countries import seed_countries
from add_all_classifications import seed_classifications


ISSUE_CATEGORIES = [
    {
        'alias': 'masters',
        'name': "Series: Master's",
        'name_uz': 'Seriya: Magistratura',
        'name_ru': 'Серия: Магистратура',
    },
    {
        'alias': 'phd',
        'name': 'Series: Doctoral',
        'name_uz': 'Seriya: Doktorantura',
        'name_ru': 'Серия: Докторантура',
    },
    {
        'alias': 'teacher',
        'name': 'Series: Professors & Teachers',
        'name_uz': "Seriya: Professor-o'qituvchilar",
        'name_ru': 'Серия: Профессора-преподаватели',
    },
    {
        'alias': 'special',
        'name': 'Special Issue',
        'name_uz': 'Maxsus son',
        'name_ru': 'Специальный выпуск',
    },
]


DEFAULT_TARIFFS = [
    {
        'name': 'Basic',
        'name_uz': 'Asosiy',
        'name_ru': 'Базовый',
        'description': 'Basic subscription for readers',
        'description_uz': "O'quvchilar uchun asosiy obuna",
        'description_ru': 'Базовая подписка для читателей',
        'price_usd': 0.0,
        'price_uzs': 0.0,
        'price_rub': 0.0,
        'user_limit': 100,
        'is_default': True,
        'is_verified': False,
        'duration_days': 30,
    },
    {
        'name': 'Premium',
        'name_uz': 'Premium',
        'name_ru': 'Премиум',
        'description': 'Premium subscription with full access',
        'description_uz': "To'liq kirish bilan premium obuna",
        'description_ru': 'Премиальная подписка с полным доступом',
        'price_usd': 5.5,
        'price_uzs': 75000.0,
        'price_rub': 500.0,
        'user_limit': 50,
        'is_default': False,
        'is_verified': False,
        'duration_days': 30,
    },
]


def _build_connector():
    return PostgreSQLConnector(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', '5432')),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '1'),
        database=os.getenv('DB_NAME', 'journal2'),
    )


def _refresh_schema_cache(dbc):
    dbc.tables = []
    dbc.columns = {}
    dbc.primary_columns = {}
    dbc._init_tables()
    dbc._init_columns()


def _table_row_count(dbc, table_name):
    try:
        return int(getattr(dbc, table_name).count().exec() or 0)
    except Exception:
        return 0


def _ensure_tariff_duration_column(dbc):
    if 'duration_days' in set(dbc.columns.get('tariffs', [])):
        return

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS duration_days integer DEFAULT 30;")
        dbc.conn.commit()
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        raise
    finally:
        if cursor is not None:
            cursor.close()

    _refresh_schema_cache(dbc)


def seed_issue_categories(dbc, replace=False):
    existing_count = _table_row_count(dbc, 'fix_issue_categories')
    if existing_count > 0 and not replace:
        print(f"fix_issue_categories already has {existing_count} rows. Skipping issue category seed.")
        return existing_count

    if replace and existing_count > 0:
        print("Clearing existing issue categories...")
        dbc.fix_issue_categories.get().delete().exec()

    print("Adding issue categories...")
    for item in ISSUE_CATEGORIES:
        dbc.fix_issue_categories.add(
            alias=item['alias'],
            name=item['name'],
            name_uz=item['name_uz'],
            name_ru=item['name_ru'],
        ).exec()

    count = _table_row_count(dbc, 'fix_issue_categories')
    print(f"Issue category seed complete. Total rows: {count}")
    return count


def seed_tariffs(dbc, replace=False):
    _ensure_tariff_duration_column(dbc)

    existing_count = _table_row_count(dbc, 'tariffs')
    if existing_count > 0 and not replace:
        print(f"tariffs already has {existing_count} rows. Skipping tariff seed.")
        return existing_count

    if replace and existing_count > 0:
        print("Clearing existing tariffs...")
        dbc.tariffs.get().delete().exec()

    print("Adding default tariffs...")
    now_ts = int(time.time())
    available_columns = set(dbc.columns.get('tariffs', []))
    for tariff in DEFAULT_TARIFFS:
        payload = dict(tariff)
        payload['created_at'] = now_ts
        payload['updated_at'] = now_ts

        # Keep inserts compatible with both old and upgraded schema.
        payload = {k: v for k, v in payload.items() if k in available_columns}
        dbc.tariffs.add(**payload).exec()

    count = _table_row_count(dbc, 'tariffs')
    print(f"Tariff seed complete. Total rows: {count}")
    return count


def _parse_args():
    parser = argparse.ArgumentParser(description='Seed baseline database data')
    parser.add_argument(
        '--replace',
        action='store_true',
        help='Delete existing rows in seeded tables before inserting baseline data',
    )
    parser.add_argument('--skip-countries', action='store_true', help='Skip fix_country seed')
    parser.add_argument('--skip-classifications', action='store_true', help='Skip fix_classifications seed')
    parser.add_argument('--skip-issue-categories', action='store_true', help='Skip fix_issue_categories seed')
    parser.add_argument('--skip-tariffs', action='store_true', help='Skip tariffs seed')
    return parser.parse_args()


def main():
    args = _parse_args()
    dbc = _build_connector()

    if not args.skip_countries:
        seed_countries(dbc, replace=args.replace)
    if not args.skip_classifications:
        seed_classifications(dbc, replace=args.replace)
    if not args.skip_issue_categories:
        seed_issue_categories(dbc, replace=args.replace)
    if not args.skip_tariffs:
        seed_tariffs(dbc, replace=args.replace)

    print("Baseline seed finished.")


if __name__ == '__main__':
    main()
