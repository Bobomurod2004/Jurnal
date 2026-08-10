# flake8: noqa
from extensions import dbc
from modules.translate import t
from flask import request, session
from utils.auth import sanitize_next_url
from utils.notifications import apply_localized_notification_content, dashboard_notification_access_clause
try:
    import mainweb.settings as settings
except ImportError:
    import settings


def register_context_processors(app):
    def _safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _clean_text(value):
        if value is None:
            return ''
        return str(value).strip()

    def _format_number_with_label(number_value, label_text):
        value_text = _clean_text(number_value) or '-'
        label = _clean_text(label_text)
        if not label:
            return value_text
        normalized_label = label.lower()
        if normalized_label in {'jild', 'son'}:
            return f'{value_text}-{normalized_label}'
        return f'{label} {value_text}'

    def _format_issue_label(volume_no, issue_no, year=None):
        volume_text = _format_number_with_label(volume_no, t('volume'))
        issue_text = _format_number_with_label(issue_no, t('issue'))
        meta = f'{volume_text}, {issue_text}'
        year_text = _clean_text(year)
        if year_text:
            return f'{meta} ({year_text})'
        return meta

    def _format_volume_label(volume_no):
        return _format_number_with_label(volume_no, t('volume'))

    def _format_labeled_value(label_text, value_text):
        value = _clean_text(value_text)
        if not value:
            return ''

        label = _clean_text(label_text).rstrip(':').strip()
        if not label:
            return value

        collapsed_value = value
        for _ in range(5):
            if ':' not in collapsed_value:
                break
            head, tail = collapsed_value.split(':', 1)
            if head.strip().casefold() != label.casefold():
                break
            collapsed_value = tail.strip()

        if not collapsed_value or collapsed_value.casefold() == label.casefold():
            return label
        return f'{label}: {collapsed_value}'

    def _current_lang_code():
        lang = str(session.get('language') or 'en').strip().lower()
        return lang if lang in {'uz', 'ru', 'en'} else 'en'

    def _localized_field(item, base_field):
        language = _current_lang_code()
        if language == 'uz':
            localized = item.get(f'{base_field}_uz')
        elif language == 'ru':
            localized = item.get(f'{base_field}_ru')
        else:
            localized = item.get(f'{base_field}_en') if f'{base_field}_en' in item else item.get(base_field)
        if localized in (None, ''):
            fallback = item.get(base_field)
            return '' if fallback is None else fallback
        return localized

    def _is_masters_issue_alias(value):
        normalized = str(value or '').strip().lower().replace('-', '_').replace(' ', '_')
        return normalized in {'masters', 'special_masters'}

    def _ensure_role_notifications_table():
        try:
            cursor = dbc.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS role_notifications (
                    id SERIAL PRIMARY KEY,
                    target_user_id INTEGER,
                    target_role TEXT,
                    actor_user_id INTEGER,
                    event_type TEXT,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    level TEXT DEFAULT 'info',
                    action_url TEXT,
                    related_submission_id INTEGER,
                    related_assignment_id INTEGER,
                    metadata_text TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at BIGINT DEFAULT EXTRACT(epoch FROM now()),
                    read_at BIGINT
                );
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_target_user ON role_notifications(target_user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_target_role ON role_notifications(target_role);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_notifications_unread ON role_notifications(is_read, created_at DESC);")
            dbc.conn.commit()
            cursor.close()
            dbc._init_tables()
            dbc._init_columns()
        except Exception:
            try:
                dbc.conn.rollback()
            except Exception:
                pass

    def _author_notifications_overview():
        user_id = session.get('user_id')
        access_clause, access_args = dashboard_notification_access_clause(user_id)
        if not access_clause:
            return {'count': 0, 'preview': []}

        query = (
            "SELECT id, title, message, level, action_url, is_read, created_at, metadata_text "
            "FROM role_notifications "
            f"WHERE {access_clause} "
            "ORDER BY created_at DESC, id DESC LIMIT 6"
        )
        count_query = (
            "SELECT COUNT(*) FROM role_notifications "
            "WHERE is_read = FALSE "
            f"AND {access_clause}"
        )
        try:
            cursor = dbc.conn.cursor()
            cursor.execute(query, tuple(access_args))
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            preview = [apply_localized_notification_content(dict(zip(cols, row))) for row in rows]
            cursor.execute(count_query, tuple(access_args))
            unread_row = cursor.fetchone()
            cursor.close()
            return {'count': int(unread_row[0] or 0) if unread_row else 0, 'preview': preview}
        except Exception:
            try:
                dbc.conn.rollback()
            except Exception:
                pass
            return {'count': 0, 'preview': []}

    _ensure_role_notifications_table()

    @app.context_processor
    def inject_latest_issue():
        issues = [
            issue for issue in (dbc.issues.get().exec() or [])
            if not _is_masters_issue_alias(issue.get('category'))
        ]
        if not issues:
            return {'latest_issue': None}

        def _latest_issue_sort_key(item):
            # Current issue should follow the most recently created issue,
            # even before its year/issue_no metadata is fully finalized.
            return (
                _safe_int(item.get('created_at')),
                _safe_int(item.get('id')),
                _safe_int(item.get('year')),
                _safe_int(item.get('issue_no')),
            )

        latest_issue_item = max(
            issues,
            key=_latest_issue_sort_key,
        )
        latest_issue_item = dict(latest_issue_item)
        latest_issue_item['title'] = _localized_field(latest_issue_item, 'title')
        latest_issue_item['shortinfo'] = _localized_field(latest_issue_item, 'shortinfo')
        latest_issue_item['price'] = _localized_field(latest_issue_item, 'price')
        return {'latest_issue': latest_issue_item}

    @app.context_processor
    def inject_translations():
        return dict(t=t)

    @app.context_processor
    def inject_formatters():
        return {
            'format_issue_label': _format_issue_label,
            'format_volume_label': _format_volume_label,
            'format_labeled_value': _format_labeled_value,
        }

    @app.context_processor
    def inject_version():
        return {'app_version': settings.APP_VERSION}

    @app.context_processor
    def inject_login_next_url():
        """Safe return path for the header's "sign in" link, or None.

        The header used to build `url_for('app__login', next=request.full_path)`
        directly, so on /login it pointed back at /login. Each crawl re-encoded
        the previous URL into a new one
        (/login?next=/login?next%3D/login?next%253D...) and bots walked an
        endless tree. `sanitize_next_url` refuses the auth paths, which stops
        the chain at the source.

        Returns the raw path rather than a finished URL: a context processor
        runs on every render, and reaching into the URL map here would make it
        fail wherever that endpoint is not registered.
        """
        current_path = request.full_path or request.path
        # `full_path` always appends '?', even with no query string.
        if current_path.endswith('?'):
            current_path = current_path[:-1]

        return {'login_next_url': sanitize_next_url(current_path)}

    @app.context_processor
    def inject_author_notifications():
        notifications = _author_notifications_overview()
        return {
            'dashboard_notifications_unread_count': notifications['count'],
            'dashboard_notifications_preview': notifications['preview']
        }
