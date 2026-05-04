import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from urllib.parse import urljoin

from flask import current_app

try:
    import mainweb.settings as settings
except ImportError:
    import settings

logger = logging.getLogger(__name__)


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


def _absolute_url(path):
    base_url = (settings.APP_BASE_URL or '').rstrip('/') + '/'
    value = _clean_text(path)
    if not value:
        return settings.APP_BASE_URL
    if value.startswith('http://') or value.startswith('https://'):
        return value
    return urljoin(base_url, value.lstrip('/'))


def _build_context(subject, intro, details=None, body_lines=None, cta_url=None, cta_label=None):
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
):
    normalized_recipients = _normalize_recipients(recipients)
    if not normalized_recipients:
        return False

    if not settings.MAIL_ENABLED:
        logger.info('Email delivery is disabled; skipped subject=%s', subject)
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
        return True
    except Exception:
        logger.exception('Failed to send email subject=%s recipients=%s', subject, normalized_recipients)
        if fail_silently:
            return False
        raise
