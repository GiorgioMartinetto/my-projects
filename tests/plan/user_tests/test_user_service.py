import sys
import types
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

# Ensure `src.*` imports resolve when tests run from project root.
APP_DIR = Path(__file__).resolve().parents[3] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.exceptions.user_exception import (
    EmailAlreadyExistsException,
    NewPasswordAndOldPasswordNotMatchException,
    PasswordAndConfirmPasswordNotMatchException,
)
from src.schemas.user_request import UserRegisterRequest, UserUpdateRequest

# user_service importa UserRegisterRequest dal router, creando un ciclo in test unitari.
# Iniettiamo uno stub minimale del modulo router per isolare il servizio.
router_stub = types.ModuleType("src.routers.v1.user_endpoint")
router_stub.UserRegisterRequest = UserRegisterRequest
sys.modules.setdefault("src.routers.v1.user_endpoint", router_stub)

from src.services.users import user_service


@contextmanager
def fake_session_scope(session):
    yield session


def setup_repo_mocks(monkeypatch):
    session = object()
    repo = MagicMock()
    repo_cls = MagicMock(return_value=repo)

    monkeypatch.setattr(
        user_service, "session_scope", lambda: fake_session_scope(session)
    )
    monkeypatch.setattr(user_service, "UserRepository", repo_cls)

    return repo, repo_cls, session


def test_safe_existing_user_returns_true_when_user_exists(monkeypatch):
    repo, repo_cls, session = setup_repo_mocks(monkeypatch)
    repo.get_user_by_email.return_value = SimpleNamespace(email="john@example.com")

    result = user_service._safe_existing_user(email="john@example.com")

    assert result is True
    repo_cls.assert_called_once_with(session)
    repo.get_user_by_email.assert_called_once_with(email="john@example.com")


def test_safe_existing_user_returns_false_when_user_missing(monkeypatch):
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_user_by_email.return_value = None

    result = user_service._safe_existing_user(email="missing@example.com")

    assert result is False


def test_safe_create_user_delegates_to_repository(monkeypatch):
    repo, _, _ = setup_repo_mocks(monkeypatch)
    created_user = SimpleNamespace(email="john@example.com", username="John")
    repo.create_user.return_value = created_user

    result = user_service._safe_create_user(
        email="john@example.com", username="John", password="hashed-pass"
    )

    assert result is created_user
    repo.create_user.assert_called_once_with(
        email="john@example.com",
        username="John",
        hashed_password="hashed-pass",
    )


def test_safe_authenticate_user_returns_none_if_user_not_found(monkeypatch):
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_user_by_email.return_value = None

    result = user_service._safe_authenticate_user(
        email="john@example.com", password="StrongPassw0rd!"
    )

    assert result is None


def test_safe_authenticate_user_returns_none_if_password_is_invalid(monkeypatch):
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_user_by_email.return_value = SimpleNamespace(
        id="user-id",
        email="john@example.com",
        username="John",
        password_hash="stored-hash",
    )
    verify_mock = MagicMock(return_value=False)
    monkeypatch.setattr(user_service, "verify_password", verify_mock)

    result = user_service._safe_authenticate_user(
        email="john@example.com", password="wrong-pass"
    )

    assert result is None
    verify_mock.assert_called_once_with(
        plain_password="wrong-pass", hashed_password="stored-hash"
    )


def test_safe_authenticate_user_returns_detached_user_when_password_is_valid(
    monkeypatch,
):
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_user_by_email.return_value = SimpleNamespace(
        id="user-id",
        email="john@example.com",
        username="John",
        password_hash="stored-hash",
    )
    monkeypatch.setattr(user_service, "verify_password", MagicMock(return_value=True))

    result = user_service._safe_authenticate_user(
        email="john@example.com", password="StrongPassw0rd!"
    )

    assert result is not None
    assert result.id == "user-id"
    assert result.email == "john@example.com"
    assert result.username == "John"


def test_safe_update_user_raises_when_old_password_does_not_match(monkeypatch):
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_user_by_email.return_value = SimpleNamespace(password_hash="stored-hash")
    monkeypatch.setattr(user_service, "verify_password", MagicMock(return_value=False))

    with pytest.raises(NewPasswordAndOldPasswordNotMatchException):
        user_service._safe_update_user(
            fields={"old_password": "OldPassw0rd!", "new_password": "NewPassw0rd!"},
            user_email="john@example.com",
        )

    repo.update_user.assert_not_called()


def test_safe_update_user_hashes_new_password_before_update(monkeypatch):
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_user_by_email.return_value = SimpleNamespace(password_hash="stored-hash")
    updated_user = SimpleNamespace(email="john@example.com", username="Neo")
    repo.update_user.return_value = updated_user

    monkeypatch.setattr(user_service, "verify_password", MagicMock(return_value=True))
    hash_mock = MagicMock(return_value="new-hash")
    monkeypatch.setattr(user_service, "hash_password", hash_mock)

    fields = {
        "old_password": "OldPassw0rd!",
        "new_password": "NewPassw0rd!",
        "username": "Neo",
    }

    result = user_service._safe_update_user(
        fields=fields, user_email="john@example.com"
    )

    assert result is updated_user
    hash_mock.assert_called_once_with("NewPassw0rd!")
    repo.update_user.assert_called_once_with(
        email="john@example.com",
        fields={"username": "Neo", "password_hash": "new-hash"},
    )


def test_safe_delete_user_delegates_to_repository(monkeypatch):
    repo, _, _ = setup_repo_mocks(monkeypatch)
    deleted_user = SimpleNamespace(email="john@example.com")
    repo.delete_user.return_value = deleted_user

    result = user_service._safe_delete_user(email="john@example.com")

    assert result is deleted_user
    repo.delete_user.assert_called_once_with(email="john@example.com")


def test_register_user_raises_when_email_already_exists(monkeypatch):
    monkeypatch.setattr(
        user_service, "_safe_existing_user", MagicMock(return_value=True)
    )

    payload = UserRegisterRequest(
        email="john@example.com",
        name="John",
        password="StrongPassw0rd!",
        confirm_password="StrongPassw0rd!",
    )

    with pytest.raises(EmailAlreadyExistsException):
        user_service.register_user(payload=payload)


def test_register_user_raises_when_passwords_do_not_match(monkeypatch):
    monkeypatch.setattr(
        user_service, "_safe_existing_user", MagicMock(return_value=False)
    )

    payload = UserRegisterRequest(
        email="john@example.com",
        name="John",
        password="StrongPassw0rd!",
        confirm_password="DifferentPassw0rd!",
    )

    with pytest.raises(PasswordAndConfirmPasswordNotMatchException):
        user_service.register_user(payload=payload)


def test_register_user_success_returns_response(monkeypatch):
    monkeypatch.setattr(
        user_service, "_safe_existing_user", MagicMock(return_value=False)
    )
    monkeypatch.setattr(user_service, "hash_password", MagicMock(return_value="hashed"))
    new_user = SimpleNamespace(
        id=str(uuid4()),
        email="john@example.com",
        username="John",
        created_at=datetime.now(UTC),
    )
    create_mock = MagicMock(return_value=new_user)
    monkeypatch.setattr(user_service, "_safe_create_user", create_mock)

    payload = UserRegisterRequest(
        email="john@example.com",
        name="John",
        password="StrongPassw0rd!",
        confirm_password="StrongPassw0rd!",
    )

    result = user_service.register_user(payload=payload)

    assert result.message == "User registered successfully."
    assert result.user.email == "john@example.com"
    create_mock.assert_called_once_with(
        email="john@example.com", username="John", password="hashed"
    )


def test_authenticate_user_returns_none_for_invalid_credentials(monkeypatch):
    monkeypatch.setattr(
        user_service, "_safe_authenticate_user", MagicMock(return_value=None)
    )

    result = user_service.authenticate_user(
        email="john@example.com", password="wrong-pass"
    )

    assert result is None


def test_authenticate_user_returns_login_response_for_valid_credentials(monkeypatch):
    monkeypatch.setattr(
        user_service,
        "_safe_authenticate_user",
        MagicMock(return_value=SimpleNamespace(email="john@example.com")),
    )

    result = user_service.authenticate_user(
        email="john@example.com", password="StrongPassw0rd!"
    )

    assert result is not None
    assert result.message == "User authenticated successfully."
    assert result.email == "john@example.com"


def test_update_user_data_filters_none_fields_before_updating(monkeypatch):
    update_mock = MagicMock(return_value=SimpleNamespace(email="john@example.com"))
    monkeypatch.setattr(user_service, "_safe_update_user", update_mock)

    payload = UserUpdateRequest(username="Neo")
    current_user = {"email": "john@example.com"}

    result = user_service.update_user_data(
        user_to_update=payload, current_user=current_user
    )

    assert result.email == "john@example.com"
    update_mock.assert_called_once_with(
        fields={"username": "Neo"}, user_email="john@example.com"
    )


def test_user_deletion_returns_response_when_user_is_deleted(monkeypatch):
    monkeypatch.setattr(
        user_service,
        "_safe_delete_user",
        MagicMock(return_value=SimpleNamespace(email="john@example.com")),
    )

    result = user_service.user_deletion(user_email="john@example.com")

    assert result is not None
    assert result.message == "User deleted successfully."
    assert result.email == "john@example.com"


def test_user_deletion_returns_none_when_user_not_found(monkeypatch):
    monkeypatch.setattr(user_service, "_safe_delete_user", MagicMock(return_value=None))

    result = user_service.user_deletion(user_email="missing@example.com")

    assert result is None
