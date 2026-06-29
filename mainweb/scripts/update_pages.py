"""Seed/update static pages in the database.

The page content itself lives under ``mainweb/content/pages/`` (one folder per
page with ``meta.json`` + ``content.<lang>.html``). This script only loads that
content via :func:`content.pages.load_pages` and writes it into the ``pages``
table.

Usage::

    python3 scripts/update_pages.py                 # create + overwrite all pages
    python3 scripts/update_pages.py --only-missing  # create missing pages only
"""
import argparse
import os
import sys
import time

# Add the parent directory (mainweb) to the Python path.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector
from content.pages import load_pages


def _env(name, default=''):
    value = os.environ.get(name, default)
    return default if value is None else value


DB_HOST = _env('DB_HOST', 'db')
DB_PORT = int(_env('DB_PORT', '5432'))
DB_USER = _env('DB_USER', 'postgres')
DB_PASSWORD = _env('DB_PASSWORD', '')
DB_NAME = _env('DB_NAME', 'journal2')

# Backwards-compatible alias for callers that imported the literal dict.
PAGES_DATA = load_pages()


def update_pages(only_missing=False):
    dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

    current_time = int(time.time())

    existing_pages = dbc.pages.get().exec()
    existing_aliases = {page['alias']: page for page in existing_pages} if existing_pages else {}

    for alias, page_data in PAGES_DATA.items():
        if alias in existing_aliases:
            if only_missing:
                print(f"Skipping existing page: {page_data['title']}")
                continue
            print(f"Updating page: {page_data['title']}")
            dbc.pages.get(alias=alias).update(
                title=page_data['title'],
                title_uz=page_data['title_uz'],
                title_ru=page_data['title_ru'],
                content=page_data['content'],
                content_uz=page_data['content_uz'],
                content_ru=page_data['content_ru'],
                last_update=current_time
            ).exec()
        else:
            print(f"Creating new page: {page_data['title']}")
            dbc.pages.add(
                alias=alias,
                title=page_data['title'],
                title_uz=page_data['title_uz'],
                title_ru=page_data['title_ru'],
                content=page_data['content'],
                content_uz=page_data['content_uz'],
                content_ru=page_data['content_ru'],
                last_update=current_time,
                created_at=current_time
            ).exec()

    print("All pages updated successfully!")


def _parse_args():
    parser = argparse.ArgumentParser(description='Seed/update static pages')
    parser.add_argument(
        '--only-missing',
        action='store_true',
        help='Create only missing pages and keep existing content untouched',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    update_pages(only_missing=args.only_missing)
