# flake8: noqa
"""Two isolated message threads per submission.

- 'author_admin' (Stream A): the author and the submission's assigned admin.
  Visible in fmadmin to the assigned admin and superadmins.
- 'admin_editor' (Stream B): the assigned admin and one specific editor's
  review assignment. Internal only -- the author must never be able to read
  this thread, to preserve blind peer review.

The access check (`_can_view_message_thread`) lives here, at the data-access
layer, and is called at the top of every route below -- never inferred from
which URL the client happened to hit. Stream A and Stream B are on
structurally separate URL paths (submission-scoped vs assignment-scoped) so
a client can never flip a scope parameter to reach the other thread.
"""
import json
import time

from flask import Response, jsonify, request, session, stream_with_context

from .web import (
    bp,
    get_current_user,
    _can_access_submission,
    _clean_text,
    _create_role_notification,
    _decorate_assignment,
    _parse_int,
    _role_of,
    _send_user_email,
    _submission_title,
)
from utils.auth import is_admin_or_editor
from utils.notifications import localized_texts
from extensions import db

MESSAGE_POLL_INTERVAL_SECONDS = 2
MESSAGE_STREAM_MAX_SECONDS = 110
MESSAGE_BODY_MAX_LENGTH = 4000
MESSAGE_LIST_LIMIT = 200


def _load_user(user_id):
    parsed_id = _parse_int(user_id)
    if parsed_id is None:
        return None
    rows = db.users.all().equal(id=parsed_id).exec()
    return rows[0] if rows else None


def _load_submission(submission_id):
    rows = db.submissions.all().equal(id=submission_id).exec()
    return rows[0] if rows else None


def _load_assignment(assignment_id):
    rows = db.editor_assignments.all().equal(id=assignment_id).exec()
    return rows[0] if rows else None


def _stream_b_notification_target(sender_role, submission, assignment):
    """Who to ping when a Stream B (admin<->editor) message is sent.

    Takes only `assignment` for the editor case and never reads
    submission['user_id'] at all -- there is no variable in scope from which
    an author id could leak into this thread's notifications, by
    construction, not just by convention.
    """
    if sender_role == 'editor':
        return _parse_int((submission or {}).get('assigned_admin_id')), 'admin'
    return _parse_int((assignment or {}).get('editor_id')), 'editor'


def _can_view_message_thread(current_user, submission, visibility_scope, assignment=None):
    role = _role_of(current_user)
    if role == 'superadmin':
        return True
    if visibility_scope == 'author_admin':
        return role == 'admin' and _can_access_submission(current_user, submission)
    if visibility_scope == 'admin_editor':
        if role == 'admin':
            return _can_access_submission(current_user, submission)
        if role == 'editor':
            current_user_id = _parse_int(current_user.get('id'))
            return current_user_id is not None and _parse_int((assignment or {}).get('editor_id')) == current_user_id
    return False


def _counterpart_last_read_message_id(submission, visibility_scope, viewer_user_id, assignment=None):
    """How far the OTHER party in this thread has read, for tick-mark
    purposes. Returns 0 (never read) if unknown."""
    submission_id = _parse_int((submission or {}).get('id'))

    if visibility_scope == 'author_admin':
        # Only admins/superadmins reach this thread from fmadmin (the author
        # never does) -- the counterpart is always the author.
        counterpart_id = _parse_int((submission or {}).get('user_id'))
        editor_assignment_id = None
    else:
        editor_id = _parse_int((assignment or {}).get('editor_id'))
        if viewer_user_id == editor_id:
            # Viewer is the editor -- counterpart is "the admin side" as a
            # whole: the furthest any non-editor reader has reached.
            cursor = db.conn.cursor()
            try:
                cursor.execute(
                    "SELECT MAX(last_read_message_id) FROM submission_message_reads "
                    "WHERE submission_id = %s AND visibility_scope = 'admin_editor' "
                    "AND editor_assignment_id = %s AND user_id != %s",
                    (submission_id, _parse_int((assignment or {}).get('id')), editor_id)
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
            return row[0] if row and row[0] is not None else 0
        counterpart_id = editor_id
        editor_assignment_id = _parse_int((assignment or {}).get('id'))

    if counterpart_id is None:
        return 0
    cursor = db.conn.cursor()
    try:
        cursor.execute(
            "SELECT last_read_message_id FROM submission_message_reads "
            "WHERE submission_id = %s AND visibility_scope = %s "
            "AND COALESCE(editor_assignment_id, 0) = %s AND user_id = %s",
            (submission_id, visibility_scope, editor_assignment_id or 0, counterpart_id)
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
    return row[0] if row and row[0] is not None else 0


def _fetch_messages(submission_id, visibility_scope, viewer_user_id, counterpart_last_read_id, editor_assignment_id=None, after_id=0, limit=MESSAGE_LIST_LIMIT):
    cursor = db.conn.cursor()
    try:
        if editor_assignment_id is None:
            cursor.execute(
                "SELECT id, sender_user_id, sender_role, body, created_at "
                "FROM submission_messages "
                "WHERE submission_id = %s AND visibility_scope = %s AND editor_assignment_id IS NULL "
                "AND id > %s AND is_deleted = FALSE "
                "ORDER BY id DESC LIMIT %s",
                (submission_id, visibility_scope, after_id or 0, limit)
            )
        else:
            cursor.execute(
                "SELECT id, sender_user_id, sender_role, body, created_at "
                "FROM submission_messages "
                "WHERE submission_id = %s AND visibility_scope = %s AND editor_assignment_id = %s "
                "AND id > %s AND is_deleted = FALSE "
                "ORDER BY id DESC LIMIT %s",
                (submission_id, visibility_scope, editor_assignment_id, after_id or 0, limit)
            )
        rows = cursor.fetchall()
    finally:
        cursor.close()
    rows.reverse()
    messages = []
    for row in rows:
        message = {'id': row[0], 'sender_user_id': row[1], 'sender_role': row[2], 'body': row[3], 'created_at': row[4]}
        if row[1] == viewer_user_id:
            message['read'] = row[0] <= counterpart_last_read_id
        messages.append(message)
    return messages


def _mark_read(submission_id, visibility_scope, editor_assignment_id, user_id, last_message_id):
    if last_message_id is None:
        return
    now_ts = int(time.time())
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO submission_message_reads
                (submission_id, visibility_scope, editor_assignment_id, user_id, last_read_message_id, last_read_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (submission_id, visibility_scope, COALESCE(editor_assignment_id, 0), user_id)
            DO UPDATE SET last_read_message_id = EXCLUDED.last_read_message_id,
                          last_read_at = EXCLUDED.last_read_at,
                          updated_at = EXCLUDED.updated_at
            """,
            (submission_id, visibility_scope, editor_assignment_id, user_id, last_message_id, now_ts, now_ts)
        )
        db.conn.commit()
        cursor.close()
    except Exception:
        try:
            db.conn.rollback()
        except Exception:
            pass


def _insert_message(submission_id, visibility_scope, editor_assignment_id, sender_user_id, sender_role, body):
    now_ts = int(time.time())
    try:
        created = db.submission_messages.add(
            submission_id=submission_id,
            visibility_scope=visibility_scope,
            editor_assignment_id=editor_assignment_id,
            sender_user_id=sender_user_id,
            sender_role=sender_role,
            body=body,
            is_deleted=False,
            created_at=now_ts
        ).exec()
    except Exception:
        return None
    saved = created[0] if isinstance(created, list) and created else {}
    return {
        'id': _parse_int(saved.get('id')),
        'sender_user_id': sender_user_id,
        'sender_role': sender_role,
        'body': body,
        'created_at': now_ts,
        'read': False,
    }


def _sse_response(generator_func):
    response = Response(stream_with_context(generator_func()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


# --- Stream A: author <-> assigned admin, scoped by submission_id --------

@bp.route('/fmadmin/submissions/<int:submission_id>/messages')
@is_admin_or_editor
def submission_messages_list(submission_id):
    current_user = get_current_user() or {}
    submission = _load_submission(submission_id)
    if not submission or not _can_view_message_thread(current_user, submission, 'author_admin'):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    viewer_id = _parse_int(current_user.get('id'))
    after_id = _parse_int(request.args.get('after_id')) or 0
    counterpart_read_id = _counterpart_last_read_message_id(submission, 'author_admin', viewer_id)
    messages = _fetch_messages(submission_id, 'author_admin', viewer_id, counterpart_read_id, after_id=after_id)
    if messages:
        _mark_read(submission_id, 'author_admin', None, viewer_id, messages[-1]['id'])
    return jsonify({'success': True, 'messages': messages})


@bp.route('/fmadmin/submissions/<int:submission_id>/messages/send', methods=['POST'])
@is_admin_or_editor
def submission_messages_send(submission_id):
    current_user = get_current_user() or {}
    submission = _load_submission(submission_id)
    if not submission or not _can_view_message_thread(current_user, submission, 'author_admin'):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    data = request.get_json(silent=True) or {}
    body = _clean_text(data.get('message'))[:MESSAGE_BODY_MAX_LENGTH]
    if not body:
        return jsonify({'success': False, 'message': 'Message cannot be empty'}), 400

    sender_id = _parse_int(current_user.get('id'))
    message = _insert_message(submission_id, 'author_admin', None, sender_id, _role_of(current_user), body)
    if message is None:
        return jsonify({'success': False, 'message': 'Failed to send message'}), 500

    _mark_read(submission_id, 'author_admin', None, sender_id, message['id'])

    author_id = _parse_int(submission.get('user_id'))
    if author_id is not None:
        title = _submission_title(submission)
        _create_role_notification(
            target_user_id=author_id,
            target_role='user',
            title=localized_texts("Yangi xabar", "Новое сообщение", "New message"),
            message=localized_texts(
                f'"{title}" bo\'yicha yangi xabar bor',
                f'По заявке "{title}" есть новое сообщение',
                f'There is a new message about "{title}"'
            ),
            action_url=f"/dashboard/articles/{submission_id}/messages",
            level='info',
            event_type='submission_chat_message',
            related_submission_id=submission_id,
            actor_user_id=sender_id
        )
        author_row = _load_user(author_id)
        if author_row:
            _send_user_email(
                author_row,
                subject=localized_texts("Yangi xabar", "Новое сообщение", "New message"),
                intro=localized_texts(
                    f'"{title}" bo\'yicha yangi xabar keldi. Ko\'rish uchun tizimga kiring.',
                    f'По заявке "{title}" поступило новое сообщение. Войдите в систему, чтобы прочитать.',
                    f'A new message arrived about "{title}". Log in to read it.',
                ),
                cta_url=f"/dashboard/articles/{submission_id}/messages",
                cta_label=localized_texts("Xabarni ochish", 'Открыть сообщение', 'Open message'),
            )

    return jsonify({'success': True, 'message_obj': message})


@bp.route('/fmadmin/submissions/<int:submission_id>/messages/stream')
@is_admin_or_editor
def submission_messages_stream(submission_id):
    current_user = get_current_user() or {}
    submission = _load_submission(submission_id)
    if not submission or not _can_view_message_thread(current_user, submission, 'author_admin'):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    after_id = _parse_int(request.args.get('after_id')) or 0
    user_id = _parse_int(current_user.get('id'))

    def _generate():
        last_id = after_id
        last_reported_read_id = 0
        started_at = time.time()
        last_keepalive = started_at
        while time.time() - started_at < MESSAGE_STREAM_MAX_SECONDS:
            counterpart_read_id = _counterpart_last_read_message_id(submission, 'author_admin', user_id)
            new_messages = _fetch_messages(submission_id, 'author_admin', user_id, counterpart_read_id, after_id=last_id)
            for message in new_messages:
                last_id = message['id']
                yield f"event: message\ndata: {json.dumps(message)}\n\n"
            if new_messages:
                _mark_read(submission_id, 'author_admin', None, user_id, last_id)
            if counterpart_read_id > last_reported_read_id:
                last_reported_read_id = counterpart_read_id
                yield f"event: read\ndata: {json.dumps({'up_to_id': counterpart_read_id})}\n\n"
            now = time.time()
            if now - last_keepalive > 15:
                yield ": keepalive\n\n"
                last_keepalive = now
            time.sleep(MESSAGE_POLL_INTERVAL_SECONDS)

    return _sse_response(_generate)


# --- Stream B: assigned admin <-> one specific editor, scoped by assignment_id --------

@bp.route('/fmadmin/editor-assignments/<int:assignment_id>/messages')
@is_admin_or_editor
def assignment_messages_list(assignment_id):
    current_user = get_current_user() or {}
    assignment = _load_assignment(assignment_id)
    submission = _load_submission(assignment.get('submission_id')) if assignment else None
    if not assignment or not submission or not _can_view_message_thread(current_user, submission, 'admin_editor', assignment=assignment):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    viewer_id = _parse_int(current_user.get('id'))
    after_id = _parse_int(request.args.get('after_id')) or 0
    counterpart_read_id = _counterpart_last_read_message_id(submission, 'admin_editor', viewer_id, assignment=assignment)
    messages = _fetch_messages(submission['id'], 'admin_editor', viewer_id, counterpart_read_id, editor_assignment_id=assignment_id, after_id=after_id)
    if messages:
        _mark_read(submission['id'], 'admin_editor', assignment_id, viewer_id, messages[-1]['id'])
    return jsonify({'success': True, 'messages': messages})


@bp.route('/fmadmin/editor-assignments/<int:assignment_id>/messages/send', methods=['POST'])
@is_admin_or_editor
def assignment_messages_send(assignment_id):
    current_user = get_current_user() or {}
    assignment = _load_assignment(assignment_id)
    submission = _load_submission(assignment.get('submission_id')) if assignment else None
    if not assignment or not submission or not _can_view_message_thread(current_user, submission, 'admin_editor', assignment=assignment):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    data = request.get_json(silent=True) or {}
    body = _clean_text(data.get('message'))[:MESSAGE_BODY_MAX_LENGTH]
    if not body:
        return jsonify({'success': False, 'message': 'Message cannot be empty'}), 400

    sender_id = _parse_int(current_user.get('id'))
    sender_role = _role_of(current_user)
    message = _insert_message(submission['id'], 'admin_editor', assignment_id, sender_id, sender_role, body)
    if message is None:
        return jsonify({'success': False, 'message': 'Failed to send message'}), 500

    _mark_read(submission['id'], 'admin_editor', assignment_id, sender_id, message['id'])

    # Notify the OTHER side of this specific thread only -- see
    # _stream_b_notification_target for why the author can never be a target.
    title = _submission_title(submission)
    target_user_id, target_role = _stream_b_notification_target(sender_role, submission, assignment)

    if target_user_id is not None:
        _create_role_notification(
            target_user_id=target_user_id,
            target_role=target_role,
            title=localized_texts("Yangi xabar", "Новое сообщение", "New message"),
            message=localized_texts(
                f'"{title}" bo\'yicha ichki muhokamada yangi xabar bor',
                f'Во внутреннем обсуждении по "{title}" есть новое сообщение',
                f'There is a new internal message about "{title}"'
            ),
            action_url=f"/fmadmin/editor-assignments/{assignment_id}/review",
            level='info',
            event_type='assignment_chat_message',
            related_submission_id=submission['id'],
            related_assignment_id=assignment_id,
            actor_user_id=sender_id
        )
        target_row = _load_user(target_user_id)
        if target_row:
            _send_user_email(
                target_row,
                subject=localized_texts("Yangi xabar", "Новое сообщение", "New message"),
                intro=localized_texts(
                    f'"{title}" bo\'yicha ichki muhokamada yangi xabar keldi. Ko\'rish uchun tizimga kiring.',
                    f'Во внутреннем обсуждении по "{title}" появилось новое сообщение. Войдите в систему, чтобы прочитать.',
                    f'A new internal message arrived about "{title}". Log in to read it.',
                ),
                cta_url=f"/fmadmin/editor-assignments/{assignment_id}/review",
                cta_label=localized_texts("Xabarni ochish", 'Открыть сообщение', 'Open message'),
            )

    return jsonify({'success': True, 'message_obj': message})


@bp.route('/fmadmin/editor-assignments/<int:assignment_id>/messages/stream')
@is_admin_or_editor
def assignment_messages_stream(assignment_id):
    current_user = get_current_user() or {}
    assignment = _load_assignment(assignment_id)
    submission = _load_submission(assignment.get('submission_id')) if assignment else None
    if not assignment or not submission or not _can_view_message_thread(current_user, submission, 'admin_editor', assignment=assignment):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    after_id = _parse_int(request.args.get('after_id')) or 0
    user_id = _parse_int(current_user.get('id'))
    submission_id = submission['id']

    def _generate():
        last_id = after_id
        last_reported_read_id = 0
        started_at = time.time()
        last_keepalive = started_at
        while time.time() - started_at < MESSAGE_STREAM_MAX_SECONDS:
            counterpart_read_id = _counterpart_last_read_message_id(submission, 'admin_editor', user_id, assignment=assignment)
            new_messages = _fetch_messages(submission_id, 'admin_editor', user_id, counterpart_read_id, editor_assignment_id=assignment_id, after_id=last_id)
            for message in new_messages:
                last_id = message['id']
                yield f"event: message\ndata: {json.dumps(message)}\n\n"
            if new_messages:
                _mark_read(submission_id, 'admin_editor', assignment_id, user_id, last_id)
            if counterpart_read_id > last_reported_read_id:
                last_reported_read_id = counterpart_read_id
                yield f"event: read\ndata: {json.dumps({'up_to_id': counterpart_read_id})}\n\n"
            now = time.time()
            if now - last_keepalive > 15:
                yield ": keepalive\n\n"
                last_keepalive = now
            time.sleep(MESSAGE_POLL_INTERVAL_SECONDS)

    return _sse_response(_generate)
