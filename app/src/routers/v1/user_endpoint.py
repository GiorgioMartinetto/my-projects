from datetime import timedelta

from fastapi import APIRouter, Response
from src.core.config import settings
from src.core.security import create_access_token
from src.exceptions.user_exception import InvalidCredentialsException
from src.schemas.user_request import UserLoginRequest, UserRegisterRequest
from src.schemas.user_response import UserLoginResponse, UserRegisterResponse, \
    UserLogoutResponse
from src.services.users.user_service import authenticate_user, register_user
from starlette import status

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@user_router.post(
    path="/auth/registration",
    tags=["Auth"],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Endpoint to register a new user with email, name, and password.",
)
async def registration(user: UserRegisterRequest) -> UserRegisterResponse:
    """
    Register a new user.

    Args:
        user: UserCreationRequest - The user registration details.

    Returns:
        UserCreationResponse - The created user's details.
    """
    user_created = await register_user(payload=user)

    return user_created


@user_router.post(
    path="/auth/login",
    tags=["Auth"],
    status_code=status.HTTP_200_OK,
    summary="Login a user",
    description="Endpoint to login a user with email and password.",
)
async def login(response: Response, user: UserLoginRequest) -> UserLoginResponse:
    user = await authenticate_user(email=user.email, password=user.password)

    if not user:
        raise InvalidCredentialsException(
            message="Invalid email or password.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.token.expiration),
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=settings.token.http_only,
        secure=settings.token.secure,
        samesite=settings.token.same_site,
        max_age=settings.token.expiration * 60,
    )
    return user


@user_router.post(
    path="/auth/logout",
    tags=["Auth"],
    status_code=status.HTTP_200_OK,
    summary="Logout a user",
    description="Endpoint to logout a user and invalidate the access token.",
)
async def logout(response: Response) -> UserLogoutResponse:
    """
    Logout a user.

    Args:
        response: Response - The response object to set cookies for logout.

    Returns:
        dict - A message indicating successful logout.
    """
    # Invalidate the access token by setting an expired cookie
    response.delete_cookie(key="access_token")
    return UserLogoutResponse.model_validate(
        {"message": "User logged out successfully."}
    )

