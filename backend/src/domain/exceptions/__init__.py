"""Custom exceptions for the receipt search application."""


class DomainException(Exception):
    """Base exception for domain layer errors."""

    pass


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated."""

    pass


class ResourceNotFoundError(DomainException):
    """Raised when a requested resource is not found."""

    pass


class UnauthorizedAccessError(DomainException):
    """Raised when a user tries to access a resource they don't own."""

    pass


class QuotaExceededError(BusinessRuleViolationError):
    """Raised when a user exceeds their upload quota."""

    pass


class ProcessingError(DomainException):
    """Raised when receipt processing fails."""

    pass


class ValidationError(DomainException):
    """Raised when input validation fails."""

    pass


class RepositoryError(DomainException):
    """Raised when repository operations fail."""

    pass


class SearchError(DomainException):
    """Raised when search operations fail."""

    pass


class UserNotFoundError(ResourceNotFoundError):
    """Raised when a user is not found."""

    pass


class ReceiptNotFoundError(ResourceNotFoundError):
    """Raised when a receipt is not found."""

    pass


class DatabaseError(RepositoryError):
    """Raised when database operations fail."""

    pass


# Alias for backward compatibility
DomainError = DomainException
