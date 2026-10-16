import pytest

from app.auth.verifier import InvalidTokenError, decode_access_token
from tests.auth_stub import install_fake_jwks, mint_token


def test_decodes_a_valid_token(monkeypatch):
    install_fake_jwks(monkeypatch)

    claims = decode_access_token(mint_token())

    assert claims["sub"]
    assert claims["email"] == "jane@example.com"


def test_rejects_an_expired_token(monkeypatch):
    install_fake_jwks(monkeypatch)

    with pytest.raises(InvalidTokenError):
        decode_access_token(mint_token(expires_in_seconds=-10))


def test_rejects_a_wrong_audience(monkeypatch):
    install_fake_jwks(monkeypatch)

    with pytest.raises(InvalidTokenError):
        decode_access_token(mint_token(audience="some-other-audience"))


def test_rejects_a_wrong_issuer(monkeypatch):
    install_fake_jwks(monkeypatch)

    with pytest.raises(InvalidTokenError):
        decode_access_token(mint_token(issuer="https://evil.example.com/auth/v1"))


def test_rejects_a_malformed_token(monkeypatch):
    install_fake_jwks(monkeypatch)

    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-jwt")
