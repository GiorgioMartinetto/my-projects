from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import jwt
from src.core.config import settings


# Hash a password using bcrypt
def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode("utf-8")
    if isinstance(hashed_password, str):
        hashed_password_bytes = hashed_password.encode("utf-8")
    else:
        hashed_password_bytes = hashed_password

    return bcrypt.checkpw(
        password=password_byte_enc, hashed_password=hashed_password_bytes
    )


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    token: str = jwt.encode(
        to_encode, settings.token.secret_key, algorithm=settings.token.algorithm
    )
    return token
