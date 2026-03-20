from src.exceptions.base_exception import AppBaseException


class CategoryAlreadyExistsException(AppBaseException):
    pass


class CategoryNotFoundException(AppBaseException):
    pass
