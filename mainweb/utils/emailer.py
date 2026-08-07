"""
Mainweb Email Service Wrapper

This is a thin wrapper around the shared EmailService.
All email functionality is now centralized in shared/email/email_service.py
"""

import logging
from flask import current_app

try:
    import mainweb.settings as settings
except ImportError:
    import settings

try:
    from extensions import dbc
except Exception:
    dbc = None

from shared.email.email_service import EmailService
from shared.email.background import dispatch as dispatch_email

logger = logging.getLogger(__name__)

# Create email service instance
_email_service = None


def _get_email_service():
    """Get or create email service instance."""
    global _email_service

    if _email_service is None:
        if dbc is None:
            raise RuntimeError("Database connector not available")
        _email_service = EmailService(dbc, settings, app_name='mainweb')

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
    background=False,
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
        background: If True, deliver off-request and return immediately.
            Only for mail nobody is waiting on -- a verification code must
            stay synchronous so a failure can still be shown to the user.

    Returns:
        bool: True if sent successfully (or, in background mode, if queued)
    """
    service = _get_email_service()

    # Get Jinja2 environment from Flask app
    jinja_env = current_app.jinja_env if current_app else None

    def _send(env=jinja_env):
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
            jinja_env=env,
        )

    if background:
        app = current_app._get_current_object() if current_app else None
        # The captured jinja_env belongs to this app, so the worker reuses it.
        return dispatch_email(app, _send, description=subject)

    return _send()
