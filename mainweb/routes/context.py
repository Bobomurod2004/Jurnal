# flake8: noqa
from extensions import dbc
from modules.translate import t
from flask import session
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
    def inject_version():
        return {'app_version': settings.APP_VERSION}

    @app.context_processor
    def inject_author_notifications():
        notifications = _author_notifications_overview()
        return {
            'dashboard_notifications_unread_count': notifications['count'],
            'dashboard_notifications_preview': notifications['preview']
        }
