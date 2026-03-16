from typing import Any

from fastapi import Request
from jose import JWTError, jwt
from src.core.config import settings
from src.exceptions.user_exception import InvalidTokenException
from starlette import status


def get_current_user(request: Request) -> dict[str, dict[str, Any]]:
    """
    Legge il JWT dal cookie, lo valida e restituisce i dati dell'utente.
    Usala come Depends() in qualsiasi rotta protetta.
    """
    token = request.cookies.get("access_token")

    if not token:
        raise InvalidTokenException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="You must be logged in to access this resource",
        )

    try:
        payload = jwt.decode(
            token, settings.token.secret_key, algorithms=settings.token.algorithm
        )
        email: str = payload.get("sub")
        if not email:
            raise InvalidTokenException(
                status_code=status.HTTP_401_UNAUTHORIZED, message="Invalid token"
            )
    except JWTError:
        raise InvalidTokenException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="The token is invalid or has expired",
        ) from None

    return {"email": email, "payload": payload}
