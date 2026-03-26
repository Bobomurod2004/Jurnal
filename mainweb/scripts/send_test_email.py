import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from utils.emailer import send_notification_email


def main():
    recipient = sys.argv[1] if len(sys.argv) > 1 else ''
    if not recipient:
        print('Usage: python mainweb/scripts/send_test_email.py recipient@example.com')
        return 1

    app = create_app()
    with app.app_context():
        sent = send_notification_email(
            recipients=[recipient],
            subject='Philology Matters test email',
            intro='This is a real SMTP test from the project configuration.',
            body_lines=[
                'If you received this message, the configured email transport is working.',
                'You can now continue with production email rollout.'
            ],
            cta_url='/',
            cta_label='Open website',
            fail_silently=False,
        )

    print('Email sent successfully.' if sent else 'Email was not sent.')
    return 0 if sent else 1


if __name__ == '__main__':
    raise SystemExit(main())
