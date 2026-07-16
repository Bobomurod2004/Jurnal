# flake8: noqa
import json
import logging
import mimetypes
import os
import re
import time
import io
import zipfile
from functools import lru_cache
from urllib.parse import urlparse, parse_qs, unquote
from flask import current_app, render_template, session, request, jsonify, flash, redirect, url_for, send_file, send_from_directory, abort, Response
from markupsafe import escape
from extensions import dbc
from modules.translate import t, translate, clear_translations_cache
try:
    import mainweb.settings as settings
except ImportError:
    import settings
from utils.auth import is_valid_email, login_required, sanitize_input
from utils.emailer import send_notification_email
from utils.private_uploads import extract_private_upload_key
from utils.roles import hydrate_user_roles, user_has_role
from shared.publication_metadata import (
    publication_metadata_field_labels,
    publication_metadata_label,
    publication_metadata_options,
)

try:
    import maxminddb
except ImportError:
    maxminddb = None

GEOIP_DB_PATH = os.getenv(
    'GEOIP_DB_PATH',
    os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'geoip', 'GeoLite2-Country.mmdb')
)

EDITORIAL_MEMBER_TYPE_LABELS = {
    'en': {
        'editor_in_chief': "Editor-in-Chief",
        'deputy_editor_in_chief': "Deputy Editor-in-Chief",
        'executive_secretary': "Executive Secretary",
        'editorial_board': "Editorial Board",
        'international_editorial_board': "International Editorial Board",
        'editorial_council': "Editorial Council",
        'international_editorial_council': "International Editorial Council",
    },
    'uz': {
        'editor_in_chief': "Bosh muharrir",
        'deputy_editor_in_chief': "Bosh muharrir o'rinbosari",
        'executive_secretary': "Mas'ul kotib",
        'editorial_board': "Tahrir hay'ati",
        'international_editorial_board': "Xalqaro tahrir hay'ati",
        'editorial_council': "Tahrir kengashi",
        'international_editorial_council': "Xalqaro tahrir kengashi",
    },
    'ru': {
        'editor_in_chief': "Главный редактор",
        'deputy_editor_in_chief': "Заместитель главного редактора",
        'executive_secretary': "Ответственный секретарь",
        'editorial_board': "Редакционная коллегия",
        'international_editorial_board': "Международная редакционная коллегия",
        'editorial_council': "Редакционный совет",
        'international_editorial_council': "Международный редакционный совет",
    }
}
EDITORIAL_MEMBER_TYPE_LEGACY_ALIASES = {
    'deputy_editor': 'executive_secretary',
    'editor': 'editorial_board',
    'reviewer': 'editorial_board',
    'advisory_member': 'editorial_board',
    'technical_editor': 'editorial_board',
    'translator': 'editorial_board',
}
EDITORIAL_MEMBER_TYPE_ORDER = [
    'editor_in_chief',
    'deputy_editor_in_chief',
    'executive_secretary',
    'editorial_board',
    'international_editorial_board',
    'editorial_council',
    'international_editorial_council',
]
FEATURED_EDITORIAL_GROUP_KEYS = (
    'editor_in_chief',
    'deputy_editor_in_chief',
    'executive_secretary',
)
EDITORIAL_GROUP_THEMES = {
    'editor_in_chief': {
        'accent': '#d62828',
        'accent_dark': '#a61e1e',
        'soft': '#fff2f2',
        'border': '#f4b9b9',
    },
    'deputy_editor_in_chief': {
        'accent': '#f4b400',
        'accent_dark': '#d39a00',
        'soft': '#fff9e7',
        'border': '#f5d97b',
    },
    'executive_secretary': {
        'accent': '#3a9c23',
        'accent_dark': '#2f7e1d',
        'soft': '#eefbe8',
        'border': '#b9e3ab',
    },
    'editorial_board': {
        'accent': '#1666d3',
        'accent_dark': '#104ea3',
        'soft': '#edf5ff',
        'border': '#bfd8fb',
    },
    'international_editorial_board': {
        'accent': '#8c3fd1',
        'accent_dark': '#6d2fa4',
        'soft': '#f7efff',
        'border': '#dbc1f6',
    },
    'editorial_council': {
        'accent': '#b06a2a',
        'accent_dark': '#8a5120',
        'soft': '#fff5ec',
        'border': '#efd0b0',
    },
    'international_editorial_council': {
        'accent': '#0f8b9d',
        'accent_dark': '#0c6e7d',
        'soft': '#ebfbfd',
        'border': '#b7e7ee',
    },
}


def _build_editorial_member_type_aliases():
    aliases = {}
    for group_key in EDITORIAL_MEMBER_TYPE_ORDER:
        aliases[group_key] = group_key
    for labels in EDITORIAL_MEMBER_TYPE_LABELS.values():
        for group_key, label in labels.items():
            aliases[(label or '').strip().lower()] = group_key
    aliases.update(EDITORIAL_MEMBER_TYPE_LEGACY_ALIASES)
    return aliases


EDITORIAL_MEMBER_TYPE_ALIASES = _build_editorial_member_type_aliases()
EDITORIAL_UI_TEXTS = {
    'en': {
        'total_members': 'Total Members',
        'sections': 'Sections',
        'sections_title': 'Sections',
        'members_suffix': 'members',
        'empty': 'No editorial team members have been added yet.',
        'editor_fallback': 'Editor',
        'profile_button': 'Profile',
        'cv_button': 'CV',
        'orcid_button': 'ORCID',
        'scopus_button': 'Scopus',
        'researcherid_button': 'ResearcherID',
        'google_scholar_button': 'Scholar',
        'google_scholar_full': 'Google Scholar',
        'biography_title': 'Short Biography',
        'research_interests_title': 'Research Interests',
        'academic_degree_title': 'Academic Degree',
        'academic_title_title': 'Academic Title',
        'contact_title': 'Academic Profiles',
        'close_button': 'Close',
        'note': 'Click on Profile to view detailed information about each member.',
        'team_heading_uz': 'TAHRIRIY JAMOA',
        'team_heading_ru': 'РЕДАКЦИОННАЯ КОМАНДА',
        'leadership_label': 'Leadership',
    },
    'uz': {
        'total_members': "Umumiy a'zolar",
        'sections': "Yo'nalishlar",
        'sections_title': "Bo'limlar",
        'members_suffix': "a'zo",
        'empty': "Hozircha tahririyat jamoasi a'zolari qo'shilmagan.",
        'editor_fallback': "Tahrirchi",
        'profile_button': 'Profil',
        'cv_button': 'CV',
        'orcid_button': 'ORCID',
        'scopus_button': 'Scopus',
        'researcherid_button': 'ResearcherID',
        'google_scholar_button': 'Scholar',
        'google_scholar_full': 'Google Scholar',
        'biography_title': 'Qisqacha biografiya',
        'research_interests_title': 'Ilmiy qiziqishlar',
        'academic_degree_title': 'Ilmiy daraja',
        'academic_title_title': 'Ilmiy unvon',
        'contact_title': 'Ilmiy profillar',
        'close_button': 'Yopish',
        'note': "Har bir a'zo haqida batafsil ma'lumotni Profil tugmasi orqali ko'rishingiz mumkin.",
        'team_heading_uz': 'TAHRIRIY JAMOA',
        'team_heading_ru': 'РЕДАКЦИОННАЯ КОМАНДА',
        'leadership_label': 'Rahbariyat',
    },
    'ru': {
        'total_members': 'Всего участников',
        'sections': 'Разделы',
        'sections_title': 'Разделы',
        'members_suffix': 'участников',
        'empty': 'Пока участники редакционной команды не добавлены.',
        'editor_fallback': 'Редактор',
        'profile_button': 'Профиль',
        'cv_button': 'CV',
        'orcid_button': 'ORCID',
        'scopus_button': 'Scopus',
        'researcherid_button': 'ResearcherID',
        'google_scholar_button': 'Scholar',
        'google_scholar_full': 'Google Scholar',
        'biography_title': 'Краткая биография',
        'research_interests_title': 'Научные интересы',
        'academic_degree_title': 'Учёная степень',
        'academic_title_title': 'Учёное звание',
        'contact_title': 'Научные профили',
        'close_button': 'Закрыть',
        'note': 'Нажмите Profile, чтобы открыть подробную информацию о каждом участнике.',
        'team_heading_uz': 'TAHRIRIY JAMOA',
        'team_heading_ru': 'РЕДАКЦИОННАЯ КОМАНДА',
        'leadership_label': 'Руководство',
    }
}
ISSUE_UI_TEXTS = {
    'en': {
        'members_suffix': 'members',
        'uzbekistan_title': 'From Uzbekistan',
        'international_title': 'From Other Countries'
    },
    'uz': {
        'members_suffix': "a'zo",
        'uzbekistan_title': "O'zbekistondan",
        'international_title': 'Boshqa davlatlardan'
    },
    'ru': {
        'members_suffix': 'участников',
        'uzbekistan_title': 'Из Узбекистана',
        'international_title': 'Из других стран'
    }
}
COUNTRY_STATS_UI_TEXTS = {
    'en': {
        'title': 'Country Statistics',
        'view_full_map': 'View map',
        'view_all_countries': 'View all countries',
        'modal_title': 'Statistics by Country',
        'top_title': 'Top 10 - Statistics',
        'select_country': 'Select a country',
        'total': 'Total',
        'authors': 'Authors',
        'views': 'Views',
        'downloads': 'Downloads',
        'close': 'Close',
        'unknown_country': 'Other countries',
        'view_country_stats': 'View statistics',
    },
    'uz': {
        'title': "Davlatlar statistikasi",
        'view_full_map': "Xaritani ko'rish",
        'view_all_countries': "Barchasini ko'rish",
        'modal_title': "Davlatlar bo'yicha statistika",
        'top_title': 'Top 10 - Statistika',
        'select_country': 'Davlat tanlang',
        'total': 'Jami',
        'authors': 'Mualliflar',
        'views': "Ko'rishlar",
        'downloads': 'Yuklamalar',
        'close': 'Yopish',
        'unknown_country': 'Boshqa davlatlar',
        'view_country_stats': "Statistikani ko'rish",
    },
    'ru': {
        'title': 'Статистика по странам',
        'view_full_map': 'Открыть карту',
        'view_all_countries': 'Показать все страны',
        'modal_title': 'Статистика по странам',
        'top_title': 'Топ-10 - Статистика',
        'select_country': 'Выберите страну',
        'total': 'Всего',
        'authors': 'Авторы',
        'views': 'Просмотры',
        'downloads': 'Загрузки',
        'close': 'Закрыть',
        'unknown_country': 'Другие страны',
        'view_country_stats': 'Показать статистику',
    },
}
AUTHOR_TOOLTIP_UI_TEXTS = {
    'en': {
        'email_label': 'Email',
        'organization_label': 'Organization',
        'country_label': 'Country',
        'workplace_label': 'Department',
        'orcid_label': 'ORCID',
        'not_specified': 'Not specified',
    },
    'uz': {
        'email_label': 'Email',
        'organization_label': 'Tashkilot',
        'country_label': 'Mamlakat',
        'workplace_label': "Bo'limi",
        'orcid_label': 'ORCID',
        'not_specified': "Ko'rsatilmagan",
    },
    'ru': {
        'email_label': 'Email',
        'organization_label': 'Организация',
        'country_label': 'Страна',
        'workplace_label': 'Отдел',
        'orcid_label': 'ORCID',
        'not_specified': 'Не указано',
    },
}
UZBEKISTAN_LOCATION_TOKENS = (
    "o'zbekiston", 'ozbekiston', 'uzbekistan', 'узбекистан', 'tashkent', 'toshkent'
)
INTERNATIONAL_LOCATION_TOKENS = (
    'italy', 'italiya', 'италия', 'russia', 'rossiya', 'россия',
    'japan', 'yaponiya', 'япония', 'india', 'hindiston', 'индия',
    'france', 'fransiya', 'франция', 'germany', 'germaniya', 'германия',
    'canada', 'kanada', 'канада', 'london', 'moscow', 'moskva', 'москва'
)
PAYMENT_GUIDE_KEY = 'payment_guide_html'
PAGE_ALIAS_REDIRECTS = {
    'editorial_board': ('app__editorial', {}),
    'latest_articles': ('app__articles', {}),
    'all_issues': ('app__issues', {}),
    'special_issues': ('app__issues', {'category': 'special'}),
    'current_issue': ('app__issues', {}),
}

logger = logging.getLogger(__name__)
TARIFF_ENTITLEMENT_SCOPES = {'all', 'archive'}
DEFAULT_ARCHIVE_DAYS_THRESHOLD = 365
ALLOWED_TARIFF_FEATURE_PERMISSIONS = {
    'access_latest_content',
    'access_archive_content',
    'download_subscription_files',
    'article_discount',
    'issue_discount',
}
ACTIVITY_EVENT_TYPES = {'view', 'download'}
UNKNOWN_COUNTRY_KEY = 'unknown'
OTHER_COUNTRY_KEY = 'other'
OTHER_COUNTRY_NAME = 'Other countries'
ACTIVITY_EVENTS_BOOTSTRAP_MIGRATION = 'bootstrap_legacy_stats_v1'
ACTIVITY_EVENTS_BOOTSTRAP_LOCK_ID = 741920531

COUNTRY_ISO_BY_NAME = {
    # Central Asia
    'Uzbekistan': 'uz', "O'zbekiston": 'uz', 'Ozbekiston': 'uz', 'Uzbekiston': 'uz', 'Ўзбекистон': 'uz', 'Узбекистан': 'uz',
    'Russia': 'ru', 'Россия': 'ru', 'Rossiya': 'ru', 'Russian Federation': 'ru',
    'Kazakhstan': 'kz', "Qozog'iston": 'kz', 'Казахстан': 'kz',
    'Kyrgyzstan': 'kg', 'Qirgʻiziston': 'kg', 'Кыргызстан': 'kg',
    'Tajikistan': 'tj', 'Tojikiston': 'tj', 'Таджикистан': 'tj',
    'Turkmenistan': 'tm', 'Туркменистан': 'tm', 'Турменистан': 'tm', 'Turkmaniston': 'tm',
    'Azerbaijan': 'az', 'Озарбайжон': 'az', 'Азербайджан': 'az',
    'Georgia': 'ge', 'Грузия': 'ge',
    'Armenia': 'am', 'Armaniston': 'am', 'Армения': 'am',
    'Mongolia': 'mn', 'Mongʻoliya': 'mn',
    # Middle East
    'Turkey': 'tr', 'Türkiye': 'tr', 'Turkiya': 'tr', 'Турция': 'tr',
    'Iran': 'ir', 'Eron': 'ir', 'Иран': 'ir',
    'Iraq': 'iq', 'Iroq': 'iq',
    'Saudi Arabia': 'sa', 'Saudiya Arabistoni': 'sa',
    'United Arab Emirates': 'ae', 'UAE': 'ae', 'BAA': 'ae',
    'Kuwait': 'kw', 'Quvayt': 'kw',
    'Qatar': 'qa', 'Qatar': 'qa',
    'Jordan': 'jo', 'Iordaniya': 'jo',
    'Lebanon': 'lb', 'Livan': 'lb',
    'Syria': 'sy', 'Suriya': 'sy',
    'Israel': 'il', 'Isroil': 'il',
    'Egypt': 'eg', 'Misr': 'eg', 'Египет': 'eg',
    'Yemen': 'ye', 'Yaman': 'ye',
    # South & East Asia
    'China': 'cn', 'Xitoy': 'cn', 'Китай': 'cn',
    'Japan': 'jp', 'Yaponiya': 'jp', 'Япония': 'jp',
    'South Korea': 'kr', 'Korea': 'kr', 'Janubiy Koreya': 'kr',
    'North Korea': 'kp', 'Shimoliy Koreya': 'kp',
    'India': 'in', 'Hindiston': 'in', 'Индия': 'in',
    'Pakistan': 'pk', 'Pokiston': 'pk', 'Пакистан': 'pk',
    'Bangladesh': 'bd', 'Bangladesh': 'bd',
    'Afghanistan': 'af', 'Afgʻoniston': 'af', 'Афганистан': 'af',
    'Indonesia': 'id', 'Indoneziya': 'id',
    'Malaysia': 'my', 'Malayziya': 'my',
    'Philippines': 'ph', 'Filippin': 'ph',
    'Vietnam': 'vn', 'Vyetnam': 'vn',
    'Thailand': 'th', 'Tailand': 'th',
    'Singapore': 'sg', 'Singapur': 'sg',
    'Taiwan': 'tw', 'Tayvan': 'tw',
    'Myanmar': 'mm', 'Burma': 'mm',
    'Cambodia': 'kh', 'Kambodja': 'kh',
    'Sri Lanka': 'lk', 'Shri-Lanka': 'lk',
    'Nepal': 'np', 'Nepal': 'np',
    # Europe (West)
    'Germany': 'de', 'Deutschland': 'de', 'Germaniya': 'de', 'Германия': 'de',
    'United Kingdom': 'gb', 'UK': 'gb', 'Britain': 'gb', 'Buyuk Britaniya': 'gb', 'England': 'gb',
    'France': 'fr', 'Frantsiya': 'fr', 'Франция': 'fr',
    'Italy': 'it', 'Italiya': 'it', 'Италия': 'it',
    'Spain': 'es', 'Ispaniya': 'es', 'Испания': 'es',
    'Netherlands': 'nl', 'Niderlandiya': 'nl', 'Holland': 'nl',
    'Switzerland': 'ch', 'Shveytsariya': 'ch',
    'Sweden': 'se', 'Shvetsiya': 'se',
    'Norway': 'no', 'Norvegiya': 'no',
    'Finland': 'fi', 'Finlyandiya': 'fi',
    'Belgium': 'be', 'Belgiya': 'be',
    'Austria': 'at', 'Avstriya': 'at',
    'Denmark': 'dk', 'Daniya': 'dk',
    'Ireland': 'ie', 'Irlandiya': 'ie',
    'Portugal': 'pt', 'Portugaliya': 'pt',
    'Greece': 'gr', 'Gretsiya': 'gr',
    # Europe (East)
    'Poland': 'pl', 'Polsha': 'pl', 'Польша': 'pl',
    'Ukraine': 'ua', 'Ukraina': 'ua', 'Украина': 'ua',
    'Belarus': 'by', 'Belorussiya': 'by', 'Беларусь': 'by',
    'Czech Republic': 'cz', 'Czechia': 'cz', 'Chexiya': 'cz',
    'Slovakia': 'sk', 'Slovakiya': 'sk',
    'Hungary': 'hu', 'Vengriya': 'hu',
    'Romania': 'ro', 'Ruminiya': 'ro',
    'Bulgaria': 'bg', 'Bolgariya': 'bg',
    'Serbia': 'rs', 'Serbiya': 'rs',
    'Croatia': 'hr', 'Xorvatiya': 'hr',
    'Slovenia': 'si', 'Sloveniya': 'si',
    'Lithuania': 'lt', 'Litva': 'lt',
    'Latvia': 'lv', 'Latviya': 'lv',
    'Estonia': 'ee', 'Estoniya': 'ee',
    'Moldova': 'md', 'Moldova': 'md',
    'Albania': 'al', 'Albaniya': 'al',
    'North Macedonia': 'mk', 'Makedoniya': 'mk',
    'Bosnia and Herzegovina': 'ba', 'Bosniya': 'ba',
    # North America
    'United States': 'us', 'USA': 'us', 'U.S.A.': 'us', 'AQSh': 'us', 'America': 'us',
    'Canada': 'ca', 'Kanada': 'ca', 'Канада': 'ca',
    'Mexico': 'mx', 'Meksika': 'mx',
    # Latin America
    'Brazil': 'br', 'Braziliya': 'br',
    'Argentina': 'ar', 'Argentina': 'ar',
    'Colombia': 'co', 'Kolumbiya': 'co',
    'Chile': 'cl', 'Chili': 'cl',
    'Peru': 'pe', 'Peru': 'pe',
    'Venezuela': 've', 'Venesuela': 've',
    # Africa
    'Morocco': 'ma', 'Marokash': 'ma',
    'Algeria': 'dz', 'Jazoir': 'dz',
    'Tunisia': 'tn', 'Tunis': 'tn',
    'Libya': 'ly', 'Liviya': 'ly',
    'Nigeria': 'ng', 'Nigeriya': 'ng',
    'South Africa': 'za', 'Janubiy Afrika': 'za',
    'Kenya': 'ke', 'Keniya': 'ke',
    'Ethiopia': 'et', 'Efiopiya': 'et',
    'Ghana': 'gh', 'Gana': 'gh',
    'Tanzania': 'tz', 'Tanzaniya': 'tz',
    # Oceania
    'Australia': 'au', 'Avstraliya': 'au', 'Австралия': 'au',
    'New Zealand': 'nz', 'Yangi Zelandiya': 'nz',
}

APOSTROPHE_FOLD_TABLE = str.maketrans({
    'ʻ': "'",  # U+02BB modifier letter turned comma (official Uzbek Latin)
    'ʼ': "'",  # U+02BC modifier letter apostrophe
    '’': "'",  # U+2019 right single quotation mark
    '‘': "'",  # U+2018 left single quotation mark
    '`': "'",
    '´': "'",
})


def _fold_apostrophes(value):
    return str(value or '').translate(APOSTROPHE_FOLD_TABLE)


COUNTRY_ISO_LOOKUP = {
    re.sub(r'\s+', ' ', _fold_apostrophes(name)).strip().lower(): str(iso or '').strip().lower()
    for name, iso in COUNTRY_ISO_BY_NAME.items()
    if str(name or '').strip() and str(iso or '').strip()
}

COUNTRY_DISPLAY_BY_ISO = {}
for _country_name_raw, _country_iso_raw in COUNTRY_ISO_BY_NAME.items():
    _country_name_clean = str(_country_name_raw or '').strip()
    _country_iso_clean = str(_country_iso_raw or '').strip().lower()
    if not _country_name_clean or not _country_iso_clean:
        continue
    if re.match(r"^[A-Za-z0-9 .,'()\-]+$", _country_name_clean):
        COUNTRY_DISPLAY_BY_ISO.setdefault(_country_iso_clean, _country_name_clean)
for _country_name_raw, _country_iso_raw in COUNTRY_ISO_BY_NAME.items():
    _country_name_clean = str(_country_name_raw or '').strip()
    _country_iso_clean = str(_country_iso_raw or '').strip().lower()
    if not _country_name_clean or not _country_iso_clean:
        continue
    COUNTRY_DISPLAY_BY_ISO.setdefault(_country_iso_clean, _country_name_clean)


def _parse_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_float(value, default=0.0):
    if value in (None, ''):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _stored_upload_value_to_list(value):
    if value is None:
        return []

    raw_items = None
    if isinstance(value, (list, tuple)):
        raw_items = list(value)
    else:
        raw_text = _clean_text(value)
        if not raw_text:
            return []
        if raw_text.startswith('['):
            try:
                parsed = json.loads(raw_text)
            except (TypeError, ValueError, json.JSONDecodeError):
                parsed = None
            if isinstance(parsed, list):
                raw_items = parsed
        if raw_items is None:
            raw_items = [raw_text]

    items = []
    seen = set()
    for item in raw_items:
        cleaned = _clean_text(item)
        if cleaned and cleaned not in seen:
            items.append(cleaned)
            seen.add(cleaned)
    return items


def _multilingual_email_text(uz_text, ru_text=None, en_text=None, separator=' | ', include_labels=False):
    items = (
        ('UZ', _clean_text(uz_text)),
        ('RU', _clean_text(ru_text if ru_text is not None else uz_text)),
        ('EN', _clean_text(en_text if en_text is not None else uz_text)),
    )
    parts = []
    for label, text in items:
        if not text:
            continue
        if include_labels:
            parts.append(f'[{label}] {text}')
        else:
            parts.append(text)
    return separator.join(parts)


def _format_scholar_date_from_timestamp(timestamp_value):
    ts = _parse_int(timestamp_value)
    if ts is None or ts <= 0:
        return ''
    try:
        dt = time.gmtime(ts)
    except (OverflowError, ValueError, OSError):
        return ''
    return f"{dt.tm_year}/{dt.tm_mon}/{dt.tm_mday}"


def _extract_page_range_bounds(page_range_value):
    page_range_text = _clean_text(page_range_value)
    if not page_range_text:
        return '', ''

    normalized = page_range_text.replace('–', '-').replace('—', '-')
    range_match = re.search(r'([A-Za-z]?\d+)\s*-\s*([A-Za-z]?\d+)', normalized)
    if range_match:
        return range_match.group(1), range_match.group(2)

    single_match = re.search(r'([A-Za-z]?\d+)', normalized)
    if single_match:
        single_page = single_match.group(1)
        return single_page, single_page

    return '', ''


def _build_scholar_meta(publication, issue, author_names, article_id, current_lang):
    publication_row = publication or {}
    issue_row = issue or {}
    unique_authors = []
    for author_name in author_names or []:
        cleaned = _clean_text(author_name)
        if cleaned and cleaned not in unique_authors:
            unique_authors.append(cleaned)

    publication_date = _format_scholar_date_from_timestamp(publication_row.get('date_publish'))
    if not publication_date:
        publication_date = _format_scholar_date_from_timestamp(publication_row.get('created_at'))
    if not publication_date:
        publication_date = _format_scholar_date_from_timestamp(issue_row.get('created_at'))
    if not publication_date:
        issue_year = _parse_int(issue_row.get('year'))
        publication_date = str(issue_year) if issue_year is not None else ''

    first_page, last_page = _extract_page_range_bounds(publication_row.get('page_range'))

    requires_access = bool(publication_row.get('is_paid') or publication_row.get('subscription_enable'))
    is_world_readable = not requires_access
    pdf_url = url_for('app__download_article', article_id=article_id, _external=True) if is_world_readable else ''

    meta = {
        'title': _clean_text(publication_row.get('title')),
        'authors': unique_authors,
        'publication_date': publication_date,
        'journal_title': _clean_text(t('website_title')) or 'Philology Matters',
        'volume': _clean_text(issue_row.get('vol_no')),
        'issue': _clean_text(issue_row.get('issue_no')),
        'first_page': first_page,
        'last_page': last_page,
        'doi': _clean_text(publication_row.get('doi')),
        'abstract_url': url_for('app__article', article_id=article_id, _external=True),
        'pdf_url': pdf_url,
        'language': _clean_text(current_lang).lower(),
        'is_world_readable': is_world_readable,
    }
    return meta


def _format_iso_date_from_timestamp(timestamp_value):
    ts = _parse_int(timestamp_value)
    if ts is None or ts <= 0:
        return ''
    try:
        return time.strftime('%Y-%m-%d', time.gmtime(ts))
    except (OverflowError, ValueError, OSError):
        return ''


def _extract_timestamp_by_keys(record, keys):
    row = record or {}
    for key in keys:
        ts = _parse_int(row.get(key))
        if ts is not None and ts > 0:
            return ts
    return None


def _timestamp_from_year(year_value):
    year = _parse_int(year_value)
    if year is None or year < 1970 or year > 2100:
        return None
    try:
        return int(time.mktime(time.strptime(f'{year}-01-01', '%Y-%m-%d')))
    except Exception:
        return None


def _add_sitemap_url(entries, seen_urls, endpoint, endpoint_kwargs=None, lastmod_ts=None, changefreq=None, priority=None):
    kwargs = dict(endpoint_kwargs or {})
    kwargs['_external'] = True
    try:
        loc = url_for(endpoint, **kwargs)
    except Exception:
        return

    if not loc or loc in seen_urls:
        return

    payload = {
        'loc': loc,
        'lastmod': _format_iso_date_from_timestamp(lastmod_ts),
        'changefreq': _clean_text(changefreq).lower(),
        'priority': _clean_text(priority),
    }
    entries.append(payload)
    seen_urls.add(loc)


def _issue_sort_key(issue_row):
    row = issue_row or {}
    year = _parse_int(row.get('year')) or 0
    issue_no_text = _clean_text(row.get('issue_no'))
    issue_no_numeric = _parse_int(issue_no_text)
    issue_no_sort = issue_no_numeric if issue_no_numeric is not None else -1
    return (year, issue_no_sort, issue_no_text.lower())


class _SimplePagination:
    def __init__(self, page, pages):
        self.page = max(_parse_int(page) or 1, 1)
        self.pages = max(_parse_int(pages) or 1, 1)

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_num(self):
        return self.page + 1

    def iter_pages(self, left_edge=1, left_current=2, right_current=2, right_edge=1):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (num > self.page - left_current - 1 and num < self.page + right_current)
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


MASTERS_ISSUE_ALIASES = {
    'masters',
    'special_masters',
}
MASTERS_ISSUE_ALIASES_NORMALIZED = {
    'masters',
    'special masters',
}
MASTERS_SERIES_KEYS = {
    'series_masters',
    'special_issue_masters',
}
MASTERS_SERIES_SESSION_KEY = 'mainweb_masters_series_enabled'


ISSUE_CATEGORY_ALIASES = {
    'masters': 'masters',
    'master': 'masters',
    'magistr': 'masters',
    'magistratura': 'masters',
    'magistrantura': 'masters',
    'magituradi': 'masters',
    'магистр': 'masters',
    'магистратура': 'masters',
    'phd': 'phd',
    'doctor': 'phd',
    'doctoral': 'phd',
    'doktor': 'phd',
    'doktorant': 'phd',
    'doktorantura': 'phd',
    'доктор': 'phd',
    'докторант': 'phd',
    'докторантура': 'phd',
    'teacher': 'teacher',
    "o'qituvchi": 'teacher',
    'oqituvchi': 'teacher',
    'professor': 'teacher',
    'professors': 'teacher',
    'преподаватель': 'teacher',
    'профессор': 'teacher',
    'special': 'special',
    'special issue': 'special',
    'maxsus': 'special',
    'maxsus son': 'special',
    'специальный выпуск': 'special',
    'special_masters': 'special_masters',
    'special masters': 'special_masters',
    'masters_special': 'special_masters',
    'masters special': 'special_masters',
    'special master': 'special_masters',
    'maxsus magistratura': 'special_masters',
    'специальный выпуск магистратура': 'special_masters',
    'special_phd': 'special_phd',
    'special phd': 'special_phd',
    'phd_special': 'special_phd',
    'phd special': 'special_phd',
    'special doctoral': 'special_phd',
    'maxsus doktorantura': 'special_phd',
    'специальный выпуск докторантура': 'special_phd',
    'special_teacher': 'special_teacher',
    'special teacher': 'special_teacher',
    'teacher_special': 'special_teacher',
    'teacher special': 'special_teacher',
    'special academic staff': 'special_teacher',
    "maxsus professor o'qituvchilar": 'special_teacher',
    'специальный выпуск профессорско преподавательский состав': 'special_teacher',
}

ISSUE_CATEGORY_PREFIXES = (
    'fm',
    'series',
    'seriya',
    'серия',
)


def _normalize_issue_category_text(value):
    text = _clean_text(value).lower()
    if not text:
        return ''

    text = (
        text.replace('’', "'")
        .replace('`', "'")
        .replace('“', '"')
        .replace('”', '"')
        .replace('&', ' and ')
    )
    text = re.sub(r"[_\-/]+", ' ', text)
    text = re.sub(r"[^\w\s']", ' ', text, flags=re.UNICODE)
    return ' '.join(text.split())


def _is_masters_issue_alias(value):
    raw = _clean_text(value).lower().replace('-', '_')
    if raw in MASTERS_ISSUE_ALIASES:
        return True
    return _normalize_issue_category_text(value) in MASTERS_ISSUE_ALIASES_NORMALIZED


def _set_masters_series_mode(enabled):
    session[MASTERS_SERIES_SESSION_KEY] = bool(enabled)
    session.modified = True


def _masters_series_mode_enabled():
    return bool(session.get(MASTERS_SERIES_SESSION_KEY))


def _masters_issue_category_for_redirect(issue_row):
    normalized = _normalize_issue_category_text((issue_row or {}).get('category'))
    if normalized == 'special masters':
        return 'special_masters'
    return 'masters'


def _is_masters_issue(issue_row):
    return _is_masters_issue_alias((issue_row or {}).get('category'))


def _is_masters_publication(publication_row, issue_row=None, issue_cache=None):
    publication = publication_row or {}
    series_key = _clean_text(publication.get('series_key')).lower()
    if series_key in MASTERS_SERIES_KEYS:
        return True

    resolved_issue = issue_row
    if resolved_issue is None:
        issue_id = _parse_int(publication.get('issue_id'))
        if issue_id is not None:
            if issue_cache is not None and issue_id in issue_cache:
                resolved_issue = issue_cache[issue_id]
            else:
                issue_rows = dbc.issues.get(id=issue_id).exec()
                resolved_issue = issue_rows[0] if issue_rows else None
                if issue_cache is not None:
                    issue_cache[issue_id] = resolved_issue

    return _is_masters_issue(resolved_issue)


def _issue_category_candidates(value):
    normalized = _normalize_issue_category_text(value)
    if not normalized:
        return set()

    candidates = {normalized}
    words = normalized.split()

    while words and words[0] in ISSUE_CATEGORY_PREFIXES:
        words = words[1:]
    if words:
        candidates.add(' '.join(words))

    return {item for item in candidates if item}


def _issue_category_lookup_map():
    lookup = dict(ISSUE_CATEGORY_ALIASES)
    try:
        categories = dbc.fix_issue_categories.get().exec()
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        categories = []

    for category in categories:
        alias_raw = _clean_text(category.get('alias'))
        alias_normalized = _normalize_issue_category_text(alias_raw)
        if not alias_normalized:
            continue

        for source in (alias_raw, category.get('name'), category.get('name_uz'), category.get('name_ru')):
            for candidate in _issue_category_candidates(source):
                lookup[candidate] = alias_raw
    return lookup


def _resolve_issue_category_filter(value):
    raw_value = _clean_text(value)
    if not raw_value:
        return ''

    lookup = _issue_category_lookup_map()
    alias_values = {_clean_text(alias) for alias in lookup.values() if _clean_text(alias)}
    candidates = _issue_category_candidates(raw_value)
    for candidate in candidates:
        mapped = lookup.get(candidate)
        if mapped:
            return mapped

    normalized = _normalize_issue_category_text(raw_value)
    has_masters = any(fragment in normalized for fragment in ('magistr', 'magist', 'master', 'magitur'))
    has_phd = any(fragment in normalized for fragment in ('doktor', 'doctor', 'phd'))
    has_teacher = any(fragment in normalized for fragment in ('teacher', 'oqit', "o'qit", 'professor', 'prepod', 'профессор', 'преподав'))
    has_special = any(fragment in normalized for fragment in ('special', 'maxsus', 'спец'))

    if has_special:
        if has_masters:
            for alias in ('special_masters', 'masters_special', 'special-masters', 'masters-special'):
                if alias in alias_values:
                    return alias
        if has_phd:
            for alias in ('special_phd', 'phd_special', 'special-phd', 'phd-special'):
                if alias in alias_values:
                    return alias
        if has_teacher:
            for alias in ('special_teacher', 'teacher_special', 'special-teacher', 'teacher-special'):
                if alias in alias_values:
                    return alias
        return 'special'

    if has_masters:
        return 'masters'
    if has_phd:
        return 'phd'
    if has_teacher:
        return 'teacher'

    return raw_value


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


BOT_USER_AGENT_PATTERN = re.compile(
    r'bot|crawl|spider|slurp|bingpreview|facebookexternalhit|embedly|quora link preview|'
    r'pinterest|vkshare|whatsapp|telegrambot|curl|wget|python-requests|python-urllib|aiohttp|'
    r'httpx|go-http-client|java/|libwww|okhttp|scrapy|headlesschrome|phantomjs|lighthouse|'
    r'pingdom|uptimerobot|statuscake|site24x7|newspaper|feedfetcher|ahrefssiteaudit|semrush',
    re.IGNORECASE,
)

ACTIVITY_SESSION_MARKS_KEY = 'activity_marks'
ACTIVITY_SESSION_MARKS_LIMIT = 80


def _is_bot_request():
    user_agent = _clean_text(request.headers.get('User-Agent'))
    if not user_agent:
        return True
    return bool(BOT_USER_AGENT_PATTERN.search(user_agent))


def _should_count_activity(kind, object_id, user_id=None, ttl_seconds=6 * 60 * 60):
    """Session-based dedup for view/download counters.

    Returns True at most once per (kind, object, visitor) within ttl_seconds.
    Expired entries are pruned and the mark list is capped so the cookie-backed
    session cannot grow without bound.
    """
    if not object_id:
        return False

    marks = session.get(ACTIVITY_SESSION_MARKS_KEY)
    if not isinstance(marks, dict):
        marks = {}
        # Migrate pre-existing view marks from the legacy session key
        legacy_views = session.get('article_views')
        if isinstance(legacy_views, dict):
            for legacy_key, legacy_ts in legacy_views.items():
                marks[f"view:{legacy_key}"] = legacy_ts
            session.pop('article_views', None)

    now_ts = int(time.time())
    marks = {
        mark_key: mark_ts
        for mark_key, mark_ts in marks.items()
        if (_parse_int(mark_ts) or 0) > now_ts - ttl_seconds
    }

    user_id_int = _parse_int(user_id)
    visitor = f"user:{user_id_int}" if user_id_int is not None else 'guest'
    key = f"{kind}:{object_id}:{visitor}"

    should_count = key not in marks
    if should_count:
        marks[key] = now_ts

    if len(marks) > ACTIVITY_SESSION_MARKS_LIMIT:
        oldest_first = sorted(marks.items(), key=lambda item: _parse_int(item[1]) or 0)
        marks = dict(oldest_first[-ACTIVITY_SESSION_MARKS_LIMIT:])

    session[ACTIVITY_SESSION_MARKS_KEY] = marks
    session.modified = True
    return should_count


def _should_increment_article_view(article_id, user_id=None, ttl_seconds=6 * 60 * 60):
    if _is_bot_request():
        return False
    return _should_count_activity('view', article_id, user_id=user_id, ttl_seconds=ttl_seconds)


def _should_increment_download(kind, object_id, user_id=None, ttl_seconds=6 * 60 * 60):
    if _is_bot_request():
        return False
    return _should_count_activity(kind, object_id, user_id=user_id, ttl_seconds=ttl_seconds)


def _normalize_country_name(value):
    return re.sub(r'\s+', ' ', _clean_text(value)).strip()


def _country_iso_for_name(country_name):
    normalized_name = _fold_apostrophes(_normalize_country_name(country_name)).lower()
    if not normalized_name:
        return ''
    return COUNTRY_ISO_LOOKUP.get(normalized_name, '')


def _country_code_to_flag(country_code):
    code = _clean_text(country_code).upper()
    if len(code) != 2 or not code.isalpha():
        return ''
    return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)


def _country_stat_bucket(country_name):
    normalized_name = _normalize_country_name(country_name)
    if not normalized_name:
        return '', '', ''
    iso = _country_iso_for_name(normalized_name)
    if iso:
        bucket_key = iso
        display_name = COUNTRY_DISPLAY_BY_ISO.get(iso) or normalized_name
        return bucket_key, display_name, iso
    # Check if the value is already a bare 2-letter ISO code (e.g. from CDN header)
    if re.match(r'^[A-Za-z]{2}$', normalized_name):
        iso_candidate = normalized_name.lower()
        display_name = COUNTRY_DISPLAY_BY_ISO.get(iso_candidate) or normalized_name.upper()
        return iso_candidate, display_name, iso_candidate
    return normalized_name.lower(), normalized_name, ''


def _resolved_country_bucket(country_name='', country_key=''):
    normalized_key = _clean_text(country_key).lower()
    normalized_country_name = _normalize_country_name(country_name)

    if _is_other_country_bucket_key(normalized_key):
        bucket_key, display_name = _other_country_bucket()
        return bucket_key, display_name, ''

    if normalized_country_name:
        resolved_key, resolved_name, resolved_iso = _country_stat_bucket(normalized_country_name)
        if resolved_key:
            return resolved_key, resolved_name, resolved_iso

    if normalized_key:
        if re.match(r'^[a-z]{2}$', normalized_key):
            display_name = COUNTRY_DISPLAY_BY_ISO.get(normalized_key) or normalized_key.upper()
            return normalized_key, display_name, normalized_key
        return normalized_key, normalized_country_name or _clean_text(country_key), ''

    return '', '', ''


def _other_country_bucket():
    return OTHER_COUNTRY_KEY, OTHER_COUNTRY_NAME


def _is_other_country_bucket_key(value):
    normalized = _clean_text(value).lower()
    return normalized in {UNKNOWN_COUNTRY_KEY, OTHER_COUNTRY_KEY}


@lru_cache(maxsize=1)
def _country_localized_names_by_iso():
    localized = {}
    try:
        countries = dbc.fix_country.get().exec() or []
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return localized

    for country in countries:
        name_en = _clean_text(country.get('name'))
        name_uz = _clean_text(country.get('name_uz'))
        name_ru = _clean_text(country.get('name_ru'))
        iso = ''

        for candidate_name in (name_en, name_uz, name_ru):
            if not candidate_name:
                continue
            iso = _country_iso_for_name(candidate_name)
            if iso:
                break

        if not iso:
            continue

        bucket = localized.setdefault(iso, {})
        if name_en and not bucket.get('en'):
            bucket['en'] = name_en
        if name_uz and not bucket.get('uz'):
            bucket['uz'] = name_uz
        if name_ru and not bucket.get('ru'):
            bucket['ru'] = name_ru

    return localized


def _localized_country_display_name(iso_code, fallback_name='', lang=None):
    language = _clean_text(lang or _current_lang_code()).lower()
    if language not in {'uz', 'ru', 'en'}:
        language = 'en'

    iso = _clean_text(iso_code).lower()
    if iso:
        localized_names = _country_localized_names_by_iso().get(iso) or {}
        localized_name = (
            _clean_text(localized_names.get(language))
            or _clean_text(localized_names.get('en'))
            or _clean_text(localized_names.get('uz'))
            or _clean_text(localized_names.get('ru'))
        )
        if localized_name:
            return localized_name

        known_name = _clean_text(COUNTRY_DISPLAY_BY_ISO.get(iso))
        if known_name:
            return known_name
        return iso.upper()

    return _clean_text(fallback_name)


def _author_workplace(author_row):
    row = author_row or {}
    department = _clean_text(row.get('department'))
    position = _clean_text(row.get('position'))
    return department or position


def _author_country_display_name(country_value, lang=None):
    raw_country = _clean_text(country_value)
    if not raw_country:
        return ''
    bucket_key, fallback_name, iso = _country_stat_bucket(raw_country)
    if not (bucket_key or fallback_name):
        return raw_country
    return _localized_country_display_name(iso, fallback_name=fallback_name or raw_country, lang=lang)


def _normalize_orcid_profile(orcid_value):
    text = _clean_text(orcid_value)
    if not text:
        return '', ''

    match = re.search(r'(\d{4}-\d{4}-\d{4}-[\dXx]{4})', text)
    if match:
        orcid_id = match.group(1).upper()
        return orcid_id, f"https://orcid.org/{orcid_id}"

    digits_only = re.sub(r'[^0-9Xx]', '', text).upper()
    if len(digits_only) == 16:
        orcid_id = f"{digits_only[0:4]}-{digits_only[4:8]}-{digits_only[8:12]}-{digits_only[12:16]}"
        return orcid_id, f"https://orcid.org/{orcid_id}"

    return text, ''


def _normalize_scopus_profile(scopus_value, raw_url=None):
    author_id = _clean_text(scopus_value)
    profile_url = _normalize_external_profile_url(raw_url)
    digits_only = re.sub(r'[^0-9]', '', author_id)
    if digits_only:
        author_id = digits_only
        if not profile_url:
            profile_url = f"https://www.scopus.com/authid/detail.uri?authorId={author_id}"
    return author_id, profile_url


def _normalize_researcherid_profile(researcherid_value, raw_url=None):
    researcherid = _clean_text(researcherid_value).upper()
    profile_url = _normalize_external_profile_url(raw_url)
    if researcherid and not profile_url:
        profile_url = f"https://www.researcherid.com/rid/{researcherid}"
    return researcherid, profile_url


def _editorial_research_interest_items(raw_value):
    text = _clean_text(raw_value)
    if not text:
        return []

    normalized = re.sub(r'\r\n?', '\n', text)
    if '\n' in normalized:
        candidates = [item.strip(" \t-•,;") for item in normalized.split('\n')]
    else:
        candidates = [item.strip(" \t-•") for item in re.split(r'[;,]+', normalized)]

    return [item for item in candidates if item]


def _author_tooltip_payload(author_row, lang=None):
    row = author_row or {}
    name = _clean_text(row.get('name'))
    if not name:
        return None
    orcid_value, orcid_url = _normalize_orcid_profile(row.get('orcid'))
    return {
        'name': name,
        'email': _clean_text(row.get('email')),
        'organization': _clean_text(row.get('organization')),
        'country': _author_country_display_name(row.get('address_country'), lang=lang),
        'workplace': _author_workplace(row),
        'orcid': orcid_value,
        'orcid_url': orcid_url,
    }


def _ensure_activity_events_table():
    if getattr(_ensure_activity_events_table, '_ready', False):
        return True

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_events (
                id BIGSERIAL PRIMARY KEY,
                event_type TEXT NOT NULL,
                publication_id BIGINT NULL,
                issue_id BIGINT NULL,
                user_id BIGINT NULL,
                country_key TEXT NOT NULL,
                country_name TEXT NOT NULL,
                created_at BIGINT NOT NULL
            );
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_events_type_created "
            "ON activity_events(event_type, created_at DESC);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_events_country_key "
            "ON activity_events(country_key);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_events_publication_id "
            "ON activity_events(publication_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_events_issue_id "
            "ON activity_events(issue_id);"
        )
        dbc.conn.commit()
        _ensure_activity_events_table._ready = True
        return True
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to ensure activity_events table")
        return False
    finally:
        if cursor is not None:
            cursor.close()


def _insert_activity_event_rows(cursor, metric_key, country_key, country_name, amount, created_at_ts):
    amount_int = max(0, _parse_int(amount) or 0)
    if amount_int <= 0:
        return 0

    inserted_total = 0
    batch_size = 1000
    while inserted_total < amount_int:
        remaining = amount_int - inserted_total
        chunk_size = min(batch_size, remaining)
        params = [
            (
                metric_key,
                None,
                None,
                None,
                country_key,
                country_name,
                created_at_ts,
            )
            for _ in range(chunk_size)
        ]
        cursor.executemany(
            """
            INSERT INTO activity_events (
                event_type,
                publication_id,
                issue_id,
                user_id,
                country_key,
                country_name,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            params
        )
        inserted_total += chunk_size
    return inserted_total


def _bootstrap_activity_events_from_legacy():
    if getattr(_bootstrap_activity_events_from_legacy, '_done', False):
        return

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute("SELECT pg_advisory_xact_lock(%s);", (ACTIVITY_EVENTS_BOOTSTRAP_LOCK_ID,))
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_event_migrations (
                migration_name TEXT PRIMARY KEY,
                applied_at BIGINT NOT NULL DEFAULT 0
            );
            """
        )
        cursor.execute(
            """
            SELECT applied_at
            FROM activity_event_migrations
            WHERE migration_name = %s
            LIMIT 1
            """,
            (ACTIVITY_EVENTS_BOOTSTRAP_MIGRATION,)
        )
        migration_row = cursor.fetchone()
        if migration_row and (_parse_int(migration_row[0]) or 0) > 0:
            dbc.conn.commit()
            _bootstrap_activity_events_from_legacy._done = True
            return

        if not migration_row:
            cursor.execute(
                """
                INSERT INTO activity_event_migrations (migration_name, applied_at)
                VALUES (%s, 0)
                ON CONFLICT (migration_name) DO NOTHING
                """,
                (ACTIVITY_EVENTS_BOOTSTRAP_MIGRATION,)
            )

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END), 0) AS views_count,
                COALESCE(SUM(CASE WHEN event_type = 'download' THEN 1 ELSE 0 END), 0) AS downloads_count
            FROM activity_events
            """
        )
        existing_totals = cursor.fetchone() or (0, 0)
        existing_views = max(0, _parse_int(existing_totals[0]) or 0)
        existing_downloads = max(0, _parse_int(existing_totals[1]) or 0)

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(stat_views), 0) AS views_count,
                COALESCE(SUM(stat_alt), 0) AS downloads_count
            FROM publications
            """
        )
        publication_totals = cursor.fetchone() or (0, 0)
        publication_views = max(0, _parse_int(publication_totals[0]) or 0)
        publication_downloads = max(0, _parse_int(publication_totals[1]) or 0)

        legacy_rows = []
        cursor.execute("SELECT to_regclass('public.country_activity_stats');")
        legacy_table_row = cursor.fetchone()
        legacy_table_exists = bool(legacy_table_row and legacy_table_row[0])
        if legacy_table_exists:
            cursor.execute(
                """
                SELECT
                    COALESCE(NULLIF(TRIM(country_key), ''), ''),
                    COALESCE(NULLIF(TRIM(country_name), ''), ''),
                    COALESCE(views_count, 0),
                    COALESCE(downloads_count, 0)
                FROM country_activity_stats
                """
            )
            legacy_rows = cursor.fetchall() or []

        now_ts = int(time.time())
        legacy_views_total = 0
        legacy_downloads_total = 0

        for legacy_country_key, legacy_country_name, views_count, downloads_count in legacy_rows:
            key_text = _clean_text(legacy_country_key).lower()
            name_text = _normalize_country_name(legacy_country_name)

            bucket_key, bucket_name, _bucket_iso = _resolved_country_bucket(
                country_name=name_text,
                country_key=key_text,
            )
            if not bucket_key or not bucket_name:
                bucket_key, bucket_name = _other_country_bucket()

            views_int = max(0, _parse_int(views_count) or 0)
            downloads_int = max(0, _parse_int(downloads_count) or 0)
            if views_int > 0:
                _insert_activity_event_rows(
                    cursor,
                    metric_key='view',
                    country_key=bucket_key,
                    country_name=bucket_name,
                    amount=views_int,
                    created_at_ts=now_ts,
                )
                legacy_views_total += views_int
            if downloads_int > 0:
                _insert_activity_event_rows(
                    cursor,
                    metric_key='download',
                    country_key=bucket_key,
                    country_name=bucket_name,
                    amount=downloads_int,
                    created_at_ts=now_ts,
                )
                legacy_downloads_total += downloads_int

        remaining_views = max(0, publication_views - existing_views - legacy_views_total)
        remaining_downloads = max(0, publication_downloads - existing_downloads - legacy_downloads_total)

        if remaining_views > 0:
            other_country_key, other_country_name = _other_country_bucket()
            _insert_activity_event_rows(
                cursor,
                metric_key='view',
                country_key=other_country_key,
                country_name=other_country_name,
                amount=remaining_views,
                created_at_ts=now_ts,
            )
        if remaining_downloads > 0:
            other_country_key, other_country_name = _other_country_bucket()
            _insert_activity_event_rows(
                cursor,
                metric_key='download',
                country_key=other_country_key,
                country_name=other_country_name,
                amount=remaining_downloads,
                created_at_ts=now_ts,
            )

        cursor.execute(
            """
            UPDATE activity_event_migrations
            SET applied_at = %s
            WHERE migration_name = %s
            """,
            (now_ts, ACTIVITY_EVENTS_BOOTSTRAP_MIGRATION)
        )
        dbc.conn.commit()
        _bootstrap_activity_events_from_legacy._done = True
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to bootstrap activity_events from legacy stats")
    finally:
        if cursor is not None:
            cursor.close()


def _ensure_activity_events_ready():
    if not _ensure_activity_events_table():
        return False
    _bootstrap_activity_events_from_legacy()
    return True


def _resolve_user_country_name(user_id):
    user_id_int = _parse_int(user_id)
    if user_id_int is None:
        return ''

    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            """
            SELECT
                COALESCE(
                    NULLIF(TRIM(fc.name), ''),
                    NULLIF(TRIM(fc.name_uz), ''),
                    NULLIF(TRIM(fc.name_ru), '')
                ) AS country_name
            FROM users u
            LEFT JOIN fix_country fc ON fc.id = u.country_id
            WHERE u.id = %s
            LIMIT 1
            """,
            (user_id_int,)
        )
        row = cursor.fetchone()
        country_name = _normalize_country_name(row[0] if row else '')
        if country_name:
            return country_name

        cursor.execute(
            """
            SELECT TRIM(address_country)
            FROM author_profile
            WHERE user_id = %s
              AND address_country IS NOT NULL
              AND TRIM(address_country) != ''
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id_int,)
        )
        fallback_row = cursor.fetchone()
        return _normalize_country_name(fallback_row[0] if fallback_row else '')
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return ''
    finally:
        if cursor is not None:
            cursor.close()


_geoip_reader_cache = {'reader': None, 'failed': False}


def _get_geoip_reader():
    if _geoip_reader_cache['reader'] is not None:
        return _geoip_reader_cache['reader']
    if _geoip_reader_cache['failed'] or maxminddb is None:
        return None
    try:
        _geoip_reader_cache['reader'] = maxminddb.open_database(GEOIP_DB_PATH)
        return _geoip_reader_cache['reader']
    except Exception:
        _geoip_reader_cache['failed'] = True
        logger.warning('GeoIP database is not available at %s — falling back to CDN headers', GEOIP_DB_PATH)
        return None


def _client_ip_address():
    # ProxyFix already rewrites remote_addr from X-Forwarded-For
    candidate = _clean_text(request.remote_addr)
    if candidate:
        return candidate
    forwarded_for = _clean_text(request.headers.get('X-Forwarded-For'))
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return ''


def _geoip_country_iso(ip_address):
    if not ip_address:
        return ''
    reader = _get_geoip_reader()
    if reader is None:
        return ''
    try:
        record = reader.get(ip_address) or {}
        iso_code = ((record.get('country') or {}).get('iso_code') or '').strip().lower()
        if re.match(r'^[a-z]{2}$', iso_code):
            return iso_code
    except Exception:
        pass
    return ''


def _resolve_request_country_name():
    for header_name in (
        'CF-IPCountry',
        'CloudFront-Viewer-Country',
        'X-AppEngine-Country',
        'X-Country-Code',
    ):
        header_value = _clean_text(request.headers.get(header_name)).upper()
        if not header_value or header_value in {'XX', 'ZZ', 'T1'}:
            continue
        if re.match(r'^[A-Z]{2}$', header_value):
            iso_lower = header_value.lower()
            country_name = COUNTRY_DISPLAY_BY_ISO.get(iso_lower)
            if country_name:
                return country_name
            # Country code not in our lookup — still record using ISO code as key
            # so it shows up in stats (without flag, but counted)
            return header_value

    geoip_iso = _geoip_country_iso(_client_ip_address())
    if geoip_iso:
        return COUNTRY_DISPLAY_BY_ISO.get(geoip_iso) or geoip_iso.upper()
    return ''


def _resolve_activity_country_bucket(user_id):
    # Prefer the visitor's actual location (CDN header / GeoIP); fall back to
    # the registered profile country for logged-in users on private networks.
    country_name = _resolve_request_country_name()
    if not country_name:
        country_name = _resolve_user_country_name(user_id)
    if not country_name:
        return _other_country_bucket()

    bucket_key, display_name, _iso = _resolved_country_bucket(country_name=country_name)
    if not bucket_key or not display_name:
        return _other_country_bucket()
    return bucket_key, display_name


def _record_activity_event(user_id, metric, publication_id=None, issue_id=None, amount=1):
    metric_key = _clean_text(metric).lower()
    if metric_key not in ACTIVITY_EVENT_TYPES:
        return
    amount_int = _parse_int(amount) or 0
    if amount_int <= 0:
        return

    if not _ensure_activity_events_ready():
        return

    publication_id_int = _parse_int(publication_id)
    issue_id_int = _parse_int(issue_id)
    user_id_int = _parse_int(user_id)
    country_key, country_name = _resolve_activity_country_bucket(user_id)
    now_ts = int(time.time())
    cursor = None
    try:
        cursor = dbc.conn.cursor()
        params = [
            (
                metric_key,
                publication_id_int,
                issue_id_int,
                user_id_int,
                country_key,
                country_name,
                now_ts,
            )
            for _ in range(amount_int)
        ]
        cursor.executemany(
            """
            INSERT INTO activity_events (
                event_type,
                publication_id,
                issue_id,
                user_id,
                country_key,
                country_name,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            params
        )
        dbc.conn.commit()
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        logger.exception(
            "Failed to record activity event: user_id=%s metric=%s publication_id=%s issue_id=%s amount=%s",
            user_id,
            metric_key,
            publication_id_int,
            issue_id_int,
            amount_int,
        )
    finally:
        if cursor is not None:
            cursor.close()


def _get_site_setting(key, default=''):
    key_text = _clean_text(key)
    if not key_text:
        return default
    try:
        rows = dbc.settings.get(k=key_text).exec()
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return default
    if not rows:
        return default
    value = rows[0].get('v')
    return _clean_text(value) or default


def _get_home_video_url(base_key, lang):
    lang_text = _clean_text(lang).lower()
    localized_values = {}
    for candidate_lang in ('uz', 'ru', 'en'):
        value = _get_site_setting(f"{base_key}_{candidate_lang}")
        if value:
            localized_values[candidate_lang] = value

    if lang_text in localized_values:
        return localized_values[lang_text]

    base_value = _get_site_setting(base_key)
    if base_value:
        return base_value

    for candidate_lang in ('uz', 'ru', 'en'):
        candidate = localized_values.get(candidate_lang)
        if candidate:
            return candidate
    return ''


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


def _get_payment_guide_html(lang):
    lang_text = _clean_text(lang).lower()
    if lang_text in {'uz', 'ru', 'en'}:
        localized = _get_site_setting(f"{PAYMENT_GUIDE_KEY}_{lang_text}")
        if localized:
            return localized
    fallback = _get_site_setting(PAYMENT_GUIDE_KEY)
    if fallback:
        return fallback
    return _default_payment_guide_html(lang_text)


def _youtube_embed_url(raw_url):
    url_text = _clean_text(raw_url)
    if not url_text:
        return ''

    # Support URLs without scheme, e.g. "youtube.com/watch?v=..."
    if url_text.startswith('//'):
        url_text = f"https:{url_text}"
    elif not re.match(r'^[a-z][a-z0-9+\-.]*://', url_text, re.IGNORECASE):
        url_text = f"https://{url_text.lstrip('/')}"

    parsed = urlparse(url_text)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return ''

    host = (parsed.netloc or '').lower()
    if host.startswith('www.'):
        host = host[4:]
    if '.' not in host:
        return ''
    path = (parsed.path or '').strip('/')
    video_id = ''
    is_youtube_host = ('youtube.com' in host) or (host == 'youtu.be') or ('youtube-nocookie.com' in host)

    if host in {'youtu.be'}:
        video_id = path.split('/')[0] if path else ''
    elif 'youtube.com' in host or 'youtube-nocookie.com' in host:
        if path.startswith('watch'):
            params = parse_qs(parsed.query or '')
            video_id = (params.get('v') or [''])[0]
        elif path.startswith('embed/'):
            video_id = path.split('/', 1)[1] if '/' in path else ''
        elif path.startswith('shorts/'):
            video_id = path.split('/', 1)[1] if '/' in path else ''
        elif path.startswith('live/'):
            video_id = path.split('/', 1)[1] if '/' in path else ''
        elif path.startswith('v/'):
            video_id = path.split('/', 1)[1] if '/' in path else ''
        elif path.startswith('attribution_link'):
            params = parse_qs(parsed.query or '')
            encoded_u = (params.get('u') or [''])[0]
            decoded_u = unquote(encoded_u or '')
            nested_params = parse_qs(urlparse(decoded_u).query or '')
            video_id = (nested_params.get('v') or [''])[0]

    video_id = video_id.split('?')[0].split('&')[0].split('/')[0].strip()
    if video_id and re.match(r'^[A-Za-z0-9_-]{6,}$', video_id):
        return f"https://www.youtube.com/embed/{video_id}"

    if is_youtube_host:
        return ''

    # Non-YouTube providers may still be embeddable by iframe.
    return url_text


@lru_cache(maxsize=1)
def _seed_pages_data():
    try:
        from content.pages import load_pages
        return dict(load_pages())
    except Exception as exc:
        logger.warning("Unable to load static pages seed data: %s", exc)
        return {}


def _seed_page_payload(alias):
    page_alias = _clean_text(alias).lower()
    page_data = _seed_pages_data().get(page_alias)
    if not page_data:
        return None

    now_ts = int(time.time())
    return {
        'alias': page_alias,
        'title': page_data.get('title') or '',
        'title_uz': page_data.get('title_uz') or page_data.get('title') or '',
        'title_ru': page_data.get('title_ru') or page_data.get('title') or '',
        'content': page_data.get('content') or '',
        'content_uz': page_data.get('content_uz') or page_data.get('content') or '',
        'content_ru': page_data.get('content_ru') or page_data.get('content') or '',
        'last_update': now_ts,
        'created_at': now_ts,
    }


def _pages_table_columns():
    columns = getattr(dbc, 'columns', None)
    if isinstance(columns, dict):
        page_columns = set(columns.get('pages', []))
        if page_columns:
            return page_columns
    return set()


def _is_blank_text(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _seed_page_backfill_payload(existing_page, seed_payload):
    if not existing_page or not seed_payload:
        return {}

    base_field_candidates = {
        'title': ('title_uz', 'title_ru'),
        'content': ('content_uz', 'content_ru'),
    }
    localized_field_map = {
        'title_uz': 'title',
        'title_ru': 'title',
        'content_uz': 'content',
        'content_ru': 'content',
    }
    update_payload = {}

    for base_field, localized_fields in base_field_candidates.items():
        seed_base_value = seed_payload.get(base_field)
        if _is_blank_text(seed_base_value):
            continue

        current_base_value = existing_page.get(base_field)
        if _is_blank_text(current_base_value):
            update_payload[base_field] = seed_base_value
            continue

        if current_base_value == seed_base_value:
            continue

        for localized_field in localized_fields:
            localized_seed_value = seed_payload.get(localized_field)
            if localized_seed_value and current_base_value == localized_seed_value:
                update_payload[base_field] = seed_base_value
                break

    for localized_field, base_field in localized_field_map.items():
        seed_localized_value = seed_payload.get(localized_field)
        if _is_blank_text(seed_localized_value):
            continue

        current_localized_value = existing_page.get(localized_field)
        if _is_blank_text(current_localized_value):
            update_payload[localized_field] = seed_localized_value
            continue

        current_base_value = existing_page.get(base_field)
        seed_base_value = seed_payload.get(base_field)
        if (
            current_localized_value == current_base_value
            and current_base_value == seed_base_value
            and current_localized_value != seed_localized_value
        ):
            update_payload[localized_field] = seed_localized_value
            continue

        sibling_seed_values = {
            seed_base_value,
            seed_payload.get(f'{base_field}_uz'),
            seed_payload.get(f'{base_field}_ru'),
        }
        sibling_seed_values.discard(None)
        sibling_seed_values.discard(seed_localized_value)
        if current_localized_value in sibling_seed_values:
            update_payload[localized_field] = seed_localized_value

    if update_payload:
        update_payload['last_update'] = seed_payload.get('last_update', int(time.time()))
    return update_payload


def _backfill_seed_page_localizations(page_alias, existing_page):
    seed_payload = _seed_page_payload(page_alias)
    update_payload = _seed_page_backfill_payload(existing_page, seed_payload)
    if not update_payload:
        return existing_page

    page_columns = _pages_table_columns()
    if page_columns:
        update_payload = {k: v for k, v in update_payload.items() if k in page_columns}
    if not update_payload:
        return existing_page

    try:
        dbc.pages.get(alias=page_alias).update(**update_payload).exec()
        refetched = dbc.pages.get(alias=page_alias).exec()
        if refetched:
            return refetched[0]
    except Exception as exc:
        logger.warning("Unable to backfill page alias '%s' localizations: %s", page_alias, exc)
        try:
            dbc.conn.rollback()
        except Exception:
            pass

    return existing_page


def _ensure_seed_page(alias):
    page_alias = _clean_text(alias).lower()
    if not page_alias:
        return None

    try:
        existing = dbc.pages.get(alias=page_alias).exec()
        if existing:
            return _backfill_seed_page_localizations(page_alias, existing[0])
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass

    payload = _seed_page_payload(page_alias)
    if not payload:
        return None

    try:
        page_columns = _pages_table_columns()
        insert_payload = {k: v for k, v in payload.items() if k in page_columns} if page_columns else dict(payload)
        created_rows = dbc.pages.add(**insert_payload).exec()
        if created_rows:
            return created_rows[0]

        refetched = dbc.pages.get(alias=page_alias).exec()
        if refetched:
            return refetched[0]
    except Exception as exc:
        logger.warning("Unable to seed page alias '%s': %s", page_alias, exc)
        try:
            dbc.conn.rollback()
        except Exception:
            pass

    return payload


def _localized_content_field(item, base_field, lang=None, strict=False):
    record = item or {}
    language = _clean_text(lang or _current_lang_code()).lower()
    if language not in {'uz', 'ru', 'en'}:
        language = 'en'

    base_value = record.get(base_field)
    fallback_value = '' if base_value is None else base_value

    if language == 'uz':
        localized_value = record.get(f'{base_field}_uz')
    elif language == 'ru':
        localized_value = record.get(f'{base_field}_ru')
    else:
        localized_value = record.get(f'{base_field}_en') if f'{base_field}_en' in record else base_value

    if strict:
        return '' if localized_value is None else localized_value

    if localized_value in (None, ''):
        return fallback_value
    return localized_value


def _apply_localized_content(item, base_fields, lang=None, strict=False):
    if not item:
        return item
    for base_field in base_fields:
        item[base_field] = _localized_content_field(item, base_field, lang=lang, strict=strict)
    return item


def _editorial_member_type_label(member_type):
    lang = _current_lang_code()
    labels = EDITORIAL_MEMBER_TYPE_LABELS.get(lang, EDITORIAL_MEMBER_TYPE_LABELS['en'])
    key = (member_type or '').strip().lower()
    return labels.get(key, labels.get('editorial_board', 'Editorial Board'))


def _normalize_editorial_member_type(member_type):
    key = (member_type or '').strip().lower()
    return EDITORIAL_MEMBER_TYPE_ALIASES.get(key, 'editorial_board')


def _current_lang_code():
    try:
        lang = (session.get('language') or 'en').strip().lower()
    except RuntimeError:
        return 'en'
    if lang not in {'uz', 'ru', 'en'}:
        return 'en'
    return lang


def _editorial_ui_texts():
    lang = _current_lang_code()
    return EDITORIAL_UI_TEXTS.get(lang, EDITORIAL_UI_TEXTS['en'])


def _editorial_group_theme(group_key):
    theme = EDITORIAL_GROUP_THEMES.get(group_key) or EDITORIAL_GROUP_THEMES.get('editorial_board') or {}
    return {
        'accent': theme.get('accent', '#1666d3'),
        'accent_dark': theme.get('accent_dark', '#104ea3'),
        'soft': theme.get('soft', '#edf5ff'),
        'border': theme.get('border', '#bfd8fb'),
    }


def _editorial_group_role_labels(group_key):
    return {
        'uz': EDITORIAL_MEMBER_TYPE_LABELS.get('uz', {}).get(group_key, ''),
        'en': EDITORIAL_MEMBER_TYPE_LABELS.get('en', {}).get(group_key, ''),
        'ru': EDITORIAL_MEMBER_TYPE_LABELS.get('ru', {}).get(group_key, ''),
    }


def _normalize_external_profile_url(raw_url):
    url_text = _clean_text(raw_url)
    if not url_text:
        return ''

    if url_text.startswith('//'):
        url_text = f"https:{url_text}"
    elif not re.match(r'^[a-z][a-z0-9+\-.]*://', url_text, re.IGNORECASE):
        url_text = f"https://{url_text.lstrip('/')}"

    parsed = urlparse(url_text)
    host = (parsed.netloc or '').strip().lower()
    if parsed.scheme not in {'http', 'https'} or not host or '.' not in host:
        return ''
    return url_text


def _issue_ui_texts():
    lang = _current_lang_code()
    return ISSUE_UI_TEXTS.get(lang, ISSUE_UI_TEXTS['en'])


def _country_stats_ui_texts():
    lang = _current_lang_code()
    return COUNTRY_STATS_UI_TEXTS.get(lang, COUNTRY_STATS_UI_TEXTS['en'])


def _author_tooltip_ui_texts():
    lang = _current_lang_code()
    return AUTHOR_TOOLTIP_UI_TEXTS.get(lang, AUTHOR_TOOLTIP_UI_TEXTS['en'])


def _split_issue_shortinfo_items(text):
    items = []
    buffer = []
    depth = 0

    for char in text:
        if char == '(':
            depth += 1
        elif char == ')' and depth > 0:
            depth -= 1

        if char == ',' and depth == 0:
            item = ''.join(buffer).strip(" \t\r\n,;")
            if item:
                items.append(item)
            buffer = []
            continue

        buffer.append(char)

    last_item = ''.join(buffer).strip(" \t\r\n,;")
    if last_item:
        items.append(last_item)

    return items


def _classify_issue_shortinfo_member(member_name):
    match = re.search(r'\(([^)]+)\)', member_name or '')
    location = (match.group(1).strip().lower() if match else '')

    if not location:
        return 'uzbekistan'

    if any(token in location for token in UZBEKISTAN_LOCATION_TOKENS):
        return 'uzbekistan'

    if any(token in location for token in INTERNATIONAL_LOCATION_TOKENS):
        return 'international'

    return 'international'


def _build_issue_shortinfo(shortinfo):
    parsed = {
        'is_structured': False,
        'heading': '',
        'text': '',
        'items': [],
        'groups': {
            'uzbekistan': [],
            'international': []
        }
    }

    raw_value = '' if shortinfo is None else str(shortinfo)
    normalized = re.sub(r'\s+', ' ', raw_value).strip()
    if not normalized:
        return parsed

    parsed['text'] = normalized

    if ':' not in normalized:
        return parsed

    heading, body = normalized.split(':', 1)
    heading = heading.strip()
    body = body.strip()
    if not heading or not body:
        return parsed

    items = _split_issue_shortinfo_items(body)
    if len(items) < 4:
        return parsed

    items = sorted(items, key=lambda value: value.lower())
    grouped_items = {
        'uzbekistan': [],
        'international': []
    }
    for item in items:
        grouped_items[_classify_issue_shortinfo_member(item)].append(item)

    parsed['is_structured'] = True
    parsed['heading'] = heading
    parsed['text'] = body
    parsed['items'] = items
    parsed['groups'] = grouped_items
    return parsed


def _prepare_editorial_groups(editors):
    grouped = {key: [] for key in EDITORIAL_MEMBER_TYPE_ORDER}
    extra_grouped = {}

    for editor_item in editors or []:
        group_key = _normalize_editorial_member_type(editor_item.get('member_type'))
        if group_key in grouped:
            grouped[group_key].append(editor_item)
        else:
            extra_grouped.setdefault(group_key, []).append(editor_item)

    groups = []
    for group_key in EDITORIAL_MEMBER_TYPE_ORDER:
        members = grouped.get(group_key) or []
        if not members:
            continue
        groups.append({
            'key': group_key,
            'label': _editorial_member_type_label(group_key),
            'labels': _editorial_group_role_labels(group_key),
            'theme': _editorial_group_theme(group_key),
            'is_featured': group_key in FEATURED_EDITORIAL_GROUP_KEYS,
            'members': members,
            'count': len(members)
        })

    for group_key, members in extra_grouped.items():
        if not members:
            continue
        groups.append({
            'key': group_key,
            'label': _editorial_member_type_label(group_key),
            'labels': _editorial_group_role_labels(group_key),
            'theme': _editorial_group_theme(group_key),
            'is_featured': group_key in FEATURED_EDITORIAL_GROUP_KEYS,
            'members': members,
            'count': len(members)
        })

    return groups


def _load_editorial_members():
    table_name = 'editorial_members'
    known_tables = set(getattr(dbc, 'tables', []) or [])

    if table_name not in known_tables:
        try:
            if hasattr(dbc, 'tables'):
                dbc.tables = []
            if hasattr(dbc, '_init_tables'):
                dbc._init_tables()
            if hasattr(dbc, 'columns'):
                dbc.columns = {}
            if hasattr(dbc, 'primary_columns'):
                dbc.primary_columns = {}
            if hasattr(dbc, '_init_columns'):
                dbc._init_columns()
        except Exception:
            return None
        known_tables = set(getattr(dbc, 'tables', []) or [])
        if table_name not in known_tables:
            return None

    try:
        rows = dbc.editorial_members.all().exec()
    except Exception:
        return None

    members = []
    for member in rows:
        is_active = True if member.get('is_active') is None else bool(member.get('is_active'))
        if not is_active:
            continue

        prepared_member = dict(member or {})
        _apply_localized_content(
            prepared_member,
            ('full_name', 'position', 'organization', 'biography', 'country', 'research_interests',
             'academic_degree', 'academic_title')
        )

        full_name = _clean_text(prepared_member.get('full_name'))
        if not full_name:
            full_name = (
                _clean_text(prepared_member.get('full_name'))
                or _clean_text(member.get('full_name'))
                or _clean_text(member.get('full_name_uz'))
                or _clean_text(member.get('full_name_ru'))
            )
        if not full_name:
            continue

        position = (
            _clean_text(prepared_member.get('position'))
            or _clean_text(member.get('position'))
            or _clean_text(member.get('position_uz'))
            or _clean_text(member.get('position_ru'))
        )
        organization = (
            _clean_text(prepared_member.get('organization'))
            or _clean_text(member.get('organization'))
            or _clean_text(member.get('organization_uz'))
            or _clean_text(member.get('organization_ru'))
        )
        biography = (
            _clean_text(prepared_member.get('biography'))
            or _clean_text(member.get('biography'))
            or _clean_text(member.get('biography_uz'))
            or _clean_text(member.get('biography_ru'))
        )
        country = (
            _clean_text(prepared_member.get('country'))
            or _clean_text(member.get('country'))
            or _clean_text(member.get('country_uz'))
            or _clean_text(member.get('country_ru'))
        )
        academic_degree = (
            _clean_text(prepared_member.get('academic_degree'))
            or _clean_text(member.get('academic_degree'))
            or _clean_text(member.get('academic_degree_uz'))
            or _clean_text(member.get('academic_degree_ru'))
        )
        academic_title = (
            _clean_text(prepared_member.get('academic_title'))
            or _clean_text(member.get('academic_title'))
            or _clean_text(member.get('academic_title_uz'))
            or _clean_text(member.get('academic_title_ru'))
        )
        country_code = _clean_text(member.get('country_code')).lower()
        research_interests = (
            _clean_text(prepared_member.get('research_interests'))
            or _clean_text(member.get('research_interests'))
            or _clean_text(member.get('research_interests_uz'))
            or _clean_text(member.get('research_interests_ru'))
        )
        cv_urls = _normalize_public_upload_urls(_localized_content_field(member, 'cv_file'))
        cv_url = cv_urls[0] if cv_urls else None
        google_scholar_url = _normalize_external_profile_url(member.get('google_scholar_url'))
        orcid_value, orcid_url = _normalize_orcid_profile(member.get('orcid'))
        scopus_value, scopus_url = _normalize_scopus_profile(
            member.get('scopus_author_id'),
            member.get('scopus_author_url')
        )
        researcherid_value, researcherid_url = _normalize_researcherid_profile(
            member.get('researcherid'),
            member.get('researcherid_url')
        )
        email_value = _clean_text(member.get('email'))
        _, country_fallback_name, country_iso = _country_stat_bucket(country)
        resolved_country_code = country_code if re.match(r'^[a-z]{2}$', country_code) else country_iso
        country_display = _localized_country_display_name(
            resolved_country_code,
            fallback_name=country_fallback_name or country,
            lang=_current_lang_code()
        )
        research_interest_items = _editorial_research_interest_items(research_interests)

        normalized_type = _normalize_editorial_member_type(member.get('member_type'))
        member_type_label = _editorial_member_type_label(member.get('member_type'))
        prepared_member['full_name'] = full_name
        prepared_member['position'] = position
        prepared_member['organization'] = organization
        prepared_member['biography'] = biography
        prepared_member['country'] = country_display or country
        prepared_member['country_code'] = resolved_country_code
        prepared_member['country_flag'] = _country_code_to_flag(resolved_country_code)
        prepared_member['research_interests'] = research_interests
        prepared_member['research_interests_list'] = research_interest_items
        prepared_member['academic_degree'] = academic_degree
        prepared_member['academic_title'] = academic_title
        prepared_member['member_type'] = normalized_type
        prepared_member['member_type_label'] = member_type_label
        prepared_member['title'] = position or member_type_label
        prepared_member['orcid'] = orcid_value
        prepared_member['orcid_url'] = orcid_url
        prepared_member['scopus'] = scopus_value
        prepared_member['scopus_url'] = scopus_url
        prepared_member['researcherid'] = researcherid_value
        prepared_member['researcherid_url'] = researcherid_url
        prepared_member['email'] = email_value
        prepared_member['cv_urls'] = cv_urls
        prepared_member['cv_url'] = cv_url
        prepared_member['google_scholar_url'] = google_scholar_url
        prepared_member['modal_id'] = f"editorial-member-{_parse_int(member.get('id')) or len(members) + 1}"
        prepared_member['sort_order'] = _parse_int(member.get('sort_order')) or 0
        members.append(prepared_member)

    members = sorted(
        members,
        key=lambda item: (
            _parse_int(item.get('sort_order')) or 0,
            (item.get('full_name') or '').lower(),
            -(_parse_int(item.get('id')) or 0)
        )
    )
    return members


def _load_public_editorial_members():
    editorial_members = _load_editorial_members()
    return editorial_members or []


def _load_home_gallery(lang=None):
    """Active homepage gallery images with a language-resolved title."""
    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            """
            SELECT id, title, title_uz, title_ru, image_path
            FROM home_gallery
            WHERE is_active = TRUE AND COALESCE(image_path, '') <> ''
            ORDER BY sort_order ASC, id ASC
            """
        )
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        dbc.conn.commit()
    except Exception:
        # Table may not exist yet (migration pending) — the card is simply hidden.
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return []
    finally:
        if cursor is not None:
            cursor.close()

    lang = lang or _current_lang_code()
    items = []
    for row in rows:
        if lang == 'uz':
            title = row.get('title_uz') or row.get('title') or row.get('title_ru')
        elif lang == 'ru':
            title = row.get('title_ru') or row.get('title') or row.get('title_uz')
        else:
            title = row.get('title') or row.get('title_uz') or row.get('title_ru')
        items.append({
            'id': row.get('id'),
            'image_path': row.get('image_path'),
            'title': _clean_text(title),
        })
    return items


def _select_featured_editorial_member(editors):
    if not editors:
        return None

    priority_map = {
        key: index
        for index, key in enumerate(EDITORIAL_MEMBER_TYPE_ORDER)
    }
    ranked = sorted(
        editors,
        key=lambda item: (
            priority_map.get(
                _normalize_editorial_member_type(item.get('member_type')),
                len(priority_map)
            ),
            _parse_int(item.get('sort_order')) or 0,
            (item.get('full_name') or '').lower(),
            -(_parse_int(item.get('id')) or 0)
        )
    )
    return ranked[0] if ranked else None


def app__index():
    if 'language' not in session:
        browser_lang = request.accept_languages.best_match(['uz', 'ru', 'en'])
        session['language'] = browser_lang or 'en'
        session.modified = True

    current_lang = _current_lang_code()
    issue_cache_for_masters = {}
    _home_publications_cache = None
    _home_visible_publications_cache = None
    _home_issues_cache = None
    _home_visible_issues_cache = None
    _author_profiles_by_id_cache = None
    _visible_author_ids_cache = None

    def _coerce_int_list(value):
        if value in (None, '', [], (), set()):
            return []
        if isinstance(value, (list, tuple, set)):
            raw_values = list(value)
        else:
            raw_text = _clean_text(value)
            if not raw_text:
                return []
            raw_text = raw_text.strip('{}[]')
            raw_values = [item.strip().strip('"') for item in raw_text.split(',')] if raw_text else []
        parsed_values = []
        for item in raw_values:
            parsed_item = _parse_int(item)
            if parsed_item is not None and parsed_item > 0:
                parsed_values.append(parsed_item)
        return parsed_values

    def _home_publications():
        nonlocal _home_publications_cache
        if _home_publications_cache is None:
            _home_publications_cache = dbc.publications.get().exec() or []
        return _home_publications_cache

    def _home_visible_publications():
        nonlocal _home_visible_publications_cache
        if _home_visible_publications_cache is None:
            _home_visible_publications_cache = [
                row for row in _home_publications()
                if not _is_masters_publication(row, issue_cache=issue_cache_for_masters)
            ]
        return _home_visible_publications_cache

    def _home_issues():
        nonlocal _home_issues_cache
        if _home_issues_cache is None:
            _home_issues_cache = dbc.issues.get().exec() or []
        return _home_issues_cache

    def _home_visible_issues():
        nonlocal _home_visible_issues_cache
        if _home_visible_issues_cache is None:
            _home_visible_issues_cache = [
                issue for issue in _home_issues()
                if not _is_masters_issue(issue)
            ]
        return _home_visible_issues_cache

    def _author_profiles_by_id():
        nonlocal _author_profiles_by_id_cache
        if _author_profiles_by_id_cache is None:
            rows = dbc.author_profile.get().exec() or []
            _author_profiles_by_id_cache = {
                _parse_int(row.get('id')): row
                for row in rows
                if _parse_int(row.get('id')) is not None
            }
        return _author_profiles_by_id_cache

    def _visible_author_ids():
        nonlocal _visible_author_ids_cache
        if _visible_author_ids_cache is None:
            collected = set()
            for publication in _home_visible_publications():
                main_author_id = _parse_int(publication.get('main_author_id'))
                if main_author_id is not None and main_author_id > 0:
                    collected.add(main_author_id)
                for subauthor_id in _coerce_int_list(publication.get('subauthor_ids')):
                    collected.add(subauthor_id)
            _visible_author_ids_cache = collected
        return _visible_author_ids_cache

    def _load_home_publications(order_field, limit=8, sample_size=80):
        visible_rows = list(_home_visible_publications())
        if order_field == 'date_publish':
            visible_rows = sorted(visible_rows, key=_publication_recent_sort_key, reverse=True)
        elif order_field in {'stat_alt', 'stat_views'}:
            visible_rows = sorted(
                visible_rows,
                key=lambda row: (
                    _parse_int(row.get(order_field)) or 0,
                    _publication_recent_sort_key(row),
                ),
                reverse=True,
            )
        elif order_field:
            visible_rows = sorted(
                visible_rows,
                key=lambda row: (_parse_int(row.get(order_field)) or 0, _publication_recent_sort_key(row)),
                reverse=True,
            )
        return visible_rows[:limit]

    latest_publications = _load_home_publications('date_publish')
    downloaded_publications = _load_home_publications('stat_alt')
    popular_publications = _load_home_publications('stat_views')
    news_items = dbc.news.get(type='news', status='published').order_by('published_at').per_page(4).page(1).exec()
    announcements = dbc.news.get(type='announcement', status='published').order_by('published_at').per_page(4).page(1).exec()
    editorial_members = _load_public_editorial_members() or []
    home_video_usage_url = _get_home_video_url('home_video_site_usage_url', current_lang)
    home_video_submission_url = _get_home_video_url('home_video_submission_url', current_lang)
    home_video_usage_embed = _youtube_embed_url(home_video_usage_url)
    home_video_submission_embed = _youtube_embed_url(home_video_submission_url)

    try:
        visible_publications = _home_visible_publications()
        visible_author_ids = _visible_author_ids()
        author_profiles_by_id = _author_profiles_by_id()
        stat_total_publications = len(visible_publications)
        stat_total_authors = sum(1 for author_id in visible_author_ids if author_id in author_profiles_by_id)
        stat_total_issues = len(_home_visible_issues())

        stat_total_views = 0
        stat_total_downloads = 0
        if _ensure_activity_events_ready():
            cursor = None
            try:
                cursor = dbc.conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        COALESCE(SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END), 0) AS views_count,
                        COALESCE(SUM(CASE WHEN event_type = 'download' THEN 1 ELSE 0 END), 0) AS downloads_count
                    FROM activity_events
                    """
                )
                totals_row = cursor.fetchone() or (0, 0)
                stat_total_views = _parse_int(totals_row[0]) or 0
                stat_total_downloads = _parse_int(totals_row[1]) or 0
            finally:
                if cursor is not None:
                    cursor.close()
        else:
            stat_total_views = sum(max(0, _parse_int(pub.get('stat_views')) or 0) for pub in visible_publications)
            stat_total_downloads = sum(max(0, _parse_int(pub.get('stat_alt')) or 0) for pub in visible_publications)
    except Exception:
        stat_total_publications = 0
        stat_total_views = 0
        stat_total_downloads = 0
        stat_total_authors = 0
        stat_total_issues = 0

    journal_stats = {
        'publications': int(stat_total_publications),
        'views': int(stat_total_views),
        'downloads': int(stat_total_downloads),
        'authors': int(stat_total_authors),
        'issues': int(stat_total_issues),
    }

    country_stats = []
    country_stats_top = []
    country_stats_ui = _country_stats_ui_texts()
    author_tooltip_ui = _author_tooltip_ui_texts()
    try:
        # Use ALL author profiles (not just visible-publication authors) so every
        # registered author's country contributes to the global-reach map.
        author_rows_map = {}
        for profile in (dbc.author_profile.get().exec() or []):
            country_name = _normalize_country_name(profile.get('address_country'))
            if not country_name:
                continue
            author_rows_map[country_name] = author_rows_map.get(country_name, 0) + 1
        author_rows = list(author_rows_map.items())

        activity_rows = []
        if _ensure_activity_events_ready():
            cursor = dbc.conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT
                        country_key,
                        country_name,
                        COALESCE(SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END), 0) AS views_count,
                        COALESCE(SUM(CASE WHEN event_type = 'download' THEN 1 ELSE 0 END), 0) AS downloads_count
                    FROM activity_events
                    GROUP BY country_key, country_name
                    """
                )
                activity_rows = cursor.fetchall() or []
            finally:
                cursor.close()

        aggregated = {}

        def _merge_country_row(country_name='', country_key='', authors=0, views=0, downloads=0):
            bucket_key, display_name, iso = _resolved_country_bucket(
                country_name=country_name,
                country_key=country_key,
            )

            if not bucket_key:
                return

            if bucket_key not in aggregated:
                aggregated[bucket_key] = {
                    'country_key': bucket_key,
                    'name': display_name,
                    'authors': 0,
                    'count': 0,
                    'views': 0,
                    'downloads': 0,
                    'iso': iso,
                }

            item = aggregated[bucket_key]
            item['authors'] += max(0, _parse_int(authors) or 0)
            item['views'] += max(0, _parse_int(views) or 0)
            item['downloads'] += max(0, _parse_int(downloads) or 0)
            if iso and not item.get('iso'):
                item['iso'] = iso
                item['name'] = COUNTRY_DISPLAY_BY_ISO.get(iso) or display_name

        for country_name, authors_cnt in author_rows:
            _merge_country_row(country_name=country_name, authors=authors_cnt)

        for country_key, country_name, views_cnt, downloads_cnt in activity_rows:
            _merge_country_row(
                country_name=country_name,
                country_key=country_key,
                views=views_cnt,
                downloads=downloads_cnt,
            )

        for item in aggregated.values():
            a = max(0, _parse_int(item.get('authors')) or 0)
            v = max(0, _parse_int(item.get('views')) or 0)
            d = max(0, _parse_int(item.get('downloads')) or 0)
            item['authors'] = a
            item['views'] = v
            item['downloads'] = d
            item['count'] = v + d
            item['total'] = a + v + d

        real_items = [
            item
            for item in aggregated.values()
            if item['total'] > 0
            and not _is_other_country_bucket_key(item.get('country_key'))
        ]
        sorted_stats = sorted(
            real_items,
            key=lambda item: (
                -item['total'],
                -item['count'],
                -item['authors'],
                (item.get('name') or '').lower(),
            )
        )
        max_total = max((item['total'] for item in sorted_stats), default=1)
        max_total = max(max_total, 1)

        for item in sorted_stats:
            item['pct'] = round(item['total'] / max_total * 100)
            if item.get('iso'):
                item['name'] = _localized_country_display_name(
                    item.get('iso'),
                    fallback_name=item.get('name'),
                    lang=current_lang,
                )

        country_stats = sorted_stats
        top10 = sorted_stats[:10]
        rest = sorted_stats[10:]
        if rest:
            _ui = country_stats_ui
            other_row = {
                'country_key': 'other',
                'name': _ui.get('unknown_country', 'Other countries'),
                'iso': '',
                'authors': sum(r['authors'] for r in rest),
                'views': sum(r['views'] for r in rest),
                'downloads': sum(r['downloads'] for r in rest),
                'count': sum(r['count'] for r in rest),
                'total': sum(r['total'] for r in rest),
                'pct': 0,
                'is_other': True,
            }
            other_row['pct'] = round(other_row['total'] / max_total * 100) if max_total > 0 else 0
            country_stats_top = top10 + [other_row]
        else:
            country_stats_top = top10
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        country_stats = []
        country_stats_top = []
    author_profile_cache = {}

    def get_author_profile(author_id):
        if not author_id:
            return None
        if author_id not in author_profile_cache:
            author_rows = dbc.author_profile.get(id=author_id).exec()
            if author_rows:
                author_profile_cache[author_id] = _author_tooltip_payload(
                    translate(author_rows[0]),
                    lang=current_lang,
                )
            else:
                author_profile_cache[author_id] = None
        return author_profile_cache[author_id]

    def enrich_home_publication(pub):
        translate(pub)
        _apply_localized_content(pub, ('title', 'abstract', 'keywords'), lang=current_lang)
        pub['page_range'] = _clean_text(pub.get('page_range'))
        if pub.get('doi') and not pub.get('doi_link'):
            pub['doi_link'] = f"https://doi.org/{pub.get('doi')}"

        author_profiles = []
        main_author_profile = get_author_profile(pub.get('main_author_id'))
        if main_author_profile:
            author_profiles.append(main_author_profile)

        subauthor_ids = pub.get('subauthor_ids') or pub.get('sub_author_ids') or []
        for author_id in subauthor_ids:
            author_profile = get_author_profile(author_id)
            if author_profile:
                author_profiles.append(author_profile)

        pub['author_profiles'] = author_profiles
        pub['main_author_name'] = author_profiles[0]['name'] if author_profiles else ''
        pub['subauthor_names'] = [author_item.get('name') for author_item in author_profiles[1:] if author_item.get('name')]

        issue_id = _parse_int(pub.get('issue_id'))
        if issue_id is not None:
            if issue_id not in issue_cache_for_masters:
                issue_rows = dbc.issues.get(id=issue_id).exec()
                issue_cache_for_masters[issue_id] = issue_rows[0] if issue_rows else None
            issue = issue_cache_for_masters.get(issue_id)
            if issue:
                translated_issue = translate(dict(issue))
                pub['issue'] = _apply_localized_content(translated_issue, ('title', 'shortinfo', 'price'), lang=current_lang)

    for publications in [latest_publications, downloaded_publications, popular_publications]:
        for pub in publications:
            enrich_home_publication(pub)

    # Recent issues for sidebar quick navigation: only the latest few are
    # shown here — the full list lives on the Issues page.
    recent_issues = []
    try:
        recent_issues_rows = dbc.issues.get().exec() or []
        visible_issues = [
            issue for issue in recent_issues_rows
            if not _is_masters_issue(issue)
        ]
        visible_issues = sorted(
            visible_issues,
            key=lambda issue: (
                _parse_int(issue.get('year')) or 0,
                _parse_int(issue.get('vol_no')) or 0,
                _parse_int(issue.get('issue_no')) or 0,
                _parse_int(issue.get('created_at')) or 0,
                _parse_int(issue.get('id')) or 0,
            ),
            reverse=True,
        )
        recent_issues = visible_issues[:3]
        for iss in recent_issues:
            try:
                translate(iss)
                _apply_localized_content(iss, ('title', 'shortinfo', 'price'), lang=current_lang)
            except Exception:
                pass
    except Exception:
        recent_issues = []

    for item in news_items + announcements:
        translate(item)

    return render_template(
        'index.html',
        latest_publications=latest_publications,
        downloaded_publications=downloaded_publications,
        popular_publications=popular_publications,
        news_items=news_items,
        announcements=announcements,
        editorial_members=editorial_members,
        home_gallery=_load_home_gallery(current_lang),
        home_video_usage_embed=home_video_usage_embed,
        home_video_submission_embed=home_video_submission_embed,
        journal_stats=journal_stats,
        country_stats=country_stats,
        country_stats_top=country_stats_top,
        country_stats_ui=country_stats_ui,
        author_tooltip_ui=author_tooltip_ui,
        recent_issues=recent_issues,
    )


def app__editorial():
    editorial_ui = _editorial_ui_texts()
    prepared_editors = _load_public_editorial_members()
    editor_groups = _prepare_editorial_groups(prepared_editors)
    featured_editor = _select_featured_editorial_member(prepared_editors)
    featured_group = None
    if featured_editor:
        featured_key = _normalize_editorial_member_type(featured_editor.get('member_type'))
        for group in editor_groups:
            if group.get('key') == featured_key:
                featured_group = group
                break
    leadership_groups = [group for group in editor_groups if group.get('is_featured')]
    board_groups = [group for group in editor_groups if not group.get('is_featured')]
    return render_template(
        'mainweb/editorial.html',
        editors=prepared_editors,
        editor_groups=editor_groups,
        featured_editor=featured_editor,
        featured_group=featured_group,
        leadership_groups=leadership_groups,
        board_groups=board_groups,
        total_editors=len(prepared_editors),
        total_groups=len(editor_groups),
        editorial_ui=editorial_ui
    )


_SOCIAL_ICONS = {
    'telegram': 'tabler:brand-telegram',
    'instagram': 'tabler:brand-instagram',
    'facebook': 'tabler:brand-facebook',
    'twitter': 'tabler:brand-x',
    'youtube': 'tabler:brand-youtube',
    'linkedin': 'tabler:brand-linkedin',
    'website': 'tabler:world-www',
    'other': 'tabler:link',
}
_SOCIAL_NAMES = {
    'telegram': 'Telegram Messenger',
    'instagram': 'Instagram',
    'facebook': 'Facebook',
    'twitter': 'Twitter / X',
    'youtube': 'YouTube',
    'linkedin': 'LinkedIn',
    'website': 'Website',
}


def _fetch_contact_social_links():
    social_links = []
    try:
        sl_rows = dbc.settings.get(k='contact_social_links').exec()
        if sl_rows and sl_rows[0].get('v'):
            data = json.loads(sl_rows[0]['v'])
            if isinstance(data, list):
                social_links = data
        if not social_links:
            tg_rows = dbc.settings.get(k='contact_telegram').exec()
            if tg_rows and tg_rows[0].get('v'):
                social_links = [{'platform': 'telegram', 'url': tg_rows[0]['v'].strip()}]
    except Exception:
        pass
    return social_links


# Localized heading for the download section
_AUTHOR_GUIDELINE_DOWNLOAD_HEADING = {
    'uz': 'Hujjatlarni yuklab olish',
    'ru': 'Скачать документы',
    'en': 'Download Documents',
}


def _build_attachments_section(attachments, lang):
    """Build HTML section for page attachments (files)."""
    if not attachments:
        return ''

    heading = _AUTHOR_GUIDELINE_DOWNLOAD_HEADING.get(lang, _AUTHOR_GUIDELINE_DOWNLOAD_HEADING['en'])

    items_html = ''
    for file_info in attachments:
        file_name = escape(file_info.get('name', 'Download'))
        file_path = file_info.get('path', '')

        # Normalize URL
        normalized_url = _normalize_public_upload_url(file_path) or file_path
        safe_url = escape(normalized_url)

        # Determine icon based on file extension
        ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ''
        icon_map = {
            'pdf': 'tabler:file-type-pdf',
            'doc': 'tabler:file-type-doc',
            'docx': 'tabler:file-type-docx',
            'txt': 'tabler:file-text',
            'jpg': 'tabler:photo',
            'jpeg': 'tabler:photo',
            'png': 'tabler:photo',
        }
        icon = icon_map.get(ext, 'tabler:file')

        items_html += (
            f'<div class="mb-2">'
            f'<a href="{safe_url}" target="_blank" class="inline-flex items-center gap-2 text-fmmain hover:underline font-medium">'
            f'<iconify-icon icon="{icon}" class="text-lg"></iconify-icon> {file_name}'
            f'</a>'
            f'</div>'
        )

    if not items_html:
        return ''

    return (
        '\n<div class="mt-8 p-6 bg-gray-50 border border-gray-200 rounded-lg">'
        f'<h3 class="text-xl font-bold mb-4 text-gray-900">{escape(heading)}</h3>'
        f'<div class="space-y-2">{items_html}</div>'
        '</div>'
    )


def _render_journal_info_page():
    page = _ensure_seed_page('journal_info')
    if not page:
        flash('Page not found', 'error')
        return redirect(url_for('app__index'))

    lang = _current_lang_code()
    page = _apply_localized_content(page, ('title', 'content'), lang=lang)

    social_links = _fetch_contact_social_links()
    if social_links:
        items_html = ''
        for sl in social_links:
            url = (sl.get('url') or '').strip()
            if not url:
                continue
            platform = sl.get('platform', 'other')
            if not url.startswith('http'):
                if platform == 'telegram':
                    url = 'https://t.me/' + url.lstrip('@')
            icon = _SOCIAL_ICONS.get(platform, 'tabler:link')
            name = _SOCIAL_NAMES.get(platform, platform.capitalize())
            items_html += (
                f'<div class="flex items-center gap-3">'
                f'<iconify-icon icon="{icon}" class="text-fmmain text-xl flex-shrink-0"></iconify-icon>'
                f'<a href="{url}" target="_blank" rel="noopener" class="text-fmmain hover:underline break-all">'
                f'{name} &#8211; {url}</a></div>'
            )
        if items_html:
            official_pages_heading = {
                'uz': 'Jurnalning rasmiy sahifalari',
                'ru': 'Официальные страницы журнала',
                'en': 'Official Pages of the Journal',
            }.get(lang, 'Official Pages of the Journal')
            social_section = (
                '\n<section>'
                f'<h4 class="text-lg font-semibold mb-3">{official_pages_heading}</h4>'
                '<div class="space-y-3">' + items_html + '</div>'
                '</section>'
            )
            page['content'] = page['content'].rstrip() + social_section

    return render_template('mainweb/page.html', page=page, show_toc=True)


def _render_news_calls_page():
    """Dynamic 'News & Calls' page: published news + announcements as cards."""
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    per_page = 12

    items = dbc.news.get(status='published').exec() or []
    items.sort(key=lambda row: _parse_int(row.get('published_at')) or 0, reverse=True)
    for item in items:
        translate(item)

    total_results = len(items)
    total_pages = max((total_results + per_page - 1) // per_page, 1)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    page_items = items[start:start + per_page]
    pagination = _SimplePagination(page, total_pages)

    return render_template(
        'mainweb/news_calls.html',
        items=page_items,
        pagination=pagination,
    )


def app__page_alias(alias):
    page_alias = _clean_text(alias).lower()

    if page_alias == 'payment_guide':
        return redirect(url_for('app__payment_guide'))

    if page_alias == 'news_calls':
        return _render_news_calls_page()

    if page_alias == 'journal_info':
        return _render_journal_info_page()

    redirected = PAGE_ALIAS_REDIRECTS.get(page_alias)
    if redirected:
        endpoint, endpoint_kwargs = redirected
        return redirect(url_for(endpoint, **endpoint_kwargs))

    page = _ensure_seed_page(page_alias)
    if not page:
        flash('Page not found', 'error')
        return redirect(url_for('app__index'))

    lang = _current_lang_code()
    page = _apply_localized_content(page, ('title', 'content'), lang=lang)

    if page_alias == 'submission_guidelines':
        # Load attachments from database and display them
        attachments_field = f'attachments_{lang}'
        attachments_json = page.get(attachments_field) or '[]'
        try:
            attachments = json.loads(attachments_json)
            if attachments:
                download_section = _build_attachments_section(attachments, lang)
                page['content'] = (page.get('content') or '').rstrip() + download_section
        except (json.JSONDecodeError, Exception):
            pass  # If JSON parsing fails, just skip attachments

    no_toc_aliases = {'author_instructions'}
    return render_template('mainweb/page.html', page=page, show_toc=(page_alias not in no_toc_aliases))


def app__payment_guide():
    lang = _current_lang_code()
    guide_html = _get_payment_guide_html(lang)
    page = {
        'title': t('payment_guide'),
        'content': guide_html
    }
    return render_template('mainweb/page.html', page=page)


def app__contact():
    current_lang = _current_lang_code()
    if request.method == 'POST':
        name = sanitize_input(request.form.get('name'))
        email = sanitize_input(request.form.get('email')).lower()
        subject = sanitize_input(request.form.get('subject'))
        message = sanitize_input(request.form.get('message'))
        privacy_policy = request.form.get('privacy_policy')

        if not all([name, email, subject, message, privacy_policy]):
            flash('All fields are required', 'error')
            return redirect(url_for('app__contact'))

        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('app__contact'))

        if name and email and subject and message:
            admin_subject = subject if len(subject) <= 120 else f"{subject[:117]}..."
            admin_title = _multilingual_email_text(
                f'Yangi murojaat: {admin_subject}',
                f'Новое обращение: {admin_subject}',
                f'New contact request: {admin_subject}',
            )
            admin_intro = _multilingual_email_text(
                'Saytdagi contact form orqali yangi xabar yuborildi.',
                'Через контактную форму сайта было отправлено новое сообщение.',
                'A new message was sent through the website contact form.',
                include_labels=True,
            )
            try:
                send_notification_email(
                    recipients=settings.MAIL_CONTACT_RECIPIENTS,
                    subject=admin_title,
                    intro=admin_intro,
                    details=[
                        (
                            _multilingual_email_text('Ism', 'Имя', 'Name', separator=' / '),
                            name,
                        ),
                        (
                            _multilingual_email_text('Email', 'Email', 'Email', separator=' / '),
                            email,
                        ),
                        (
                            _multilingual_email_text('Mavzu', 'Тема', 'Subject', separator=' / '),
                            subject,
                        ),
                    ],
                    body_lines=[_multilingual_email_text(message, message, message, include_labels=True)],
                    reply_to=email,
                    fail_silently=False,
                )
            except Exception:
                current_app.logger.exception('Failed to deliver contact form email for %s', email)
                flash('Message could not be delivered right now. Please try again later.', 'error')
                return redirect(url_for('app__contact'))

            user_subject = _multilingual_email_text(
                "Murojaatingiz qabul qilindi",
                'Ваше сообщение получено',
                'We received your message',
            )
            user_intro = _multilingual_email_text(
                "Murojaatingiz Philology Matters jamoasiga yuborildi.",
                'Ваше сообщение было отправлено команде Philology Matters.',
                'Your message has been delivered to the Philology Matters team.',
                include_labels=True,
            )
            user_body = _multilingual_email_text(
                "Jamoamiz tez orada siz bilan bog'lanadi.",
                'Наша команда скоро свяжется с вами.',
                'Our team will get back to you soon.',
                include_labels=True,
            )
            send_notification_email(
                recipients=[email],
                subject=user_subject,
                intro=user_intro,
                details=[
                    (
                        _multilingual_email_text('Mavzu', 'Тема', 'Subject', separator=' / '),
                        subject,
                    ),
                ],
                body_lines=[user_body],
                cta_url=url_for('app__contact'),
                cta_label=_multilingual_email_text(
                    "Saytni ochish",
                    'Открыть сайт',
                    'Open website',
                    separator=' / ',
                ),
                fail_silently=True,
            )
            flash('Message sent successfully', 'success')
        else:
            flash('All fields are required', 'error')
        return redirect(url_for('app__contact'))

    contact_persons = []
    contact_social_links = []
    try:
        rows = dbc.settings.get(k='contact_persons').exec()
        if rows and rows[0].get('v'):
            data = json.loads(rows[0]['v'])
            if isinstance(data, list):
                contact_persons = data
    except Exception:
        pass
    try:
        sl_rows = dbc.settings.get(k='contact_social_links').exec()
        if sl_rows and sl_rows[0].get('v'):
            data = json.loads(sl_rows[0]['v'])
            if isinstance(data, list):
                contact_social_links = data
        elif not contact_social_links:
            tg_rows = dbc.settings.get(k='contact_telegram').exec()
            if tg_rows and tg_rows[0].get('v'):
                contact_social_links = [{'platform': 'telegram', 'url': tg_rows[0]['v'].strip()}]
    except Exception:
        pass

    _SOCIAL_ICONS = {
        'telegram': 'tabler:brand-telegram',
        'instagram': 'tabler:brand-instagram',
        'facebook': 'tabler:brand-facebook',
        'twitter': 'tabler:brand-x',
        'youtube': 'tabler:brand-youtube',
        'linkedin': 'tabler:brand-linkedin',
        'website': 'tabler:world-www',
        'other': 'tabler:link',
    }
    for sl in contact_social_links:
        sl['icon'] = _SOCIAL_ICONS.get(sl.get('platform', ''), 'tabler:link')

    def _person_localized(person, field):
        if current_lang == 'uz':
            val = person.get(f'{field}_uz') or person.get(field, '')
        elif current_lang == 'ru':
            val = person.get(f'{field}_ru') or person.get(field, '')
        else:
            val = person.get(field, '')
        return val or ''

    for p in contact_persons:
        p['display_name'] = _person_localized(p, 'name')
        p['display_position'] = _person_localized(p, 'position')

    return render_template('mainweb/contact.html',
                           contact_persons=contact_persons,
                           contact_social_links=contact_social_links)


def app__articles():
    current_lang = _current_lang_code()
    metadata_labels = publication_metadata_field_labels(current_lang)
    author_tooltip_ui = _author_tooltip_ui_texts()
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    per_page = 20

    search_query = request.args.get('search', '').strip()
    issue_filter = request.args.get('issue', '').strip()
    volume_filter = request.args.get('volume', '')
    year_filter = request.args.get('year', '').strip()
    access_filter = request.args.get('access', '').strip().lower()
    sort_by = request.args.get('sort', 'newest').strip().lower()

    valid_sort_options = {'newest', 'oldest', 'title_az', 'title_za', 'most_viewed', 'most_cited'}
    if sort_by not in valid_sort_options:
        sort_by = 'newest'

    query = dbc.publications.get()
    issue_cache_for_masters = {}

    parsed_issue_id = _parse_int(issue_filter)
    if issue_filter and parsed_issue_id is not None:
        selected_issue_rows = dbc.issues.get(id=parsed_issue_id).exec()
        selected_issue = selected_issue_rows[0] if selected_issue_rows else None
        issue_cache_for_masters[parsed_issue_id] = selected_issue
        if selected_issue and not _is_masters_issue(selected_issue):
            query = query.equal(issue_id=parsed_issue_id)
        else:
            query = query.get(id=-1)
    elif issue_filter:
        issue_filter = ''

    parsed_year = _parse_int(year_filter)
    if year_filter and parsed_year is not None:
        year_issues = dbc.issues.get(year=parsed_year).exec()
        if year_issues:
            visible_year_issues = [
                issue for issue in year_issues
                if not _is_masters_issue(issue)
            ]
            issue_ids = [issue['id'] for issue in visible_year_issues]
            if issue_ids:
                query = query.any(issue_id=issue_ids)
            else:
                query = query.get(id=-1)
        else:
            query = query.get(id=-1)
    elif year_filter:
        year_filter = ''

    if volume_filter:
        volume_issues = dbc.issues.get(vol_no=volume_filter).exec()
        if volume_issues:
            visible_volume_issues = [
                issue for issue in volume_issues
                if not _is_masters_issue(issue)
            ]
            issue_ids = [issue['id'] for issue in visible_volume_issues]
            if issue_ids:
                query = query.any(issue_id=issue_ids)
            else:
                query = query.get(id=-1)
        else:
            query = query.get(id=-1)

    if access_filter:
        if access_filter == 'open':
            query = query.equal(is_paid=False)
        elif access_filter == 'paid':
            query = query.equal(is_paid=True, subscription_enable=False)
        elif access_filter == 'subscription':
            query = query.equal(subscription_enable=True)
        else:
            access_filter = ''

    publications = query.exec()
    for publication in publications:
        translate(publication)
        _apply_localized_content(publication, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)
    publications = [
        publication for publication in publications
        if not _is_masters_publication(publication, issue_cache=issue_cache_for_masters)
    ]

    author_profile_cache = {}
    issue_cache = {}
    references_count_cache = {}
    citations_count_cache = {}

    def get_author_profile(author_id):
        if not author_id:
            return None
        if author_id not in author_profile_cache:
            author_row = dbc.author_profile.get(id=author_id).exec()
            if author_row:
                author_profile_cache[author_id] = _author_tooltip_payload(
                    translate(author_row[0]),
                    lang=current_lang,
                )
            else:
                author_profile_cache[author_id] = None
        return author_profile_cache[author_id]

    def get_author_name(author_id):
        author_profile = get_author_profile(author_id)
        if author_profile:
            return author_profile.get('name')
        return None

    def get_issue(issue_id):
        if not issue_id:
            return None
        if issue_id not in issue_cache:
            issue_row = dbc.issues.get(id=issue_id).exec()
            if issue_row:
                translated_issue = translate(issue_row[0])
                issue_cache[issue_id] = _apply_localized_content(translated_issue, ('title', 'shortinfo', 'price'), lang=current_lang)
            else:
                issue_cache[issue_id] = None
        return issue_cache[issue_id]

    def get_references_count(publication_id):
        if publication_id not in references_count_cache:
            references_count_cache[publication_id] = len(dbc.publication_refs.get(publication_id=publication_id).exec())
        return references_count_cache[publication_id]

    def get_citations_count(publication_id):
        if publication_id not in citations_count_cache:
            citations_count_cache[publication_id] = len(dbc.publication_citations.get(publication_id=publication_id).exec())
        return citations_count_cache[publication_id]

    if search_query:
        filtered_publications = []
        lowered_search = search_query.lower()
        for pub in publications:
            search_fields = [
                (pub.get('title') or '').lower(),
                (pub.get('abstract') or '').lower(),
                ' '.join(pub.get('keywords', []) or []).lower()
            ]
            author_names = []
            if pub['main_author_id']:
                main_author_name = get_author_name(pub['main_author_id'])
                if main_author_name:
                    author_names.append(main_author_name.lower())

            co_author_ids = pub.get('subauthor_ids') or pub.get('sub_author_ids') or []
            for author_id in co_author_ids:
                co_author_name = get_author_name(author_id)
                if co_author_name:
                    author_names.append(co_author_name.lower())

            search_fields.extend(author_names)
            if any(lowered_search in field for field in search_fields):
                filtered_publications.append(pub)
        publications = filtered_publications

    if sort_by == 'newest':
        publications = sorted(publications, key=_publication_recent_sort_key, reverse=True)
    elif sort_by == 'oldest':
        publications = sorted(publications, key=_publication_recent_sort_key)
    elif sort_by == 'title_az':
        publications = sorted(publications, key=lambda x: (x.get('title') or '').lower())
    elif sort_by == 'title_za':
        publications = sorted(publications, key=lambda x: (x.get('title') or '').lower(), reverse=True)
    elif sort_by == 'most_viewed':
        publications = sorted(publications, key=lambda x: _parse_int(x.get('stat_views')) or 0, reverse=True)
    elif sort_by == 'most_cited':
        publications = sorted(publications, key=lambda x: get_citations_count(x['id']), reverse=True)

    total_results = len(publications)
    total_pages = max((total_results + per_page - 1) // per_page, 1)
    page = min(page, total_pages)
    pagination_start = max(1, page - 2)
    pagination_end = min(total_pages, page + 2)
    pagination_pages = list(range(pagination_start, pagination_end + 1))
    start = (page - 1) * per_page
    end = start + per_page
    publications = publications[start:end]

    processed_publications = []
    for pub in publications:
        author_profiles = []
        if pub['main_author_id']:
            main_author_profile = get_author_profile(pub['main_author_id'])
            if main_author_profile:
                author_profiles.append(main_author_profile)

        co_author_ids = pub.get('subauthor_ids') or pub.get('sub_author_ids') or []
        for author_id in co_author_ids:
            co_author_profile = get_author_profile(author_id)
            if co_author_profile:
                author_profiles.append(co_author_profile)

        issue = get_issue(pub['issue_id']) if pub.get('issue_id') else None
        references_count = get_references_count(pub['id'])
        citations_count = get_citations_count(pub['id'])
        doi_value = _clean_text(pub.get('doi'))
        doi_link = _clean_text(pub.get('doi_link'))
        if doi_value and not doi_link:
            doi_link = f"https://doi.org/{doi_value}"

        processed_publications.append({
            'id': pub['id'],
            'title': pub['title'],
            'abstract': pub['abstract'],
            'authors': ', '.join(author_item.get('name') for author_item in author_profiles if author_item.get('name')),
            'author_profiles': author_profiles,
            'date_publish': pub['date_publish'],
            'stat_views': pub.get('stat_views', 0),
            'stat_crossref': pub.get('stat_crossref', 0),
            'references_count': references_count,
            'citations_count': citations_count,
            'doi': doi_value,
            'doi_link': doi_link,
            'keywords': pub.get('keywords', []),
            'is_paid': pub.get('is_paid', False),
            'subscription_enable': pub.get('subscription_enable', False),
            'page_range': _clean_text(pub.get('page_range')),
            'issue': issue,
            'author_position_display': publication_metadata_label('author_position_key', pub.get('author_position_key'), current_lang),
            'academic_title_display': publication_metadata_label('academic_title_key', pub.get('academic_title_key'), current_lang),
            'academic_degree_display': publication_metadata_label('academic_degree_key', pub.get('academic_degree_key'), current_lang),
            'series_display': publication_metadata_label('series_key', pub.get('series_key'), current_lang),
            'section_display': publication_metadata_label('section_key', pub.get('section_key'), current_lang),
        })

    all_issues = dbc.issues.get().order_by('year').exec()
    all_issues = [issue for issue in all_issues if not _is_masters_issue(issue)]
    for issue in all_issues:
        translate(issue)
        _apply_localized_content(issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    all_volumes = sorted(list(set([issue['vol_no'] for issue in all_issues if issue['vol_no']])), reverse=True)
    all_years = sorted(list(set([issue['year'] for issue in all_issues if issue['year']])), reverse=True)

    return render_template('mainweb/articles.html',
                         publications=processed_publications,
                         metadata_labels=metadata_labels,
                         all_issues=all_issues,
                         all_volumes=all_volumes,
                         all_years=all_years,
                         current_filters={
                             'search': search_query,
                             'issue': issue_filter,
                             'volume': volume_filter,
                             'year': year_filter,
                             'access': access_filter,
                             'sort': sort_by
                         },
                         total_results=total_results,
                         total_pages=total_pages,
                         page=page,
                         pagination_pages=pagination_pages,
                         per_page=per_page,
                         author_tooltip_ui=author_tooltip_ui)


def app__news():
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    per_page = 12

    all_items = dbc.news.get(status='published').order_by('published_at').exec()
    news_items = dbc.news.get(type='news', status='published').order_by('published_at').exec()
    announcements = dbc.news.get(type='announcement', status='published').order_by('published_at').exec()

    for item in all_items + news_items + announcements:
        translate(item)

    total_results = len(all_items)
    total_pages = max((total_results + per_page - 1) // per_page, 1)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    all_items = all_items[start:start + per_page]
    pagination = _SimplePagination(page, total_pages)

    return render_template('mainweb/news.html',
                         all_items=all_items,
                         news_items=news_items,
                         announcements=announcements,
                         pagination=pagination)


def app__news_detail(news_id):
    news_item = dbc.news.get(id=news_id, status='published').exec()
    if not news_item:
        flash('News item not found', 'error')
        return redirect(url_for('app__news'))

    news_item = translate(news_item[0])

    author = None
    if news_item.get('author_id'):
        author_data = dbc.author_profile.get(id=news_item['author_id']).exec()
        if author_data:
            author = author_data[0]

    related_items = dbc.news.get(type=news_item['type'], status='published').unequal(id=news_id).order_by('published_at').per_page(3).page(1).exec()
    for item in related_items:
        item = translate(item)

    return render_template('mainweb/news_detail.html',
                         news_item=news_item,
                         author=author,
                         related_items=related_items)


def app__change_language(lang):
    if lang in ['en', 'uz', 'ru']:
        session['language'] = lang
        session.modified = True
        user_id = session.get('user_id')
        if user_id:
            try:
                dbc.users.get(id=user_id).update(ui_language=lang).exec()
            except Exception:
                try:
                    dbc.conn.rollback()
                except Exception:
                    pass
            session_user = session.get('user') or {}
            if session_user:
                session_user['ui_language'] = lang
                session['user'] = session_user
        clear_translations_cache()
        flash(f'language_changed_to_{lang}', 'success')
    else:
        flash('invalid_language', 'error')

    redirect_url = _safe_internal_redirect(request.form.get('redirect_url') or request.referrer, 'app__index')
    if 'change_language' in redirect_url:
        redirect_url = url_for('app__index')

    return redirect(redirect_url)


def app__issues():
    current_lang = _current_lang_code()
    year_filter_raw = _clean_text(request.args.get('year'))
    parsed_year_filter = _parse_int(year_filter_raw)
    year_filter = str(parsed_year_filter) if parsed_year_filter is not None else ''
    category_filter_raw = _clean_text(request.args.get('category'))
    category_filter = _resolve_issue_category_filter(category_filter_raw)
    masters_series_mode = _is_masters_issue_alias(category_filter)
    _set_masters_series_mode(masters_series_mode)
    access_filter = request.args.get('access')

    query = dbc.issues.get()

    if parsed_year_filter is not None:
        query = query.equal(year=parsed_year_filter)

    if category_filter:
        query = query.equal(category=category_filter)

    if access_filter:
        if access_filter == 'free':
            query = query.equal(is_paid=False)
        elif access_filter == 'paid':
            query = query.equal(is_paid=True)
        elif access_filter == 'subscription':
            query = query.equal(subscription_enable=True)

    issues = query.exec()
    if not masters_series_mode:
        issues = [
            issue for issue in issues
            if not _is_masters_issue(issue)
        ]
    for issue in issues:
        translate(issue)
        _apply_localized_content(issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    issues = sorted(issues, key=lambda x: (_parse_int(x.get('created_at')) or 0), reverse=True)

    all_issues = dbc.issues.get().exec()
    year_source = [
        issue for issue in all_issues
        if _is_masters_issue(issue)
    ] if masters_series_mode else [
        issue for issue in all_issues
        if not _is_masters_issue(issue)
    ]
    available_years = sorted({
        parsed_year
        for issue in year_source
        for parsed_year in [_parse_int(issue.get('year'))]
        if parsed_year is not None
    }, reverse=True)
    return render_template('mainweb/issues.html',
                         issues=issues,
                         available_years=available_years,
                         current_filters={
                             'year': year_filter,
                             'category': category_filter,
                             'access': access_filter
                         })


def _user_subscription_is_active(user_row):
    user = user_row or {}
    end_ts = _parse_int(user.get('subscription_end_date'))
    if end_ts is None:
        return False
    return end_ts > int(time.time())


def _normalize_entitlement_scope(value):
    normalized = _clean_text(value).lower()
    if normalized in TARIFF_ENTITLEMENT_SCOPES:
        return normalized
    return 'all'


def _normalize_feature_permission(value):
    normalized = _clean_text(value).lower()
    if normalized in ALLOWED_TARIFF_FEATURE_PERMISSIONS:
        return normalized
    return None


def _parse_feature_permissions(value):
    if isinstance(value, (list, tuple, set)):
        raw_items = [str(item or '').strip() for item in value if str(item or '').strip()]
    else:
        text = _clean_text(value)
        if text.startswith('{') and text.endswith('}'):
            text = text[1:-1]
        raw_items = [item.strip().strip('"').strip("'") for item in text.split(',') if item.strip()]

    normalized_items = []
    for item in raw_items:
        normalized = _normalize_feature_permission(item)
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


def _tariff_feature_permissions(tariff):
    return _parse_feature_permissions((tariff or {}).get('feature_permissions'))


def _tariff_has_feature_permission(tariff, permission_key):
    permission = _normalize_feature_permission(permission_key)
    if not permission:
        return False
    permissions = _tariff_feature_permissions(tariff)
    if permissions:
        return permission in permissions

    # Backward compatibility for old tariffs without explicit permissions matrix.
    scope = _normalize_entitlement_scope((tariff or {}).get('entitlement_scope'))
    if permission in {'access_latest_content', 'access_archive_content'}:
        if scope == 'all':
            return True
        return permission == 'access_archive_content'
    return True


def _tariff_discount_percent(tariff, field_name):
    tariff_row = tariff or {}
    permission_map = {
        'article_discount_pct': 'article_discount',
        'issue_discount_pct': 'issue_discount',
    }
    required_permission = permission_map.get(field_name)
    if required_permission and not _tariff_has_feature_permission(tariff_row, required_permission):
        return 0.0

    percent = _parse_float(tariff_row.get(field_name), 0.0)
    if percent < 0:
        return 0.0
    if percent > 100:
        return 100.0
    return percent


def _apply_discount_percent(amount, discount_percent):
    base_amount = _parse_float(amount, 0.0)
    percent = _parse_float(discount_percent, 0.0)
    if percent <= 0:
        return round(base_amount, 2)
    if percent >= 100:
        return 0.0
    discounted = base_amount * ((100.0 - percent) / 100.0)
    return round(max(discounted, 0.0), 2)


def _extract_content_timestamp(record, fallback_year_key=None):
    row = record or {}
    for key in ('date_publish', 'published_at', 'created_at', 'created_date'):
        timestamp = _parse_int(row.get(key))
        if timestamp and timestamp > 0:
            return timestamp

    if fallback_year_key:
        year = _parse_int(row.get(fallback_year_key))
        if year and 1970 <= year <= 2100:
            try:
                return int(time.mktime(time.strptime(f'{year}-01-01', '%Y-%m-%d')))
            except Exception:
                return None
    return None


def _normalize_timestamp_to_local_day_start(timestamp):
    timestamp_int = _parse_int(timestamp)
    if not timestamp_int or timestamp_int <= 0:
        return 0
    try:
        local_date = time.localtime(timestamp_int)
        midnight = time.struct_time((
            local_date.tm_year,
            local_date.tm_mon,
            local_date.tm_mday,
            0,
            0,
            0,
            local_date.tm_wday,
            local_date.tm_yday,
            local_date.tm_isdst,
        ))
        return int(time.mktime(midnight))
    except Exception:
        return timestamp_int


def _publication_sort_key(publication):
    row = publication or {}
    publish_ts = _normalize_timestamp_to_local_day_start(row.get('date_publish'))
    created_ts = _parse_int(row.get('created_at')) or 0
    primary_ts = publish_ts or created_ts
    publication_id = _parse_int(row.get('id')) or 0
    return (primary_ts, publication_id, created_ts)


def _publication_recent_sort_key(publication):
    # Keep "latest" ordering stable across environments:
    # 1) publish date (if present),
    # 2) id for the same publish date — insertion order is immutable, while
    #    created_at is editable in the admin form and unreliable in practice,
    # 3) creation timestamp as the last tie-breaker.
    return _publication_sort_key(publication)


def _record_age_days(timestamp):
    timestamp_int = _parse_int(timestamp)
    if timestamp_int is None:
        return None
    seconds = int(time.time()) - timestamp_int
    if seconds < 0:
        return 0
    return seconds // (24 * 60 * 60)


def _tariff_allows_issue_access(tariff, issue):
    tariff_row = tariff or {}
    permissions = _tariff_feature_permissions(tariff_row)
    threshold_days = _parse_int(tariff_row.get('archive_days_threshold'))
    if threshold_days is None or threshold_days < 1:
        threshold_days = DEFAULT_ARCHIVE_DAYS_THRESHOLD

    if permissions:
        issue_timestamp = _extract_content_timestamp(issue, fallback_year_key='year')
        age_days = _record_age_days(issue_timestamp)
        if age_days is None:
            return False
        if age_days >= threshold_days:
            return 'access_archive_content' in permissions
        return 'access_latest_content' in permissions

    scope = _normalize_entitlement_scope(tariff_row.get('entitlement_scope'))
    if scope == 'all':
        return True

    issue_timestamp = _extract_content_timestamp(issue, fallback_year_key='year')
    age_days = _record_age_days(issue_timestamp)
    if age_days is None:
        return False
    return age_days >= threshold_days


def _tariff_allows_article_access(tariff, publication):
    tariff_row = tariff or {}
    permissions = _tariff_feature_permissions(tariff_row)
    threshold_days = _parse_int(tariff_row.get('archive_days_threshold'))
    if threshold_days is None or threshold_days < 1:
        threshold_days = DEFAULT_ARCHIVE_DAYS_THRESHOLD

    if permissions:
        publication_timestamp = _extract_content_timestamp(publication)
        if publication_timestamp is None:
            issue_id = _parse_int((publication or {}).get('issue_id'))
            if issue_id is not None:
                issue_rows = dbc.issues.get(id=issue_id).exec()
                if issue_rows:
                    publication_timestamp = _extract_content_timestamp(issue_rows[0], fallback_year_key='year')

        age_days = _record_age_days(publication_timestamp)
        if age_days is None:
            return False
        if age_days >= threshold_days:
            return 'access_archive_content' in permissions
        return 'access_latest_content' in permissions

    scope = _normalize_entitlement_scope(tariff_row.get('entitlement_scope'))
    if scope == 'all':
        return True

    publication_timestamp = _extract_content_timestamp(publication)
    if publication_timestamp is None:
        issue_id = _parse_int((publication or {}).get('issue_id'))
        if issue_id is not None:
            issue_rows = dbc.issues.get(id=issue_id).exec()
            if issue_rows:
                publication_timestamp = _extract_content_timestamp(issue_rows[0], fallback_year_key='year')

    age_days = _record_age_days(publication_timestamp)
    if age_days is None:
        return False
    return age_days >= threshold_days


def _load_user_row(user_id):
    user_id_int = _parse_int(user_id)
    if user_id_int is None:
        return {}
    user_rows = dbc.users.get(id=user_id_int).exec()
    return user_rows[0] if user_rows else {}


def _load_active_subscription_tariff(user_row):
    user = user_row or {}
    if not _user_subscription_is_active(user):
        return None
    tariff_id = _parse_int(user.get('tariff_id'))
    if tariff_id is None:
        return None
    tariff_rows = dbc.tariffs.get(id=tariff_id).exec()
    return tariff_rows[0] if tariff_rows else None


def _subscription_grants_issue_access(user_row, issue, tariff_row=None):
    user = user_row or {}
    if not _user_subscription_is_active(user):
        return False

    tariff = tariff_row
    if tariff is None:
        tariff = _load_active_subscription_tariff(user)

    if tariff is None:
        # Legacy users can still have an active subscription_end_date without tariff_id.
        return True

    return _tariff_allows_issue_access(tariff, issue)


def _subscription_grants_article_access(user_row, publication, tariff_row=None):
    user = user_row or {}
    if not _user_subscription_is_active(user):
        return False

    tariff = tariff_row
    if tariff is None:
        tariff = _load_active_subscription_tariff(user)

    if tariff is None:
        # Legacy users can still have an active subscription_end_date without tariff_id.
        return True

    return _tariff_allows_article_access(tariff, publication)


def _user_has_paid_access(user_id, payment_type, target_id):
    user_id_int = _parse_int(user_id)
    if user_id_int is None or target_id is None:
        return False

    target_text = str(target_id)
    payments = dbc.payments.get(user_id=user_id_int, status='paid').exec()
    for payment in payments:
        if _clean_text(payment.get('payment_type')).lower() != payment_type:
            continue
        payment_ids = payment.get('ids') or []
        if not isinstance(payment_ids, (list, tuple)):
            continue
        if target_text in {str(item) for item in payment_ids}:
            return True
    return False


def _resolve_issue_access_context(issue, user_id=None):
    issue_row = issue or {}
    requires_subscription = bool(issue_row.get('subscription_enable'))
    requires_purchase = bool(issue_row.get('is_paid'))
    requires_access = requires_subscription or requires_purchase
    context = {
        'has_access': False,
        'requires_subscription': requires_subscription,
        'requires_purchase': requires_purchase,
        'access_via': None,
        'user': {},
        'tariff': None,
    }
    if not requires_access:
        context['has_access'] = True
        context['access_via'] = 'open'
        return context

    user_id_int = _parse_int(user_id)
    if user_id_int is None:
        return context

    user = _load_user_row(user_id_int)
    tariff = _load_active_subscription_tariff(user)
    context['user'] = user
    context['tariff'] = tariff

    if requires_purchase and _user_has_paid_access(user_id_int, 'issue', issue_row.get('id')):
        context['has_access'] = True
        context['access_via'] = 'purchase'
        return context

    # Subscription should unlock any restricted issue (paid or subscription-only)
    # when the active tariff grants access by entitlement rules.
    if requires_access and _subscription_grants_issue_access(user, issue_row, tariff):
        context['has_access'] = True
        context['access_via'] = 'subscription'
        return context

    return context


def _resolve_article_access_context(publication, user_id=None):
    publication_row = publication or {}
    requires_subscription = bool(publication_row.get('subscription_enable'))
    requires_purchase = bool(publication_row.get('is_paid'))
    requires_access = requires_subscription or requires_purchase
    context = {
        'has_access': False,
        'requires_subscription': requires_subscription,
        'requires_purchase': requires_purchase,
        'access_via': None,
        'user': {},
        'tariff': None,
    }
    if not requires_access:
        context['has_access'] = True
        context['access_via'] = 'open'
        return context

    user_id_int = _parse_int(user_id)
    if user_id_int is None:
        return context

    user = _load_user_row(user_id_int)
    tariff = _load_active_subscription_tariff(user)
    context['user'] = user
    context['tariff'] = tariff

    if requires_purchase and _user_has_paid_access(user_id_int, 'article', publication_row.get('id')):
        context['has_access'] = True
        context['access_via'] = 'purchase'
        return context

    # Subscription should unlock any restricted article (paid or subscription-only)
    # when the active tariff grants access by entitlement rules.
    if requires_access and _subscription_grants_article_access(user, publication_row, tariff):
        context['has_access'] = True
        context['access_via'] = 'subscription'
        return context

    return context


def _resolve_issue_access(issue, user_id=None):
    return bool(_resolve_issue_access_context(issue, user_id).get('has_access'))


def _resolve_article_access(publication, user_id=None):
    return bool(_resolve_article_access_context(publication, user_id).get('has_access'))


def app__issue(issue_id):
    current_lang = _current_lang_code()
    author_tooltip_ui = _author_tooltip_ui_texts()
    section_options = publication_metadata_options('section_key', current_lang)
    section_order = [item.get('key') for item in section_options if item.get('key')]
    section_label_map = {
        item.get('key'): item.get('label')
        for item in section_options
        if item.get('key')
    }
    issue = dbc.issues.get(id=issue_id).exec()
    if not issue:
        flash('Issue not found', 'error')
        return redirect(url_for('app__issues'))

    issue = issue[0]
    issue_is_masters = _is_masters_issue(issue)
    if issue_is_masters and not _masters_series_mode_enabled():
        return redirect(url_for('app__issues', category=_masters_issue_category_for_redirect(issue)))

    all_issues = dbc.issues.get().exec()
    if issue_is_masters:
        all_issues = [row for row in all_issues if _is_masters_issue(row)]
    else:
        all_issues = [row for row in all_issues if not _is_masters_issue(row)]
    for list_issue in all_issues:
        _apply_localized_content(list_issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    all_issues = sorted(all_issues, key=_issue_sort_key)

    current_index = None
    for i, curr_issue in enumerate(all_issues):
        if curr_issue['id'] == issue_id:
            current_index = i
            break

    prev_issue = all_issues[current_index - 1] if current_index > 0 else None
    next_issue = all_issues[current_index + 1] if current_index < len(all_issues) - 1 else None

    has_access = _resolve_issue_access(issue, session.get('user_id'))
    issue_toc_public_url = _issue_toc_public_url(issue)
    issue_toc_file_path, _ = _resolve_issue_toc_download_file(issue)
    if issue_toc_file_path:
        issue_toc_download_url = url_for('app__download_issue_toc', issue_id=issue_id)
    else:
        issue_toc_download_url = issue_toc_public_url

    publications = dbc.publications.get(issue_id=issue_id).exec()
    publications = sorted(publications, key=_publication_sort_key, reverse=True)
    articles = []
    author_profile_cache = {}

    def get_author_profile(author_id):
        if not author_id:
            return None
        if author_id not in author_profile_cache:
            author_rows = dbc.author_profile.get(id=author_id).exec()
            if author_rows:
                author_profile_cache[author_id] = _author_tooltip_payload(
                    translate(author_rows[0]),
                    lang=current_lang,
                )
            else:
                author_profile_cache[author_id] = None
        return author_profile_cache[author_id]

    if publications:
        for pub in publications:
            translate(pub)
            _apply_localized_content(pub, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)
            author_profiles = []
            main_author_profile = get_author_profile(pub.get('main_author_id'))
            if main_author_profile:
                author_profiles.append(main_author_profile)

            co_author_ids = pub.get('subauthor_ids') or pub.get('sub_author_ids') or []
            for author_id in co_author_ids:
                co_author_profile = get_author_profile(author_id)
                if co_author_profile:
                    author_profiles.append(co_author_profile)

            doi_value = _clean_text(pub.get('doi'))
            doi_link = _clean_text(pub.get('doi_link'))
            if doi_value and not doi_link:
                doi_link = f"https://doi.org/{doi_value}"

            articles.append({
                'id': pub['id'],
                'title': pub['title'],
                'authors': ', '.join(author_item.get('name') for author_item in author_profiles if author_item.get('name')),
                'author_profiles': author_profiles,
                'doi': doi_value,
                'doi_link': doi_link,
                'page_range': _clean_text(pub.get('page_range')),
                'section_key': _clean_text(pub.get('section_key')),
                'section_display': publication_metadata_label('section_key', pub.get('section_key'), current_lang),
            })

    article_sections = []
    for section_key in section_order:
        items = [item for item in articles if item.get('section_key') == section_key]
        if not items:
            continue
        article_sections.append({
            'key': section_key,
            'label': section_label_map.get(section_key) or '',
            'articles': items,
        })

    remaining_articles = [
        item for item in articles
        if not item.get('section_key') or item.get('section_key') not in section_label_map
    ]
    if remaining_articles:
        article_sections.append({
            'key': '__unassigned__',
            'label': '',
            'articles': remaining_articles,
        })

    if not article_sections and articles:
        article_sections = [{
            'key': '__all__',
            'label': '',
            'articles': articles,
        }]
    issue = translate(issue)
    _apply_localized_content(issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    if prev_issue:
        _apply_localized_content(prev_issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    if next_issue:
        _apply_localized_content(next_issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    issue_shortinfo = _build_issue_shortinfo(issue.get('shortinfo'))
    issue_ui = _issue_ui_texts()
    return render_template('mainweb/issue.html',
                         issue=issue,
                         has_access=has_access,
                         prev_issue=prev_issue,
                         next_issue=next_issue,
                         articles=articles,
                         article_sections=article_sections,
                         issue_toc_download_url=issue_toc_download_url,
                         issue_shortinfo=issue_shortinfo,
                         issue_ui=issue_ui,
                         author_tooltip_ui=author_tooltip_ui)


def app__purchase_issue(issue_id):
    return redirect(url_for('app__issues'))


def _normalize_currency(currency):
    normalized = (currency or 'usd').strip().lower()
    if normalized in {'usd', 'uzs', 'rub'}:
        return normalized
    return 'usd'


def _default_currency_for_language():
    lang = _current_lang_code()
    if lang == 'uz':
        return 'uzs'
    if lang == 'ru':
        return 'rub'
    return 'usd'


def _resolve_publication_price_local(publication, currency='usd'):
    if not publication:
        return 0.0
    normalized = _normalize_currency(currency)
    if normalized == 'uzs':
        return float(publication.get('price_uz') or publication.get('price') or 0.0)
    if normalized == 'rub':
        return float(publication.get('price_ru') or publication.get('price') or 0.0)
    return float(publication.get('price') or 0.0)


def app__purchase_article(article_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to continue', 'error')
        return redirect(url_for('app__login'))

    current_lang = _current_lang_code()
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = publication[0]
    issue_cache_for_visibility = {}
    if _is_masters_publication(publication, issue_cache=issue_cache_for_visibility) and not _masters_series_mode_enabled():
        issue_id = _parse_int(publication.get('issue_id'))
        issue_row = issue_cache_for_visibility.get(issue_id) if issue_id is not None else None
        target_category = _masters_issue_category_for_redirect(issue_row or {'category': 'masters'})
        return redirect(url_for('app__issues', category=target_category))

    publication = translate(publication)
    _apply_localized_content(publication, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)

    if not publication.get('is_paid'):
        return redirect(url_for('app__article', article_id=article_id))

    access_context = _resolve_article_access_context(publication, user_id)
    if access_context.get('has_access'):
        return redirect(url_for('app__article', article_id=article_id))

    currency = _normalize_currency(request.args.get('currency') or _default_currency_for_language())
    original_amount = _resolve_publication_price_local(publication, currency)
    active_tariff = access_context.get('tariff')
    discount_percent = _tariff_discount_percent(active_tariff, 'article_discount_pct') if active_tariff else 0.0
    amount = _apply_discount_percent(original_amount, discount_percent)
    guide_html = _get_payment_guide_html(current_lang)

    return render_template(
        'mainweb/purchase_article.html',
        publication=publication,
        amount=amount,
        original_amount=original_amount,
        discount_percent=discount_percent,
        currency=currency,
        guide_html=guide_html
    )


def app__article(article_id):
    current_lang = _current_lang_code()
    metadata_labels = publication_metadata_field_labels(current_lang)
    author_tooltip_ui = _author_tooltip_ui_texts()
    viewer_user_id = session.get('user_id')
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = publication[0]
    issue_row_for_visibility = None
    issue_id = _parse_int(publication.get('issue_id'))
    if issue_id is not None:
        issue_rows = dbc.issues.get(id=issue_id).exec()
        issue_row_for_visibility = issue_rows[0] if issue_rows else None

    if _is_masters_publication(publication, issue_row=issue_row_for_visibility) and not _masters_series_mode_enabled():
        target_category = _masters_issue_category_for_redirect(issue_row_for_visibility or {'category': 'masters'})
        return redirect(url_for('app__issues', category=target_category))

    publication = translate(publication)
    _apply_localized_content(publication, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)
    if publication.get('doi') and not publication.get('doi_link'):
        publication['doi_link'] = f"https://doi.org/{publication.get('doi')}"
    publication['page_range'] = _clean_text(publication.get('page_range'))
    publication['author_position_display'] = publication_metadata_label(
        'author_position_key',
        publication.get('author_position_key'),
        current_lang
    )
    publication['academic_title_display'] = publication_metadata_label(
        'academic_title_key',
        publication.get('academic_title_key'),
        current_lang
    )
    publication['academic_degree_display'] = publication_metadata_label(
        'academic_degree_key',
        publication.get('academic_degree_key'),
        current_lang
    )
    publication['series_display'] = publication_metadata_label(
        'series_key',
        publication.get('series_key'),
        current_lang
    )
    publication['section_display'] = publication_metadata_label(
        'section_key',
        publication.get('section_key'),
        current_lang
    )
    references_count = len(dbc.publication_refs.get(publication_id=article_id).exec())
    citations_count = len(dbc.publication_citations.get(publication_id=article_id).exec())
    publication['references_count'] = references_count
    publication['citations_count'] = citations_count
    if _should_increment_article_view(article_id, user_id=viewer_user_id):
        new_views = (publication.get('stat_views') or 0) + 1
        try:
            dbc.publications.get(id=article_id).update(stat_views=new_views).exec()
            publication['stat_views'] = new_views
        except Exception:
            current_app.logger.exception('Failed to update view count for article %s', article_id)
        _record_activity_event(
            viewer_user_id,
            metric='view',
            publication_id=article_id,
            issue_id=issue_id,
            amount=1,
        )
    access_context = _resolve_article_access_context(publication, session.get('user_id'))
    has_access = bool(access_context.get('has_access'))
    purchase_currency = _default_currency_for_language()
    purchase_base_amount = _resolve_publication_price_local(publication, purchase_currency)
    purchase_discount_percent = _tariff_discount_percent(access_context.get('tariff'), 'article_discount_pct')
    purchase_amount = _apply_discount_percent(purchase_base_amount, purchase_discount_percent)

    main_author = None
    if publication['main_author_id']:
        main_author_rows = dbc.author_profile.get(id=publication['main_author_id']).exec()
        if main_author_rows:
            main_author = _author_tooltip_payload(
                translate(main_author_rows[0]),
                lang=current_lang,
            )

    co_authors = []
    for author_id in (publication.get('subauthor_ids') or publication.get('sub_author_ids') or []):
        co_author_rows = dbc.author_profile.get(id=author_id).exec()
        if co_author_rows:
            co_author_profile = _author_tooltip_payload(
                translate(co_author_rows[0]),
                lang=current_lang,
            )
            if co_author_profile:
                co_authors.append(co_author_profile)

    issue = None
    if issue_row_for_visibility:
        translated_issue = translate(dict(issue_row_for_visibility))
        issue = _apply_localized_content(translated_issue, ('title', 'shortinfo', 'price'), lang=current_lang)

    scholar_author_names = []
    for profile in [main_author] + list(co_authors):
        if not profile:
            continue
        author_name = _clean_text(profile.get('name')) if isinstance(profile, dict) else _clean_text(profile)
        if author_name:
            scholar_author_names.append(author_name)

    scholar_meta = _build_scholar_meta(
        publication=publication,
        issue=issue,
        author_names=scholar_author_names,
        article_id=article_id,
        current_lang=current_lang
    )

    parts = []
    figures = []
    references = []
    citations = []
    if has_access:
        parts = dbc.publication_parts.get(publication_id=article_id).order_by('order_id').exec()
        figures = dbc.publication_figures.get(publication_id=article_id).order_by('order_id').exec()
        references = dbc.publication_refs.get(publication_id=article_id).exec()
        citations = dbc.publication_citations.get(publication_id=article_id).exec()

        for ref in references:
            translate(ref)
            if not ref.get('doi_link') and ref.get('doi'):
                ref['doi_link'] = f"https://doi.org/{ref['doi']}"
            if not ref.get('wos_link') and ref.get('web_of_science_url'):
                ref['wos_link'] = ref.get('web_of_science_url')
            if not ref.get('gscholar_link') and ref.get('google_scholar_url'):
                ref['gscholar_link'] = ref.get('google_scholar_url')
            if not ref.get('web_link') and ref.get('url'):
                ref['web_link'] = ref.get('url')
            if not ref.get('resource') and ref.get('source_title'):
                ref['resource'] = ref.get('source_title')
        for citation in citations:
            translate(citation)
            if not citation.get('doi_link') and citation.get('doi'):
                citation['doi_link'] = f"https://doi.org/{citation['doi']}"
            if not citation.get('wos_link') and citation.get('web_of_science_url'):
                citation['wos_link'] = citation.get('web_of_science_url')
            if not citation.get('gscholar_link') and citation.get('google_scholar_url'):
                citation['gscholar_link'] = citation.get('google_scholar_url')

    return render_template('mainweb/article.html',
                         publication=publication,
                         metadata_labels=metadata_labels,
                         has_access=has_access,
                         purchase_currency=purchase_currency,
                         purchase_amount=purchase_amount,
                         purchase_base_amount=purchase_base_amount,
                         purchase_discount_percent=purchase_discount_percent,
                         main_author=main_author,
                         co_authors=co_authors,
                         author_tooltip_ui=author_tooltip_ui,
                         issue=issue,
                         scholar_meta=scholar_meta,
                         publication_parts=parts,
                         publication_figures=figures,
                         publication_refs=references,
                         publication_citations=citations)


def _ensure_subscription_download_usage_table():
    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subscription_download_usage (
                user_id INTEGER NOT NULL,
                period_key TEXT NOT NULL,
                downloads_count INTEGER NOT NULL DEFAULT 0,
                created_at BIGINT NOT NULL,
                updated_at BIGINT NOT NULL,
                PRIMARY KEY (user_id, period_key)
            );
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_subscription_download_usage_period "
            "ON subscription_download_usage(period_key);"
        )
        dbc.conn.commit()
        return True
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to ensure subscription_download_usage table")
        return False
    finally:
        if cursor is not None:
            cursor.close()


def _subscription_usage_period_key(now_ts=None):
    timestamp = _parse_int(now_ts)
    if timestamp is None:
        timestamp = int(time.time())
    local_ts = timestamp + (5 * 60 * 60)
    return time.strftime('%Y-%m', time.gmtime(local_ts))


def _consume_subscription_download_slot(user_id, monthly_limit):
    user_id_int = _parse_int(user_id)
    limit = _parse_int(monthly_limit) or 0
    if user_id_int is None:
        return {'allowed': False, 'used': 0, 'limit': limit}
    if limit <= 0:
        return {'allowed': True, 'used': 0, 'limit': 0}
    if not _ensure_subscription_download_usage_table():
        # Fail open: do not block legitimate downloads when usage tracking is temporarily unavailable.
        return {'allowed': True, 'used': 0, 'limit': limit}

    period_key = _subscription_usage_period_key()
    lock_name = f"sub-download:{user_id_int}:{period_key}"
    cursor = None
    try:
        cursor = dbc.conn.cursor()
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s)::bigint)", (lock_name,))
        cursor.execute(
            "SELECT downloads_count FROM subscription_download_usage "
            "WHERE user_id = %s AND period_key = %s FOR UPDATE",
            (user_id_int, period_key)
        )
        row = cursor.fetchone()
        current_count = int(row[0] or 0) if row else 0
        if current_count >= limit:
            dbc.conn.commit()
            return {'allowed': False, 'used': current_count, 'limit': limit}

        now_ts = int(time.time())
        if row:
            cursor.execute(
                "UPDATE subscription_download_usage "
                "SET downloads_count = downloads_count + 1, updated_at = %s "
                "WHERE user_id = %s AND period_key = %s "
                "RETURNING downloads_count",
                (now_ts, user_id_int, period_key)
            )
        else:
            cursor.execute(
                "INSERT INTO subscription_download_usage "
                "(user_id, period_key, downloads_count, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING downloads_count",
                (user_id_int, period_key, 1, now_ts, now_ts)
            )
        used_row = cursor.fetchone()
        used_count = int(used_row[0] or 0) if used_row else (current_count + 1)
        dbc.conn.commit()
        return {'allowed': True, 'used': used_count, 'limit': limit}
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to consume download slot for user_id=%s", user_id_int)
        return {'allowed': True, 'used': 0, 'limit': limit}
    finally:
        if cursor is not None:
            cursor.close()


def _resolve_public_upload_abspath(stored_filepath):
    public_url = _normalize_public_upload_url(stored_filepath)
    if not public_url:
        return None
    relative_path = public_url[len('/static/uploads/'):].lstrip('/')

    base_dir = os.path.abspath(os.path.join(settings.SAVE_PATH, 'static', 'uploads'))
    candidate_path = os.path.abspath(os.path.join(base_dir, relative_path))
    try:
        if os.path.commonpath([candidate_path, base_dir]) != base_dir:
            return None
    except ValueError:
        return None
    return candidate_path


def _resolve_publication_download_file(publication):
    publication_row = publication or {}
    file_ids = publication_row.get('file_ids') or []
    for file_id in reversed(file_ids):
        file_record_rows = dbc.files.get(id=file_id).exec()
        if not file_record_rows:
            continue

        file_record = file_record_rows[0]
        stored_filepath = (file_record.get('filepath') or '').strip()
        if not stored_filepath:
            continue

        file_path = _resolve_public_upload_abspath(stored_filepath)
        if not file_path:
            current_app.logger.warning(
                'Blocked article download for publication=%s due to invalid filepath=%r',
                publication_row.get('id'),
                stored_filepath,
            )
            continue
        if not os.path.exists(file_path):
            continue

        default_title = _clean_text(publication_row.get('title')) or f"article-{publication_row.get('id') or file_id}"
        download_name = (file_record.get('name') or '').strip() or f"{default_title}.pdf"
        return file_path, download_name

    return None, None


def _normalize_public_upload_url(stored_filepath):
    normalized_path = str(stored_filepath or '').strip()
    if not normalized_path or normalized_path.startswith('private://'):
        return None

    parsed = urlparse(normalized_path)
    candidate_path = parsed.path if parsed.scheme and parsed.netloc else normalized_path
    if not candidate_path:
        return None

    candidate_path = unquote(candidate_path).replace('\\', '/').strip()
    if not candidate_path:
        return None

    if candidate_path.startswith('/uploads/'):
        candidate_path = f"/static{candidate_path}"
    elif candidate_path.startswith('uploads/'):
        candidate_path = f"/static/{candidate_path}"
    elif candidate_path.startswith('static/uploads/'):
        candidate_path = f"/{candidate_path}"

    if not candidate_path.startswith('/static/uploads/'):
        return None

    relative_path = candidate_path[len('/static/uploads/'):].lstrip('/')
    if not relative_path:
        return None

    parts = [part for part in relative_path.split('/') if part]
    if not parts or any(part in {'.', '..'} for part in parts):
        return None

    return f"/static/uploads/{'/'.join(parts)}"


def _normalize_public_upload_urls(stored_filepath):
    urls = []
    for item in _stored_upload_value_to_list(stored_filepath):
        normalized = _normalize_public_upload_url(item)
        if normalized and normalized not in urls:
            urls.append(normalized)
    return urls


def _issue_toc_stored_filepath(issue):
    issue_row = issue or {}
    for field_name in ('table_of_contents_file', 'issue_toc_file', 'toc_file'):
        raw_value = _clean_text(issue_row.get(field_name))
        if raw_value:
            return raw_value
    return ''


def _issue_toc_public_url(issue):
    stored_filepath = _issue_toc_stored_filepath(issue)
    if not stored_filepath:
        return None

    public_url = _normalize_public_upload_url(stored_filepath)
    if not public_url:
        return None

    ext = os.path.splitext(public_url)[1].lower()
    if ext not in {'.pdf', '.doc', '.docx'}:
        logger.warning(
            'Blocked issue TOC link for issue=%s due to unsupported extension=%r',
            (issue or {}).get('id'),
            ext,
        )
        return None
    return public_url


def _resolve_issue_toc_download_file(issue):
    issue_row = issue or {}
    stored_filepath = _issue_toc_stored_filepath(issue_row)
    public_url = _issue_toc_public_url(issue_row)
    if not stored_filepath or not public_url:
        return None, None

    file_path = _resolve_public_upload_abspath(public_url)
    if not file_path:
        current_app.logger.warning(
            'Blocked issue TOC download for issue=%s due to invalid filepath=%r',
            issue_row.get('id'),
            stored_filepath,
        )
        return None, None
    if not os.path.exists(file_path):
        current_app.logger.warning(
            'Issue TOC file is not present on local filesystem for issue=%s path=%r',
            issue_row.get('id'),
            file_path,
        )
        return None, None

    ext = os.path.splitext(file_path)[1].lower()
    volume_value = _clean_text(issue_row.get('vol_no')) or 'x'
    issue_value = _clean_text(issue_row.get('issue_no')) or 'x'
    download_base = f"volume-{volume_value}-issue-{issue_value}-table-of-contents"
    download_base = re.sub(r'[^a-zA-Z0-9._-]+', '-', download_base).strip('-').lower() or f"issue-{issue_row.get('id') or 'x'}-table-of-contents"
    return file_path, f"{download_base}{ext}"


def app__download_article(article_id):
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = publication[0]
    issue_cache_for_visibility = {}
    if _is_masters_publication(publication, issue_cache=issue_cache_for_visibility) and not _masters_series_mode_enabled():
        issue_id = _parse_int(publication.get('issue_id'))
        issue_row = issue_cache_for_visibility.get(issue_id) if issue_id is not None else None
        target_category = _masters_issue_category_for_redirect(issue_row or {'category': 'masters'})
        return redirect(url_for('app__issues', category=target_category))

    requires_access = bool(publication.get('is_paid') or publication.get('subscription_enable'))
    access_context = {'has_access': True, 'access_via': 'open', 'tariff': None}
    user_id = None
    if requires_access:
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to download this article', 'error')
            return redirect(url_for('app__login'))

        access_context = _resolve_article_access_context(publication, user_id)
        has_access = bool(access_context.get('has_access'))
        if not has_access:
            flash('Access denied. Please purchase or subscribe.', 'error')
            return redirect(url_for('app__article', article_id=article_id))

    if not publication.get('file_ids'):
        flash('Article file not found', 'error')
        return redirect(url_for('app__article', article_id=article_id))

    selected_file_path, selected_download_name = _resolve_publication_download_file(publication)

    if not selected_file_path:
        flash('Article file not found', 'error')
        return redirect(url_for('app__article', article_id=article_id))

    if access_context.get('access_via') == 'subscription':
        tariff = access_context.get('tariff') or {}
        if not _tariff_has_feature_permission(tariff, 'download_subscription_files'):
            flash('Your current subscription does not include file downloads.', 'error')
            return redirect(url_for('app__article', article_id=article_id))
        monthly_limit = _parse_int(tariff.get('monthly_download_limit')) or 0
        limit_result = _consume_subscription_download_slot(user_id, monthly_limit)
        if not limit_result.get('allowed'):
            flash(f"Monthly download limit reached ({limit_result.get('limit')} downloads).", 'error')
            return redirect(url_for('app__article', article_id=article_id))

    if _should_increment_download('download', article_id, user_id=session.get('user_id')):
        try:
            new_downloads = (publication.get('stat_alt') or 0) + 1
            dbc.publications.get(id=article_id).update(stat_alt=new_downloads).exec()
        except Exception:
            current_app.logger.exception('Failed to update download count for article %s', article_id)
        _record_activity_event(
            session.get('user_id'),
            metric='download',
            publication_id=article_id,
            issue_id=publication.get('issue_id'),
            amount=1,
        )
        # A direct download (e.g. from an issue's table of contents) implies the
        # article was consulted, yet it bypasses the article page where views are
        # counted. Register a view too — guarded by the same per-session dedup and
        # bot filter — so total downloads can never outpace total views.
        if _should_increment_article_view(article_id, user_id=session.get('user_id')):
            try:
                new_views = (publication.get('stat_views') or 0) + 1
                dbc.publications.get(id=article_id).update(stat_views=new_views).exec()
            except Exception:
                current_app.logger.exception('Failed to update view count for article %s', article_id)
            _record_activity_event(
                session.get('user_id'),
                metric='view',
                publication_id=article_id,
                issue_id=publication.get('issue_id'),
                amount=1,
            )

    mime_type = mimetypes.guess_type(selected_file_path)[0] or 'application/pdf'
    return send_file(
        selected_file_path,
        as_attachment=False,
        download_name=selected_download_name,
        mimetype=mime_type,
    )


def app__download_issue(issue_id):
    issue_rows = dbc.issues.get(id=issue_id).exec()
    if not issue_rows:
        flash('Issue not found', 'error')
        return redirect(url_for('app__issues'))

    issue = issue_rows[0]
    if _is_masters_issue(issue) and not _masters_series_mode_enabled():
        return redirect(url_for('app__issues', category=_masters_issue_category_for_redirect(issue)))
    requires_access = bool(issue.get('is_paid') or issue.get('subscription_enable'))
    access_context = {'has_access': True, 'access_via': 'open', 'tariff': None}
    user_id = None
    if requires_access:
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to download this issue', 'error')
            return redirect(url_for('app__login'))

        access_context = _resolve_issue_access_context(issue, user_id)
        if not access_context.get('has_access'):
            flash('Access denied. Please purchase or subscribe.', 'error')
            return redirect(url_for('app__issue', issue_id=issue_id))

    publications = dbc.publications.get(issue_id=issue_id).exec()
    downloadable_files = []
    for publication in publications:
        file_path, download_name = _resolve_publication_download_file(publication)
        if file_path:
            downloadable_files.append((publication, file_path, download_name))

    if not downloadable_files:
        flash('Issue files not found', 'error')
        return redirect(url_for('app__issue', issue_id=issue_id))

    if access_context.get('access_via') == 'subscription':
        tariff = access_context.get('tariff') or {}
        if not _tariff_has_feature_permission(tariff, 'download_subscription_files'):
            flash('Your current subscription does not include file downloads.', 'error')
            return redirect(url_for('app__issue', issue_id=issue_id))
        monthly_limit = _parse_int(tariff.get('monthly_download_limit')) or 0
        limit_result = _consume_subscription_download_slot(user_id, monthly_limit)
        if not limit_result.get('allowed'):
            flash(f"Monthly download limit reached ({limit_result.get('limit')} downloads).", 'error')
            return redirect(url_for('app__issue', issue_id=issue_id))

    used_names = set()

    def _unique_name(name):
        filename = _clean_text(name) or 'article.pdf'
        stem, ext = os.path.splitext(filename)
        if not ext:
            ext = '.pdf'
        candidate = f"{stem}{ext}"
        counter = 2
        while candidate.lower() in used_names:
            candidate = f"{stem}-{counter}{ext}"
            counter += 1
        used_names.add(candidate.lower())
        return candidate

    count_issue_download = _should_increment_download(
        'issue_download', issue_id, user_id=session.get('user_id')
    )
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        for publication, file_path, download_name in downloadable_files:
            archive.write(file_path, arcname=_unique_name(download_name))
            if count_issue_download:
                try:
                    new_downloads = (publication.get('stat_alt') or 0) + 1
                    dbc.publications.get(id=publication.get('id')).update(stat_alt=new_downloads).exec()
                except Exception:
                    current_app.logger.exception('Failed to update download count for article %s', publication.get('id'))
    if count_issue_download:
        # One user action = one download event, regardless of how many
        # article files end up inside the ZIP archive.
        _record_activity_event(
            session.get('user_id'),
            metric='download',
            issue_id=issue_id,
            amount=1,
        )

    archive_buffer.seek(0)
    issue_filename = f"volume-{_clean_text(issue.get('vol_no')) or 'x'}-issue-{_clean_text(issue.get('issue_no')) or 'x'}"
    issue_filename = re.sub(r'[^a-zA-Z0-9._-]+', '-', issue_filename).strip('-').lower() or f"issue-{issue_id}"
    return send_file(
        archive_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{issue_filename}.zip",
    )


def app__download_issue_toc(issue_id):
    issue_rows = dbc.issues.get(id=issue_id).exec()
    if not issue_rows:
        flash('Issue not found', 'error')
        return redirect(url_for('app__issues'))

    issue = issue_rows[0]
    if _is_masters_issue(issue) and not _masters_series_mode_enabled():
        return redirect(url_for('app__issues', category=_masters_issue_category_for_redirect(issue)))

    file_path, download_name = _resolve_issue_toc_download_file(issue)
    if not file_path:
        fallback_public_url = _issue_toc_public_url(issue)
        if fallback_public_url:
            return redirect(fallback_public_url)
        flash('Table of contents file not found', 'error')
        return redirect(url_for('app__issue', issue_id=issue_id))

    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    return send_file(
        file_path,
        as_attachment=True,
        download_name=download_name,
        mimetype=mime_type,
    )


def app__robots_txt():
    response = render_template('robots.txt')
    return Response(response, mimetype='text/plain')


def app__sitemap_xml():
    now_ts = int(time.time())
    entries = []
    seen_urls = set()

    static_pages = [
        ('app__index', {}, now_ts, 'daily', '1.0'),
        ('app__articles', {}, now_ts, 'daily', '0.9'),
        ('app__issues', {}, now_ts, 'weekly', '0.9'),
        ('app__news', {}, now_ts, 'daily', '0.8'),
        ('app__editorial', {}, now_ts, 'monthly', '0.6'),
        ('app__contact', {}, now_ts, 'monthly', '0.5'),
        ('app__payment_guide', {}, now_ts, 'monthly', '0.4'),
    ]
    for endpoint, endpoint_kwargs, lastmod_ts, changefreq, priority in static_pages:
        _add_sitemap_url(
            entries=entries,
            seen_urls=seen_urls,
            endpoint=endpoint,
            endpoint_kwargs=endpoint_kwargs,
            lastmod_ts=lastmod_ts,
            changefreq=changefreq,
            priority=priority,
        )

    # Include seed/static pages (except aliases that only redirect).
    existing_aliases = set()
    try:
        page_rows = dbc.pages.get().exec()
    except Exception:
        page_rows = []
    for page_row in page_rows:
        alias_text = _clean_text((page_row or {}).get('alias')).lower()
        if alias_text:
            existing_aliases.add(alias_text)

    for seed_alias in _seed_pages_data().keys():
        alias_text = _clean_text(seed_alias).lower()
        if alias_text:
            existing_aliases.add(alias_text)

    for page_alias in sorted(existing_aliases):
        if page_alias in PAGE_ALIAS_REDIRECTS or page_alias == 'payment_guide':
            continue
        _add_sitemap_url(
            entries=entries,
            seen_urls=seen_urls,
            endpoint='app__page_alias',
            endpoint_kwargs={'alias': page_alias},
            lastmod_ts=now_ts,
            changefreq='monthly',
            priority='0.5',
        )

    masters_mode_enabled = _masters_series_mode_enabled()
    issue_cache = {}
    try:
        issue_rows = dbc.issues.get().exec()
    except Exception:
        issue_rows = []
    for issue_row in issue_rows:
        issue_id = _parse_int(issue_row.get('id'))
        if issue_id is None:
            continue
        issue_cache[issue_id] = issue_row
        if _is_masters_issue(issue_row) and not masters_mode_enabled:
            continue
        issue_lastmod_ts = _extract_timestamp_by_keys(issue_row, ('updated_at', 'created_at'))
        if issue_lastmod_ts is None:
            issue_lastmod_ts = _timestamp_from_year(issue_row.get('year'))
        _add_sitemap_url(
            entries=entries,
            seen_urls=seen_urls,
            endpoint='app__issue',
            endpoint_kwargs={'issue_id': issue_id},
            lastmod_ts=issue_lastmod_ts,
            changefreq='weekly',
            priority='0.8',
        )

    try:
        publication_rows = dbc.publications.get().exec()
    except Exception:
        publication_rows = []
    for publication_row in publication_rows:
        article_id = _parse_int(publication_row.get('id'))
        if article_id is None:
            continue

        if not masters_mode_enabled:
            issue_id = _parse_int(publication_row.get('issue_id'))
            issue_row = issue_cache.get(issue_id)
            if issue_id is not None and issue_row is None:
                cached_rows = dbc.issues.get(id=issue_id).exec()
                issue_row = cached_rows[0] if cached_rows else None
                issue_cache[issue_id] = issue_row
            if _is_masters_publication(publication_row, issue_row=issue_row, issue_cache=issue_cache):
                continue

        publication_lastmod_ts = _extract_timestamp_by_keys(
            publication_row,
            ('updated_at', 'date_publish', 'published_at', 'created_at')
        )
        if publication_lastmod_ts is None:
            issue_id = _parse_int(publication_row.get('issue_id'))
            issue_row = issue_cache.get(issue_id)
            if issue_row:
                publication_lastmod_ts = _extract_timestamp_by_keys(issue_row, ('updated_at', 'created_at'))
                if publication_lastmod_ts is None:
                    publication_lastmod_ts = _timestamp_from_year(issue_row.get('year'))

        _add_sitemap_url(
            entries=entries,
            seen_urls=seen_urls,
            endpoint='app__article',
            endpoint_kwargs={'article_id': article_id},
            lastmod_ts=publication_lastmod_ts,
            changefreq='weekly',
            priority='0.9',
        )

    try:
        news_rows = dbc.news.get(status='published').exec()
    except Exception:
        news_rows = []
    for news_row in news_rows:
        news_id = _parse_int(news_row.get('id'))
        if news_id is None:
            continue
        news_lastmod_ts = _extract_timestamp_by_keys(news_row, ('updated_at', 'published_at', 'created_at'))
        _add_sitemap_url(
            entries=entries,
            seen_urls=seen_urls,
            endpoint='app__news_detail',
            endpoint_kwargs={'news_id': news_id},
            lastmod_ts=news_lastmod_ts,
            changefreq='monthly',
            priority='0.6',
        )

    response = render_template('sitemap.xml', urls=entries)
    return Response(response, mimetype='application/xml')


def serve_static_uploads(filename):
    if extract_private_upload_key(filename):
        abort(404)
    return send_from_directory(os.path.join(settings.SAVE_PATH, 'static', 'uploads'), filename)


def register(app):
    app.add_url_rule('/', view_func=app__index)
    app.add_url_rule('/editorial', view_func=app__editorial)
    app.add_url_rule('/page/<string:alias>', view_func=app__page_alias)
    app.add_url_rule('/payment-guide', view_func=app__payment_guide)
    app.add_url_rule('/article/purchase/<int:article_id>', view_func=login_required(app__purchase_article))
    app.add_url_rule('/contact', view_func=app__contact, methods=['GET', 'POST'])
    app.add_url_rule('/articles', view_func=app__articles)
    app.add_url_rule('/news', view_func=app__news)
    app.add_url_rule('/news/<int:news_id>', view_func=app__news_detail)
    app.add_url_rule('/robots.txt', view_func=app__robots_txt)
    app.add_url_rule('/sitemap.xml', view_func=app__sitemap_xml)
    app.add_url_rule('/change_language/<string:lang>', view_func=app__change_language, methods=['POST'])
    app.add_url_rule('/issues', view_func=app__issues)
    app.add_url_rule('/issue/<int:issue_id>', view_func=app__issue)
    app.add_url_rule('/issue/purchase/<int:issue_id>', view_func=login_required(app__purchase_issue))
    app.add_url_rule('/issue/download/<int:issue_id>', view_func=app__download_issue)
    app.add_url_rule('/issue/toc/download/<int:issue_id>', view_func=app__download_issue_toc)
    app.add_url_rule('/article/<int:article_id>', view_func=app__article)
    app.add_url_rule('/article/download/<int:article_id>', view_func=app__download_article)
    app.add_url_rule('/static/uploads/<path:filename>', view_func=serve_static_uploads)
