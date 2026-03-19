import pytest
from pydantic import ValidationError

from src.schemas.product_request import (
    ProductCreationRequest,
    ProductDeleteRequest,
    ProductUpdateRequest,
)


def _assert_has_field_error(
    exc: ValidationError, field_name: str, expected_fragment: str | None = None
) -> None:
    """Assert helper to keep error checks readable across parametrized tests."""
    errors = exc.errors()
    matching_errors = [
        error
        for error in errors
        if error.get("loc") and error["loc"][-1] == field_name
    ]
    assert matching_errors, f"No validation error found for field: {field_name}"

    if expected_fragment is not None:
        assert any(expected_fragment in error.get("msg", "") for error in matching_errors)


class TestProductCreationRequest:
    def test_valid_payload(self) -> None:
        payload = ProductCreationRequest(
            name="Keyboard",
            price=129.99,
            description="Mechanical keyboard",
            quantity=5,
        )

        assert payload.name == "Keyboard"
        assert payload.price == 129.99
        assert payload.description == "Mechanical keyboard"
        assert payload.quantity == 5

    def test_valid_payload_without_description(self) -> None:
        payload = ProductCreationRequest(name="Mouse", price=59.9, quantity=10)

        assert payload.description is None

    @pytest.mark.parametrize("invalid_price", [0, -1, -0.01])
    def test_rejects_non_positive_price(self, invalid_price: float) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProductCreationRequest(
                name="Mouse",
                price=invalid_price,
                description="Wireless mouse",
                quantity=10,
            )

        _assert_has_field_error(
            exc_info.value,
            "price",
            "price_must_be_greater_than_zero",
        )

    @pytest.mark.parametrize("invalid_quantity", [0, -1, -10])
    def test_rejects_non_positive_quantity(self, invalid_quantity: int) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProductCreationRequest(
                name="Mouse",
                price=59.9,
                description="Wireless mouse",
                quantity=invalid_quantity,
            )

        _assert_has_field_error(
            exc_info.value,
            "quantity",
            "quantity_must_be_greater_than_zero",
        )

    @pytest.mark.parametrize("missing_field", ["name", "price", "quantity"])
    def test_rejects_missing_required_fields(self, missing_field: str) -> None:
        payload = {
            "name": "Mouse",
            "price": 59.9,
            "description": "Wireless mouse",
            "quantity": 10,
        }
        payload.pop(missing_field)

        with pytest.raises(ValidationError) as exc_info:
            ProductCreationRequest(**payload)

        _assert_has_field_error(exc_info.value, missing_field, "Field required")

    @pytest.mark.parametrize(
        "field_name, field_value",
        [
            ("name", 123),
            ("price", "abc"),
            ("price", [10]),
            ("quantity", "abc"),
            ("quantity", 1.5),
            ("description", ["not", "a", "string"]),
        ],
    )
    def test_rejects_invalid_field_types(self, field_name: str, field_value: object) -> None:
        payload = {
            "name": "Mouse",
            "price": 59.9,
            "description": "Wireless mouse",
            "quantity": 10,
        }
        payload[field_name] = field_value

        with pytest.raises(ValidationError) as exc_info:
            ProductCreationRequest(**payload)

        _assert_has_field_error(exc_info.value, field_name)

    @pytest.mark.parametrize("field_name", ["name", "price", "quantity"])
    def test_rejects_null_on_non_nullable_required_fields(self, field_name: str) -> None:
        payload = {
            "name": "Mouse",
            "price": 59.9,
            "description": "Wireless mouse",
            "quantity": 10,
        }
        payload[field_name] = None

        with pytest.raises(ValidationError) as exc_info:
            ProductCreationRequest(**payload)

        _assert_has_field_error(exc_info.value, field_name)


class TestProductUpdateRequest:
    def test_valid_minimal_payload_only_required_name(self) -> None:
        payload = ProductUpdateRequest(name="Keyboard")

        assert payload.name == "Keyboard"
        assert payload.new_name is None
        assert payload.price is None
        assert payload.description is None
        assert payload.quantity is None

    def test_valid_payload_with_all_fields(self) -> None:
        payload = ProductUpdateRequest(
            name="Keyboard",
            new_name="Keyboard Pro",
            price=199.9,
            description="Updated model",
            quantity=3,
        )

        assert payload.name == "Keyboard"
        assert payload.new_name == "Keyboard Pro"
        assert payload.price == 199.9
        assert payload.description == "Updated model"
        assert payload.quantity == 3

    @pytest.mark.parametrize("invalid_price", [0, -1, -10.5])
    def test_rejects_non_positive_price(self, invalid_price: float) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProductUpdateRequest(name="Mouse", price=invalid_price)

        _assert_has_field_error(
            exc_info.value,
            "price",
            "price_must_be_greater_than_zero",
        )

    @pytest.mark.parametrize("invalid_quantity", [0, -1, -10])
    def test_rejects_non_positive_quantity(self, invalid_quantity: int) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProductUpdateRequest(name="Mouse", quantity=invalid_quantity)

        _assert_has_field_error(
            exc_info.value,
            "quantity",
            "quantity_must_be_greater_than_zero",
        )

    def test_rejects_missing_required_name(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProductUpdateRequest(price=99.9)

        _assert_has_field_error(exc_info.value, "name", "Field required")

    @pytest.mark.parametrize(
        "field_name, field_value",
        [
            ("name", None),
            ("name", 123),
            ("new_name", 123),
            ("price", "abc"),
            ("price", [10]),
            ("quantity", "abc"),
            ("quantity", 1.5),
            ("description", ["not", "a", "string"]),
        ],
    )
    def test_rejects_invalid_types(self, field_name: str, field_value: object) -> None:
        payload = {
            "name": "Mouse",
            "new_name": "Mouse V2",
            "price": 59.9,
            "description": "Wireless mouse",
            "quantity": 10,
        }
        payload[field_name] = field_value

        with pytest.raises((ValidationError, TypeError)) as exc_info:
            ProductUpdateRequest(**payload)

        if isinstance(exc_info.value, ValidationError):
            _assert_has_field_error(exc_info.value, field_name)
        else:
            assert field_name in str(exc_info.value) or "NoneType" in str(exc_info.value)

    def test_accepts_null_for_optional_text_fields(self) -> None:
        payload = ProductUpdateRequest(
            name="Mouse",
            new_name=None,
            description=None,
        )

        assert payload.new_name is None
        assert payload.description is None

    @pytest.mark.parametrize("field_name", ["price", "quantity"])
    def test_rejects_null_for_optional_numeric_fields(self, field_name: str) -> None:
        payload = {
            "name": "Mouse",
            "price": 59.9,
            "quantity": 10,
        }
        payload[field_name] = None

        with pytest.raises((ValidationError, TypeError)) as exc_info:
            ProductUpdateRequest(**payload)

        if isinstance(exc_info.value, ValidationError):
            _assert_has_field_error(exc_info.value, field_name)
        else:
            assert "NoneType" in str(exc_info.value)


class TestProductDeleteRequest:
    def test_valid_payload(self) -> None:
        payload = ProductDeleteRequest(name="Keyboard")

        assert payload.name == "Keyboard"

    def test_rejects_missing_required_name(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProductDeleteRequest()

        _assert_has_field_error(exc_info.value, "name", "Field required")

    @pytest.mark.parametrize("invalid_name", [None, 123, ["Mouse"], {"name": "Mouse"}])
    def test_rejects_invalid_name_type(self, invalid_name: object) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProductDeleteRequest(name=invalid_name)

        _assert_has_field_error(exc_info.value, "name")


