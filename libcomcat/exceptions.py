class ComCatError(Exception):
    """Base class for all libcomcat exceptions/errors.
    """
    pass


class ConnectionError(ComCatError):
    """Could not connect to ComCat"""
    pass


class ParsingError(ComCatError):
    """Could not parse QuakeML files for some reason"""
    pass


class ProductNotFoundError(ComCatError):
    """Missing products in JSON"""
    pass


class ProductNotSpecifiedError(ComCatError):
    """Missing products in JSON"""
    pass


class ContentNotFoundError(ComCatError):
    """Missing products in JSON"""
    pass


class ArgumentConflictError(ComCatError):
    """Arguments passed to a function that cannot be combined"""
    pass


class UndefinedVersionError(ComCatError):
    """Arguments passed to a function that cannot be combined"""
    pass


class TimeOutError(ComCatError):
    """Connection timed out."""
    pass
