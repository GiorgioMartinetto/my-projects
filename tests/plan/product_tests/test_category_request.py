import pytest
from pydantic import ValidationError

from src.schemas.category_request import CategoryRequest


def _assert_has_field_error(
	exc: ValidationError, field_name: str, expected_fragment: str | None = None
) -> None:
	errors = exc.errors()
	matching_errors = [
		error
		for error in errors
		if error.get("loc") and error["loc"][-1] == field_name
	]
	assert matching_errors, f"No validation error found for field: {field_name}"

	if expected_fragment is not None:
		assert any(expected_fragment in error.get("msg", "") for error in matching_errors)


class TestCategoryRequest:
	@pytest.mark.parametrize("valid_name", ["TV", "Gaming", "A" * 20])
	def test_accepts_valid_name(self, valid_name: str) -> None:
		payload = CategoryRequest(name=valid_name)

		assert payload.name == valid_name

	@pytest.mark.parametrize(
		"invalid_name",
		["Gaming1", "Gaming Room", "gaming-room", "gaming_room", ""],
	)
	def test_rejects_non_alphabetical_name(self, invalid_name: str) -> None:
		with pytest.raises(ValidationError) as exc_info:
			CategoryRequest(name=invalid_name)

		_assert_has_field_error(exc_info.value, "name", "Name must be alphabetical")

	@pytest.mark.parametrize("invalid_name", ["A", "A" * 21])
	def test_rejects_name_outside_length_bounds(self, invalid_name: str) -> None:
		with pytest.raises(ValidationError) as exc_info:
			CategoryRequest(name=invalid_name)

		_assert_has_field_error(
			exc_info.value,
			"name",
			"Name length must be between 2 and 20 characters",
		)

	def test_rejects_missing_required_name(self) -> None:
		with pytest.raises(ValidationError) as exc_info:
			CategoryRequest()

		_assert_has_field_error(exc_info.value, "name", "Field required")

	@pytest.mark.parametrize("invalid_name", [None, 123, ["Gaming"], {"name": "Gaming"}])
	def test_rejects_invalid_name_types(self, invalid_name: object) -> None:
		with pytest.raises(ValidationError) as exc_info:
			CategoryRequest(name=invalid_name)

		_assert_has_field_error(exc_info.value, "name")

