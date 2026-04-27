import argparse
import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FMADMIN_DIR = os.path.dirname(CURRENT_DIR)
if FMADMIN_DIR not in sys.path:
    sys.path.insert(0, FMADMIN_DIR)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            'Run fmadmin editor assignment deadline '
            'reminders/expiry automation'
        )
    )
    parser.add_argument('--actor-user-id', type=int, default=None)
    parser.add_argument('--force', action='store_true')
    return parser.parse_args()


def main():
    from app import create_app
    import settings
    from routes.web import run_editor_assignment_automation

    args = parse_args()
    app = create_app()

    base_url = (settings.APP_BASE_URL or '').strip()
    if not base_url:
        base_url = 'http://localhost'

    with app.app_context():
        # Reminder flow uses url_for(), so provide a request context.
        with app.test_request_context(base_url=base_url):
            result = run_editor_assignment_automation(
                actor_user_id=args.actor_user_id,
                force=args.force,
            )

    print(json.dumps({'success': True, 'result': result}, ensure_ascii=False))


if __name__ == '__main__':
    main()
