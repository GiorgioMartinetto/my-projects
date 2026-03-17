import sys
from pathlib import Path

# Ensure `src.*` imports resolve when tests run from project root.
APP_DIR = Path(__file__).resolve().parents[2] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import JWTError
from src.exceptions.user_exception import InvalidTokenException
from src.main import create_app
from src.routers.deps import get_current_user
from src.schemas.user_response import UserLoginResponse, UserRegisterResponse


@pytest.fixture
def app():
    app_instance = create_app()
    yield app_instance
    app_instance.dependency_overrides.clear()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def test_registration_success(client, monkeypatch):
    expected_response = UserRegisterResponse.model_validate(
        {
            "message": "User registered successfully.",
            "user": {
                "id": str(uuid4()),
                "email": "john@example.com",
                "username": "John",
                "created_at": datetime.now(UTC),
            },
        }
    )
    register_mock = MagicMock(return_value=expected_response)
    monkeypatch.setattr("src.routers.v1.user_endpoint.register_user", register_mock)

    response = client.post(
        "/user/auth/registration",
        json={
            "email": "john@example.com",
            "name": "John",
            "password": "StrongPassw0rd!",
            "confirm_password": "StrongPassw0rd!",
        },
    )

    assert response.status_code == 201
    assert response.json()["message"] == "User registered successfully."
    assert response.json()["user"]["email"] == "john@example.com"
    register_mock.assert_called_once()


def test_login_success_sets_auth_cookie(client, monkeypatch):
    auth_mock = MagicMock(
        return_value=UserLoginResponse.model_validate(
            {"message": "User authenticated successfully.", "email": "john@example.com"}
        )
    )
    token_mock = MagicMock(return_value="fake.jwt.token")
    monkeypatch.setattr("src.routers.v1.user_endpoint.authenticate_user", auth_mock)
    monkeypatch.setattr("src.routers.v1.user_endpoint.create_access_token", token_mock)

    response = client.post(
        "/user/auth/login",
        json={"email": "john@example.com", "password": "StrongPassw0rd!"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"
    assert "access_token=fake.jwt.token" in response.headers.get("set-cookie", "")
    auth_mock.assert_called_once_with(
        email="john@example.com", password="StrongPassw0rd!"
    )


def test_login_invalid_credentials_returns_401(client, monkeypatch):
    auth_mock = MagicMock(return_value=None)
    monkeypatch.setattr("src.routers.v1.user_endpoint.authenticate_user", auth_mock)

    response = client.post(
        "/user/auth/login",
        json={"email": "john@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_logout_success_with_current_user_override(client, app):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}

    response = client.post("/user/auth/logout")

    assert response.status_code == 200
    assert response.json() == {
        "message": "User logged out successfully.",
        "email": "john@example.com",
    }
    assert "access_token=" in response.headers.get("set-cookie", "")


def test_logout_requires_authentication(client):
    response = client.post("/user/auth/logout")

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


def test_update_profile_without_email_change_does_not_refresh_cookie(
    client, app, monkeypatch
):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
    update_mock = MagicMock(return_value=SimpleNamespace(email="john@example.com"))
    token_mock = MagicMock(return_value="unused.token")
    monkeypatch.setattr("src.routers.v1.user_endpoint.update_user_data", update_mock)
    monkeypatch.setattr("src.routers.v1.user_endpoint.create_access_token", token_mock)

    response = client.put("/user/profile/update", json={"username": "John Updated"})

    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"
    assert "set-cookie" not in response.headers
    token_mock.assert_not_called()


def test_update_profile_with_email_change_refreshes_cookie(client, app, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
    update_mock = MagicMock(return_value=SimpleNamespace(email="new@example.com"))
    token_mock = MagicMock(return_value="new.token")
    monkeypatch.setattr("src.routers.v1.user_endpoint.update_user_data", update_mock)
    monkeypatch.setattr("src.routers.v1.user_endpoint.create_access_token", token_mock)

    response = client.put("/user/profile/update", json={"email": "new@example.com"})

    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
    assert "access_token=new.token" in response.headers.get("set-cookie", "")
    token_mock.assert_called_once()


def test_update_profile_with_no_fields_returns_422(client, app):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}

    response = client.put("/user/profile/update", json={})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_delete_account_success(client, app, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
    delete_mock = MagicMock(return_value=True)
    monkeypatch.setattr("src.routers.v1.user_endpoint.user_deletion", delete_mock)

    response = client.delete("/user/profile/delete")

    assert response.status_code == 200
    assert response.json() == {
        "message": "User deleted successfully.",
        "email": "john@example.com",
    }
    assert "access_token=" in response.headers.get("set-cookie", "")
    delete_mock.assert_called_once_with(user_email="john@example.com")


def test_delete_account_user_not_found_returns_404(client, app, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
    monkeypatch.setattr(
        "src.routers.v1.user_endpoint.user_deletion", MagicMock(return_value=None)
    )

    response = client.delete("/user/profile/delete")

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


def test_get_current_user_returns_payload_when_token_valid(monkeypatch):
    request = MagicMock()
    request.cookies = {"access_token": "valid.token"}
    payload = {"sub": "john@example.com", "role": "user"}
    monkeypatch.setattr("src.routers.deps.jwt.decode", MagicMock(return_value=payload))

    result = get_current_user(request)

    assert result == {"email": "john@example.com", "payload": payload}


def test_get_current_user_raises_if_token_missing():
    request = MagicMock()
    request.cookies = {}

    with pytest.raises(InvalidTokenException) as exc_info:
        get_current_user(request)

    assert exc_info.value.status_code == 401


def test_get_current_user_raises_if_token_invalid(monkeypatch):
    request = MagicMock()
    request.cookies = {"access_token": "invalid.token"}
    monkeypatch.setattr(
        "src.routers.deps.jwt.decode", MagicMock(side_effect=JWTError("invalid"))
    )

    with pytest.raises(InvalidTokenException) as exc_info:
        get_current_user(request)

    assert exc_info.value.status_code == 401


def test_get_current_user_raises_if_sub_missing(monkeypatch):
    request = MagicMock()
    request.cookies = {"access_token": "token.without.sub"}
    monkeypatch.setattr("src.routers.deps.jwt.decode", MagicMock(return_value={}))

    with pytest.raises(InvalidTokenException) as exc_info:
        get_current_user(request)

    assert exc_info.value.status_code == 401
