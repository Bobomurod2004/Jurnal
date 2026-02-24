# flake8: noqa
from extensions import dbc
from modules.translate import t


def register_context_processors(app):
    @app.context_processor
    def inject_latest_issue():
        latest_issue = dbc.issues.get().order_by('year').order_by('issue_no').per_page(1).page(1).exec()
        return {'latest_issue': latest_issue[0] if latest_issue else None}

    @app.context_processor
    def inject_translations():
        return dict(t=t)
