# flake8: noqa
import os
import re
import time
import settings
from flask import render_template, session, request, jsonify, flash, redirect, url_for, current_app, send_file, abort
from extensions import dbc
from modules.translate import t, translate
from utils.auth import (
    author_login_required,
    sanitize_input,
    decode_html_entities,
    is_valid_email,
    get_user_profile_completion,
)
from utils.notifications import apply_localized_notification_content, dashboard_notification_access_clause
from utils.private_uploads import build_private_upload_ref, extract_private_upload_key, private_upload_abspath, upload_access_url
from utils.uploads import allowed_file


SUBMISSION_TRACKS = {
    'masters': {
        'title_key': 'track_masters_title',
        'desc_key': 'track_masters_desc',
        'fallback_title': 'Magistr',
        'fallback_desc': 'Magistrlar uchun maqola yuborish formasi',
        'icon': 'solar:document-add-bold-duotone'
    },
    'phd': {
        'title_key': 'track_phd_title',
        'desc_key': 'track_phd_desc',
        'fallback_title': 'Doktorant',
        'fallback_desc': 'Doktorantlar uchun maqola yuborish formasi',
        'icon': 'solar:book-2-bold-duotone'
    },
    'teacher': {
        'title_key': 'track_teacher_title',
        'desc_key': 'track_teacher_desc',
        'fallback_title': "O'qituvchi",
        'fallback_desc': "O'qituvchilar uchun maqola yuborish formasi",
        'icon': 'solar:user-check-bold-duotone'
    }
}

SUBMISSION_WORKFLOW_STEPS = [
    ('waiting', 'workflow_stage_waiting', "Kutilmoqda"),
    ('technical_check', 'workflow_stage_technical_check', "Texnik talablarga mos"),
    ('anti_plagiarism', 'workflow_stage_anti_plagiarism', "Antiplagiatga tekshirish"),
    ('in_review', 'workflow_stage_in_review', "Tahrizda"),
    ('recommended', 'workflow_stage_recommended', "Nashrga tavsiya etildi"),
    ('payment', 'workflow_stage_payment', "To'lov"),
    ('published', 'workflow_stage_published', "Nashr qilindi")
]
SUBMISSION_WORKFLOW_KEYS = {key for key, _, _ in SUBMISSION_WORKFLOW_STEPS}
TARIFF_CURRENCY_FIELDS = {
    'usd': 'price_usd',
    'uzs': 'price_uzs',
    'rub': 'price_rub'
}
ACADEMIC_POSITION_CHOICES = {'teacher', 'student', 'master', 'doctoral', 'postgraduate', 'doctor'}
ORCID_REGEX = re.compile(r'^\d{4}-\d{4}-\d{4}-\d{3}[0-9Xx]$')


def _parse_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_publication_timestamp(publication):
    if not publication:
        return None
    for key in ('date_publish', 'created_at', 'created_date'):
        timestamp = _parse_int(publication.get(key))
        if timestamp:
            return timestamp
    return None


def _format_publication_year(publication):
    timestamp = _resolve_publication_timestamp(publication)
    if not timestamp:
        return 'N/A'
    return time.strftime('%Y', time.gmtime(timestamp + 5 * 60 * 60))


def _decode_row_strings(row):
    if not row:
        return row
    decoded = {}
    for key, value in row.items():
        if isinstance(value, str):
            decoded[key] = decode_html_entities(value)
        else:
            decoded[key] = value
    return decoded


def _submission_track_list():
    return [{'key': key, **value} for key, value in SUBMISSION_TRACKS.items()]


def _resolve_submission_track(track):
    if not track:
        return None
    normalized = track.strip().lower()
    return normalized if normalized in SUBMISSION_TRACKS else None


def _resolve_submission_workflow_stage(submission):
    explicit_stage = (submission.get('workflow_stage') or '').strip().lower()
    if explicit_stage in SUBMISSION_WORKFLOW_KEYS or explicit_stage == 'rejected':
        return explicit_stage

    status = (submission.get('status') or '').strip().lower()
    editor_status = (submission.get('editor_review_status') or '').strip().lower()

    if status == 'published':
        return 'published'
    if status == 'rejected':
        return 'rejected'
    if status in ('submitted', 'pending'):
        return 'waiting'
    if status in ('in_process', 'under_review'):
        if editor_status in ('approved', 'reviewed'):
            return 'recommended'
        if editor_status in ('in_review', 'assigned'):
            return 'in_review'
        return 'technical_check'
    if status == 'paid':
        return 'payment'
    if status == 'accepted':
        return 'recommended'
    return 'waiting'


def _workflow_step_label(key, title_key, fallback):
    translated = t(title_key)
    if translated and translated != title_key:
        return translated
    return fallback


def _decorate_submission_with_workflow(submission):
    stage_key = _resolve_submission_workflow_stage(submission)
    step_index = {key: idx for idx, (key, _, _) in enumerate(SUBMISSION_WORKFLOW_STEPS)}
    current_index = step_index.get(stage_key, -1)

    steps = []
    for idx, (key, title_key, fallback) in enumerate(SUBMISSION_WORKFLOW_STEPS):
        label = _workflow_step_label(key, title_key, fallback)
        if stage_key == 'rejected':
            state = 'pending'
        elif idx < current_index:
            state = 'done'
        elif idx == current_index:
            state = 'current'
        else:
            state = 'pending'
        steps.append({
            'key': key,
            'label': label,
            'state': state
        })

    if stage_key == 'rejected':
        stage_label = t('workflow_stage_rejected')
        if stage_label == 'workflow_stage_rejected':
            stage_label = 'Rad etilgan'
    else:
        stage_info = next((item for item in SUBMISSION_WORKFLOW_STEPS if item[0] == stage_key), None)
        if stage_info:
            stage_label = _workflow_step_label(*stage_info)
        else:
            stage_label = _workflow_step_label(*SUBMISSION_WORKFLOW_STEPS[0])

    submission['workflow_stage_key'] = stage_key
    submission['workflow_stage_label'] = stage_label
    submission['workflow_steps'] = steps
    return submission


def _normalize_currency(currency):
    normalized = (currency or 'usd').strip().lower()
    return normalized if normalized in TARIFF_CURRENCY_FIELDS else 'usd'


def _resolve_upload_file_path(file_url):
    if not file_url:
        return None
    private_path = private_upload_abspath(file_url)
    if private_path:
        return private_path

    normalized_url = str(file_url).strip()
    prefix = '/static/uploads/'
    if not normalized_url.startswith(prefix):
        return None

    relative_path = normalized_url[len(prefix):].lstrip('/')
    base_dir = os.path.abspath(current_app.config.get('UPLOAD_FOLDER', ''))
    if not base_dir:
        return None

    candidate_path = os.path.abspath(os.path.join(base_dir, relative_path))
    try:
        if os.path.commonpath([candidate_path, base_dir]) != base_dir:
            return None
    except ValueError:
        return None
    return candidate_path


def _submission_has_private_file(submission, storage_key):
    for field_name in ('file_authors', 'file_anonymized', 'anti_plagiarism_file'):
        if extract_private_upload_key((submission or {}).get(field_name)) == storage_key:
            return True
    return False


def _user_matches_private_upload_pattern(user_id, storage_key):
    if not user_id or not storage_key:
        return False

    filename = storage_key.rsplit('/', 1)[-1]
    user_marker = f'_{user_id}_'

    if storage_key.startswith('documents/'):
        return filename.startswith(f'academic_doc_{user_id}_')
    if storage_key.startswith('payments/'):
        return filename.startswith(f'payment_proof_{user_id}_')
    if storage_key.startswith('articles/'):
        return (
            filename.startswith(f'authors_{user_id}_')
            or filename.startswith(f'anonymized_{user_id}_')
            or filename.startswith(f'anti_plagiarism_{user_id}_')
            or user_marker in filename
        )
    return False


def _user_has_private_upload_record(user_id, storage_key):
    if not user_id or not storage_key:
        return False

    if storage_key.startswith('documents/'):
        rows = dbc.user_doc_uploads.get(user_id=user_id).exec()
        return any(extract_private_upload_key(row.get('file_path')) == storage_key for row in rows)

    if storage_key.startswith('payments/'):
        rows = dbc.payments.get(user_id=user_id).exec()
        return any(
            extract_private_upload_key(row.get('proof')) == storage_key
            or extract_private_upload_key(row.get('confirmation_file')) == storage_key
            for row in rows
        )

    if storage_key.startswith('articles/'):
        rows = dbc.submissions.get(user_id=user_id).exec()
        return any(_submission_has_private_file(row, storage_key) for row in rows)

    return False


def _resolve_tariff_price(tariff, currency):
    selected_key = TARIFF_CURRENCY_FIELDS[currency]
    selected_value = tariff.get(selected_key)

    if selected_value in (None, ''):
        for fallback_key in ('price_usd', 'price_uzs', 'price_rub'):
            fallback_value = tariff.get(fallback_key)
            if fallback_value not in (None, ''):
                selected_value = fallback_value
                break

    try:
        return float(selected_value or 0)
    except (TypeError, ValueError):
        return 0.0


def _is_valid_orcid(orcid):
    normalized = (orcid or '').strip()
    if not normalized:
        return False
    return ORCID_REGEX.match(normalized) is not None


def _fetch_dashboard_notifications(user_id, limit=200):
    safe_limit = max(1, min(_parse_int(limit) or 200, 500))
    return _fetch_dashboard_notifications_page(user_id, page=1, per_page=safe_limit)


def _fetch_dashboard_notifications_page(user_id, page=1, per_page=20):
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if not access_clause:
        return []

    safe_page = max(_parse_int(page) or 1, 1)
    safe_per_page = max(1, min(_parse_int(per_page) or 20, 100))
    safe_offset = (safe_page - 1) * safe_per_page
    query = (
        "SELECT id, title, message, level, action_url, is_read, created_at, read_at, event_type, metadata_text "
        "FROM role_notifications "
        f"WHERE {access_clause} "
        "ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    )
    args = tuple(access_args) + (safe_per_page, safe_offset)
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, args)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        return [apply_localized_notification_content(dict(zip(columns, row))) for row in rows]
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return []


def _count_dashboard_notifications(user_id):
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if not access_clause:
        return 0

    query = (
        "SELECT COUNT(*) FROM role_notifications "
        f"WHERE {access_clause}"
    )
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, tuple(access_args))
        row = cursor.fetchone()
        cursor.close()
        return int(row[0] or 0) if row else 0
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return 0


def _count_dashboard_unread_notifications(user_id):
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if not access_clause:
        return 0

    query = (
        "SELECT COUNT(*) FROM role_notifications "
        "WHERE is_read = FALSE "
        f"AND {access_clause}"
    )
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, tuple(access_args))
        row = cursor.fetchone()
        cursor.close()
        return int(row[0] or 0) if row else 0
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return 0


def _mark_dashboard_notification_read(notification_id, user_id):
    notification_id_int = _parse_int(notification_id)
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if notification_id_int is None or not access_clause:
        return False

    query = (
        "UPDATE role_notifications SET is_read = TRUE, read_at = %s "
        "WHERE id = %s AND is_read = FALSE "
        f"AND {access_clause}"
    )
    args = (int(time.time()), notification_id_int, *access_args)
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, args)
        changed = cursor.rowcount
        dbc.conn.commit()
        cursor.close()
        return changed > 0
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return False


def _mark_dashboard_notifications_read_all(user_id):
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if not access_clause:
        return 0

    query = (
        "UPDATE role_notifications SET is_read = TRUE, read_at = %s "
        "WHERE is_read = FALSE "
        f"AND {access_clause}"
    )
    args = (int(time.time()), *access_args)
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, args)
        changed = cursor.rowcount
        dbc.conn.commit()
        cursor.close()
        return changed
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return 0


def app__dashboard_private_file(storage_key):
    user_id = session.get('user_id')
    resolved_key = extract_private_upload_key(storage_key)
    if not user_id or not resolved_key:
        abort(404)

    if not (_user_matches_private_upload_pattern(user_id, resolved_key) or _user_has_private_upload_record(user_id, resolved_key)):
        abort(404)

    file_path = private_upload_abspath(resolved_key)
    if not file_path or not os.path.exists(file_path):
        abort(404)

    return send_file(file_path, as_attachment=False, download_name=os.path.basename(file_path))


def _get_dashboard_notification(notification_id, user_id):
    notification_id_int = _parse_int(notification_id)
    access_clause, access_args = dashboard_notification_access_clause(user_id)
    if notification_id_int is None or not access_clause:
        return None

    query = (
        "SELECT id, title, message, level, action_url, is_read, created_at, read_at, event_type, metadata_text "
        "FROM role_notifications "
        f"WHERE id = %s AND {access_clause} "
        "LIMIT 1"
    )
    args = (notification_id_int, *access_args)
    try:
        cursor = dbc.conn.cursor()
        cursor.execute(query, args)
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        if not row:
            return None
        return apply_localized_notification_content(dict(zip(columns, row)))
    except Exception:
        try:
            dbc.conn.rollback()
        except Exception:
            pass
        return None


def app__dashboard():
    user_id = session['user_id']
    all_submissions = dbc.submissions.get().equal(user_id=user_id).order_by('id').exec()

    drafts_count = 0
    visible_submissions = []
    for submission in all_submissions:
        translate(submission)
        status = (submission.get('status') or '').strip().lower()
        if status == 'draft':
            drafts_count += 1
            continue
        _decorate_submission_with_workflow(submission)
        visible_submissions.append(submission)

    visible_submissions.sort(key=lambda item: _parse_int(item.get('created_date')) or 0, reverse=True)
    recent_submissions = visible_submissions[:4]

    published_count = 0
    rejected_count = 0
    in_progress_count = 0
    payment_count = 0
    for submission in visible_submissions:
        stage = submission.get('workflow_stage_key') or _resolve_submission_workflow_stage(submission)
        if stage == 'published':
            published_count += 1
        elif stage == 'rejected':
            rejected_count += 1
        elif stage == 'payment':
            payment_count += 1
            in_progress_count += 1
        else:
            in_progress_count += 1

    dashboard_stats = {
        'total': len(visible_submissions),
        'in_progress': in_progress_count,
        'published': published_count,
        'drafts': drafts_count,
        'rejected': rejected_count,
        'payment': payment_count,
        'unread_notifications': _count_dashboard_unread_notifications(user_id)
    }

    return render_template(
        'dashboard/index.html',
        submissions=recent_submissions,
        dashboard_stats=dashboard_stats
    )


def app__dashboard_articles():
    submissions = dbc.submissions.get().equal(user_id=session['user_id']).unequal(status='draft').order_by('id').exec()
    author_profiles = {}

    # Collect unique author IDs first to avoid repeated DB lookups in template rendering.
    author_ids = set()
    for submission in submissions:
        translate(submission)
        _decorate_submission_with_workflow(submission)
        if submission.get('main_author_id'):
            author_ids.add(submission['main_author_id'])

        co_author_ids = submission.get('sub_author_ids') or submission.get('subauthor_ids') or []
        for author_id in co_author_ids:
            author_ids.add(author_id)

    for author_id in author_ids:
        author = dbc.author_profile.get(id=author_id).exec()
        if author:
            author_profiles[author_id] = translate(author[0])

    return render_template('dashboard/articles.html', submissions=submissions, author_profiles=author_profiles)


def app__dashboard_articles_delete(submission_id):
    expects_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json
    submission = dbc.submissions.get(id=submission_id, user_id=session['user_id']).exec()
    if not submission:
        if expects_json:
            return jsonify({'success': False, 'message': t('submission_not_found')}), 404
        flash('Submission not found', 'error')
        return redirect(url_for('app__dashboard_articles'))

    dbc.submissions.get(id=submission_id, user_id=session['user_id']).delete().exec()
    if expects_json:
        return jsonify({'success': True, 'message': t('submission_deleted_successfully')})
    flash('Submission deleted successfully', 'success')
    return redirect(url_for('app__dashboard_articles'))


def app__dashboard_purchases():
    payments = dbc.payments.get(user_id=session['user_id']).order_by('id').exec()
    for payment in payments:
        payment = translate(payment)
        if payment['payment_type'] == 'article' and payment['ids']:
            articles = []
            for article_id in payment['ids']:
                publication = dbc.publications.get(id=article_id).exec()
                if publication:
                    translated_article = translate(publication[0])
                    main_author = None
                    if translated_article['main_author_id']:
                        author = dbc.author_profile.get(id=translated_article['main_author_id']).exec()
                        if author:
                            main_author = translate(author[0])
                    articles.append({
                        'id': translated_article['id'],
                        'title': translated_article['title'],
                        'author': main_author['name'] if main_author else 'Unknown',
                        'volume': translated_article.get('volume', 'N/A'),
                        'issue': translated_article.get('issue', 'N/A'),
                        'year': _format_publication_year(translated_article)
                    })
            payment['articles'] = articles
        elif payment['payment_type'] == 'subscription' and payment['ids']:
            tariff_id = payment['ids'][0]
            tariff = dbc.tariffs.get(id=tariff_id).exec()
            if tariff:
                tariff_data = translate(tariff[0])
                payment['tariff'] = tariff_data

    subscription_active = False
    subscription_end_date = None
    days_left = None
    user = dbc.users.get(id=session['user_id']).exec()[0]
    if user.get('subscription_end_date') and user['subscription_end_date'] > int(time.time()):
        subscription_active = True
        subscription_end_date = user['subscription_end_date']
        days_left = (user['subscription_end_date'] - int(time.time())) // (24 * 60 * 60)

    currency = _normalize_currency(request.args.get('currency', 'usd'))
    tariffs = dbc.tariffs.get().exec()
    processed_tariffs = []
    for tariff in tariffs:
        tariff = translate(tariff)
        tariff['selected_price'] = _resolve_tariff_price(tariff, currency)
        processed_tariffs.append(tariff)

    user_docs = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()
    is_verified = bool(user.get('is_verified')) or bool(user_docs)

    return render_template(
        'dashboard/payments.html',
        payments=payments,
        subscription_active=subscription_active,
        subscription_end_date=subscription_end_date,
        days_left=days_left,
        tariffs=processed_tariffs,
        currency=currency,
        is_verified=is_verified
    )


def app__dashboard_new_article():
    submission_id = request.args.get('id', type=int)
    track = _resolve_submission_track(request.args.get('track'))

    if not submission_id and track is None and request.args.get('track'):
        flash(
            t('invalid_submission_track') if t('invalid_submission_track') != 'invalid_submission_track' else 'Please select a valid submission track',
            'error'
        )
        return redirect(url_for('app__dashboard_new_article'))

    if not submission_id and not track:
        return render_template('dashboard/new_article_type.html', submission_tracks=_submission_track_list())

    translations = dbc.translations.get().exec()
    authors = dbc.author_profile.get().exec()
    classifications = dbc.fix_classifications.get().exec()
    countries = dbc.fix_country.get().exec()

    for author in authors:
        author = translate(author)
    for classification in classifications:
        classification = translate(classification)
    for country in countries:
        country = translate(country)

    return render_template('dashboard/new_article.html',
                         translations=translations,
                         authors=authors,
                         classifications=classifications,
                         countries=countries,
                         selected_track=track,
                         selected_track_info=SUBMISSION_TRACKS.get(track))


def app__dashboard_new_article_track(track):
    resolved_track = _resolve_submission_track(track)
    if not resolved_track:
        flash(
            t('invalid_submission_track') if t('invalid_submission_track') != 'invalid_submission_track' else 'Please select a valid submission track',
            'error'
        )
        return redirect(url_for('app__dashboard_new_article'))
    return redirect(url_for('app__dashboard_new_article', track=resolved_track))


def app__dashboard_payments():
    return app__dashboard_purchases()


def app__dashboard_guides():
    return render_template('dashboard/guides.html')


def app__dashboard_notifications():
    user_id = session.get('user_id')
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = 20

    total_notifications = _count_dashboard_notifications(user_id)
    total_pages = (total_notifications + per_page - 1) // per_page if total_notifications else 1
    notifications = _fetch_dashboard_notifications_page(user_id, page=page, per_page=per_page)
    unread_count = _count_dashboard_unread_notifications(user_id)

    return render_template(
        'dashboard/notifications.html',
        notifications=notifications,
        page=page,
        total_pages=total_pages,
        total_notifications=total_notifications,
        unread_count=unread_count
    )


def app__dashboard_notification_read(notification_id):
    _mark_dashboard_notification_read(notification_id, session.get('user_id'))
    redirect_url = request.form.get('redirect_url') or request.referrer or url_for('app__dashboard_notifications')
    return redirect(redirect_url)


def app__dashboard_notification_open(notification_id):
    notification = _get_dashboard_notification(notification_id, session.get('user_id'))
    if not notification:
        flash(
            t('notification_not_found') if t('notification_not_found') != 'notification_not_found' else 'Notification not found',
            'error'
        )
        return redirect(url_for('app__dashboard_notifications'))

    _mark_dashboard_notification_read(notification_id, session.get('user_id'))
    action_url = (notification.get('action_url') or '').strip()
    if action_url.startswith('/'):
        return redirect(action_url)
    return redirect(url_for('app__dashboard_notifications'))


def app__dashboard_notification_read_all():
    changed = _mark_dashboard_notifications_read_all(session.get('user_id'))
    if changed:
        flash(
            t('notifications_marked_read') if t('notifications_marked_read') != 'notifications_marked_read' else f'Marked as read: {changed}',
            'success'
        )
    redirect_url = request.form.get('redirect_url') or request.referrer or url_for('app__dashboard_notifications')
    return redirect(redirect_url)


def app__dashboard_profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_photo':
            if 'photo' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})

            file = request.files['photo']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})

            if file and allowed_file(file.filename):
                try:
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"avatar_{session['user_id']}_{int(time.time())}.{extension}"
                    avatars_folder = current_app.config['AVATARS_FOLDER']
                    os.makedirs(avatars_folder, exist_ok=True)
                    filepath = os.path.join(avatars_folder, filename)

                    user_rows = dbc.users.get(id=session['user_id']).exec()
                    user = user_rows[0] if user_rows else {}
                    old_avatar_path = _resolve_upload_file_path(user.get('avatar'))
                    if old_avatar_path and os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)

                    file.save(filepath)
                    avatar_url = f"/static/uploads/avatars/{filename}"

                    dbc.users.get(id=session['user_id']).update(avatar=avatar_url).exec()

                    session_user = session.get('user') or {}
                    if session_user:
                        session_user['avatar'] = avatar_url
                        session['user'] = session_user

                    return jsonify({'success': True, 'avatar_url': avatar_url})
                except Exception:
                    current_app.logger.exception('Failed to update profile avatar')
                    return jsonify({'success': False, 'message': 'Failed to upload profile photo'})

            return jsonify({'success': False, 'message': 'Invalid file type'})

        if action == 'delete_photo':
            try:
                user_rows = dbc.users.get(id=session['user_id']).exec()
                user = user_rows[0] if user_rows else {}
                old_avatar_path = _resolve_upload_file_path(user.get('avatar'))
                if old_avatar_path and os.path.exists(old_avatar_path):
                    os.remove(old_avatar_path)

                dbc.users.get(id=session['user_id']).update(avatar=None).exec()

                session_user = session.get('user') or {}
                if session_user:
                    session_user['avatar'] = None
                    session['user'] = session_user

                return jsonify({'success': True, 'avatar_url': '/static/default_avatar.png'})
            except Exception:
                current_app.logger.exception('Failed to delete profile avatar')
                return jsonify({'success': False, 'message': 'Failed to delete profile photo'})

        if action == 'save_profile':
            country_id_raw = request.form.get('country_id')
            country_id = _parse_int(country_id_raw)
            if country_id_raw and country_id is None:
                flash('Invalid country selected', 'error')
                return redirect(url_for('app__dashboard_profile'))
            if country_id is None:
                flash('Country is required', 'error')
                return redirect(url_for('app__dashboard_profile'))
            if country_id is not None:
                country = dbc.fix_country.get(id=country_id).exec()
                if not country:
                    flash('Invalid country selected', 'error')
                    return redirect(url_for('app__dashboard_profile'))

            first_name = sanitize_input(request.form.get('name'))
            second_name = sanitize_input(request.form.get('second_name'))
            father_name = sanitize_input(request.form.get('father_name')) or None
            if not first_name or not second_name or not father_name:
                flash("Ism, familiya va sharif maydonlari majburiy", 'error')
                return redirect(url_for('app__dashboard_profile'))

            dbc.users.get(id=session['user_id']).update(
                name=first_name,
                second_name=second_name,
                father_name=father_name,
                country_id=country_id
            ).exec()

            academic_position = (request.form.get('academic_position') or '').strip().lower()
            if not academic_position:
                flash("Ilmiy daraja yoki faoliyat turini tanlash majburiy", 'error')
                return redirect(url_for('app__dashboard_profile'))
            if academic_position not in ACADEMIC_POSITION_CHOICES:
                flash('Invalid academic position selected', 'error')
                return redirect(url_for('app__dashboard_profile'))

            submitted_doc_path = sanitize_input(request.form.get('document_path')) or None
            if submitted_doc_path and not _resolve_upload_file_path(submitted_doc_path):
                flash('Invalid document path', 'error')
                return redirect(url_for('app__dashboard_profile'))

            existing_doc_rows = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()
            existing_doc = existing_doc_rows[0] if existing_doc_rows else None
            effective_doc_path = submitted_doc_path or (existing_doc.get('file_path') if existing_doc else None)
            now_ts = int(time.time())

            if existing_doc:
                old_doc_path = existing_doc.get('file_path')
                doc_changed = old_doc_path != effective_doc_path
                title_changed = (existing_doc.get('work_title') or '').strip().lower() != academic_position

                update_payload = {
                    'work_title': academic_position,
                    'file_path': effective_doc_path,
                    'updated_at': now_ts
                }
                if effective_doc_path and (doc_changed or title_changed or not existing_doc.get('verification_status')):
                    update_payload['verification_status'] = 'pending'

                dbc.user_doc_uploads.get(id=existing_doc['id']).update(**update_payload).exec()

                if doc_changed and old_doc_path and submitted_doc_path:
                    old_doc_abs = _resolve_upload_file_path(old_doc_path)
                    if old_doc_abs and os.path.exists(old_doc_abs):
                        try:
                            os.remove(old_doc_abs)
                        except OSError:
                            pass
            else:
                dbc.user_doc_uploads.add(
                    user_id=session['user_id'],
                    work_title=academic_position,
                    file_path=effective_doc_path,
                    verification_status='pending' if effective_doc_path else None,
                    created_at=now_ts,
                    updated_at=now_ts
                ).exec()

            session_user = session.get('user') or {}
            if session_user:
                session_user.update({
                    'name': first_name,
                    'second_name': second_name,
                    'father_name': father_name,
                    'country_id': country_id
                })
                session['user'] = _decode_row_strings(session_user)

            flash('Profile updated successfully', 'success')
            return redirect(url_for('app__dashboard_profile'))

        if action == 'save_author_profile':
            orcid = sanitize_input(request.form.get('orcid')) or None
            author_email = sanitize_input(request.form.get('email')).lower()
            profile_data = {
                'name': sanitize_input(request.form.get('name')),
                'organization': sanitize_input(request.form.get('organization')),
                'department': sanitize_input(request.form.get('department')),
                'position': sanitize_input(request.form.get('position')),
                'email': author_email,
                'phone': sanitize_input(request.form.get('phone')),
                'orcid': orcid,
                'address_street': sanitize_input(request.form.get('address_street')),
                'address_city': sanitize_input(request.form.get('address_city')),
                'address_country': sanitize_input(request.form.get('address_country')),
                'address_zip': sanitize_input(request.form.get('address_zip')),
                'updated_at': int(time.time())
            }

            required_fields = (
                'name',
                'organization',
                'department',
                'position',
                'email',
                'phone',
                'address_street',
                'address_city',
                'address_country',
                'address_zip',
            )
            if not all(profile_data[field] for field in required_fields):
                flash('Please fill in all required author profile fields', 'error')
                return redirect(url_for('app__dashboard_profile'))
            if orcid and not _is_valid_orcid(orcid):
                flash('ORCID format is invalid. Example: 0000-0000-0000-0000', 'error')
                return redirect(url_for('app__dashboard_profile'))
            if not is_valid_email(profile_data['email']):
                flash('Invalid email format', 'error')
                return redirect(url_for('app__dashboard_profile'))

            author_profile = dbc.author_profile.get(user_id=session['user_id']).exec()
            if author_profile:
                dbc.author_profile.get(user_id=session['user_id']).update(**profile_data).exec()
            else:
                profile_data['user_id'] = session['user_id']
                profile_data['created_at'] = int(time.time())
                dbc.author_profile.add(**profile_data).exec()

            flash('Author profile updated successfully', 'success')
            return redirect(url_for('app__dashboard_profile'))

        if action == 'upload_academic_document':
            if 'academic_document' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})

            file = request.files['academic_document']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})

            if file and allowed_file(file.filename, {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}):
                timestamp = int(time.time())
                filename = f"academic_doc_{session['user_id']}_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}"

                documents_folder = os.path.join(settings.SAVE_PATH, 'private_uploads', 'documents')
                os.makedirs(documents_folder, exist_ok=True)

                filepath = os.path.join(documents_folder, filename)

                file.save(filepath)
                file_ref = build_private_upload_ref('documents', filename)

                return jsonify({
                    'success': True,
                    'file_ref': file_ref,
                    'file_path': file_ref,
                    'download': upload_access_url(file_ref),
                    'filename': filename
                })

            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PDF, DOC, DOCX, JPG, PNG'})

    user = _decode_row_strings(dbc.users.get(id=session['user_id']).exec()[0])
    author_profile = dbc.author_profile.get(user_id=session['user_id']).exec()
    author_profile_row = _decode_row_strings(author_profile[0]) if author_profile else None
    user_doc_upload = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()
    fix_country = dbc.fix_country.get().exec()
    profile_completion = get_user_profile_completion(user_row=user, user_id=session['user_id'], author_row=author_profile_row)

    # Keep sidebar session info readable for already logged-in users.
    session_user = session.get('user') or {}
    if session_user:
        session['user'] = _decode_row_strings(session_user)

    return render_template('dashboard/profile.html',
                         user=user,
                         author_profile=author_profile_row,
                         user_doc_upload=user_doc_upload[0] if user_doc_upload else None,
                         fix_country=fix_country,
                         profile_completion=profile_completion)


def register(app):
    app.add_url_rule('/dashboard', view_func=author_login_required(app__dashboard))
    app.add_url_rule('/dashboard/articles', view_func=author_login_required(app__dashboard_articles))
    app.add_url_rule('/dashboard/articles/delete/<int:submission_id>', view_func=author_login_required(app__dashboard_articles_delete), methods=['POST'])
    app.add_url_rule('/dashboard/purchases', view_func=author_login_required(app__dashboard_purchases))
    app.add_url_rule('/dashboard/new_article', view_func=author_login_required(app__dashboard_new_article))
    app.add_url_rule('/dashboard/new_article/<track>', view_func=author_login_required(app__dashboard_new_article_track))
    app.add_url_rule('/dashboard/payments', view_func=author_login_required(app__dashboard_payments))
    app.add_url_rule('/dashboard/guides', view_func=author_login_required(app__dashboard_guides))
    app.add_url_rule('/dashboard/notifications', view_func=author_login_required(app__dashboard_notifications))
    app.add_url_rule('/dashboard/notifications/open/<int:notification_id>', view_func=author_login_required(app__dashboard_notification_open))
    app.add_url_rule('/dashboard/notifications/read/<int:notification_id>', view_func=author_login_required(app__dashboard_notification_read), methods=['POST'])
    app.add_url_rule('/dashboard/notifications/read-all', view_func=author_login_required(app__dashboard_notification_read_all), methods=['POST'])
    app.add_url_rule('/dashboard/profile', view_func=author_login_required(app__dashboard_profile), methods=['GET', 'POST'])
    app.add_url_rule('/dashboard/files/<path:storage_key>', endpoint='app__dashboard_private_file', view_func=author_login_required(app__dashboard_private_file))
