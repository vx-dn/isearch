"""Domain layer for receipt search application.

This module contains the core business logic including entities, repository interfaces,
use cases, and data transfer objects. It follows Clean Architecture principles and has
no dependencies on external frameworks or infrastructure.
"""

from .entities import Receipt, User, ProcessingStatus, UserRole
from .repositories import ReceiptRepository, UserRepository, SearchRepository
from .use_cases import (
    UploadReceiptUseCase,
    SearchReceiptsUseCase,
    ProcessReceiptUseCase,
    DeleteReceiptsUseCase,
    CleanupInactiveReceiptsUseCase,
    GetReceiptDetailsUseCase,
    GetUserQuotaUseCase,
)
from .dtos import (
    UploadReceiptRequest,
    UploadReceiptResponse,
    ReceiptSearchRequest,
    ReceiptSearchResponse,
    ReceiptSearchResult,
    ReceiptDetailsResponse,
    UserQuotaResponse,
    ProcessReceiptRequest,
    ProcessReceiptResponse,
    DeleteReceiptsRequest,
    DeleteReceiptsResponse,
)
from .exceptions import (
    DomainException,
    BusinessRuleViolationError,
    ResourceNotFoundError,
    UnauthorizedAccessError,
    QuotaExceededError,
    ProcessingError,
    ValidationError,
    RepositoryError,
    SearchError,
)
from .config import DOMAIN_CONFIG

__all__ = [
    # Configuration
    "DOMAIN_CONFIG",
    # Entities
    "Receipt",
    "User",
    "ProcessingStatus",
    "UserRole",
    # Repository Interfaces
    "ReceiptRepository",
    "UserRepository",
    "SearchRepository",
    # Use Cases
    "UploadReceiptUseCase",
    "SearchReceiptsUseCase",
    "ProcessReceiptUseCase",
    "DeleteReceiptsUseCase",
    "CleanupInactiveReceiptsUseCase",
    "GetReceiptDetailsUseCase",
    "GetUserQuotaUseCase",
    # DTOs
    "UploadReceiptRequest",
    "UploadReceiptResponse",
    "ReceiptSearchRequest",
    "ReceiptSearchResponse",
    "ReceiptSearchResult",
    "ReceiptDetailsResponse",
    "UserQuotaResponse",
    "ProcessReceiptRequest",
    "ProcessReceiptResponse",
    "DeleteReceiptsRequest",
    "DeleteReceiptsResponse",
    # Exceptions
    "DomainException",
    "BusinessRuleViolationError",
    "ResourceNotFoundError",
    "UnauthorizedAccessError",
    "QuotaExceededError",
    "ProcessingError",
    "ValidationError",
    "RepositoryError",
    "SearchError",
]
