# flake8: noqa
import os
import re
import time
from urllib.parse import urlparse, parse_qs
from flask import current_app, render_template, session, request, jsonify, flash, redirect, url_for, send_file, send_from_directory, abort
from extensions import dbc
from modules.translate import t, translate, clear_translations_cache
import settings
from utils.auth import is_valid_email, login_required, sanitize_input
from utils.emailer import send_notification_email
from utils.private_uploads import extract_private_upload_key
from utils.roles import hydrate_user_roles, user_has_role

EDITORIAL_MEMBER_TYPE_LABELS = {
    'en': {
        'editor_in_chief': "Editor-in-Chief",
        'deputy_editor': "Responsible Secretary",
        'editor': "Editor",
        'reviewer': "Scientific Editor",
        'advisory_member': "Layout Editor",
        'technical_editor': "Proofreader",
        'translator': "Translator",
    },
    'uz': {
        'editor_in_chief': "Bosh muharrir",
        'deputy_editor': "Mas'ul kotib",
        'editor': "Muharrir",
        'reviewer': "Ilmiy muharrir",
        'advisory_member': "Sahifalovchi",
        'technical_editor': "Musahhih",
        'translator': "Tarjimon",
    },
    'ru': {
        'editor_in_chief': "Главный редактор",
        'deputy_editor': "Ответственный секретарь",
        'editor': "Редактор",
        'reviewer': "Научный редактор",
        'advisory_member': "Редактор верстки",
        'technical_editor': "Корректор",
        'translator': "Переводчик",
    }
}
EDITORIAL_MEMBER_TYPE_ORDER = [
    'editor_in_chief',
    'deputy_editor',
    'editor',
    'reviewer',
    'advisory_member',
    'technical_editor',
    'translator',
]
EDITORIAL_UI_TEXTS = {
    'en': {
        'total_members': 'Total Members',
        'sections': 'Sections',
        'sections_title': 'Sections',
        'members_suffix': 'members',
        'empty': 'No editorial board members have been added yet.',
        'editor_fallback': 'Editor'
    },
    'uz': {
        'total_members': "Umumiy a'zolar",
        'sections': "Yo'nalishlar",
        'sections_title': "Bo'limlar",
        'members_suffix': "a'zo",
        'empty': "Hozircha tahrir hay'ati a'zolari qo'shilmagan.",
        'editor_fallback': "Tahrirchi"
    },
    'ru': {
        'total_members': 'Всего участников',
        'sections': 'Разделы',
        'sections_title': 'Разделы',
        'members_suffix': 'участников',
        'empty': 'Пока участники редакционной коллегии не добавлены.',
        'editor_fallback': 'Редактор'
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


def _parse_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _should_increment_article_view(article_id, ttl_seconds=6 * 60 * 60):
    if not article_id:
        return False
    viewed = session.get('article_views')
    if not isinstance(viewed, dict):
        viewed = {}
    now_ts = int(time.time())
    key = str(article_id)
    last_seen = _parse_int(viewed.get(key))
    if last_seen and (now_ts - last_seen) < ttl_seconds:
        return False
    viewed[key] = now_ts
    session['article_views'] = viewed
    session.modified = True
    return True


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
    if lang_text in {'uz', 'ru', 'en'}:
        localized = _get_site_setting(f"{base_key}_{lang_text}")
        if localized:
            return localized
    localized_exists = False
    for candidate_lang in ('uz', 'ru', 'en'):
        if _get_site_setting(f"{base_key}_{candidate_lang}"):
            localized_exists = True
            break
    if localized_exists:
        return ''
    return _get_site_setting(base_key)


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

    parsed = urlparse(url_text)
    host = (parsed.netloc or '').lower()
    path = (parsed.path or '').strip('/')
    video_id = ''

    if host in {'youtu.be', 'www.youtu.be'}:
        video_id = path.split('/')[0] if path else ''
    elif 'youtube.com' in host or 'youtube-nocookie.com' in host:
        if path.startswith('watch'):
            params = parse_qs(parsed.query or '')
            video_id = (params.get('v') or [''])[0]
        elif path.startswith('embed/'):
            video_id = path.split('/', 1)[1] if '/' in path else ''
        elif path.startswith('shorts/'):
            video_id = path.split('/', 1)[1] if '/' in path else ''

    if not video_id or not re.match(r'^[A-Za-z0-9_-]{6,}$', video_id):
        return ''

    return f"https://www.youtube.com/embed/{video_id}"


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
    return labels.get(key, labels.get('editor', 'Editor'))


def _normalize_editorial_member_type(member_type):
    key = (member_type or '').strip().lower()
    label_map = EDITORIAL_MEMBER_TYPE_LABELS.get('en', {})
    if key in label_map:
        return key
    return 'editor'


def _current_lang_code():
    lang = (session.get('language') or 'en').strip().lower()
    if lang not in {'uz', 'ru', 'en'}:
        return 'en'
    return lang


def _editorial_ui_texts():
    lang = _current_lang_code()
    return EDITORIAL_UI_TEXTS.get(lang, EDITORIAL_UI_TEXTS['en'])


def _issue_ui_texts():
    lang = _current_lang_code()
    return ISSUE_UI_TEXTS.get(lang, ISSUE_UI_TEXTS['en'])


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
            'members': members,
            'count': len(members)
        })

    for group_key, members in extra_grouped.items():
        if not members:
            continue
        groups.append({
            'key': group_key,
            'label': _editorial_member_type_label(group_key),
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
        _apply_localized_content(prepared_member, ('full_name', 'position', 'organization', 'biography'))

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

        normalized_type = _normalize_editorial_member_type(member.get('member_type'))
        member_type_label = _editorial_member_type_label(member.get('member_type'))
        prepared_member['full_name'] = full_name
        prepared_member['position'] = position
        prepared_member['organization'] = organization
        prepared_member['biography'] = biography
        prepared_member['member_type'] = normalized_type
        prepared_member['member_type_label'] = member_type_label
        prepared_member['title'] = position or member_type_label
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
    if editorial_members:
        return editorial_members

    try:
        raw_users = dbc.users.all().exec()
    except Exception:
        raw_users = []

    editors = [
        hydrate_user_roles(user)
        for user in raw_users
        if user_has_role(user, 'editor')
    ]

    prepared_editors = []
    for editor in editors:
        if editor.get('is_hidden') or editor.get('is_blocked'):
            continue
        translate(editor)
        full_name_parts = [
            (editor.get('name') or '').strip(),
            (editor.get('second_name') or '').strip(),
            (editor.get('father_name') or '').strip()
        ]
        full_name = ' '.join([part for part in full_name_parts if part]).strip()
        editor['full_name'] = full_name or editor.get('email') or 'Editor'
        editor['member_type'] = 'editor'
        editor['member_type_label'] = _editorial_member_type_label('editor')
        editor['title'] = (editor.get('position') or '').strip() or (editor.get('title') or '').strip()
        editor['sort_order'] = _parse_int(editor.get('sort_order')) or 0
        prepared_editors.append(editor)

    return sorted(
        prepared_editors,
        key=lambda item: (
            _parse_int(item.get('sort_order')) or 0,
            (item.get('full_name') or '').lower()
        )
    )


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
    latest_publications = dbc.publications.get().order_by('date_publish').per_page(8).page(1).exec()
    downloaded_publications = dbc.publications.get().order_by('stat_alt').per_page(8).page(1).exec()
    popular_publications = dbc.publications.get().order_by('stat_views').per_page(8).page(1).exec()
    news_items = dbc.news.get(type='news', status='published').order_by('published_at').per_page(4).page(1).exec()
    announcements = dbc.news.get(type='announcement', status='published').order_by('published_at').per_page(4).page(1).exec()
    featured_editor = _select_featured_editorial_member(_load_public_editorial_members())
    home_video_usage_url = _get_home_video_url('home_video_site_usage_url', current_lang)
    home_video_submission_url = _get_home_video_url('home_video_submission_url', current_lang)
    home_video_usage_embed = _youtube_embed_url(home_video_usage_url)
    home_video_submission_embed = _youtube_embed_url(home_video_submission_url)

    author_name_cache = {}

    def get_author_name(author_id):
        if not author_id:
            return None
        if author_id not in author_name_cache:
            author = dbc.author_profile.get(id=author_id).exec()
            author_name_cache[author_id] = translate(author[0]).get('name') if author else None
        return author_name_cache[author_id]

    def enrich_home_publication(pub):
        translate(pub)
        _apply_localized_content(pub, ('title', 'abstract', 'keywords'), lang=current_lang)
        pub['main_author_name'] = get_author_name(pub.get('main_author_id'))

        subauthor_names = []
        subauthor_ids = pub.get('subauthor_ids') or pub.get('sub_author_ids') or []
        for author_id in subauthor_ids:
            author_name = get_author_name(author_id)
            if author_name:
                subauthor_names.append(author_name)
        pub['subauthor_names'] = subauthor_names

        if pub.get('issue_id'):
            issue = dbc.issues.get(id=pub['issue_id']).exec()
            if issue:
                translated_issue = translate(issue[0])
                pub['issue'] = _apply_localized_content(translated_issue, ('title', 'shortinfo', 'price'), lang=current_lang)

    for publications in [latest_publications, downloaded_publications, popular_publications]:
        for pub in publications:
            enrich_home_publication(pub)

    for item in news_items + announcements:
        translate(item)

    return render_template(
        'index.html',
        latest_publications=latest_publications,
        downloaded_publications=downloaded_publications,
        popular_publications=popular_publications,
        news_items=news_items,
        announcements=announcements,
        featured_editor=featured_editor,
        home_video_usage_embed=home_video_usage_embed,
        home_video_submission_embed=home_video_submission_embed
    )


def app__editorial():
    editorial_ui = _editorial_ui_texts()
    prepared_editors = _load_public_editorial_members()
    editor_groups = _prepare_editorial_groups(prepared_editors)
    return render_template(
        'mainweb/editorial.html',
        editors=prepared_editors,
        editor_groups=editor_groups,
        total_editors=len(prepared_editors),
        total_groups=len(editor_groups),
        editorial_ui=editorial_ui
    )


def app__page_alias(alias):
    if alias == 'payment_guide':
        return redirect(url_for('app__payment_guide'))
    page = dbc.pages.get(alias=alias).exec()
    if not page:
        flash('Page not found', 'error')
        return redirect(url_for('app__index'))
    page = translate(page[0])
    return render_template('mainweb/page.html', page=page)


def app__payment_guide():
    lang = _current_lang_code()
    guide_html = _get_payment_guide_html(lang)
    page = {
        'title': t('payment_guide'),
        'content': guide_html
    }
    return render_template('mainweb/page.html', page=page)


def app__contact():
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
            lang = _current_lang_code()
            admin_subject = subject if len(subject) <= 120 else f"{subject[:117]}..."
            admin_title = (
                f'Yangi murojaat: {admin_subject}'
                if lang == 'uz'
                else f'Novoe obrashchenie: {admin_subject}'
                if lang == 'ru'
                else f'New contact request: {admin_subject}'
            )
            admin_intro = (
                'Saytdagi contact form orqali yangi xabar yuborildi.'
                if lang == 'uz'
                else 'Cherez kontaktnuyu formu sayta bylo otpravleno novoe soobshchenie.'
                if lang == 'ru'
                else 'A new message was sent through the website contact form.'
            )
            try:
                send_notification_email(
                    recipients=settings.MAIL_CONTACT_RECIPIENTS,
                    subject=admin_title,
                    intro=admin_intro,
                    details=[
                        ('Name', name),
                        ('Email', email),
                        ('Subject', subject),
                    ],
                    body_lines=[message],
                    reply_to=email,
                    fail_silently=False,
                )
            except Exception:
                current_app.logger.exception('Failed to deliver contact form email for %s', email)
                flash('Message could not be delivered right now. Please try again later.', 'error')
                return redirect(url_for('app__contact'))

            user_subject = (
                "Murojaatingiz qabul qilindi"
                if lang == 'uz'
                else 'Vashe soobshchenie polucheno'
                if lang == 'ru'
                else 'We received your message'
            )
            user_intro = (
                "Murojaatingiz Philology Matters jamoasiga yuborildi."
                if lang == 'uz'
                else 'Vashe soobshchenie bylo otpravleno komande Philology Matters.'
                if lang == 'ru'
                else 'Your message has been delivered to the Philology Matters team.'
            )
            user_body = (
                "Jamoamiz tez orada siz bilan bog'lanadi."
                if lang == 'uz'
                else 'Nasha komanda skoro svyazhetsya s vami.'
                if lang == 'ru'
                else 'Our team will get back to you soon.'
            )
            send_notification_email(
                recipients=[email],
                subject=user_subject,
                intro=user_intro,
                details=[('Subject', subject)],
                body_lines=[user_body],
                cta_url=url_for('app__contact'),
                cta_label='Open website',
                fail_silently=True,
            )
            flash('Message sent successfully', 'success')
        else:
            flash('All fields are required', 'error')
        return redirect(url_for('app__contact'))
    return render_template('mainweb/contact.html')


def app__articles():
    current_lang = _current_lang_code()
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

    parsed_issue_id = _parse_int(issue_filter)
    if issue_filter and parsed_issue_id is not None:
        query = query.equal(issue_id=parsed_issue_id)
    elif issue_filter:
        issue_filter = ''

    parsed_year = _parse_int(year_filter)
    if year_filter and parsed_year is not None:
        year_issues = dbc.issues.get(year=parsed_year).exec()
        if year_issues:
            issue_ids = [issue['id'] for issue in year_issues]
            query = query.any(issue_id=issue_ids)
        else:
            query = query.get(id=-1)
    elif year_filter:
        year_filter = ''

    if volume_filter:
        volume_issues = dbc.issues.get(vol_no=volume_filter).exec()
        if volume_issues:
            issue_ids = [issue['id'] for issue in volume_issues]
            query = query.any(issue_id=issue_ids)
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

    author_name_cache = {}
    issue_cache = {}
    references_count_cache = {}
    citations_count_cache = {}

    def get_author_name(author_id):
        if not author_id:
            return None
        if author_id not in author_name_cache:
            author_row = dbc.author_profile.get(id=author_id).exec()
            author_name_cache[author_id] = author_row[0].get('name') if author_row else None
        return author_name_cache[author_id]

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

    def publication_timestamp(pub):
        return _parse_int(pub.get('date_publish')) or _parse_int(pub.get('created_at')) or 0

    if sort_by == 'newest':
        publications = sorted(publications, key=publication_timestamp, reverse=True)
    elif sort_by == 'oldest':
        publications = sorted(publications, key=publication_timestamp)
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
    start = (page - 1) * per_page
    end = start + per_page
    publications = publications[start:end]

    processed_publications = []
    for pub in publications:
        author_names = []
        if pub['main_author_id']:
            main_author_name = get_author_name(pub['main_author_id'])
            if main_author_name:
                author_names.append(main_author_name)

        co_author_ids = pub.get('subauthor_ids') or pub.get('sub_author_ids') or []
        for author_id in co_author_ids:
            co_author_name = get_author_name(author_id)
            if co_author_name:
                author_names.append(co_author_name)

        issue = get_issue(pub['issue_id']) if pub.get('issue_id') else None
        references_count = get_references_count(pub['id'])
        citations_count = get_citations_count(pub['id'])

        processed_publications.append({
            'id': pub['id'],
            'title': pub['title'],
            'abstract': pub['abstract'],
            'authors': ', '.join(author_names),
            'date_publish': pub['date_publish'],
            'stat_views': pub.get('stat_views', 0),
            'stat_crossref': pub.get('stat_crossref', 0),
            'references_count': references_count,
            'citations_count': citations_count,
            'doi': pub.get('doi'),
            'keywords': pub.get('keywords', []),
            'is_paid': pub.get('is_paid', False),
            'subscription_enable': pub.get('subscription_enable', False),
            'issue': issue
        })

    all_issues = dbc.issues.get().order_by('year').exec()
    for issue in all_issues:
        translate(issue)
        _apply_localized_content(issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    all_volumes = sorted(list(set([issue['vol_no'] for issue in all_issues if issue['vol_no']])), reverse=True)
    all_years = sorted(list(set([issue['year'] for issue in all_issues if issue['year']])), reverse=True)

    return render_template('mainweb/articles.html',
                         publications=processed_publications,
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
                         per_page=per_page)


def app__news():
    page = request.args.get('page', 1, type=int)
    per_page = 12

    all_items = dbc.news.get(status='published').order_by('published_at').per_page(per_page).page(page).exec()
    news_items = dbc.news.get(type='news', status='published').order_by('published_at').exec()
    announcements = dbc.news.get(type='announcement', status='published').order_by('published_at').exec()

    for item in all_items + news_items + announcements:
        item = translate(item)

    return render_template('mainweb/news.html',
                         all_items=all_items,
                         news_items=news_items,
                         announcements=announcements)


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

    redirect_url = request.referrer
    if not redirect_url or 'change_language' in redirect_url:
        redirect_url = url_for('app__index')

    return redirect(redirect_url)


def app__issues():
    current_lang = _current_lang_code()
    year_filter = request.args.get('year')
    category_filter = request.args.get('category')
    access_filter = request.args.get('access')

    query = dbc.issues.get()

    if year_filter:
        query = query.equal(year=int(year_filter))

    if category_filter:
        query = query.equal(category=category_filter)

    if access_filter:
        if access_filter == 'free':
            query = query.equal(is_paid=False)
        elif access_filter == 'paid':
            query = query.equal(is_paid=True)
        elif access_filter == 'subscription':
            query = query.equal(subscription_enable=True)

    issues = query.order_by('year').exec()
    for issue in issues:
        translate(issue)
        _apply_localized_content(issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    issues = sorted(issues, key=lambda x: (x['year'], x['issue_no']), reverse=True)

    all_issues = dbc.issues.get().exec()
    available_years = sorted(set(issue['year'] for issue in all_issues), reverse=True)
    available_categories = dbc.fix_issue_categories.get().exec()
    for cat in available_categories:
        translate(cat)
    return render_template('mainweb/issues.html',
                         issues=issues,
                         available_years=available_years,
                         available_categories=available_categories,
                         current_filters={
                             'year': year_filter,
                             'category': category_filter,
                             'access': access_filter
                         })


def app__issue(issue_id):
    current_lang = _current_lang_code()
    issue = dbc.issues.get(id=issue_id).exec()
    if not issue:
        flash('Issue not found', 'error')
        return redirect(url_for('app__issues'))

    issue = issue[0]

    all_issues = dbc.issues.get().exec()
    for list_issue in all_issues:
        _apply_localized_content(list_issue, ('title', 'shortinfo', 'price'), lang=current_lang)
    all_issues = sorted(all_issues, key=lambda x: (x['year'], x['issue_no']))

    current_index = None
    for i, curr_issue in enumerate(all_issues):
        if curr_issue['id'] == issue_id:
            current_index = i
            break

    prev_issue = all_issues[current_index - 1] if current_index > 0 else None
    next_issue = all_issues[current_index + 1] if current_index < len(all_issues) - 1 else None

    has_access = False
    if 'user_id' in session:
        user = dbc.users.get(id=session['user_id']).exec()[0]
        if user.get('subscription_end_date') and user['subscription_end_date'] > int(time.time()):
            has_access = True
        else:
            payments = dbc.payments.get(user_id=session['user_id'], status='paid').exec()
            for payment in payments:
                if payment['payment_type'] == 'issue' and payment['ids'] and issue_id in payment['ids']:
                    has_access = True
                    break

    publications = dbc.publications.get(issue_id=issue_id).exec()
    articles = []

    if publications:
        for pub in publications:
            translate(pub)
            _apply_localized_content(pub, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)
            main_author = None
            if pub['main_author_id']:
                main_authors = dbc.author_profile.get(id=pub['main_author_id']).exec()
                if main_authors:
                    main_author = main_authors[0]

            co_authors = []
            if pub['subauthor_ids']:
                for author_id in pub['subauthor_ids']:
                    co_authors_result = dbc.author_profile.get(id=author_id).exec()
                    if co_authors_result:
                        co_authors.append(co_authors_result[0])

            authors = main_author['name'] if main_author else ''
            if co_authors:
                if authors:
                    authors += ', '
                authors += ', '.join(author['name'] for author in co_authors)

            articles.append({
                'id': pub['id'],
                'title': pub['title'],
                'authors': authors
            })
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
                         issue_shortinfo=issue_shortinfo,
                         issue_ui=issue_ui)


def app__purchase_issue(issue_id):
    return redirect(url_for('app__issues'))


def _normalize_currency(currency):
    normalized = (currency or 'usd').strip().lower()
    if normalized in {'usd', 'uzs', 'rub'}:
        return normalized
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

    publication = translate(publication[0])
    _apply_localized_content(publication, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)

    if not publication.get('is_paid'):
        return redirect(url_for('app__article', article_id=article_id))

    has_access = False
    user_rows = dbc.users.get(id=user_id).exec()
    user = user_rows[0] if user_rows else {}
    if user.get('subscription_end_date') and user['subscription_end_date'] > int(time.time()):
        has_access = True
    else:
        payments = dbc.payments.get(user_id=user_id, status='paid').exec()
        for payment in payments:
            if payment.get('payment_type') == 'article' and payment.get('ids') and article_id in payment['ids']:
                has_access = True
                break

    if has_access:
        return redirect(url_for('app__article', article_id=article_id))

    currency = _normalize_currency(request.args.get('currency', 'usd'))
    amount = _resolve_publication_price_local(publication, currency)
    guide_html = _get_payment_guide_html(current_lang)

    return render_template(
        'mainweb/purchase_article.html',
        publication=publication,
        amount=amount,
        currency=currency,
        guide_html=guide_html
    )


def app__article(article_id):
    current_lang = _current_lang_code()
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = translate(publication[0])
    _apply_localized_content(publication, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)
    references_count = len(dbc.publication_refs.get(publication_id=article_id).exec())
    citations_count = len(dbc.publication_citations.get(publication_id=article_id).exec())
    publication['references_count'] = references_count
    publication['citations_count'] = citations_count
    if _should_increment_article_view(article_id):
        new_views = (publication.get('stat_views') or 0) + 1
        try:
            dbc.publications.get(id=article_id).update(stat_views=new_views).exec()
            publication['stat_views'] = new_views
        except Exception:
            current_app.logger.exception('Failed to update view count for article %s', article_id)
    has_access = True
    if publication.get('is_paid'):
        has_access = False
        user_id = session.get('user_id')
        if user_id:
            user_rows = dbc.users.get(id=user_id).exec()
            user = user_rows[0] if user_rows else {}
            if user.get('subscription_end_date') and user['subscription_end_date'] > int(time.time()):
                has_access = True
            else:
                payments = dbc.payments.get(user_id=user_id, status='paid').exec()
                for payment in payments:
                    if payment.get('payment_type') == 'article' and payment.get('ids') and article_id in payment['ids']:
                        has_access = True
                        break

    main_author = None
    if publication['main_author_id']:
        main_author = dbc.author_profile.get(id=publication['main_author_id']).exec()
        if main_author:
            main_author = translate(main_author[0])

    co_authors = []
    if publication['subauthor_ids']:
        for author_id in publication['subauthor_ids']:
            co_author = dbc.author_profile.get(id=author_id).exec()
            if co_author:
                co_authors.append(translate(co_author[0]))

    issue = None
    if publication['issue_id']:
        issue_data = dbc.issues.get(id=publication['issue_id']).exec()
        if issue_data:
            translated_issue = translate(issue_data[0])
            issue = _apply_localized_content(translated_issue, ('title', 'shortinfo', 'price'), lang=current_lang)

    parts = []
    figures = []
    references = []
    citations = []
    if not publication.get('is_paid') or has_access:
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
                         has_access=has_access,
                         main_author=main_author,
                         co_authors=co_authors,
                         issue=issue,
                         publication_parts=parts,
                         publication_figures=figures,
                         publication_refs=references,
                         publication_citations=citations)


def app__download_article(article_id):
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = publication[0]

    if publication['is_paid']:
        if 'user_id' not in session:
            flash('Please log in to download this article', 'error')
            return redirect(url_for('app__login'))

        user = dbc.users.get(id=session['user_id']).exec()[0]
        has_access = False
        if user.get('subscription_end_date') and user['subscription_end_date'] > int(time.time()):
            has_access = True
        else:
            payments = dbc.payments.get(user_id=session['user_id'], status='paid').exec()
            for payment in payments:
                if payment['payment_type'] == 'article' and payment['ids'] and article_id in payment['ids']:
                    has_access = True
                    break

        if not has_access:
            flash('Access denied. Please purchase or subscribe.', 'error')
            return redirect(url_for('app__article', article_id=article_id))

    if not publication.get('file_ids'):
        flash('Article file not found', 'error')
        return redirect(url_for('app__article', article_id=article_id))

    file_ids = publication.get('file_ids') or []
    selected_file_path = None
    selected_download_name = None

    # Prefer the most recently attached file and gracefully skip stale file_ids.
    for file_id in reversed(file_ids):
        file_record_rows = dbc.files.get(id=file_id).exec()
        if not file_record_rows:
            continue

        file_record = file_record_rows[0]
        stored_filepath = (file_record.get('filepath') or '').strip()
        if not stored_filepath:
            continue

        file_path = os.path.join(settings.SAVE_PATH, stored_filepath.lstrip('/'))
        if not os.path.exists(file_path):
            continue

        selected_file_path = file_path
        selected_download_name = (file_record.get('name') or '').strip() or f"{publication['title']}.pdf"
        break

    if not selected_file_path:
        flash('Article file not found', 'error')
        return redirect(url_for('app__article', article_id=article_id))

    try:
        new_downloads = (publication.get('stat_alt') or 0) + 1
        dbc.publications.get(id=article_id).update(stat_alt=new_downloads).exec()
    except Exception:
        current_app.logger.exception('Failed to update download count for article %s', article_id)

    return send_file(selected_file_path,
                    as_attachment=True,
                    download_name=selected_download_name)


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
    app.add_url_rule('/change_language/<string:lang>', view_func=app__change_language)
    app.add_url_rule('/issues', view_func=app__issues)
    app.add_url_rule('/issue/<int:issue_id>', view_func=app__issue)
    app.add_url_rule('/issue/purchase/<int:issue_id>', view_func=login_required(app__purchase_issue))
    app.add_url_rule('/article/<int:article_id>', view_func=app__article)
    app.add_url_rule('/article/download/<int:article_id>', view_func=app__download_article)
    app.add_url_rule('/static/uploads/<path:filename>', view_func=serve_static_uploads)
