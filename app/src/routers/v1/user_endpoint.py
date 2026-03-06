from fastapi import APIRouter
from starlette import status

from src.schemas.user_request import UserRegisterRequest
from src.schemas.user_response import UserRegisterResponse
from src.services.users.user_service import register_user

user_router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@user_router.post(
    path="/registration",
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
    user_created = await register_user(user = user)

    return UserRegisterResponse.model_validate(user_created)

