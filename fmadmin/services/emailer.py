import logging
import smtplib
import re
from email.message import EmailMessage
from email.utils import formataddr
from urllib.parse import urljoin

from flask import current_app

try:
    import fmadmin.settings as settings
except ImportError:
    import settings
from extensions import db

logger = logging.getLogger(__name__)
EMAIL_TEMPLATE_VAR_PATTERN = re.compile(r'{{\s*([a-zA-Z0-9_]+)\s*}}')


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


def _normalize_template_alias(alias):
    value = _clean_text(alias).lower()
    value = re.sub(r'[^a-z0-9_]+', '_', value)
    return re.sub(r'_+', '_', value).strip('_')


def _normalize_template_vars(template_vars):
    if not isinstance(template_vars, dict):
        return {}
    normalized = {}
    for key, value in template_vars.items():
        normalized_key = _normalize_template_alias(key)
        if not normalized_key:
            continue
        normalized[normalized_key] = _clean_text(value)
    return normalized


def _apply_template_vars(raw_text, template_vars):
    text = _clean_text(raw_text)
    if not text:
        return ''

    vars_map = _normalize_template_vars(template_vars)
    if not vars_map:
        return text

    def _replace(match):
        key = _normalize_template_alias(match.group(1))
        if key in vars_map:
            return vars_map[key]
        return match.group(0)

    return EMAIL_TEMPLATE_VAR_PATTERN.sub(_replace, text)


def _load_email_template(alias):
    normalized_alias = _normalize_template_alias(alias)
    if not normalized_alias:
        return None
    try:
        rows = (
            db.email_templates.all()
            .equal(alias=normalized_alias)
            .equal(is_active=True)
            .exec()
        )
        return rows[0] if rows else None
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return None


def _localized_template_field(template_row, base_name, language):
    lang = _clean_text(language).lower()
    if lang not in {'uz', 'ru', 'en'}:
        lang = 'uz'

    value = _clean_text((template_row or {}).get(f'{base_name}_{lang}'))
    if value:
        return value

    for fallback_lang in ('uz', 'ru', 'en'):
        value = _clean_text(
            (template_row or {}).get(f'{base_name}_{fallback_lang}')
        )
        if value:
            return value
    return ''


def _absolute_url(path):
    base_url = (settings.APP_BASE_URL or '').rstrip('/') + '/'
    value = _clean_text(path)
    if not value:
        return settings.APP_BASE_URL
    if value.startswith('http://') or value.startswith('https://'):
        return value
    return urljoin(base_url, value.lstrip('/'))


def _build_context(
    subject,
    intro,
    details=None,
    body_lines=None,
    cta_url=None,
    cta_label=None,
):
    return {
        'subject': _clean_text(subject),
        'intro': _clean_text(intro),
        'details': _normalize_details(details),
        'body_lines': _normalize_body_lines(body_lines),
        'cta_url': _absolute_url(cta_url) if cta_url else '',
        'cta_label': _clean_text(cta_label) or 'Open',
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
        client = smtplib.SMTP_SSL(
            host,
            settings.MAIL_PORT,
            timeout=settings.MAIL_TIMEOUT,
        )
    else:
        client = smtplib.SMTP(
            host,
            settings.MAIL_PORT,
            timeout=settings.MAIL_TIMEOUT,
        )
        client.ehlo()
        if settings.MAIL_USE_TLS:
            client.starttls()
            client.ehlo()

    if settings.MAIL_USERNAME:
        client.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
    return client


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
    template_vars=None,
    preferred_language='uz',
):
    normalized_recipients = _normalize_recipients(recipients)
    if not normalized_recipients:
        return False

    if not settings.MAIL_ENABLED:
        logger.info('Email delivery is disabled; skipped subject=%s', subject)
        return False

    resolved_subject = _clean_text(subject)
    resolved_intro = _clean_text(intro)
    resolved_body_lines = _normalize_body_lines(body_lines)
    resolved_cta_label = _clean_text(cta_label) or 'Open'

    template_row = _load_email_template(template_alias)
    if template_row:
        template_subject = _localized_template_field(
            template_row,
            'subject',
            preferred_language,
        )
        template_intro = _localized_template_field(
            template_row,
            'intro',
            preferred_language,
        )
        template_body = _localized_template_field(
            template_row,
            'body',
            preferred_language,
        )
        template_cta_label = _localized_template_field(
            template_row,
            'cta_label',
            preferred_language,
        )

        resolved_subject = _apply_template_vars(
            template_subject or resolved_subject,
            template_vars,
        )
        resolved_intro = _apply_template_vars(
            template_intro or resolved_intro,
            template_vars,
        )
        if template_body:
            rendered_body = _apply_template_vars(template_body, template_vars)
            body_rows = [
                row.strip()
                for row in rendered_body.splitlines()
                if row.strip()
            ]
            resolved_body_lines = body_rows + resolved_body_lines
        resolved_cta_label = _apply_template_vars(
            template_cta_label or resolved_cta_label,
            template_vars,
        )

    context = _build_context(
        subject=resolved_subject,
        intro=resolved_intro,
        details=details,
        body_lines=resolved_body_lines,
        cta_url=cta_url,
        cta_label=resolved_cta_label,
    )

    try:
        text_body = _render_email_template(
            'emails/generic_notification.txt',
            context,
        )
        html_body = _render_email_template(
            'emails/generic_notification.html',
            context,
        )
        if settings.MAIL_SUPPRESS_SEND:
            logger.info(
                (
                    'MAIL_SUPPRESS_SEND enabled; '
                    'skipped email subject=%s recipients=%s'
                ),
                subject,
                normalized_recipients,
            )
            return True

        with _open_connection() as client:
            for recipient in normalized_recipients:
                message = EmailMessage()
                message['Subject'] = resolved_subject
                message['From'] = formataddr(
                    (settings.MAIL_FROM_NAME, settings.MAIL_FROM_EMAIL)
                )
                message['To'] = recipient
                if reply_to or settings.MAIL_REPLY_TO:
                    message['Reply-To'] = _clean_text(
                        reply_to or settings.MAIL_REPLY_TO
                    )
                message.set_content(text_body)
                message.add_alternative(html_body, subtype='html')
                client.send_message(message)

        logger.info(
            'Email sent subject=%s recipients=%s',
            resolved_subject,
            normalized_recipients,
        )
        return True
    except Exception:
        logger.exception(
            'Failed to send email subject=%s recipients=%s',
            subject,
            normalized_recipients,
        )
        if fail_silently:
            return False
        raise
