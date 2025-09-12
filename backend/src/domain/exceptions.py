"""Domain exceptions."""


class DomainException(Exception):
    """Base exception for domain errors."""

    pass


class UserNotFoundError(DomainException):
    """Raised when a user is not found."""

    pass


class ReceiptNotFoundError(DomainException):
    """Raised when a receipt is not found."""

    pass


class DatabaseError(DomainException):
    """Raised when a database operation fails."""

    pass


class ValidationError(DomainException):
    """Raised when validation fails."""

    pass


class SearchError(DomainException):
    """Raised when search operations fail."""

    pass
