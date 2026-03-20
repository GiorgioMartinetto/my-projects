from pydantic import BaseModel, field_validator


class CategoryRequest(BaseModel):
    name: str

    @field_validator("name")
    def validate_name(cls, v):
        if not v.isalpha():
            raise ValueError("Name must be alphabetical")
        if not 2 <= len(v) <= 20:
            raise ValueError("Name length must be between 2 and 20 characters")

        return v
