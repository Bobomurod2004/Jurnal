from fmadmin.routes.web import _parse_amount
from mainweb.routes.public import _youtube_embed_url


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
