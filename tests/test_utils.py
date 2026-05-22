from fmadmin.routes.web import _parse_amount
from fmadmin.services.emailer import _build_context, _build_multilingual_template_payload
from mainweb.routes.public import _youtube_embed_url, _normalize_public_upload_url, _issue_toc_public_url


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


def test_build_multilingual_template_payload_keeps_three_languages():
    template_row = {
        'subject_uz': 'UZ subject',
        'subject_ru': 'RU subject',
        'subject_en': 'EN subject',
        'intro_uz': 'UZ intro',
        'intro_ru': 'RU intro',
        'intro_en': 'EN intro',
        'body_uz': 'UZ body',
        'body_ru': 'RU body',
        'body_en': 'EN body',
        'cta_label_uz': 'UZ open',
        'cta_label_ru': 'RU open',
        'cta_label_en': 'EN open',
    }
    payload = _build_multilingual_template_payload(
        template_row,
        {'action_url': 'https://example.org'},
    )

    assert payload['subject'] == 'UZ subject | RU subject | EN subject'
    assert payload['intro'] == 'UZ intro'
    assert '[RU]' in payload['body_lines']
    assert '[EN]' in payload['body_lines']
    assert payload['cta_label'] == 'UZ open / RU open / EN open'


def test_build_multilingual_template_payload_uses_language_specific_vars():
    template_row = {
        'subject_uz': 'UZ {{time_left}}',
        'subject_ru': 'RU {{time_left}}',
        'subject_en': 'EN {{time_left}}',
        'intro_uz': 'Intro UZ',
        'intro_ru': 'Intro RU',
        'intro_en': 'Intro EN',
        'body_uz': 'Body UZ {{deadline_type}}',
        'body_ru': 'Body RU {{deadline_type}}',
        'body_en': 'Body EN {{deadline_type}}',
        'cta_label_uz': 'Open UZ',
        'cta_label_ru': 'Open RU',
        'cta_label_en': 'Open EN',
    }
    payload = _build_multilingual_template_payload(
        template_row,
        {
            'time_left': {'uz': '2 soat', 'ru': '2 часа', 'en': '2 hours'},
            'deadline_type': {'uz': 'qabul', 'ru': 'принятие', 'en': 'acceptance'},
        },
    )

    assert payload['subject'] == 'UZ 2 soat | RU 2 часа | EN 2 hours'
    assert 'Body UZ qabul' in payload['body_lines']
    assert 'Body RU принятие' in payload['body_lines']
    assert 'Body EN acceptance' in payload['body_lines']


def test_build_context_groups_multilingual_content_for_templates():
    context = _build_context(
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
