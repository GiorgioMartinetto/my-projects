from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from src.exceptions.product_exceptions.category_exception import (
	CategoryAlreadyExistsException,
)
from src.main import create_app
from src.routers.deps import get_current_user


@pytest.fixture
def app():
	app_instance = create_app()
	yield app_instance
	app_instance.dependency_overrides.clear()


@pytest.fixture
def client(app):
	with TestClient(app) as test_client:
		yield test_client


def _category_stub(category_name: str = "Gaming") -> SimpleNamespace:
	return SimpleNamespace(
		id=uuid4(),
		category_name=category_name,
		created_by="john@example.com",
		created_at=datetime.now(UTC),
	)


def test_category_create_success(client, app, monkeypatch):
	app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
	create_mock = MagicMock(return_value=_category_stub(category_name="Gaming"))
	monkeypatch.setattr("src.routers.v1.category_endpoint.create_new_category", create_mock)

	response = client.post("/category/create", json={"name": "Gaming"})

	assert response.status_code == 201
	body = response.json()
	assert body["category_name"] == "Gaming"
	assert body["created_by"] == "john@example.com"
	create_mock.assert_called_once_with(
		category_name="Gaming", user_email="john@example.com"
	)


def test_category_create_requires_authentication(client):
	response = client.post("/category/create", json={"name": "Gaming"})

	assert response.status_code == 401
	assert response.json()["code"] == "INVALID_TOKEN"


def test_category_create_validation_error(client, app):
	app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}

	response = client.post("/category/create", json={"name": "Gaming1"})

	assert response.status_code == 422
	assert response.json()["code"] == "VALIDATION_ERROR"


def test_category_create_already_exists(client, app, monkeypatch):
	app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
	create_mock = MagicMock(
		side_effect=CategoryAlreadyExistsException(
			message="Category already exists.",
			context={"category_name": "Gaming"},
		)
	)
	monkeypatch.setattr("src.routers.v1.category_endpoint.create_new_category", create_mock)

	response = client.post("/category/create", json={"name": "Gaming"})

	assert response.status_code == 409
	assert response.json()["code"] == "CATEGORY_ALREADY_EXISTS"


def test_category_list_success(client, monkeypatch):
	list_mock = MagicMock(
		return_value=[_category_stub(category_name="Gaming"), _category_stub(category_name="Office")]
	)
	monkeypatch.setattr("src.routers.v1.category_endpoint.get_all_categories", list_mock)

	response = client.get("/category/list")

	assert response.status_code == 200
	body = response.json()
	assert len(body) == 2
	assert body[0]["category_name"] == "Gaming"
	assert body[1]["category_name"] == "Office"
	list_mock.assert_called_once()


def test_category_delete_success(client, app, monkeypatch):
	app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
	delete_mock = MagicMock(
		return_value={"message": "Category deleted successfully.", "category_name": "Gaming"}
	)
	monkeypatch.setattr("src.routers.v1.category_endpoint.delete_category", delete_mock)

	response = client.request("DELETE", "/category/delete", json={"name": "Gaming"})

	assert response.status_code == 200
	assert response.json() == {
		"message": "Category deleted successfully.",
		"category_name": "Gaming",
	}
	delete_mock.assert_called_once_with(category_name="Gaming")


def test_category_delete_requires_authentication(client):
	response = client.request("DELETE", "/category/delete", json={"name": "Gaming"})

	assert response.status_code == 401
	assert response.json()["code"] == "INVALID_TOKEN"

