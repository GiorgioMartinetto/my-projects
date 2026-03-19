from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from src.exceptions.product_exceptions.product_exception import ProductNotFoundException
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


def _product_stub(name: str = "Keyboard") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        description="Mechanical keyboard",
        price=129.99,
        quantity=5,
        created_by="john@example.com",
        created_at=datetime.now(UTC),
    )


def test_product_creation_success(client, app, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
    creation_mock = MagicMock(return_value=_product_stub(name="Mouse"))
    monkeypatch.setattr("src.routers.v1.product_endpoint.product_creation", creation_mock)

    response = client.post(
        "/products/creation",
        json={
            "name": "Mouse",
            "price": 59.9,
            "description": "Wireless mouse",
            "quantity": 10,
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Mouse"
    assert response.json()["created_by"] == "john@example.com"
    creation_mock.assert_called_once()
    assert creation_mock.call_args.kwargs["user_email"] == "john@example.com"
    assert creation_mock.call_args.kwargs["product_data"].name == "Mouse"


def test_product_creation_requires_authentication(client):
    response = client.post(
        "/products/creation",
        json={
            "name": "Mouse",
            "price": 59.9,
            "description": "Wireless mouse",
            "quantity": 10,
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


def test_product_creation_validation_error(client, app):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}

    response = client.post(
        "/products/creation",
        json={
            "name": "Mouse",
            "price": -1,
            "description": "Wireless mouse",
            "quantity": 10,
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_product_update_success(client, app, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
    update_mock = MagicMock(return_value=_product_stub(name="Mouse V2"))
    monkeypatch.setattr("src.routers.v1.product_endpoint.product_to_update", update_mock)

    response = client.patch(
        "/products/update",
        json={
            "name": "Mouse",
            "new_name": "Mouse V2",
            "price": 79.9,
            "quantity": 8,
        },
    )

    assert response.status_code == 202
    assert response.json()["name"] == "Mouse V2"
    update_mock.assert_called_once()
    assert update_mock.call_args.kwargs["product_owner"] == "john@example.com"
    assert update_mock.call_args.kwargs["product_data"].name == "Mouse"


def test_product_delete_success(client, app, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {"email": "john@example.com"}
    delete_mock = MagicMock(return_value={"message": "Product deleted.", "name": "Mouse"})
    monkeypatch.setattr("src.routers.v1.product_endpoint.product_delete", delete_mock)

    response = client.request("DELETE", "/products/delete", json={"name": "Mouse"})

    assert response.status_code == 200
    assert response.json() == {"message": "Product deleted.", "name": "Mouse"}
    delete_mock.assert_called_once()
    assert delete_mock.call_args.kwargs["product_owner"] == "john@example.com"
    assert delete_mock.call_args.kwargs["product"].name == "Mouse"


def test_product_all_success(client, monkeypatch):
    products_mock = MagicMock(return_value=[_product_stub(name="Mouse"), _product_stub(name="Keyboard")])
    monkeypatch.setattr("src.routers.v1.product_endpoint.get_all_products", products_mock)

    response = client.get("/products/all")

    assert response.status_code == 200
    body = response.json()
    assert len(body["products"]) == 2
    assert body["products"][0]["name"] == "Mouse"
    assert body["products"][1]["name"] == "Keyboard"
    products_mock.assert_called_once()


def test_product_get_success(client, monkeypatch):
    single_mock = MagicMock(return_value=_product_stub(name="Mouse"))
    monkeypatch.setattr("src.routers.v1.product_endpoint.get_single_product", single_mock)

    response = client.get("/products/Mouse")

    assert response.status_code == 200
    assert response.json()["name"] == "Mouse"
    single_mock.assert_called_once_with(product_name="Mouse")


def test_product_get_not_found_returns_409(client, monkeypatch):
    single_mock = MagicMock(
        side_effect=ProductNotFoundException(
            message="Product not found.",
            context={"product_name": "Ghost", "product_owner": ""},
        )
    )
    monkeypatch.setattr("src.routers.v1.product_endpoint.get_single_product", single_mock)

    response = client.get("/products/Ghost")

    assert response.status_code == 409
    assert response.json()["code"] == "PRODUCT_NOT_FOUND"

