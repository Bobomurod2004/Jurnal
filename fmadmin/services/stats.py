# flake8: noqa
import datetime
from extensions import db
from shared.submission_status import SUBMISSION_STATUSES, SUBMISSION_STATUS_LABELS, SUBMISSION_STATUS_BADGE_TONE


WORKFLOW_STAGE_ORDER = SUBMISSION_STATUSES
WORKFLOW_STAGE_LABELS = {key: labels['uz'] for key, labels in SUBMISSION_STATUS_LABELS.items()}

STATUS_ORDER = SUBMISSION_STATUSES
ACTIVE_STATUS_SET = set(STATUS_ORDER) - {'published', 'rejected'}


def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _normalize_text(value):
    return str(value or '').strip().lower()


def _normalize_status(value):
    status = _normalize_text(value)
    return status if status else 'unknown'


def _normalize_workflow_stage(value):
    stage = _normalize_text(value)
    return stage if stage in WORKFLOW_STAGE_LABELS else ''


def _status_badge_tone(status):
    return SUBMISSION_STATUS_BADGE_TONE.get(status, 'secondary')


def _truthy(value):
    if isinstance(value, bool):
        return value
    return _normalize_text(value) in {'1', 'true', 'yes', 'on'}


def _safe_dt_from_ts(value):
    ts = _safe_int(value, default=None)
    if ts is None or ts <= 0:
        return None
    try:
        return datetime.datetime.fromtimestamp(ts)
    except Exception:
        return None


def _infer_workflow_stage(submission):
    # `status` is the single canonical field now (shared/submission_status.py);
    # kept as a thin resolver so callers below don't need to change.
    stage = _normalize_workflow_stage(submission.get('status'))
    return stage or 'pending'


def _month_start(dt):
    return datetime.datetime(dt.year, dt.month, 1)


def _shift_month(dt, offset):
    month_idx = dt.month - 1 + offset
    year = dt.year + (month_idx // 12)
    month = (month_idx % 12) + 1
    return datetime.datetime(year, month, 1)


def _month_range(months=6, now=None):
    if now is None:
        now = datetime.datetime.now()
    current = _month_start(now)
    points = [_shift_month(current, -i) for i in range(months - 1, -1, -1)]
    keys = [item.strftime('%Y-%m') for item in points]
    labels = [item.strftime('%b %Y') for item in points]
    return keys, labels


def _load_all_dashboard_data():
    try:
        submissions = db.submissions.all().exec() or []
    except Exception:
        submissions = []
    try:
        publications = db.publications.all().exec() or []
    except Exception:
        publications = []
    try:
        users = db.users.all().exec() or []
    except Exception:
        users = []
    try:
        authors = db.author_profile.all().exec() or []
    except Exception:
        authors = []
    return submissions, publications, users, authors


def get_dashboard_snapshot(months=6, recent_limit=6, top_limit=6, stale_days=14):
    try:
        now = datetime.datetime.now()
        now_ts = int(now.timestamp())
        month_keys, month_labels = _month_range(months=months, now=now)
        month_key_set = set(month_keys)

        submissions, publications, users, authors = _load_all_dashboard_data()
        visible_submissions = [item for item in submissions if _normalize_status(item.get('status')) != 'draft']

        author_name_by_user_id = {}
        author_name_by_author_id = {}
        for author in authors:
            display_name = (
                author.get('name')
                or author.get('full_name')
                or author.get('fio')
                or "Noma'lum muallif"
            )
            user_id = _safe_int(author.get('user_id'), default=None)
            author_id = _safe_int(author.get('id'), default=None)
            if user_id is not None and user_id not in author_name_by_user_id:
                author_name_by_user_id[user_id] = display_name
            if author_id is not None and author_id not in author_name_by_author_id:
                author_name_by_author_id[author_id] = display_name

        status_counts = {}
        stage_counts = {key: 0 for key in WORKFLOW_STAGE_ORDER}
        active_submissions = []
        decided_durations = []
        submissions_monthly = {key: 0 for key in month_keys}
        stale_submissions = []
        recent_pool = []

        published_submissions = 0
        rejected_submissions = 0
        submissions_last_30d = 0
        decision_pool = 0

        for submission in visible_submissions:
            status = _normalize_status(submission.get('status'))
            stage = _infer_workflow_stage(submission)
            created_ts = _safe_int(submission.get('created_date'), default=0)
            updated_ts = _safe_int(submission.get('updated_at'), default=0)

            status_counts[status] = status_counts.get(status, 0) + 1
            if stage in stage_counts:
                stage_counts[stage] += 1
            else:
                stage_counts['pending'] += 1

            created_dt = _safe_dt_from_ts(created_ts)
            if created_dt:
                month_key = created_dt.strftime('%Y-%m')
                if month_key in month_key_set:
                    submissions_monthly[month_key] += 1
                if now_ts - created_ts <= 30 * 24 * 3600:
                    submissions_last_30d += 1

            recent_pool.append(submission)

            is_published = status == 'published' or stage == 'published'
            is_rejected = status == 'rejected' or stage == 'rejected'
            if is_published:
                published_submissions += 1
                decision_pool += 1
            elif is_rejected:
                rejected_submissions += 1
                decision_pool += 1
            else:
                active_submissions.append(submission)
                age_days = ((now_ts - created_ts) // 86400) if created_ts > 0 else 0
                if age_days >= stale_days:
                    stale_submissions.append({
                        'id': _safe_int(submission.get('id'), default=0),
                        'title': submission.get('title') or "Nomsiz ariza",
                        'status': status,
                        'workflow_stage': stage,
                        'author_name': author_name_by_user_id.get(_safe_int(submission.get('user_id'), default=None), "Noma'lum muallif"),
                        'created_at': created_ts,
                        'age_days': int(age_days),
                    })

            decision_ts = updated_ts if updated_ts > 0 else 0
            if decision_ts > 0 and created_ts > 0 and decision_ts >= created_ts and (is_published or is_rejected):
                decided_durations.append((decision_ts - created_ts) / 86400.0)

        total_views = 0
        published_monthly = {key: 0 for key in month_keys}
        top_article_pool = []
        new_articles_30d = 0

        for article in publications:
            views = _safe_int(article.get('stat_views'), default=0)
            total_views += max(views, 0)
            top_article_pool.append(article)

            published_ts = _safe_int(article.get('date_publish'), default=0)
            published_dt = _safe_dt_from_ts(published_ts)
            if published_dt:
                month_key = published_dt.strftime('%Y-%m')
                if month_key in month_key_set:
                    published_monthly[month_key] += 1
                if now_ts - published_ts <= 30 * 24 * 3600:
                    new_articles_30d += 1

        active_users = []
        for user in users:
            if _truthy(user.get('is_hidden')):
                continue
            if _safe_int(user.get('deleted_at'), default=0) > 0:
                continue
            active_users.append(user)

        acceptance_rate = round((published_submissions * 100.0) / decision_pool, 1) if decision_pool else 0.0
        avg_decision_days = round(sum(decided_durations) / len(decided_durations), 1) if decided_durations else 0.0

        ordered_status_codes = [code for code in STATUS_ORDER if status_counts.get(code, 0) > 0]
        for code in status_counts.keys():
            if code not in STATUS_ORDER and status_counts.get(code, 0) > 0:
                ordered_status_codes.append(code)
        status_chart_data = [status_counts.get(code, 0) for code in ordered_status_codes]

        workflow_cards = []
        for stage_key in WORKFLOW_STAGE_ORDER:
            workflow_cards.append({
                'key': stage_key,
                'label': WORKFLOW_STAGE_LABELS.get(stage_key, stage_key),
                'count': stage_counts.get(stage_key, 0),
                'tone': _status_badge_tone(stage_key),
            })

        recent_submissions_sorted = sorted(
            recent_pool,
            key=lambda item: _safe_int(item.get('created_date'), default=0),
            reverse=True,
        )[:max(recent_limit, 1)]
        recent_submissions = []
        for submission in recent_submissions_sorted:
            created_ts = _safe_int(submission.get('created_date'), default=0)
            status = _normalize_status(submission.get('status'))
            stage = _infer_workflow_stage(submission)
            recent_submissions.append({
                'id': _safe_int(submission.get('id'), default=0),
                'title': submission.get('title') or "Nomsiz ariza",
                'status': status,
                'workflow_stage': stage,
                'author_name': author_name_by_user_id.get(_safe_int(submission.get('user_id'), default=None), "Noma'lum muallif"),
                'created_at': created_ts,
                'age_days': int((now_ts - created_ts) // 86400) if created_ts > 0 else 0,
            })

        top_articles_sorted = sorted(
            top_article_pool,
            key=lambda item: _safe_int(item.get('stat_views'), default=0),
            reverse=True,
        )[:max(top_limit, 1)]
        top_articles = []
        for article in top_articles_sorted:
            main_author_id = _safe_int(article.get('main_author_id'), default=None)
            top_articles.append({
                'id': _safe_int(article.get('id'), default=0),
                'title': article.get('title') or "Nomsiz maqola",
                'author_name': author_name_by_author_id.get(main_author_id, "Noma'lum muallif"),
                'stat_views': _safe_int(article.get('stat_views'), default=0),
                'doi': article.get('doi'),
            })

        attention_submissions = sorted(
            stale_submissions,
            key=lambda item: item.get('age_days', 0),
            reverse=True,
        )[:max(recent_limit, 1)]

        stats = {
            'total_articles': len(publications),
            'active_submissions': len(active_submissions),
            'total_views': total_views,
            'total_users': len(active_users),
            'total_submissions': len(visible_submissions),
            'published_submissions': published_submissions,
            'rejected_submissions': rejected_submissions,
            'acceptance_rate': acceptance_rate,
            'avg_decision_days': avg_decision_days,
            'stalled_submissions': len(stale_submissions),
            'new_submissions_30d': submissions_last_30d,
            'new_articles_30d': new_articles_30d,
            'generated_at': now_ts,
        }

        timeline_chart = {
            'labels': month_labels,
            'submissions': [submissions_monthly.get(key, 0) for key in month_keys],
            'published': [published_monthly.get(key, 0) for key in month_keys],
        }

        status_chart = {
            'codes': ordered_status_codes,
            'data': status_chart_data,
            'total': len(visible_submissions),
        }

        return {
            'stats': stats,
            'status_chart': status_chart,
            'timeline_chart': timeline_chart,
            'workflow_cards': workflow_cards,
            'recent_submissions': recent_submissions,
            'attention_submissions': attention_submissions,
            'top_articles': top_articles,
        }
    except Exception as e:
        print(f"Error building dashboard snapshot: {e}")
        return {
            'stats': {
                'total_articles': 0,
                'active_submissions': 0,
                'total_views': 0,
                'total_users': 0,
                'total_submissions': 0,
                'published_submissions': 0,
                'rejected_submissions': 0,
                'acceptance_rate': 0.0,
                'avg_decision_days': 0.0,
                'stalled_submissions': 0,
                'new_submissions_30d': 0,
                'new_articles_30d': 0,
                'generated_at': int(datetime.datetime.now().timestamp()),
            },
            'status_chart': {'codes': [], 'data': [], 'total': 0},
            'timeline_chart': {'labels': [], 'submissions': [], 'published': []},
            'workflow_cards': [],
            'recent_submissions': [],
            'attention_submissions': [],
            'top_articles': [],
        }


def calculate_dashboard_stats():
    return get_dashboard_snapshot().get('stats', {})


def get_submissions_stats():
    chart = get_dashboard_snapshot().get('status_chart', {})
    return {
        'labels': chart.get('codes', []),
        'data': chart.get('data', []),
    }


def get_monthly_articles_stats():
    chart = get_dashboard_snapshot().get('timeline_chart', {})
    return {
        'labels': chart.get('labels', []),
        'data': chart.get('published', []),
    }


def get_recent_submissions():
    return get_dashboard_snapshot().get('recent_submissions', [])


def get_top_articles():
    return get_dashboard_snapshot().get('top_articles', [])
