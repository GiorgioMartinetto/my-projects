from pydantic import BaseModel, EmailStr, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    confirm_password: str

    @field_validator("password")
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit.")
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for char in value):
            raise ValueError("Password must contain at least one special character.")
        return value

    @field_validator("name")
    def name_validator(cls, value: str) -> str:
        v = value.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
