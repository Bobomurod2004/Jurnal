from types import SimpleNamespace

from fmadmin.routes.web import (
    _missing_nonempty_payload_fields,
    _parse_amount,
    _serialize_upload_value_list,
    _stored_upload_value_to_list as _admin_upload_value_to_list,
)
from shared.email.email_service import EmailService
from mainweb.routes.public import (
    _issue_toc_public_url,
    _normalize_public_upload_url,
    _normalize_public_upload_urls,
    _resolved_country_bucket,
    _youtube_embed_url,
)


def test_parse_amount_handles_common_formats():
    assert _parse_amount('10 000') == 10000.0
    assert _parse_amount('10,5') == 10.5
    assert _parse_amount('10,500.75') == 10500.75
    assert _parse_amount('10.500,75') == 10500.75


def test_youtube_embed_url_parsing():
    assert _youtube_embed_url('https://youtu.be/abc123') == 'https://www.youtube.com/embed/abc123'
    assert _youtube_embed_url('https://www.youtube.com/watch?v=abc123') == 'https://www.youtube.com/embed/abc123'
    assert _youtube_embed_url('https://www.youtube.com/shorts/abc123') == 'https://www.youtube.com/embed/abc123'
    assert _youtube_embed_url('not-a-url') == ''


def test_normalize_public_upload_url_accepts_multiple_input_formats():
    assert _normalize_public_upload_url('/static/uploads/issues/2026/05/toc.pdf') == '/static/uploads/issues/2026/05/toc.pdf'
    assert _normalize_public_upload_url('static/uploads/issues/2026/05/toc.pdf') == '/static/uploads/issues/2026/05/toc.pdf'
    assert _normalize_public_upload_url('/uploads/issues/2026/05/toc.pdf') == '/static/uploads/issues/2026/05/toc.pdf'
    assert _normalize_public_upload_url('https://journal.example/static/uploads/issues/2026/05/toc.pdf') == '/static/uploads/issues/2026/05/toc.pdf'
    assert _normalize_public_upload_url('https://journal.example/uploads/issues/2026/05/toc.pdf') == '/static/uploads/issues/2026/05/toc.pdf'


def test_issue_toc_public_url_allows_only_supported_extensions():
    assert _issue_toc_public_url({'table_of_contents_file': '/static/uploads/issues/2026/05/toc.docx'}) == '/static/uploads/issues/2026/05/toc.docx'
    assert _issue_toc_public_url({'table_of_contents_file': '/static/uploads/issues/2026/05/toc.exe'}) is None


def test_editorial_upload_value_helpers_support_legacy_and_multi_file_formats():
    assert _admin_upload_value_to_list('/static/uploads/editorial_members/2026/06/cv.pdf') == [
        '/static/uploads/editorial_members/2026/06/cv.pdf'
    ]
    assert _admin_upload_value_to_list(
        '["/static/uploads/editorial_members/2026/06/cv-1.pdf", "/static/uploads/editorial_members/2026/06/cv-2.docx"]'
    ) == [
        '/static/uploads/editorial_members/2026/06/cv-1.pdf',
        '/static/uploads/editorial_members/2026/06/cv-2.docx',
    ]
    assert _serialize_upload_value_list(['/static/uploads/editorial_members/2026/06/cv.pdf']) == '/static/uploads/editorial_members/2026/06/cv.pdf'
    assert _serialize_upload_value_list(
        ['/static/uploads/editorial_members/2026/06/cv-1.pdf', '/static/uploads/editorial_members/2026/06/cv-2.docx']
    ) == '["/static/uploads/editorial_members/2026/06/cv-1.pdf", "/static/uploads/editorial_members/2026/06/cv-2.docx"]'


def test_missing_nonempty_payload_fields_ignores_blank_unsupported_values():
    payload = {
        'full_name': 'Alice Example',
        'google_scholar_url': '',
        'research_interests': '',
        'cv_file': None,
    }

    assert _missing_nonempty_payload_fields(payload, {'full_name'}) == []


def test_normalize_public_upload_urls_supports_multi_file_values():
    assert _normalize_public_upload_urls(
        '["/uploads/editorial_members/2026/06/cv-1.pdf", "https://journal.example/static/uploads/editorial_members/2026/06/cv-2.docx", "/etc/passwd"]'
    ) == [
        '/static/uploads/editorial_members/2026/06/cv-1.pdf',
        '/static/uploads/editorial_members/2026/06/cv-2.docx',
    ]


def test_resolved_country_bucket_preserves_explicit_country_name_without_iso():
    assert _resolved_country_bucket(country_name='Atlantis') == ('atlantis', 'Atlantis', '')
    assert _resolved_country_bucket(country_name='Uzbekistan') == ('uz', 'Uzbekistan', 'uz')


def _email_service():
    """Building a template context needs no database -- only the base URL for
    the call-to-action link and the signature name, so stub settings do."""
    settings = SimpleNamespace(
        APP_BASE_URL='https://example.org',
        MAIL_FROM_NAME='Philology Matters',
    )
    return EmailService(None, settings, app_name='tests')


def test_build_context_groups_multilingual_content_for_templates():
    context = _email_service()._build_context(
        subject='Subject UZ | Subject RU | Subject EN',
        intro='[UZ] Intro UZ | [RU] Intro RU | [EN] Intro EN',
        details=[
            ('Label UZ / Label RU / Label EN', 'Value UZ / Value RU / Value EN'),
        ],
        body_lines=[
            '[UZ] Body UZ line',
            '[RU] Body RU line',
            '[EN] Body EN line',
        ],
        cta_url='/dashboard',
        cta_label='Open UZ / Open RU / Open EN',
    )

    assert context['is_multilingual'] is True
    assert [section['code'] for section in context['language_sections']] == ['uz', 'ru', 'en']
    assert context['language_sections'][0]['subject'] == 'Subject UZ'
    assert context['language_sections'][1]['intro'] == 'Intro RU'
    assert context['language_sections'][2]['cta_label'] == 'Open EN'
    assert context['language_sections'][0]['details'][0]['label'] == 'Label UZ'
    assert context['language_sections'][2]['body_lines'][0] == 'Body EN line'


def test_build_context_mirrors_untranslated_text_into_every_language():
    # Text that carries no "uz | ru | en" separators is treated as common
    # content and copied into all three sections, so such an email renders the
    # same paragraph three times.
    context = _email_service()._build_context(
        subject='Yagona sarlavha',
        intro='Yagona kirish',
        cta_url='/dashboard',
        cta_label='Ochish',
    )

    assert context['subject'] == 'Yagona sarlavha'
    assert context['cta_url'] == 'https://example.org/dashboard'
    assert [section['subject'] for section in context['language_sections']] == [
        'Yagona sarlavha'
    ] * 3
