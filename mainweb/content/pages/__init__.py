"""Static page seed content.

Each page lives in its own folder so the HTML is easy to find and edit:

    <alias>/meta.json          -> {"title", "title_uz", "title_ru"}
    <alias>/content.en.html
    <alias>/content.uz.html
    <alias>/content.ru.html

`_order.txt` lists aliases in display order (one alias per line; `#` comments).

This package only holds the *initial* (seed) content. At runtime the public
site reads pages from the database (table ``pages``) and seeds a row from here
on first access, after which editors manage the content from fmadmin.

Use :func:`load_pages` to get an ordered dict keyed by alias. ``PAGES_DATA`` is
kept as a module-level alias for backwards compatibility with older imports.
"""
import json
import os
from functools import lru_cache

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ORDER_FILE = os.path.join(_BASE_DIR, '_order.txt')

_REQUIRED_FIELDS = (
    'title', 'title_uz', 'title_ru',
    'content', 'content_uz', 'content_ru',
)


def _read_html(folder, filename):
    try:
        with open(os.path.join(folder, filename), encoding='utf-8') as fh:
            return fh.read().strip()
    except FileNotFoundError:
        return ''


def _ordered_aliases():
    """Aliases from _order.txt first, then any unlisted page folder."""
    aliases = []
    if os.path.isfile(_ORDER_FILE):
        with open(_ORDER_FILE, encoding='utf-8') as fh:
            for line in fh:
                alias = line.strip()
                if alias and not alias.startswith('#'):
                    aliases.append(alias)

    for name in sorted(os.listdir(_BASE_DIR)):
        full = os.path.join(_BASE_DIR, name)
        if os.path.isdir(full) and not name.startswith('_') and name not in aliases:
            aliases.append(name)
    return aliases


@lru_cache(maxsize=1)
def load_pages():
    """Return an ordered dict: alias -> {title*, content*} built from disk."""
    pages = {}
    for alias in _ordered_aliases():
        folder = os.path.join(_BASE_DIR, alias)
        meta_path = os.path.join(folder, 'meta.json')
        if not os.path.isfile(meta_path):
            continue
        with open(meta_path, encoding='utf-8') as fh:
            meta = json.load(fh)
        pages[alias] = {
            'title': (meta.get('title') or '').strip(),
            'title_uz': (meta.get('title_uz') or '').strip(),
            'title_ru': (meta.get('title_ru') or '').strip(),
            'content': _read_html(folder, 'content.en.html'),
            'content_uz': _read_html(folder, 'content.uz.html'),
            'content_ru': _read_html(folder, 'content.ru.html'),
        }
    return pages


# Backwards-compatible alias for callers that imported the literal dict.
PAGES_DATA = load_pages()
