"""Domain configuration constants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserQuotas:
    """User quota configuration."""

    FREE_USER_QUOTA: int = 50
    PAID_USER_QUOTA: int = 1000
    ADMIN_USER_QUOTA: int = 1000


@dataclass(frozen=True)
class FileConstraints:
    """File size and processing constraints."""

    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20MB
    MAX_IMAGE_SIZE_FOR_PROCESSING: int = 10 * 1024 * 1024  # 10MB
    THUMBNAIL_WIDTH: int = 400
    THUMBNAIL_HEIGHT: int = 240


@dataclass(frozen=True)
class DataRetention:
    """Data retention configuration."""

    INACTIVE_FREE_USER_THRESHOLD_DAYS: int = 30
    TEMP_FILE_RETENTION_HOURS: int = 24


@dataclass(frozen=True)
class SearchConfiguration:
    """Search-related configuration."""

    DEFAULT_SEARCH_LIMIT: int = 20
    MAX_SEARCH_LIMIT: int = 100
    MAX_EXTRACTED_TEXT_SNIPPET_LENGTH: int = 200


@dataclass(frozen=True)
class ProcessingConfiguration:
    """Processing pipeline configuration."""

    S3_DELETE_BATCH_SIZE: int = 1000  # S3 delete batch limit
    DEFAULT_PROCESSING_TIMEOUT_MINUTES: int = 2


@dataclass(frozen=True)
class InfrastructureConfiguration:
    """Infrastructure configuration constants."""

    # DynamoDB Tables
    RECEIPT_TABLE_NAME: str = "receipt-search-receipts"
    USER_TABLE_NAME: str = "receipt-search-users"

    # S3 Configuration
    S3_BUCKET_NAME: str = "receipt-search-images"

    # Search Configuration
    SEARCH_INDEX_NAME: str = "receipts"

    # File Upload Configuration
    UPLOAD_URL_EXPIRES_IN: int = 3600  # 1 hour
    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20MB


@dataclass(frozen=True)
class DomainConfig:
    """Central domain configuration."""

    user_quotas: UserQuotas = UserQuotas()
    file_constraints: FileConstraints = FileConstraints()
    data_retention: DataRetention = DataRetention()
    search: SearchConfiguration = SearchConfiguration()
    processing: ProcessingConfiguration = ProcessingConfiguration()
    infrastructure: InfrastructureConfiguration = InfrastructureConfiguration()

    # Convenience properties for backward compatibility
    @property
    def RECEIPT_TABLE_NAME(self) -> str:
        return self.infrastructure.RECEIPT_TABLE_NAME

    @property
    def USER_TABLE_NAME(self) -> str:
        return self.infrastructure.USER_TABLE_NAME

    @property
    def S3_BUCKET_NAME(self) -> str:
        return self.infrastructure.S3_BUCKET_NAME

    @property
    def SEARCH_INDEX_NAME(self) -> str:
        return self.infrastructure.SEARCH_INDEX_NAME

    @property
    def UPLOAD_URL_EXPIRES_IN(self) -> int:
        return self.infrastructure.UPLOAD_URL_EXPIRES_IN

    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.infrastructure.MAX_FILE_SIZE_BYTES


# Global configuration instance
DOMAIN_CONFIG = DomainConfig()
