import os
# flake8: noqa
import uuid
import datetime
import time
import secrets
import re
import json
import logging
from html import escape as html_escape
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
from flask import Blueprint, send_from_directory, render_template, request, jsonify, flash, redirect, url_for, session, send_file, abort
from werkzeug.utils import secure_filename
from modules.translate import t, translate
from extensions import db
try:
    import fmadmin.settings as settings
except ImportError:
    import settings
from services.emailer import send_notification_email
from utils.notifications import (
    apply_localized_notification_content,
    current_notification_language,
    localized_texts,
    normalize_notification_language,
    prepare_notification_content,
    role_notification_access_clause as build_role_notification_access_clause,
    user_allows_email_notifications,
)
from utils.auth import is_allowed, is_editor_allowed, is_admin_or_editor, is_superadmin_required
from utils.private_uploads import extract_private_upload_key, private_upload_abspath
from utils.roles import (
    AUTHOR_ROLE,
    PRIVILEGED_ROLES,
    build_user_roles,
    hydrate_user_roles,
    parse_role_names,
    primary_role,
    staff_roles_for_user,
    user_has_permission,
    user_has_role,
)
from services.stats import get_dashboard_snapshot
from shared.publication_metadata import (
    PUBLICATION_METADATA_COLUMN_TYPES,
    normalize_publication_metadata_key,
    publication_metadata_field_labels,
    publication_metadata_options,
)

bp = Blueprint('fmadmin_web', __name__)
logger = logging.getLogger(__name__)
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 15 * 60
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5
LOGIN_RATE_LIMIT_BASE_LOCK_SECONDS = 60
LOGIN_RATE_LIMIT_MAX_LOCK_SECONDS = 30 * 60
LOGIN_RATE_LIMIT_STATE = {}
LOGIN_RATE_LIMIT_SCOPE = 'fmadmin'
LOGIN_RATE_LIMIT_TABLE = 'auth_login_rate_limits'
LOGIN_RATE_LIMIT_STORAGE_READY = False

WORKFLOW_STAGE_CHOICES = [
    ('waiting', "Kutilmoqda"),
    ('technical_check', "Texnik talablarga mos"),
    ('anti_plagiarism', "Antiplagiatga tekshirish"),
    ('in_review', "Taqrizda"),
    ('recommended', "Nashrga tavsiya etildi"),
    ('payment', "To'lov"),
    ('published', "Nashr qilindi"),
]
WORKFLOW_STAGE_LABELS = {key: label for key, label in WORKFLOW_STAGE_CHOICES}
WORKFLOW_STAGE_KEYS = set(WORKFLOW_STAGE_LABELS.keys()) | {'rejected'}
SUBMISSION_EXTRA_COLUMN_TYPES = {
    'workflow_stage': 'text',
    'assigned_admin_id': 'integer',
    'anti_plagiarism_file': 'text',
    'anti_plagiarism_checked_at': 'bigint',
    'anti_plagiarism_checked_by': 'integer',
    'related_submission_id': 'integer'
}
USER_EXTRA_COLUMN_TYPES = {
    'is_hidden': 'boolean',
    'deleted_at': 'bigint',
    'admin_tracks': 'text[]',
    'editor_admin_id': 'integer',
    'roles': 'text[]',
    'ui_language': 'text'
}
EDITOR_ASSIGNMENT_EXTRA_COLUMN_TYPES = {
    'assignment_note': 'text',
    'deadline_at': 'bigint',
    'acceptance_deadline_at': 'bigint',
    'completion_deadline_at': 'bigint',
    'accepted_at': 'bigint',
    'acceptance_reminder_level': 'text',
    'completion_reminder_level': 'text',
    'admin_decision': 'text',
    'admin_comment': 'text',
    'admin_decided_by': 'integer',
    'admin_decided_at': 'bigint'
}
PUBLICATION_EXTRA_COLUMN_TYPES = dict(PUBLICATION_METADATA_COLUMN_TYPES)
PUBLICATION_EXTRA_COLUMN_TYPES['page_range'] = 'text'
ISSUE_EXTRA_COLUMN_TYPES = {
    'table_of_contents_file': 'text'
}

EDITOR_ASSIGNMENT_STATUS_VALUES = {'pending', 'in_review', 'reviewed', 'rejected'}
EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES = {'pending', 'in_review'}
EDITOR_ASSIGNMENT_REVIEWED_STATUS_VALUES = {'reviewed', 'rejected'}
EDITOR_ASSIGNMENT_ADMIN_DECISION_VALUES = {'pending', 'accepted', 'revision_requested'}
ROLE_NOTIFICATION_LEVELS = {'info', 'success', 'warning', 'danger'}
EDITOR_ASSIGNMENT_REMINDER_LEVEL_RANKS = {'': 0, '24h': 1, '6h': 2, '1h': 3}
EDITOR_ASSIGNMENT_AUTOMATION_INTERVAL_SECONDS = 30
_LAST_EDITOR_ASSIGNMENT_AUTOMATION_TS = 0

EDITORIAL_MEMBER_TYPE_ORDER = [
    'editor_in_chief',
    'deputy_editor',
    'editor',
    'reviewer',
    'advisory_member',
    'technical_editor',
    'translator'
]
EDITORIAL_MEMBER_TYPE_LABELS = {
    'uz': {
        'editor_in_chief': "Bosh muharrir",
        'deputy_editor': "Mas'ul kotib",
        'editor': "Muharrir",
        'reviewer': "Ilmiy muharrir",
        'advisory_member': "Sahifalovchi",
        'technical_editor': "Musahhih",
        'translator': "Tarjimon"
    },
    'ru': {
        'editor_in_chief': "Главный редактор",
        'deputy_editor': "Ответственный секретарь",
        'editor': "Редактор",
        'reviewer': "Научный редактор",
        'advisory_member': "Редактор верстки",
        'technical_editor': "Корректор",
        'translator': "Переводчик"
    },
    'en': {
        'editor_in_chief': "Editor-in-Chief",
        'deputy_editor': "Responsible Secretary",
        'editor': "Editor",
        'reviewer': "Scientific Editor",
        'advisory_member': "Layout Editor",
        'technical_editor': "Proofreader",
        'translator': "Translator"
    }
}
EDITORIAL_MEMBER_TYPE_KEYS = set(EDITORIAL_MEMBER_TYPE_ORDER)

EMAIL_TEMPLATE_VAR_PATTERN = re.compile(r'{{\s*([a-zA-Z0-9_]+)\s*}}')
EMAIL_TEMPLATE_DEFAULTS = [
    {
        'alias': 'assignment_deadline_editor',
        'name': 'Editor deadline reminder',
        'description': 'Editor uchun deadline eslatmasi',
        'variables': ['name', 'title', 'time_left', 'deadline_type'],
        'subject_uz': 'Topshiriq muddati yaqin',
        'subject_ru': 'Срок задания приближается',
        'subject_en': 'Assignment deadline is near',
        'intro_uz': '{{name}}, "{{title}}" bo\'yicha {{deadline_type}} muddatiga {{time_left}} qoldi.',
        'intro_ru': '{{name}}, по "{{title}}" до срока {{deadline_type}} осталось {{time_left}}.',
        'intro_en': '{{name}}, {{time_left}} left before {{deadline_type}} deadline for "{{title}}".',
        'body_uz': 'Iltimos, topshiriqni vaqtida yakunlang.',
        'body_ru': 'Пожалуйста, завершите задачу вовремя.',
        'body_en': 'Please complete the assignment on time.',
        'cta_label_uz': 'Topshiriqni ochish',
        'cta_label_ru': 'Открыть назначение',
        'cta_label_en': 'Open assignment',
    },
    {
        'alias': 'assignment_deadline_admin',
        'name': 'Admin deadline reminder',
        'description': 'Admin uchun editor deadline eslatmasi',
        'variables': ['editor_name', 'title', 'time_left', 'deadline_type'],
        'subject_uz': 'Editor muddati yaqin',
        'subject_ru': 'Срок редактора приближается',
        'subject_en': 'Editor deadline is near',
        'intro_uz': '{{editor_name}} uchun "{{title}}" bo\'yicha {{deadline_type}} muddatiga {{time_left}} qoldi.',
        'intro_ru': 'Для {{editor_name}} по "{{title}}" до срока {{deadline_type}} осталось {{time_left}}.',
        'intro_en': '{{time_left}} left before {{editor_name}} reaches {{deadline_type}} deadline for "{{title}}".',
        'body_uz': 'Kerak bo\'lsa, admin panel orqali qo\'lda boshqaruvni amalga oshiring.',
        'body_ru': 'При необходимости выполните ручное управление через админ-панель.',
        'body_en': 'If needed, use manual controls in admin panel.',
        'cta_label_uz': 'Batafsil ko\'rish',
        'cta_label_ru': 'Открыть детали',
        'cta_label_en': 'Open details',
    },
]

ADMIN_TRACK_CHOICES = [
    ('masters', 'Magistratura'),
    ('phd', 'Doktorantura'),
    ('teacher', "O'qituvchi")
]
ADMIN_TRACK_KEYS = tuple(key for key, _ in ADMIN_TRACK_CHOICES)
ADMIN_TRACK_LABELS = {key: label for key, label in ADMIN_TRACK_CHOICES}
ADMIN_TRACK_ALIASES = {
    'masters': 'masters',
    'master': 'masters',
    'magister': 'masters',
    'magistr': 'masters',
    'magistratura': 'masters',
    'магистр': 'masters',
    'магистратура': 'masters',
    'phd': 'phd',
    'doctor': 'phd',
    'doctoral': 'phd',
    'doktor': 'phd',
    'doktorant': 'phd',
    'doktorantura': 'phd',
    'doctorant': 'phd',
    'doctorantura': 'phd',
    'докторант': 'phd',
    'докторантура': 'phd',
    'teacher': 'teacher',
    "o'qituvchi": 'teacher',
    'oqituvchi': 'teacher',
    'ustoz': 'teacher',
    'prepodavatel': 'teacher',
    'преподаватель': 'teacher'
}

CLASSIFICATION_AREA_ORDER = [
    'linguistics',
    'literature',
    'translation',
    'methodology',
    'journalism',
    'pedagogy',
    'psychology'
]

CLASSIFICATION_AREA_ID_MAP = {
    'linguistics': {'3', '14', '15', '18', '20', '23', '26', '28', '32', '37', '43', '46', '49', '52'},
    'literature': {'1', '2', '7', '22', '30', '31', '45', '48'},
    'translation': {'16', '51'},
    'methodology': {'5', '13', '17', '39'},
    'journalism': {'8', '12', '21', '33', '35', '36', '38', '41'},
    'pedagogy': {'9', '19', '24', '25', '40'},
    'psychology': {'4', '6', '10', '11', '27', '29', '34', '42', '44', '47', '50'}
}

CLASSIFICATION_AREA_LABELS = {
    'uz': {
        'linguistics': '1. TILSHUNOSLIK',
        'literature': '2. ADABIYOTSHUNOSLIK',
        'translation': '3. TARJIMASHUNOSLIK',
        'methodology': '4. METODIKA',
        'journalism': '5. JURNALISTIKA',
        'pedagogy': '6. PEDAGOGIKA',
        'psychology': '7. PSIXOLOGIYA'
    },
    'ru': {
        'linguistics': '1. ЯЗЫКОЗНАНИЕ',
        'literature': '2. ЛИТЕРАТУРОВЕДЕНИЕ',
        'translation': '3. ПЕРЕВОДОВЕДЕНИЕ',
        'methodology': '4. МЕТОДИКА',
        'journalism': '5. ЖУРНАЛИСТИКА',
        'pedagogy': '6. ПЕДАГОГИКА',
        'psychology': '7. ПСИХОЛОГИЯ'
    },
    'en': {
        'linguistics': '1. LINGUISTICS',
        'literature': '2. LITERARY STUDIES',
        'translation': '3. TRANSLATION STUDIES',
        'methodology': '4. METHODOLOGY',
        'journalism': '5. JOURNALISM',
        'pedagogy': '6. PEDAGOGY',
        'psychology': '7. PSYCHOLOGY'
    }
}

CLASSIFICATION_CUSTOM_ITEMS = {
    'tr_lang_uz': {
        'area': 'translation',
        'label': {
            'uz': "Tarjimashunoslik (o'zbek tili)",
            'ru': 'Переводоведение (узбекский язык)',
            'en': 'Translation Studies (Uzbek)'
        }
    },
    'tr_lang_ru': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (rus tili)',
            'ru': 'Переводоведение (русский язык)',
            'en': 'Translation Studies (Russian)'
        }
    },
    'tr_lang_en': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (ingliz tili)',
            'ru': 'Переводоведение (английский язык)',
            'en': 'Translation Studies (English)'
        }
    },
    'tr_lang_fr': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (fransuz tili)',
            'ru': 'Переводоведение (французский язык)',
            'en': 'Translation Studies (French)'
        }
    },
    'tr_lang_de': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (nemis tili)',
            'ru': 'Переводоведение (немецкий язык)',
            'en': 'Translation Studies (German)'
        }
    },
    'tr_lang_es': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (ispan tili)',
            'ru': 'Переводоведение (испанский язык)',
            'en': 'Translation Studies (Spanish)'
        }
    },
    'tr_lang_it': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (italyan tili)',
            'ru': 'Переводоведение (итальянский язык)',
            'en': 'Translation Studies (Italian)'
        }
    },
    'tr_lang_ar': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (arab tili)',
            'ru': 'Переводоведение (арабский язык)',
            'en': 'Translation Studies (Arabic)'
        }
    },
    'tr_lang_zh': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (xitoy tili)',
            'ru': 'Переводоведение (китайский язык)',
            'en': 'Translation Studies (Chinese)'
        }
    },
    'tr_lang_ja': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (yapon tili)',
            'ru': 'Переводоведение (японский язык)',
            'en': 'Translation Studies (Japanese)'
        }
    },
    'tr_lang_ms': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (malay tili)',
            'ru': 'Переводоведение (малайский язык)',
            'en': 'Translation Studies (Malay)'
        }
    },
    'tr_lang_ko': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (koreys tili)',
            'ru': 'Переводоведение (корейский язык)',
            'en': 'Translation Studies (Korean)'
        }
    },
    'tr_lang_hi': {
        'area': 'translation',
        'label': {
            'uz': 'Tarjimashunoslik (hind tili)',
            'ru': 'Переводоведение (хинди)',
            'en': 'Translation Studies (Hindi)'
        }
    }
}


def _clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _split_author_full_name(value):
    parts = [part for part in re.split(r'\s+', _clean_text(value)) if part]
    if not parts:
        return '', '', ''
    if len(parts) == 1:
        return parts[0], '', ''
    if len(parts) == 2:
        return parts[0], parts[1], ''
    return parts[0], parts[1], ' '.join(parts[2:])


def _compose_author_full_name(first_name, second_name='', father_name=''):
    return ' '.join(
        part for part in (
            _clean_text(first_name),
            _clean_text(second_name),
            _clean_text(father_name),
        )
        if part
    )


def _normalize_email_template_alias(value):
    normalized = _clean_text(value).lower()
    normalized = re.sub(r'[^a-z0-9_]+', '_', normalized)
    return re.sub(r'_+', '_', normalized).strip('_')


def _parse_template_variables_csv(value):
    if value is None:
        return []
    seen = set()
    result = []
    raw_items = re.split(r'[\s,]+', str(value))
    for item in raw_items:
        normalized = _normalize_email_template_alias(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _collect_template_variables(*texts):
    found = set()
    for text in texts:
        for match in EMAIL_TEMPLATE_VAR_PATTERN.findall(str(text or '')):
            normalized = _normalize_email_template_alias(match)
            if normalized:
                found.add(normalized)
    return sorted(found)


def _render_template_preview_text(text_value, sample_values=None):
    text = str(text_value or '')
    values = sample_values or {}

    def _replace(match):
        key = _normalize_email_template_alias(match.group(1))
        if key in values:
            return str(values[key])
        return match.group(0)

    return EMAIL_TEMPLATE_VAR_PATTERN.sub(_replace, text)


ARTICLE_HTML_ALLOWED_TAGS = {
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
ARTICLE_HTML_VOID_TAGS = {'br', 'hr', 'img'}
ARTICLE_HTML_STRIP_CONTENT_TAGS = {
    'script', 'style', 'iframe', 'object', 'embed', 'form',
    'input', 'button', 'textarea', 'select', 'option', 'svg', 'math',
}
ARTICLE_HTML_ALLOWED_PROTOCOLS = {'http', 'https', 'mailto', 'tel'}
ARTICLE_HTML_ALLOWED_ATTRS = {
    '*': {'title'},
    'a': {'href', 'target', 'rel'},
    'img': {'src', 'alt', 'width', 'height', 'loading'},
    'th': {'colspan', 'rowspan'},
    'td': {'colspan', 'rowspan'},
    'ol': {'start'},
    'blockquote': {'cite'},
}


class _ArticleHTMLSanitizer(HTMLParser):
    """Keep semantic content and drop noisy/unsafe Word-style inline markup."""

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
        if parsed.scheme and parsed.scheme.lower() not in ARTICLE_HTML_ALLOWED_PROTOCOLS:
            return ''
        return value

    def _sanitize_attrs(self, tag, attrs):
        allowed = set(ARTICLE_HTML_ALLOWED_ATTRS.get('*', set()))
        allowed.update(ARTICLE_HTML_ALLOWED_ATTRS.get(tag, set()))
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
            if normalized_tag in ARTICLE_HTML_STRIP_CONTENT_TAGS:
                self._ignore_depth += 1
            return

        if normalized_tag in ARTICLE_HTML_STRIP_CONTENT_TAGS:
            self._ignore_depth = 1
            return
        if normalized_tag not in ARTICLE_HTML_ALLOWED_TAGS:
            return

        cleaned_attrs = self._sanitize_attrs(normalized_tag, attrs)
        self._write_start_tag(normalized_tag, cleaned_attrs)

    def handle_startendtag(self, tag, attrs):
        normalized_tag = (tag or '').lower()
        if normalized_tag in ARTICLE_HTML_VOID_TAGS:
            self.handle_starttag(normalized_tag, attrs)
            return
        self.handle_starttag(normalized_tag, attrs)
        self.handle_endtag(normalized_tag)

    def handle_endtag(self, tag):
        normalized_tag = (tag or '').lower()
        if self._ignore_depth:
            if normalized_tag in ARTICLE_HTML_STRIP_CONTENT_TAGS:
                self._ignore_depth -= 1
            return
        if normalized_tag in ARTICLE_HTML_ALLOWED_TAGS and normalized_tag not in ARTICLE_HTML_VOID_TAGS:
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


def _normalize_plain_article_text(raw_text):
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


def _normalize_article_page_range(value):
    text = _clean_text(value)
    if not text:
        return None
    text = text.replace('–', '-').replace('—', '-')
    text = re.sub(r'\s*-\s*', '-', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:50] or None


def _sanitize_article_block_html(raw_html):
    source = str(raw_html or '').strip()
    if not source:
        return ''

    if '<' not in source and '>' not in source:
        return _normalize_plain_article_text(source)

    sanitizer = _ArticleHTMLSanitizer()
    sanitizer.feed(source)
    sanitizer.close()
    cleaned = sanitizer.html

    cleaned = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<p>\s*(?:&nbsp;|\s|<br\s*/?>)*</p>', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    has_block_tag = re.search(r'<(p|h[1-6]|ul|ol|blockquote|pre|table|figure)\b', cleaned, flags=re.IGNORECASE)
    if cleaned and not has_block_tag:
        cleaned = f'<p>{cleaned}</p>'
    return cleaned


def _safe_internal_redirect(target, fallback_endpoint):
    fallback_url = url_for(fallback_endpoint)
    target_text = _clean_text(target)
    if not target_text:
        return fallback_url

    parsed = urlparse(target_text)
    if parsed.scheme or parsed.netloc:
        request_host = (request.host or '').split(':')[0]
        parsed_host = (parsed.hostname or '').split(':')[0] if parsed.hostname else ''
        if parsed_host != request_host:
            return fallback_url
        path = parsed.path or '/'
        query = f"?{parsed.query}" if parsed.query else ''
        return f"{path}{query}"

    if not target_text.startswith('/') or target_text.startswith('//'):
        return fallback_url
    return target_text


def _login_rate_limit_key(email):
    ip_address = _get_request_ip()
    return f"{ip_address or 'unknown'}::{(email or '').strip().lower()}"


def _get_request_ip():
    return (request.remote_addr or '').strip()


def _ensure_login_rate_limit_storage():
    global LOGIN_RATE_LIMIT_STORAGE_READY
    if LOGIN_RATE_LIMIT_STORAGE_READY:
        return True

    try:
        cursor = db.conn.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {LOGIN_RATE_LIMIT_TABLE} (
                scope TEXT NOT NULL,
                rate_key TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                first_attempt_at DOUBLE PRECISION NOT NULL DEFAULT 0,
                last_attempt_at DOUBLE PRECISION NOT NULL DEFAULT 0,
                locked_until DOUBLE PRECISION NOT NULL DEFAULT 0,
                updated_at BIGINT NOT NULL DEFAULT EXTRACT(epoch FROM now()),
                PRIMARY KEY (scope, rate_key)
            );
            """
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{LOGIN_RATE_LIMIT_TABLE}_cleanup "
            f"ON {LOGIN_RATE_LIMIT_TABLE}(scope, last_attempt_at, locked_until);"
        )
        db.conn.commit()
        cursor.close()
        LOGIN_RATE_LIMIT_STORAGE_READY = True
        return True
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return False


def _load_login_rate_limit_state(key):
    state = LOGIN_RATE_LIMIT_STATE.get(key)
    if not _ensure_login_rate_limit_storage():
        return state

    try:
        cursor = db.conn.cursor()
        cursor.execute(
            f"SELECT attempt_count, first_attempt_at, last_attempt_at, locked_until "
            f"FROM {LOGIN_RATE_LIMIT_TABLE} WHERE scope = %s AND rate_key = %s",
            (LOGIN_RATE_LIMIT_SCOPE, key),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return state
        return {
            'count': int(row[0] or 0),
            'first_attempt_at': float(row[1] or 0),
            'last_attempt_at': float(row[2] or 0),
            'locked_until': float(row[3] or 0),
        }
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return state


def _save_login_rate_limit_state(key, state):
    LOGIN_RATE_LIMIT_STATE[key] = state
    if not _ensure_login_rate_limit_storage():
        return

    try:
        cursor = db.conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {LOGIN_RATE_LIMIT_TABLE}
                (scope, rate_key, attempt_count, first_attempt_at, last_attempt_at, locked_until, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scope, rate_key) DO UPDATE
            SET attempt_count = EXCLUDED.attempt_count,
                first_attempt_at = EXCLUDED.first_attempt_at,
                last_attempt_at = EXCLUDED.last_attempt_at,
                locked_until = EXCLUDED.locked_until,
                updated_at = EXCLUDED.updated_at
            """,
            (
                LOGIN_RATE_LIMIT_SCOPE,
                key,
                int(state.get('count') or 0),
                float(state.get('first_attempt_at') or 0),
                float(state.get('last_attempt_at') or 0),
                float(state.get('locked_until') or 0),
                int(time.time()),
            ),
        )
        db.conn.commit()
        cursor.close()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass


def _delete_login_rate_limit_state(key):
    LOGIN_RATE_LIMIT_STATE.pop(key, None)
    if not _ensure_login_rate_limit_storage():
        return

    try:
        cursor = db.conn.cursor()
        cursor.execute(
            f"DELETE FROM {LOGIN_RATE_LIMIT_TABLE} WHERE scope = %s AND rate_key = %s",
            (LOGIN_RATE_LIMIT_SCOPE, key),
        )
        db.conn.commit()
        cursor.close()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass


def _clear_admin_session():
    session.pop('fmadmin_user', None)


def _prune_login_rate_limits(now_ts):
    stale_before_ts = now_ts - LOGIN_RATE_LIMIT_WINDOW_SECONDS
    if _ensure_login_rate_limit_storage():
        try:
            cursor = db.conn.cursor()
            cursor.execute(
                f"DELETE FROM {LOGIN_RATE_LIMIT_TABLE} "
                f"WHERE scope = %s AND last_attempt_at < %s AND locked_until <= %s",
                (LOGIN_RATE_LIMIT_SCOPE, float(stale_before_ts), float(now_ts)),
            )
            db.conn.commit()
            cursor.close()
        except Exception:
            try:
                db.conn.rollback()
            except Exception:
                pass

    stale_keys = []
    for key, state in LOGIN_RATE_LIMIT_STATE.items():
        last_attempt_at = float(state.get('last_attempt_at') or 0)
        locked_until = float(state.get('locked_until') or 0)
        if (now_ts - last_attempt_at) > LOGIN_RATE_LIMIT_WINDOW_SECONDS and locked_until <= now_ts:
            stale_keys.append(key)
    for key in stale_keys:
        LOGIN_RATE_LIMIT_STATE.pop(key, None)


def _remaining_login_lock_seconds(email):
    now_ts = time.time()
    _prune_login_rate_limits(now_ts)
    state = _load_login_rate_limit_state(_login_rate_limit_key(email))
    if not state:
        return 0
    return max(0, int((state.get('locked_until') or 0) - now_ts))


def _record_login_failure(email):
    now_ts = time.time()
    _prune_login_rate_limits(now_ts)
    key = _login_rate_limit_key(email)
    state = _load_login_rate_limit_state(key)
    if not state or (now_ts - float(state.get('first_attempt_at') or 0)) > LOGIN_RATE_LIMIT_WINDOW_SECONDS:
        state = {
            'count': 0,
            'first_attempt_at': now_ts,
            'last_attempt_at': now_ts,
            'locked_until': 0,
        }

    state['count'] = int(state.get('count') or 0) + 1
    state['last_attempt_at'] = now_ts
    if state['count'] >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        lock_step = state['count'] - LOGIN_RATE_LIMIT_MAX_ATTEMPTS
        lock_seconds = min(
            LOGIN_RATE_LIMIT_BASE_LOCK_SECONDS * (2 ** lock_step),
            LOGIN_RATE_LIMIT_MAX_LOCK_SECONDS,
        )
        state['locked_until'] = now_ts + lock_seconds

    _save_login_rate_limit_state(key, state)
    return max(0, int((state.get('locked_until') or 0) - now_ts))


def _clear_login_failures(email):
    _delete_login_rate_limit_state(_login_rate_limit_key(email))


def _parse_text_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            cleaned = _clean_text(item)
            if cleaned:
                result.append(cleaned)
        return result

    text = _clean_text(value)
    if not text:
        return []
    if text.startswith('[') and text.endswith(']'):
        try:
            parsed_json = json.loads(text)
            if isinstance(parsed_json, list):
                return _parse_text_list(parsed_json)
        except Exception:
            pass
    if text.startswith('{') and text.endswith('}'):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [
            item.strip().strip('"').strip("'")
            for item in inner.split(',')
            if item.strip().strip('"').strip("'")
        ]
    return [item.strip() for item in text.split(',') if item.strip()]


def _parse_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_amount(value):
    if value in (None, ''):
        return None
    text = _clean_text(value)
    if not text:
        return None
    text = re.sub(r'[^0-9,.-]', '', text)
    if not text:
        return None
    if ',' in text and '.' in text:
        if text.rfind(',') > text.rfind('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    else:
        text = text.replace(',', '.')
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _ensure_tariff_duration_column(default_days=30):
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('tariffs', []))
        if 'duration_days' in existing_columns:
            return
        cursor = db.conn.cursor()
        cursor.execute(f"ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS duration_days integer DEFAULT {int(default_days)};")
        cursor.execute(
            "UPDATE tariffs "
            "SET duration_days = COALESCE(duration_days, user_limit, %s) "
            "WHERE duration_days IS NULL;",
            (int(default_days),)
        )
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass


def _ensure_tariff_archive_column():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('tariffs', []))
        if 'is_archived' in existing_columns:
            return
        cursor = db.conn.cursor()
        cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS is_archived boolean DEFAULT false;")
        cursor.execute("UPDATE tariffs SET is_archived = false WHERE is_archived IS NULL;")
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass


def _ensure_tariff_entitlement_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('tariffs', []))
        if not existing_columns:
            return

        missing_columns = {}
        if 'entitlement_scope' not in existing_columns:
            missing_columns['entitlement_scope'] = "text DEFAULT 'all'"
        if 'archive_days_threshold' not in existing_columns:
            missing_columns['archive_days_threshold'] = "integer DEFAULT 365"
        if 'article_discount_pct' not in existing_columns:
            missing_columns['article_discount_pct'] = "double precision DEFAULT 0"
        if 'issue_discount_pct' not in existing_columns:
            missing_columns['issue_discount_pct'] = "double precision DEFAULT 0"
        if 'subscription_discount_pct' not in existing_columns:
            missing_columns['subscription_discount_pct'] = "double precision DEFAULT 0"
        if 'subscription_discount_start_at' not in existing_columns:
            missing_columns['subscription_discount_start_at'] = "bigint"
        if 'subscription_discount_end_at' not in existing_columns:
            missing_columns['subscription_discount_end_at'] = "bigint"
        if 'monthly_download_limit' not in existing_columns:
            missing_columns['monthly_download_limit'] = "integer DEFAULT 0"
        if 'required_academic_positions' not in existing_columns:
            missing_columns['required_academic_positions'] = "text[] DEFAULT '{}'::text[]"
        if 'requires_verified_document' not in existing_columns:
            missing_columns['requires_verified_document'] = "boolean DEFAULT false"
        if 'eligibility_note' not in existing_columns:
            missing_columns['eligibility_note'] = "text"
        if 'feature_permissions' not in existing_columns:
            missing_columns['feature_permissions'] = "text[] DEFAULT '{}'::text[]"
        if 'required_document_types' not in existing_columns:
            missing_columns['required_document_types'] = "text[] DEFAULT '{}'::text[]"

        cursor = db.conn.cursor()
        for column_name, column_type in missing_columns.items():
            cursor.execute(f"ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS {column_name} {column_type};")

        cursor.execute(
            "UPDATE tariffs "
            "SET entitlement_scope = COALESCE(NULLIF(TRIM(entitlement_scope), ''), 'all') "
            "WHERE entitlement_scope IS NULL OR NULLIF(TRIM(entitlement_scope), '') IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET archive_days_threshold = COALESCE(archive_days_threshold, 365) "
            "WHERE archive_days_threshold IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET article_discount_pct = COALESCE(article_discount_pct, 0) "
            "WHERE article_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET issue_discount_pct = COALESCE(issue_discount_pct, 0) "
            "WHERE issue_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET subscription_discount_pct = COALESCE(subscription_discount_pct, 0) "
            "WHERE subscription_discount_pct IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET monthly_download_limit = COALESCE(monthly_download_limit, 0) "
            "WHERE monthly_download_limit IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET required_academic_positions = COALESCE(required_academic_positions, ARRAY[]::text[]) "
            "WHERE required_academic_positions IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET requires_verified_document = COALESCE(requires_verified_document, false) "
            "WHERE requires_verified_document IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET feature_permissions = COALESCE(feature_permissions, ARRAY[]::text[]) "
            "WHERE feature_permissions IS NULL;"
        )
        cursor.execute(
            "UPDATE tariffs SET required_document_types = COALESCE(required_document_types, ARRAY[]::text[]) "
            "WHERE required_document_types IS NULL;"
        )
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass


def _ensure_payment_snapshot_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('payments', []))
        missing_columns = []
        if 'snapshot_duration_days' not in existing_columns:
            missing_columns.append(('snapshot_duration_days', 'integer'))
        if 'snapshot_start_at' not in existing_columns:
            missing_columns.append(('snapshot_start_at', 'bigint'))
        if 'snapshot_end_at' not in existing_columns:
            missing_columns.append(('snapshot_end_at', 'bigint'))
        if not missing_columns:
            return
        cursor = db.conn.cursor()
        for column_name, column_type in missing_columns:
            cursor.execute(f"ALTER TABLE payments ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass


def _ensure_user_doc_upload_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('user_doc_uploads', []))
        if not existing_columns:
            return
        missing_columns = []
        if 'document_type' not in existing_columns:
            missing_columns.append(('document_type', 'text'))
        if 'document_holder_name' not in existing_columns:
            missing_columns.append(('document_holder_name', 'text'))
        if 'institution_name' not in existing_columns:
            missing_columns.append(('institution_name', 'text'))
        if not missing_columns:
            return
        cursor = db.conn.cursor()
        for column_name, column_type in missing_columns:
            cursor.execute(f"ALTER TABLE user_doc_uploads ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        cursor.execute(
            "UPDATE user_doc_uploads "
            "SET document_type = 'other_academic' "
            "WHERE document_type IS NULL AND COALESCE(TRIM(file_path), '') <> '';"
        )
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass


def _is_tariff_archived(tariff):
    value = (tariff or {}).get('is_archived')
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


HOME_VIDEO_USAGE_KEY = 'home_video_site_usage_url'
HOME_VIDEO_SUBMISSION_KEY = 'home_video_submission_url'
HOME_VIDEO_LANGS = ('uz', 'ru', 'en')
PAYMENT_GUIDE_KEY = 'payment_guide_html'
PAYMENT_GUIDE_LANGS = ('uz', 'ru', 'en')


def _home_video_key(base_key, lang):
    lang_text = _clean_text(lang).lower()
    if lang_text in HOME_VIDEO_LANGS:
        return f"{base_key}_{lang_text}"
    return base_key


def _default_payment_guide_html(lang='uz'):
    content = """
<p>To'lovlar bank o'tkazmasi orqali amalga oshiriladi. Tarif yoki maqola/son tanlangach tizim sizga to'lov ID raqamini beradi. To'lovni amalga oshirgach, chek yoki skrinshotni shaxsiy kabinetdagi to'lov sahifasiga yuklang.</p>
<h5>To'lov rekvizitlari</h5>
<ul>
  <li>Qabul qiluvchi: Philology Matters jurnali tahririyati</li>
  <li>Hisob raqami: 2020 0000 0000 1234 5678</li>
  <li>Bank: "Tijorat banki" AJ, Toshkent shahar filiali</li>
  <li>MFO: 00415</li>
  <li>INN/STIR: 305123456</li>
  <li>SWIFT: TJJBUZ2X</li>
</ul>
<h5>To'lovni tasdiqlash</h5>
<ol>
  <li>To'lovni amalga oshiring va chek/skrinshotni saqlang.</li>
  <li>Shaxsiy kabinetdagi "To'lovlar" bo'limiga kiring.</li>
  <li>"To'lov tasdiqnomasi"ni yuklang va izoh qoldiring.</li>
  <li>Moliyaviy bo'lim tekshiruvdan so'ng to'lovni tasdiqlaydi.</li>
</ol>
<h5>To'lov nimaga qarab hisoblanadi?</h5>
<ul>
  <li>Obuna: tanlangan tarif narxi bo'yicha.</li>
  <li>Son/maqola: tegishli narxlar bo'yicha.</li>
</ul>
<p>Agar savollar bo'lsa, finance@philologymatters.uz manzili yoki +998 71 000 00 00 raqamiga murojaat qiling.</p>
"""
    return content


def _get_site_setting(key, default=''):
    key_text = _clean_text(key)
    if not key_text:
        return default
    try:
        rows = db.settings.get(k=key_text).exec()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return default
    if not rows:
        return default
    value = rows[0].get('v')
    return _clean_text(value) or default


def _set_site_setting(key, value):
    key_text = _clean_text(key)
    if not key_text:
        return False
    value_text = _clean_text(value)
    try:
        rows = db.settings.get(k=key_text).exec()
        now_ts = int(datetime.datetime.now().timestamp())
        if rows:
            db.settings.get(id=rows[0]['id']).update(v=value_text).exec()
        else:
            db.settings.add(k=key_text, v=value_text, created_at=now_ts).exec()
        return True
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return False


def _normalize_editorial_member_type(value):
    normalized = _clean_text(value).lower()
    if normalized in EDITORIAL_MEMBER_TYPE_KEYS:
        return normalized
    return 'editor'


def _editorial_member_type_label(value, lang=None):
    normalized = _normalize_editorial_member_type(value)
    language = _clean_text(lang or _ui_language()).lower()
    labels = EDITORIAL_MEMBER_TYPE_LABELS.get(language) or EDITORIAL_MEMBER_TYPE_LABELS['uz']
    return labels.get(normalized, labels.get('editor', 'Editor'))


def _editorial_member_type_options(lang=None):
    language = _clean_text(lang or _ui_language()).lower()
    labels = EDITORIAL_MEMBER_TYPE_LABELS.get(language) or EDITORIAL_MEMBER_TYPE_LABELS['uz']
    return [{'value': key, 'label': labels.get(key, key)} for key in EDITORIAL_MEMBER_TYPE_ORDER]


def _localized_editorial_field(item, base_field, lang=None):
    if not isinstance(item, dict):
        return ''
    language = _clean_text(lang or _ui_language()).lower()
    default_value = _clean_text(item.get(base_field))
    uz_value = _clean_text(item.get(f'{base_field}_uz'))
    ru_value = _clean_text(item.get(f'{base_field}_ru'))
    if language == 'uz':
        return uz_value or default_value or ru_value
    if language == 'ru':
        return ru_value or default_value or uz_value
    return default_value or uz_value or ru_value


def _localized_content_field(item, base_field, lang=None, strict=False):
    if not isinstance(item, dict):
        return ''
    language = _clean_text(lang or _admin_language()).lower()
    en_value = _clean_text(item.get(base_field))
    uz_value = _clean_text(item.get(f'{base_field}_uz'))
    ru_value = _clean_text(item.get(f'{base_field}_ru'))
    if language == 'uz':
        return uz_value if strict else (uz_value or en_value or ru_value)
    if language == 'ru':
        return ru_value if strict else (ru_value or en_value or uz_value)
    return en_value if strict else (en_value or uz_value or ru_value)


def _editorial_admin_ui_texts(lang=None):
    language = _clean_text(lang or _ui_language()).lower()
    texts = {
        'uz': {
            'page_title': "Tahrir hay'ati",
            'page_subtitle': "Saytda ko'rinadigan tahrir hay'ati va tahrizchilar ro'yxati",
            'add_member': "A'zo qo'shish",
            'label_name': "F.I.Sh.",
            'label_type': "Turi",
            'label_status': "Holati",
            'label_position': "Lavozim",
            'label_organization': "Tashkilot",
            'label_sort': "Tartib",
            'all': "Barchasi",
            'active': "Faol",
            'inactive': "Nofaol",
            'clear': "Tozalash",
            'search': "Qidirish",
            'search_placeholder': "Qidirish...",
            'confirm_delete': "A'zoni o'chirishni tasdiqlaysizmi?",
            'empty': "Hozircha a'zolar qo'shilmagan",
            'showing': "Ko'rsatilmoqda",
            'back_to_list': "Ro'yxatga qaytish",
            'save': "Saqlash",
            'delete': "O'chirish",
            'add_title': "Tahrir hay'ati a'zosini qo'shish",
            'edit_subtitle': "Superadmin ushbu bo'limda EN/UZ/RU tillarda ma'lumot kiritadi",
            'section_main': "Asosiy ma'lumotlar (3 til)",
            'fill_note': "Kamida bitta tilda F.I.Sh. to'ldirilishi shart. EN maydon asosiy (default) til sifatida ishlatiladi.",
            'field_full_name': "F.I.Sh.",
            'field_position': "Lavozim",
            'field_organization': "Tashkilot",
            'field_bio': "Biografiya",
            'field_type': "Turi",
            'field_email': "Email",
            'field_orcid': "ORCID",
            'field_image': "Rasm",
            'field_sort': "Tartib",
            'field_state': "Holati",
            'remove_image': "Rasmni o'chirish",
            'ph_full_name_en': "Masalan: John Smith",
            'ph_full_name_uz': "Masalan: Jo'n Smit",
            'ph_full_name_ru': "Masalan: Джон Смит",
            'ph_position_en': "Masalan: Professor, PhD",
            'ph_position_uz': "Masalan: Professor, PhD",
            'ph_position_ru': "Masalan: Профессор, PhD",
            'ph_org_en': "Masalan: Uzbek State World Languages University",
            'ph_org_uz': "Masalan: O'zbekiston davlat jahon tillari universiteti",
            'ph_org_ru': "Masalan: Узбекский государственный университет мировых языков",
            'ph_bio_en': "Qisqacha biografiya...",
            'ph_bio_uz': "Qisqacha biografiya...",
            'ph_bio_ru': "Qisqacha biografiya...",
        },
        'ru': {
            'page_title': "Редакционная коллегия",
            'page_subtitle': "Список участников редакционной коллегии и рецензентов, отображаемый на сайте",
            'add_member': "Добавить участника",
            'label_name': "Ф.И.О.",
            'label_type': "Тип",
            'label_status': "Статус",
            'label_position': "Должность",
            'label_organization': "Организация",
            'label_sort': "Порядок",
            'all': "Все",
            'active': "Активен",
            'inactive': "Неактивен",
            'clear': "Очистить",
            'search': "Поиск",
            'search_placeholder': "Поиск...",
            'confirm_delete': "Подтверждаете удаление участника?",
            'empty': "Пока участники не добавлены",
            'showing': "Показано",
            'back_to_list': "Вернуться к списку",
            'save': "Сохранить",
            'delete': "Удалить",
            'add_title': "Добавление участника редакционной коллегии",
            'edit_subtitle': "В этом разделе superadmin заполняет данные на EN/UZ/RU языках",
            'section_main': "Основная информация (3 языка)",
            'fill_note': "Заполните Ф.И.О. минимум на одном языке. Поле EN используется как основное (default).",
            'field_full_name': "Ф.И.О.",
            'field_position': "Должность",
            'field_organization': "Организация",
            'field_bio': "Биография",
            'field_type': "Тип",
            'field_email': "Email",
            'field_orcid': "ORCID",
            'field_image': "Фото",
            'field_sort': "Порядок",
            'field_state': "Статус",
            'remove_image': "Удалить фото",
            'ph_full_name_en': "Например: John Smith",
            'ph_full_name_uz': "Например: Джон Смит (узб.)",
            'ph_full_name_ru': "Например: Джон Смит",
            'ph_position_en': "Например: Professor, PhD",
            'ph_position_uz': "Например: Профессор, PhD (узб.)",
            'ph_position_ru': "Например: Профессор, PhD",
            'ph_org_en': "Например: Uzbek State World Languages University",
            'ph_org_uz': "Например: Узбекский государственный университет мировых языков (узб.)",
            'ph_org_ru': "Например: Узбекский государственный университет мировых языков",
            'ph_bio_en': "Краткая биография...",
            'ph_bio_uz': "Краткая биография (узб.)...",
            'ph_bio_ru': "Краткая биография...",
        },
        'en': {
            'page_title': "Editorial Board",
            'page_subtitle': "List of editorial board members and reviewers displayed on the site",
            'add_member': "Add member",
            'label_name': "Full name",
            'label_type': "Type",
            'label_status': "Status",
            'label_position': "Position",
            'label_organization': "Organization",
            'label_sort': "Order",
            'all': "All",
            'active': "Active",
            'inactive': "Inactive",
            'clear': "Clear",
            'search': "Search",
            'search_placeholder': "Search...",
            'confirm_delete': "Confirm member deletion?",
            'empty': "No members have been added yet",
            'showing': "Showing",
            'back_to_list': "Back to list",
            'save': "Save",
            'delete': "Delete",
            'add_title': "Add editorial board member",
            'edit_subtitle': "In this section, superadmin fills data in EN/UZ/RU languages",
            'section_main': "Main information (3 languages)",
            'fill_note': "Fill full name in at least one language. EN field is used as default.",
            'field_full_name': "Full name",
            'field_position': "Position",
            'field_organization': "Organization",
            'field_bio': "Biography",
            'field_type': "Type",
            'field_email': "Email",
            'field_orcid': "ORCID",
            'field_image': "Image",
            'field_sort': "Order",
            'field_state': "Status",
            'remove_image': "Remove image",
            'ph_full_name_en': "Example: John Smith",
            'ph_full_name_uz': "Example: Jo'n Smit",
            'ph_full_name_ru': "Example: Джон Смит",
            'ph_position_en': "Example: Professor, PhD",
            'ph_position_uz': "Example: Professor, PhD (UZ)",
            'ph_position_ru': "Example: Профессор, PhD",
            'ph_org_en': "Example: Uzbek State World Languages University",
            'ph_org_uz': "Example: O'zbekiston davlat jahon tillari universiteti",
            'ph_org_ru': "Example: Узбекский государственный университет мировых языков",
            'ph_bio_en': "Short biography...",
            'ph_bio_uz': "Short biography (UZ)...",
            'ph_bio_ru': "Short biography (RU)...",
        }
    }
    return texts.get(language, texts['uz'])


def _parse_date_to_timestamp(value, end_of_day=False):
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    try:
        dt = datetime.datetime.strptime(cleaned, '%Y-%m-%d')
    except ValueError:
        return None
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return int(dt.timestamp())


def _parse_datetime_to_timestamp(value):
    cleaned = _clean_text(value)
    if not cleaned:
        return None

    formats = (
        '%Y-%m-%dT%H:%M',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d'
    )
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(cleaned, fmt)
            if fmt == '%Y-%m-%d':
                dt = dt.replace(hour=23, minute=59, second=59)
            return int(dt.timestamp())
        except ValueError:
            continue
    return None


def _format_duration_text(total_seconds, lang='uz'):
    seconds = max(int(total_seconds or 0), 0)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)

    if lang == 'ru':
        labels = {'day': 'д', 'hour': 'ч', 'minute': 'м'}
    elif lang == 'en':
        labels = {'day': 'd', 'hour': 'h', 'minute': 'm'}
    else:
        labels = {'day': 'kun', 'hour': 'soat', 'minute': 'daq'}

    parts = []
    if days:
        parts.append(f"{days}{labels['day']}")
    if hours:
        parts.append(f"{hours}{labels['hour']}")
    if minutes or not parts:
        parts.append(f"{minutes}{labels['minute']}")
    return ' '.join(parts[:2])


def _assignment_remaining_label(remaining_seconds, lang=None):
    language = _clean_text(lang or _ui_language()).lower()
    if language not in {'uz', 'ru', 'en'}:
        language = 'uz'

    if remaining_seconds is None:
        return ''
    if int(remaining_seconds) <= 0:
        if language == 'ru':
            return 'Срок истёк'
        if language == 'en':
            return 'Deadline passed'
        return "Muddat o'tgan"
    return _format_duration_text(remaining_seconds, language)


def _determine_reminder_level(remaining_seconds):
    seconds = _parse_int(remaining_seconds)
    if seconds is None or seconds <= 0:
        return ''
    if seconds <= 3600:
        return '1h'
    if seconds <= 21600:
        return '6h'
    if seconds <= 86400:
        return '24h'
    return ''


def _reminder_level_rank(level):
    normalized = _clean_text(level).lower()
    return EDITOR_ASSIGNMENT_REMINDER_LEVEL_RANKS.get(normalized, 0)


def _normalize_assignment_status(status):
    normalized = _clean_text(status).lower()
    if normalized in EDITOR_ASSIGNMENT_STATUS_VALUES:
        return normalized
    return 'pending'


def _normalize_assignment_admin_decision(decision):
    normalized = _clean_text(decision).lower()
    if normalized in EDITOR_ASSIGNMENT_ADMIN_DECISION_VALUES:
        return normalized
    return 'pending'


def _assignment_stats(assignments):
    normalized_statuses = [_normalize_assignment_status(item.get('status')) for item in (assignments or [])]
    return {
        'total': len(normalized_statuses),
        'pending': len([status for status in normalized_statuses if status in EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES]),
        'reviewed': len([status for status in normalized_statuses if status == 'reviewed']),
        'rejected': len([status for status in normalized_statuses if status == 'rejected'])
    }


def _decorate_assignment(assignment, now_ts=None, lang=None):
    decorated = dict(assignment or {})
    decorated['status'] = _normalize_assignment_status(decorated.get('status'))
    decorated['admin_decision'] = _normalize_assignment_admin_decision(decorated.get('admin_decision'))
    decorated['accepted_at'] = _parse_int(decorated.get('accepted_at'))

    acceptance_deadline_at = _parse_int(decorated.get('acceptance_deadline_at'))
    completion_deadline_at = _parse_int(decorated.get('completion_deadline_at'))
    legacy_deadline_at = _parse_int(decorated.get('deadline_at'))

    if completion_deadline_at is None:
        completion_deadline_at = legacy_deadline_at
    if legacy_deadline_at is None and completion_deadline_at is not None:
        decorated['deadline_at'] = completion_deadline_at

    decorated['acceptance_deadline_at'] = acceptance_deadline_at
    decorated['completion_deadline_at'] = completion_deadline_at
    decorated['acceptance_reminder_level'] = _clean_text(decorated.get('acceptance_reminder_level')).lower()
    decorated['completion_reminder_level'] = _clean_text(decorated.get('completion_reminder_level')).lower()

    current_ts = _parse_int(now_ts) or int(datetime.datetime.now().timestamp())
    acceptance_remaining_seconds = None
    completion_remaining_seconds = None
    if acceptance_deadline_at is not None:
        acceptance_remaining_seconds = acceptance_deadline_at - current_ts
    if completion_deadline_at is not None:
        completion_remaining_seconds = completion_deadline_at - current_ts

    decorated['acceptance_remaining_seconds'] = acceptance_remaining_seconds
    decorated['completion_remaining_seconds'] = completion_remaining_seconds
    decorated['acceptance_remaining_label'] = _assignment_remaining_label(acceptance_remaining_seconds, lang=lang)
    decorated['completion_remaining_label'] = _assignment_remaining_label(completion_remaining_seconds, lang=lang)
    return decorated


def _refresh_submission_editor_review_status(submission_id):
    submission_id_int = _parse_int(submission_id)
    if submission_id_int is None:
        return None

    submission_rows = db.submissions.all().equal(id=submission_id_int).exec()
    if not submission_rows:
        return None
    submission = submission_rows[0]

    try:
        assignments = db.editor_assignments.all().equal(submission_id=submission_id_int).exec()
    except Exception:
        assignments = []

    normalized_assignments = [_decorate_assignment(item) for item in assignments]
    normalized_statuses = [item.get('status') for item in normalized_assignments]
    normalized_decisions = [item.get('admin_decision') for item in normalized_assignments]

    if not normalized_assignments:
        review_status = 'not_assigned'
    elif any(status in EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES for status in normalized_statuses):
        if all(status == 'pending' for status in normalized_statuses):
            review_status = 'assigned'
        else:
            review_status = 'in_review'
    elif all(status in EDITOR_ASSIGNMENT_REVIEWED_STATUS_VALUES for status in normalized_statuses):
        if normalized_decisions and all(decision == 'accepted' for decision in normalized_decisions):
            review_status = 'approved'
        else:
            review_status = 'reviewed'
    else:
        review_status = 'in_review'

    now_ts = int(datetime.datetime.now().timestamp())
    update_data = {
        'editor_review_status': review_status,
        'updated_at': now_ts
    }

    submission_status = _clean_text(submission.get('status')).lower()
    if review_status in {'assigned', 'in_review', 'reviewed'}:
        update_data['workflow_stage'] = 'in_review'
        if submission_status in {'submitted', 'pending'}:
            update_data['status'] = 'in_process'
    elif review_status == 'approved':
        update_data['workflow_stage'] = 'recommended'
        if submission_status in {'submitted', 'pending'}:
            update_data['status'] = 'in_process'

    db.submissions.all().equal(id=submission_id_int).update(**update_data).exec()
    return review_status


def _deadline_ts_label(timestamp_value):
    ts = _parse_int(timestamp_value)
    if ts is None:
        return '-'
    try:
        return datetime.datetime.fromtimestamp(ts).strftime('%d.%m.%Y %H:%M')
    except Exception:
        return '-'


def _assignment_editor_name(editor_user, editor_id):
    if isinstance(editor_user, dict):
        full_name = _clean_text(f"{editor_user.get('name') or ''} {editor_user.get('second_name') or ''}")
        if full_name:
            return full_name
    parsed_id = _parse_int(editor_id)
    return f"ID: {parsed_id}" if parsed_id is not None else 'Editor'


def _notify_assignment_deadline_reminder(
    assignment,
    submission=None,
    editor_user=None,
    reminder_type='acceptance',
    remaining_seconds=None,
    actor_user_id=None
):
    assignment_id = _parse_int((assignment or {}).get('id'))
    if assignment_id is None:
        return 0

    submission_title = _submission_title(submission or {})
    editor_id = _parse_int((assignment or {}).get('editor_id'))
    submission_id = _parse_int((assignment or {}).get('submission_id'))
    if editor_id is None:
        return 0

    left_uz = _format_duration_text(remaining_seconds, 'uz')
    left_ru = _format_duration_text(remaining_seconds, 'ru')
    left_en = _format_duration_text(remaining_seconds, 'en')
    editor_name = _assignment_editor_name(editor_user, editor_id)
    review_url = url_for('review_assignment', assignment_id=assignment_id)

    if reminder_type == 'completion':
        editor_title = localized_texts(
            "Tahriz topshirish muddati yaqin",
            "Срок отправки рецензии приближается",
            "Review submission deadline is near"
        )
        editor_message = localized_texts(
            f'"{submission_title}" bo\'yicha tahriz yuborish uchun {left_uz} qoldi.',
            f'До отправки рецензии по "{submission_title}" осталось {left_ru}.',
            f'{left_en} left to submit review for "{submission_title}".'
        )
        admin_message = localized_texts(
            f'{editor_name} uchun "{submission_title}" bo\'yicha tahriz muddati tugashiga {left_uz} qoldi.',
            f'До дедлайна рецензии "{submission_title}" у {editor_name} осталось {left_ru}.',
            f'{left_en} left for {editor_name} to submit review for "{submission_title}".'
        )
        event_type = 'editor_assignment_completion_deadline_reminder'
    else:
        editor_title = localized_texts(
            "Topshiriqni qabul qilish muddati yaqin",
            "Срок принятия задания приближается",
            "Assignment acceptance deadline is near"
        )
        editor_message = localized_texts(
            f'"{submission_title}" maqolasini ochib ko\'rish uchun {left_uz} qoldi.',
            f'Осталось {left_ru}, чтобы открыть задание по "{submission_title}".',
            f'{left_en} left to open assignment for "{submission_title}".'
        )
        admin_message = localized_texts(
            f'{editor_name} "{submission_title}" topshirig\'ini ochishiga {left_uz} qoldi.',
            f'У {editor_name} осталось {left_ru}, чтобы открыть задание "{submission_title}".',
            f'{left_en} left for {editor_name} to open assignment "{submission_title}".'
        )
        event_type = 'editor_assignment_acceptance_deadline_reminder'

    if not isinstance(editor_user, dict):
        editor_rows = db.users.all().equal(id=editor_id).exec()
        editor_user = editor_rows[0] if editor_rows else None

    sent_count = 0
    if _create_role_notification(
        target_user_id=editor_id,
        target_role='editor',
        title=editor_title,
        message=editor_message,
        action_url=review_url,
        level='warning',
        event_type=event_type,
        related_submission_id=submission_id,
        related_assignment_id=assignment_id,
        actor_user_id=actor_user_id
    ):
        sent_count += 1

    admin_user_id = _parse_int((submission or {}).get('assigned_admin_id'))
    admin_user = None
    if admin_user_id is None:
        admin_user_id = _parse_int((assignment or {}).get('assigned_by'))
    if admin_user_id is not None and admin_user_id != editor_id:
        admin_rows = db.users.all().equal(id=admin_user_id).exec()
        admin_user = admin_rows[0] if admin_rows else None
        if _create_role_notification(
            target_user_id=admin_user_id,
            target_role='admin',
            title=editor_title,
            message=admin_message,
            action_url=review_url,
            level='warning',
            event_type=event_type,
            related_submission_id=submission_id,
            related_assignment_id=assignment_id,
            actor_user_id=actor_user_id
        ):
            sent_count += 1

    deadline_kind = localized_texts(
        "qabul qilish",
        "принятия задания",
        "assignment acceptance"
    )
    if reminder_type == 'completion':
        deadline_kind = localized_texts(
            "tahriz topshirish",
            "отправки рецензии",
            "review submission"
        )

    deadline_label = _format_duration_text(remaining_seconds, 'uz')
    email_subject = editor_title
    email_intro_editor = localized_texts(
        f'"{submission_title}" bo\'yicha {deadline_kind} muddati yaqin: {deadline_label} qoldi.',
        f'По "{submission_title}" приближается срок {deadline_kind}: осталось {left_ru}.',
        f'The {deadline_kind} deadline for "{submission_title}" is near: {left_en} left.'
    )
    email_intro_admin = localized_texts(
        f'{editor_name} uchun "{submission_title}" bo\'yicha {deadline_kind} muddatiga {deadline_label} qoldi.',
        f'Для {editor_name} по "{submission_title}" приближается срок {deadline_kind}: осталось {left_ru}.',
        f'{left_en} left before {editor_name} reaches the {deadline_kind} deadline for "{submission_title}".'
    )
    email_details = [
        (
            localized_texts('Maqola', 'Материал', 'Submission'),
            submission_title,
        ),
        (
            localized_texts('Qolgan vaqt', 'Оставшееся время', 'Time left'),
            localized_texts(left_uz, left_ru, left_en),
        ),
    ]

    _send_user_email(
        editor_user,
        subject=email_subject,
        intro=email_intro_editor,
        details=email_details,
        cta_url=review_url,
        cta_label=localized_texts('Topshiriqni ochish', 'Открыть назначение', 'Open assignment'),
        template_alias='assignment_deadline_editor',
        template_vars={
            'name': editor_name,
            'title': submission_title,
            'time_left': localized_texts(left_uz, left_ru, left_en),
            'deadline_type': deadline_kind,
            'editor_name': editor_name,
        },
    )
    _send_user_email(
        admin_user,
        subject=email_subject,
        intro=email_intro_admin,
        details=email_details,
        cta_url=review_url,
        cta_label=localized_texts('Batafsil ko\'rish', 'Открыть детали', 'Open details'),
        template_alias='assignment_deadline_admin',
        template_vars={
            'editor_name': editor_name,
            'title': submission_title,
            'time_left': localized_texts(left_uz, left_ru, left_en),
            'deadline_type': deadline_kind,
            'name': editor_name,
        },
    )

    return sent_count


def _expire_assignment_due_deadline(
    assignment,
    submission=None,
    editor_user=None,
    reason='acceptance',
    now_ts=None,
    actor_user_id=None
):
    assignment_id = _parse_int((assignment or {}).get('id'))
    submission_id = _parse_int((assignment or {}).get('submission_id'))
    editor_id = _parse_int((assignment or {}).get('editor_id'))
    if assignment_id is None:
        return False

    deadline_ts = _parse_int((assignment or {}).get('acceptance_deadline_at' if reason == 'acceptance' else 'completion_deadline_at'))
    deadline_label = _deadline_ts_label(deadline_ts)
    submission_title = _submission_title(submission or {})
    editor_name = _assignment_editor_name(editor_user, editor_id)
    current_ts = _parse_int(now_ts) or int(datetime.datetime.now().timestamp())

    try:
        db.editor_assignments.all().equal(id=assignment_id).delete().exec()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return False

    try:
        db.editor_notifications.all().equal(assignment_id=assignment_id).delete().exec()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass

    if submission_id is not None:
        _refresh_submission_editor_review_status(submission_id)

    if reason == 'completion':
        editor_title = localized_texts(
            "Tahriz topshirish muddati o'tdi",
            "Срок отправки рецензии истёк",
            "Review submission deadline passed"
        )
        editor_message = localized_texts(
            f'"{submission_title}" bo\'yicha tahriz topshirish muddati ({deadline_label}) tugadi. Topshiriq bekor qilindi.',
            f'Срок отправки рецензии по "{submission_title}" ({deadline_label}) истёк. Назначение отменено.',
            f'The review deadline for "{submission_title}" ({deadline_label}) has passed. Assignment was removed.'
        )
        admin_message = localized_texts(
            f'{editor_name} uchun "{submission_title}" bo\'yicha topshirish muddati ({deadline_label}) o\'tdi. Topshiriq olib tashlandi.',
            f'У {editor_name} истёк дедлайн по "{submission_title}" ({deadline_label}). Назначение удалено.',
            f'Deadline for {editor_name} on "{submission_title}" ({deadline_label}) has passed. Assignment was removed.'
        )
    else:
        editor_title = localized_texts(
            "Topshiriqni qabul qilish muddati o'tdi",
            "Срок принятия задания истёк",
            "Assignment acceptance deadline passed"
        )
        editor_message = localized_texts(
            f'"{submission_title}" topshirig\'ini qabul qilish muddati ({deadline_label}) tugadi. Topshiriq bekor qilindi.',
            f'Срок принятия задания "{submission_title}" ({deadline_label}) истёк. Назначение отменено.',
            f'The acceptance deadline for "{submission_title}" ({deadline_label}) has passed. Assignment was removed.'
        )
        admin_message = localized_texts(
            f'{editor_name} "{submission_title}" topshirig\'ini vaqtida qabul qilmadi ({deadline_label}). Topshiriq olib tashlandi.',
            f'{editor_name} не принял задание "{submission_title}" в срок ({deadline_label}). Назначение удалено.',
            f'{editor_name} did not accept "{submission_title}" before {deadline_label}. Assignment was removed.'
        )

    if editor_id is not None:
        _create_role_notification(
            target_user_id=editor_id,
            target_role='editor',
            title=editor_title,
            message=editor_message,
            action_url=url_for('editor_assignments'),
            level='danger',
            event_type='editor_assignment_expired',
            related_submission_id=submission_id,
            related_assignment_id=assignment_id,
            actor_user_id=actor_user_id
        )

    admin_user_id = _parse_int((submission or {}).get('assigned_admin_id'))
    if admin_user_id is None:
        admin_user_id = _parse_int((assignment or {}).get('assigned_by'))
    if admin_user_id is not None and admin_user_id != editor_id:
        admin_action_url = url_for('submission_detail', submission_id=submission_id) if submission_id is not None else url_for('editor_assignments')
        _create_role_notification(
            target_user_id=admin_user_id,
            target_role='admin',
            title=editor_title,
            message=admin_message,
            action_url=admin_action_url,
            level='danger',
            event_type='editor_assignment_expired',
            related_submission_id=submission_id,
            related_assignment_id=assignment_id,
            actor_user_id=actor_user_id
        )

    _notify_role_users(
        'superadmin',
        title=editor_title,
        message=admin_message,
        action_url=url_for('submission_detail', submission_id=submission_id) if submission_id is not None else url_for('editor_assignments'),
        level='danger',
        event_type='editor_assignment_expired',
        related_submission_id=submission_id,
        related_assignment_id=assignment_id,
        actor_user_id=actor_user_id
    )

    try:
        db.role_notifications.all().equal(related_assignment_id=assignment_id).unequal(event_type='editor_assignment_expired').update(
            is_read=True,
            read_at=current_ts
        ).exec()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass

    return True


def _process_editor_assignments_deadline_cycle(actor_user_id=None):
    now_ts = int(datetime.datetime.now().timestamp())
    try:
        assignments = db.editor_assignments.all().any(status=list(EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES)).exec()
    except Exception:
        assignments = []

    if not assignments:
        return {'processed': 0, 'expired': 0, 'reminders': 0}

    submission_ids = list({_parse_int(item.get('submission_id')) for item in assignments if _parse_int(item.get('submission_id')) is not None})
    editor_ids = list({_parse_int(item.get('editor_id')) for item in assignments if _parse_int(item.get('editor_id')) is not None})

    submissions_map = {}
    if submission_ids:
        try:
            submissions_rows = db.submissions.all().any(id=submission_ids).exec()
        except Exception:
            submissions_rows = db.submissions.all().exec()
        submissions_map = {item.get('id'): item for item in submissions_rows if item.get('id') is not None}

    editors_map = {}
    if editor_ids:
        try:
            editors_rows = db.users.all().any(id=editor_ids).exec()
        except Exception:
            editors_rows = db.users.all().exec()
        editors_map = {item.get('id'): item for item in editors_rows if item.get('id') is not None}

    processed_count = 0
    expired_count = 0
    reminders_count = 0

    for raw_assignment in assignments:
        assignment = _decorate_assignment(raw_assignment, now_ts=now_ts)
        assignment_id = _parse_int(assignment.get('id'))
        if assignment_id is None:
            continue

        processed_count += 1
        submission = submissions_map.get(_parse_int(assignment.get('submission_id')))
        editor_user = editors_map.get(_parse_int(assignment.get('editor_id')))
        assignment_status = assignment.get('status')
        accepted_at = _parse_int(assignment.get('accepted_at'))

        acceptance_deadline_at = _parse_int(assignment.get('acceptance_deadline_at'))
        completion_deadline_at = _parse_int(assignment.get('completion_deadline_at'))
        acceptance_remaining_seconds = assignment.get('acceptance_remaining_seconds')
        completion_remaining_seconds = assignment.get('completion_remaining_seconds')

        # Remove task if acceptance window is missed before opening the assignment.
        if (
            assignment_status == 'pending'
            and accepted_at is None
            and acceptance_deadline_at is not None
            and acceptance_deadline_at <= now_ts
        ):
            if _expire_assignment_due_deadline(
                assignment,
                submission=submission,
                editor_user=editor_user,
                reason='acceptance',
                now_ts=now_ts,
                actor_user_id=actor_user_id
            ):
                expired_count += 1
            continue

        # Remove task if completion deadline is missed while still active.
        if (
            assignment_status in EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES
            and completion_deadline_at is not None
            and completion_deadline_at <= now_ts
        ):
            if _expire_assignment_due_deadline(
                assignment,
                submission=submission,
                editor_user=editor_user,
                reason='completion',
                now_ts=now_ts,
                actor_user_id=actor_user_id
            ):
                expired_count += 1
            continue

        if (
            assignment_status == 'pending'
            and accepted_at is None
            and acceptance_deadline_at is not None
            and acceptance_deadline_at > now_ts
        ):
            next_level = _determine_reminder_level(acceptance_remaining_seconds)
            current_level = _clean_text(assignment.get('acceptance_reminder_level')).lower()
            if _reminder_level_rank(next_level) > _reminder_level_rank(current_level):
                reminders_count += _notify_assignment_deadline_reminder(
                    assignment,
                    submission=submission,
                    editor_user=editor_user,
                    reminder_type='acceptance',
                    remaining_seconds=acceptance_remaining_seconds,
                    actor_user_id=actor_user_id
                )
                db.editor_assignments.all().equal(id=assignment_id).update(
                    acceptance_reminder_level=next_level,
                    updated_at=now_ts
                ).exec()

        if (
            assignment_status in EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES
            and completion_deadline_at is not None
            and completion_deadline_at > now_ts
            and assignment_status == 'in_review'
        ):
            next_level = _determine_reminder_level(completion_remaining_seconds)
            current_level = _clean_text(assignment.get('completion_reminder_level')).lower()
            if _reminder_level_rank(next_level) > _reminder_level_rank(current_level):
                reminders_count += _notify_assignment_deadline_reminder(
                    assignment,
                    submission=submission,
                    editor_user=editor_user,
                    reminder_type='completion',
                    remaining_seconds=completion_remaining_seconds,
                    actor_user_id=actor_user_id
                )
                db.editor_assignments.all().equal(id=assignment_id).update(
                    completion_reminder_level=next_level,
                    updated_at=now_ts
                ).exec()

    return {'processed': processed_count, 'expired': expired_count, 'reminders': reminders_count}


def run_editor_assignment_automation(actor_user_id=None, force=False):
    global _LAST_EDITOR_ASSIGNMENT_AUTOMATION_TS
    now_ts = int(datetime.datetime.now().timestamp())
    if not force and now_ts - _LAST_EDITOR_ASSIGNMENT_AUTOMATION_TS < EDITOR_ASSIGNMENT_AUTOMATION_INTERVAL_SECONDS:
        return {'processed': 0, 'expired': 0, 'reminders': 0, 'skipped': True}

    _LAST_EDITOR_ASSIGNMENT_AUTOMATION_TS = now_ts
    try:
        result = _process_editor_assignments_deadline_cycle(actor_user_id=actor_user_id)
        result['skipped'] = False
        return result
    except Exception as exc:
        logger.warning("Editor assignment deadline automation warning: %s", exc)
        try:
            db.conn.rollback()
        except Exception:
            pass
        return {'processed': 0, 'expired': 0, 'reminders': 0, 'skipped': False}


def _normalize_admin_track(track):
    if track is None:
        return None
    normalized = str(track).strip().lower()
    normalized = normalized.replace('’', "'")
    normalized = ADMIN_TRACK_ALIASES.get(normalized, normalized)
    return normalized if normalized in ADMIN_TRACK_KEYS else None


def _parse_admin_tracks(value):
    normalized_tracks = []
    for track in _parse_text_list(value):
        normalized_track = _normalize_admin_track(track)
        if normalized_track and normalized_track not in normalized_tracks:
            normalized_tracks.append(normalized_track)
    return normalized_tracks


def _extract_admin_tracks(data):
    if hasattr(data, 'getlist'):
        raw_tracks = data.getlist('admin_tracks')
    else:
        raw_tracks = data.get('admin_tracks')
    tracks = _parse_admin_tracks(raw_tracks)
    return tracks


def _extract_author_role_flag(data, primary_role_name):
    normalized_primary_role = (primary_role_name or '').strip().lower()
    if normalized_primary_role == AUTHOR_ROLE:
        return True

    if hasattr(data, 'getlist'):
        raw_values = data.getlist('author_role')
        if raw_values:
            return any(_to_bool(value) for value in raw_values)

    return _to_bool(data.get('author_role'))


def _extract_selected_roles(data, primary_role_name, allowed_roles=None, fallback_roles=None):
    if hasattr(data, 'getlist'):
        raw_roles = data.getlist('roles')
        if not raw_roles:
            raw_roles = data.get('roles')
    else:
        raw_roles = data.get('roles')

    roles = parse_role_names(raw_roles)
    if not roles:
        roles = parse_role_names(fallback_roles)

    allowed_set = set(allowed_roles or [])
    if allowed_set:
        roles = [role_name for role_name in roles if role_name in allowed_set]

    primary = (primary_role_name or '').strip().lower() or AUTHOR_ROLE
    if primary in allowed_set or not allowed_set:
        roles = build_user_roles(primary, include_author_role=False, extra_roles=roles)

    if not roles:
        roles = build_user_roles(primary, include_author_role=(primary == AUTHOR_ROLE))

    if AUTHOR_ROLE not in roles and primary == AUTHOR_ROLE:
        roles.append(AUTHOR_ROLE)

    selected_staff_roles = [role_name for role_name in roles if role_name in PRIVILEGED_ROLES]
    if selected_staff_roles and primary == AUTHOR_ROLE:
        primary = selected_staff_roles[0]
        roles = build_user_roles(primary, include_author_role=(AUTHOR_ROLE in roles), extra_roles=roles)

    if 'superadmin' in roles and primary != 'superadmin':
        primary = 'superadmin'
        roles = build_user_roles(primary, include_author_role=(AUTHOR_ROLE in roles), extra_roles=roles)

    return {
        'primary_role': primary,
        'roles': roles,
    }


def _admin_tracks_for_user(user):
    return _parse_admin_tracks((user or {}).get('admin_tracks'))


def _admin_tracks_label_list(user):
    labels = []
    for track in _admin_tracks_for_user(user):
        labels.append(ADMIN_TRACK_LABELS.get(track, track))
    return labels


def _users_with_role(role_name, include_hidden=False, include_blocked=False):
    normalized_role = _clean_text(role_name).lower()
    if not normalized_role:
        return []
    try:
        rows = db.users.all().exec()
    except Exception:
        return []

    matched_users = []
    for row in rows or []:
        user = hydrate_user_roles(row)
        if not include_hidden and user.get('is_hidden'):
            continue
        if not include_blocked and user.get('is_blocked'):
            continue
        if user_has_role(user, normalized_role):
            matched_users.append(user)
    return matched_users


def _role_notification_access_clause(current_user):
    return build_role_notification_access_clause(current_user)


def _user_has_track_access(user, track):
    normalized_track = _normalize_admin_track(track)
    if not normalized_track:
        return True
    return normalized_track in _admin_tracks_for_user(user)


def _realign_submission_admin_assignments():
    try:
        admins = _active_admins()
        submissions = db.submissions.all().unequal(status='draft').exec()
    except Exception:
        return 0

    admin_tracks_map = {}
    for admin in admins:
        admin_id = _parse_int(admin.get('id'))
        tracks = set(_admin_tracks_for_user(admin))
        if admin_id is None or not tracks:
            continue
        admin_tracks_map[admin_id] = tracks

    now_ts = int(datetime.datetime.now().timestamp())
    admin_loads = {admin_id: 0 for admin_id in admin_tracks_map.keys()}
    for submission in submissions:
        assigned_admin_id = _parse_int(submission.get('assigned_admin_id'))
        if assigned_admin_id in admin_loads:
            admin_loads[assigned_admin_id] += 1

    changed_count = 0
    for submission in submissions:
        submission_id = _parse_int(submission.get('id'))
        if submission_id is None:
            continue

        normalized_track = _normalize_admin_track(submission.get('submission_track'))
        if not normalized_track:
            continue

        assigned_admin_id = _parse_int(submission.get('assigned_admin_id'))
        candidate_admin_ids = [
            admin_id for admin_id, tracks in admin_tracks_map.items()
            if normalized_track in tracks
        ]

        if assigned_admin_id in candidate_admin_ids:
            continue

        if assigned_admin_id in admin_loads:
            admin_loads[assigned_admin_id] = max(0, admin_loads[assigned_admin_id] - 1)

        new_assigned_admin_id = None
        if candidate_admin_ids:
            new_assigned_admin_id = min(
                candidate_admin_ids,
                key=lambda admin_id: (admin_loads.get(admin_id, 0), admin_id)
            )
            admin_loads[new_assigned_admin_id] = admin_loads.get(new_assigned_admin_id, 0) + 1

        db.submissions.all().equal(id=submission_id).update(
            assigned_admin_id=new_assigned_admin_id,
            updated_at=now_ts
        ).exec()
        changed_count += 1

    return changed_count


def _admin_language():
    language = _clean_text(session.get('language') or 'uz').lower()
    if language in {'uz', 'ru', 'en'}:
        return language
    return 'uz'


def _issue_series_options(lang=None):
    language = _clean_text(lang or _admin_language()).lower()
    if language not in {'uz', 'ru', 'en'}:
        language = 'uz'
    catalog = {
        'masters': {
            'uz': 'Seriya: Magistratura',
            'ru': 'Серия: Магистратура',
            'en': "Series: Master's Program",
        },
        'phd': {
            'uz': 'Seriya: Doktorantura',
            'ru': 'Серия: Докторантура',
            'en': 'Series: Doctoral Program',
        },
        'teacher': {
            'uz': "Seriya: Professor-o'qituvchilar",
            'ru': 'Серия: Профессорско-преподавательский состав',
            'en': 'Series: Academic Staff',
        },
        'special_masters': {
            'uz': 'Maxsus son (magistratura)',
            'ru': 'Специальный выпуск (магистратура)',
            'en': "Special Issue (Master's Program)",
        },
        'special_phd': {
            'uz': 'Maxsus son (doktorantura)',
            'ru': 'Специальный выпуск (докторантура)',
            'en': 'Special Issue (Doctoral Program)',
        },
        'special_teacher': {
            'uz': "Maxsus son (professor-o'qituvchilar)",
            'ru': 'Специальный выпуск (профессорско-преподавательский состав)',
            'en': 'Special Issue (Academic Staff)',
        },
    }
    ordered_aliases = (
        'masters',
        'phd',
        'teacher',
        'special_masters',
        'special_phd',
        'special_teacher',
    )
    options = []
    for alias in ordered_aliases:
        labels = catalog.get(alias) or {}
        options.append({
            'alias': alias,
            'name_display': labels.get(language) or labels.get('uz') or alias,
        })
    return options


def _resolve_classification_area(classification_id):
    normalized_id = _clean_text(classification_id)
    if not normalized_id:
        return 'linguistics'
    if normalized_id.startswith('tr_lang_'):
        return 'translation'

    for area_key, id_set in CLASSIFICATION_AREA_ID_MAP.items():
        if normalized_id in id_set:
            return area_key
    return 'linguistics'


def _classification_area_label(area_key, lang):
    labels = CLASSIFICATION_AREA_LABELS.get(lang) or CLASSIFICATION_AREA_LABELS['uz']
    return labels.get(area_key, area_key)


def _classification_label_for_language(item, lang):
    if lang == 'ru':
        return _clean_text(item.get('name_ru') or item.get('name') or item.get('name_uz'))
    if lang == 'en':
        return _clean_text(item.get('name') or item.get('name_uz') or item.get('name_ru'))
    return _clean_text(item.get('name_uz') or item.get('name') or item.get('name_ru'))


def _classification_catalog_lookup(lang):
    lookup = {}
    try:
        rows = db.fix_classifications.all().exec()
    except Exception:
        rows = []

    for item in rows:
        item_id = _clean_text(item.get('id'))
        if not item_id:
            continue
        area_key = _resolve_classification_area(item_id)
        lookup[item_id] = {
            'id': item_id,
            'area_key': area_key,
            'area_label': _classification_area_label(area_key, lang),
            'label': _classification_label_for_language(item, lang),
            'is_custom': False
        }

    for custom_id, custom_data in CLASSIFICATION_CUSTOM_ITEMS.items():
        area_key = custom_data.get('area', 'translation')
        label = custom_data.get('label', {}).get(lang) or custom_data.get('label', {}).get('uz') or custom_id
        lookup[custom_id] = {
            'id': custom_id,
            'area_key': area_key,
            'area_label': _classification_area_label(area_key, lang),
            'label': label,
            'is_custom': True
        }
    return lookup


def _serialize_submission_classifications(raw_classifications, lookup, lang):
    result = []
    seen = set()
    for item_id in _parse_text_list(raw_classifications):
        normalized_id = _clean_text(item_id)
        if not normalized_id or normalized_id in seen:
            continue
        seen.add(normalized_id)

        if normalized_id in lookup:
            result.append(dict(lookup[normalized_id]))
            continue

        area_key = _resolve_classification_area(normalized_id)
        result.append({
            'id': normalized_id,
            'area_key': area_key,
            'area_label': _classification_area_label(area_key, lang),
            'label': normalized_id,
            'is_custom': False
        })
    return result


def _group_submission_classifications(classification_items):
    grouped = []
    for area_key in CLASSIFICATION_AREA_ORDER:
        area_items = [item for item in classification_items if item.get('area_key') == area_key]
        if area_items:
            grouped.append({
                'area_key': area_key,
                'area_label': area_items[0].get('area_label', area_key),
                'items': area_items
            })

    extra_area_keys = []
    for item in classification_items:
        area_key = item.get('area_key')
        if area_key and area_key not in CLASSIFICATION_AREA_ORDER and area_key not in extra_area_keys:
            extra_area_keys.append(area_key)

    for area_key in extra_area_keys:
        area_items = [item for item in classification_items if item.get('area_key') == area_key]
        if area_items:
            grouped.append({
                'area_key': area_key,
                'area_label': area_items[0].get('area_label', area_key),
                'items': area_items
            })

    return grouped


def _normalize_workflow_stage(stage):
    if stage is None:
        return None
    normalized = str(stage).strip().lower()
    return normalized if normalized in WORKFLOW_STAGE_KEYS else None


def _infer_workflow_stage(submission):
    stage = _normalize_workflow_stage(submission.get('workflow_stage'))
    if stage:
        return stage

    status = (submission.get('status') or '').strip().lower()
    editor_status = (submission.get('editor_review_status') or '').strip().lower()
    if status == 'published':
        return 'published'
    if status == 'rejected':
        return 'rejected'
    if status in ('submitted', 'pending'):
        return 'waiting'
    if status in ('in_process', 'under_review'):
        if editor_status in ('approved', 'reviewed'):
            return 'recommended'
        if editor_status in ('in_review', 'assigned'):
            return 'in_review'
        return 'technical_check'
    if status == 'paid':
        return 'payment'
    if status == 'accepted':
        return 'recommended'
    return 'waiting'


def _ensure_submission_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('submissions', []))
        if not existing_columns:
            return

        missing_columns = [name for name in SUBMISSION_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        if not missing_columns:
            return

        cursor = db.conn.cursor()
        for column_name in missing_columns:
            column_type = SUBMISSION_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE submissions ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception as e:
        logger.warning("Submission columns sync warning: %s", e)
        try:
            db.conn.rollback()
        except Exception:
            pass

def _ensure_user_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('users', []))
        if not existing_columns:
            return

        missing_columns = [name for name in USER_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        cursor = db.conn.cursor()
        for column_name in missing_columns:
            column_type = USER_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        # Keep visibility flags consistent for legacy rows where values might stay NULL.
        cursor.execute("UPDATE users SET is_hidden = FALSE WHERE is_hidden IS NULL;")
        cursor.execute("UPDATE users SET is_blocked = FALSE WHERE is_blocked IS NULL;")
        cursor.execute("ALTER TABLE users ALTER COLUMN is_hidden SET DEFAULT FALSE;")
        cursor.execute("ALTER TABLE users ALTER COLUMN is_blocked SET DEFAULT FALSE;")
        cursor.execute("ALTER TABLE users ALTER COLUMN is_hidden SET NOT NULL;")
        cursor.execute("ALTER TABLE users ALTER COLUMN is_blocked SET NOT NULL;")
        if 'roles' in existing_columns or 'roles' in missing_columns:
            cursor.execute(
                "UPDATE users "
                "SET roles = ARRAY[LOWER(COALESCE(NULLIF(TRIM(rolename), ''), 'user'))]::text[] "
                "WHERE roles IS NULL OR COALESCE(array_length(roles, 1), 0) = 0;"
            )
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception as e:
        logger.warning("Users columns sync warning: %s", e)
        try:
            db.conn.rollback()
        except Exception:
            pass

def _ensure_editor_assignment_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('editor_assignments', []))
        if not existing_columns:
            return

        missing_columns = [name for name in EDITOR_ASSIGNMENT_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        if not missing_columns:
            return

        cursor = db.conn.cursor()
        for column_name in missing_columns:
            column_type = EDITOR_ASSIGNMENT_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE editor_assignments ADD COLUMN IF NOT EXISTS {column_name} {column_type};")

        if 'admin_decision' in missing_columns:
            cursor.execute("UPDATE editor_assignments SET admin_decision = 'pending' WHERE admin_decision IS NULL;")
        if 'completion_deadline_at' in missing_columns:
            cursor.execute(
                "UPDATE editor_assignments "
                "SET completion_deadline_at = deadline_at "
                "WHERE completion_deadline_at IS NULL AND deadline_at IS NOT NULL;"
            )
        if 'acceptance_reminder_level' in missing_columns:
            cursor.execute("UPDATE editor_assignments SET acceptance_reminder_level = '' WHERE acceptance_reminder_level IS NULL;")
        if 'completion_reminder_level' in missing_columns:
            cursor.execute("UPDATE editor_assignments SET completion_reminder_level = '' WHERE completion_reminder_level IS NULL;")
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception as e:
        logger.warning("Editor assignments columns sync warning: %s", e)
        try:
            db.conn.rollback()
        except Exception:
            pass


def _ensure_publication_metadata_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('publications', []))
        if not existing_columns:
            return

        missing_columns = [name for name in PUBLICATION_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        if not missing_columns:
            return

        cursor = db.conn.cursor()
        for column_name in missing_columns:
            column_type = PUBLICATION_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE publications ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception as e:
        logger.warning("Publications metadata columns sync warning: %s", e)
        try:
            db.conn.rollback()
        except Exception:
            pass


def _ensure_issue_columns():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        existing_columns = set(db.columns.get('issues', []))
        if not existing_columns:
            return

        missing_columns = [name for name in ISSUE_EXTRA_COLUMN_TYPES.keys() if name not in existing_columns]
        if not missing_columns:
            return

        cursor = db.conn.cursor()
        for column_name in missing_columns:
            column_type = ISSUE_EXTRA_COLUMN_TYPES[column_name]
            cursor.execute(f"ALTER TABLE issues ADD COLUMN IF NOT EXISTS {column_name} {column_type};")
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception as e:
        logger.warning("Issues columns sync warning: %s", e)
        try:
            db.conn.rollback()
        except Exception:
            pass

def _ensure_role_notifications_table():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS role_notifications (
                id SERIAL PRIMARY KEY,
                target_user_id INTEGER,
                target_role TEXT,
                actor_user_id INTEGER,
                event_type TEXT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                level TEXT DEFAULT 'info',
                action_url TEXT,
                related_submission_id INTEGER,
                related_assignment_id INTEGER,
                metadata_text TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at BIGINT DEFAULT EXTRACT(epoch FROM now()),
                read_at BIGINT
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_target_user ON role_notifications(target_user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_target_role ON role_notifications(target_role);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_unread ON role_notifications(is_read, created_at DESC);")
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception as e:
        logger.warning("Role notifications table sync warning: %s", e)
        try:
            db.conn.rollback()
        except Exception:
            pass

def _ensure_editorial_members_table():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS editorial_members (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                position TEXT,
                organization TEXT,
                biography TEXT,
                image TEXT,
                member_type TEXT DEFAULT 'editor',
                email TEXT,
                orcid TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at BIGINT DEFAULT EXTRACT(epoch FROM now()),
                updated_at BIGINT,
                created_by INTEGER,
                updated_by INTEGER
            );
            """
        )
        multilingual_columns = {
            'full_name_uz': 'TEXT',
            'full_name_ru': 'TEXT',
            'position_uz': 'TEXT',
            'position_ru': 'TEXT',
            'organization_uz': 'TEXT',
            'organization_ru': 'TEXT',
            'biography_uz': 'TEXT',
            'biography_ru': 'TEXT',
        }
        for col_name, col_type in multilingual_columns.items():
            cursor.execute(f"ALTER TABLE editorial_members ADD COLUMN IF NOT EXISTS {col_name} {col_type};")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_editorial_members_active ON editorial_members(is_active);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_editorial_members_sort ON editorial_members(sort_order, id DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_editorial_members_type ON editorial_members(member_type);")
        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
    except Exception as e:
        logger.warning("Editorial members table sync warning: %s", e)
        try:
            db.conn.rollback()
        except Exception:
            pass


def _ensure_email_templates_table(force=False):
    if not force and not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        existing_tables = set(getattr(db, 'tables', []) or [])
        return 'email_templates' in existing_tables
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS email_templates (
                id SERIAL PRIMARY KEY,
                alias TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                variables TEXT[] DEFAULT '{}'::text[],
                subject_uz TEXT,
                subject_ru TEXT,
                subject_en TEXT,
                intro_uz TEXT,
                intro_ru TEXT,
                intro_en TEXT,
                body_uz TEXT,
                body_ru TEXT,
                body_en TEXT,
                cta_label_uz TEXT,
                cta_label_ru TEXT,
                cta_label_en TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at BIGINT DEFAULT EXTRACT(epoch FROM now()),
                updated_at BIGINT,
                created_by INTEGER,
                updated_by INTEGER
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_templates_alias ON email_templates(alias);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_templates_active ON email_templates(is_active);")

        now_ts = int(time.time())
        for item in EMAIL_TEMPLATE_DEFAULTS:
            cursor.execute(
                """
                INSERT INTO email_templates (
                    alias, name, description, variables,
                    subject_uz, subject_ru, subject_en,
                    intro_uz, intro_ru, intro_en,
                    body_uz, body_ru, body_en,
                    cta_label_uz, cta_label_ru, cta_label_en,
                    is_active, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (alias) DO NOTHING
                """,
                (
                    item['alias'],
                    item['name'],
                    item['description'],
                    item['variables'],
                    item['subject_uz'],
                    item['subject_ru'],
                    item['subject_en'],
                    item['intro_uz'],
                    item['intro_ru'],
                    item['intro_en'],
                    item['body_uz'],
                    item['body_ru'],
                    item['body_en'],
                    item['cta_label_uz'],
                    item['cta_label_ru'],
                    item['cta_label_en'],
                    True,
                    now_ts,
                    now_ts,
                ),
            )

        db.conn.commit()
        cursor.close()
        db._init_tables()
        db._init_columns()
        existing_tables = set(getattr(db, 'tables', []) or [])
        return 'email_templates' in existing_tables
    except Exception as e:
        logger.warning("Email templates table sync warning: %s", e)
        try:
            db.conn.rollback()
        except Exception:
            pass
        existing_tables = set(getattr(db, 'tables', []) or [])
        return 'email_templates' in existing_tables


def _ensure_email_templates_ready(force_schema_sync=False):
    return bool(_ensure_email_templates_table(force=force_schema_sync))


def run_runtime_schema_syncs():
    if not settings.RUNTIME_SCHEMA_SYNC_ENABLED:
        return
    _ensure_tariff_duration_column()
    _ensure_tariff_archive_column()
    _ensure_tariff_entitlement_columns()
    _ensure_payment_snapshot_columns()
    _ensure_user_doc_upload_columns()
    _ensure_submission_columns()
    _ensure_user_columns()
    _ensure_editor_assignment_columns()
    _ensure_publication_metadata_columns()
    _ensure_issue_columns()
    _ensure_role_notifications_table()
    _ensure_editorial_members_table()
    _ensure_email_templates_table()


def _normalize_notification_level(level):
    normalized = _clean_text(level).lower()
    if normalized in ROLE_NOTIFICATION_LEVELS:
        return normalized
    return 'info'


def _create_role_notification(
    target_user_id=None,
    target_role=None,
    title=None,
    message=None,
    action_url=None,
    level='info',
    event_type=None,
    related_submission_id=None,
    related_assignment_id=None,
    actor_user_id=None,
    metadata_text=None
):
    title_text, message_text, metadata_text_value = prepare_notification_content(
        title=title,
        message=message,
        metadata_text=metadata_text,
        default_language='uz'
    )
    target_user_id_int = _parse_int(target_user_id)
    target_role_text = _clean_text(target_role)
    actor_user_id_int = _parse_int(actor_user_id)

    if not title_text or not message_text:
        return None
    if target_user_id_int is None and not target_role_text:
        return None

    stored_target_role = target_role_text.lower() if target_role_text else None
    # If a specific user is targeted, don't broadcast by role.
    if target_user_id_int is not None and stored_target_role != 'all':
        stored_target_role = None

    event_type_text = _clean_text(event_type)
    action_url_text = _clean_text(action_url)
    related_submission_id_int = _parse_int(related_submission_id)
    related_assignment_id_int = _parse_int(related_assignment_id)
    now_ts = int(datetime.datetime.now().timestamp())

    dedup_query = (
        "SELECT id FROM role_notifications "
        "WHERE COALESCE(target_user_id, -1) = COALESCE(%s, -1) "
        "AND COALESCE(target_role, '') = COALESCE(%s, '') "
        "AND COALESCE(event_type, '') = COALESCE(%s, '') "
        "AND COALESCE(related_submission_id, -1) = COALESCE(%s, -1) "
        "AND COALESCE(related_assignment_id, -1) = COALESCE(%s, -1) "
        "AND COALESCE(action_url, '') = COALESCE(%s, '') "
        "AND title = %s AND message = %s "
        "AND created_at >= %s LIMIT 1"
    )
    dedup_args = (
        target_user_id_int,
        stored_target_role,
        event_type_text,
        related_submission_id_int,
        related_assignment_id_int,
        action_url_text,
        title_text,
        message_text,
        now_ts - 120
    )
    try:
        cursor = db.conn.cursor()
        cursor.execute(dedup_query, dedup_args)
        existing_row = cursor.fetchone()
        cursor.close()
        if existing_row:
            return _parse_int(existing_row[0])
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass

    payload = {
        'target_user_id': target_user_id_int,
        'target_role': stored_target_role,
        'actor_user_id': actor_user_id_int,
        'event_type': event_type_text,
        'title': title_text,
        'message': message_text,
        'level': _normalize_notification_level(level),
        'action_url': action_url_text,
        'related_submission_id': related_submission_id_int,
        'related_assignment_id': related_assignment_id_int,
        'metadata_text': metadata_text_value,
        'is_read': False,
        'created_at': now_ts
    }
    created = db.role_notifications.add(**payload).exec()
    return _extract_inserted_id(created)


def _active_users_by_role(role_name):
    return _users_with_role(role_name, include_hidden=False, include_blocked=False)


def _notify_role_users(
    role_name,
    title,
    message,
    action_url=None,
    level='info',
    event_type=None,
    related_submission_id=None,
    related_assignment_id=None,
    actor_user_id=None,
    exclude_user_ids=None
):
    excluded = {_parse_int(item) for item in (exclude_user_ids or []) if _parse_int(item) is not None}
    for user in _active_users_by_role(role_name):
        target_id = _parse_int(user.get('id'))
        if target_id is None or target_id in excluded:
            continue
        _create_role_notification(
            target_user_id=target_id,
            target_role=role_name,
            title=title,
            message=message,
            action_url=action_url,
            level=level,
            event_type=event_type,
            related_submission_id=related_submission_id,
            related_assignment_id=related_assignment_id,
            actor_user_id=actor_user_id
        )


def _fetch_role_notifications_for_user(current_user, only_unread=False, limit=20):
    safe_limit = max(1, min(_parse_int(limit) or 20, 100))
    return _fetch_role_notifications_page(current_user, only_unread=only_unread, page=1, per_page=safe_limit)


def _fetch_role_notifications_page(current_user, only_unread=False, page=1, per_page=20):
    access_clause, access_args = _role_notification_access_clause(current_user)
    if not access_clause:
        return []

    safe_page = max(_parse_int(page) or 1, 1)
    safe_per_page = max(1, min(_parse_int(per_page) or 20, 100))
    safe_offset = (safe_page - 1) * safe_per_page
    query = (
        "SELECT id, target_user_id, target_role, actor_user_id, event_type, title, message, level, action_url, "
        "related_submission_id, related_assignment_id, metadata_text, is_read, created_at, read_at "
        "FROM role_notifications "
        f"WHERE {access_clause} "
        "AND (%s = FALSE OR is_read = FALSE) "
        "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    )
    args = tuple(access_args) + (bool(only_unread), safe_per_page, safe_offset)
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, args)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        return [apply_localized_notification_content(dict(zip(columns, row))) for row in rows]
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return []


def _count_role_notifications(current_user):
    access_clause, access_args = _role_notification_access_clause(current_user)
    if not access_clause:
        return 0

    query = (
        "SELECT COUNT(*) FROM role_notifications "
        f"WHERE {access_clause}"
    )
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, tuple(access_args))
        result = cursor.fetchone()
        cursor.close()
        return int(result[0] or 0) if result else 0
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return 0


def _count_unread_role_notifications(current_user):
    access_clause, access_args = _role_notification_access_clause(current_user)
    if not access_clause:
        return 0

    query = (
        "SELECT COUNT(*) FROM role_notifications "
        "WHERE is_read = FALSE "
        f"AND {access_clause}"
    )
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, tuple(access_args))
        result = cursor.fetchone()
        cursor.close()
        return int(result[0] or 0) if result else 0
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return 0


def _mark_role_notification_as_read(notification_id, current_user):
    access_clause, access_args = _role_notification_access_clause(current_user)
    notification_id_int = _parse_int(notification_id)
    if not access_clause or notification_id_int is None:
        return False

    query = (
        "UPDATE role_notifications "
        "SET is_read = TRUE, read_at = %s "
        "WHERE id = %s AND is_read = FALSE "
        f"AND {access_clause}"
    )
    now_ts = int(datetime.datetime.now().timestamp())
    args = (now_ts, notification_id_int, *access_args)
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, args)
        changed = cursor.rowcount
        db.conn.commit()
        cursor.close()
        return changed > 0
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return False


def _mark_all_role_notifications_as_read(current_user):
    access_clause, access_args = _role_notification_access_clause(current_user)
    if not access_clause:
        return 0

    query = (
        "UPDATE role_notifications "
        "SET is_read = TRUE, read_at = %s "
        "WHERE is_read = FALSE "
        f"AND {access_clause}"
    )
    now_ts = int(datetime.datetime.now().timestamp())
    args = (now_ts, *access_args)
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, args)
        changed = cursor.rowcount
        db.conn.commit()
        cursor.close()
        return changed
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return 0


def _get_role_notification_for_user(notification_id, current_user):
    access_clause, access_args = _role_notification_access_clause(current_user)
    notification_id_int = _parse_int(notification_id)
    if not access_clause or notification_id_int is None:
        return None

    query = (
        "SELECT id, target_user_id, target_role, actor_user_id, event_type, title, message, level, action_url, "
        "related_submission_id, related_assignment_id, metadata_text, is_read, created_at, read_at "
        "FROM role_notifications "
        f"WHERE id = %s AND {access_clause} "
        "LIMIT 1"
    )
    args = (notification_id_int, *access_args)
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, args)
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        if not row:
            return None
        return apply_localized_notification_content(dict(zip(columns, row)))
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return None


def _submission_title(submission):
    title = _clean_text((submission or {}).get('title'))
    return title or f'ID: {_parse_int((submission or {}).get("id")) or "-"}'


def _user_display_name(user_row):
    full_name = _clean_text(f"{(user_row or {}).get('name') or ''} {(user_row or {}).get('second_name') or ''}")
    return full_name or _clean_text((user_row or {}).get('name')) or _clean_text((user_row or {}).get('email'))


def _resolve_localized_text(value, user_row=None):
    if isinstance(value, dict):
        preferred = normalize_notification_language(
            (user_row or {}).get('ui_language'),
            default=current_notification_language()
        )
        fallback_order = [preferred, 'uz', 'ru', 'en']
        for language in fallback_order:
            text = _clean_text(value.get(language))
            if text:
                return text
        for text in value.values():
            resolved = _clean_text(text)
            if resolved:
                return resolved
        return ''
    return _clean_text(value)


def _normalize_localized_details(details, user_row=None):
    normalized = []
    for label, value in details or []:
        label_text = _resolve_localized_text(label, user_row=user_row)
        value_text = _resolve_localized_text(value, user_row=user_row)
        if not label_text or not value_text:
            continue
        normalized.append((label_text, value_text))
    return normalized


def _normalize_localized_body_lines(body_lines, user_row=None):
    normalized = []
    for line in body_lines or []:
        line_text = _resolve_localized_text(line, user_row=user_row)
        if line_text:
            normalized.append(line_text)
    return normalized


def _send_user_email(
    user_row,
    subject,
    intro,
    details=None,
    body_lines=None,
    cta_url=None,
    cta_label=None,
    reply_to=None,
    template_alias=None,
    template_vars=None,
):
    email = _clean_text((user_row or {}).get('email'))
    if not email or not user_allows_email_notifications(user_row):
        return False
    preferred_language = normalize_notification_language(
        (user_row or {}).get('ui_language'),
        default=current_notification_language()
    )
    subject_text, intro_text, _ = prepare_notification_content(
        title=subject,
        message=intro,
        default_language=preferred_language
    )
    details_rows = _normalize_localized_details(details, user_row=user_row)
    body_rows = _normalize_localized_body_lines(body_lines, user_row=user_row)
    cta_label_text = _resolve_localized_text(cta_label, user_row=user_row) or 'Open'
    return send_notification_email(
        recipients=[email],
        subject=subject_text,
        intro=intro_text,
        details=details_rows,
        body_lines=body_rows,
        cta_url=cta_url,
        cta_label=cta_label_text,
        reply_to=reply_to,
        fail_silently=True,
        template_alias=template_alias,
        template_vars=template_vars,
        preferred_language=preferred_language,
    )


def new_alert(message, category='info'):
    flash(message, category)


def _ui_language():
    language = _clean_text(session.get('language') or 'uz').lower()
    if language in {'uz', 'ru', 'en'}:
        return language
    return 'uz'


def _msg_text(uz_text, ru_text=None, en_text=None):
    language = _ui_language()
    if language == 'ru':
        return ru_text or uz_text
    if language == 'en':
        return en_text or uz_text
    return uz_text


STATUS_LABEL_TRANSLATIONS = {
    'draft': {'uz': 'Qoralama', 'ru': 'Черновик', 'en': 'Draft'},
    'submitted': {'uz': 'Yuborilgan', 'ru': 'Отправлено', 'en': 'Submitted'},
    'pending': {'uz': 'Kutilmoqda', 'ru': 'Ожидает', 'en': 'Pending'},
    'in_process': {'uz': 'Jarayonda', 'ru': 'В процессе', 'en': 'In process'},
    'under_review': {'uz': "Ko'rib chiqilmoqda", 'ru': 'На рассмотрении', 'en': 'Under review'},
    'accepted': {'uz': 'Qabul qilingan', 'ru': 'Принято', 'en': 'Accepted'},
    'published': {'uz': 'Nashr qilindi', 'ru': 'Опубликовано', 'en': 'Published'},
    'rejected': {'uz': 'Rad etilgan', 'ru': 'Отклонено', 'en': 'Rejected'},
    'paid': {'uz': "To'lov qilingan", 'ru': 'Оплачено', 'en': 'Paid'}
}

WORKFLOW_STAGE_LABEL_TRANSLATIONS = {
    'waiting': {'uz': 'Kutilmoqda', 'ru': 'Ожидание', 'en': 'Waiting'},
    'technical_check': {'uz': 'Texnik tekshiruv', 'ru': 'Техническая проверка', 'en': 'Technical check'},
    'anti_plagiarism': {'uz': 'Antiplagiat tekshiruvi', 'ru': 'Проверка на антиплагиат', 'en': 'Anti-plagiarism check'},
    'in_review': {'uz': 'Taqrizda', 'ru': 'На рецензии', 'en': 'In review'},
    'recommended': {'uz': "Nashrga tavsiya etildi", 'ru': 'Рекомендовано к публикации', 'en': 'Recommended'},
    'payment': {'uz': "To'lov", 'ru': 'Оплата', 'en': 'Payment'},
    'published': {'uz': 'Nashr qilindi', 'ru': 'Опубликовано', 'en': 'Published'},
    'rejected': {'uz': 'Rad etilgan', 'ru': 'Отклонено', 'en': 'Rejected'}
}


def _status_label_text(status, lang='uz'):
    key = _clean_text(status).lower()
    if not key:
        return '-'
    return STATUS_LABEL_TRANSLATIONS.get(key, {}).get(lang, key)


def _workflow_stage_label_text(stage, lang='uz'):
    key = _clean_text(stage).lower()
    if not key:
        return '-'
    return WORKFLOW_STAGE_LABEL_TRANSLATIONS.get(key, {}).get(lang, key)


def _status_stage_change_message(submission_title, new_status, new_stage):
    return localized_texts(
        f'"{submission_title}" yangilandi. Holat: {_status_label_text(new_status, "uz")}. Bosqich: {_workflow_stage_label_text(new_stage, "uz")}.',
        f'"{submission_title}" обновлена. Статус: {_status_label_text(new_status, "ru")}. Этап: {_workflow_stage_label_text(new_stage, "ru")}.',
        f'"{submission_title}" was updated. Status: {_status_label_text(new_status, "en")}. Stage: {_workflow_stage_label_text(new_stage, "en")}.',
    )


def _privileged_role(role_name):
    return role_name in {'admin', 'editor', 'superadmin'}


def _role_of(user):
    return primary_role(user)


def _load_user_from_db(user_id):
    if not user_id:
        return None
    try:
        rows = db.users.all().equal(id=user_id).exec()
    except Exception:
        return None
    return rows[0] if rows else None


def _current_user_with_details():
    session_user = session.get('fmadmin_user') or {}
    user_id = _parse_int(session_user.get('id'))
    if not user_id:
        return hydrate_user_roles(session_user)
    db_user = _load_user_from_db(user_id)
    if not db_user:
        return hydrate_user_roles(session_user)
    merged = dict(session_user)
    merged.update(db_user)
    return hydrate_user_roles(merged)


def _session_admin_user_payload(user_row):
    hydrated_user = hydrate_user_roles(user_row)
    return {
        'id': hydrated_user.get('id'),
        'name': hydrated_user.get('name'),
        'email': hydrated_user.get('email'),
        'ui_language': normalize_notification_language(hydrated_user.get('ui_language'), default=session.get('language') or 'uz'),
        'rolename': primary_role(hydrated_user),
        'roles': hydrated_user.get('roles'),
        'permissions': hydrated_user.get('permissions'),
        'capabilities': hydrated_user.get('capabilities'),
        'editor_specialization': hydrated_user.get('editor_specialization'),
        'admin_tracks': hydrated_user.get('admin_tracks'),
        'editor_admin_id': hydrated_user.get('editor_admin_id')
    }


def _active_admins():
    return _users_with_role('admin', include_hidden=False, include_blocked=False)


def _submission_track_label(track):
    normalized_track = _normalize_admin_track(track)
    return ADMIN_TRACK_LABELS.get(normalized_track, normalized_track or t("admin_label_not_specified"))


def _can_access_submission(current_user, submission):
    if user_has_role(current_user, 'superadmin'):
        return True
    if not user_has_role(current_user, 'admin'):
        return False

    current_user_id = _parse_int(current_user.get('id'))
    if current_user_id is None:
        return False

    assigned_admin_id = _parse_int((submission or {}).get('assigned_admin_id'))
    if assigned_admin_id is not None:
        return assigned_admin_id == current_user_id

    # Fallback for legacy rows where admin is not assigned yet.
    return _user_has_track_access(current_user, (submission or {}).get('submission_track'))


def _redirect_to_role_dashboard(user=None):
    user_data = user or session.get('fmadmin_user') or {}
    role = primary_role(user_data)
    if role == 'editor':
        return redirect(url_for('editor_dashboard'))
    return redirect(url_for('index'))


@bp.route('/fmadmin/lang/<lang_code>', methods=['POST'])
def set_language(lang_code):
    if lang_code in ['en', 'ru', 'uz']:
        session['language'] = lang_code
        fmadmin_user = session.get('fmadmin_user') or {}
        user_id = _parse_int(fmadmin_user.get('id'))
        if user_id is not None:
            try:
                db.users.all().equal(id=user_id).update(ui_language=lang_code).exec()
            except Exception:
                try:
                    db.conn.rollback()
                except Exception:
                    pass
            fmadmin_user['ui_language'] = lang_code
            session['fmadmin_user'] = fmadmin_user
    return redirect(_safe_internal_redirect(request.form.get('redirect_url') or request.referrer, 'index'))

@bp.route('/fmadmin/')
@is_admin_or_editor
def index():
    current_user = session.get('fmadmin_user') or {}
    if current_user.get('rolename') == 'editor':
        return redirect(url_for('editor_dashboard'))

    dashboard_snapshot = get_dashboard_snapshot(months=6, recent_limit=6, top_limit=6, stale_days=14)

    return render_template(
        'index.html',
        stats=dashboard_snapshot.get('stats', {}),
        status_chart=dashboard_snapshot.get('status_chart', {}),
        timeline_chart=dashboard_snapshot.get('timeline_chart', {}),
        workflow_cards=dashboard_snapshot.get('workflow_cards', []),
        attention_submissions=dashboard_snapshot.get('attention_submissions', []),
        recent_submissions=dashboard_snapshot.get('recent_submissions', []),
        top_articles=dashboard_snapshot.get('top_articles', []),
        can_run_assignment_automation=user_has_permission(current_user, 'fmadmin.submissions.manage'),
    )


@bp.route('/fmadmin/automation/editor-assignments/run', methods=['POST'])
@is_allowed
def run_editor_assignment_automation_now():
    actor_user_id = _parse_int((session.get('fmadmin_user') or {}).get('id'))
    result = run_editor_assignment_automation(actor_user_id=actor_user_id, force=True)

    if result.get('skipped'):
        flash('Automation skip qilindi (interval chegarasi).', 'warning')
    else:
        flash(
            (
                'Automation bajarildi: '
                f"processed={result.get('processed', 0)}, "
                f"expired={result.get('expired', 0)}, "
                f"reminders={result.get('reminders', 0)}"
            ),
            'success'
        )
    return redirect(_safe_internal_redirect(request.referrer, 'index'))


@bp.route('/fmadmin/editor/dashboard')
@is_editor_allowed
def editor_dashboard():
    current_user = session.get('fmadmin_user') or {}
    if current_user.get('rolename') in ['admin', 'superadmin']:
        return redirect(url_for('index'))

    editor_id = current_user.get('id')
    if not editor_id:
        flash(t('admin_error_no_access'), 'danger')
        _clear_admin_session()
        return redirect(url_for('login'))

    try:
        assignments = db.editor_assignments.all().equal(editor_id=editor_id).order_by('assigned_at').exec()
    except Exception:
        assignments = []

    assignments = [_decorate_assignment(item) for item in assignments]
    assignments = sorted(assignments, key=lambda item: _parse_int(item.get('assigned_at')) or 0, reverse=True)
    stats = _assignment_stats(assignments)

    submission_ids = list({a.get('submission_id') for a in assignments if a.get('submission_id')})
    submissions_map = {}
    if submission_ids:
        try:
            submissions = db.submissions.all().any(id=submission_ids).exec()
        except Exception:
            submissions = db.submissions.all().exec()
        submissions_map = {s.get('id'): s for s in submissions if s.get('id')}

    recent_assignments = []
    for assignment in assignments[:8]:
        submission = submissions_map.get(assignment.get('submission_id')) or {}
        recent_assignments.append({
            'id': assignment.get('id'),
            'submission_id': assignment.get('submission_id'),
            'submission_title': submission.get('title') or f"ID: {assignment.get('submission_id')}",
            'status': assignment.get('status') or 'pending',
            'assigned_at': assignment.get('assigned_at'),
            'reviewed_at': assignment.get('reviewed_at'),
        })

    unread_notifications = _count_unread_role_notifications(current_user)

    return render_template(
        'editors/dashboard.html',
        current_user=current_user,
        stats=stats,
        recent_assignments=recent_assignments,
        unread_notifications=unread_notifications
    )

@bp.route('/fmadmin/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже авторизован, перенаправляем на главную
    if 'fmadmin_user' in session and user_has_permission(session['fmadmin_user'], 'fmadmin.access'):
        return _redirect_to_role_dashboard()

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password')

        if not email or not password:
            flash(t('admin_error_fill_all_fields'), 'danger')
            return render_template('auth/login.html')

        remaining_lock = _remaining_login_lock_seconds(email)
        if remaining_lock > 0:
            flash(f"Juda ko'p noto'g'ri urinish. {remaining_lock} soniyadan keyin qayta urinib ko'ring.", 'danger')
            return render_template('auth/login.html')

        user = db.users.all().equal(email=email).exec()
        if not user:
            remaining_lock = _record_login_failure(email)
            if remaining_lock > 0:
                flash(f"Juda ko'p noto'g'ri urinish. {remaining_lock} soniyadan keyin qayta urinib ko'ring.", 'danger')
            else:
                flash(t('admin_error_invalid_credentials'), 'danger')
            return render_template('auth/login.html')

        from werkzeug.security import check_password_hash, generate_password_hash
        user = user[0]

        # Проверяем пароль
        password_valid = False
        stored_password = user.get('password')
        
        if stored_password and stored_password.startswith(('pbkdf2:', 'scrypt:')):
            password_valid = check_password_hash(stored_password, password)
        else:
            # Plain text comparison
            password_valid = (stored_password == password)
            if password_valid:
                # Auto-migrate to hash
                hashed = generate_password_hash(password)
                db.users.all().equal(id=user['id']).update(password=hashed).exec()

        if not password_valid:
            remaining_lock = _record_login_failure(email)
            if remaining_lock > 0:
                flash(f"Juda ko'p noto'g'ri urinish. {remaining_lock} soniyadan keyin qayta urinib ko'ring.", 'danger')
            else:
                flash(t('admin_error_invalid_credentials'), 'danger')
            return render_template('auth/login.html')

        if user.get('is_blocked') or user.get('is_hidden'):
            _record_login_failure(email)
            flash(t('admin_error_no_access'), 'danger')
            return render_template('auth/login.html')

        # Проверяем роль (только админы и редакторы)
        user = hydrate_user_roles(user)
        if not user_has_permission(user, 'fmadmin.access'):
            _record_login_failure(email)
            flash(t('admin_error_no_access'), 'danger')
            return render_template('auth/login.html')

        _clear_login_failures(email)

        # Сохраняем пользователя в сессии
        session['fmadmin_user'] = _session_admin_user_payload(user)
        session['language'] = normalize_notification_language(user.get('ui_language'), default=session.get('language') or 'uz')

        flash(f"{t('admin_welcome_body')}, {user['name']}!", 'success')
        return _redirect_to_role_dashboard(session['fmadmin_user'])

    return render_template('auth/login.html')

@bp.route('/fmadmin/logout', methods=['POST'])
def logout():
    _clear_admin_session()
    flash(t('admin_success_logout'), 'info')
    return redirect(url_for('login'))

@bp.route('/fmadmin/users/users')
@is_superadmin_required
def users():
    current_user = hydrate_user_roles(session.get('fmadmin_user') or {})
    current_role = primary_role(current_user)

    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_name = request.args.get('name', '').strip()
    search_email = request.args.get('email', '').strip()
    search_orcid = request.args.get('orcid', '').strip()
    include_hidden = request.args.get('include_hidden') == '1' if current_role == 'superadmin' else False

    query = db.users.all().order_by('id')
    if not include_hidden:
        query = query.unequal(is_hidden=True)
    if current_role != 'superadmin':
        query = query.unequal(rolename='superadmin')
    if search_name:
        query = query.like(name=search_name)
    if search_email:
        query = query.like(email=search_email)

    total_users = query.copy().count().exec()
    users = [hydrate_user_roles(user) for user in query.per_page(per_page).page(page).exec()]
    total_pages = (total_users + per_page - 1) // per_page

    for user in users:
        user['has_author_role'] = user_has_role(user, AUTHOR_ROLE)
        user['admin_tracks_labels'] = _admin_tracks_label_list(user) if user_has_role(user, 'admin') else []

    author_profiles = db.author_profile.all().exec()
    author_map = {a['user_id']: a for a in author_profiles if a['user_id'] is not None}
    tariffs = db.tariffs.all().exec()
    tariffs_map = {t['id']: t for t in tariffs}
    admin_users = _active_admins()
    admin_map = {admin.get('id'): admin for admin in admin_users if admin.get('id')}

    return render_template('users/users/users.html', users=users, page=page, total_users=total_users, total_pages=total_pages,
                           search_name=search_name, search_email=search_email, search_orcid=search_orcid,
                           author_map=author_map, tariffs_map=tariffs_map,
                           include_hidden=include_hidden, current_user=current_user, admin_map=admin_map)


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {'1', 'true', 'on', 'yes'}


def _extract_inserted_id(result):
    if isinstance(result, list) and result:
        return result[0].get('id')
    if isinstance(result, dict):
        return result.get('id')
    if isinstance(result, int):
        return result
    return None


def _allowed_roles_for_actor(actor_role):
    roles = ['user', 'editor', 'admin']
    if actor_role == 'superadmin':
        roles.append('superadmin')
    return roles


def _query_rows_dicts(query, args=()):
    cursor = None
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, args)
        columns = [desc[0] for desc in (cursor.description or [])]
        rows = cursor.fetchall() if columns else []
        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return []
    finally:
        if cursor is not None:
            cursor.close()


def _editor_review_status_label_text(status, lang='uz'):
    labels = {
        'not_assigned': {'uz': "Biriktirilmagan", 'ru': "Не назначено", 'en': "Not assigned"},
        'assigned': {'uz': "Biriktirilgan", 'ru': "Назначено", 'en': "Assigned"},
        'in_review': {'uz': "Ko'rib chiqilmoqda", 'ru': "На проверке", 'en': "In review"},
        'reviewed': {'uz': "Ko'rib chiqildi", 'ru': "Проверено", 'en': "Reviewed"},
        'approved': {'uz': "Tasdiqlangan", 'ru': "Одобрено", 'en': "Approved"},
        'rejected': {'uz': "Rad etilgan", 'ru': "Отклонено", 'en': "Rejected"},
    }
    key = _clean_text(status).lower()
    if not key:
        return '-'
    return labels.get(key, {}).get(lang, key)


def _status_badge_tone(status, scope='submission'):
    normalized = _clean_text(status).lower()
    mappings = {
        'submission': {
            'published': 'green',
            'submitted': 'blue',
            'in_process': 'orange',
            'rejected': 'red',
            'draft': 'secondary',
            'under_review': 'yellow',
            'accepted': 'green',
        },
        'editor_review': {
            'approved': 'green',
            'reviewed': 'blue',
            'in_review': 'orange',
            'assigned': 'yellow',
            'not_assigned': 'secondary',
            'rejected': 'red',
        },
        'payment': {
            'paid': 'green',
            'pending': 'yellow',
            'rejected': 'red',
            'unpaid': 'secondary',
        },
        'notification': {
            'success': 'green',
            'warning': 'yellow',
            'danger': 'red',
            'info': 'blue',
        },
    }
    return mappings.get(scope, {}).get(normalized, 'secondary')


def _payment_type_label_text(payment_type):
    normalized = _clean_text(payment_type).lower()
    if normalized == 'subscription':
        return _msg_text("Obuna", "Подписка", "Subscription")
    if normalized == 'article':
        return _msg_text("Maqola", "Статья", "Article")
    if normalized == 'issue':
        return _msg_text("Son", "Выпуск", "Issue")
    return _msg_text("To'lov", "Платеж", "Payment")


def _format_money_short(amount, currency='UZS'):
    amount_value = _parse_amount(amount)
    if amount_value is None:
        return '-'
    currency_code = _clean_text(currency).upper() or 'UZS'
    if float(amount_value).is_integer():
        amount_text = f"{int(amount_value):,}".replace(',', ' ')
    else:
        amount_text = f"{amount_value:,.2f}".replace(',', ' ')
    return f"{amount_text} {currency_code}"


def _build_user_360_snapshot(user_row, timeline_limit=24):
    user_id = _parse_int((user_row or {}).get('id'))
    if not user_id:
        return None

    language = _ui_language()
    safe_timeline_limit = max(8, min(_parse_int(timeline_limit) or 24, 64))
    submissions_columns = set(db.columns.get('submissions', []) or [])
    has_submission_workflow_stage = 'workflow_stage' in submissions_columns

    snapshot = {
        'profile': {
            'author_profile': None,
            'documents_total': 0,
            'documents_verified': 0,
            'documents_pending': 0,
            'notifications_incoming': 0,
            'notifications_unread': 0,
            'notifications_outgoing': 0,
            'last_activity_at': None,
        },
        'submission_stats': {
            'total': 0,
            'published': 0,
            'active': 0,
            'rejected': 0,
            'status_breakdown': [],
            'review_breakdown': [],
            'recent': [],
            'first_created_at': None,
            'last_activity_at': None,
        },
        'payment_stats': {
            'total': 0,
            'paid': 0,
            'pending': 0,
            'rejected': 0,
            'unpaid': 0,
            'paid_amount': 0.0,
            'pending_amount': 0.0,
            'status_breakdown': [],
            'recent': [],
            'last_activity_at': None,
        },
        'timeline': [],
        'timeline_has_more': False,
    }

    author_profile_rows = _query_rows_dicts(
        "SELECT id, name, email, orcid, organization, position "
        "FROM author_profile WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    if author_profile_rows:
        snapshot['profile']['author_profile'] = author_profile_rows[0]

    doc_rows = _query_rows_dicts(
        "SELECT COUNT(*)::int AS total, "
        "SUM(CASE WHEN LOWER(COALESCE(verification_status, '')) IN ('verified', 'approved') THEN 1 ELSE 0 END)::int AS verified, "
        "SUM(CASE WHEN LOWER(COALESCE(verification_status, '')) = 'pending' THEN 1 ELSE 0 END)::int AS pending "
        "FROM user_doc_uploads WHERE user_id = %s",
        (user_id,),
    )
    if doc_rows:
        docs = doc_rows[0]
        snapshot['profile']['documents_total'] = _parse_int(docs.get('total')) or 0
        snapshot['profile']['documents_verified'] = _parse_int(docs.get('verified')) or 0
        snapshot['profile']['documents_pending'] = _parse_int(docs.get('pending')) or 0

    notifications_rows = _query_rows_dicts(
        "SELECT "
        "SUM(CASE WHEN target_user_id = %s THEN 1 ELSE 0 END)::int AS incoming_count, "
        "SUM(CASE WHEN target_user_id = %s AND is_read = FALSE THEN 1 ELSE 0 END)::int AS unread_incoming_count, "
        "SUM(CASE WHEN actor_user_id = %s THEN 1 ELSE 0 END)::int AS outgoing_count "
        "FROM role_notifications "
        "WHERE target_user_id = %s OR actor_user_id = %s",
        (user_id, user_id, user_id, user_id, user_id),
    )
    if notifications_rows:
        notifications = notifications_rows[0]
        snapshot['profile']['notifications_incoming'] = _parse_int(notifications.get('incoming_count')) or 0
        snapshot['profile']['notifications_unread'] = _parse_int(notifications.get('unread_incoming_count')) or 0
        snapshot['profile']['notifications_outgoing'] = _parse_int(notifications.get('outgoing_count')) or 0

    submission_status_rows = _query_rows_dicts(
        "SELECT COALESCE(status, '') AS status, COUNT(*)::int AS count "
        "FROM submissions WHERE user_id = %s "
        "GROUP BY COALESCE(status, '')",
        (user_id,),
    )
    submission_status_map = {}
    for row in submission_status_rows:
        key = _clean_text(row.get('status')).lower()
        submission_status_map[key] = _parse_int(row.get('count')) or 0

    submission_summary_rows = _query_rows_dicts(
        "SELECT MIN(created_date) AS first_created_at, MAX(COALESCE(updated_at, created_date)) AS last_activity_at "
        "FROM submissions WHERE user_id = %s",
        (user_id,),
    )
    if submission_summary_rows:
        summary = submission_summary_rows[0]
        snapshot['submission_stats']['first_created_at'] = _parse_int(summary.get('first_created_at'))
        snapshot['submission_stats']['last_activity_at'] = _parse_int(summary.get('last_activity_at'))

    submission_review_rows = _query_rows_dicts(
        "SELECT COALESCE(editor_review_status, '') AS review_status, COUNT(*)::int AS count "
        "FROM submissions WHERE user_id = %s "
        "GROUP BY COALESCE(editor_review_status, '')",
        (user_id,),
    )
    submission_review_map = {}
    for row in submission_review_rows:
        key = _clean_text(row.get('review_status')).lower()
        submission_review_map[key] = _parse_int(row.get('count')) or 0

    ordered_submission_statuses = ['submitted', 'in_process', 'published', 'rejected', 'draft']
    extra_submission_statuses = sorted(
        [key for key in submission_status_map.keys() if key and key not in ordered_submission_statuses]
    )
    for status_key in ordered_submission_statuses + extra_submission_statuses:
        count = submission_status_map.get(status_key, 0)
        if count <= 0:
            continue
        snapshot['submission_stats']['status_breakdown'].append({
            'key': status_key,
            'label': _status_label_text(status_key, language),
            'count': count,
            'tone': _status_badge_tone(status_key, 'submission'),
        })

    ordered_review_statuses = ['not_assigned', 'assigned', 'in_review', 'reviewed', 'approved', 'rejected']
    extra_review_statuses = sorted(
        [key for key in submission_review_map.keys() if key and key not in ordered_review_statuses]
    )
    for status_key in ordered_review_statuses + extra_review_statuses:
        count = submission_review_map.get(status_key, 0)
        if count <= 0:
            continue
        snapshot['submission_stats']['review_breakdown'].append({
            'key': status_key,
            'label': _editor_review_status_label_text(status_key, language),
            'count': count,
            'tone': _status_badge_tone(status_key, 'editor_review'),
        })

    submission_recent_columns = [
        'id',
        'title',
        'status',
        'editor_review_status',
        'created_date',
        'updated_at',
    ]
    if has_submission_workflow_stage:
        submission_recent_columns.append('workflow_stage')
    submission_recent_query = (
        f"SELECT {', '.join(submission_recent_columns)} "
        "FROM submissions WHERE user_id = %s "
        "ORDER BY COALESCE(updated_at, created_date) DESC NULLS LAST, id DESC "
        "LIMIT 6"
    )
    submission_recent_rows = _query_rows_dicts(submission_recent_query, (user_id,))
    for row in submission_recent_rows:
        submission_id = _parse_int(row.get('id'))
        created_at = _parse_int(row.get('created_date'))
        updated_at = _parse_int(row.get('updated_at'))
        activity_at = max(value for value in [updated_at, created_at] if value is not None) if (updated_at or created_at) else None
        status_key = _clean_text(row.get('status')).lower()
        review_key = _clean_text(row.get('editor_review_status')).lower()
        workflow_stage = _clean_text(row.get('workflow_stage')) if has_submission_workflow_stage else ''
        snapshot['submission_stats']['recent'].append({
            'id': submission_id,
            'title': _clean_text(row.get('title')) or f"ID: {submission_id or '-'}",
            'status': status_key,
            'status_label': _status_label_text(status_key, language),
            'status_tone': _status_badge_tone(status_key, 'submission'),
            'review_status': review_key,
            'review_label': _editor_review_status_label_text(review_key, language) if review_key else '',
            'review_tone': _status_badge_tone(review_key, 'editor_review'),
            'workflow_stage': workflow_stage,
            'workflow_stage_label': _workflow_stage_label_text(workflow_stage, language) if workflow_stage else '',
            'created_at': created_at,
            'updated_at': updated_at,
            'activity_at': activity_at,
        })

    snapshot['submission_stats']['total'] = sum(submission_status_map.values())
    snapshot['submission_stats']['published'] = submission_status_map.get('published', 0)
    snapshot['submission_stats']['active'] = (
        submission_status_map.get('submitted', 0)
        + submission_status_map.get('in_process', 0)
        + submission_status_map.get('under_review', 0)
    )
    snapshot['submission_stats']['rejected'] = submission_status_map.get('rejected', 0)

    payment_status_rows = _query_rows_dicts(
        "SELECT COALESCE(status, '') AS status, COUNT(*)::int AS count, "
        "COALESCE(SUM(COALESCE(amount, 0)), 0)::double precision AS amount_total "
        "FROM payments WHERE user_id = %s "
        "GROUP BY COALESCE(status, '')",
        (user_id,),
    )
    payment_status_map = {}
    payment_amount_map = {}
    for row in payment_status_rows:
        key = _clean_text(row.get('status')).lower()
        payment_status_map[key] = _parse_int(row.get('count')) or 0
        payment_amount_map[key] = float(row.get('amount_total') or 0)

    ordered_payment_statuses = ['paid', 'pending', 'rejected', 'unpaid']
    extra_payment_statuses = sorted(
        [key for key in payment_status_map.keys() if key and key not in ordered_payment_statuses]
    )
    for status_key in ordered_payment_statuses + extra_payment_statuses:
        count = payment_status_map.get(status_key, 0)
        if count <= 0:
            continue
        snapshot['payment_stats']['status_breakdown'].append({
            'key': status_key,
            'label': _status_label_text(status_key, language),
            'count': count,
            'amount': payment_amount_map.get(status_key, 0.0),
            'tone': _status_badge_tone(status_key, 'payment'),
        })

    payment_recent_rows = _query_rows_dicts(
        "SELECT id, status, payment_type, currency, amount, payment_date, created_at "
        "FROM payments WHERE user_id = %s "
        "ORDER BY COALESCE(payment_date, created_at) DESC NULLS LAST, id DESC "
        "LIMIT 6",
        (user_id,),
    )
    for row in payment_recent_rows:
        payment_id = _parse_int(row.get('id'))
        payment_date = _parse_int(row.get('payment_date'))
        created_at = _parse_int(row.get('created_at'))
        activity_at = max(value for value in [payment_date, created_at] if value is not None) if (payment_date or created_at) else None
        status_key = _clean_text(row.get('status')).lower()
        payment_type = _clean_text(row.get('payment_type')).lower()
        amount = _parse_amount(row.get('amount')) or 0
        currency = _clean_text(row.get('currency')).upper() or 'UZS'
        snapshot['payment_stats']['recent'].append({
            'id': payment_id,
            'status': status_key,
            'status_label': _status_label_text(status_key, language),
            'status_tone': _status_badge_tone(status_key, 'payment'),
            'payment_type': payment_type,
            'payment_type_label': _payment_type_label_text(payment_type),
            'amount': amount,
            'amount_text': _format_money_short(amount, currency),
            'currency': currency,
            'payment_date': payment_date,
            'created_at': created_at,
            'activity_at': activity_at,
        })

    payment_activity_rows = _query_rows_dicts(
        "SELECT MAX(COALESCE(payment_date, created_at)) AS last_activity_at "
        "FROM payments WHERE user_id = %s",
        (user_id,),
    )
    if payment_activity_rows:
        snapshot['payment_stats']['last_activity_at'] = _parse_int(payment_activity_rows[0].get('last_activity_at'))

    snapshot['payment_stats']['total'] = sum(payment_status_map.values())
    snapshot['payment_stats']['paid'] = payment_status_map.get('paid', 0)
    snapshot['payment_stats']['pending'] = payment_status_map.get('pending', 0)
    snapshot['payment_stats']['rejected'] = payment_status_map.get('rejected', 0)
    snapshot['payment_stats']['unpaid'] = payment_status_map.get('unpaid', 0)
    snapshot['payment_stats']['paid_amount'] = payment_amount_map.get('paid', 0.0)
    snapshot['payment_stats']['pending_amount'] = payment_amount_map.get('pending', 0.0)

    timeline_events = []
    register_time = _parse_int((user_row or {}).get('register_time'))
    accept_rules_time = _parse_int((user_row or {}).get('accept_rules_time'))
    last_online = _parse_int((user_row or {}).get('last_online'))
    if register_time:
        timeline_events.append({
            'timestamp': register_time,
            'icon': 'ti-user-plus',
            'title': _msg_text("Foydalanuvchi ro'yxatdan o'tdi", "Пользователь зарегистрирован", "User registered"),
            'subtitle': _clean_text((user_row or {}).get('email')),
            'tone': 'blue',
            'url': None,
        })
    if accept_rules_time:
        timeline_events.append({
            'timestamp': accept_rules_time,
            'icon': 'ti-shield-check',
            'title': _msg_text("Qoidalar qabul qilingan", "Правила приняты", "Rules accepted"),
            'subtitle': _msg_text("Platforma shartlari tasdiqlangan", "Подтверждены условия платформы", "Platform terms confirmed"),
            'tone': 'green',
            'url': None,
        })
    if last_online:
        timeline_events.append({
            'timestamp': last_online,
            'icon': 'ti-clock',
            'title': _msg_text("Oxirgi online", "Последний онлайн", "Last seen online"),
            'subtitle': _msg_text("Sessiya faolligi qayd etilgan", "Зафиксирована активность сессии", "Session activity detected"),
            'tone': 'secondary',
            'url': None,
        })

    timeline_submissions_rows = _query_rows_dicts(
        f"SELECT id, title, status, editor_review_status, created_date, updated_at{', workflow_stage' if has_submission_workflow_stage else ''} "
        "FROM submissions WHERE user_id = %s "
        "ORDER BY COALESCE(updated_at, created_date) DESC NULLS LAST, id DESC "
        "LIMIT %s",
        (user_id, safe_timeline_limit),
    )
    for row in timeline_submissions_rows:
        submission_id = _parse_int(row.get('id'))
        created_at = _parse_int(row.get('created_date'))
        updated_at = _parse_int(row.get('updated_at'))
        event_ts = max(value for value in [updated_at, created_at] if value is not None) if (updated_at or created_at) else None
        if not event_ts:
            continue
        status_key = _clean_text(row.get('status')).lower()
        review_key = _clean_text(row.get('editor_review_status')).lower()
        stage_key = _clean_text(row.get('workflow_stage')) if has_submission_workflow_stage else ''
        is_updated = bool(updated_at and created_at and updated_at > created_at)
        title = (
            _msg_text("Maqola yangilandi", "Статья обновлена", "Submission updated")
            if is_updated
            else _msg_text("Maqola yuborildi", "Статья отправлена", "Submission created")
        )
        subtitle_parts = [_clean_text(row.get('title')) or f"ID: {submission_id or '-'}"]
        if status_key:
            subtitle_parts.append(_status_label_text(status_key, language))
        if review_key:
            subtitle_parts.append(_editor_review_status_label_text(review_key, language))
        if stage_key:
            subtitle_parts.append(_workflow_stage_label_text(stage_key, language))
        timeline_events.append({
            'timestamp': event_ts,
            'icon': 'ti-file-text',
            'title': title,
            'subtitle': ' • '.join(part for part in subtitle_parts if part),
            'tone': _status_badge_tone(status_key, 'submission'),
            'url': url_for('submission_detail', submission_id=submission_id) if submission_id else None,
        })

    timeline_payments_rows = _query_rows_dicts(
        "SELECT id, status, payment_type, amount, currency, payment_date, created_at "
        "FROM payments WHERE user_id = %s "
        "ORDER BY COALESCE(payment_date, created_at) DESC NULLS LAST, id DESC "
        "LIMIT %s",
        (user_id, safe_timeline_limit),
    )
    for row in timeline_payments_rows:
        payment_date = _parse_int(row.get('payment_date'))
        created_at = _parse_int(row.get('created_at'))
        event_ts = max(value for value in [payment_date, created_at] if value is not None) if (payment_date or created_at) else None
        if not event_ts:
            continue
        status_key = _clean_text(row.get('status')).lower()
        type_key = _clean_text(row.get('payment_type')).lower()
        amount = _parse_amount(row.get('amount')) or 0
        currency = _clean_text(row.get('currency')).upper() or 'UZS'
        timeline_events.append({
            'timestamp': event_ts,
            'icon': 'ti-credit-card',
            'title': _msg_text("To'lov harakati", "Платежная активность", "Payment activity"),
            'subtitle': (
                f"{_payment_type_label_text(type_key)} • "
                f"{_status_label_text(status_key, language)} • "
                f"{_format_money_short(amount, currency)}"
            ),
            'tone': _status_badge_tone(status_key, 'payment'),
            'url': url_for('payments', status=status_key) if status_key else url_for('payments'),
        })

    assignment_rows = _query_rows_dicts(
        "SELECT id, submission_id, editor_id, assigned_by, status, assigned_at, reviewed_at "
        "FROM editor_assignments "
        "WHERE editor_id = %s OR assigned_by = %s "
        "ORDER BY COALESCE(reviewed_at, assigned_at) DESC NULLS LAST, id DESC "
        "LIMIT %s",
        (user_id, user_id, safe_timeline_limit),
    )
    for row in assignment_rows:
        assignment_id = _parse_int(row.get('id'))
        submission_id = _parse_int(row.get('submission_id'))
        reviewed_at = _parse_int(row.get('reviewed_at'))
        assigned_at = _parse_int(row.get('assigned_at'))
        event_ts = max(value for value in [reviewed_at, assigned_at] if value is not None) if (reviewed_at or assigned_at) else None
        if not event_ts:
            continue
        status_key = _clean_text(row.get('status')).lower()
        is_editor = _parse_int(row.get('editor_id')) == user_id
        is_assigner = _parse_int(row.get('assigned_by')) == user_id
        if reviewed_at and status_key in {'reviewed', 'rejected'}:
            title = _msg_text("Review yakunlandi", "Рецензирование завершено", "Review completed")
        elif is_editor and not is_assigner:
            title = _msg_text("Tahrirchi sifatida biriktirildi", "Назначено как редактору", "Assigned as editor")
        elif is_assigner and not is_editor:
            title = _msg_text("Admin biriktiruvi bajarildi", "Выполнено назначение админом", "Assignment made by admin")
        else:
            title = _msg_text("Editor assignment harakati", "Активность назначения редактора", "Editor assignment activity")
        timeline_events.append({
            'timestamp': event_ts,
            'icon': 'ti-user-check',
            'title': title,
            'subtitle': f"Assignment #{assignment_id or '-'} • Submission #{submission_id or '-'} • {_status_label_text(status_key, language)}",
            'tone': _status_badge_tone(status_key, 'editor_review'),
            'url': url_for('review_assignment', assignment_id=assignment_id) if assignment_id else None,
        })

    notification_rows = _query_rows_dicts(
        "SELECT id, title, message, level, action_url, is_read, created_at, target_user_id, actor_user_id, metadata_text "
        "FROM role_notifications "
        "WHERE target_user_id = %s OR actor_user_id = %s "
        "ORDER BY created_at DESC, id DESC LIMIT %s",
        (user_id, user_id, safe_timeline_limit),
    )
    for row in notification_rows:
        event_ts = _parse_int(row.get('created_at'))
        if not event_ts:
            continue
        localized = apply_localized_notification_content(row)
        is_target = _parse_int(row.get('target_user_id')) == user_id
        is_actor = _parse_int(row.get('actor_user_id')) == user_id
        scope_label = _msg_text("Qabul qiluvchi", "Получатель", "Recipient") if is_target and not is_actor else (
            _msg_text("Yuboruvchi", "Отправитель", "Actor") if is_actor and not is_target else _msg_text("Ikki tomonlama", "Обе роли", "Both roles")
        )
        read_label = _msg_text("o'qilmagan", "непрочитано", "unread") if is_target and not row.get('is_read') else _msg_text("o'qilgan", "прочитано", "read")
        timeline_events.append({
            'timestamp': event_ts,
            'icon': 'ti-bell',
            'title': _clean_text(localized.get('title')) or _msg_text("Rol xabari", "Ролевое уведомление", "Role notification"),
            'subtitle': f"{scope_label} • {read_label}",
            'tone': _status_badge_tone(localized.get('level'), 'notification'),
            'url': _clean_text(localized.get('action_url')) or url_for('role_notifications'),
        })

    timeline_events.sort(key=lambda item: (_parse_int(item.get('timestamp')) or 0), reverse=True)
    snapshot['timeline_has_more'] = len(timeline_events) > safe_timeline_limit
    snapshot['timeline'] = timeline_events[:safe_timeline_limit]

    all_activity_timestamps = [
        _parse_int(snapshot['submission_stats']['last_activity_at']),
        _parse_int(snapshot['payment_stats']['last_activity_at']),
        register_time,
        accept_rules_time,
        last_online,
    ]
    if snapshot['timeline']:
        all_activity_timestamps.append(_parse_int(snapshot['timeline'][0].get('timestamp')))
    all_activity_timestamps = [value for value in all_activity_timestamps if value is not None]
    snapshot['profile']['last_activity_at'] = max(all_activity_timestamps) if all_activity_timestamps else None

    return snapshot

@bp.route('/fmadmin/users/users/<int:user_id>', methods=['GET', 'POST'])
@is_superadmin_required
def user_edit(user_id):
    current_user = hydrate_user_roles(session.get('fmadmin_user') or {})
    current_role = primary_role(current_user)
    existing_user = None
    if user_id != 0:
        existing = db.users.all().equal(id=user_id).exec()
        if not existing:
            return 'Пользователь не найден', 404
        existing_user = hydrate_user_roles(existing[0])
        if existing_user.get('is_hidden') and current_role != 'superadmin':
            flash(t('admin_error_no_access'), 'danger')
            return redirect(url_for('users'))
        if existing_user.get('rolename') == 'superadmin' and current_role != 'superadmin':
            flash(t('admin_error_no_access'), 'danger')
            return redirect(url_for('users'))

    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        allowed_roles = _allowed_roles_for_actor(current_role)

        if user_id == 0:
            name = (data.get('name') or '').strip()
            email = (data.get('email') or '').strip().lower()
            rolename = (data.get('rolename') or 'user').strip().lower()
            role_selection = _extract_selected_roles(data, rolename, allowed_roles=allowed_roles)
            rolename = role_selection['primary_role']
            roles = role_selection['roles']
            password = data.get('password') or ''
            password_confirm = data.get('password_confirm') or ''
            has_staff_role = any(role_name in PRIVILEGED_ROLES for role_name in roles)
            has_admin_role = 'admin' in roles
            has_editor_role = 'editor' in roles

            if not name or not email:
                new_alert(_msg_text("Ism va email majburiy", 'Имя и email обязательны', 'Name and email are required'), 'danger')
                return redirect(url_for('user_edit', user_id=0))
            if rolename not in allowed_roles:
                new_alert(_msg_text("Noto'g'ri rol tanlandi", 'Недопустимая роль', 'Invalid role'), 'danger')
                return redirect(url_for('user_edit', user_id=0))
            if len(password) < 6:
                new_alert(_msg_text("Parol kamida 6 ta belgidan iborat bo'lishi kerak", 'Пароль должен быть не короче 6 символов', 'Password must be at least 6 characters long'), 'danger')
                return redirect(url_for('user_edit', user_id=0))
            if password != password_confirm:
                new_alert(_msg_text('Parol va tasdiq paroli mos emas', 'Пароль и подтверждение не совпадают', 'Password and confirmation do not match'), 'danger')
                return redirect(url_for('user_edit', user_id=0))
            existing_email = db.users.all().equal(email=email).exec()
            if existing_email:
                new_alert(_msg_text('Bu email bilan foydalanuvchi allaqachon mavjud', 'Пользователь с таким email уже существует', 'A user with this email already exists'), 'danger')
                return redirect(url_for('user_edit', user_id=0))

            country_id = data.get('country_id')
            region = data.get('region')
            is_blocked = _to_bool(data.get('is_blocked'))
            is_notify = _to_bool(data.get('is_notify'))
            is_hidden = _to_bool(data.get('is_hidden')) if current_role == 'superadmin' else False
            tariff_id = data.get('tariff_id')
            subscription_end_date = parse_date(data.get('subscription_end_date'))
            admin_tracks = _extract_admin_tracks(data) if has_admin_role else None
            if has_admin_role and not admin_tracks:
                new_alert(
                    _msg_text(
                        "Admin uchun kamida bitta yo'nalish tanlang",
                        "Для администратора выберите минимум одно направление",
                        "Select at least one track for admin"
                    ),
                    'danger'
                )
                return redirect(url_for('user_edit', user_id=0))
            editor_admin_id = _parse_int(data.get('editor_admin_id')) if has_editor_role else None
            if has_editor_role and editor_admin_id is not None:
                admin_target = _load_user_from_db(editor_admin_id)
                if not admin_target or not user_has_role(admin_target, 'admin') or admin_target.get('is_hidden') or admin_target.get('is_blocked'):
                    new_alert(_msg_text("Tahrirchi uchun biriktirilgan admin topilmadi", "Для редактора не найден назначенный администратор", "Assigned admin for editor not found"), 'danger')
                    return redirect(url_for('user_edit', user_id=0))
            if has_staff_role:
                is_hidden = False
                is_blocked = False
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(password) if password else None
            created_ts = int(datetime.datetime.now().timestamp())
            user_id_new = db.users.add(
                name=name,
                second_name=data.get('second_name'),
                father_name=data.get('father_name'),
                email=email,
                country_id=country_id or None,
                region=region,
                rolename=rolename,
                roles=roles,
                is_blocked=is_blocked,
                is_hidden=is_hidden,
                deleted_at=created_ts if is_hidden else None,
                is_notify=is_notify,
                ui_language=normalize_notification_language(_ui_language(), default='uz'),
                password=hashed_password,
                tariff_id=tariff_id or None,
                subscription_end_date=subscription_end_date,
                admin_tracks=admin_tracks,
                editor_admin_id=editor_admin_id,
                created_at=created_ts,
                register_time=created_ts
            ).exec()
            user_id_new = _extract_inserted_id(user_id_new)
            if has_admin_role:
                _realign_submission_admin_assignments()
            new_alert(_msg_text("Foydalanuvchi muvaffaqiyatli saqlandi", 'Пользователь успешно сохранён', 'User saved successfully'), 'success')
            return redirect(url_for('user_edit', user_id=user_id_new or 0))

        if not existing_user:
            return 'Пользователь не найден', 404

        new_email = (data.get('email') or '').strip().lower()
        if not new_email:
            new_alert(_msg_text("Email majburiy", 'Email обязателен', 'Email is required'), 'danger')
            return redirect(url_for('user_edit', user_id=user_id))
        if new_email != (existing_user.get('email') or '').strip().lower():
            existing_email = db.users.all().equal(email=new_email).exec()
            if existing_email:
                new_alert(_msg_text('Bu email bilan foydalanuvchi allaqachon mavjud', 'Пользователь с таким email уже существует', 'A user with this email already exists'), 'danger')
                return redirect(url_for('user_edit', user_id=user_id))

        submitted_role = (data.get('rolename') or existing_user.get('rolename') or 'user').strip().lower()
        if submitted_role not in allowed_roles:
            submitted_role = existing_user.get('rolename') or 'user'
        role_selection = _extract_selected_roles(
            data,
            submitted_role,
            allowed_roles=allowed_roles,
            fallback_roles=existing_user.get('roles'),
        )
        submitted_role = role_selection['primary_role']
        roles = role_selection['roles']
        has_staff_role = any(role_name in PRIVILEGED_ROLES for role_name in roles)
        had_staff_role = any(role_name in PRIVILEGED_ROLES for role_name in parse_role_names(existing_user.get('roles')))
        has_admin_role = 'admin' in roles
        has_editor_role = 'editor' in roles

        password = data.get('password') or ''
        password_confirm = data.get('password_confirm') or ''
        password_hash = None
        if password or password_confirm:
            if len(password) < 6:
                new_alert(_msg_text("Parol kamida 6 ta belgidan iborat bo'lishi kerak", 'Пароль должен быть не короче 6 символов', 'Password must be at least 6 characters long'), 'danger')
                return redirect(url_for('user_edit', user_id=user_id))
            if password != password_confirm:
                new_alert(_msg_text('Parol va tasdiq paroli mos emas', 'Пароль и подтверждение не совпадают', 'Password and confirmation do not match'), 'danger')
                return redirect(url_for('user_edit', user_id=user_id))
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password)

        if has_staff_role and not had_staff_role and not password_hash:
            new_alert(
                _msg_text(
                    "Rolda o'zgarish bor: admin/tahrirchi qilishda yangi parol kiritish shart.",
                    "Роль изменена: при назначении admin/editor нужно задать новый пароль.",
                    "Role changed: assigning admin/editor requires setting a new password."
                ),
                'danger'
            )
            return redirect(url_for('user_edit', user_id=user_id))

        if has_staff_role and not (existing_user.get('password') or password_hash):
            new_alert(
                _msg_text(
                    "Bu rol uchun parol o'rnatish majburiy. Iltimos, yangi parol kiriting.",
                    "Для этой роли необходимо задать пароль. Пожалуйста, введите новый пароль.",
                    "Password is required for this role. Please set a new password."
                ),
                'danger'
            )
            return redirect(url_for('user_edit', user_id=user_id))

        subscription_end_date = parse_date(data.get('subscription_end_date'))
        is_hidden = existing_user.get('is_hidden', False)
        deleted_at = existing_user.get('deleted_at')
        is_blocked = _to_bool(data.get('is_blocked'))
        if current_role == 'superadmin':
            is_hidden = _to_bool(data.get('is_hidden'))
            deleted_at = int(datetime.datetime.now().timestamp()) if is_hidden else None
        admin_tracks = _extract_admin_tracks(data) if has_admin_role else None
        if has_admin_role and not admin_tracks:
            new_alert(
                _msg_text(
                    "Admin uchun kamida bitta yo'nalish tanlang",
                    "Для администратора выберите минимум одно направление",
                    "Select at least one track for admin"
                ),
                'danger'
            )
            return redirect(url_for('user_edit', user_id=user_id))
        editor_admin_id = _parse_int(data.get('editor_admin_id')) if has_editor_role else None
        if has_editor_role and editor_admin_id is not None:
            admin_target = _load_user_from_db(editor_admin_id)
            if not admin_target or not user_has_role(admin_target, 'admin') or admin_target.get('is_hidden') or admin_target.get('is_blocked'):
                new_alert(_msg_text("Tahrirchi uchun biriktirilgan admin topilmadi", "Для редактора не найден назначенный администратор", "Assigned admin for editor not found"), 'danger')
                return redirect(url_for('user_edit', user_id=user_id))
        if has_staff_role:
            # Admin/editor/superadmin should be active to access fmadmin after role assignment.
            is_hidden = False
            deleted_at = None
            is_blocked = False

        update_data = dict(
            name=data.get('name'),
            second_name=data.get('second_name'),
            father_name=data.get('father_name'),
            email=new_email,
            country_id=data.get('country_id') or None,
            region=data.get('region'),
            rolename=submitted_role,
            roles=roles,
            is_blocked=is_blocked or bool(is_hidden),
            is_hidden=is_hidden,
            deleted_at=deleted_at,
            is_notify=_to_bool(data.get('is_notify')),
            ui_language=normalize_notification_language(existing_user.get('ui_language') or _ui_language(), default='uz'),
            tariff_id=data.get('tariff_id') or None,
            subscription_end_date=subscription_end_date,
            admin_tracks=admin_tracks,
            editor_admin_id=editor_admin_id
        )
        if password_hash:
            update_data['password'] = password_hash

        saved_user_rows = db.users.all().equal(id=user_id).update(**update_data).exec()
        saved_user = saved_user_rows[0] if saved_user_rows else None
        if user_has_role(existing_user, 'admin') or has_admin_role:
            _realign_submission_admin_assignments()
        if _parse_int(current_user.get('id')) == user_id and saved_user:
            session['fmadmin_user'] = _session_admin_user_payload(saved_user)
        new_alert(_msg_text("Foydalanuvchi muvaffaqiyatli saqlandi", 'Пользователь успешно сохранён', 'User saved successfully'), 'success')
        return redirect(url_for('user_edit', user_id=user_id))

    if user_id == 0:
        # Новый пользователь
        user = {
            'id': 0,
            'name': '',
            'second_name': '',
            'father_name': '',
            'email': '',
            'country_id': None,
            'region': '',
            'rolename': 'user',
            'roles': [AUTHOR_ROLE],
            'is_blocked': False,
            'is_hidden': False,
            'is_notify': False,
            'accept_rules_time': None,
            'last_online': None,
            'created_at': None,
            'register_time': None,
            'tariff_id': None,
            'subscription_end_date': None,
            'deleted_at': None,
            'admin_tracks': [],
            'editor_admin_id': None,
            'has_author_role': True
        }
    else:
        user = existing_user
    user = hydrate_user_roles(user)
    user['has_author_role'] = user_has_role(user, AUTHOR_ROLE)
    user['admin_tracks'] = _admin_tracks_for_user(user)
    countries = db.fix_country.all().exec()
    _ensure_tariff_archive_column()
    tariffs = db.tariffs.all().exec()
    active_admins = _active_admins()
    role_choices = []
    for role_name in _allowed_roles_for_actor(current_role):
        if role_name == 'user':
            label = "Muallif / Author"
        elif role_name == 'admin':
            label = t("admin_role_admin")
        elif role_name == 'editor':
            label = t("admin_role_editor")
        elif role_name == 'superadmin':
            label = 'Super Admin'
        else:
            label = role_name.title()
        role_choices.append((role_name, label))
    
    # Проверяем, есть ли у пользователя верифицированные документы (для фильтрации тарифов)
    user_has_verified_documents = False
    if user_id > 0:
        user_docs = db.user_doc_uploads.all().equal(user_id=user_id).exec()
        user_has_verified_documents = any(
            _clean_text(item.get('verification_status')).lower() in {'verified', 'approved'}
            for item in user_docs
        )
    
    # Фильтруем тарифы: если у пользователя нет документов, скрываем тарифы "для верифицированных"
    filtered_tariffs = []
    current_tariff_id = _parse_int(user.get('tariff_id'))
    for tariff in tariffs:
        tariff_id = _parse_int(tariff.get('id'))
        if _is_tariff_archived(tariff) and tariff_id != current_tariff_id:
            continue  # Показываем архивный тариф только если он уже назначен пользователю
        if tariff.get('is_verified', False) and not user_has_verified_documents:
            continue  # Пропускаем тарифы для верифицированных, если у пользователя нет документов
        filtered_tariffs.append(tariff)

    user_360 = _build_user_360_snapshot(user) if user_id > 0 else None
    
    return render_template(
        'users/users/edit.html',
        user=user,
        countries=countries,
        tariffs=filtered_tariffs,
        current_user=current_user,
        active_admins=active_admins,
        admin_track_choices=ADMIN_TRACK_CHOICES,
        role_choices=role_choices,
        user_360=user_360
    )


@bp.route('/fmadmin/users/users/<int:user_id>/state', methods=['POST'])
@is_superadmin_required
def user_state_change(user_id):
    current_user = session.get('fmadmin_user') or {}
    current_user_id = _parse_int(current_user.get('id'))
    action = (request.form.get('action') or '').strip().lower()

    user_rows = db.users.all().equal(id=user_id).exec()
    if not user_rows:
        new_alert(_msg_text('Foydalanuvchi topilmadi', 'Пользователь не найден', 'User not found'), 'danger')
        return redirect(url_for('users', include_hidden=1))

    user = user_rows[0]
    if user_id == current_user_id and action in {'hide', 'block'}:
        new_alert(_msg_text("O'zingizni yashirish yoki bloklash mumkin emas", 'Нельзя скрыть или заблокировать самого себя', 'You cannot hide or block yourself'), 'danger')
        return redirect(url_for('users', include_hidden=1))

    now_ts = int(datetime.datetime.now().timestamp())
    update_data = {}
    if action == 'hide':
        update_data = {'is_hidden': True, 'is_blocked': True, 'deleted_at': now_ts}
    elif action == 'restore':
        update_data = {'is_hidden': False, 'is_blocked': False, 'deleted_at': None}
    elif action == 'block':
        update_data = {'is_blocked': True}
    elif action == 'unblock':
        update_data = {'is_blocked': False}
    else:
        new_alert(_msg_text("Noma'lum amal", 'Неизвестное действие', 'Unknown action'), 'danger')
        return redirect(url_for('users', include_hidden=1))

    db.users.all().equal(id=user_id).update(**update_data).exec()
    new_alert(_msg_text("Foydalanuvchi holati yangilandi", 'Статус пользователя обновлён', 'User status updated'), 'success')
    return redirect(url_for('users', include_hidden=1))


def _hide_users_except(keep_ids, now_ts):
    cursor = None
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET is_hidden = TRUE, is_blocked = TRUE, deleted_at = %s
            WHERE NOT (id = ANY(%s::int[]))
            RETURNING id
            """,
            (now_ts, list(keep_ids)),
        )
        updated_rows = cursor.fetchall()
        db.conn.commit()
        return len(updated_rows)
    except Exception:
        db.conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()


@bp.route('/fmadmin/users/users/bulk', methods=['POST'])
@is_superadmin_required
def users_bulk_action():
    action = (request.form.get('action') or '').strip().lower()
    current_user = session.get('fmadmin_user') or {}
    current_user_id = _parse_int(current_user.get('id'))
    selected_ids = []
    for value in request.form.getlist('selected_user_ids'):
        try:
            selected_ids.append(int(value))
        except (TypeError, ValueError):
            continue
    selected_ids = list(dict.fromkeys(selected_ids))

    if not action:
        new_alert(_msg_text("Amal tanlanmagan", 'Действие не выбрано', 'Action is not selected'), 'danger')
        return redirect(url_for('users', include_hidden=1))

    allowed_actions = {'hide_others', 'hide_selected', 'restore_selected', 'block_selected', 'unblock_selected'}
    if action not in allowed_actions:
        new_alert(_msg_text("Noma'lum amal", 'Неизвестное действие', 'Unknown action'), 'danger')
        return redirect(url_for('users', include_hidden=1))

    if action == 'hide_others':
        if not selected_ids:
            new_alert(_msg_text("Kamida bitta foydalanuvchi tanlang", 'Выберите хотя бы одного пользователя', 'Select at least one user'), 'danger')
            return redirect(url_for('users', include_hidden=1))
        if (request.form.get('confirm_phrase') or '').strip() != 'HIDE_OTHERS':
            new_alert(_msg_text("Keng ta'sirli amal tasdiqlanmadi", 'Массовое действие не подтверждено', 'Bulk action was not confirmed'), 'danger')
            return redirect(url_for('users', include_hidden=1))
        keep_ids = set(selected_ids)
        if current_user_id is not None:
            keep_ids.add(current_user_id)
        now_ts = int(datetime.datetime.now().timestamp())
        changed = _hide_users_except(keep_ids, now_ts)
        new_alert(_msg_text(f"Yashirilgan foydalanuvchilar soni: {changed}", f'Скрыто пользователей: {changed}', f'Users hidden: {changed}'), 'success')
        return redirect(url_for('users', include_hidden=1))

    if not selected_ids:
        new_alert(_msg_text("Kamida bitta foydalanuvchi tanlang", 'Выберите хотя бы одного пользователя', 'Select at least one user'), 'danger')
        return redirect(url_for('users', include_hidden=1))

    now_ts = int(datetime.datetime.now().timestamp())
    selected_update_map = {
        'hide_selected': {'is_hidden': True, 'is_blocked': True, 'deleted_at': now_ts},
        'restore_selected': {'is_hidden': False, 'is_blocked': False, 'deleted_at': None},
        'block_selected': {'is_blocked': True},
        'unblock_selected': {'is_blocked': False},
    }
    target_ids = selected_ids
    if current_user_id is not None and action in {'hide_selected', 'block_selected'}:
        target_ids = [uid for uid in selected_ids if uid != current_user_id]
    updated_users = (
        db.users.all().any(id=target_ids).update(**selected_update_map[action]).exec()
        if target_ids else []
    )
    changed = len(updated_users)

    new_alert(_msg_text(f"Yangilangan foydalanuvchilar soni: {changed}", f'Обновлено пользователей: {changed}', f'Users updated: {changed}'), 'success')
    return redirect(url_for('users', include_hidden=1))


@bp.route('/fmadmin/users/authors')
@is_superadmin_required
def authors():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_name = request.args.get('name', '').strip()
    search_orcid = request.args.get('orcid', '').strip()
    search_by_name = request.args.get('search_by_name', '')
    has_articles = request.args.get('has_articles', '')

    query = db.author_profile.all()
    if search_name:
        query = query.like(name=search_name)
    if search_orcid:
        if search_by_name:
            query = query.like(name=search_orcid)
        else:
            query = query.like(orcid=search_orcid)

    if has_articles in ('true', 'false'):
        cursor = db.conn.cursor()
        try:
            cursor.execute(
                "SELECT DISTINCT main_author_id FROM publications WHERE main_author_id IS NOT NULL"
            )
            author_ids_with_articles = [r[0] for r in cursor.fetchall()]
        finally:
            cursor.close()
        if has_articles == 'true':
            query = query.any(id=author_ids_with_articles) if author_ids_with_articles else query.any(id=[-1])
        else:
            all_author_ids = [a['id'] for a in db.author_profile.all().exec()]
            without = list(set(all_author_ids) - set(author_ids_with_articles))
            query = query.any(id=without) if without else query.any(id=[-1])

    total_authors = query.copy().count().exec()
    authors_page = query.per_page(per_page).page(page).exec()
    total_pages = (total_authors + per_page - 1) // per_page

    # Article counts via SQL — avoids loading all publications into memory
    author_ids_page = [a['id'] for a in authors_page]
    author_stats = {aid: {'as_main': 0, 'as_co': 0} for aid in author_ids_page}
    if author_ids_page:
        cursor = db.conn.cursor()
        try:
            placeholders = ','.join(['%s'] * len(author_ids_page))
            cursor.execute(
                f"SELECT main_author_id, COUNT(*) FROM publications WHERE main_author_id IN ({placeholders}) GROUP BY main_author_id",
                author_ids_page,
            )
            for aid, cnt in cursor.fetchall():
                if aid in author_stats:
                    author_stats[aid]['as_main'] = cnt
            cursor.execute(
                "SELECT aid, COUNT(*) FROM (SELECT UNNEST(subauthor_ids) AS aid FROM publications WHERE subauthor_ids IS NOT NULL) t WHERE aid = ANY(%s::int[]) GROUP BY aid",
                (author_ids_page,),
            )
            for aid, cnt in cursor.fetchall():
                if aid in author_stats:
                    author_stats[aid]['as_co'] = cnt
        finally:
            cursor.close()

    # Detect authors whose linked user shares email/ORCID with another user (duplicates)
    duplicate_author_ids = set()
    if author_ids_page:
        cursor = db.conn.cursor()
        try:
            cursor.execute("""
                SELECT ap.id
                FROM author_profile ap
                JOIN users u ON u.id = ap.user_id
                WHERE ap.id = ANY(%s::int[])
                  AND (
                      (u.email IS NOT NULL AND TRIM(u.email) != '' AND LOWER(TRIM(u.email)) NOT LIKE '%%@orcid.local' AND EXISTS (
                          SELECT 1
                          FROM users u2
                          WHERE u2.id != u.id
                            AND LOWER(TRIM(u2.email)) = LOWER(TRIM(u.email))
                      ))
                      OR (
                          regexp_replace(UPPER(TRIM(COALESCE(ap.orcid, ''))), '[^0-9X]', '', 'g') ~ '^[0-9]{15}[0-9X]$'
                          AND EXISTS (
                              SELECT 1
                              FROM author_profile ap2
                              WHERE ap2.id != ap.id
                                AND regexp_replace(UPPER(TRIM(COALESCE(ap2.orcid, ''))), '[^0-9X]', '', 'g')
                                    = regexp_replace(UPPER(TRIM(COALESCE(ap.orcid, ''))), '[^0-9X]', '', 'g')
                          )
                      )
                      OR (
                          regexp_replace(UPPER(TRIM(COALESCE(ap.orcid, ''))), '[^0-9X]', '', 'g') ~ '^[0-9]{15}[0-9X]$'
                          AND EXISTS (
                              SELECT 1 FROM information_schema.columns
                              WHERE table_schema = 'public' AND table_name = 'users'
                                AND column_name = 'oauth_sub'
                          )
                          AND EXISTS (
                              SELECT 1
                              FROM users u4
                              WHERE u4.id != u.id
                                AND LOWER(COALESCE(u4.oauth_provider, '')) = 'orcid'
                                AND regexp_replace(UPPER(TRIM(COALESCE(u4.oauth_sub, ''))), '[^0-9X]', '', 'g')
                                    = regexp_replace(UPPER(TRIM(COALESCE(ap.orcid, ''))), '[^0-9X]', '', 'g')
                          )
                      )
                  )
            """, (author_ids_page,))
            duplicate_author_ids = {r[0] for r in cursor.fetchall()}
        finally:
            cursor.close()

    users_map = {u['id']: u for u in db.users.all().exec()}

    return render_template(
        'users/authors/authors.html',
        authors=authors_page,
        page=page,
        total_authors=total_authors,
        total_pages=total_pages,
        search_name=search_name,
        search_orcid=search_orcid,
        search_by_name=search_by_name,
        has_articles=has_articles,
        author_stats=author_stats,
        users_map=users_map,
        duplicate_author_ids=duplicate_author_ids,
    )


def _find_duplicate_users_for_author(author):
    """Return list of user dicts that share the same email or ORCID as this author's linked user."""
    author_user_id = author.get('user_id')
    author_orcid = _normalize_orcid_identifier(author.get('orcid'))
    author_orcid_compact = author_orcid.replace('-', '') if author_orcid else ''

    # Determine the canonical email to search for
    lookup_email = ''
    if author_user_id:
        linked = db.users.all().equal(id=author_user_id).exec()
        if linked:
            lookup_email = _normalized_social_email(linked[0].get('email'))
    if not lookup_email:
        lookup_email = _normalized_social_email(author.get('email'))

    if not lookup_email and not author_orcid_compact:
        return []

    cursor = db.conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT u.*
            FROM users u
            WHERE u.id != %s
              AND (
                  (%s != '' AND LOWER(u.email) = %s)
                  OR (%s != '' AND EXISTS (
                      SELECT 1 FROM author_profile ap2
                      WHERE ap2.user_id = u.id
                        AND regexp_replace(UPPER(TRIM(COALESCE(ap2.orcid, ''))), '[^0-9X]', '', 'g') = %s
                        AND ap2.id != %s
                  ))
                  OR (%s != '' AND EXISTS (
                      SELECT 1 FROM information_schema.columns
                      WHERE table_schema = 'public' AND table_name = 'users'
                        AND column_name IN ('oauth_provider', 'oauth_sub')
                  ) AND EXISTS (
                      SELECT 1 FROM users u3
                      WHERE u3.id = u.id
                        AND LOWER(COALESCE(u3.oauth_provider, '')) = 'orcid'
                        AND regexp_replace(UPPER(TRIM(COALESCE(u3.oauth_sub, ''))), '[^0-9X]', '', 'g') = %s
                  ))
              )
            ORDER BY u.id DESC
            LIMIT 20
        """, (
            author_user_id or 0,
            lookup_email, lookup_email,
            author_orcid_compact, author_orcid_compact, author.get('id') or 0,
            author_orcid_compact, author_orcid_compact,
        ))
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    except Exception:
        logger.exception("Error finding duplicate users for author %s", author.get('id'))
        return []
    finally:
        cursor.close()


def _normalized_social_email(value):
    email = _clean_text(value).lower()
    if not email:
        return ''
    if email.endswith('@orcid.local'):
        return ''
    # Keep validation lightweight for admin merge paths.
    if '@' not in email:
        return ''
    return email


def _normalize_orcid_identifier(value):
    text = _clean_text(value)
    if not text:
        return ''
    compact = re.sub(r'[^0-9Xx]', '', text)
    if len(compact) == 16 and re.match(r'^\d{15}[\dXx]$', compact):
        compact = compact.upper()
        return f'{compact[0:4]}-{compact[4:8]}-{compact[8:12]}-{compact[12:16]}'
    return ''


def _table_column_exists(cursor, cache, table_name, column_name):
    key = (table_name, column_name)
    if key in cache:
        return cache[key]
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        );
        """,
        (table_name, column_name),
    )
    exists = bool(cursor.fetchone()[0])
    cache[key] = exists
    return exists


def _merge_author_profile_references(cursor, column_cache, source_author_id, target_author_id):
    if not source_author_id or not target_author_id or source_author_id == target_author_id:
        return

    for table_name in ('submissions', 'publications'):
        if _table_column_exists(cursor, column_cache, table_name, 'main_author_id'):
            cursor.execute(
                f"UPDATE {table_name} SET main_author_id = %s WHERE main_author_id = %s",
                (target_author_id, source_author_id),
            )

    array_columns = (
        ('submissions', 'sub_author_ids'),
        ('publications', 'subauthor_ids'),
        ('publications', 'sub_author_ids'),
    )
    for table_name, column_name in array_columns:
        if not _table_column_exists(cursor, column_cache, table_name, column_name):
            continue
        cursor.execute(
            f"""
            UPDATE {table_name}
               SET {column_name} = array_replace({column_name}, %s, %s)
             WHERE {column_name} IS NOT NULL
               AND %s = ANY({column_name})
            """,
            (source_author_id, target_author_id, source_author_id),
        )


def _merge_author_profiles_for_users(cursor, column_cache, primary_user_id, secondary_user_id, now_ts):
    if not _table_column_exists(cursor, column_cache, 'author_profile', 'user_id'):
        return

    cursor.execute("SELECT * FROM author_profile WHERE user_id = %s ORDER BY id ASC", (primary_user_id,))
    primary_cols = [desc[0] for desc in cursor.description]
    primary_rows = [dict(zip(primary_cols, row)) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM author_profile WHERE user_id = %s ORDER BY id ASC", (secondary_user_id,))
    secondary_cols = [desc[0] for desc in cursor.description]
    secondary_rows = [dict(zip(secondary_cols, row)) for row in cursor.fetchall()]
    if not secondary_rows:
        return

    canonical = primary_rows[0] if primary_rows else secondary_rows.pop(0)
    canonical_id = _parse_int(canonical.get('id'))
    if not canonical_id:
        return

    if _parse_int(canonical.get('user_id')) != int(primary_user_id):
        if _table_column_exists(cursor, column_cache, 'author_profile', 'updated_at'):
            cursor.execute(
                "UPDATE author_profile SET user_id = %s, updated_at = %s WHERE id = %s",
                (primary_user_id, now_ts, canonical_id),
            )
        else:
            cursor.execute(
                "UPDATE author_profile SET user_id = %s WHERE id = %s",
                (primary_user_id, canonical_id),
            )
        canonical['user_id'] = primary_user_id

    merge_fields = (
        'name',
        'second_name',
        'father_name',
        'organization',
        'email',
        'position',
        'address_street',
        'address_country',
        'address_city',
        'address_zip',
        'phone',
        'orcid',
        'department',
    )

    for row in secondary_rows:
        source_id = _parse_int(row.get('id'))
        if not source_id:
            continue

        patch = {}
        for field_name in merge_fields:
            source_value = row.get(field_name)
            source_text = _clean_text(source_value)
            if not source_text:
                continue

            current_text = _clean_text(canonical.get(field_name))
            if field_name == 'email':
                source_email = _normalized_social_email(source_text)
                current_email = _normalized_social_email(current_text)
                if source_email and not current_email:
                    patch[field_name] = source_email
                continue
            if field_name == 'orcid':
                source_orcid = _normalize_orcid_identifier(source_text)
                current_orcid = _normalize_orcid_identifier(current_text)
                if source_orcid and not current_orcid:
                    patch[field_name] = source_orcid
                continue
            if not current_text:
                patch[field_name] = source_value

        if patch:
            if _table_column_exists(cursor, column_cache, 'author_profile', 'updated_at'):
                patch['updated_at'] = now_ts
            set_clause = ', '.join(f"{key} = %s" for key in patch)
            args = list(patch.values()) + [canonical_id]
            cursor.execute(f"UPDATE author_profile SET {set_clause} WHERE id = %s", args)
            canonical.update(patch)

        _merge_author_profile_references(cursor, column_cache, source_id, canonical_id)
        cursor.execute("DELETE FROM author_profile WHERE id = %s", (source_id,))


@bp.route('/fmadmin/users/authors/<int:author_id>', methods=['GET', 'POST'])
@is_superadmin_required
def author_edit(author_id):
    column_cache = {}
    cursor = db.conn.cursor()
    try:
        has_second_name_column = _table_column_exists(cursor, column_cache, 'author_profile', 'second_name')
        has_father_name_column = _table_column_exists(cursor, column_cache, 'author_profile', 'father_name')
    finally:
        cursor.close()

    if request.method == 'POST':
        data = request.form
        first_name = _clean_text(data.get('first_name'))
        second_name = _clean_text(data.get('second_name'))
        father_name = _clean_text(data.get('father_name'))
        full_name = _compose_author_full_name(first_name, second_name, father_name)
        if not full_name:
            full_name = _clean_text(data.get('name'))
            if not first_name and full_name:
                first_name, second_name, father_name = _split_author_full_name(full_name)

        address_country = data.get('address_country', '').strip()
        payload = {
            'user_id': data.get('user_id') or None,
            'name': full_name,
            'organization': data.get('organization'),
            'email': data.get('email'),
            'position': data.get('position'),
            'address_street': data.get('address_street'),
            'address_country': address_country,
            'address_city': data.get('address_city'),
            'address_zip': data.get('address_zip'),
            'phone': data.get('phone'),
            'orcid': data.get('orcid'),
            'department': data.get('department'),
        }
        if has_second_name_column:
            payload['second_name'] = second_name or None
        if has_father_name_column:
            payload['father_name'] = father_name or None

        if author_id == 0:
            created_at = parse_date(data.get('created_at'), with_time=True)
            updated_at = parse_date(data.get('updated_at'), with_time=True)
            payload['created_at'] = created_at or int(datetime.datetime.now().timestamp())
            payload['updated_at'] = updated_at or int(datetime.datetime.now().timestamp())
            created_authors = db.author_profile.add(**payload).exec()
            created_author = created_authors[0] if created_authors else None
            if not created_author or not created_author.get('id'):
                new_alert(_msg_text('Muallif yaratilmadi', 'Автор не создан', 'Author was not created'), 'danger')
                return redirect(url_for('author_edit', author_id=0))
            new_alert(_msg_text('Muallif muvaffaqiyatli yaratildi', 'Автор успешно создан', 'Author created successfully'), 'success')
            return redirect(url_for('author_edit', author_id=created_author['id']))
        else:
            created_at = parse_date(data.get('created_at'), with_time=True)
            updated_at = parse_date(data.get('updated_at'), with_time=True)
            payload['created_at'] = created_at
            payload['updated_at'] = updated_at or int(datetime.datetime.now().timestamp())
            db.author_profile.all().equal(id=author_id).update(**payload).exec()
            new_alert(_msg_text('Muallif muvaffaqiyatli saqlandi', 'Автор успешно сохранён', 'Author saved successfully'), 'success')
            return redirect(url_for('author_edit', author_id=author_id))

    if author_id == 0:
        author = {
            'id': 0, 'user_id': None, 'name': '', 'organization': '', 'email': '',
            'position': '', 'address_street': '', 'address_country': '', 'address_city': '',
            'address_zip': '', 'phone': '', 'orcid': '', 'department': '',
            'second_name': '', 'father_name': '', 'first_name': '',
            'created_at': None, 'updated_at': None,
        }
    else:
        author = db.author_profile.all().equal(id=author_id).exec()
        if not author:
            return 'Автор не найден', 404
        author = author[0]
        first_name, fallback_second_name, fallback_father_name = _split_author_full_name(author.get('name'))
        author_second_name = _clean_text(author.get('second_name'))
        author_father_name = _clean_text(author.get('father_name'))
        author['first_name'] = first_name
        author['second_name'] = author_second_name or fallback_second_name
        author['father_name'] = author_father_name or fallback_father_name

    all_authors = db.author_profile.all().exec()
    used_user_ids = set(a['user_id'] for a in all_authors if a['user_id'])
    if author.get('user_id'):
        used_user_ids.discard(author['user_id'])
    users = [u for u in db.users.all().exec() if u['id'] not in used_user_ids or u['id'] == author.get('user_id')]
    countries = db.fix_country.all().exec()
    duplicate_users = _find_duplicate_users_for_author(author) if author_id != 0 else []
    return render_template('users/authors/edit.html', author=author, users=users,
                           countries=countries, duplicate_users=duplicate_users)


@bp.route('/fmadmin/users/authors/<int:author_id>/merge', methods=['POST'])
@is_superadmin_required
def author_merge_users(author_id):
    """Merge a duplicate user account into the primary user linked to this author."""
    primary_user_id = request.form.get('primary_user_id', type=int)
    secondary_user_id = request.form.get('secondary_user_id', type=int)
    if not primary_user_id or not secondary_user_id or primary_user_id == secondary_user_id:
        new_alert(_msg_text('Noto\'g\'ri ma\'lumotlar', 'Неверные данные', 'Invalid data'), 'danger')
        return redirect(url_for('author_edit', author_id=author_id))

    now_ts = int(datetime.datetime.now().timestamp())
    column_cache = {}

    def _to_row(cursor, user_id):
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        fetched = cursor.fetchone()
        if not fetched:
            return None
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, fetched))

    try:
        with db._lock:
            cursor = db.conn.cursor()
            try:
                lock_first, lock_second = sorted([primary_user_id, secondary_user_id])
                cursor.execute(
                    "SELECT id FROM users WHERE id IN (%s, %s) ORDER BY id FOR UPDATE",
                    (lock_first, lock_second),
                )

                primary_row = _to_row(cursor, primary_user_id)
                secondary_row = _to_row(cursor, secondary_user_id)
                if not primary_row or not secondary_row:
                    db.conn.rollback()
                    new_alert(_msg_text('Foydalanuvchi topilmadi', 'Пользователь не найден', 'User not found'), 'danger')
                    return redirect(url_for('author_edit', author_id=author_id))

                _merge_author_profiles_for_users(
                    cursor,
                    column_cache,
                    primary_user_id=primary_user_id,
                    secondary_user_id=secondary_user_id,
                    now_ts=now_ts,
                )

                user_ref_columns = (
                    ('author_profile', 'user_id'),
                    ('submissions', 'user_id'),
                    ('payments', 'user_id'),
                    ('user_doc_uploads', 'user_id'),
                    ('files', 'user_id'),
                    ('news', 'author_id'),
                    ('editor_assignments', 'editor_id'),
                    ('editor_assignments', 'assigned_by'),
                    ('editor_notifications', 'editor_id'),
                    ('role_notifications', 'target_user_id'),
                    ('role_notifications', 'actor_user_id'),
                    ('editorial_members', 'created_by'),
                    ('editorial_members', 'updated_by'),
                    ('email_templates', 'created_by'),
                    ('email_templates', 'updated_by'),
                )
                for table_name, column_name in user_ref_columns:
                    if not _table_column_exists(cursor, column_cache, table_name, column_name):
                        continue
                    cursor.execute(
                        f"UPDATE {table_name} SET {column_name} = %s WHERE {column_name} = %s",
                        (primary_user_id, secondary_user_id),
                    )

                users_columns = set(primary_row.keys()) | set(secondary_row.keys())
                patch = {}

                if 'email' in users_columns:
                    primary_email_raw = _clean_text(primary_row.get('email')).lower()
                    secondary_email_raw = _clean_text(secondary_row.get('email')).lower()
                    primary_email = _normalized_social_email(primary_email_raw)
                    secondary_email = _normalized_social_email(secondary_email_raw)
                    if secondary_email and not primary_email:
                        patch['email'] = secondary_email
                    elif not primary_email_raw and secondary_email_raw:
                        patch['email'] = secondary_email_raw

                for field_name in (
                    'name', 'second_name', 'father_name', 'password', 'country_id', 'region', 'avatar',
                    'tariff_id', 'editor_specialization', 'ui_language', 'token', 'rolename',
                    'editor_admin_id',
                ):
                    if field_name not in users_columns:
                        continue
                    primary_value = primary_row.get(field_name)
                    secondary_value = secondary_row.get(field_name)
                    if primary_value in (None, '', []) and secondary_value not in (None, '', []):
                        patch[field_name] = secondary_value

                for field_name in ('accept_rules_time', 'register_time', 'created_at'):
                    if field_name not in users_columns:
                        continue
                    primary_value = _parse_int(primary_row.get(field_name)) or 0
                    secondary_value = _parse_int(secondary_row.get(field_name)) or 0
                    if primary_value <= 0 and secondary_value > 0:
                        patch[field_name] = secondary_value
                    elif primary_value > 0 and secondary_value > 0 and secondary_value < primary_value:
                        patch[field_name] = secondary_value

                for field_name in ('last_online', 'subscription_end_date'):
                    if field_name not in users_columns:
                        continue
                    primary_value = _parse_int(primary_row.get(field_name)) or 0
                    secondary_value = _parse_int(secondary_row.get(field_name)) or 0
                    if secondary_value > primary_value:
                        patch[field_name] = secondary_value

                if 'is_notify' in users_columns and bool(secondary_row.get('is_notify')) and not bool(primary_row.get('is_notify')):
                    patch['is_notify'] = True

                if 'roles' in users_columns:
                    merged_roles = []
                    for role_name in parse_role_names(primary_row.get('roles')) + parse_role_names(secondary_row.get('roles')):
                        if role_name not in merged_roles:
                            merged_roles.append(role_name)
                    if merged_roles and merged_roles != parse_role_names(primary_row.get('roles')):
                        patch['roles'] = merged_roles

                if 'admin_tracks' in users_columns:
                    merged_tracks = []
                    for track_name in _parse_text_list(primary_row.get('admin_tracks')) + _parse_text_list(secondary_row.get('admin_tracks')):
                        track_clean = _clean_text(track_name)
                        if track_clean and track_clean not in merged_tracks:
                            merged_tracks.append(track_clean)
                    if merged_tracks and merged_tracks != _parse_text_list(primary_row.get('admin_tracks')):
                        patch['admin_tracks'] = merged_tracks

                if 'oauth_provider' in users_columns and 'oauth_sub' in users_columns:
                    primary_provider = _clean_text(primary_row.get('oauth_provider')).lower()
                    secondary_provider = _clean_text(secondary_row.get('oauth_provider')).lower()
                    primary_sub = _clean_text(primary_row.get('oauth_sub'))
                    secondary_sub = _clean_text(secondary_row.get('oauth_sub'))
                    if not primary_provider and secondary_provider:
                        patch['oauth_provider'] = secondary_provider
                        primary_provider = secondary_provider
                    if not primary_sub and secondary_sub and (not primary_provider or primary_provider == secondary_provider):
                        patch['oauth_sub'] = secondary_sub

                if 'updated_at' in users_columns:
                    patch['updated_at'] = now_ts

                if patch:
                    set_clause = ', '.join(f"{k} = %s" for k in patch)
                    cursor.execute(
                        f"UPDATE users SET {set_clause} WHERE id = %s",
                        list(patch.values()) + [primary_user_id],
                    )

                cursor.execute("DELETE FROM users WHERE id = %s", (secondary_user_id,))
                db.conn.commit()
                logger.info("Admin merged user accounts primary=%s secondary=%s author=%s", primary_user_id, secondary_user_id, author_id)
            except Exception:
                db.conn.rollback()
                raise
            finally:
                cursor.close()

        new_alert(_msg_text(
            f'Foydalanuvchilar birlashtirildi (ID {secondary_user_id} → {primary_user_id})',
            f'Аккаунты объединены (ID {secondary_user_id} → {primary_user_id})',
            f'Accounts merged (ID {secondary_user_id} → {primary_user_id})',
        ), 'success')
    except Exception:
        db.conn.rollback()
        logger.exception("Failed to merge user accounts primary=%s secondary=%s", primary_user_id, secondary_user_id)
        new_alert(_msg_text('Birlashtirishda xatolik yuz berdi', 'Ошибка при объединении', 'Merge failed'), 'danger')
    return redirect(url_for('author_edit', author_id=author_id))


@bp.route('/fmadmin/users/authors/<int:author_id>/link-user', methods=['POST'])
@is_superadmin_required
def author_link_user(author_id):
    candidate_user_id = request.form.get('user_id', type=int)
    if not candidate_user_id:
        new_alert(_msg_text('Noto\'g\'ri foydalanuvchi', 'Неверный пользователь', 'Invalid user'), 'danger')
        return redirect(url_for('author_edit', author_id=author_id))

    now_ts = int(datetime.datetime.now().timestamp())
    column_cache = {}
    try:
        with db._lock:
            cursor = db.conn.cursor()
            try:
                cursor.execute("SELECT id, user_id FROM author_profile WHERE id = %s FOR UPDATE", (author_id,))
                row = cursor.fetchone()
                if not row:
                    db.conn.rollback()
                    new_alert(_msg_text('Muallif topilmadi', 'Автор не найден', 'Author not found'), 'danger')
                    return redirect(url_for('authors'))

                old_user_id = row[1]

                cursor.execute("SELECT id FROM users WHERE id = %s", (candidate_user_id,))
                if not cursor.fetchone():
                    db.conn.rollback()
                    new_alert(_msg_text('Foydalanuvchi topilmadi', 'Пользователь не найден', 'User not found'), 'danger')
                    return redirect(url_for('author_edit', author_id=author_id))

                has_updated_at = _table_column_exists(cursor, column_cache, 'author_profile', 'updated_at')
                if has_updated_at:
                    cursor.execute(
                        "UPDATE author_profile SET user_id = %s, updated_at = %s WHERE id = %s",
                        (candidate_user_id, now_ts, author_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE author_profile SET user_id = %s WHERE id = %s",
                        (candidate_user_id, author_id),
                    )

                # If the profile was linked to a different user, migrate all FK references
                # from that old user to the new (candidate) user so no records are left orphaned.
                if old_user_id and old_user_id != candidate_user_id:
                    user_ref_columns = (
                        ('author_profile', 'user_id'),
                        ('submissions', 'user_id'),
                        ('payments', 'user_id'),
                        ('user_doc_uploads', 'user_id'),
                        ('files', 'user_id'),
                        ('news', 'author_id'),
                        ('editor_assignments', 'editor_id'),
                        ('editor_assignments', 'assigned_by'),
                        ('editor_notifications', 'editor_id'),
                        ('role_notifications', 'target_user_id'),
                        ('role_notifications', 'actor_user_id'),
                        ('editorial_members', 'created_by'),
                        ('editorial_members', 'updated_by'),
                        ('email_templates', 'created_by'),
                        ('email_templates', 'updated_by'),
                    )
                    for table_name, column_name in user_ref_columns:
                        if not _table_column_exists(cursor, column_cache, table_name, column_name):
                            continue
                        cursor.execute(
                            f"UPDATE {table_name} SET {column_name} = %s WHERE {column_name} = %s",
                            (candidate_user_id, old_user_id),
                        )

                db.conn.commit()
            except Exception:
                db.conn.rollback()
                raise
            finally:
                cursor.close()

        new_alert(
            _msg_text('Asosiy foydalanuvchi bog\'landi', 'Основной пользователь привязан', 'Primary user linked'),
            'success'
        )
    except Exception:
        db.conn.rollback()
        logger.exception("Failed to link author %s with user %s", author_id, candidate_user_id)
        new_alert(
            _msg_text('Bog\'lashda xatolik yuz berdi', 'Ошибка при привязке', 'Linking failed'),
            'danger'
        )
    return redirect(url_for('author_edit', author_id=author_id))


@bp.route('/fmadmin/website/issues')
@is_superadmin_required
def issues():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    admin_lang = _admin_language()
    series_label_map = {
        item['alias']: item['name_display']
        for item in _issue_series_options(admin_lang)
    }
    # Получаем значения фильтров
    search_title = request.args.get('title', '').strip()
    search_vol_no = request.args.get('vol_no', '').strip()
    search_issue_no = request.args.get('issue_no', '').strip()
    search_status = request.args.get('status', '').strip()
    # Получаем все выпуски с учётом фильтров
    query = db.issues.all()
    if search_vol_no:
        query = query.like(vol_no=search_vol_no)
    if search_issue_no:
        query = query.like(issue_no=search_issue_no)
    if search_status:
        if search_status == 'published':
            query = query.equal(subscription_enable=True)
        elif search_status == 'draft':
            query = query.equal(subscription_enable=False)

    issues = query.exec()
    if search_title:
        title_query = search_title.lower()
        issues = [
            issue for issue in issues
            if title_query in _clean_text(issue.get('title')).lower()
            or title_query in _clean_text(issue.get('title_uz')).lower()
            or title_query in _clean_text(issue.get('title_ru')).lower()
        ]

    total_issues = len(issues)
    start = max(page - 1, 0) * per_page
    end = start + per_page
    issues = issues[start:end]
    total_pages = (total_issues + per_page - 1) // per_page
    # Получаем все публикации для подсчёта статей по выпускам
    publications = db.publications.all().exec()
    issue_article_count = {}
    for issue in issues:
        issue['title_display'] = _localized_content_field(issue, 'title', admin_lang, strict=True)
        issue_category = _clean_text(issue.get('category'))
        issue['series_display'] = series_label_map.get(issue_category, issue_category)
        issue_article_count[issue['id']] = sum(1 for p in publications if p['issue_id'] == issue['id'])
    # Формируем query_string для пагинации (без page)
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    return render_template('website/issues/issues.html', issues=issues, page=page, total_issues=total_issues, total_pages=total_pages,
                           issue_article_count=issue_article_count,
                           search_title=search_title, search_vol_no=search_vol_no, search_issue_no=search_issue_no, search_status=search_status,
                           pagination_query_string=pagination_query_string)

def save_file(category, file, allow_exts):
    if not file or not file.filename:
        raise ValueError('Файл не выбран')
    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
    if not ext or ext not in allow_exts:
        raise ValueError('Недопустимое расширение файла')
    now = datetime.datetime.now()
    rel_dir = f'static/uploads/{category}/{now.year}/{now.month:02d}'
    abs_dir = os.path.join(settings.SAVE_PATH, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    filename = f'{uuid.uuid4().hex}.{ext}'
    file_path = os.path.join(abs_dir, filename)
    file.save(file_path)
    return f'/{rel_dir}/{filename}'

def save_file_to_db(file, category='articles', comment=''):
    """Сохраняет файл и записывает его в таблицу files, возвращает ID файла"""
    if not file or not file.filename:
        raise ValueError('Файл не выбран')
    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
    if not ext:
        raise ValueError('Недопустимое расширение файла')
    now = datetime.datetime.now()
    rel_dir = f'static/uploads/{category}/{now.year}/{now.month:02d}'
    abs_dir = os.path.join(settings.SAVE_PATH, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    filename = f'{uuid.uuid4().hex}.{ext}'
    file_path = os.path.join(abs_dir, filename)
    file.save(file_path)
    filepath = f'/{rel_dir}/{filename}'

    # Сохраняем в таблицу files
    file_id = db.files.add(
        name=file.filename,
        filepath=filepath,
        upload_time=int(now.timestamp()),
        comment=comment,
        filesize=os.path.getsize(file_path),
        created_at=int(now.timestamp())
    ).exec()

    if isinstance(file_id, list) and file_id:
        file_id = file_id[0]['id']
    elif isinstance(file_id, dict):
        file_id = file_id.get('id')

    return file_id

# Вспомогательные функции для работы с редакторами
def get_current_user():
    """Получить текущего пользователя из сессии"""
    return _current_user_with_details()

def create_editor_notification(editor_id, assignment_id, message):
    """Создать уведомление для редактора"""
    if _parse_int(editor_id) is None or _parse_int(assignment_id) is None:
        return
    db.editor_notifications.add(
        editor_id=editor_id,
        assignment_id=assignment_id,
        message=message,
        is_read=False,
        created_at=int(datetime.datetime.now().timestamp())
    ).exec()

def get_editors(admin_id=None):
    """Получить список редакторов; для admin_id возвращает только привязанных редакторов."""
    editors = _users_with_role('editor', include_hidden=False, include_blocked=False)
    if admin_id is not None:
        admin_id = _parse_int(admin_id)
        editors = [editor for editor in editors if _parse_int(editor.get('editor_admin_id')) == admin_id]
    return editors


def _select_best_editor_for_submission(submission, candidate_editors):
    if not candidate_editors:
        return None

    submission_id = _parse_int((submission or {}).get('id'))
    track_key = _normalize_admin_track((submission or {}).get('submission_track'))
    track_text = _clean_text(track_key).lower()

    existing_assignments = []
    if submission_id is not None:
        try:
            existing_assignments = db.editor_assignments.all().equal(submission_id=submission_id).exec()
        except Exception:
            existing_assignments = []

    assigned_editor_ids = {
        _parse_int(item.get('editor_id'))
        for item in existing_assignments
        if _parse_int(item.get('editor_id')) is not None
    }

    available_editors = [
        editor for editor in candidate_editors
        if _parse_int(editor.get('id')) not in assigned_editor_ids
    ]
    if not available_editors:
        return None

    matching_editors = []
    if track_text:
        for editor in available_editors:
            specialization_text = _clean_text(editor.get('editor_specialization')).lower()
            if track_text in specialization_text:
                matching_editors.append(editor)
    pool = matching_editors or available_editors

    try:
        all_assignments = db.editor_assignments.all().exec()
    except Exception:
        all_assignments = []

    load_map = {}
    for assignment in all_assignments:
        editor_id = _parse_int(assignment.get('editor_id'))
        status = _clean_text(assignment.get('status')).lower()
        if editor_id is None or status not in EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES:
            continue
        load_map[editor_id] = load_map.get(editor_id, 0) + 1

    ranked = sorted(
        pool,
        key=lambda editor: (
            load_map.get(_parse_int(editor.get('id')), 0),
            _parse_int(editor.get('id')) or 10**9,
        )
    )
    return ranked[0] if ranked else None

def parse_date(date_str, with_time=False):
    """Парсинг даты из строки"""
    if not date_str:
        return None
    try:
        if with_time:
            return int(datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M').timestamp())
        else:
            return int(datetime.datetime.strptime(date_str, '%Y-%m-%d').timestamp())
    except Exception:
        return None

@bp.route('/fmadmin/website/issues/<int:issue_id>', methods=['GET', 'POST'])
@is_superadmin_required
def issue_edit(issue_id):
    if request.method == 'POST':
        issue_columns = set(db.columns.get('issues', []) or [])
        has_toc_column = 'table_of_contents_file' in issue_columns
        cover_image = None
        if 'cover_image' in request.files and request.files['cover_image'].filename:
            cover_image = save_file('issues', request.files['cover_image'], ['jpg', 'jpeg', 'png', 'gif', 'webp'])
        table_of_contents_file = None
        if has_toc_column and 'table_of_contents_file' in request.files and request.files['table_of_contents_file'].filename:
            table_of_contents_file = save_file('issues', request.files['table_of_contents_file'], ['pdf', 'doc', 'docx'])
        if issue_id == 0:
            title = request.form.get('title')
            title_uz = request.form.get('title_uz')
            title_ru = request.form.get('title_ru')
            vol_no = request.form.get('vol_no')
            issue_no = request.form.get('issue_no')
            year = request.form.get('year')
            category = request.form.get('category')
            shortinfo = request.form.get('shortinfo')
            shortinfo_uz = request.form.get('shortinfo_uz')
            shortinfo_ru = request.form.get('shortinfo_ru')
            price = request.form.get('price')
            price_uz = request.form.get('price_uz')
            price_ru = request.form.get('price_ru')
            subscription_enable = bool(request.form.get('subscription_enable'))
            is_paid = bool(request.form.get('is_paid'))
            created_at = parse_date(request.form.get('created_at'), with_time=False)
            create_data = dict(
                title=title,
                title_uz=title_uz,
                title_ru=title_ru,
                vol_no=vol_no,
                issue_no=issue_no,
                year=year,
                category=category,
                shortinfo=shortinfo,
                shortinfo_uz=shortinfo_uz,
                shortinfo_ru=shortinfo_ru,
                price=price,
                price_uz=price_uz,
                price_ru=price_ru,
                subscription_enable=subscription_enable,
                is_paid=is_paid,
                cover_image=cover_image,
                created_at=created_at or int(datetime.datetime.now().timestamp())
            )
            if has_toc_column:
                create_data['table_of_contents_file'] = table_of_contents_file
            issue_id_new = db.issues.add(**create_data).exec()
            if issue_id_new:
                issue_id_new = issue_id_new[0]['id']
                new_alert(_msg_text("Nashr soni muvaffaqiyatli yaratildi", 'Выпуск успешно создан', 'Issue created successfully'), 'success')
            else:
                issue_id_new = 0
                new_alert(_msg_text('Xatolik yuz berdi', 'Ошибка', 'An error occurred'), 'danger')
            return redirect(url_for('issue_edit', issue_id=issue_id_new))
        else:
            data = request.json if request.is_json else request.form
            created_at_raw = data.get('created_at')
            created_at = (
                parse_date(created_at_raw, with_time=True)
                or parse_date(created_at_raw, with_time=False)
            )
            update_data = dict(
                title=data.get('title'),
                title_uz=data.get('title_uz'),
                title_ru=data.get('title_ru'),
                vol_no=data.get('vol_no'),
                issue_no=data.get('issue_no'),
                year=data.get('year'),
                category=data.get('category'),
                shortinfo=data.get('shortinfo'),
                shortinfo_uz=data.get('shortinfo_uz'),
                shortinfo_ru=data.get('shortinfo_ru'),
                price=data.get('price'),
                price_uz=data.get('price_uz'),
                price_ru=data.get('price_ru'),
                subscription_enable=bool(data.get('subscription_enable')),
                is_paid=bool(data.get('is_paid')),
            )
            if created_at is not None:
                update_data['created_at'] = created_at
            if cover_image:
                update_data['cover_image'] = cover_image
            else:
                update_data['cover_image'] = data.get('cover_image')
            if has_toc_column:
                if table_of_contents_file:
                    update_data['table_of_contents_file'] = table_of_contents_file
                else:
                    update_data['table_of_contents_file'] = data.get('table_of_contents_file')
            db.issues.all().equal(id=issue_id).update(**update_data).exec()
            new_alert(_msg_text("Nashr soni muvaffaqiyatli saqlandi", 'Выпуск успешно сохранён', 'Issue saved successfully'), 'success')
            return redirect(url_for('issue_edit', issue_id=issue_id))

    if issue_id == 0:
        issue = {
            'id': 0,
            'title': '',
            'title_uz': '',
            'title_ru': '',
            'vol_no': '',
            'issue_no': '',
            'year': '',
            'category': '',
            'shortinfo': '',
            'shortinfo_uz': '',
            'shortinfo_ru': '',
            'price': '',
            'price_uz': '',
            'price_ru': '',
            'subscription_enable': False,
            'is_paid': False,
            'cover_image': '',
            'table_of_contents_file': '',
            'created_at': None
        }
    else:
        issue = db.issues.all().equal(id=issue_id).exec()
        if not issue:
            return 'Выпуск не найден', 404
        issue = issue[0]

    admin_lang = _admin_language()
    issue_categories = _issue_series_options(admin_lang)
    return render_template('website/issues/edit.html', issue=issue, issue_categories = issue_categories)



@bp.route('/fmadmin/website/articles')
@is_superadmin_required
def articles():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    admin_lang = _admin_language()
    # Получаем значения фильтров
    search_title = request.args.get('title', '').strip()
    search_author = request.args.get('author', '').strip()
    search_orcid = request.args.get('orcid', '').strip()
    search_orcid_by_name = request.args.get('search_orcid_by_name', '')
    search_issue = request.args.get('issue', '').strip()
    search_missing_page_range = request.args.get('missing_page_range', '').strip()

    # Получаем всех авторов и строим карту id/ORCID/имя
    authors = db.author_profile.all().exec()
    authors_map = {a['id']: a for a in authors}
    orcid_to_id = {a['orcid']: a['id'] for a in authors if a['orcid']}
    name_to_id = {a['name']: a['id'] for a in authors if a['name']}

    # Получаем все выпуски
    issues = db.issues.all().exec()
    issues_map = {i['id']: i for i in issues}

    # Формируем запрос к публикациям
    query = db.publications.all()
    if search_issue:
        try:
            query = query.equal(issue_id=int(search_issue))
        except Exception:
            pass
    # Фильтр по автору (по имени или id)
    if search_author:
        author_ids = [aid for name, aid in name_to_id.items() if search_author.lower() in name.lower()]
        if author_ids:
            query = query.any(main_author_id=author_ids)
        else:
            query = query.any(main_author_id=[-1])
    # Фильтр по ORCID
    if search_orcid:
        if search_orcid_by_name:
            # Поиск по полному имени в поле ORCID
            author_ids = [aid for name, aid in name_to_id.items() if search_orcid.lower() in name.lower()]
            if author_ids:
                query = query.any(main_author_id=author_ids)
            else:
                query = query.any(main_author_id=[-1])
        else:
            # Обычный поиск по ORCID
            author_id = orcid_to_id.get(search_orcid)
            if author_id:
                query = query.any(main_author_id=[author_id])
            else:
                query = query.any(main_author_id=[-1])

    articles = query.exec()
    if search_title:
        title_query = search_title.lower()
        articles = [
            article for article in articles
            if title_query in _clean_text(article.get('title')).lower()
            or title_query in _clean_text(article.get('title_uz')).lower()
            or title_query in _clean_text(article.get('title_ru')).lower()
        ]
    if search_missing_page_range:
        articles = [
            article for article in articles
            if not _clean_text(article.get('page_range'))
        ]

    total_articles = len(articles)
    start = max(page - 1, 0) * per_page
    end = start + per_page
    articles = articles[start:end]
    total_pages = (total_articles + per_page - 1) // per_page

    for article in articles:
        article['title_display'] = _localized_content_field(article, 'title', admin_lang, strict=True)

    # Формируем query_string для пагинации (без page)
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)

    return render_template('website/articles/articles.html', articles=articles, authors_map=authors_map, issues_map=issues_map,
                           page=page, total_articles=total_articles, total_pages=total_pages,
                           search_title=search_title, search_author=search_author, search_orcid=search_orcid, search_orcid_by_name=search_orcid_by_name, search_issue=search_issue, search_missing_page_range=search_missing_page_range,
                           issues=issues, pagination_query_string=pagination_query_string)

@bp.route('/fmadmin/website/articles/<int:article_id>', methods=['GET', 'POST'])
@is_superadmin_required
def article_edit(article_id):
    _ensure_publication_metadata_columns()
    admin_lang = _admin_language()
    metadata_labels = publication_metadata_field_labels(admin_lang)
    author_position_options = publication_metadata_options('author_position_key', admin_lang)
    academic_title_options = publication_metadata_options('academic_title_key', admin_lang)
    academic_degree_options = publication_metadata_options('academic_degree_key', admin_lang)
    series_options = publication_metadata_options('series_key', admin_lang)

    if request.method == 'POST':        
        title = request.form.get('title')
        title_uz = request.form.get('title_uz')
        title_ru = request.form.get('title_ru')
        abstract = request.form.get('abstract')
        abstract_uz = request.form.get('abstract_uz')
        abstract_ru = request.form.get('abstract_ru')
        keywords = request.form.get('keywords')
        if keywords:
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        else:
            keywords = []

        keywords_uz = request.form.get('keywords_uz')
        if keywords_uz:
            keywords_uz = [k.strip() for k in keywords_uz.split(',') if k.strip()]
        else:
            keywords_uz = []

        keywords_ru = request.form.get('keywords_ru')
        if keywords_ru:
            keywords_ru = [k.strip() for k in keywords_ru.split(',') if k.strip()]
        else:
            keywords_ru = []
        additional = request.form.get('additional')
        main_author_id = request.form.get('main_author_id') or None
        subauthor_ids = request.form.getlist('subauthor_ids')
        subauthor_ids = [int(i) for i in subauthor_ids if i]
        issue_id = request.form.get('issue_id') or None
        doi = request.form.get('doi')
        doi_link = request.form.get('doi_link')
        page_range = _normalize_article_page_range(request.form.get('page_range'))
        title = _clean_text(title)
        if not title:
            new_alert(
                _msg_text(
                    "Inglizcha sarlavha majburiy",
                    "Английский заголовок обязателен",
                    "English title is required"
                ),
                'danger'
            )
            return redirect(url_for('article_edit', article_id=article_id))
        if not page_range:
            new_alert(
                _msg_text(
                    "Maqola betlari (page range) majburiy. Masalan: 7-26",
                    "Диапазон страниц обязателен. Например: 7-26",
                    "Page range is required. Example: 7-26"
                ),
                'danger'
            )
            return redirect(url_for('article_edit', article_id=article_id))
        author_position_key = normalize_publication_metadata_key('author_position_key', request.form.get('author_position_key'))
        academic_title_key = normalize_publication_metadata_key('academic_title_key', request.form.get('academic_title_key'))
        academic_degree_key = normalize_publication_metadata_key('academic_degree_key', request.form.get('academic_degree_key'))
        series_key = normalize_publication_metadata_key('series_key', request.form.get('series_key'))
        publication_columns = set(db.columns.get('publications', []))
        metadata_payload = {}
        if 'author_position_key' in publication_columns:
            metadata_payload['author_position_key'] = author_position_key
        if 'academic_title_key' in publication_columns:
            metadata_payload['academic_title_key'] = academic_title_key
        if 'academic_degree_key' in publication_columns:
            metadata_payload['academic_degree_key'] = academic_degree_key
        if 'series_key' in publication_columns:
            metadata_payload['series_key'] = series_key
        if 'page_range' in publication_columns:
            metadata_payload['page_range'] = page_range
        date_sent = parse_date(request.form.get('date_sent'), with_time=True)
        date_accept = parse_date(request.form.get('date_accept'), with_time=True)
        date_publish = parse_date(request.form.get('date_publish'), with_time=True)
        comments = request.form.get('comments')
        # Обработка загруженных PDF файлов
        file_ids = []

        # Получаем существующие file_ids если они есть
        existing_file_ids = request.form.get('file_ids')
        if existing_file_ids:
            file_ids = [int(f.strip()) for f in existing_file_ids.split(',') if f.strip().isdigit()]

        # Обрабатываем новые загруженные файлы
        uploaded_files = request.files.getlist('pdf_files')
        for file in uploaded_files:
            if file and file.filename and file.filename.lower().endswith('.pdf'):
                try:
                    file_id = save_file_to_db(file, 'articles', f'PDF для статьи {article_id}')
                    if file_id:
                        file_ids.append(file_id)
                except Exception:
                    logger.exception('Failed to upload PDF file for article_id=%s', article_id)
                    new_alert(
                        _msg_text(
                            f'{file.filename} faylini yuklashda xatolik',
                            f'Ошибка загрузки файла {file.filename}',
                            f'File upload error: {file.filename}'
                        ),
                        'danger'
                    )
        is_paid = bool(request.form.get('is_paid'))
        price = request.form.get('price', 0, float)
        price_uz = request.form.get('price_uz', 0, float)
        price_ru = request.form.get('price_ru', 0, float)
        subscription_enable = bool(request.form.get('subscription_enable'))
        created_at = parse_date(request.form.get('created_at'), with_time=True)
        
        if article_id == 0:
            article_id_new = db.publications.add(
                title=title,
                title_uz=title_uz,
                title_ru=title_ru,
                abstract=abstract,
                abstract_uz=abstract_uz,
                abstract_ru=abstract_ru,
                keywords=keywords,
                keywords_uz=keywords_uz,
                keywords_ru=keywords_ru,
                additional=additional,
                main_author_id=main_author_id,
                subauthor_ids=subauthor_ids,
                issue_id=issue_id,
                doi=doi,
                doi_link=doi_link,
                **metadata_payload,
                date_sent=date_sent,
                date_accept=date_accept,
                date_publish=date_publish,
                comments=comments,
                file_ids=file_ids,
                is_paid=is_paid,
                price=price,
                price_uz=price_uz,
                price_ru=price_ru,
                subscription_enable=subscription_enable,
                current_views = 0,
                created_at=created_at or int(datetime.datetime.now().timestamp())
            ).exec()
            new_alert(_msg_text('Maqola muvaffaqiyatli yaratildi', 'Статья успешно создана', 'Article created successfully'), 'success')
            return redirect(url_for('article_edit', article_id=article_id_new[0]['id']))
        else:
            db.publications.all().equal(id=article_id).update(
                title=title,
                title_uz=title_uz,
                title_ru=title_ru,
                abstract=abstract,
                abstract_uz=abstract_uz,
                abstract_ru=abstract_ru,
                keywords=keywords,
                keywords_uz=keywords_uz,
                keywords_ru=keywords_ru,
                additional=additional,
                main_author_id=main_author_id,
                subauthor_ids=subauthor_ids,
                issue_id=issue_id,
                doi=doi,
                doi_link=doi_link,
                **metadata_payload,
                date_sent=date_sent,
                date_accept=date_accept,
                date_publish=date_publish,
                comments=comments,
                file_ids=file_ids,
                is_paid=is_paid,
                price=price,
                price_uz=price_uz,
                price_ru=price_ru,
                subscription_enable=subscription_enable,
                created_at=created_at
            ).exec()
            new_alert(_msg_text('Maqola muvaffaqiyatli saqlandi', 'Статья успешно сохранена', 'Article saved successfully'), 'success')
            return redirect(url_for('article_edit', article_id=article_id))

    if article_id == 0:
        article = {
            'id': 0,
            'title': '',
            'title_uz': '',
            'title_ru': '',
            'abstract': '',
            'abstract_uz': '',
            'abstract_ru': '',
            'keywords': [],
            'keywords_uz': [],
            'keywords_ru': [],
            'additional': '',
            'main_author_id': None,
            'subauthor_ids': [],
            'issue_id': None,
            'doi': '',
            'doi_link': '',
            'page_range': '',
            'author_position_key': '',
            'academic_title_key': '',
            'academic_degree_key': '',
            'series_key': '',
            'date_sent': None,
            'date_accept': None,
            'date_publish': None,
            'comments': '',
            'file_ids': [],
            'is_paid': False,
            'price': '',
            'price_uz': '',
            'price_ru': '',
            'subscription_enable': False,
            'created_at': None
        }
    else:
        article = db.publications.all().equal(id=article_id).exec()
        if not article:
            return 'Статья не найдена', 404
        article = article[0]
    authors = db.author_profile.all().exec()
    issues = db.issues.all().exec()
    return render_template(
        'website/articles/edit.html',
        article=article,
        authors=authors,
        issues=issues,
        metadata_labels=metadata_labels,
        author_position_options=author_position_options,
        academic_title_options=academic_title_options,
        academic_degree_options=academic_degree_options,
        series_options=series_options,
    )

@bp.route('/fmadmin/website/articles/<int:article_id>/content', methods=['GET', 'POST'])
@is_superadmin_required
def article_content(article_id):
    if request.method == 'POST':
        move_block_id = request.form.get('move_block_id')
        move_dir = request.form.get('move_dir')
        if move_block_id and move_dir:
            # Получить все блоки с order_id
            parts = db.publication_parts.all().equal(publication_id=article_id).order_by('order_id').exec()
            figures = db.publication_figures.all().equal(publication_id=article_id).order_by('order_id').exec()
            blocks = []
            for p in parts:
                blocks.append({'id': p['id'], 'order_id': p.get('order_id', 0), 'table': 'publication_parts'})
            for f in figures:
                blocks.append({'id': f['id'], 'order_id': f.get('order_id', 0), 'table': 'publication_figures'})
            blocks.sort(key=lambda x: x['order_id'])
            idx = next((i for i, b in enumerate(blocks) if str(b['id']) == str(move_block_id)), None)
            if idx is not None:
                if move_dir == 'up' and idx > 0:
                    a, b = blocks[idx], blocks[idx-1]
                elif move_dir == 'down' and idx < len(blocks)-1:
                    a, b = blocks[idx], blocks[idx+1]
                else:
                    return redirect(url_for('article_content', article_id=article_id))
                # Поменять order_id местами
                db.__getattr__(a['table']).all().equal(id=a['id']).update(order_id=b['order_id']).exec()
                db.__getattr__(b['table']).all().equal(id=b['id']).update(order_id=a['order_id']).exec()
            return redirect(url_for('article_content', article_id=article_id))
        delete_block_id = request.form.get('delete_block_id')
        if delete_block_id:
            db.publication_parts.all().equal(id=delete_block_id).delete().exec()
            db.publication_figures.all().equal(id=delete_block_id).delete().exec()
            return redirect(url_for('article_content', article_id=article_id))
        block_id = request.form.get('block_id')
        block_type = request.form.get('block_type')
        block_title = _clean_text(request.form.get('block_title'))
        if block_type == 'text':
            block_text = _sanitize_article_block_html(request.form.get('block_text'))
            if block_id:
                db.publication_parts.all().equal(id=block_id).update(
                    title=block_title,
                    content=block_text
                ).exec()
            else:
                max_order = 0
                parts = db.publication_parts.all().equal(publication_id=article_id).exec()
                figures = db.publication_figures.all().equal(publication_id=article_id).exec()
                for p in parts:
                    if p.get('order_id', 0) > max_order:
                        max_order = p.get('order_id', 0)
                for f in figures:
                    if f.get('order_id', 0) > max_order:
                        max_order = f.get('order_id', 0)
                db.publication_parts.add(
                    publication_id=article_id,
                    title=block_title,
                    content=block_text,
                    order_id=max_order + 1,
                    created_at=int(datetime.datetime.now().timestamp())
                ).exec()
        elif block_type == 'image':
            file = request.files.get('block_image')
            image_desc = request.form.get('block_image_desc')
            filepath = None
            if file and file.filename:
                try:
                    filepath = save_file('figures', file, ['jpg', 'jpeg', 'png', 'gif', 'webp'])
                except ValueError:
                    new_alert(_msg_text("Fayl formati noto'g'ri", 'Недопустимый формат файла', 'Invalid file format'), 'danger')
                    return redirect(url_for('article_content', article_id=article_id))
            if block_id:
                db.publication_figures.all().equal(id=block_id).update(
                    title=image_desc,
                    filepath=filepath if filepath else None
                ).exec()
            else:
                max_order = 0
                parts = db.publication_parts.all().equal(publication_id=article_id).exec()
                figures = db.publication_figures.all().equal(publication_id=article_id).exec()
                for p in parts:
                    if p.get('order_id', 0) > max_order:
                        max_order = p.get('order_id', 0)
                for f in figures:
                    if f.get('order_id', 0) > max_order:
                        max_order = f.get('order_id', 0)
                db.publication_figures.add(
                    publication_id=article_id,
                    title=image_desc,
                    filepath=filepath,
                    order_id=max_order + 1,
                    created_at=int(datetime.datetime.now().timestamp())
                ).exec()
        elif block_type == 'table':
            pass
        return redirect(url_for('article_content', article_id=article_id))
    # GET: собрать контент из двух таблиц
    parts = db.publication_parts.all().equal(publication_id=article_id).order_by('order_id').exec()
    figures = db.publication_figures.all().equal(publication_id=article_id).order_by('order_id').exec()
    content_list = []
    for p in parts:
        content_list.append({'id': p.get('id'), 'type': 'text', 'title': p.get('title', ''), 'text': p.get('content', ''), 'order_id': p.get('order_id', 0)})
    for f in figures:
        content_list.append({'id': f.get('id'), 'type': 'image', 'image': f.get('filepath', ''), 'image_desc': f.get('title', ''), 'order_id': f.get('order_id', 0)})
    content_list.sort(key=lambda x: x.get('order_id', 0))
    article = db.publications.all().equal(id=article_id).exec()
    article = article[0] if article else None
    return render_template('website/articles/content.html', article_id=article_id, content_list=content_list, article=article)

@bp.route('/fmadmin/website/news')
@is_superadmin_required
def news():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = db.news.all().equal(type='news')
    total_news = query.copy().count().exec()
    news_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_news + per_page - 1) // per_page
    # Формируем query_string для пагинации (без page)
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    return render_template('website/news/news.html', news_list=news_list, page=page, total_news=total_news, total_pages=total_pages, pagination_query_string=pagination_query_string)

@bp.route('/fmadmin/website/announcements')
@is_superadmin_required
def announcements():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = db.news.all().equal(type='announcement')
    total_announcements = query.copy().count().exec()
    announcements_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_announcements + per_page - 1) // per_page
    # Формируем query_string для пагинации (без page)
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    return render_template('website/announcements.html', announcements_list=announcements_list, page=page, total_announcements=total_announcements, total_pages=total_pages, pagination_query_string=pagination_query_string)

@bp.route('/fmadmin/website/tariffs')
@is_superadmin_required
def tariffs():
    _ensure_tariff_duration_column()
    _ensure_tariff_archive_column()
    _ensure_tariff_entitlement_columns()
    tariffs = db.tariffs.all().exec()
    tariffs = [item for item in tariffs if not _is_tariff_archived(item)]
    # Считаем количество пользователей на каждом тарифе
    users = db.users.all().exec()
    tariffs_user_count = {}
    for t in tariffs:
        tariffs_user_count[t['id']] = sum(1 for u in users if u.get('tariff_id') == t['id'])
    return render_template('website/tariffs.html', tariffs=tariffs, tariffs_user_count=tariffs_user_count)

@bp.route('/fmadmin/website/translations')
@is_superadmin_required
def translations():
    search = request.args.get('search', '').strip()
    translations = db.translations.all().exec()
    if search:
        search_lower = search.lower()
        translations = [t for t in translations if search_lower in (t.get('alias') or '').lower() or search_lower in (t.get('content') or '').lower() or search_lower in (t.get('content_uz') or '').lower() or search_lower in (t.get('content_ru') or '').lower()]
    translations = sorted(translations, key=lambda item: (item.get('alias') or '').lower())
    return render_template('website/translations.html', translations=translations, search=search)


def _email_template_form_payload(form_data):
    alias = _normalize_email_template_alias(form_data.get('alias'))
    name = _clean_text(form_data.get('name'))
    description = _clean_text(form_data.get('description'))

    subject_uz = _clean_text(form_data.get('subject_uz'))
    subject_ru = _clean_text(form_data.get('subject_ru'))
    subject_en = _clean_text(form_data.get('subject_en'))

    intro_uz = _clean_text(form_data.get('intro_uz'))
    intro_ru = _clean_text(form_data.get('intro_ru'))
    intro_en = _clean_text(form_data.get('intro_en'))

    body_uz = _clean_text(form_data.get('body_uz'))
    body_ru = _clean_text(form_data.get('body_ru'))
    body_en = _clean_text(form_data.get('body_en'))

    cta_label_uz = _clean_text(form_data.get('cta_label_uz'))
    cta_label_ru = _clean_text(form_data.get('cta_label_ru'))
    cta_label_en = _clean_text(form_data.get('cta_label_en'))

    variables_csv = form_data.get('variables_csv')
    explicit_variables = _parse_template_variables_csv(variables_csv)
    inferred_variables = _collect_template_variables(
        subject_uz, subject_ru, subject_en,
        intro_uz, intro_ru, intro_en,
        body_uz, body_ru, body_en,
        cta_label_uz, cta_label_ru, cta_label_en,
    )
    variables = sorted(set(explicit_variables) | set(inferred_variables))

    is_active = bool(form_data.get('is_active'))
    now_ts = int(time.time())

    return {
        'alias': alias,
        'name': name or alias,
        'description': description,
        'variables': variables,
        'subject_uz': subject_uz,
        'subject_ru': subject_ru,
        'subject_en': subject_en,
        'intro_uz': intro_uz,
        'intro_ru': intro_ru,
        'intro_en': intro_en,
        'body_uz': body_uz,
        'body_ru': body_ru,
        'body_en': body_en,
        'cta_label_uz': cta_label_uz,
        'cta_label_ru': cta_label_ru,
        'cta_label_en': cta_label_en,
        'is_active': is_active,
        'updated_at': now_ts,
    }


def _email_template_preview_payload(template_row):
    sample_values = {
        'name': 'Ali Valiyev',
        'editor_name': 'Dilnoza Rahimova',
        'title': 'Tilshunoslikda yangi yondashuvlar',
        'time_left': '6 soat',
        'deadline_type': 'tahriz topshirish',
        'link': settings.APP_BASE_URL or 'https://example.com',
    }

    return {
        'sample_values': sample_values,
        'variables': _collect_template_variables(
            template_row.get('subject_uz'),
            template_row.get('subject_ru'),
            template_row.get('subject_en'),
            template_row.get('intro_uz'),
            template_row.get('intro_ru'),
            template_row.get('intro_en'),
            template_row.get('body_uz'),
            template_row.get('body_ru'),
            template_row.get('body_en'),
            template_row.get('cta_label_uz'),
            template_row.get('cta_label_ru'),
            template_row.get('cta_label_en'),
        ),
        'rendered': {
            'subject_uz': _render_template_preview_text(template_row.get('subject_uz'), sample_values),
            'subject_ru': _render_template_preview_text(template_row.get('subject_ru'), sample_values),
            'subject_en': _render_template_preview_text(template_row.get('subject_en'), sample_values),
            'intro_uz': _render_template_preview_text(template_row.get('intro_uz'), sample_values),
            'intro_ru': _render_template_preview_text(template_row.get('intro_ru'), sample_values),
            'intro_en': _render_template_preview_text(template_row.get('intro_en'), sample_values),
            'body_uz': _render_template_preview_text(template_row.get('body_uz'), sample_values),
            'body_ru': _render_template_preview_text(template_row.get('body_ru'), sample_values),
            'body_en': _render_template_preview_text(template_row.get('body_en'), sample_values),
            'cta_label_uz': _render_template_preview_text(template_row.get('cta_label_uz'), sample_values),
            'cta_label_ru': _render_template_preview_text(template_row.get('cta_label_ru'), sample_values),
            'cta_label_en': _render_template_preview_text(template_row.get('cta_label_en'), sample_values),
        }
    }


@bp.route('/fmadmin/website/email-templates')
@is_superadmin_required
def email_templates():
    if not _ensure_email_templates_ready(force_schema_sync=True):
        flash('Email templates jadvali tayyor emas. Iltimos, administratorga murojaat qiling.', 'danger')
        return redirect(url_for('index'))
    search = _clean_text(request.args.get('search')).lower()
    templates = db.email_templates.all().exec()
    if search:
        templates = [
            item for item in templates
            if search in _clean_text(item.get('alias')).lower()
            or search in _clean_text(item.get('name')).lower()
            or search in _clean_text(item.get('description')).lower()
        ]

    for item in templates:
        item['variables'] = item.get('variables') or []
    templates = sorted(templates, key=lambda item: _clean_text(item.get('alias')).lower())
    return render_template('website/email_templates/list.html', templates=templates, search=search)


@bp.route('/fmadmin/website/email-templates/new', methods=['GET', 'POST'])
@is_superadmin_required
def email_template_create():
    if not _ensure_email_templates_ready(force_schema_sync=True):
        flash('Email templates jadvali tayyor emas. Iltimos, administratorga murojaat qiling.', 'danger')
        return redirect(url_for('index'))
    current_user_id = _parse_int((session.get('fmadmin_user') or {}).get('id'))

    if request.method == 'POST':
        payload = _email_template_form_payload(request.form)
        if not payload['alias']:
            flash('Alias noto\'g\'ri. Faqat a-z, 0-9 va _ ishlatiladi.', 'danger')
            return render_template(
                'website/email_templates/edit.html',
                template_row=payload,
                is_new=True,
                preview=_email_template_preview_payload(payload),
            )

        exists = db.email_templates.all().equal(alias=payload['alias']).exec()
        if exists:
            flash('Bunday alias allaqachon mavjud.', 'danger')
            return render_template(
                'website/email_templates/edit.html',
                template_row=payload,
                is_new=True,
                preview=_email_template_preview_payload(payload),
            )

        payload['created_at'] = payload['updated_at']
        payload['created_by'] = current_user_id
        payload['updated_by'] = current_user_id
        created = db.email_templates.add(**payload).exec()
        template_id = _extract_inserted_id(created)

        flash('Email shabloni yaratildi.', 'success')
        if template_id is not None:
            return redirect(url_for('email_template_edit', template_id=template_id))
        return redirect(url_for('email_templates'))

    initial_row = {
        'alias': '',
        'name': '',
        'description': '',
        'variables': [],
        'subject_uz': '',
        'subject_ru': '',
        'subject_en': '',
        'intro_uz': '',
        'intro_ru': '',
        'intro_en': '',
        'body_uz': '',
        'body_ru': '',
        'body_en': '',
        'cta_label_uz': '',
        'cta_label_ru': '',
        'cta_label_en': '',
        'is_active': True,
    }
    return render_template(
        'website/email_templates/edit.html',
        template_row=initial_row,
        is_new=True,
        preview=_email_template_preview_payload(initial_row),
    )


@bp.route('/fmadmin/website/email-templates/<int:template_id>', methods=['GET', 'POST'])
@is_superadmin_required
def email_template_edit(template_id):
    if not _ensure_email_templates_ready(force_schema_sync=True):
        flash('Email templates jadvali tayyor emas. Iltimos, administratorga murojaat qiling.', 'danger')
        return redirect(url_for('index'))
    current_user_id = _parse_int((session.get('fmadmin_user') or {}).get('id'))

    rows = db.email_templates.all().equal(id=template_id).exec()
    if not rows:
        flash('Email shabloni topilmadi.', 'danger')
        return redirect(url_for('email_templates'))

    template_row = rows[0]

    if request.method == 'POST':
        payload = _email_template_form_payload(request.form)
        if not payload['alias']:
            flash('Alias noto\'g\'ri. Faqat a-z, 0-9 va _ ishlatiladi.', 'danger')
            merged = dict(template_row)
            merged.update(payload)
            return render_template(
                'website/email_templates/edit.html',
                template_row=merged,
                is_new=False,
                preview=_email_template_preview_payload(merged),
            )

        exists = db.email_templates.all().equal(alias=payload['alias']).exec()
        for row in exists:
            if _parse_int(row.get('id')) != template_id:
                flash('Bunday alias allaqachon mavjud.', 'danger')
                merged = dict(template_row)
                merged.update(payload)
                return render_template(
                    'website/email_templates/edit.html',
                    template_row=merged,
                    is_new=False,
                    preview=_email_template_preview_payload(merged),
                )

        payload['updated_by'] = current_user_id
        db.email_templates.all().equal(id=template_id).update(**payload).exec()
        flash('Email shabloni saqlandi.', 'success')
        return redirect(url_for('email_template_edit', template_id=template_id))

    template_row['variables'] = template_row.get('variables') or []
    return render_template(
        'website/email_templates/edit.html',
        template_row=template_row,
        is_new=False,
        preview=_email_template_preview_payload(template_row),
    )


@bp.route('/fmadmin/website/email-templates/<int:template_id>/delete', methods=['POST'])
@is_superadmin_required
def email_template_delete(template_id):
    if not _ensure_email_templates_ready(force_schema_sync=True):
        flash('Email templates jadvali tayyor emas. Iltimos, administratorga murojaat qiling.', 'danger')
        return redirect(url_for('index'))
    rows = db.email_templates.all().equal(id=template_id).exec()
    if not rows:
        flash('Email shabloni topilmadi.', 'danger')
        return redirect(url_for('email_templates'))

    db.email_templates.all().equal(id=template_id).delete().exec()
    flash('Email shabloni o\'chirildi.', 'success')
    return redirect(url_for('email_templates'))


@bp.route('/fmadmin/website/home-videos', methods=['GET', 'POST'])
@is_superadmin_required
def home_videos():
    base_usage_url = _get_site_setting(HOME_VIDEO_USAGE_KEY)
    base_submission_url = _get_site_setting(HOME_VIDEO_SUBMISSION_KEY)
    site_usage_urls = {}
    submission_urls = {}
    for lang in HOME_VIDEO_LANGS:
        site_usage_urls[lang] = _get_site_setting(_home_video_key(HOME_VIDEO_USAGE_KEY, lang)) or base_usage_url
        submission_urls[lang] = _get_site_setting(_home_video_key(HOME_VIDEO_SUBMISSION_KEY, lang)) or base_submission_url

    if request.method == 'POST':
        ok_all = True
        for lang in HOME_VIDEO_LANGS:
            site_key = _home_video_key(HOME_VIDEO_USAGE_KEY, lang)
            submission_key = _home_video_key(HOME_VIDEO_SUBMISSION_KEY, lang)
            site_value = _clean_text(request.form.get(f'site_usage_url_{lang}'))
            submission_value = _clean_text(request.form.get(f'submission_url_{lang}'))
            ok_all = _set_site_setting(site_key, site_value) and ok_all
            ok_all = _set_site_setting(submission_key, submission_value) and ok_all

        if ok_all:
            flash("Videolar saqlandi", "success")
        else:
            flash("Saqlashda xatolik yuz berdi", "danger")
        return redirect(url_for('home_videos'))

    return render_template(
        'website/home_videos.html',
        site_usage_urls=site_usage_urls,
        submission_urls=submission_urls
    )


@bp.route('/fmadmin/website/payment-guide', methods=['GET', 'POST'])
@is_superadmin_required
def payment_guide_settings():
    guide_values = {}
    guide_defaults = {}
    for lang in PAYMENT_GUIDE_LANGS:
        guide_values[lang] = _get_site_setting(f"{PAYMENT_GUIDE_KEY}_{lang}")
        guide_defaults[lang] = _default_payment_guide_html(lang)

    if request.method == 'POST':
        ok_all = True
        fallback_value = ''
        for lang in PAYMENT_GUIDE_LANGS:
            field_name = f'payment_guide_{lang}'
            value = _clean_text(request.form.get(field_name))
            ok_all = _set_site_setting(f"{PAYMENT_GUIDE_KEY}_{lang}", value) and ok_all
            if not fallback_value and value:
                fallback_value = value

        if fallback_value:
            ok_all = _set_site_setting(PAYMENT_GUIDE_KEY, fallback_value) and ok_all

        if ok_all:
            flash("To'lov yo'riqnomasi saqlandi", "success")
        else:
            flash("Saqlashda xatolik yuz berdi", "danger")
        return redirect(url_for('payment_guide_settings'))

    return render_template(
        'website/payment_guide.html',
        guide_values=guide_values,
        guide_defaults=guide_defaults
    )

@bp.route('/fmadmin/website/news/edit/<int:news_id>', methods=['GET', 'POST'])
@is_superadmin_required
def news_edit(news_id):
    if request.method == 'POST':
        title_ru = request.form.get('title_ru', '')
        title_uz = request.form.get('title_uz', '')
        title = request.form.get('title_en', '')
        content_ru = request.form.get('content_ru', '')
        content_uz = request.form.get('content_uz', '')
        content = request.form.get('content_en', '')
        status = request.form.get('status', 'draft')
        published_at = parse_date(request.form.get('published_at'), with_time=False)
        cover_image = None
        if 'cover_image' in request.files and request.files['cover_image'].filename:
            try:
                cover_image = save_file(
                    'news',
                    request.files['cover_image'],
                    ['jpg', 'jpeg', 'png', 'gif', 'webp']
                )
            except ValueError as err:
                flash(str(err), 'danger')
                return redirect(url_for('news_edit', news_id=news_id))
        if news_id == 0:
            new_id = db.news.add(
                type='news',
                title=title,
                title_ru=title_ru,
                title_uz=title_uz,
                content=content,
                content_ru=content_ru,
                content_uz=content_uz,
                status=status,
                published_at=published_at,
                cover_image=cover_image,
                created_at=int(datetime.datetime.now().timestamp())
            ).exec()
            if isinstance(new_id, list):
                new_id = new_id[0]['id']
            elif isinstance(new_id, dict) and 'id' in new_id:
                new_id = new_id['id']
            return redirect(url_for('news_edit', news_id=new_id))
        else:
            news = {
                'id': news_id,
                'title': title,
                'title_ru': title_ru,
                'title_uz': title_uz,
                'content': content,
                'content_ru': content_ru,
                'content_uz': content_uz,
                'status': status,
                'published_at': published_at,
            }
            if cover_image:
                news['cover_image'] = cover_image
            _res = db.news.all().equal(id=news_id).update(**{k: v for k, v in news.items() if v is not None}).exec()
            if _res:
                flash(_msg_text('Yangilik muvaffaqiyatli saqlandi', 'Новость успешно сохранена', 'News saved successfully'), 'success')
            else:
                flash(_msg_text('Yangilikni saqlashda xatolik yuz berdi', 'Ошибка при сохранении новости', 'Failed to save news'), 'danger')
            return redirect(url_for('news_edit', news_id=news_id))
    news = db.news.all().equal(id=news_id).exec()
    if not news and news_id != 0:
        return 'Новость не найдена', 404
    news = news[0] if news else {
        'id': 0,
        'title': '',
        'title_ru': '',
        'title_uz': '',
        'content': '',
        'content_ru': '',
        'content_uz': '',
        'status': 'draft',
        'published_at': None,
        'cover_image': ''
    }
    return render_template('website/news/news_edit.html', news_id=news_id, news=news)

@bp.route('/fmadmin/website/announcements/edit/<int:announcement_id>', methods=['GET', 'POST'])
@is_superadmin_required
def announcement_edit(announcement_id):
    if request.method == 'POST':
        title_ru = request.form.get('title_ru', '')
        title_uz = request.form.get('title_uz', '')
        title = request.form.get('title_en', '')
        content_ru = request.form.get('content_ru', '')
        content_uz = request.form.get('content_uz', '')
        content = request.form.get('content_en', '')
        status = request.form.get('status', 'draft')
        published_at = parse_date(request.form.get('published_at'), with_time=False)
        cover_image = None
        if 'cover_image' in request.files and request.files['cover_image'].filename:
            try:
                cover_image = save_file(
                    'announcements',
                    request.files['cover_image'],
                    ['jpg', 'jpeg', 'png', 'gif', 'webp']
                )
            except ValueError as err:
                flash(str(err), 'danger')
                return redirect(url_for('announcement_edit', announcement_id=announcement_id))
        if announcement_id == 0:
            new_id = db.news.add(
                type='announcement',
                title=title,
                title_ru=title_ru,
                title_uz=title_uz,
                content=content,
                content_ru=content_ru,
                content_uz=content_uz,
                status=status,
                published_at=published_at,
                cover_image=cover_image,
                created_at=int(datetime.datetime.now().timestamp())
            ).exec()
            if isinstance(new_id, list):
                new_id = new_id[0]['id']
            elif isinstance(new_id, dict) and 'id' in new_id:
                new_id = new_id['id']
            return redirect(url_for('announcement_edit', announcement_id=new_id))
        else:
            announcement = {
                'id': announcement_id,
                'title': title,
                'title_ru': title_ru,
                'title_uz': title_uz,
                'content': content,
                'content_ru': content_ru,
                'content_uz': content_uz,
                'status': status,
                'published_at': published_at,
            }
            if cover_image:
                announcement['cover_image'] = cover_image
            _res = db.news.all().equal(id=announcement_id).update(**{k: v for k, v in announcement.items() if v is not None}).exec()
            if _res:
                flash(_msg_text("E'lon muvaffaqiyatli saqlandi", 'Объявление успешно сохранено', 'Announcement saved successfully'), 'success')
            else:
                flash(_msg_text("E'lonni saqlashda xatolik yuz berdi", 'Ошибка при сохранении объявления', 'Failed to save announcement'), 'danger')
            return redirect(url_for('announcement_edit', announcement_id=announcement_id))
    announcement = db.news.all().equal(id=announcement_id).exec()
    if not announcement and announcement_id != 0:
        return 'Объявление не найдено', 404
    announcement = announcement[0] if announcement else {
        'id': 0,
        'title': '',
        'title_ru': '',
        'title_uz': '',
        'content': '',
        'content_ru': '',
        'content_uz': '',
        'status': 'draft',
        'published_at': None,
        'cover_image': ''
    }
    return render_template('website/announcements/announcement_edit.html', announcement_id=announcement_id, announcement=announcement)

@bp.route('/fmadmin/finance/payments')
@is_superadmin_required
def payments():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', '').strip()
    
    # Получаем все платежи, исключая unpaid
    query = db.payments.all().unequal(status='unpaid')
    
    # Фильтр по статусу
    if status_filter and status_filter in ['pending', 'paid', 'rejected']:
        query = query.equal(status=status_filter)
    
    total_payments = query.copy().count().exec()
    payments_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_payments + per_page - 1) // per_page
    
    # Формируем query_string для пагинации
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    
    # Получаем пользователей для отображения имен
    users = db.users.all().exec()
    users_map = {u['id']: u for u in users}

    tariff_ids = set()
    issue_ids = set()
    article_ids = set()
    for payment in payments_list:
        payment_type = _clean_text(payment.get('payment_type')).lower()
        ids = payment.get('ids') or []
        if not isinstance(ids, (list, tuple)):
            ids = []
        if payment_type == 'subscription' and ids:
            tariff_ids.add(ids[0])
        elif payment_type == 'issue' and ids:
            issue_ids.add(ids[0])
        elif payment_type == 'article' and ids:
            article_ids.update(ids)

    tariffs_map = {}
    if tariff_ids:
        for item in db.tariffs.any(id=list(tariff_ids)).exec():
            tariffs_map[item['id']] = translate(item)

    issues_map = {}
    if issue_ids:
        for item in db.issues.any(id=list(issue_ids)).exec():
            issues_map[item['id']] = translate(item)

    articles_map = {}
    if article_ids:
        for item in db.publications.any(id=list(article_ids)).exec():
            articles_map[item['id']] = translate(item)

    for payment in payments_list:
        payment_type = _clean_text(payment.get('payment_type')).lower()
        ids = payment.get('ids') or []
        if not isinstance(ids, (list, tuple)):
            ids = []

        if payment_type == 'subscription':
            payment['type_label'] = _msg_text("Obuna", "Подписка", "Subscription")
            tariff_id = ids[0] if ids else None
            tariff = tariffs_map.get(tariff_id)
            payment['item_label'] = tariff.get('name') if tariff else (f"Tarif #{tariff_id}" if tariff_id else '-')
        elif payment_type == 'issue':
            payment['type_label'] = _msg_text("Son", "Выпуск", "Issue")
            issue_id = ids[0] if ids else None
            issue = issues_map.get(issue_id)
            payment['item_label'] = issue.get('title') if issue else (f"Son #{issue_id}" if issue_id else '-')
        elif payment_type == 'article':
            payment['type_label'] = _msg_text("Maqola", "Статья", "Article")
            titles = []
            for article_id in ids:
                article = articles_map.get(article_id)
                if article:
                    title = _clean_text(article.get('title'))
                    if title:
                        titles.append(title)
            if titles:
                label = ', '.join(titles[:2])
                if len(titles) > 2:
                    label = f"{label} (+{len(titles) - 2})"
                payment['item_label'] = label
            else:
                payment['item_label'] = _msg_text("Maqola(lar)", "Статья(и)", "Article(s)")
        else:
            payment['type_label'] = '-'
            payment['item_label'] = '-'
    
    return render_template('finance/payments.html', 
                         payments_list=payments_list, 
                         page=page, 
                         total_payments=total_payments, 
                         total_pages=total_pages, 
                         pagination_query_string=pagination_query_string,
                         status_filter=status_filter,
                         users_map=users_map)

@bp.route('/fmadmin/finance/payments/edit', methods=['POST'])
@is_superadmin_required
def payment_edit():
    try:
        _ensure_payment_snapshot_columns()
        payment_id = _parse_int(request.form.get('payment_id'))
        status = request.form.get('status')
        amount = request.form.get('amount')
        comment = request.form.get('comment', '')

        amount_value = _parse_amount(amount)
        normalized_status = _clean_text(status).lower()
        if payment_id is None or not normalized_status or amount_value is None:
            return jsonify({'success': False, 'error': 'Не все обязательные поля заполнены'})
        if normalized_status not in {'pending', 'paid', 'rejected'}:
            return jsonify({'success': False, 'error': 'Недопустимый статус платежа'})

        now_ts = int(time.time())
        payment = None
        updated_payment = None
        payment_user = None
        status_changed = False

        with db._lock:
            cursor = db.conn.cursor()
            try:
                cursor.execute("SELECT * FROM payments WHERE id = %s FOR UPDATE", (payment_id,))
                payment_row = cursor.fetchone()
                if not payment_row:
                    db.conn.rollback()
                    return jsonify({'success': False, 'error': 'Платеж не найден'})
                payment_columns = [desc[0] for desc in cursor.description]
                payment = dict(zip(payment_columns, payment_row))

                previous_status = _clean_text(payment.get('status')).lower()
                status_changed = normalized_status != previous_status

                update_data = {
                    'status': normalized_status,
                    'amount': amount_value,
                }
                if normalized_status == 'paid' and not payment.get('payment_date'):
                    update_data['payment_date'] = now_ts
                if comment:
                    update_data['note'] = comment

                update_clauses = []
                update_args = []
                for column_name, column_value in update_data.items():
                    update_clauses.append(f"{column_name} = %s")
                    update_args.append(column_value)
                update_args.append(payment_id)

                cursor.execute(
                    f"UPDATE payments SET {', '.join(update_clauses)} WHERE id = %s RETURNING *",
                    tuple(update_args),
                )
                updated_row = cursor.fetchone()
                if not updated_row:
                    db.conn.rollback()
                    return jsonify({'success': False, 'error': 'Платеж не найден'})
                updated_payment_columns = [desc[0] for desc in cursor.description]
                updated_payment = dict(zip(updated_payment_columns, updated_row))

                payment_user_id = _parse_int(payment.get('user_id'))
                if payment_user_id is not None:
                    cursor.execute("SELECT * FROM users WHERE id = %s FOR UPDATE", (payment_user_id,))
                    payment_user_row = cursor.fetchone()
                    if payment_user_row:
                        payment_user_columns = [desc[0] for desc in cursor.description]
                        payment_user = dict(zip(payment_user_columns, payment_user_row))

                if (
                    payment_user
                    and status_changed
                    and normalized_status == 'paid'
                    and _clean_text(payment.get('payment_type')).lower() == 'subscription'
                ):
                    ids = payment.get('ids') or []
                    tariff_id = ids[0] if isinstance(ids, (list, tuple)) and ids else None
                    snapshot_duration_days = _parse_int(payment.get('snapshot_duration_days'))
                    resolved_tariff_id = _parse_int(payment_user.get('tariff_id'))
                    duration_days = snapshot_duration_days
                    tariff = {}

                    if tariff_id:
                        cursor.execute("SELECT * FROM tariffs WHERE id = %s", (tariff_id,))
                        tariff_row = cursor.fetchone()
                        if tariff_row:
                            tariff_columns = [desc[0] for desc in cursor.description]
                            tariff = dict(zip(tariff_columns, tariff_row))
                            resolved_tariff_id = _parse_int(tariff.get('id'))
                        if duration_days is None:
                            duration_days = _parse_int(tariff.get('duration_days') or tariff.get('user_limit'))

                    if duration_days is None:
                        db.conn.rollback()
                        return jsonify({
                            'success': False,
                            'error': "Невозможно активировать подписку: не найдена длительность тарифа."
                        })

                    base_ts = now_ts
                    current_end = _parse_int(payment_user.get('subscription_end_date'))
                    if current_end and current_end > now_ts:
                        base_ts = current_end
                    new_end = base_ts + (duration_days * 24 * 60 * 60)
                    cursor.execute(
                        "UPDATE payments SET snapshot_start_at = %s, snapshot_end_at = %s WHERE id = %s",
                        (base_ts, new_end, payment_id),
                    )
                    cursor.execute(
                        "UPDATE users SET tariff_id = %s, subscription_end_date = %s WHERE id = %s RETURNING *",
                        (resolved_tariff_id, new_end, payment_user.get('id')),
                    )
                    updated_user_row = cursor.fetchone()
                    if updated_user_row:
                        updated_user_columns = [desc[0] for desc in cursor.description]
                        payment_user = dict(zip(updated_user_columns, updated_user_row))

                db.conn.commit()
            except Exception:
                db.conn.rollback()
                raise
            finally:
                cursor.close()

        if payment_user and status_changed:
            if normalized_status == 'paid':
                email_subject = localized_texts("To'lovingiz tasdiqlandi", 'Ваш платеж подтверждён', 'Your payment has been approved')
                email_intro = localized_texts(
                    "Sizning to'lovingiz moliya bo'limi tomonidan tasdiqlandi.",
                    'Ваш платеж был подтверждён финансовым отделом.',
                    'Your payment was approved by the finance team.',
                )
            elif normalized_status == 'rejected':
                email_subject = localized_texts("To'lovingiz rad etildi", 'Ваш платеж отклонён', 'Your payment was rejected')
                email_intro = localized_texts(
                    "Sizning to'lovingiz moliya bo'limi tomonidan rad etildi.",
                    'Ваш платеж был отклонён финансовым отделом.',
                    'Your payment was rejected by the finance team.',
                )
            else:
                email_subject = localized_texts("To'lovingiz ko'rib chiqilmoqda", 'Ваш платеж рассматривается', 'Your payment is being reviewed')
                email_intro = localized_texts(
                    "Sizning to'lovingiz hozir ko'rib chiqish jarayonida.",
                    'Ваш платеж сейчас находится на рассмотрении.',
                    'Your payment is now under review.',
                )

            body_lines = []
            if comment:
                body_lines.append(localized_texts(
                    f'Izoh: {comment}',
                    f'Комментарий: {comment}',
                    f'Comment: {comment}',
                ))

            _send_user_email(
                payment_user,
                subject=email_subject,
                intro=email_intro,
                details=[],
                body_lines=body_lines,
                cta_url='/dashboard/payments',
                cta_label=localized_texts("To'lovlarni ochish", 'Открыть оплаты', 'Open payments'),
            )

        return jsonify({'success': True})
            
    except Exception:
        logger.exception('Payment update failed in payment_edit')
        return jsonify({'success': False, 'error': 'Internal server error'})

def _submission_has_private_upload(submission, storage_key):
    return (
        extract_private_upload_key((submission or {}).get('file_authors')) == storage_key
        or extract_private_upload_key((submission or {}).get('file_anonymized')) == storage_key
        or extract_private_upload_key((submission or {}).get('anti_plagiarism_file')) == storage_key
    )


def _current_user_can_access_private_upload(current_user, storage_key):
    if not storage_key:
        return False
    if user_has_role(current_user, 'superadmin'):
        return True

    can_access_admin_files = user_has_role(current_user, 'admin')
    can_access_editor_files = user_has_role(current_user, 'editor')
    current_user_id = _parse_int((current_user or {}).get('id'))

    if storage_key.startswith('documents/'):
        if not can_access_admin_files:
            return False
        rows = db.user_doc_uploads.all().exec()
        return any(extract_private_upload_key(row.get('file_path')) == storage_key for row in rows)

    if storage_key.startswith('payments/'):
        if not can_access_admin_files:
            return False
        rows = db.payments.all().exec()
        return any(
            extract_private_upload_key(row.get('proof')) == storage_key
            or extract_private_upload_key(row.get('confirmation_file')) == storage_key
            for row in rows
        )

    if storage_key.startswith('articles/'):
        editor_submission_ids = set()
        if can_access_editor_files and current_user_id is not None:
            assignment_rows = db.editor_assignments.all().equal(editor_id=current_user_id).exec()
            editor_submission_ids = {
                _parse_int(item.get('submission_id'))
                for item in assignment_rows
                if _parse_int(item.get('submission_id')) is not None
            }

        submissions = db.submissions.all().exec()
        for submission in submissions:
            if not _submission_has_private_upload(submission, storage_key):
                continue
            if can_access_admin_files and _can_access_submission(current_user, submission):
                return True
            submission_id = _parse_int(submission.get('id'))
            if submission_id is not None and submission_id in editor_submission_ids:
                return True
        return False

    return False


@bp.route('/fmadmin/files/<path:storage_key>')
@is_admin_or_editor
def serve_private_file(storage_key):
    current_user = get_current_user() or {}
    resolved_key = extract_private_upload_key(storage_key)
    if not resolved_key or not _current_user_can_access_private_upload(current_user, resolved_key):
        abort(404)

    file_path = private_upload_abspath(resolved_key)
    if not file_path or not os.path.exists(file_path):
        abort(404)

    return send_file(file_path, as_attachment=False, download_name=os.path.basename(file_path))

@bp.route('/static/<path:filename>')
def serve_static_any(filename):
    if filename.startswith('uploads/') and extract_private_upload_key(filename[len('uploads/'):]):
        abort(404)
    return send_from_directory(os.path.join(settings.SAVE_PATH, 'static'), filename)

@bp.route('/fmadmin/submissions')
@is_allowed
def submissions():
    current_user = get_current_user() or {}
    current_role = _role_of(current_user)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', '').strip()
    legacy_user_filter = request.args.get('user', '').strip()
    user_id_filter = request.args.get('user_id', '').strip() or legacy_user_filter
    submission_id_filter = _parse_int(request.args.get('submission_id', '').strip())
    title_filter = _clean_text(request.args.get('title'))
    track_filter = _clean_text(request.args.get('track'))
    assigned_admin_filter = _parse_int(request.args.get('assigned_admin', '').strip())
    editor_id_filter = _parse_int(request.args.get('editor_id', '').strip())
    author_filter = _clean_text(request.args.get('author'))
    workflow_filter = _clean_text(request.args.get('workflow_stage'))
    review_filter = _clean_text(request.args.get('review_status'))
    created_from = _clean_text(request.args.get('created_from'))
    created_to = _clean_text(request.args.get('created_to'))
    created_from_ts = _parse_date_to_timestamp(created_from) if created_from else None
    created_to_ts = _parse_date_to_timestamp(created_to, end_of_day=True) if created_to else None

    query = db.submissions.all().unequal(status='draft').order_by('id')

    # Получаем пользователей и авторов для отображения имен и фильтрации
    users = db.users.all().exec()
    users_map = {u['id']: u for u in users}

    authors = db.author_profile.all().exec()
    authors_map = {a['id']: a for a in authors}
    admin_options = _active_admins()
    current_user_id = _parse_int(current_user.get('id'))
    editor_options = get_editors(admin_id=current_user_id) if current_role == 'admin' else get_editors()

    submissions_rows = query.exec()
    title_filter_lower = title_filter.lower() if title_filter else ''
    author_filter_lower = author_filter.lower() if author_filter else ''
    normalized_track_filter = _normalize_admin_track(track_filter) if track_filter else ''
    normalized_workflow_filter = workflow_filter.lower() if workflow_filter else ''
    normalized_review_filter = review_filter.lower() if review_filter else ''
    user_id_filter_value = _parse_int(user_id_filter)
    submission_ids = [submission.get('id') for submission in submissions_rows if submission.get('id') is not None]
    assignment_rows = []
    if submission_ids:
        try:
            assignment_rows = db.editor_assignments.all().any(submission_id=submission_ids).exec()
        except Exception:
            assignment_rows = []
    assignments_by_submission = {}
    for assignment in assignment_rows:
        submission_id = _parse_int(assignment.get('submission_id'))
        editor_id = _parse_int(assignment.get('editor_id'))
        if submission_id is None or editor_id is None:
            continue
        assignments_by_submission.setdefault(submission_id, [])
        if editor_id not in assignments_by_submission[submission_id]:
            assignments_by_submission[submission_id].append(editor_id)

    filtered_submissions = []
    for submission in submissions_rows:
        if current_role != 'superadmin' and not _can_access_submission(current_user, submission):
            continue
        if submission_id_filter is not None and submission.get('id') != submission_id_filter:
            continue
        if status_filter and submission.get('status') != status_filter:
            continue
        if user_id_filter_value is not None and submission.get('user_id') != user_id_filter_value:
            continue
        if title_filter_lower and title_filter_lower not in _clean_text(submission.get('title')).lower():
            continue
        if normalized_track_filter:
            submission_track = _normalize_admin_track(submission.get('submission_track'))
            if submission_track != normalized_track_filter:
                continue
        if assigned_admin_filter is not None:
            if _parse_int(submission.get('assigned_admin_id')) != assigned_admin_filter:
                continue
        if editor_id_filter is not None:
            assigned_editor_ids = assignments_by_submission.get(submission.get('id'), [])
            if editor_id_filter not in assigned_editor_ids:
                continue
        if author_filter_lower:
            author = authors_map.get(submission.get('main_author_id')) or {}
            author_name = _clean_text(author.get('name')).lower()
            if author_filter_lower not in author_name:
                continue
        if normalized_workflow_filter:
            stage_key = _infer_workflow_stage(submission)
            submission['workflow_stage'] = stage_key
            if stage_key != normalized_workflow_filter:
                continue
        if normalized_review_filter:
            review_status = _clean_text(submission.get('editor_review_status')).lower()
            if review_status != normalized_review_filter:
                continue
        if created_from_ts is not None or created_to_ts is not None:
            created_ts = _parse_int(submission.get('created_date'))
            if created_ts is None:
                continue
            if created_from_ts is not None and created_ts < created_from_ts:
                continue
            if created_to_ts is not None and created_ts > created_to_ts:
                continue
        filtered_submissions.append(submission)

    total_submissions = len(filtered_submissions)
    start_idx = max(page - 1, 0) * per_page
    end_idx = start_idx + per_page
    submissions_list = filtered_submissions[start_idx:end_idx]

    total_pages = (total_submissions + per_page - 1) // per_page

    # Формируем query_string для пагинации
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    admin_lang = _admin_language()
    classification_lookup = _classification_catalog_lookup(admin_lang)

    for submission in submissions_list:
        stage_key = submission.get('workflow_stage') or _infer_workflow_stage(submission)
        submission['workflow_stage'] = stage_key
        submission['workflow_stage_label'] = WORKFLOW_STAGE_LABELS.get(stage_key, stage_key)
        submission['submission_track_label'] = _submission_track_label(submission.get('submission_track'))
        assigned_admin = users_map.get(_parse_int(submission.get('assigned_admin_id')))
        submission['assigned_admin_name'] = assigned_admin.get('name') if assigned_admin else t("admin_label_not_specified")
        assigned_editor_ids = assignments_by_submission.get(submission.get('id'), [])
        assigned_editor_names = []
        seen_editor_ids = set()
        for editor_id in assigned_editor_ids:
            if editor_id in seen_editor_ids:
                continue
            seen_editor_ids.add(editor_id)
            editor_user = users_map.get(editor_id) or {}
            label = editor_user.get('name') or editor_user.get('email')
            if label:
                assigned_editor_names.append(label)
        submission['assigned_editors_label'] = (
            ', '.join(assigned_editor_names)
            if assigned_editor_names
            else t("admin_label_not_specified")
        )
        classification_items = _serialize_submission_classifications(
            submission.get('classifications'),
            classification_lookup,
            admin_lang
        )
        submission['classification_items'] = classification_items
        submission['classification_total'] = len(classification_items)
        submission['classification_preview'] = ', '.join([item.get('label', '') for item in classification_items[:3]])
    
    return render_template('submissions/list.html', 
                         submissions_list=submissions_list, 
                         page=page, 
                         total_submissions=total_submissions, 
                         total_pages=total_pages, 
                         pagination_query_string=pagination_query_string,
                         submission_id_filter=submission_id_filter,
                         status_filter=status_filter,
                         user_id_filter=user_id_filter,
                         title_filter=title_filter,
                         track_filter=track_filter,
                         assigned_admin_filter=assigned_admin_filter,
                         editor_id_filter=editor_id_filter,
                         author_filter=author_filter,
                         workflow_filter=workflow_filter,
                         review_filter=review_filter,
                         created_from=created_from,
                         created_to=created_to,
                         users_map=users_map,
                         authors_map=authors_map,
                         admin_options=admin_options,
                         admin_track_choices=ADMIN_TRACK_CHOICES,
                         editor_options=editor_options,
                         current_user=current_user,
                         workflow_stage_choices=WORKFLOW_STAGE_CHOICES,
                         workflow_stage_labels=WORKFLOW_STAGE_LABELS)

@bp.route('/fmadmin/submissions/<int:submission_id>')
@is_allowed
def submission_detail(submission_id):
    current_user = get_current_user() or {}
    submission = db.submissions.all().equal(id=submission_id).exec()
    if not submission:
        return 'Подача не найдена', 404
    submission = submission[0]
    if not _can_access_submission(current_user, submission):
        flash(t('admin_error_no_access'), 'danger')
        return redirect(url_for('submissions'))
    admin_lang = _admin_language()
    classification_lookup = _classification_catalog_lookup(admin_lang)
    stage_key = _infer_workflow_stage(submission)
    submission['workflow_stage'] = stage_key
    submission['workflow_stage_label'] = WORKFLOW_STAGE_LABELS.get(stage_key, stage_key)
    submission['submission_track_label'] = _submission_track_label(submission.get('submission_track'))
    classification_items = _serialize_submission_classifications(
        submission.get('classifications'),
        classification_lookup,
        admin_lang
    )
    submission['classification_items'] = classification_items
    submission['classification_groups'] = _group_submission_classifications(classification_items)
    
    # Получаем данные пользователя
    user = None
    if submission.get('user_id'):
        user_data = db.users.all().equal(id=submission['user_id']).exec()
        if user_data:
            user = user_data[0]

    assigned_admin = None
    assigned_admin_id = _parse_int(submission.get('assigned_admin_id'))
    if assigned_admin_id is not None:
        assigned_admin_data = _load_user_from_db(assigned_admin_id)
        if assigned_admin_data and user_has_role(assigned_admin_data, 'admin'):
            assigned_admin = assigned_admin_data

    try:
        submission_assignments = db.editor_assignments.all().equal(submission_id=submission_id).order_by('assigned_at').exec()
    except Exception:
        submission_assignments = []
    submission_assignments = [_decorate_assignment(item) for item in submission_assignments]
    submission_assignments = sorted(submission_assignments, key=lambda item: _parse_int(item.get('assigned_at')) or 0, reverse=True)
    for assignment in submission_assignments:
        assignment['can_admin_decide'] = assignment.get('status') in EDITOR_ASSIGNMENT_REVIEWED_STATUS_VALUES

    editor_ids = [assignment.get('editor_id') for assignment in submission_assignments if assignment.get('editor_id')]
    assignment_editors_map = {}
    if editor_ids:
        try:
            assignment_editors = db.users.all().any(id=editor_ids).exec()
        except Exception:
            assignment_editors = db.users.all().exec()
        assignment_editors_map = {item.get('id'): item for item in assignment_editors if item.get('id')}

    # Получаем данные авторов
    main_author = None
    if submission.get('main_author_id'):
        author_data = db.author_profile.all().equal(id=submission['main_author_id']).exec()
        if author_data:
            main_author = author_data[0]
    
    sub_authors = []
    if submission.get('sub_author_ids'):
        sub_authors = db.author_profile.all().any(id=submission['sub_author_ids']).exec()
    
    return render_template('submissions/detail.html', 
                         submission=submission, 
                         user=user, 
                         assigned_admin=assigned_admin,
                         submission_assignments=submission_assignments,
                         assignment_editors_map=assignment_editors_map,
                         main_author=main_author, 
                         sub_authors=sub_authors,
                         workflow_stage_choices=WORKFLOW_STAGE_CHOICES,
                         workflow_stage_labels=WORKFLOW_STAGE_LABELS)

@bp.route('/fmadmin/submissions/documents')
@is_allowed
def submission_documents():
    _ensure_user_doc_upload_columns()
    page = request.args.get('page', 1, type=int)
    per_page = 25
    status_filter = request.args.get('status', '').strip()
    search_title = request.args.get('title', '').strip()
    user_filter = request.args.get('user', '').strip()
    
    # Получаем документы из user_doc_uploads
    query = db.user_doc_uploads.all()
    
    # Фильтр по статусу верификации
    if status_filter and status_filter in ['verified', 'pending', 'rejected']:
        query = query.equal(verification_status=status_filter)
    
    # Поиск по названию работы
    if search_title:
        query = query.like(work_title=search_title)
    
    # Фильтр по пользователю
    if user_filter:
        try:
            query = query.equal(user_id=int(user_filter))
        except:
            pass
    
    total_docs = query.copy().count().exec()
    docs_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_docs + per_page - 1) // per_page
    
    # Формируем query_string для пагинации
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    
    # Получаем пользователей для отображения имен
    users = db.users.all().exec()
    users_map = {u['id']: u for u in users}
    
    return render_template('submissions/documents.html', 
                         docs_list=docs_list, 
                         page=page, 
                         total_docs=total_docs, 
                         total_pages=total_pages, 
                         pagination_query_string=pagination_query_string,
                         status_filter=status_filter,
                         search_title=search_title,
                         user_filter=user_filter,
                         users_map=users_map)

@bp.route('/fmadmin/submissions/edit', methods=['POST'])
@is_allowed
def submission_edit():
    try:
        current_user = get_current_user() or {}
        actor_id = _parse_int(current_user.get('id'))
        submission_id = request.form.get('submission_id')
        status = (request.form.get('status') or '').strip().lower()
        workflow_stage = _normalize_workflow_stage(request.form.get('workflow_stage'))
        notes = request.form.get('notes', '')

        submission_id_int = _parse_int(submission_id)
        if submission_id_int is None or not status:
            return jsonify({'success': False, 'error': 'Не все обязательные поля заполнены'})

        if status == 'rejected' and not _clean_text(notes):
            return jsonify({
                'success': False,
                'error': _msg_text(
                    "Rad etish sababi majburiy. Iltimos, izoh yozing.",
                    "Причина отклонения обязательна. Пожалуйста, укажите комментарий.",
                    "Rejection reason is required. Please add a note."
                )
            })

        submission_rows = db.submissions.all().equal(id=submission_id_int).exec()
        if not submission_rows:
            return jsonify({'success': False, 'error': 'Подача не найдена'})
        submission = submission_rows[0]
        old_status = _clean_text(submission.get('status')).lower()
        old_stage = _normalize_workflow_stage(submission.get('workflow_stage')) or _infer_workflow_stage(submission)
        old_notes = _clean_text(submission.get('notes'))
        anti_plagiarism_file = _clean_text(submission.get('anti_plagiarism_file'))
        if not _can_access_submission(current_user, submission):
            return jsonify({'success': False, 'error': t('admin_error_no_access')})

        if status == 'published':
            workflow_stage = 'published'
        elif status == 'rejected':
            workflow_stage = 'rejected'
        elif workflow_stage == 'published':
            status = 'published'
        elif workflow_stage == 'rejected':
            status = 'rejected'
        elif workflow_stage == 'anti_plagiarism' and status in {'submitted', 'pending'}:
            status = 'in_process'
        elif status == 'submitted' and not workflow_stage:
            workflow_stage = 'waiting'

        target_stage = workflow_stage or old_stage
        if target_stage in {'in_review', 'recommended', 'payment', 'published'} and not anti_plagiarism_file:
            return jsonify({
                'success': False,
                'error': _msg_text(
                    "Avval muallif antiplagiat hujjatini yuklashi kerak",
                    "Сначала автор должен загрузить документ антиплагиата",
                    "Author must upload anti-plagiarism document first"
                )
            })

        now_ts = int(datetime.datetime.now().timestamp())

        # Обновляем подачу
        update_data = {
            'status': status,
            'notes': notes,
            'updated_at': now_ts
        }
        if workflow_stage:
            update_data['workflow_stage'] = workflow_stage

        result = db.submissions.all().equal(id=submission_id_int).update(**update_data).exec()
        
        if result:
            new_status = _clean_text(status).lower()
            new_stage = workflow_stage or old_stage
            new_notes = _clean_text(notes)
            entered_anti_plagiarism_stage = old_stage != 'anti_plagiarism' and new_stage == 'anti_plagiarism'
            submission_title = _submission_title(submission)
            detail_url = url_for('submission_detail', submission_id=submission_id_int)
            author_url = '/dashboard/articles'
            author_id = _parse_int(submission.get('user_id'))
            assigned_admin_id = _parse_int(submission.get('assigned_admin_id'))
            author_user = None
            if author_id is not None:
                author_rows = db.users.all().equal(id=author_id).exec()
                author_user = author_rows[0] if author_rows else None

            status_or_stage_changed = old_status != new_status or old_stage != new_stage
            notes_changed = old_notes != new_notes
            if status_or_stage_changed or notes_changed:
                changed_at_label = datetime.datetime.fromtimestamp(now_ts).strftime('%d.%m.%Y %H:%M')
                if status_or_stage_changed:
                    if new_status == 'published' or new_stage == 'published':
                        notification_title = localized_texts(
                            "Tabriklaymiz! Maqolangiz nashr qilindi",
                            "Поздравляем! Ваша статья опубликована",
                            "Congratulations! Your article is published"
                        )
                        notification_message = localized_texts(
                            f'"{submission_title}" maqolangiz muvaffaqiyatli nashr qilindi.',
                            f'Ваша статья "{submission_title}" успешно опубликована.',
                            f'Your article "{submission_title}" was published successfully.',
                        )
                        notification_event = 'submission_published'
                    else:
                        notification_title = localized_texts(
                            "Maqolangiz holati yangilandi",
                            "Статус вашей статьи обновлён",
                            "Your article status was updated"
                        )
                        notification_message = _status_stage_change_message(
                            submission_title,
                            new_status,
                            new_stage,
                        )
                        notification_event = 'submission_status_updated'
                else:
                    notification_title = localized_texts(
                        "Maqola izohi yangilandi",
                        "Комментарий к статье обновлён",
                        "Submission note updated"
                    )
                    notification_message = localized_texts(
                        f'"{submission_title}" uchun admin izohi yangilandi. Sana: {changed_at_label}',
                        f'Комментарий администратора для "{submission_title}" обновлён. Дата: {changed_at_label}',
                        f'Admin note for "{submission_title}" was updated. Date: {changed_at_label}'
                    )
                    notification_event = 'submission_notes_updated'

                if author_id is not None:
                    _create_role_notification(
                        target_user_id=author_id,
                        target_role='user',
                        title=notification_title,
                        message=notification_message,
                        action_url=author_url,
                        level='info',
                        event_type=notification_event,
                        related_submission_id=submission_id_int,
                        actor_user_id=actor_id
                    )
                    email_body_lines = []
                    if entered_anti_plagiarism_stage:
                        email_body_lines.append(
                            _msg_text(
                                "Iltimos, dashboard orqali antiplagiat hujjatini yuklang.",
                                "Пожалуйста, загрузите антиплагиат-документ через личный кабинет.",
                                "Please upload the anti-plagiarism document from your dashboard."
                            )
                        )
                    elif new_notes:
                        email_body_lines.append(
                            _msg_text(
                                f"Admin izohi: {new_notes}",
                                f"Комментарий администратора: {new_notes}",
                                f"Admin note: {new_notes}"
                            )
                        )

                    _send_user_email(
                        author_user,
                        subject=notification_title,
                        intro=notification_message,
                        body_lines=email_body_lines,
                        cta_url=author_url,
                        cta_label=localized_texts("Dashboardga o'tish", 'Перейти в кабинет', 'Go to dashboard'),
                    )

                if assigned_admin_id is not None and assigned_admin_id != actor_id:
                    _create_role_notification(
                        target_user_id=assigned_admin_id,
                        target_role='admin',
                        title=notification_title,
                        message=notification_message,
                        action_url=detail_url,
                        level='info',
                        event_type=notification_event,
                        related_submission_id=submission_id_int,
                        actor_user_id=actor_id
                    )

                _notify_role_users(
                    'superadmin',
                    title=notification_title,
                    message=notification_message,
                    action_url=detail_url,
                    level='info',
                    event_type=notification_event,
                    related_submission_id=submission_id_int,
                    actor_user_id=actor_id,
                    exclude_user_ids=[actor_id]
                )

            if entered_anti_plagiarism_stage:
                anti_plagiarism_text = localized_texts(
                    f"\"{submission_title}\" antiplagiat bosqichiga o'tdi. Antiplagiat hujjatini yuklang.",
                    f"\"{submission_title}\" переведена на этап антиплагиата. Загрузите антиплагиат-документ.",
                    f"\"{submission_title}\" moved to anti-plagiarism stage. Upload anti-plagiarism document."
                )
                if author_id is not None:
                    _create_role_notification(
                        target_user_id=author_id,
                        target_role='user',
                        title=localized_texts(
                            "Antiplagiat hujjati talab qilindi",
                            "Требуется антиплагиат-документ",
                            "Anti-plagiarism document required"
                        ),
                        message=anti_plagiarism_text,
                        action_url=author_url,
                        level='warning',
                        event_type='submission_antiplagiarism_requested',
                        related_submission_id=submission_id_int,
                        actor_user_id=actor_id
                    )

                if assigned_admin_id is not None and assigned_admin_id != actor_id:
                    _create_role_notification(
                        target_user_id=assigned_admin_id,
                        target_role='admin',
                        title=localized_texts(
                            "Antiplagiat bosqichi boshlandi",
                            "Этап антиплагиата начат",
                            "Anti-plagiarism stage started"
                        ),
                        message=anti_plagiarism_text,
                        action_url=detail_url,
                        level='info',
                        event_type='submission_antiplagiarism_requested',
                        related_submission_id=submission_id_int,
                        actor_user_id=actor_id
                    )

                _notify_role_users(
                    'superadmin',
                    title=localized_texts(
                        "Antiplagiat bosqichi boshlandi",
                        "Этап антиплагиата начат",
                        "Anti-plagiarism stage started"
                    ),
                    message=anti_plagiarism_text,
                    action_url=detail_url,
                    level='info',
                    event_type='submission_antiplagiarism_requested',
                    related_submission_id=submission_id_int,
                    actor_user_id=actor_id,
                    exclude_user_ids=[actor_id]
                )
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Подача не найдена'})
            
    except Exception:
        logger.exception('Submission edit failed in submission_edit')
        return jsonify({'success': False, 'error': 'Internal server error'})


@bp.route('/fmadmin/submissions/bulk', methods=['POST'])
@is_allowed
def submissions_bulk_action():
    action = _clean_text(request.form.get('action')).lower()
    current_user = get_current_user() or {}

    allowed_actions = {
        'set_submitted': {'status': 'submitted', 'workflow_stage': 'waiting'},
        'set_in_process': {'status': 'in_process', 'workflow_stage': 'technical_check'},
        'set_published': {'status': 'published', 'workflow_stage': 'published'},
        'set_rejected': {'status': 'rejected', 'workflow_stage': 'rejected'},
    }
    if action not in allowed_actions:
        new_alert(_msg_text("Noma'lum amal", 'Неизвестное действие', 'Unknown action'), 'danger')
        return redirect(url_for('submissions'))

    selected_ids = []
    for raw_id in request.form.getlist('selected_submission_ids'):
        parsed_id = _parse_int(raw_id)
        if parsed_id is not None:
            selected_ids.append(parsed_id)
    selected_ids = list(dict.fromkeys(selected_ids))

    if not selected_ids:
        new_alert(_msg_text("Kamida bitta maqola tanlang", 'Выберите хотя бы одну статью', 'Select at least one submission'), 'danger')
        return redirect(url_for('submissions'))

    submissions_map = {}
    try:
        submission_rows = db.submissions.all().any(id=selected_ids).exec()
    except Exception:
        submission_rows = []
    for item in submission_rows:
        item_id = _parse_int(item.get('id'))
        if item_id is not None:
            submissions_map[item_id] = item

    changed = 0
    update_payload = dict(allowed_actions[action])
    for submission_id in selected_ids:
        submission = submissions_map.get(submission_id)
        if not submission:
            continue
        if not _can_access_submission(current_user, submission):
            continue
        try:
            db.submissions.all().equal(id=submission_id).update(**update_payload).exec()
            changed += 1
        except Exception:
            logger.exception('Bulk submission update failed for submission_id=%s', submission_id)

    if changed:
        new_alert(_msg_text(
            f"Yangilangan maqolalar soni: {changed}",
            f"Обновлено статей: {changed}",
            f"Updated submissions: {changed}"
        ), 'success')
    else:
        new_alert(_msg_text(
            "Tanlangan maqolalar yangilanmadi",
            'Выбранные статьи не были обновлены',
            'Selected submissions were not updated'
        ), 'warning')

    return redirect(url_for('submissions'))

@bp.route('/fmadmin/submissions/documents/edit', methods=['POST'])
@is_allowed
def document_edit():
    try:
        _ensure_user_doc_upload_columns()
        doc_id = request.form.get('doc_id')
        verification_status = request.form.get('verification_status')
        
        if not doc_id or not verification_status:
            return jsonify({'success': False, 'error': 'Не все обязательные поля заполнены'})
        
        # Обновляем документ
        update_data = {
            'verification_status': verification_status,
            'updated_at': int(datetime.datetime.now().timestamp())
        }
        
        result = db.user_doc_uploads.all().equal(id=int(doc_id)).update(**update_data).exec()
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Документ не найден'})
            
    except Exception:
        logger.exception('Document edit failed in document_edit')
        return jsonify({'success': False, 'error': 'Internal server error'})

# ==================== РЕДАКТОРЫ ====================

@bp.route('/fmadmin/editors')
@is_superadmin_required
def editors():
    """Список всех редакторов"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_name = request.args.get('name', '').strip()
    search_specialization = request.args.get('specialization', '').strip()

    editors_pool = _users_with_role('editor', include_hidden=False, include_blocked=False)
    if search_name:
        search_name_lower = search_name.lower()
        editors_pool = [
            editor for editor in editors_pool
            if search_name_lower in _clean_text(editor.get('name')).lower()
            or search_name_lower in _clean_text(editor.get('second_name')).lower()
            or search_name_lower in _clean_text(editor.get('email')).lower()
        ]
    if search_specialization:
        search_specialization_lower = search_specialization.lower()
        editors_pool = [
            editor for editor in editors_pool
            if search_specialization_lower in _clean_text(editor.get('editor_specialization')).lower()
        ]

    total_editors = len(editors_pool)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    editors_list = editors_pool[start_idx:end_idx]
    total_pages = (total_editors + per_page - 1) // per_page
    admin_map = {admin.get('id'): admin for admin in _active_admins() if admin.get('id')}

    # Получаем статистику по назначениям для каждого редактора
    try:
        assignments = db.editor_assignments.all().exec()
    except:
        assignments = []

    editor_stats = {}
    for editor in editors_list:
        assigned_admin = admin_map.get(_parse_int(editor.get('editor_admin_id')))
        editor['assigned_admin_name'] = assigned_admin.get('name') if assigned_admin else None
        editor_assignments = [_decorate_assignment(a) for a in assignments if a.get('editor_id') == editor.get('id')]
        editor_stats[editor.get('id')] = _assignment_stats(editor_assignments)

    return render_template('editors/editors.html',
                         editors=editors_list,
                         page=page,
                         total_editors=total_editors,
                         total_pages=total_pages,
                         search_name=search_name,
                         search_specialization=search_specialization,
                         editor_stats=editor_stats)

@bp.route('/fmadmin/editors/<int:editor_id>', methods=['GET', 'POST'])
@is_superadmin_required
def editor_edit(editor_id):
    """Редактирование редактора"""
    active_admins = _active_admins()
    if request.method == 'POST':
        if editor_id == 0:
            # Создание нового редактора
            name = request.form.get('name')
            second_name = request.form.get('second_name')
            father_name = request.form.get('father_name')
            email = request.form.get('email')
            editor_specialization = request.form.get('editor_specialization')
            editor_admin_id = _parse_int(request.form.get('editor_admin_id'))
            if editor_admin_id is not None:
                admin_target = _load_user_from_db(editor_admin_id)
                if not admin_target or not user_has_role(admin_target, 'admin') or admin_target.get('is_hidden') or admin_target.get('is_blocked'):
                    new_alert(_msg_text("Tahrirchi uchun biriktirilgan admin topilmadi", "Для редактора не найден назначенный администратор", "Assigned admin for editor not found"), 'danger')
                    return redirect(url_for('editor_edit', editor_id=0))
            from werkzeug.security import generate_password_hash
            password = request.form.get('password')
            hashed_password = generate_password_hash(password) if password else None

            editor_id_new = db.users.add(
                name=name,
                second_name=second_name,
                father_name=father_name,
                email=email,
                rolename='editor',
                roles=build_user_roles('editor', include_author_role=False),
                editor_specialization=editor_specialization,
                editor_admin_id=editor_admin_id,
                password=hashed_password,
                created_at=int(datetime.datetime.now().timestamp()),
                register_time=int(datetime.datetime.now().timestamp())
            ).exec()
            editor_id_new = _extract_inserted_id(editor_id_new)
            new_alert(_msg_text('Tahrirchi muvaffaqiyatli yaratildi', 'Редактор успешно создан', 'Editor created successfully'), 'success')
            return redirect(url_for('editor_edit', editor_id=editor_id_new or 0))
        else:
            # Обновление существующего редактора
            data = request.json if request.is_json else request.form
            existing_editor = _load_user_from_db(editor_id) or {}
            editor_admin_id = _parse_int(data.get('editor_admin_id'))
            if editor_admin_id is not None:
                admin_target = _load_user_from_db(editor_admin_id)
                if not admin_target or not user_has_role(admin_target, 'admin') or admin_target.get('is_hidden') or admin_target.get('is_blocked'):
                    new_alert(_msg_text("Tahrirchi uchun biriktirilgan admin topilmadi", "Для редактора не найден назначенный администратор", "Assigned admin for editor not found"), 'danger')
                    return redirect(url_for('editor_edit', editor_id=editor_id))
            db.users.all().equal(id=editor_id).update(
                name=data.get('name'),
                second_name=data.get('second_name'),
                father_name=data.get('father_name'),
                email=data.get('email'),
                roles=build_user_roles(
                    existing_editor.get('rolename') or 'editor',
                    include_author_role=user_has_role(existing_editor, AUTHOR_ROLE),
                    extra_roles=parse_role_names(existing_editor.get('roles')) + ['editor'],
                ),
                editor_specialization=data.get('editor_specialization'),
                editor_admin_id=editor_admin_id
            ).exec()
            new_alert(_msg_text('Tahrirchi muvaffaqiyatli saqlandi', 'Редактор успешно сохранён', 'Editor saved successfully'), 'success')
            return redirect(url_for('editor_edit', editor_id=editor_id))

    if editor_id == 0:
        # Новый редактор
        editor = {
            'id': 0,
            'name': '',
            'second_name': '',
            'father_name': '',
            'email': '',
            'editor_specialization': '',
            'editor_admin_id': None,
            'rolename': 'editor'
        }
        password = uuid.uuid4().hex
        return render_template('editors/edit.html', editor=editor, password=password, active_admins=active_admins)
    else:
        editor = _load_user_from_db(editor_id)
        if not editor or not user_has_role(editor, 'editor'):
            return 'Редактор не найден', 404

        # Получаем назначения редактора
        try:
            editor_assignments = db.editor_assignments.all().equal(editor_id=editor_id).exec()
        except:
            editor_assignments = []

        # Получаем статистику
        editor_assignments = [_decorate_assignment(item) for item in editor_assignments]
        editor_stats = _assignment_stats(editor_assignments)

        # Получаем информацию о статьях
        submission_ids = [a.get('submission_id') for a in editor_assignments if a.get('submission_id')]
        submissions = []
        if submission_ids:
            try:
                submissions = db.submissions.all().exec()
            except:
                submissions = []

        submissions_map = {s.get('id'): s for s in submissions if s.get('id')}

        return render_template('editors/edit.html',
                             editor=editor,
                             editor_assignments=editor_assignments,
                             editor_stats=editor_stats,
                             submissions_map=submissions_map,
                             active_admins=active_admins)


@bp.route('/fmadmin/editors/<int:editor_id>/delete', methods=['POST'])
@is_superadmin_required
def editor_delete(editor_id):
    current_user = session.get('fmadmin_user') or {}
    current_user_id = _parse_int(current_user.get('id'))
    redirect_url = _safe_internal_redirect(request.form.get('redirect_url') or request.referrer, 'editors')

    editor_rows = _load_user_from_db(editor_id)
    if not editor_rows or not user_has_role(editor_rows, 'editor'):
        new_alert(_msg_text("Tahrirchi topilmadi", "Редактор не найден", "Editor not found"), 'danger')
        return redirect(redirect_url)

    if current_user_id is not None and editor_id == current_user_id:
        new_alert(_msg_text("O'zingizni o'chirib bo'lmaydi", "Нельзя удалить самого себя", "You cannot delete yourself"), 'danger')
        return redirect(redirect_url)

    now_ts = int(datetime.datetime.now().timestamp())
    db.users.all().equal(id=editor_id).update(
        is_hidden=True,
        is_blocked=True,
        deleted_at=now_ts
    ).exec()
    new_alert(_msg_text("Tahrirchi o'chirildi", "Редактор удалён", "Editor deleted"), 'success')
    return redirect(redirect_url)


@bp.route('/fmadmin/editorial-members')
@is_superadmin_required
def editorial_members():
    ui_lang = _ui_language()
    editorial_ui = _editorial_admin_ui_texts(ui_lang)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_name = _clean_text(request.args.get('name'))
    raw_type = _clean_text(request.args.get('member_type'))
    search_member_type = _normalize_editorial_member_type(raw_type) if raw_type else ''
    raw_status = _clean_text(request.args.get('status')).lower()
    search_status = raw_status if raw_status in {'active', 'inactive'} else ''

    try:
        all_members = db.editorial_members.all().exec()
    except Exception:
        all_members = []

    filtered_members = []
    for member in all_members:
        full_name = _clean_text(member.get('full_name'))
        full_name_uz = _clean_text(member.get('full_name_uz'))
        full_name_ru = _clean_text(member.get('full_name_ru'))
        full_name_joined = ' '.join([name for name in [full_name, full_name_uz, full_name_ru] if name]).strip()
        normalized_type = _normalize_editorial_member_type(member.get('member_type'))
        is_active = True if member.get('is_active') is None else bool(member.get('is_active'))

        if search_name and search_name.lower() not in full_name_joined.lower():
            continue
        if search_member_type and normalized_type != search_member_type:
            continue
        if search_status == 'active' and not is_active:
            continue
        if search_status == 'inactive' and is_active:
            continue

        member['member_type'] = normalized_type
        member['member_type_label'] = _editorial_member_type_label(normalized_type, ui_lang)
        member['is_active'] = is_active
        member['full_name_display'] = _localized_editorial_field(member, 'full_name', ui_lang)
        member['position_display'] = _localized_editorial_field(member, 'position', ui_lang)
        member['organization_display'] = _localized_editorial_field(member, 'organization', ui_lang)
        member['sort_order'] = _parse_int(member.get('sort_order')) or 0
        filtered_members.append(member)

    filtered_members = sorted(
        filtered_members,
        key=lambda item: (
            _parse_int(item.get('sort_order')) or 0,
            _clean_text(item.get('full_name_display') or item.get('full_name')).lower(),
            -(_parse_int(item.get('id')) or 0)
        )
    )

    total_members = len(filtered_members)
    total_pages = (total_members + per_page - 1) // per_page if total_members else 1
    safe_page = max(1, min(page, total_pages))
    start = (safe_page - 1) * per_page
    members_page = filtered_members[start:start + per_page]

    return render_template(
        'website/editorial/members.html',
        members=members_page,
        page=safe_page,
        total_members=total_members,
        total_pages=total_pages,
        search_name=search_name,
        search_member_type=search_member_type,
        search_status=search_status,
        member_type_options=_editorial_member_type_options(ui_lang),
        editorial_ui=editorial_ui
    )


@bp.route('/fmadmin/editorial-members/<int:member_id>', methods=['GET', 'POST'])
@is_superadmin_required
def editorial_member_edit(member_id):
    ui_lang = _ui_language()
    editorial_ui = _editorial_admin_ui_texts(ui_lang)
    current_user = session.get('fmadmin_user') or {}
    current_user_id = _parse_int(current_user.get('id'))

    if request.method == 'POST':
        full_name_en = _clean_text(request.form.get('full_name'))
        full_name_uz = _clean_text(request.form.get('full_name_uz'))
        full_name_ru = _clean_text(request.form.get('full_name_ru'))
        full_name = full_name_en or full_name_uz or full_name_ru
        if not full_name:
            new_alert(
                _msg_text(
                    "Kamida bitta tilda F.I.Sh. to'ldiring",
                    "Заполните ФИО хотя бы на одном языке",
                    "Fill full name in at least one language"
                ),
                'danger'
            )
            return redirect(url_for('editorial_member_edit', member_id=member_id))

        position_en = _clean_text(request.form.get('position'))
        position_uz = _clean_text(request.form.get('position_uz'))
        position_ru = _clean_text(request.form.get('position_ru'))
        organization_en = _clean_text(request.form.get('organization'))
        organization_uz = _clean_text(request.form.get('organization_uz'))
        organization_ru = _clean_text(request.form.get('organization_ru'))
        biography_en = _clean_text(request.form.get('biography'))
        biography_uz = _clean_text(request.form.get('biography_uz'))
        biography_ru = _clean_text(request.form.get('biography_ru'))

        payload = {
            'full_name': full_name,
            'full_name_uz': full_name_uz,
            'full_name_ru': full_name_ru,
            'position': position_en or position_uz or position_ru,
            'position_uz': position_uz,
            'position_ru': position_ru,
            'organization': organization_en or organization_uz or organization_ru,
            'organization_uz': organization_uz,
            'organization_ru': organization_ru,
            'biography': biography_en or biography_uz or biography_ru,
            'biography_uz': biography_uz,
            'biography_ru': biography_ru,
            'member_type': _normalize_editorial_member_type(request.form.get('member_type')),
            'email': _clean_text(request.form.get('email')),
            'orcid': _clean_text(request.form.get('orcid')),
            'sort_order': _parse_int(request.form.get('sort_order')) or 0,
            'is_active': request.form.get('is_active') in {'1', 'on', 'true', 'yes'}
        }

        image_value = _clean_text(request.form.get('current_image'))
        if request.form.get('remove_image') in {'1', 'on', 'true', 'yes'}:
            image_value = ''

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            try:
                image_value = save_file('editorial_members', image_file, ['jpg', 'jpeg', 'png', 'webp'])
            except Exception as e:
                new_alert(
                    _msg_text(
                        f"Rasm yuklashda xatolik: {e}",
                        f"Ошибка загрузки изображения: {e}",
                        f"Image upload error: {e}"
                    ),
                    'danger'
                )
                return redirect(url_for('editorial_member_edit', member_id=member_id))

        payload['image'] = image_value or None
        now_ts = int(datetime.datetime.now().timestamp())

        if member_id == 0:
            payload['created_at'] = now_ts
            payload['updated_at'] = now_ts
            payload['created_by'] = current_user_id
            payload['updated_by'] = current_user_id
            created = db.editorial_members.add(**payload).exec()
            created_id = _extract_inserted_id(created)
            new_alert(
                _msg_text(
                    "Tahrir hay'ati a'zosi qo'shildi",
                    "Участник редакционной коллегии добавлен",
                    "Editorial member added"
                ),
                'success'
            )
            return redirect(url_for('editorial_member_edit', member_id=created_id or 0))

        existing = db.editorial_members.all().equal(id=member_id).exec()
        if not existing:
            new_alert(
                _msg_text(
                    "Tahrir hay'ati a'zosi topilmadi",
                    "Участник редакционной коллегии не найден",
                    "Editorial member not found"
                ),
                'danger'
            )
            return redirect(url_for('editorial_members'))

        payload['updated_at'] = now_ts
        payload['updated_by'] = current_user_id
        db.editorial_members.all().equal(id=member_id).update(**payload).exec()
        new_alert(
            _msg_text(
                "Tahrir hay'ati a'zosi saqlandi",
                "Участник редакционной коллегии сохранён",
                "Editorial member saved"
            ),
            'success'
        )
        return redirect(url_for('editorial_member_edit', member_id=member_id))

    if member_id == 0:
        member = {
            'id': 0,
            'full_name': '',
            'full_name_uz': '',
            'full_name_ru': '',
            'position': '',
            'position_uz': '',
            'position_ru': '',
            'organization': '',
            'organization_uz': '',
            'organization_ru': '',
            'biography': '',
            'biography_uz': '',
            'biography_ru': '',
            'image': '',
            'member_type': 'editor',
            'email': '',
            'orcid': '',
            'sort_order': 0,
            'is_active': True
        }
    else:
        rows = db.editorial_members.all().equal(id=member_id).exec()
        if not rows:
            new_alert(
                _msg_text(
                    "Tahrir hay'ati a'zosi topilmadi",
                    "Участник редакционной коллегии не найден",
                    "Editorial member not found"
                ),
                'danger'
            )
            return redirect(url_for('editorial_members'))
        member = rows[0]
        member['full_name'] = _clean_text(member.get('full_name'))
        member['full_name_uz'] = _clean_text(member.get('full_name_uz'))
        member['full_name_ru'] = _clean_text(member.get('full_name_ru'))
        member['position'] = _clean_text(member.get('position'))
        member['position_uz'] = _clean_text(member.get('position_uz'))
        member['position_ru'] = _clean_text(member.get('position_ru'))
        member['organization'] = _clean_text(member.get('organization'))
        member['organization_uz'] = _clean_text(member.get('organization_uz'))
        member['organization_ru'] = _clean_text(member.get('organization_ru'))
        member['biography'] = _clean_text(member.get('biography'))
        member['biography_uz'] = _clean_text(member.get('biography_uz'))
        member['biography_ru'] = _clean_text(member.get('biography_ru'))
        member['member_type'] = _normalize_editorial_member_type(member.get('member_type'))
        member['sort_order'] = _parse_int(member.get('sort_order')) or 0
        member['is_active'] = True if member.get('is_active') is None else bool(member.get('is_active'))

    return render_template(
        'website/editorial/member_edit.html',
        member=member,
        member_type_options=_editorial_member_type_options(ui_lang),
        editorial_ui=editorial_ui
    )


@bp.route('/fmadmin/editorial-members/<int:member_id>/delete', methods=['POST'])
@is_superadmin_required
def editorial_member_delete(member_id):
    redirect_url = _safe_internal_redirect(request.form.get('redirect_url') or request.referrer, 'editorial_members')
    rows = db.editorial_members.all().equal(id=member_id).exec()
    if not rows:
        new_alert(
            _msg_text(
                "Tahrir hay'ati a'zosi topilmadi",
                "Участник редакционной коллегии не найден",
                "Editorial member not found"
            ),
            'danger'
        )
        return redirect(redirect_url)

    db.editorial_members.all().equal(id=member_id).delete().exec()
    new_alert(
        _msg_text(
            "Tahrir hay'ati a'zosi o'chirildi",
            "Участник редакционной коллегии удалён",
            "Editorial member deleted"
        ),
        'success'
    )
    return redirect(redirect_url)


@bp.route('/fmadmin/editor-assignments')
@is_admin_or_editor
def editor_assignments():
    """Список назначений для редакторов"""
    current_user = get_current_user() or {}
    current_role = _role_of(current_user)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    raw_status_filter = (request.args.get('status') or '').strip().lower()
    status_filter = raw_status_filter if raw_status_filter in EDITOR_ASSIGNMENT_STATUS_VALUES else ''
    editor_filter = request.args.get('editor', '').strip()
    submission_id_filter = request.args.get('submission_id', '').strip()
    submission_title_filter = request.args.get('submission_title', '').strip()
    current_user_id = _parse_int(current_user.get('id'))

    query = db.editor_assignments.all()

    # Если текущий пользователь - редактор, показываем только его назначения
    if current_role == 'editor' and current_user_id is not None:
        query = query.equal(editor_id=current_user_id)

    if status_filter:
        query = query.equal(status=status_filter)
    editor_filter_id = _parse_int(editor_filter)
    if editor_filter_id is not None:
        query = query.equal(editor_id=editor_filter_id)

    # Получаем все назначения для фильтрации по статьям
    try:
        all_assignments = query.exec()
    except:
        all_assignments = []
    all_assignments = [_decorate_assignment(item) for item in all_assignments]

    # Получаем все статьи для фильтрации
    try:
        all_submissions = db.submissions.all().exec()
    except:
        all_submissions = []

    submissions_map = {s.get('id'): s for s in all_submissions if s.get('id')}

    if current_role == 'admin':
        allowed_admin_submission_ids = {
            submission_id
            for submission_id, submission in submissions_map.items()
            if _can_access_submission(current_user, submission)
        }
        all_assignments = [
            assignment
            for assignment in all_assignments
            if assignment.get('submission_id') in allowed_admin_submission_ids
        ]

    # Фильтрация по ID статьи
    if submission_id_filter:
        submission_id = _parse_int(submission_id_filter)
        if submission_id is not None:
            all_assignments = [a for a in all_assignments if a.get('submission_id') == submission_id]

    # Фильтрация по названию статьи
    if submission_title_filter:
        filtered_assignments = []
        for assignment in all_assignments:
            submission = submissions_map.get(assignment.get('submission_id'))
            if submission and submission_title_filter.lower() in submission.get('title', '').lower():
                filtered_assignments.append(assignment)
        all_assignments = filtered_assignments

    all_assignments = sorted(all_assignments, key=lambda item: _parse_int(item.get('assigned_at')) or 0, reverse=True)
    total_assignments = len(all_assignments)
    total_pages = (total_assignments + per_page - 1) // per_page

    # Пагинация
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    assignments_list = all_assignments[start_idx:end_idx]

    # Получаем связанные данные
    if current_role == 'admin' and current_user_id is not None:
        editors_list = get_editors(admin_id=current_user_id)
    else:
        editors_list = get_editors()
    editors_map = {e.get('id'): e for e in get_editors() if e.get('id')}

    try:
        users = db.users.all().exec()
    except:
        users = []
    users_map = {u.get('id'): u for u in users if u.get('id')}

    return render_template('editors/assignments.html',
                         assignments=assignments_list,
                         page=page,
                         total_assignments=total_assignments,
                         total_pages=total_pages,
                         status_filter=status_filter,
                         editor_filter=editor_filter,
                         submission_id_filter=submission_id_filter,
                         submission_title_filter=submission_title_filter,
                         submissions_map=submissions_map,
                         editors_map=editors_map,
                         users_map=users_map,
                         editors=editors_list,
                         current_user=current_user)


@bp.route('/fmadmin/notifications')
@is_admin_or_editor
def role_notifications():
    current_user = get_current_user() or {}
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = 20

    total_notifications = _count_role_notifications(current_user)
    total_pages = (total_notifications + per_page - 1) // per_page if total_notifications else 1
    notifications_list = _fetch_role_notifications_page(current_user, only_unread=False, page=page, per_page=per_page)

    actor_ids = [_parse_int(item.get('actor_user_id')) for item in notifications_list if _parse_int(item.get('actor_user_id'))]
    actors_map = {}
    if actor_ids:
        try:
            actor_rows = db.users.all().any(id=list(set(actor_ids))).exec()
        except Exception:
            actor_rows = db.users.all().exec()
        actors_map = {item.get('id'): item for item in actor_rows if item.get('id')}

    unread_count = _count_unread_role_notifications(current_user)
    return render_template(
        'notifications/list.html',
        notifications=notifications_list,
        page=page,
        total_pages=total_pages,
        total_notifications=total_notifications,
        unread_count=unread_count,
        actors_map=actors_map
    )


@bp.route('/fmadmin/notifications/read/<int:notification_id>', methods=['POST'])
@is_admin_or_editor
def role_notification_read(notification_id):
    current_user = get_current_user() or {}
    _mark_role_notification_as_read(notification_id, current_user)
    redirect_url = _safe_internal_redirect(
        request.form.get('redirect_url') or request.referrer,
        'role_notifications',
    )
    return redirect(redirect_url)


@bp.route('/fmadmin/notifications/open/<int:notification_id>', methods=['POST'])
@is_admin_or_editor
def role_notification_open(notification_id):
    current_user = get_current_user() or {}
    fallback_url = _safe_internal_redirect(
        request.form.get('redirect_url') or request.referrer,
        'role_notifications',
    )
    notification = _get_role_notification_for_user(notification_id, current_user)
    if not notification:
        return redirect(fallback_url)

    _mark_role_notification_as_read(notification_id, current_user)
    action_url = _clean_text(notification.get('action_url'))
    if action_url:
        return redirect(_safe_internal_redirect(action_url, 'role_notifications'))
    return redirect(fallback_url)


@bp.route('/fmadmin/notifications/read-all', methods=['POST'])
@is_admin_or_editor
def role_notification_read_all():
    current_user = get_current_user() or {}
    changed = _mark_all_role_notifications_as_read(current_user)
    if changed:
        new_alert(
            _msg_text(
                f"{changed} ta bildirishnoma o'qildi deb belgilandi",
                f"Отмечено как прочитано: {changed}",
                f"Marked as read: {changed}"
            ),
            'success'
        )
    redirect_url = _safe_internal_redirect(
        request.form.get('redirect_url') or request.referrer,
        'role_notifications',
    )
    return redirect(redirect_url)


@bp.route('/fmadmin/submissions/<int:submission_id>/auto-assign', methods=['POST'])
@is_allowed
def auto_assign_editor(submission_id):
    current_user = get_current_user() or {}
    current_role = _role_of(current_user)
    current_user_id = _parse_int(current_user.get('id'))

    submission_rows = db.submissions.all().equal(id=submission_id).exec()
    if not submission_rows:
        new_alert(_msg_text('Maqola topilmadi', 'Статья не найдена', 'Submission not found'), 'danger')
        return redirect(url_for('submissions'))
    submission = submission_rows[0]

    if not _can_access_submission(current_user, submission):
        new_alert(t('admin_error_no_access'), 'danger')
        return redirect(url_for('submissions'))

    if not _clean_text(submission.get('anti_plagiarism_file')):
        new_alert(
            _msg_text(
                "Avto-biriktirishdan oldin antiplagiat tekshiruv faylini yuklang",
                "Перед автоназначением загрузите файл антиплагиат-проверки",
                "Upload anti-plagiarism checked file before auto assignment"
            ),
            'danger'
        )
        return redirect(url_for('submission_detail', submission_id=submission_id))

    if current_role == 'admin' and current_user_id is not None:
        candidate_editors = get_editors(admin_id=current_user_id)
    else:
        candidate_editors = get_editors()

    selected_editor = _select_best_editor_for_submission(submission, candidate_editors)
    if not selected_editor:
        new_alert(
            _msg_text(
                "Mos bo'sh tahrirchi topilmadi",
                'Подходящий свободный редактор не найден',
                'No suitable available editor found'
            ),
            'warning'
        )
        return redirect(url_for('submission_detail', submission_id=submission_id))

    editor_id = _parse_int(selected_editor.get('id'))
    now_ts = int(datetime.datetime.now().timestamp())
    acceptance_deadline_at = now_ts + 24 * 60 * 60
    completion_deadline_at = now_ts + 5 * 24 * 60 * 60

    assignment_row = db.editor_assignments.add(
        submission_id=submission_id,
        editor_id=editor_id,
        assigned_by=current_user_id or current_user.get('id'),
        assigned_at=now_ts,
        status='pending',
        assignment_note='Auto assignment',
        deadline_at=completion_deadline_at,
        acceptance_deadline_at=acceptance_deadline_at,
        completion_deadline_at=completion_deadline_at,
        accepted_at=None,
        acceptance_reminder_level='',
        completion_reminder_level='',
        admin_decision='pending',
        created_at=now_ts,
        updated_at=now_ts
    ).exec()
    assignment_id = _extract_inserted_id(assignment_row)

    _refresh_submission_editor_review_status(submission_id)

    title_text = submission.get('title') or submission_id
    message = localized_texts(
        f'Sizga "{title_text}" maqolasi avtomatik biriktirildi',
        f'Вам автоматически назначена статья "{title_text}"',
        f'You were auto-assigned submission "{title_text}"'
    )
    _create_role_notification(
        target_user_id=editor_id,
        target_role='editor',
        title=localized_texts("Yangi tahriz topshirig'i", "Новое задание на рецензию", "New review assignment"),
        message=message,
        action_url=url_for('review_assignment', assignment_id=assignment_id) if assignment_id else url_for('editor_assignments'),
        level='info',
        event_type='editor_assignment_created',
        related_submission_id=submission_id,
        related_assignment_id=assignment_id,
        actor_user_id=current_user_id
    )

    new_alert(
        _msg_text(
            f"Tahrirchi avtomatik biriktirildi: {selected_editor.get('name') or selected_editor.get('email')}",
            f"Редактор назначен автоматически: {selected_editor.get('name') or selected_editor.get('email')}",
            f"Editor auto-assigned: {selected_editor.get('name') or selected_editor.get('email')}"
        ),
        'success'
    )
    return redirect(url_for('submission_detail', submission_id=submission_id))


@bp.route('/fmadmin/submissions/<int:submission_id>/assign-editors', methods=['GET', 'POST'])
@is_allowed
def assign_editors(submission_id):
    """Назначение редакторов для проверки статьи"""
    current_user = get_current_user() or {}
    current_role = _role_of(current_user)
    current_user_id = _parse_int(current_user.get('id'))

    submission_rows = db.submissions.all().equal(id=submission_id).exec()
    if not submission_rows:
        if request.method == 'POST':
            new_alert(_msg_text('Maqola topilmadi', 'Статья не найдена', 'Submission not found'), 'danger')
            return redirect(url_for('submissions'))
        return 'Статья не найдена', 404
    submission = submission_rows[0]

    if not _can_access_submission(current_user, submission):
        if request.method == 'POST':
            new_alert(t('admin_error_no_access'), 'danger')
            return redirect(url_for('submissions'))
        return 'Доступ запрещен', 403

    anti_plagiarism_file = _clean_text(submission.get('anti_plagiarism_file'))
    is_antiplag_ready = bool(anti_plagiarism_file)

    if current_role == 'admin' and current_user_id is not None:
        editors_list = get_editors(admin_id=current_user_id)
    else:
        editors_list = get_editors()
    allowed_editor_ids = {editor.get('id') for editor in editors_list if editor.get('id')}
    now_dt = datetime.datetime.now()
    now_ts = int(now_dt.timestamp())
    min_deadline_datetime = now_dt.strftime('%Y-%m-%dT%H:%M')
    default_acceptance_deadline = (now_dt + datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M')
    default_completion_deadline = (now_dt + datetime.timedelta(days=5)).strftime('%Y-%m-%dT%H:%M')

    if request.method == 'POST':
        if not is_antiplag_ready:
            new_alert(
                _msg_text(
                    "Tahrirchiga yuborishdan oldin antiplagiat tekshiruv faylini yuklang",
                    "Перед отправкой редактору загрузите файл антиплагиат-проверки",
                    "Upload anti-plagiarism checked file before assigning editors"
                ),
                'danger'
            )
            return redirect(url_for('submission_detail', submission_id=submission_id))

        raw_editor_ids = request.form.getlist('editor_ids')
        assignment_note = _clean_text(request.form.get('assignment_note'))
        acceptance_input = _clean_text(request.form.get('acceptance_deadline') or request.form.get('acceptance_deadline_date'))
        completion_input = _clean_text(request.form.get('completion_deadline') or request.form.get('deadline_date'))
        acceptance_deadline_at = _parse_datetime_to_timestamp(acceptance_input)
        completion_deadline_at = _parse_datetime_to_timestamp(completion_input)

        if not acceptance_deadline_at:
            new_alert(
                _msg_text(
                    "Qabul qilish muddatini kiriting",
                    "Укажите срок принятия задания",
                    "Provide assignment acceptance deadline"
                ),
                'danger'
            )
            return redirect(url_for('assign_editors', submission_id=submission_id))

        if not completion_deadline_at:
            new_alert(
                _msg_text(
                    "Topshirish muddatini kiriting",
                    "Укажите срок отправки рецензии",
                    "Provide review submission deadline"
                ),
                'danger'
            )
            return redirect(url_for('assign_editors', submission_id=submission_id))

        if acceptance_deadline_at is not None and acceptance_deadline_at <= now_ts:
            new_alert(
                _msg_text(
                    "Qabul qilish muddati hozirgi vaqtdan keyin bo'lishi kerak",
                    "Срок принятия должен быть позже текущего времени",
                    "Acceptance deadline must be in the future"
                ),
                'danger'
            )
            return redirect(url_for('assign_editors', submission_id=submission_id))

        if completion_deadline_at <= now_ts:
            new_alert(
                _msg_text(
                    "Topshirish muddati hozirgi vaqtdan keyin bo'lishi kerak",
                    "Срок отправки должен быть позже текущего времени",
                    "Completion deadline must be in the future"
                ),
                'danger'
            )
            return redirect(url_for('assign_editors', submission_id=submission_id))

        if acceptance_deadline_at is not None and completion_deadline_at < acceptance_deadline_at:
            new_alert(
                _msg_text(
                    "Topshirish muddati qabul qilish muddatidan oldin bo'lmasligi kerak",
                    "Срок отправки не может быть раньше срока принятия",
                    "Completion deadline cannot be earlier than acceptance deadline"
                ),
                'danger'
            )
            return redirect(url_for('assign_editors', submission_id=submission_id))

        selected_editor_ids = []
        for editor_id in raw_editor_ids:
            parsed_editor_id = _parse_int(editor_id)
            if parsed_editor_id is None or parsed_editor_id not in allowed_editor_ids:
                continue
            if parsed_editor_id not in selected_editor_ids:
                selected_editor_ids.append(parsed_editor_id)

        if not selected_editor_ids:
            new_alert(
                _msg_text(
                    "Kamida bitta tahrirchini tanlang",
                    "Выберите хотя бы одного редактора",
                    "Select at least one editor"
                ),
                'danger'
            )
            return redirect(url_for('assign_editors', submission_id=submission_id))

        created_count = 0
        updated_count = 0

        for editor_id in selected_editor_ids:
            existing = db.editor_assignments.all().equal(submission_id=submission_id).equal(editor_id=editor_id).exec()
            if existing:
                existing_assignment = _decorate_assignment(existing[0])
                update_payload = {'updated_at': now_ts}
                if assignment_note:
                    update_payload['assignment_note'] = assignment_note
                update_payload['acceptance_deadline_at'] = acceptance_deadline_at
                update_payload['completion_deadline_at'] = completion_deadline_at
                update_payload['deadline_at'] = completion_deadline_at
                update_payload['acceptance_reminder_level'] = ''
                update_payload['completion_reminder_level'] = ''
                if existing_assignment.get('admin_decision') == 'revision_requested':
                    update_payload['admin_decision'] = 'pending'
                if update_payload:
                    db.editor_assignments.all().equal(id=existing_assignment.get('id')).update(**update_payload).exec()
                    updated_count += 1
                continue

            assignment_id = db.editor_assignments.add(
                submission_id=submission_id,
                editor_id=editor_id,
                assigned_by=current_user_id or current_user.get('id'),
                assigned_at=now_ts,
                status='pending',
                assignment_note=assignment_note,
                deadline_at=completion_deadline_at,
                acceptance_deadline_at=acceptance_deadline_at,
                completion_deadline_at=completion_deadline_at,
                accepted_at=None,
                acceptance_reminder_level='',
                completion_reminder_level='',
                admin_decision='pending',
                created_at=now_ts,
                updated_at=now_ts
            ).exec()
            assignment_id = _extract_inserted_id(assignment_id)
            created_count += 1

            message = localized_texts(
                f'Sizga "{submission.get("title") or submission_id}" maqolasi biriktirildi',
                f'Вам назначена статья "{submission.get("title") or submission_id}"',
                f'You were assigned submission "{submission.get("title") or submission_id}"'
            )
            if anti_plagiarism_file:
                message = localized_texts(
                    f'{message["uz"]}. Antiplagiat tekshiruv fayli biriktirilgan',
                    f'{message["ru"]}. Прикреплён файл антиплагиат-проверки',
                    f'{message["en"]}. Anti-plagiarism checked file is attached'
                )
            if acceptance_deadline_at:
                acceptance_label = _deadline_ts_label(acceptance_deadline_at)
                message = localized_texts(
                    f'{message["uz"]}. Qabul qilish muddati: {acceptance_label}',
                    f'{message["ru"]}. Срок принятия: {acceptance_label}',
                    f'{message["en"]}. Acceptance deadline: {acceptance_label}'
                )
            if completion_deadline_at:
                completion_label = _deadline_ts_label(completion_deadline_at)
                message = localized_texts(
                    f'{message["uz"]}. Topshirish muddati: {completion_label}',
                    f'{message["ru"]}. Срок отправки: {completion_label}',
                    f'{message["en"]}. Submission deadline: {completion_label}'
                )
            _create_role_notification(
                target_user_id=editor_id,
                target_role='editor',
                title=localized_texts("Yangi tahriz topshirig'i", "Новое задание на рецензию", "New review assignment"),
                message=message,
                action_url=url_for('review_assignment', assignment_id=assignment_id) if assignment_id else url_for('editor_assignments'),
                level='info',
                event_type='editor_assignment_created',
                related_submission_id=submission_id,
                related_assignment_id=assignment_id,
                actor_user_id=current_user_id
            )

        _refresh_submission_editor_review_status(submission_id)

        if created_count or updated_count:
            submission_title = _submission_title(submission)
            detail_url = url_for('submission_detail', submission_id=submission_id)
            author_url = '/dashboard/articles'
            author_id = _parse_int(submission.get('user_id'))
            if author_id is not None:
                _create_role_notification(
                    target_user_id=author_id,
                    target_role='user',
                    title=localized_texts("Maqolangiz tahrizga yuborildi", "Ваша статья направлена на рецензию", "Your submission was sent for review"),
                    message=localized_texts(
                        f'"{submission_title}" maqolasi tahrirchiga yuborildi',
                        f'Статья "{submission_title}" направлена редактору',
                        f'Submission "{submission_title}" was sent to editor'
                    ),
                    action_url=author_url,
                    level='info',
                    event_type='submission_sent_to_editor',
                    related_submission_id=submission_id,
                    actor_user_id=current_user_id
                )

            _notify_role_users(
                'superadmin',
                title=localized_texts("Maqolaga tahrirchi biriktirildi", "Редактор назначен на статью", "Editor assigned to submission"),
                message=localized_texts(
                    f'"{submission_title}" uchun {created_count} ta yangi topshiriq berildi',
                    f'Для "{submission_title}" создано новых назначений: {created_count}',
                    f'New editor assignments for "{submission_title}": {created_count}'
                ),
                action_url=detail_url,
                level='info',
                event_type='editor_assignment_created',
                related_submission_id=submission_id,
                actor_user_id=current_user_id,
                exclude_user_ids=[current_user_id]
            )

            assigned_admin_id = _parse_int(submission.get('assigned_admin_id'))
            if assigned_admin_id is not None and assigned_admin_id != current_user_id:
                _create_role_notification(
                    target_user_id=assigned_admin_id,
                    target_role='admin',
                    title=localized_texts("Maqolaga tahrirchi biriktirildi", "Редактор назначен на статью", "Editor assigned to submission"),
                    message=localized_texts(
                        f'"{submission_title}" uchun tahrirchi topshirig\'i yangilandi',
                        f'Для "{submission_title}" обновлено назначение редактора',
                        f'Editor assignment updated for "{submission_title}"'
                    ),
                    action_url=detail_url,
                    level='info',
                    event_type='editor_assignment_updated',
                    related_submission_id=submission_id,
                    actor_user_id=current_user_id
                )

        if created_count == 0 and updated_count == 0:
            new_alert(
                _msg_text(
                    "Tanlangan tahrirchilar allaqachon biriktirilgan",
                    "Выбранные редакторы уже назначены",
                    "Selected editors are already assigned"
                ),
                'info'
            )
            return redirect(url_for('assign_editors', submission_id=submission_id))

        new_alert(
            _msg_text(
                f'Topshiriqlar saqlandi: yangi {created_count}, yangilangan {updated_count}',
                f'Назначения сохранены: новых {created_count}, обновлено {updated_count}',
                f'Assignments saved: created {created_count}, updated {updated_count}'
            ),
            'success'
        )
        return redirect(url_for('submissions'))

    # Получаем уже назначенных редакторов
    assigned_editors = db.editor_assignments.all().equal(submission_id=submission_id).exec()
    assigned_editors = [_decorate_assignment(item) for item in assigned_editors]
    assigned_editor_ids = [a.get('editor_id') for a in assigned_editors if a.get('editor_id')]

    return render_template('editors/assign.html',
                         submission=submission,
                         editors=editors_list,
                         assigned_editor_ids=assigned_editor_ids,
                         assigned_editors=assigned_editors,
                         anti_plagiarism_file=anti_plagiarism_file,
                         is_antiplag_ready=is_antiplag_ready,
                         min_deadline_datetime=min_deadline_datetime,
                         default_acceptance_deadline=default_acceptance_deadline,
                         default_completion_deadline=default_completion_deadline)

@bp.route('/fmadmin/editor-assignments/<int:assignment_id>/review', methods=['GET', 'POST'])
@is_editor_allowed
def review_assignment(assignment_id):
    """Страница проверки статьи редактором"""
    current_user = get_current_user() or {}
    current_role = _role_of(current_user)
    current_user_id = _parse_int(current_user.get('id'))

    # Получаем назначение
    assignment_rows = db.editor_assignments.all().equal(id=assignment_id).exec()
    if not assignment_rows:
        return 'Назначение не найдено', 404
    assignment = _decorate_assignment(assignment_rows[0])

    # Проверяем права доступа
    if current_role == 'editor' and assignment.get('editor_id') != current_user_id:
        return 'Доступ запрещен', 403
    submission_rows = db.submissions.all().equal(id=assignment.get('submission_id')).exec()
    if not submission_rows:
        return 'Статья не найдена', 404
    submission = submission_rows[0]
    if current_role in {'admin', 'superadmin'} and not _can_access_submission(current_user, submission):
        return 'Доступ запрещен', 403

    if request.method == 'POST':
        if current_role != 'editor':
            new_alert(
                _msg_text(
                    "Faqat tahrirchi review yubora oladi",
                    "Только редактор может отправить рецензию",
                    "Only editor can submit review"
                ),
                'danger'
            )
            return redirect(url_for('review_assignment', assignment_id=assignment_id))

        status = _clean_text(request.form.get('status')).lower()
        if status not in EDITOR_ASSIGNMENT_REVIEWED_STATUS_VALUES:
            status = 'reviewed'
        editor_comment = _clean_text(request.form.get('editor_comment'))

        # Обработка загруженного файла
        editor_file = assignment.get('editor_file')
        has_uploaded_file = False
        if 'editor_file' in request.files and request.files['editor_file'].filename:
            file = request.files['editor_file']
            try:
                editor_file = save_file('editor_reviews', file, ['pdf', 'doc', 'docx', 'txt'])
                has_uploaded_file = True
            except ValueError:
                new_alert(_msg_text("Fayl formati noto'g'ri", 'Недопустимый формат файла', 'Invalid file format'), 'danger')
                return redirect(url_for('review_assignment', assignment_id=assignment_id))

        if not editor_comment and not has_uploaded_file and not editor_file:
            new_alert(
                _msg_text(
                    "Kamida izoh yoki fayl yuboring",
                    "Добавьте комментарий или файл",
                    "Provide comment or attach file"
                ),
                'danger'
            )
            return redirect(url_for('review_assignment', assignment_id=assignment_id))

        now_ts = int(datetime.datetime.now().timestamp())
        db.editor_assignments.all().equal(id=assignment_id).update(
            status=status,
            editor_comment=editor_comment,
            editor_file=editor_file,
            reviewed_at=now_ts,
            completion_reminder_level='',
            admin_decision='pending',
            admin_comment=None,
            admin_decided_by=None,
            admin_decided_at=None,
            updated_at=now_ts
        ).exec()

        _refresh_submission_editor_review_status(assignment.get('submission_id'))

        submission_title = _submission_title(submission)
        assignment_url = url_for('review_assignment', assignment_id=assignment_id)
        editor_decision_label = localized_texts(
            "nashrga tavsiya" if status == 'reviewed' else "rad etish tavsiyasi",
            "рекомендовано к публикации" if status == 'reviewed' else "рекомендация отклонить",
            "recommended for publication" if status == 'reviewed' else "recommendation to reject"
        )

        assigned_admin_id = _parse_int(submission.get('assigned_admin_id'))
        if assigned_admin_id is not None:
            _create_role_notification(
                target_user_id=assigned_admin_id,
                target_role='admin',
                title=localized_texts("Tahrirchi tahriz yubordi", "Редактор отправил рецензию", "Editor submitted review"),
                message=localized_texts(
                    f'"{submission_title}" bo\'yicha tahriz yuborildi: {editor_decision_label["uz"]}',
                    f'По "{submission_title}" отправлена рецензия: {editor_decision_label["ru"]}',
                    f'Review submitted for "{submission_title}": {editor_decision_label["en"]}'
                ),
                action_url=assignment_url,
                level='info',
                event_type='editor_review_submitted',
                related_submission_id=assignment.get('submission_id'),
                related_assignment_id=assignment_id,
                actor_user_id=current_user_id
            )

        _notify_role_users(
            'superadmin',
            title=localized_texts("Tahrirchi tahriz yubordi", "Редактор отправил рецензию", "Editor submitted review"),
            message=localized_texts(
                f'"{submission_title}" bo\'yicha tahriz yuborildi: {editor_decision_label["uz"]}',
                f'По "{submission_title}" отправлена рецензия: {editor_decision_label["ru"]}',
                f'Review submitted for "{submission_title}": {editor_decision_label["en"]}'
            ),
            action_url=assignment_url,
            level='info',
            event_type='editor_review_submitted',
            related_submission_id=assignment.get('submission_id'),
            related_assignment_id=assignment_id,
            actor_user_id=current_user_id
        )

        new_alert(_msg_text('Tekshiruv saqlandi', 'Проверка сохранена', 'Review saved'), 'success')
        return redirect(url_for('editor_assignments'))

    if current_role == 'editor':
        db.editor_notifications.all().equal(editor_id=current_user_id).equal(assignment_id=assignment_id).update(is_read=True).exec()
        now_ts = int(datetime.datetime.now().timestamp())
        db.role_notifications.all().equal(target_user_id=current_user_id).equal(related_assignment_id=assignment_id).update(
            is_read=True,
            read_at=now_ts
        ).exec()
        if assignment.get('status') == 'pending':
            db.editor_assignments.all().equal(id=assignment_id).update(
                status='in_review',
                accepted_at=now_ts,
                completion_reminder_level='',
                updated_at=now_ts
            ).exec()
            assignment['status'] = 'in_review'
            assignment['accepted_at'] = now_ts

    editor_user = None
    if assignment.get('editor_id'):
        editor_rows = db.users.all().equal(id=assignment.get('editor_id')).exec()
        editor_user = editor_rows[0] if editor_rows else None
    assigned_by_user = None
    if assignment.get('assigned_by'):
        assigned_rows = db.users.all().equal(id=assignment.get('assigned_by')).exec()
        assigned_by_user = assigned_rows[0] if assigned_rows else None
    admin_decided_user = None
    if assignment.get('admin_decided_by'):
        decided_rows = db.users.all().equal(id=assignment.get('admin_decided_by')).exec()
        admin_decided_user = decided_rows[0] if decided_rows else None

    can_editor_submit = current_role == 'editor' and assignment.get('status') in EDITOR_ASSIGNMENT_ACTIVE_STATUS_VALUES
    return render_template('editors/review.html',
                         assignment=assignment,
                         submission=submission,
                         current_role=current_role,
                         editor_user=editor_user,
                         assigned_by_user=assigned_by_user,
                         admin_decided_user=admin_decided_user,
                         can_editor_submit=can_editor_submit)


@bp.route('/fmadmin/editor-assignments/<int:assignment_id>/admin-decision', methods=['POST'])
@is_allowed
def assignment_admin_decision(assignment_id):
    current_user = get_current_user() or {}
    current_user_id = _parse_int(current_user.get('id'))

    assignment_rows = db.editor_assignments.all().equal(id=assignment_id).exec()
    if not assignment_rows:
        new_alert(_msg_text("Topshiriq topilmadi", "Назначение не найдено", "Assignment not found"), 'danger')
        return redirect(url_for('editor_assignments'))
    assignment = _decorate_assignment(assignment_rows[0])

    submission_rows = db.submissions.all().equal(id=assignment.get('submission_id')).exec()
    if not submission_rows:
        new_alert(_msg_text("Maqola topilmadi", "Статья не найдена", "Submission not found"), 'danger')
        return redirect(url_for('editor_assignments'))
    submission = submission_rows[0]

    if not _can_access_submission(current_user, submission):
        new_alert(t('admin_error_no_access'), 'danger')
        return redirect(url_for('editor_assignments'))

    if assignment.get('status') not in EDITOR_ASSIGNMENT_REVIEWED_STATUS_VALUES:
        new_alert(
            _msg_text(
                "Avval tahrirchi natija yuborishi kerak",
                "Сначала редактор должен отправить рецензию",
                "Editor must submit review first"
            ),
            'danger'
        )
        return redirect(url_for('review_assignment', assignment_id=assignment_id))

    admin_decision = _normalize_assignment_admin_decision(request.form.get('admin_decision'))
    if admin_decision not in {'accepted', 'revision_requested'}:
        new_alert(
            _msg_text(
                "Qarorni tanlang",
                "Выберите решение",
                "Select decision"
            ),
            'danger'
        )
        return redirect(url_for('review_assignment', assignment_id=assignment_id))

    admin_comment = _clean_text(request.form.get('admin_comment'))
    now_ts = int(datetime.datetime.now().timestamp())

    update_payload = {
        'admin_decision': admin_decision,
        'admin_comment': admin_comment,
        'admin_decided_by': current_user_id,
        'admin_decided_at': now_ts,
        'updated_at': now_ts
    }

    if admin_decision == 'revision_requested':
        update_payload['status'] = 'pending'
        update_payload['reviewed_at'] = None
        update_payload['completion_reminder_level'] = ''

    db.editor_assignments.all().equal(id=assignment_id).update(**update_payload).exec()

    editor_id = _parse_int(assignment.get('editor_id'))
    if editor_id:
        if admin_decision == 'accepted':
            notification_message = localized_texts(
                f'"{submission.get("title") or assignment.get("submission_id")}" bo\'yicha review qabul qilindi',
                f'Рецензия по "{submission.get("title") or assignment.get("submission_id")}" принята',
                f'Review for "{submission.get("title") or assignment.get("submission_id")}" was accepted'
            )
        else:
            notification_message = localized_texts(
                f'"{submission.get("title") or assignment.get("submission_id")}" bo\'yicha qayta ishlash so\'raldi',
                f'По "{submission.get("title") or assignment.get("submission_id")}" запрошена доработка',
                f'Revision requested for "{submission.get("title") or assignment.get("submission_id")}"'
            )
            if admin_comment:
                notification_message = localized_texts(
                    f'{notification_message["uz"]}. Izoh: {admin_comment}',
                    f'{notification_message["ru"]}. Комментарий: {admin_comment}',
                    f'{notification_message["en"]}. Comment: {admin_comment}'
                )
        _create_role_notification(
            target_user_id=editor_id,
            target_role='editor',
            title=localized_texts("Admin qarori yangilandi", "Решение администратора обновлено", "Admin decision updated"),
            message=notification_message,
            action_url=url_for('review_assignment', assignment_id=assignment_id),
            level='info' if admin_decision == 'accepted' else 'warning',
            event_type='assignment_admin_decision',
            related_submission_id=assignment.get('submission_id'),
            related_assignment_id=assignment_id,
            actor_user_id=current_user_id
        )

    review_status = _refresh_submission_editor_review_status(assignment.get('submission_id'))
    submission_title = _submission_title(submission)
    submission_url = url_for('submission_detail', submission_id=assignment.get('submission_id'))
    author_url = '/dashboard/articles'

    author_id = _parse_int(submission.get('user_id'))
    if author_id is not None:
        if admin_decision == 'accepted':
            author_title = localized_texts("Maqolangiz bo'yicha tahriz yakunlandi", "Рецензирование вашей статьи завершено", "Review of your submission is completed")
            author_message = localized_texts(
                f'"{submission_title}" bo\'yicha ijobiy tahriz tasdiqlandi',
                f'По "{submission_title}" подтверждена положительная рецензия',
                f'Positive review approved for "{submission_title}"'
            )
            author_level = 'success'
        else:
            author_title = localized_texts("Maqolangiz qayta ko'rib chiqilmoqda", "Ваша статья направлена на повторное рассмотрение", "Your submission is under re-review")
            author_message = localized_texts(
                f'"{submission_title}" bo\'yicha qo\'shimcha tahriz so\'raldi',
                f'По "{submission_title}" запрошена дополнительная рецензия',
                f'Additional review requested for "{submission_title}"'
            )
            author_level = 'warning'
        _create_role_notification(
            target_user_id=author_id,
            target_role='user',
            title=author_title,
            message=author_message,
            action_url=author_url,
            level=author_level,
            event_type='submission_review_progress',
            related_submission_id=assignment.get('submission_id'),
            actor_user_id=current_user_id
        )

    _notify_role_users(
        'superadmin',
        title=localized_texts("Admin tahriz bo'yicha qaror berdi", "Администратор принял решение по рецензии", "Admin made a review decision"),
        message=localized_texts(
            f'"{submission_title}" uchun qaror: {"qabul qilindi" if admin_decision == "accepted" else "qayta ishlash"}',
            f'Решение по "{submission_title}": {"принято" if admin_decision == "accepted" else "доработка"}',
            f'Decision for "{submission_title}": {"accepted" if admin_decision == "accepted" else "revision requested"}'
        ),
        action_url=submission_url,
        level='info' if admin_decision == 'accepted' else 'warning',
        event_type='assignment_admin_decision',
        related_submission_id=assignment.get('submission_id'),
        related_assignment_id=assignment_id,
        actor_user_id=current_user_id,
        exclude_user_ids=[current_user_id]
    )

    if review_status == 'approved':
        new_alert(
            _msg_text(
                'Tahriz natijasi qabul qilindi va maqola tavsiya bosqichiga o\'tdi',
                'Результат рецензирования принят, статья переведена на этап рекомендации',
                'Review accepted and submission moved to recommendation stage'
            ),
            'success'
        )
    elif admin_decision == 'revision_requested':
        new_alert(
            _msg_text(
                "Tahrirchiga qayta ishlashga yuborildi",
                "Отправлено редактору на доработку",
                "Sent back to editor for revision"
            ),
            'warning'
        )
    else:
        new_alert(
            _msg_text(
                "Tahriz natijasi qabul qilindi",
                "Результат рецензирования принят",
                "Review accepted"
            ),
            'success'
        )
    return redirect(url_for('review_assignment', assignment_id=assignment_id))

def register(app):
    app.register_blueprint(bp)
    # Add endpoint aliases without blueprint prefix for legacy templates (url_for('index'), etc.)
    for rule in list(app.url_map.iter_rules()):
        if not rule.endpoint.startswith('fmadmin_web.'):
            continue
        if not rule.rule.startswith('/fmadmin/'):
            continue
        alias = rule.endpoint.split('.', 1)[1]
        if alias == 'static' or alias in app.view_functions:
            continue
        app.add_url_rule(
            rule.rule,
            endpoint=alias,
            view_func=app.view_functions[rule.endpoint],
            methods=sorted(m for m in rule.methods if m not in {'HEAD', 'OPTIONS'}) or None
        )
