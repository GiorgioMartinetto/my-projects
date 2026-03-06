class AppBaseException(Exception):
    """Base exception for the application."""

    def __init__(
        self, message: str, context: dict | None = None, status_code: int = 400
    ):
        self.message = message
        self.context = context
        self.status_code = status_code
        super().__init__(message)
