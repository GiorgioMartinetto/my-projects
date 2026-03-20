from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CategoryResponse(BaseModel):
    id: UUID
    category_name: str
    created_by: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryGenericResponse(BaseModel):
    message: str
    category_name: str


class CategoryDeleteResponse(CategoryGenericResponse):
    pass
