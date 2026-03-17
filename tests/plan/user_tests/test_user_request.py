import sys
from pathlib import Path

# Ensure `src.*` imports resolve when tests run from project root.
APP_DIR = Path(__file__).resolve().parents[3] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pytest
from pydantic import ValidationError
from src.schemas.user_request import (
    UserLoginRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)


def test_user_register_request_valid_payload() -> None:
    payload = UserRegisterRequest(
        email="john@example.com",
        name="  John  ",
        password="StrongPassw0rd!",
        confirm_password="StrongPassw0rd!",
    )

    assert payload.email == "john@example.com"
    assert payload.name == "John"


@pytest.mark.parametrize(
    "password,error_fragment",
    [
        ("Ab1!xyz", "at least 8 characters"),
        ("Abcdefg!", "at least one digit"),
        ("ABCDEFG1!", "at least one lowercase"),
        ("abcdefg1!", "at least one uppercase"),
        ("Abcdefg12", "at least one special character"),
    ],
)
def test_user_register_request_rejects_weak_password(
    password: str, error_fragment: str
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(
            email="john@example.com",
            name="John",
            password=password,
            confirm_password=password,
        )

    assert error_fragment in str(exc_info.value)


def test_user_register_request_rejects_short_name_after_trim() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(
            email="john@example.com",
            name="  J  ",
            password="StrongPassw0rd!",
            confirm_password="StrongPassw0rd!",
        )

    assert "Name must be at least 2 characters long." in str(exc_info.value)


def test_user_register_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserRegisterRequest(
            email="not-an-email",
            name="John",
            password="StrongPassw0rd!",
            confirm_password="StrongPassw0rd!",
        )


def test_user_login_request_valid_payload() -> None:
    payload = UserLoginRequest(email="john@example.com", password="StrongPassw0rd!")

    assert payload.email == "john@example.com"
    assert payload.password == "StrongPassw0rd!"


def test_user_login_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserLoginRequest(email="invalid-email", password="StrongPassw0rd!")


def test_user_update_request_accepts_single_email_update() -> None:
    payload = UserUpdateRequest(email="new@example.com")

    assert payload.email == "new@example.com"
    assert payload.username is None


def test_user_update_request_trims_username() -> None:
    payload = UserUpdateRequest(username="  Neo  ")

    assert payload.username == "Neo"


def test_user_update_request_rejects_short_username_after_trim() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserUpdateRequest(username="  N  ")

    assert "Name must be at least 2 characters long." in str(exc_info.value)


def test_user_update_request_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserUpdateRequest()

    assert "At least one field must be provided for update." in str(exc_info.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"old_password": "OldPassw0rd!"},
        {"new_password": "NewPassw0rd!"},
    ],
)
def test_user_update_request_requires_old_and_new_password_together(
    payload: dict,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserUpdateRequest(**payload)

    assert "Both old_password and new_password must be provided together." in str(
        exc_info.value
    )


def test_user_update_request_rejects_weak_new_password() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserUpdateRequest(old_password="OldPassw0rd!", new_password="weak")

    assert "Password must be at least 8 characters long." in str(exc_info.value)
