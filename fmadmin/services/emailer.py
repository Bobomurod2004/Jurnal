"""
Fmadmin Email Service Wrapper

This is a thin wrapper around the shared EmailService.
All email functionality is now centralized in shared/email/email_service.py
"""

import logging
from flask import current_app

try:
    import fmadmin.settings as settings
except ImportError:
    import settings

from extensions import db
from shared.email.email_service import EmailService

logger = logging.getLogger(__name__)

# Create email service instance
_email_service = None


def _get_email_service():
    """Get or create email service instance."""
    global _email_service

    if _email_service is None:
        _email_service = EmailService(db, settings, app_name='fmadmin')

    return _email_service


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
    """
    Send notification email.

    This is a wrapper function that delegates to shared EmailService.

    Args:
        recipients: Email address(es) - string or list
        subject: Email subject
        intro: Introduction text
        details: List of (label, value) tuples
        body_lines: List of body text lines
        cta_url: Call-to-action button URL
        cta_label: Call-to-action button text
        reply_to: Reply-to email address
        fail_silently: If True, don't raise exceptions
        template_alias: Template alias for DB templates
        template_vars: Template variables (for future template system)
        preferred_language: Preferred language (for future template system)

    Returns:
        bool: True if sent successfully
    """
    service = _get_email_service()

    # Get Jinja2 environment from Flask app
    jinja_env = current_app.jinja_env if current_app else None

    # Note: template_vars and preferred_language are not yet implemented
    # in the shared EmailService, but parameters are kept for compatibility

    return service.send_notification_email(
        recipients=recipients,
        subject=subject,
        intro=intro,
        details=details,
        body_lines=body_lines,
        cta_url=cta_url,
        cta_label=cta_label,
        reply_to=reply_to,
        fail_silently=fail_silently,
        template_alias=template_alias,
        jinja_env=jinja_env,
    )
