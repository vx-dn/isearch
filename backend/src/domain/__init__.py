"""Domain layer for receipt search application.

This module contains the core business logic including entities, repository interfaces,
use cases, and data transfer objects. It follows Clean Architecture principles and has
no dependencies on external frameworks or infrastructure.
"""

from .config import DOMAIN_CONFIG
from .dtos import (
    DeleteReceiptsRequest,
    DeleteReceiptsResponse,
    ProcessReceiptRequest,
    ProcessReceiptResponse,
    ReceiptDetailsResponse,
    ReceiptSearchRequest,
    ReceiptSearchResponse,
    ReceiptSearchResult,
    UploadReceiptRequest,
    UploadReceiptResponse,
    UserQuotaResponse,
)
from .entities import ProcessingStatus, Receipt, User, UserRole
from .exceptions import (
    BusinessRuleViolationError,
    DomainException,
    ProcessingError,
    QuotaExceededError,
    RepositoryError,
    ResourceNotFoundError,
    SearchError,
    UnauthorizedAccessError,
    ValidationError,
)
from .repositories import ReceiptRepository, SearchRepository, UserRepository
from .use_cases import (
    CleanupInactiveReceiptsUseCase,
    DeleteReceiptsUseCase,
    GetReceiptDetailsUseCase,
    GetUserQuotaUseCase,
    ProcessReceiptUseCase,
    SearchReceiptsUseCase,
    UploadReceiptUseCase,
)

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
