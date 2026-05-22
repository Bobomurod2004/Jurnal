import logging
import re
import smtplib
import time
from email.message import EmailMessage
from email.utils import formataddr
from urllib.parse import urljoin

from flask import current_app

try:
    import mainweb.settings as settings
except ImportError:
    import settings

try:
    from extensions import dbc
except Exception:
    dbc = None

logger = logging.getLogger(__name__)
EMAIL_LOG_TABLE_READY = False
LANGUAGE_MARKER_PATTERN = re.compile(r'\[(UZ|RU|EN)\]\s*', re.IGNORECASE)
LANGUAGE_SECTION_ORDER = (
    ('uz', 'Uzbek'),
    ('ru', 'Russian'),
    ('en', 'English'),
)


def _clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _normalize_recipients(recipients):
    if not recipients:
        return []
    if isinstance(recipients, str):
        raw_items = recipients.split(',')
    else:
        raw_items = recipients

    normalized = []
    seen = set()
    for item in raw_items:
        email = _clean_text(item).lower()
        if not email or email in seen:
            continue
        seen.add(email)
        normalized.append(email)
    return normalized


def _normalize_details(details):
    rows = []
    for label, value in details or []:
        label_text = _clean_text(label)
        value_text = _clean_text(value)
        if not label_text or not value_text:
            continue
        rows.append({'label': label_text, 'value': value_text})
    return rows


def _normalize_body_lines(lines):
    rows = []
    for line in lines or []:
        value = _clean_text(line)
        if value:
            rows.append(value)
    return rows


def _first_nonempty(values):
    for value in values or []:
        text = _clean_text(value)
        if text:
            return text
    return ''


def _extract_multilingual_map(raw_text, separators=(' | ',)):
    text = _clean_text(raw_text)
    if not text:
        return {}, ''

    matches = list(LANGUAGE_MARKER_PATTERN.finditer(text))
    if matches:
        language_map = {}
        for index, match in enumerate(matches):
            language_code = match.group(1).lower()
            start_index = match.end()
            end_index = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            segment = text[start_index:end_index].strip(" \t\r\n|/-")
            if segment:
                language_map[language_code] = segment
        if language_map:
            return language_map, ''

    for separator in separators:
        if separator not in text:
            continue
        parts = [part.strip() for part in text.split(separator) if part.strip()]
        if len(parts) == len(LANGUAGE_SECTION_ORDER):
            return {
                language_code: parts[index]
                for index, (language_code, _label) in enumerate(LANGUAGE_SECTION_ORDER)
            }, ''

    return {}, text


def _new_language_section(language_code, label):
    return {
        'code': language_code,
        'label': label,
        'subject': '',
        'intro': '',
        'details': [],
        'body_lines': [],
        'cta_label': '',
    }


def _append_unique_detail(section, label, value):
    label_text = _clean_text(label)
    value_text = _clean_text(value)
    if not label_text or not value_text:
        return
    detail_row = {'label': label_text, 'value': value_text}
    if detail_row not in section['details']:
        section['details'].append(detail_row)


def _append_unique_body_line(section, line):
    line_text = _clean_text(line)
    if not line_text:
        return
    if line_text not in section['body_lines']:
        section['body_lines'].append(line_text)


def _has_section_content(section):
    return bool(
        _clean_text(section.get('subject'))
        or _clean_text(section.get('intro'))
        or _clean_text(section.get('cta_label'))
        or section.get('details')
        or section.get('body_lines')
    )


def _build_language_sections(subject, intro, details, body_lines, cta_label):
    sections = {
        language_code: _new_language_section(language_code, label)
        for language_code, label in LANGUAGE_SECTION_ORDER
    }
    common_content = {
        'subject': '',
        'intro': '',
        'cta_label': '',
        'details': [],
        'body_lines': [],
    }

    subject_map, common_subject = _extract_multilingual_map(subject)
    intro_map, common_intro = _extract_multilingual_map(intro)
    cta_map, common_cta = _extract_multilingual_map(cta_label, separators=(' / ', ' | '))

    for language_code, section in sections.items():
        section['subject'] = _clean_text(subject_map.get(language_code))
        section['intro'] = _clean_text(intro_map.get(language_code))
        section['cta_label'] = _clean_text(cta_map.get(language_code))

    common_content['subject'] = _clean_text(common_subject)
    common_content['intro'] = _clean_text(common_intro)
    common_content['cta_label'] = _clean_text(common_cta)

    for item in details or []:
        label_map, common_label = _extract_multilingual_map(
            item.get('label'),
            separators=(' / ', ' | '),
        )
        value_map, common_value = _extract_multilingual_map(
            item.get('value'),
            separators=(' / ', ' | '),
        )
        if label_map or value_map:
            for language_code, section in sections.items():
                fallback_label = common_label or _first_nonempty(label_map.values())
                fallback_value = common_value or _first_nonempty(value_map.values())
                resolved_label = label_map.get(language_code) or fallback_label
                resolved_value = value_map.get(language_code) or fallback_value
                _append_unique_detail(section, resolved_label, resolved_value)
            continue

        _append_unique_detail(
            common_content,
            common_label,
            common_value,
        )

    active_language = None
    for line in body_lines or []:
        line_text = _clean_text(line)
        if not line_text:
            continue

        marker_match = re.fullmatch(r'\[(UZ|RU|EN)\]', line_text, re.IGNORECASE)
        if marker_match:
            active_language = marker_match.group(1).lower()
            continue

        line_map, common_line = _extract_multilingual_map(line_text)
        if line_map:
            for language_code, value in line_map.items():
                _append_unique_body_line(sections[language_code], value)
            active_language = None
            continue

        if active_language in sections:
            _append_unique_body_line(sections[active_language], common_line or line_text)
        else:
            _append_unique_body_line(common_content, common_line or line_text)

    for language_code, section in sections.items():
        if common_content['subject'] and not section['subject']:
            section['subject'] = common_content['subject']
        if common_content['intro'] and not section['intro']:
            section['intro'] = common_content['intro']
        if common_content['cta_label'] and not section['cta_label']:
            section['cta_label'] = common_content['cta_label']
        for detail_row in common_content['details']:
            _append_unique_detail(section, detail_row.get('label'), detail_row.get('value'))
        for line_text in common_content['body_lines']:
            _append_unique_body_line(section, line_text)

    active_sections = [
        sections[language_code]
        for language_code, _label in LANGUAGE_SECTION_ORDER
        if _has_section_content(sections[language_code])
    ]
    return active_sections


def _absolute_url(path):
    base_url = (settings.APP_BASE_URL or '').rstrip('/') + '/'
    value = _clean_text(path)
    if not value:
        return settings.APP_BASE_URL
    if value.startswith('http://') or value.startswith('https://'):
        return value
    return urljoin(base_url, value.lstrip('/'))


def _build_context(subject, intro, details=None, body_lines=None, cta_url=None, cta_label=None):
    normalized_subject = _clean_text(subject)
    normalized_intro = _clean_text(intro)
    normalized_details = _normalize_details(details)
    normalized_body_lines = _normalize_body_lines(body_lines)
    normalized_cta_label = _clean_text(cta_label) or 'Open'
    language_sections = _build_language_sections(
        normalized_subject,
        normalized_intro,
        normalized_details,
        normalized_body_lines,
        normalized_cta_label,
    )
    is_multilingual = len(language_sections) > 1
    headline_subject = normalized_subject
    if is_multilingual:
        for section in language_sections:
            section_subject = _clean_text(section.get('subject'))
            if section_subject:
                headline_subject = section_subject
                break

    return {
        'subject': normalized_subject,
        'headline_subject': headline_subject,
        'intro': normalized_intro,
        'details': normalized_details,
        'body_lines': normalized_body_lines,
        'is_multilingual': is_multilingual,
        'language_sections': language_sections,
        'cta_url': _absolute_url(cta_url) if cta_url else '',
        'cta_label': normalized_cta_label,
        'signature_name': settings.MAIL_FROM_NAME,
        'app_base_url': settings.APP_BASE_URL,
    }


def _render_email_template(template_name, context):
    template = current_app.jinja_env.get_or_select_template(template_name)
    return template.render(**context)


def _open_connection():
    host = _clean_text(settings.MAIL_HOST)
    if not host:
        raise RuntimeError('MAIL_HOST is not configured')

    if settings.MAIL_USE_SSL:
        client = smtplib.SMTP_SSL(host, settings.MAIL_PORT, timeout=settings.MAIL_TIMEOUT)
    else:
        client = smtplib.SMTP(host, settings.MAIL_PORT, timeout=settings.MAIL_TIMEOUT)
        client.ehlo()
        if settings.MAIL_USE_TLS:
            client.starttls()
            client.ehlo()

    if settings.MAIL_USERNAME:
        client.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
    return client


def _ensure_email_delivery_logs_table():
    global EMAIL_LOG_TABLE_READY
    if EMAIL_LOG_TABLE_READY:
        return True

    conn = getattr(dbc, 'conn', None) if dbc is not None else None
    if conn is None:
        return False

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS email_delivery_logs (
                id SERIAL PRIMARY KEY,
                app TEXT NOT NULL,
                recipient_email TEXT,
                subject TEXT,
                status TEXT NOT NULL,
                template_alias TEXT,
                error_text TEXT,
                created_at BIGINT NOT NULL DEFAULT EXTRACT(epoch FROM now())
            );
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_email_delivery_logs_created_at "
            "ON email_delivery_logs(created_at DESC, id DESC);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_email_delivery_logs_status "
            "ON email_delivery_logs(status);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_email_delivery_logs_recipient "
            "ON email_delivery_logs(recipient_email);"
        )
        conn.commit()
        EMAIL_LOG_TABLE_READY = True
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("Failed to ensure email_delivery_logs table in mainweb")
        return False
    finally:
        if cursor is not None:
            cursor.close()


def _log_email_delivery(status, subject, recipients=None, template_alias=None, error_text=None):
    if not _ensure_email_delivery_logs_table():
        return False

    conn = getattr(dbc, 'conn', None) if dbc is not None else None
    if conn is None:
        return False

    rows = _normalize_recipients(recipients)
    if not rows:
        rows = [None]

    normalized_status = _clean_text(status).lower() or 'unknown'
    normalized_subject = _clean_text(subject)
    normalized_template_alias = _clean_text(template_alias) or None
    normalized_error_text = _clean_text(error_text) or None
    now_ts = int(time.time())

    cursor = None
    try:
        cursor = conn.cursor()
        for recipient in rows:
            cursor.execute(
                """
                INSERT INTO email_delivery_logs (
                    app,
                    recipient_email,
                    subject,
                    status,
                    template_alias,
                    error_text,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    'mainweb',
                    recipient,
                    normalized_subject,
                    normalized_status,
                    normalized_template_alias,
                    normalized_error_text,
                    now_ts,
                ),
            )
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception(
            "Failed to persist email delivery log status=%s subject=%s",
            normalized_status,
            normalized_subject,
        )
        return False
    finally:
        if cursor is not None:
            cursor.close()


def send_notification_email(
    recipients,
    subject,
    intro,
    details=None,
    body_lines=None,
    cta_url=None,
    cta_label=None,
    reply_to=None,
    fail_silently=True,
    template_alias=None,
):
    normalized_recipients = _normalize_recipients(recipients)
    if not normalized_recipients:
        _log_email_delivery(
            status='skipped_no_recipient',
            subject=subject,
            recipients=[],
            template_alias=template_alias,
        )
        return False

    if not settings.MAIL_ENABLED:
        logger.info('Email delivery is disabled; skipped subject=%s', subject)
        _log_email_delivery(
            status='skipped_mail_disabled',
            subject=subject,
            recipients=normalized_recipients,
            template_alias=template_alias,
        )
        return False

    context = _build_context(
        subject=subject,
        intro=intro,
        details=details,
        body_lines=body_lines,
        cta_url=cta_url,
        cta_label=cta_label,
    )

    try:
        text_body = _render_email_template('emails/generic_notification.txt', context)
        html_body = _render_email_template('emails/generic_notification.html', context)
        if settings.MAIL_SUPPRESS_SEND:
            logger.info(
                'MAIL_SUPPRESS_SEND enabled; skipped email subject=%s recipients=%s',
                subject,
                normalized_recipients,
            )
            _log_email_delivery(
                status='skipped_suppressed',
                subject=subject,
                recipients=normalized_recipients,
                template_alias=template_alias,
            )
            return True

        with _open_connection() as client:
            for recipient in normalized_recipients:
                message = EmailMessage()
                message['Subject'] = _clean_text(subject)
                message['From'] = formataddr((settings.MAIL_FROM_NAME, settings.MAIL_FROM_EMAIL))
                message['To'] = recipient
                if reply_to or settings.MAIL_REPLY_TO:
                    message['Reply-To'] = _clean_text(reply_to or settings.MAIL_REPLY_TO)
                message.set_content(text_body)
                message.add_alternative(html_body, subtype='html')
                client.send_message(message)

        logger.info('Email sent subject=%s recipients=%s', subject, normalized_recipients)
        _log_email_delivery(
            status='sent',
            subject=subject,
            recipients=normalized_recipients,
            template_alias=template_alias,
        )
        return True
    except Exception as exc:
        logger.exception('Failed to send email subject=%s recipients=%s', subject, normalized_recipients)
        _log_email_delivery(
            status='failed',
            subject=subject,
            recipients=normalized_recipients,
            template_alias=template_alias,
            error_text=str(exc),
        )
        if fail_silently:
            return False
        raise
