from .base_exception import AppBaseException


class EmailAlreadyExistsException(AppBaseException):
    """Exception raised when trying to create a user with
    an email that already exists."""

    pass


class PasswordAndConfirmPasswordNotMatchException(AppBaseException):
    """Exception raised when the provided password and confirm password do not match."""

    pass


class UserNotFoundException(AppBaseException):
    """Exception raised when trying to create a user that already exists."""

    pass


class InvalidCredentialsException(AppBaseException):
    """Exception raised when the provided credentials are invalid."""

    pass


class InvalidTokenException(AppBaseException):
    """Exception raised when the provided token is invalid."""

    pass


class NewPasswordAndOldPasswordNotMatchException(AppBaseException):
    """Exception raised when the provided new password
    and confirm password do not match."""

    pass
