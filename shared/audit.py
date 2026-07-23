"""Security-focused, append-only audit events for the two Flask services."""

import logging
import re
import time

from shared.observability import record_audit_event_metric

logger = logging.getLogger(__name__)

_SENSITIVE_ROUTE_MARKERS = (
    'login', 'logout', 'register', 'password', 'oauth', 'orcid', 'google',
    'submission', 'editor-assignment', 'payment', 'upload', 'users',
    'articles', 'issues', 'pages', 'translations', 'email-templates',
)
_SKIPPED_ROUTE_PREFIXES = ('/metrics', '/healthz', '/readyz', '/static/', '/dist/')


def _text(value, maximum=512):
    return str(value or '').strip()[:maximum]


def _action_for_request(path, method, status_code, is_admin=False):
    normalized_path = _text(path, 512).lower()
    if status_code in (401, 403):
        return 'access_denied'
    if 'login' in normalized_path:
        return 'login'
    if 'logout' in normalized_path:
        return 'logout'
    if any(token in normalized_path for token in ('register', 'password', 'oauth', 'orcid', 'google')):
        return 'account_access'
    if method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        if 'submission' in normalized_path:
            return 'submission_change'
        if 'payment' in normalized_path:
            return 'payment_change'
        if any(token in normalized_path for token in ('upload', 'files/')):
            return 'file_change'
        if is_admin:
            return 'admin_change'
        return 'account_change'
    return 'admin_access' if is_admin else 'authenticated_access'


def _resource_for_path(path):
    parts = [part for part in _text(path, 512).split('/') if part]
    if not parts:
        return '', None
    if parts[0] == 'fmadmin' and len(parts) > 1:
        parts = parts[1:]
    resource_type = parts[0] if parts else ''
    resource_id = None
    for part in reversed(parts):
        if re.fullmatch(r'\d+', part):
            resource_id = int(part)
            break
    return resource_type[:80], resource_id


def should_audit_request(path, method, status_code, actor_id=None, is_admin=False):
    normalized_path = _text(path, 512).lower()
    if not normalized_path or normalized_path.startswith(_SKIPPED_ROUTE_PREFIXES):
        return False
    if status_code in (401, 403):
        return True
    if method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        return any(marker in normalized_path for marker in _SENSITIVE_ROUTE_MARKERS)
    return bool(actor_id and is_admin)


def record_request_audit_event(
    connector,
    *,
    service,
    request_id,
    method,
    route,
    path,
    status_code,
    remote_addr,
    user_agent,
    actor_id=None,
    actor_role='',
    is_admin=False,
):
    """Persist a minimal audit record without request bodies, tokens, or passwords."""
    if not should_audit_request(path, method, status_code, actor_id, is_admin):
        return

    action = _action_for_request(path, method, status_code, is_admin)
    outcome = 'success' if 200 <= int(status_code) < 400 else 'failed'
    resource_type, resource_id = _resource_for_path(path)
    connection = getattr(connector, 'conn', None)
    if connection is None:
        record_audit_event_metric(service, action, 'unavailable')
        return

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO audit_events (
                occurred_at, service, request_id, actor_id, actor_role, action,
                resource_type, resource_id, method, route, status_code,
                remote_addr, user_agent, outcome
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                int(time.time()), _text(service, 80), _text(request_id, 80), actor_id,
                _text(actor_role, 80), action, resource_type, resource_id,
                _text(method, 12).upper(), _text(route, 255), int(status_code),
                _text(remote_addr, 64), _text(user_agent, 512), outcome,
            ),
        )
        connection.commit()
        record_audit_event_metric(service, action, outcome)
    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass
        record_audit_event_metric(service, action, 'failed_to_record')
        logger.exception('Unable to write audit event service=%s action=%s', service, action)
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
