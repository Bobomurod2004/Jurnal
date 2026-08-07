"""Off-request email delivery.

SMTP is slow and unreliable: with `MAIL_TIMEOUT` at 15s and three retry
attempts (2s + 4s backoff) a single send can hold a Gunicorn worker thread for
roughly 50 seconds.  Because the workers run `--threads N`, a handful of stuck
sends is enough to starve the whole application.

Notification emails carry nothing the caller needs back, so they are handed to
a small thread pool and the request returns immediately.  Emails the user is
actively waiting for -- verification codes above all -- must keep going out
synchronously, so that a delivery failure can still be reported on the page.

The worker pushes an application context because the shared EmailService
renders `emails/generic_notification.{html,txt}` through the app's Jinja
environment.  Those two templates do not touch `request` or `session`, so an
app context (no request context) is all they need.
"""
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

DEFAULT_MAX_WORKERS = 4

_executor = None
_executor_lock = threading.Lock()


def _max_workers():
    try:
        configured = int(os.getenv('MAIL_BACKGROUND_WORKERS', '') or DEFAULT_MAX_WORKERS)
    except (TypeError, ValueError):
        return DEFAULT_MAX_WORKERS
    return max(1, configured)


def _get_executor():
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = ThreadPoolExecutor(
                    max_workers=_max_workers(),
                    thread_name_prefix='email-bg',
                )
    return _executor


def dispatch(app, send_callable, description=''):
    """Run `send_callable` on a worker thread bound to `app`'s context.

    Returns True once the send is queued.  Delivery failures are logged, not
    raised -- the request that queued the email is long gone by then, which is
    why only `fail_silently` senders belong here.

    With no application to bind to (scripts, tests) the callable runs inline so
    behaviour stays predictable.
    """
    if app is None:
        return send_callable()

    def _run():
        try:
            with app.app_context():
                send_callable()
        except Exception:
            logger.exception("Background email delivery failed (%s)", description)

    try:
        _get_executor().submit(_run)
    except RuntimeError:
        # Interpreter is shutting down and the pool refuses new work; sending
        # inline is better than dropping the message.
        logger.warning("Email thread pool unavailable, sending inline (%s)", description)
        return send_callable()

    return True
