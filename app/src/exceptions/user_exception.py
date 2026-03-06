from .base_exception import AppBaseException

class EmailAlreadyExistsException(AppBaseException):
    """Exception raised when trying to create a user with an email that already exists."""
    pass

class UserNotFoundException(AppBaseException):
    """Exception raised when trying to create a user that already exists."""
    pass

class InvalidCredentialsException(AppBaseException):
    """Exception raised when the provided credentials are invalid."""
    pass
