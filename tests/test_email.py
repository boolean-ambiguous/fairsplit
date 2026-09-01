from app.services.email import _render_html
from app.services.passwords import DUMMY_HASH, hash_password, verify_password


def test_hash_password_round_trips():
    hashed = hash_password("correct-horse")
    assert verify_password("correct-horse", hashed)
    assert not verify_password("wrong-horse", hashed)


def test_hash_password_uses_a_fresh_salt_each_time():
    assert hash_password("correct-horse") != hash_password("correct-horse")


def test_verify_password_rejects_malformed_hash():
    assert not verify_password("correct-horse", "not-a-real-hash")


def test_dummy_hash_never_verifies():
    assert not verify_password("anything", DUMMY_HASH)


def test_render_html_escapes_user_supplied_text():
    html_body = _render_html(
        preheader="pre",
        heading='<img src=x onerror=alert(1)> added you to "Trip"',
        paragraphs=["<script>steal()</script>"],
        cta_label="View group",
        cta_url="https://fairsplit.ing/verify?token=abc",
    )
    assert "<img src=x" not in html_body
    assert "<script>steal()</script>" not in html_body
    assert "&lt;img" in html_body
    assert "&lt;script&gt;" in html_body
