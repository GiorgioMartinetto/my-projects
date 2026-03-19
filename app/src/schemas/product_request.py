from pydantic import BaseModel, field_validator


class ProductCreationRequest(BaseModel):
    name: str
    price: float
    description: str | None = None
    quantity: int

    @field_validator("price")
    def price_must_be_greater_than_zero(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price_must_be_greater_than_zero")
        return v

    @field_validator("quantity")
    def quantity_must_be_greater_than_zero(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity_must_be_greater_than_zero")
        return v


class ProductUpdateRequest(BaseModel):
    name: str
    new_name: str | None = None
    price: float | None = None
    description: str | None = None
    quantity: int | None = None

    @field_validator("price")
    def price_must_be_greater_than_zero(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price_must_be_greater_than_zero")
        return v

    @field_validator("quantity")
    def quantity_must_be_greater_than_zero(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity_must_be_greater_than_zero")
        return v


class ProductDeleteRequest(BaseModel):
    name: str
