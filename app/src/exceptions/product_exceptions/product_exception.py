from src.exceptions.base_exception import AppBaseException


class ProductAlreadyExistsException(AppBaseException):
    pass


class ProductNotFoundException(AppBaseException):
    pass


class ProductCanBeDeleteOnlyByTheCreatorException(AppBaseException):
    pass


class ProductCanOnlyBeModifiedByTheCreatorException(AppBaseException):
    pass
