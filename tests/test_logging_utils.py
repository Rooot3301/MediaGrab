from app.utils.logging_utils import redact_secrets


def test_redacts_headers_and_url_secrets():
    value = redact_secrets("token=abc https://example.com/v?id=1&signature=secret")
    assert "abc" not in value and "secret" not in value and "id=1" in value

