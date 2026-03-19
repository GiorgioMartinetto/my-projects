from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    price: float
    quantity: int
    created_by: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}
    """Per la conversione automatica da ORM a Pydantic.
    Consente di creare un'istanza del modello Pydantic direttamente da un'istanza 
    del modello ORM, mappando automaticamente i campi corrispondenti."""


class ListProductsResponse(BaseModel):
    products: list[ProductResponse]


class ProductGenericResponse(BaseModel):
    message: str
    name: str


class ProductDeletionResponse(ProductGenericResponse):
    pass
