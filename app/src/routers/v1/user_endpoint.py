from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from loguru import logger
from src.core.config import settings
from src.core.security import create_access_token
from src.exceptions.user_exception import (
    InvalidCredentialsException,
    UserNotFoundException,
)
from src.routers.deps import get_current_user
from src.schemas.user_request import (
    UserLoginRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)
from src.schemas.user_response import (
    UserDeleteResponse,
    UserLoginResponse,
    UserLogoutResponse,
    UserRegisterResponse,
    UserUpdateResponse,
)
from src.services.users.user_service import (
    authenticate_user,
    register_user,
    update_user_data,
    user_deletion,
)
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
def registration(user: UserRegisterRequest) -> UserRegisterResponse:
    """Create a new user account and persist its credentials.

    Args:
        user: Validated payload with the user email, name, and password.

    Returns:
        UserRegisterResponse: Wrapper carrying the persisted user entity.
    """
    user_created = register_user(payload=user)
    logger.success("User registered successfully: {}", user_created.user.email)
    return user_created


@user_router.post(
    path="/auth/login",
    tags=["Auth"],
    status_code=status.HTTP_200_OK,
    summary="Login a user",
    description="Endpoint to login a user with email and password.",
)
def login(response: Response, user: UserLoginRequest) -> UserLoginResponse:
    """Authenticate the provided credentials and issue the session cookie.

    Args:
        response: Mutable HTTP response used to set the access token cookie.
        user: Login payload containing email and password.

    Returns:
        UserLoginResponse: Authenticated user data plus token metadata.

    Raises:
        InvalidCredentialsException: If the email/password combination is invalid.
    """
    user = authenticate_user(email=user.email, password=user.password)

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
    logger.success("User logged in: {}", user.email)
    return user


@user_router.post(
    path="/auth/logout",
    tags=["Auth"],
    status_code=status.HTTP_200_OK,
    summary="Logout a user",
    description="Endpoint to logout a user and invalidate the access token.",
)
def logout(
    response: Response,
    current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
) -> UserLogoutResponse:
    """Invalidate the current access token by deleting the auth cookie.

    Args:
        response: Response used to delete the authentication cookie.
        current_user: Principal resolved by `get_current_user` dependency.

    Returns:
        UserLogoutResponse: Confirmation message with the user email.
    """
    # Invalidate the access token by setting an expired cookie
    response.delete_cookie(key="access_token")
    logger.success("User logged out successfully.")
    return UserLogoutResponse.model_validate(
        {
            "message": "User logged out successfully.",
            "email": current_user.get("email", None),
        }
    )


@user_router.put(
    path="/profile/update",
    tags=["Profile"],
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    description="Endpoint to update the profile information of the"
    " currently authenticated user.",
)
def update_profile(
    response: Response,
    user_to_update: UserUpdateRequest,
    current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
) -> UserUpdateResponse:
    """Update the authenticated user's profile and refresh the cookie if needed.

    Args:
        response: Response used to refresh the cookie when the email changes.
        user_to_update: Payload with the mutable fields (email, password, etc.).
        current_user: Principal resolved by `get_current_user` dependency.

    Returns:
        UserUpdateResponse: Confirmation message with the updated email address.
    """
    user = update_user_data(user_to_update=user_to_update, current_user=current_user)
    if user.email != current_user["email"]:
        # If the email was updated, we need to issue a new token with the new email
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
    logger.success("User updated successfully.")
    return UserUpdateResponse.model_validate(
        {
            "message": "User updated successfully.",
            "email": user.email,
        }
    )


# @user_router.get(
#     path="/profile",
#     tags=["Profile"],
#     status_code=status.HTTP_200_OK,
#     summary="Get user profile",
#     description="Endpoint to retrieve the profile information"
#     " of the currently authenticated user.",
# )
# def get_profile(
#     current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
# ) -> dict:
#     """Return the cached identity information for the authenticated user.
#
#     Args:
#         current_user: Principal resolved by `get_current_user` dependency.
#
#     Returns:
#         dict: Canonicalized payload with email and supplementary metadata.
#     """
#     return {"email": current_user["username"], "details": current_user["payload"]}


@user_router.delete(
    "/profile/delete",
    tags=["Profile"],
    status_code=status.HTTP_200_OK,
    summary="Delete user account",
    description="Endpoint to delete the account of the currently authenticated user.",
)
def delete_account(
    response: Response,
    current_user: Annotated[dict[Any, Any], Depends(get_current_user)],
) -> UserDeleteResponse | None:
    """Delete the authenticated user account and clear the auth cookie.

    Args:
        response: Response used to delete the authentication cookie.
        current_user: Principal resolved by `get_current_user` dependency.

    Returns:
        UserDeleteResponse | None: Confirmation payload if removal succeeds, else None.

    Raises:
        UserNotFoundException: If the user does not exist or is already deleted.
    """
    user_email = current_user["email"]
    delete_status = user_deletion(user_email=user_email)
    if not delete_status:
        raise UserNotFoundException(
            message="User not found or already deleted.",
            context={"email": user_email},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    response.delete_cookie(key="access_token")
    logger.success("User deleted successfully.")
    return UserDeleteResponse.model_validate(
        {
            "message": "User deleted successfully.",
            "email": user_email,
        }
    )
