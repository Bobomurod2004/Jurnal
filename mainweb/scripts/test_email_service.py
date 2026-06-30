#!/usr/bin/env python3
"""
Test Email Service

Test script to verify email service functionality:
- Email validation
- Retry mechanism
- Rate limiting
- Multi-language support
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Flask app setup
os.environ.setdefault('FLASK_APP', 'mainweb.app')

from flask import Flask
import mainweb.settings as settings
from extensions import dbc
from mainweb.utils.emailer import send_notification_email


def test_simple_email():
    """Test 1: Simple single-language email"""
    print("\n" + "="*60)
    print("TEST 1: Simple Single-Language Email")
    print("="*60)

    result = send_notification_email(
        recipients='test@example.com',
        subject='Test Email - Simple',
        intro='This is a simple test email.',
        body_lines=[
            'Line 1: Testing email service',
            'Line 2: All systems operational',
        ],
        cta_url='https://example.com',
        cta_label='Click Here',
        fail_silently=False,
    )

    print(f"Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    return result


def test_multilingual_email_markers():
    """Test 2: Multi-language email with markers"""
    print("\n" + "="*60)
    print("TEST 2: Multi-Language Email (Markers)")
    print("="*60)

    result = send_notification_email(
        recipients='test@example.com',
        subject='[UZ] Yangi xabar [RU] Новое сообщение [EN] New message',
        intro='[UZ] Salom! [RU] Привет! [EN] Hello!',
        body_lines=[
            '[UZ]',
            'Sizning maqolangiz qabul qilindi.',
            'Tizimda ko\'rib chiqish jarayoni boshlandi.',
            '',
            '[RU]',
            'Ваша статья принята.',
            'Процесс рассмотрения начат в системе.',
            '',
            '[EN]',
            'Your article has been accepted.',
            'The review process has started in the system.',
        ],
        details=[
            ('Article ID', '12345'),
            ('[UZ] Holat [RU] Статус [EN] Status', '[UZ] Qabul qilindi [RU] Принято [EN] Accepted'),
        ],
        cta_url='https://example.com/article/12345',
        cta_label='[UZ] Ochish [RU] Открыть [EN] Open',
        fail_silently=False,
    )

    print(f"Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    return result


def test_multilingual_email_separator():
    """Test 3: Multi-language email with separator"""
    print("\n" + "="*60)
    print("TEST 3: Multi-Language Email (Separator)")
    print("="*60)

    result = send_notification_email(
        recipients='test@example.com',
        subject='Maqola holati | Статус статьи | Article status',
        intro='Hurmatli muallif | Уважаемый автор | Dear author',
        body_lines=[
            'Maqolangiz nashr qilindi | Ваша статья опубликована | Your article has been published',
        ],
        cta_label='Ko\'rish | Посмотреть | View',
        cta_url='https://example.com',
        fail_silently=False,
    )

    print(f"Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    return result


def test_email_validation():
    """Test 4: Email validation"""
    print("\n" + "="*60)
    print("TEST 4: Email Validation")
    print("="*60)

    test_emails = [
        'valid@example.com',
        'invalid-email',
        'test@',
        '@example.com',
        'user..name@example.com',
        'a' * 100 + '@example.com',  # Too long local part
    ]

    print(f"Testing {len(test_emails)} email addresses...")

    result = send_notification_email(
        recipients=','.join(test_emails),
        subject='Validation Test',
        intro='Testing email validation',
        fail_silently=False,
    )

    print(f"Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    print("Check logs for validation warnings")
    return result


def test_rate_limiting():
    """Test 5: Rate limiting"""
    print("\n" + "="*60)
    print("TEST 5: Rate Limiting (15 recipients)")
    print("="*60)

    # Generate 15 test recipients
    recipients = [f'test{i}@example.com' for i in range(1, 16)]

    print(f"Sending to {len(recipients)} recipients...")
    print("Watch for rate limit pause messages...")

    result = send_notification_email(
        recipients=recipients,
        subject='Rate Limit Test',
        intro='Testing rate limiting feature',
        body_lines=['This tests the rate limiting mechanism'],
        fail_silently=False,
    )

    print(f"Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    return result


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# EMAIL SERVICE TEST SUITE")
    print("#"*60)
    print(f"\nSMTP Host: {settings.MAIL_HOST}")
    print(f"SMTP Port: {settings.MAIL_PORT}")
    print(f"Mail Enabled: {settings.MAIL_ENABLED}")
    print(f"Suppress Send: {settings.MAIL_SUPPRESS_SEND}")

    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(settings)

    with app.app_context():
        tests = [
            test_simple_email,
            test_multilingual_email_markers,
            test_multilingual_email_separator,
            test_email_validation,
            test_rate_limiting,
        ]

        results = []
        for test_func in tests:
            try:
                result = test_func()
                results.append((test_func.__name__, result))
            except Exception as e:
                print(f"\n❌ EXCEPTION: {e}")
                results.append((test_func.__name__, False))

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = '✅ PASS' if result else '❌ FAIL'
            print(f"{status} - {test_name}")

        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")

        print("\n" + "="*60)
        print("Check Mailpit UI: http://localhost:8025")
        print("="*60)


if __name__ == '__main__':
    main()
