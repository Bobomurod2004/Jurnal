# flake8: noqa
"""Author <-> assigned admin correspondence for a single submission ("Stream A").

This is intentionally the ONLY message stream mainweb code ever touches --
the admin<->editor internal thread ("Stream B") lives entirely in fmadmin and
is never queried here, so there is no code path in this file capable of
leaking it even if a future edit mishandles input. `visibility_scope` is
therefore never read from the client -- every query below hardcodes the
literal 'author_admin'.
"""
import json
import time
from flask import Response, jsonify, redirect, render_template, request, session, stream_with_context, url_for
from extensions import dbc
from utils.auth import author_login_required
from utils.notifications import localized_texts
from .api import _create_role_notification, _get_user_row, _send_user_email

MESSAGE_POLL_INTERVAL_SECONDS = 2
MESSAGE_STREAM_MAX_SECONDS = 110
MESSAGE_BODY_MAX_LENGTH = 4000
MESSAGE_LIST_LIMIT = 200


def _clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _parse_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _submission_title(submission):
    title = _clean_text((submission or {}).get('title'))
    return title or f"ID: {_parse_int((submission or {}).get('id')) or '-'}"


def _load_author_submission(user_id, submission_id):
    if not user_id or submission_id is None:
        return None
    rows = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
    return rows[0] if rows else None


def _counterpart_last_read_message_id(submission, viewer_user_id):
    """How far the OTHER party in Stream A has read, for tick-mark purposes.
    Returns 0 (never read) if unknown -- comparisons against 0 correctly mark
    every real message (id >= 1) as unread."""
    author_id = _parse_int((submission or {}).get('user_id'))
    admin_id = _parse_int((submission or {}).get('assigned_admin_id'))
    counterpart_id = admin_id if viewer_user_id == author_id else author_id
    if counterpart_id is None:
        return 0
    submission_id = _parse_int((submission or {}).get('id'))
    cursor = dbc.conn.cursor()
    try:
        cursor.execute(
            "SELECT last_read_message_id FROM submission_message_reads "
            "WHERE submission_id = %s AND visibility_scope = 'author_admin' AND user_id = %s",
            (submission_id, counterpart_id)
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
    return row[0] if row and row[0] is not None else 0


def _fetch_messages(submission_id, viewer_user_id, counterpart_last_read_id, after_id=0, limit=MESSAGE_LIST_LIMIT):
    cursor = dbc.conn.cursor()
    try:
        cursor.execute(
            "SELECT id, sender_user_id, sender_role, body, created_at "
            "FROM submission_messages "
            "WHERE submission_id = %s AND visibility_scope = 'author_admin' "
            "AND id > %s AND is_deleted = FALSE "
            "ORDER BY id DESC LIMIT %s",
            (submission_id, after_id or 0, limit)
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
    rows.reverse()
    messages = []
    for row in rows:
        message = {
            'id': row[0],
            'sender_user_id': row[1],
            'sender_role': row[2],
            'body': row[3],
            'created_at': row[4],
        }
        if row[1] == viewer_user_id:
            message['read'] = row[0] <= counterpart_last_read_id
        messages.append(message)
    return messages


def _mark_read(submission_id, user_id, last_message_id):
    if last_message_id is None:
        return
    now_ts = int(time.time())
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(
            """
            INSERT INTO submission_message_reads
                (submission_id, visibility_scope, editor_assignment_id, user_id, last_read_message_id, last_read_at, updated_at)
            VALUES (%s, 'author_admin', NULL, %s, %s, %s, %s)
            ON CONFLICT (submission_id, visibility_scope, COALESCE(editor_assignment_id, 0), user_id)
            DO UPDATE SET last_read_message_id = EXCLUDED.last_read_message_id,
                          last_read_at = EXCLUDED.last_read_at,
                          updated_at = EXCLUDED.updated_at
            """,
            (submission_id, user_id, last_message_id, now_ts, now_ts)
        )
        dbc.conn.commit()
        cursor.close()
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass


def _notify_new_message_author_admin(submission, sender_role, actor_user_id):
    submission_id = _parse_int((submission or {}).get('id'))
    if submission_id is None:
        return
    title = _submission_title(submission)

    if sender_role == 'author':
        target_user_id = _parse_int((submission or {}).get('assigned_admin_id'))
        target_role = 'admin'
        action_url = f"/fmadmin/submissions/{submission_id}"
    else:
        target_user_id = _parse_int((submission or {}).get('user_id'))
        target_role = 'user'
        action_url = f"/dashboard/articles/{submission_id}/messages"

    if target_user_id is None:
        return

    _create_role_notification(
        target_user_id=target_user_id,
        target_role=target_role,
        title=localized_texts("Yangi xabar", "Новое сообщение", "New message"),
        message=localized_texts(
            f'"{title}" bo\'yicha yangi xabar bor',
            f'По заявке "{title}" есть новое сообщение',
            f'There is a new message about "{title}"'
        ),
        action_url=action_url,
        level='info',
        event_type='submission_chat_message',
        related_submission_id=submission_id,
        actor_user_id=actor_user_id
    )

    user_row = _get_user_row(target_user_id)
    if user_row:
        # Ping only -- the message body itself is never sent by email.
        _send_user_email(
            user_row,
            subject=localized_texts("Yangi xabar", "Новое сообщение", "New message"),
            intro=localized_texts(
                f'"{title}" bo\'yicha yangi xabar keldi. Ko\'rish uchun tizimga kiring.',
                f'По заявке "{title}" поступило новое сообщение. Войдите в систему, чтобы прочитать.',
                f'A new message arrived about "{title}". Log in to read it.',
            ),
            cta_url=action_url,
            cta_label=localized_texts("Xabarni ochish", 'Открыть сообщение', 'Open message'),
        )


def app__dashboard_submission_messages(submission_id):
    user_id = session.get('user_id')
    submission = _load_author_submission(user_id, submission_id)
    if not submission:
        return redirect(url_for('app__dashboard_articles'))
    if _clean_text(submission.get('status')).lower() == 'draft':
        return redirect(url_for('app__dashboard_articles'))

    counterpart_read_id = _counterpart_last_read_message_id(submission, user_id)
    messages = _fetch_messages(submission_id, user_id, counterpart_read_id)
    if messages:
        _mark_read(submission_id, user_id, messages[-1]['id'])

    return render_template(
        'dashboard/submission_messages.html',
        submission=submission,
        messages=messages,
        current_user_id=user_id,
    )


def app__api_submission_messages_list(submission_id):
    user_id = session.get('user_id')
    submission = _load_author_submission(user_id, submission_id)
    if not submission:
        return jsonify({'success': False, 'message': 'Submission not found'}), 404

    after_id = _parse_int(request.args.get('after_id')) or 0
    counterpart_read_id = _counterpart_last_read_message_id(submission, user_id)
    messages = _fetch_messages(submission_id, user_id, counterpart_read_id, after_id=after_id)
    if messages:
        _mark_read(submission_id, user_id, messages[-1]['id'])
    return jsonify({'success': True, 'messages': messages})


def app__api_submission_messages_send(submission_id):
    user_id = session.get('user_id')
    submission = _load_author_submission(user_id, submission_id)
    if not submission:
        return jsonify({'success': False, 'message': 'Submission not found'}), 404

    if _parse_int(submission.get('assigned_admin_id')) is None:
        return jsonify({'success': False, 'message': 'No admin assigned to this submission yet'}), 400

    data = request.get_json(silent=True) or {}
    body = _clean_text(data.get('message'))[:MESSAGE_BODY_MAX_LENGTH]
    if not body:
        return jsonify({'success': False, 'message': 'Message cannot be empty'}), 400

    now_ts = int(time.time())
    try:
        created = dbc.submission_messages.add(
            submission_id=submission_id,
            visibility_scope='author_admin',
            editor_assignment_id=None,
            sender_user_id=user_id,
            sender_role='author',
            body=body,
            is_deleted=False,
            created_at=now_ts
        ).exec()
    except Exception:
        return jsonify({'success': False, 'message': 'Failed to send message'}), 500

    saved = created[0] if isinstance(created, list) and created else {}
    message_id = _parse_int(saved.get('id'))
    _mark_read(submission_id, user_id, message_id)
    _notify_new_message_author_admin(submission, sender_role='author', actor_user_id=user_id)

    return jsonify({
        'success': True,
        'message_obj': {
            'id': message_id,
            'sender_user_id': user_id,
            'sender_role': 'author',
            'body': body,
            'created_at': now_ts,
            'read': False,
        }
    })


def app__api_submission_messages_stream(submission_id):
    user_id = session.get('user_id')
    submission = _load_author_submission(user_id, submission_id)
    if not submission:
        return jsonify({'success': False, 'message': 'Submission not found'}), 404

    after_id = _parse_int(request.args.get('after_id')) or 0

    def _generate():
        last_id = after_id
        last_reported_read_id = 0
        started_at = time.time()
        last_keepalive = started_at
        while time.time() - started_at < MESSAGE_STREAM_MAX_SECONDS:
            counterpart_read_id = _counterpart_last_read_message_id(submission, user_id)
            new_messages = _fetch_messages(submission_id, user_id, counterpart_read_id, after_id=last_id)
            for message in new_messages:
                last_id = message['id']
                yield f"event: message\ndata: {json.dumps(message)}\n\n"
            if new_messages:
                _mark_read(submission_id, user_id, last_id)
            if counterpart_read_id > last_reported_read_id:
                last_reported_read_id = counterpart_read_id
                yield f"event: read\ndata: {json.dumps({'up_to_id': counterpart_read_id})}\n\n"
            now = time.time()
            if now - last_keepalive > 15:
                yield ": keepalive\n\n"
                last_keepalive = now
            time.sleep(MESSAGE_POLL_INTERVAL_SECONDS)

    response = Response(stream_with_context(_generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


def register(app):
    app.add_url_rule(
        '/dashboard/articles/<int:submission_id>/messages',
        view_func=author_login_required(app__dashboard_submission_messages),
    )
    app.add_url_rule(
        '/api/submissions/<int:submission_id>/messages',
        view_func=author_login_required(app__api_submission_messages_list),
    )
    app.add_url_rule(
        '/api/submissions/<int:submission_id>/messages/send',
        view_func=author_login_required(app__api_submission_messages_send),
        methods=['POST'],
    )
    app.add_url_rule(
        '/api/submissions/<int:submission_id>/messages/stream',
        view_func=author_login_required(app__api_submission_messages_stream),
    )
