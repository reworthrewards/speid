class BackendError(Exception):
    ...


class OrderNotFoundException(ReferenceError):
    ...


class MalformedOrderException(ValueError):
    ...


class ResendSuccessOrderException(ValueError):
    ...

