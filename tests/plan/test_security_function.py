import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from jose import jwt

# Ensure `src.*` imports resolve when tests run from project root.
APP_DIR = Path(__file__).resolve().parents[2] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.core import security


def test_hash_password_returns_bcrypt_hash() -> None:
    plain_fakepw = "StrongPassw0rd!"

    hashed_password = security.hash_password(plain_fakepw)

    assert isinstance(hashed_password, str)
    assert hashed_password != plain_fakepw
    assert hashed_password.startswith("$2")


def test_verify_password_returns_true_with_valid_password() -> None:
    plain_fakepw = "StrongPassw0rd!"
    hashed_password = security.hash_password(plain_fakepw)

    assert security.verify_password(plain_fakepw, hashed_password) is True


def test_verify_password_returns_false_with_invalid_password() -> None:
    hashed_password = security.hash_password("StrongPassw0rd!")

    assert security.verify_password("WrongPassword!", hashed_password) is False


def test_verify_password_accepts_hash_as_bytes() -> None:
    plain_fakepw = "StrongPassw0rd!"
    hashed_password = security.hash_password(plain_fakepw)

    assert (
        security.verify_password(plain_fakepw, hashed_password.encode("utf-8")) is True
    )


def test_create_access_token_adds_default_exp_claim(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        security.settings.token, "secret_key", "test-secret", raising=False
    )
    monkeypatch.setattr(security.settings.token, "algorithm", "HS256", raising=False)

    payload = {"sub": "user-123", "role": "admin"}
    before = datetime.now(UTC)

    token = security.create_access_token(payload)

    after = datetime.now(UTC)
    decoded = jwt.decode(
        token,
        security.settings.token.secret_key,
        algorithms=[security.settings.token.algorithm],
    )

    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "admin"
    assert "exp" in decoded
    assert "exp" not in payload

    exp_dt = datetime.fromtimestamp(decoded["exp"], UTC)
    expected_min = before + timedelta(minutes=15) - timedelta(seconds=1)
    expected_max = after + timedelta(minutes=15) + timedelta(seconds=1)
    assert expected_min <= exp_dt <= expected_max


def test_create_access_token_uses_custom_expiration(monkeypatch) -> None:
    monkeypatch.setattr(
        security.settings.token, "secret_key", "test-secret", raising=False
    )
    monkeypatch.setattr(security.settings.token, "algorithm", "HS256", raising=False)

    payload = {"sub": "user-123"}
    expires_delta = timedelta(minutes=3)
    before = datetime.now(UTC)

    token = security.create_access_token(payload, expires_delta=expires_delta)

    after = datetime.now(UTC)
    decoded = jwt.decode(
        token,
        security.settings.token.secret_key,
        algorithms=[security.settings.token.algorithm],
    )
    exp_dt = datetime.fromtimestamp(decoded["exp"], UTC)

    expected_min = before + expires_delta - timedelta(seconds=1)
    expected_max = after + expires_delta + timedelta(seconds=1)
    assert expected_min <= exp_dt <= expected_max
