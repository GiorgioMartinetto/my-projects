from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}
    """Per la conversione automatica da ORM a Pydantic.
    Consente di creare un'istanza del modello Pydantic direttamente da un'istanza 
    del modello ORM, mappando automaticamente i campi corrispondenti."""


class UserRegisterResponse(BaseModel):
    message: str
    user: UserResponse


class GenericUserResponse(BaseModel):
    message: str
    email: EmailStr


class UserLoginResponse(GenericUserResponse):
    pass


class UserLogoutResponse(GenericUserResponse):
    pass


class UserUpdateResponse(GenericUserResponse):
    pass


class UserDeleteResponse(GenericUserResponse):
    pass
