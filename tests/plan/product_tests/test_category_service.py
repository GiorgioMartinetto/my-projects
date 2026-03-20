from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from src.exceptions.product_exceptions.category_exception import (
	CategoryAlreadyExistsException,
	CategoryNotFoundException,
)
from src.services.products import category_service


@contextmanager
def fake_session_scope(session: object):
	yield session


def setup_repo_mocks(monkeypatch: pytest.MonkeyPatch):
	session = object()
	repo = MagicMock()
	repo_cls = MagicMock(return_value=repo)

	monkeypatch.setattr(
		category_service, "session_scope", lambda: fake_session_scope(session)
	)
	monkeypatch.setattr(category_service, "CategoryRepository", repo_cls)
	return repo, repo_cls, session


def _category_stub(category_name: str = "Gaming") -> SimpleNamespace:
	return SimpleNamespace(
		id="category-id",
		category_name=category_name,
		created_by="john@example.com",
	)


def test_safe_create_new_category_delegates_to_repository(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	repo, repo_cls, session = setup_repo_mocks(monkeypatch)
	category = _category_stub(category_name="Gaming")
	repo.create_category.return_value = category

	result = category_service._safe_create_new_category(
		category_name="Gaming",
		user_email="john@example.com",
	)

	assert result is category
	repo_cls.assert_called_once_with(session)
	repo.create_category.assert_called_once_with(
		category_name="Gaming",
		user_email="john@example.com",
	)


def test_get_category_by_name_returns_category(monkeypatch: pytest.MonkeyPatch) -> None:
	repo, repo_cls, session = setup_repo_mocks(monkeypatch)
	category = _category_stub(category_name="Gaming")
	repo.get_category_by_name.return_value = category

	result = category_service._get_category_by_name(category_name="Gaming")

	assert result is category
	repo_cls.assert_called_once_with(session)
	repo.get_category_by_name.assert_called_once_with("Gaming")


def test_safe_all_categories_returns_categories(monkeypatch: pytest.MonkeyPatch) -> None:
	repo, repo_cls, session = setup_repo_mocks(monkeypatch)
	categories = [_category_stub(category_name="Gaming"), _category_stub(category_name="Office")]
	repo.get_all_categories.return_value = categories

	result = category_service._safe_all_categories()

	assert result == categories
	repo_cls.assert_called_once_with(session)
	repo.get_all_categories.assert_called_once_with()


def test_safe_delete_category_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
	repo, _, _ = setup_repo_mocks(monkeypatch)
	repo.get_category_by_name.return_value = None

	with pytest.raises(CategoryNotFoundException) as exc_info:
		category_service._safe_delete_category(category_name="Ghost")

	assert exc_info.value.context == {"category_name": "Ghost"}
	repo.delete_category.assert_not_called()


def test_safe_delete_category_deletes_existing_category(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	repo, _, _ = setup_repo_mocks(monkeypatch)
	category = _category_stub(category_name="Gaming")
	repo.get_category_by_name.return_value = category
	repo.delete_category.return_value = True

	result = category_service._safe_delete_category(category_name="Gaming")

	assert result is True
	repo.delete_category.assert_called_once_with(category=category)


def test_create_new_category_raises_when_category_exists(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	lookup_mock = MagicMock(return_value=_category_stub(category_name="Gaming"))
	create_mock = MagicMock()
	monkeypatch.setattr(category_service, "_get_category_by_name", lookup_mock)
	monkeypatch.setattr(category_service, "_safe_create_new_category", create_mock)

	with pytest.raises(CategoryAlreadyExistsException) as exc_info:
		category_service.create_new_category(
			category_name="Gaming",
			user_email="john@example.com",
		)

	assert exc_info.value.context == {"category_name": "Gaming"}
	create_mock.assert_not_called()


def test_create_new_category_success(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(category_service, "_get_category_by_name", MagicMock(return_value=None))
	created = _category_stub(category_name="Gaming")
	create_mock = MagicMock(return_value=created)
	monkeypatch.setattr(category_service, "_safe_create_new_category", create_mock)

	result = category_service.create_new_category(
		category_name="Gaming",
		user_email="john@example.com",
	)

	assert result is created
	create_mock.assert_called_once_with("Gaming", "john@example.com")


def test_get_all_categories_raises_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(category_service, "_safe_all_categories", MagicMock(return_value=[]))

	with pytest.raises(CategoryNotFoundException) as exc_info:
		category_service.get_all_categories()

	assert exc_info.value.context == {}


def test_get_all_categories_returns_list(monkeypatch: pytest.MonkeyPatch) -> None:
	categories = [_category_stub(category_name="Gaming")]
	safe_mock = MagicMock(return_value=categories)
	monkeypatch.setattr(category_service, "_safe_all_categories", safe_mock)

	result = category_service.get_all_categories()

	assert result == categories
	safe_mock.assert_called_once_with()


def test_delete_category_returns_success_and_logs(monkeypatch: pytest.MonkeyPatch) -> None:
	delete_mock = MagicMock(return_value=True)
	success_log_mock = MagicMock()
	error_log_mock = MagicMock()

	monkeypatch.setattr(category_service, "_safe_delete_category", delete_mock)
	monkeypatch.setattr(category_service.logger, "success", success_log_mock)
	monkeypatch.setattr(category_service.logger, "error", error_log_mock)

	result = category_service.delete_category(category_name="Gaming")

	assert result == {
		"message": "Category deleted successfully.",
		"category_name": "Gaming",
	}
	delete_mock.assert_called_once_with(category_name="Gaming")
	success_log_mock.assert_called_once_with("Category Gaming deleted.")
	error_log_mock.assert_not_called()


def test_delete_category_returns_error_and_logs(monkeypatch: pytest.MonkeyPatch) -> None:
	delete_mock = MagicMock(return_value=False)
	success_log_mock = MagicMock()
	error_log_mock = MagicMock()

	monkeypatch.setattr(category_service, "_safe_delete_category", delete_mock)
	monkeypatch.setattr(category_service.logger, "success", success_log_mock)
	monkeypatch.setattr(category_service.logger, "error", error_log_mock)

	result = category_service.delete_category(category_name="Gaming")

	assert result == {
		"message": "Category can't be deleted.",
		"category_name": "Gaming",
	}
	delete_mock.assert_called_once_with(category_name="Gaming")
	success_log_mock.assert_not_called()
	error_log_mock.assert_called_once_with("Category Gaming not found.")


