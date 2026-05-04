import os
import re
import time
from html import escape as html_escape
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse

from flask import url_for
from markupsafe import Markup

try:
    import mainweb.settings as settings
except ImportError:
    import settings

DEFAULT_ISSUE_COVER = 'uploads/issues/2025/07/db14cd28777c448b9a7079c568448f9b.jpg'
LOCAL_STATIC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

RICHTEXT_ALLOWED_TAGS = {
    'p', 'br', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'strong', 'b', 'em', 'i', 'u', 's',
    'ul', 'ol', 'li',
    'blockquote',
    'pre', 'code',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'figure', 'figcaption',
    'a', 'img',
}
RICHTEXT_VOID_TAGS = {'br', 'hr', 'img'}
RICHTEXT_STRIP_CONTENT_TAGS = {
    'script', 'style', 'iframe', 'object', 'embed', 'form',
    'input', 'button', 'textarea', 'select', 'option', 'svg', 'math',
}
RICHTEXT_ALLOWED_PROTOCOLS = {'http', 'https', 'mailto', 'tel'}
RICHTEXT_ALLOWED_ATTRS = {
    '*': {'title'},
    'a': {'href', 'target', 'rel'},
    'img': {'src', 'alt', 'width', 'height', 'loading'},
    'th': {'colspan', 'rowspan'},
    'td': {'colspan', 'rowspan'},
    'ol': {'start'},
    'blockquote': {'cite'},
}


def _clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _static_url(path):
    if not path:
        return url_for('static', filename=DEFAULT_ISSUE_COVER)
    if path.startswith('/static/'):
        return path
    return url_for('static', filename=path.lstrip('/'))


def _public_static_path_exists(public_path):
    if not public_path or not public_path.startswith('/static/'):
        return False

    normalized_path = public_path.lstrip('/')
    candidate_paths = [os.path.join(settings.SAVE_PATH, normalized_path)]

    if normalized_path.startswith('static/'):
        candidate_paths.append(os.path.join(LOCAL_STATIC_ROOT, normalized_path[len('static/'):]))

    return any(os.path.exists(path) for path in candidate_paths)


def cover_or_default(public_path, default=DEFAULT_ISSUE_COVER):
    default_url = _static_url(default)
    if not public_path:
        return default_url
    if public_path.startswith('/static/') and not _public_static_path_exists(public_path):
        return default_url
    return public_path


def timestamp_to_date(timestamp):
    if not timestamp:
        return ''
    utc_plus_5_offset = 5 * 60 * 60
    local_timestamp = timestamp + utc_plus_5_offset
    return time.strftime('%d.%m.%Y', time.gmtime(local_timestamp))


def status_color(status):
    colors = {
        'declined': 'red',
        'rejected': 'red',
        'unpaid': 'blue',
        'paid': 'green',
        'pending': 'blue'
    }
    return colors.get(status, 'gray')


def status_text(status):
    texts = {
        'declined': 'Declined',
        'rejected': 'Declined',
        'unpaid': 'Waiting payment',
        'paid': 'Activated',
        'pending': 'Under review'
    }
    return texts.get(status, status.title())


def format_currency(value, currency='usd'):
    try:
        value = float(value)
        if currency == 'uzs':
            return f"{value:,.0f} UZS"
        if currency == 'rub':
            return f"{value:,.0f} ₽"
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def _multi_unescape(value):
    decoded = str(value)
    for _ in range(3):
        next_decoded = unescape(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    return decoded


class _RichTextSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self._chunks = []
        self._ignore_depth = 0

    @property
    def html(self):
        return ''.join(self._chunks)

    def _sanitize_url(self, raw_value):
        value = _clean_text(raw_value)
        if not value:
            return ''
        lowered = value.lower()
        if lowered.startswith(('javascript:', 'vbscript:', 'data:')):
            return ''
        if value.startswith(('#', '/', './', '../', '//')):
            return value
        parsed = urlparse(value)
        if parsed.scheme and parsed.scheme.lower() not in RICHTEXT_ALLOWED_PROTOCOLS:
            return ''
        return value

    def _sanitize_attrs(self, tag, attrs):
        allowed = set(RICHTEXT_ALLOWED_ATTRS.get('*', set()))
        allowed.update(RICHTEXT_ALLOWED_ATTRS.get(tag, set()))
        cleaned = []

        for name, value in attrs:
            attr_name = (name or '').strip().lower()
            if not attr_name or attr_name.startswith('on') or attr_name not in allowed:
                continue

            attr_value = '' if value is None else str(value).strip()
            if attr_name in {'href', 'src', 'cite'}:
                attr_value = self._sanitize_url(attr_value)
                if not attr_value:
                    continue
            elif attr_name == 'target':
                if attr_value not in {'_blank', '_self'}:
                    continue
            elif attr_name in {'colspan', 'rowspan', 'start'}:
                if not re.fullmatch(r'\d{1,2}', attr_value):
                    continue
            elif attr_name in {'width', 'height'}:
                if not re.fullmatch(r'\d{1,4}', attr_value):
                    continue
            elif attr_name == 'loading':
                if attr_value not in {'lazy', 'eager'}:
                    continue
            elif attr_name == 'rel':
                rel_values = []
                for part in re.split(r'\s+', attr_value):
                    normalized = part.strip().lower()
                    if normalized in {'noopener', 'noreferrer', 'nofollow'} and normalized not in rel_values:
                        rel_values.append(normalized)
                attr_value = ' '.join(rel_values)
                if not attr_value:
                    continue

            cleaned.append((attr_name, attr_value))

        if tag == 'a':
            attrs_map = {k: v for k, v in cleaned}
            if attrs_map.get('target') == '_blank':
                rel_tokens = set(attrs_map.get('rel', '').split()) if attrs_map.get('rel') else set()
                rel_tokens.update({'noopener', 'noreferrer'})
                rel_value = ' '.join(sorted(token for token in rel_tokens if token))
                cleaned = [(k, v) for k, v in cleaned if k != 'rel']
                cleaned.append(('rel', rel_value))

        return cleaned

    def _write_start_tag(self, tag, attrs):
        attrs_text = ''.join(f' {key}="{html_escape(val, quote=True)}"' for key, val in attrs)
        self._chunks.append(f'<{tag}{attrs_text}>')

    def handle_starttag(self, tag, attrs):
        normalized_tag = (tag or '').lower()
        if self._ignore_depth:
            if normalized_tag in RICHTEXT_STRIP_CONTENT_TAGS:
                self._ignore_depth += 1
            return

        if normalized_tag in RICHTEXT_STRIP_CONTENT_TAGS:
            self._ignore_depth = 1
            return
        if normalized_tag not in RICHTEXT_ALLOWED_TAGS:
            return

        cleaned_attrs = self._sanitize_attrs(normalized_tag, attrs)
        self._write_start_tag(normalized_tag, cleaned_attrs)

    def handle_startendtag(self, tag, attrs):
        normalized_tag = (tag or '').lower()
        if normalized_tag in RICHTEXT_VOID_TAGS:
            self.handle_starttag(normalized_tag, attrs)
            return
        self.handle_starttag(normalized_tag, attrs)
        self.handle_endtag(normalized_tag)

    def handle_endtag(self, tag):
        normalized_tag = (tag or '').lower()
        if self._ignore_depth:
            if normalized_tag in RICHTEXT_STRIP_CONTENT_TAGS:
                self._ignore_depth -= 1
            return
        if normalized_tag in RICHTEXT_ALLOWED_TAGS and normalized_tag not in RICHTEXT_VOID_TAGS:
            self._chunks.append(f'</{normalized_tag}>')

    def handle_data(self, data):
        if self._ignore_depth or not data:
            return
        self._chunks.append(html_escape(data, quote=False))

    def handle_entityref(self, name):
        if self._ignore_depth:
            return
        self._chunks.append(f'&{name};')

    def handle_charref(self, name):
        if self._ignore_depth:
            return
        self._chunks.append(f'&#{name};')


def _normalize_plain_richtext(raw_text):
    text = str(raw_text or '').replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = text.strip()
    if not text:
        return ''

    paragraphs = []
    for paragraph in re.split(r'\n\s*\n+', text):
        lines = [line.strip() for line in paragraph.split('\n') if line.strip()]
        if not lines:
            continue
        paragraphs.append(f"<p>{'<br>'.join(html_escape(line, quote=False) for line in lines)}</p>")
    return ''.join(paragraphs)


def decode_html(value):
    if value is None:
        return ''
    return _multi_unescape(value)


def render_richtext(value):
    source = _multi_unescape(value).strip() if value is not None else ''
    if not source:
        return Markup('')

    if '<' not in source and '>' not in source:
        return Markup(_normalize_plain_richtext(source))

    sanitizer = _RichTextSanitizer()
    sanitizer.feed(source)
    sanitizer.close()
    cleaned = sanitizer.html

    cleaned = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<p>\s*(?:&nbsp;|\s|<br\s*/?>)*</p>', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    has_block_tag = re.search(r'<(p|h[1-6]|ul|ol|blockquote|pre|table|figure)\b', cleaned, flags=re.IGNORECASE)
    if cleaned and not has_block_tag:
        cleaned = f'<p>{cleaned}</p>'

    return Markup(cleaned)


def register_filters(app):
    app.template_filter('cover_or_default')(cover_or_default)
    app.template_filter('timestamp_to_date')(timestamp_to_date)
    app.template_filter('status_color')(status_color)
    app.template_filter('status_text')(status_text)
    app.template_filter('format_currency')(format_currency)
    app.template_filter('decode_html')(decode_html)
    app.template_filter('render_richtext')(render_richtext)
