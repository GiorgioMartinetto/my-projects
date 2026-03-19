import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Ensure `src.*` imports resolve when tests run from project root.
APP_DIR = Path(__file__).resolve().parents[3] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.exceptions.product_exceptions.product_exception import (
    ProductAlreadyExistsException,
    ProductCanBeDeleteOnlyByTheCreatorException,
    ProductCanOnlyBeModifiedByTheCreatorException,
    ProductNotFoundException,
)
from src.schemas.product_request import (
    ProductCreationRequest,
    ProductDeleteRequest,
    ProductUpdateRequest,
)
from src.services.products import product_service


@contextmanager
def fake_session_scope(session: object):
    yield session


def setup_repo_mocks(monkeypatch: pytest.MonkeyPatch):
    session = object()
    repo = MagicMock()
    repo_cls = MagicMock(return_value=repo)

    monkeypatch.setattr(
        product_service, "session_scope", lambda: fake_session_scope(session)
    )
    monkeypatch.setattr(product_service, "ProductRepository", repo_cls)

    return repo, repo_cls, session


def _product_stub(
    name: str = "Keyboard", created_by: str = "john@example.com"
) -> SimpleNamespace:
    return SimpleNamespace(
        id="product-id",
        name=name,
        description="Mechanical keyboard",
        price=129.99,
        quantity=5,
        created_by=created_by,
    )


def test_safe_get_product_by_name_returns_product(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, repo_cls, session = setup_repo_mocks(monkeypatch)
    product = _product_stub(name="Mouse")
    repo.get_product_by_name.return_value = product

    result = product_service._safe_get_product_by_name(name="Mouse")

    assert result is product
    repo_cls.assert_called_once_with(session)
    repo.get_product_by_name.assert_called_once_with(name="Mouse")


def test_safe_get_product_by_name_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_product_by_name.return_value = None

    result = product_service._safe_get_product_by_name(name="Ghost")

    assert result is None


def test_safe_product_creation_delegates_to_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    product = _product_stub(name="Mouse")
    repo.create_product.return_value = product

    result = product_service._safe_product_creation(
        name="Mouse",
        price=59.9,
        quantity=10,
        email="john@example.com",
        description="Wireless mouse",
    )

    assert result is product
    repo.create_product.assert_called_once_with(
        name="Mouse",
        price=59.9,
        quantity=10,
        email="john@example.com",
        description="Wireless mouse",
    )


def test_safe_product_update_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_product_by_name.return_value = None

    with pytest.raises(ProductNotFoundException) as exc_info:
        product_service._safe_product_update(
            fields={"name": "Ghost", "price": 10.0},
            product_owner="john@example.com",
        )

    assert exc_info.value.context == {
        "product_name": "Ghost",
        "product_owner": "john@example.com",
    }
    repo.update_product.assert_not_called()


def test_safe_product_update_raises_not_found_when_name_is_missing_in_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_product_by_name.return_value = None

    with pytest.raises(ProductNotFoundException) as exc_info:
        product_service._safe_product_update(
            fields={"price": 10.0},
            product_owner="john@example.com",
        )

    assert exc_info.value.context == {
        "product_name": "",
        "product_owner": "john@example.com",
    }
    repo.update_product.assert_not_called()


def test_safe_product_update_raises_when_owner_is_not_creator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_product_by_name.return_value = _product_stub(created_by="owner@example.com")

    with pytest.raises(ProductCanOnlyBeModifiedByTheCreatorException) as exc_info:
        product_service._safe_product_update(
            fields={"name": "Keyboard", "price": 99.9},
            product_owner="john@example.com",
        )

    assert exc_info.value.context == {
        "product_name": "Keyboard",
        "product_owner": "john@example.com",
    }
    repo.update_product.assert_not_called()


def test_safe_product_update_maps_new_name_and_updates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    existing = _product_stub(name="Keyboard", created_by="john@example.com")
    updated = _product_stub(name="Keyboard Pro", created_by="john@example.com")

    repo.get_product_by_name.return_value = existing
    repo.update_product.return_value = updated

    fields = {"name": "Keyboard", "new_name": "Keyboard Pro", "quantity": 9}
    result = product_service._safe_product_update(
        fields=fields,
        product_owner="john@example.com",
    )

    assert result is updated
    repo.update_product.assert_called_once_with(
        fields={"name": "Keyboard Pro", "quantity": 9},
        product=existing,
    )


def test_safe_product_deletion_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_product_by_name.return_value = None

    with pytest.raises(ProductNotFoundException) as exc_info:
        product_service._safe_product_deletion(
            name="Ghost",
            product_owner="john@example.com",
        )

    assert exc_info.value.context == {
        "product_name": "Ghost",
        "product_owner": "john@example.com",
    }
    repo.delete_product.assert_not_called()


def test_safe_product_deletion_raises_when_owner_is_not_creator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_product_by_name.return_value = _product_stub(created_by="owner@example.com")

    with pytest.raises(ProductCanBeDeleteOnlyByTheCreatorException) as exc_info:
        product_service._safe_product_deletion(
            name="Keyboard",
            product_owner="john@example.com",
        )

    assert exc_info.value.context == {
        "product_name": "Keyboard",
        "product_owner": "john@example.com",
    }
    repo.delete_product.assert_not_called()


def test_safe_product_deletion_returns_repository_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    existing = _product_stub(name="Keyboard", created_by="john@example.com")
    repo.get_product_by_name.return_value = existing
    repo.delete_product.return_value = True

    result = product_service._safe_product_deletion(
        name="Keyboard",
        product_owner="john@example.com",
    )

    assert result is True
    repo.delete_product.assert_called_once_with(product=existing)


@pytest.mark.parametrize("products", [[_product_stub(name="Mouse")], []])
def test_safe_get_all_products_returns_list_or_raises(
    monkeypatch: pytest.MonkeyPatch, products: list[SimpleNamespace]
) -> None:
    repo, _, _ = setup_repo_mocks(monkeypatch)
    repo.get_all_products.return_value = products

    if products:
        result = product_service._safe_get_all_products()
        assert result == products
    else:
        with pytest.raises(ProductNotFoundException) as exc_info:
            product_service._safe_get_all_products()
        assert exc_info.value.context == {"product_name": "", "product_owner": ""}


def test_product_creation_raises_when_product_already_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_mock = MagicMock(return_value=_product_stub(name="Mouse"))
    creation_mock = MagicMock()
    monkeypatch.setattr(product_service, "_safe_get_product_by_name", existing_mock)
    monkeypatch.setattr(product_service, "_safe_product_creation", creation_mock)

    payload = ProductCreationRequest(
        name="Mouse",
        price=59.9,
        description="Wireless mouse",
        quantity=10,
    )

    with pytest.raises(ProductAlreadyExistsException) as exc_info:
        product_service.product_creation(product_data=payload, user_email="john@example.com")

    assert exc_info.value.context == {"product_name": "Mouse"}
    creation_mock.assert_not_called()


def test_product_creation_success_delegates_to_safe_creator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(product_service, "_safe_get_product_by_name", MagicMock(return_value=None))
    created = _product_stub(name="Mouse", created_by="john@example.com")
    creation_mock = MagicMock(return_value=created)
    monkeypatch.setattr(product_service, "_safe_product_creation", creation_mock)

    payload = ProductCreationRequest(name="Mouse", price=59.9, quantity=10)

    result = product_service.product_creation(
        product_data=payload,
        user_email="john@example.com",
    )

    assert result is created
    creation_mock.assert_called_once_with(
        name="Mouse",
        price=59.9,
        quantity=10,
        email="john@example.com",
        description=None,
    )


def test_product_to_update_filters_none_values_before_safe_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updated = _product_stub(name="Keyboard Pro")
    update_mock = MagicMock(return_value=updated)
    monkeypatch.setattr(product_service, "_safe_product_update", update_mock)

    payload = ProductUpdateRequest(name="Keyboard", new_name="Keyboard Pro")

    result = product_service.product_to_update(
        product_data=payload,
        product_owner="john@example.com",
    )

    assert result is updated
    update_mock.assert_called_once_with(
        fields={"name": "Keyboard", "new_name": "Keyboard Pro"},
        product_owner="john@example.com",
    )


def test_product_to_update_with_only_name_passes_minimal_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updated = _product_stub(name="Keyboard")
    update_mock = MagicMock(return_value=updated)
    monkeypatch.setattr(product_service, "_safe_product_update", update_mock)

    payload = ProductUpdateRequest(name="Keyboard")

    result = product_service.product_to_update(
        product_data=payload,
        product_owner="john@example.com",
    )

    assert result is updated
    update_mock.assert_called_once_with(
        fields={"name": "Keyboard"},
        product_owner="john@example.com",
    )


def test_product_delete_returns_success_response_and_logs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deletion_mock = MagicMock(return_value=True)
    success_log_mock = MagicMock()
    error_log_mock = MagicMock()

    monkeypatch.setattr(product_service, "_safe_product_deletion", deletion_mock)
    monkeypatch.setattr(product_service.logger, "success", success_log_mock)
    monkeypatch.setattr(product_service.logger, "error", error_log_mock)

    result = product_service.product_delete(
        product=ProductDeleteRequest(name="Keyboard"),
        product_owner="john@example.com",
    )

    assert result == {"message": "Product deleted.", "name": "Keyboard"}
    deletion_mock.assert_called_once_with(
        name="Keyboard",
        product_owner="john@example.com",
    )
    success_log_mock.assert_called_once_with("Product deleted successfully.")
    error_log_mock.assert_not_called()


def test_product_delete_returns_failure_response_and_logs_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deletion_mock = MagicMock(return_value=False)
    success_log_mock = MagicMock()
    error_log_mock = MagicMock()

    monkeypatch.setattr(product_service, "_safe_product_deletion", deletion_mock)
    monkeypatch.setattr(product_service.logger, "success", success_log_mock)
    monkeypatch.setattr(product_service.logger, "error", error_log_mock)

    result = product_service.product_delete(
        product=ProductDeleteRequest(name="Keyboard"),
        product_owner="john@example.com",
    )

    assert result == {"message": "Product can't be deleted.", "name": "Keyboard"}
    success_log_mock.assert_not_called()
    error_log_mock.assert_called_once_with("Product not deleted.")


def test_get_all_products_delegates_to_safe_function(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    products = [_product_stub(name="Mouse"), _product_stub(name="Keyboard")]
    safe_mock = MagicMock(return_value=products)
    monkeypatch.setattr(product_service, "_safe_get_all_products", safe_mock)

    result = product_service.get_all_products()

    assert result == products
    safe_mock.assert_called_once_with()


def test_get_single_product_returns_product_when_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = _product_stub(name="Mouse")
    lookup_mock = MagicMock(return_value=product)
    monkeypatch.setattr(product_service, "_safe_get_product_by_name", lookup_mock)

    result = product_service.get_single_product(product_name="Mouse")

    assert result is product
    lookup_mock.assert_called_once_with(name="Mouse")


def test_get_single_product_raises_not_found_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(product_service, "_safe_get_product_by_name", MagicMock(return_value=None))

    with pytest.raises(ProductNotFoundException) as exc_info:
        product_service.get_single_product(product_name="Ghost")

    assert exc_info.value.context == {
        "product_name": "Ghost",
        "product_owner": "",
    }


