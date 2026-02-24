# flake8: noqa
import time
import datetime
from extensions import db


def calculate_dashboard_stats():
    try:
        total_articles = db.publications.get().count().exec() or 0
        active_submissions = db.submissions.get().unequal(status='draft').unequal(status='published').count().exec() or 0
        articles_with_views = db.publications.get().exec() or []
        total_views = sum(article.get('stat_views', 0) or 0 for article in articles_with_views)
        total_users = db.users.get().count().exec() or 0

        return {
            'total_articles': total_articles,
            'active_submissions': active_submissions,
            'total_views': total_views,
            'total_users': total_users
        }
    except Exception as e:
        print(f"Error calculating dashboard stats: {e}")
        return {
            'total_articles': 0,
            'active_submissions': 0,
            'total_views': 0,
            'total_users': 0
        }


def get_submissions_stats():
    status_counts = db.submissions.group_by('status').count('id').exec()
    labels = []
    data = []
    for row in status_counts:
        labels.append(row['status'])
        data.append(row['id_count'])
    return {'labels': labels, 'data': data}


def get_monthly_articles_stats():
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=180)

        articles = db.publications.get().exec()
        monthly_counts = {}

        for article in articles:
            if article.get('date_publish'):
                pub_date = datetime.datetime.fromtimestamp(article['date_publish'])
                if start_date <= pub_date <= end_date:
                    month_key = pub_date.strftime('%Y-%m')
                    monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1

        labels = []
        data = []
        current_date = end_date

        for _ in range(6):
            month_key = current_date.strftime('%Y-%m')
            month_label = current_date.strftime('%b %Y')
            labels.insert(0, month_label)
            data.insert(0, monthly_counts.get(month_key, 0))
            if current_date.month == 1:
                current_date = current_date.replace(year=current_date.year - 1, month=12)
            else:
                current_date = current_date.replace(month=current_date.month - 1)

        return {'labels': labels, 'data': data}
    except Exception as e:
        print(f"Error getting monthly articles stats: {e}")
        return {'labels': [], 'data': []}


def get_recent_submissions():
    try:
        submissions = db.submissions.get().order_by('created_date').per_page(5).page(1).exec() or []
        result = []
        for submission in submissions:
            author_name = "Неизвестный автор"
            if submission.get('user_id'):
                author_profile = db.author_profile.get().equal(user_id=submission['user_id']).exec()
                if author_profile:
                    author_name = author_profile[0].get('name', 'Неизвестный автор')
            result.append({
                'title': submission.get('title', 'Без названия'),
                'status': submission.get('status', 'draft'),
                'author_name': author_name,
                'created_at': submission.get('created_date', 0)
            })
        return result
    except Exception as e:
        print(f"Error getting recent submissions: {e}")
        return []


def get_top_articles():
    try:
        articles = db.publications.get().order_by('stat_views').per_page(5).page(1).exec() or []
        result = []
        for article in articles:
            author_name = "Неизвестный автор"
            if article.get('main_author_id'):
                author_profile = db.author_profile.get().equal(id=article['main_author_id']).exec()
                if author_profile:
                    author_name = author_profile[0].get('name', 'Неизвестный автор')
            result.append({
                'title': article.get('title', 'Без названия'),
                'author_name': author_name,
                'stat_views': article.get('stat_views', 0),
                'doi': article.get('doi', None)
            })
        return result
    except Exception as e:
        print(f"Error getting top articles: {e}")
        return []
