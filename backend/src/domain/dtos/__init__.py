"""Data Transfer Objects for the receipt search application."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from ..entities import ProcessingStatus, UserRole


@dataclass
class UploadReceiptRequest:
    """DTO for receipt upload request."""

    user_id: str
    file_names: list[str]
    file_sizes: list[int]


@dataclass
class UploadReceiptResponse:
    """DTO for receipt upload response."""

    receipt_ids: list[str]
    presigned_urls: list[dict[str, str]]  # {"upload_url": "...", "fields": {...}}
    quota_remaining: int


@dataclass
class ReceiptSearchRequest:
    """DTO for receipt search request."""

    query: str
    user_id: str
    date_added_from: Optional[datetime] = None
    date_added_to: Optional[datetime] = None
    date_extracted_from: Optional[datetime] = None
    date_extracted_to: Optional[datetime] = None
    limit: int = None  # Will use default from config if None
    offset: int = 0
    sort_by: Optional[str] = None

    def __post_init__(self):
        """Set default limit from configuration if not provided."""
        if self.limit is None:
            from ..config import DOMAIN_CONFIG

            self.limit = DOMAIN_CONFIG.search.DEFAULT_SEARCH_LIMIT


@dataclass
class ReceiptSearchResult:
    """DTO for a single receipt search result."""

    receipt_id: str
    file_name: str
    upload_date: datetime
    thumbnail_url: str
    extracted_text_snippet: str
    processing_status: ProcessingStatus
    relevance_score: float


@dataclass
class ReceiptSearchResponse:
    """DTO for receipt search response."""

    results: list[ReceiptSearchResult]
    total_count: int
    query_time_ms: int
    has_more: bool


@dataclass
class ReceiptDetailsResponse:
    """DTO for receipt details response."""

    receipt_id: str
    file_name: str
    file_size: int
    upload_date: datetime
    processing_status: ProcessingStatus
    extracted_text: str
    structured_data: dict[str, Any]
    user_edits: dict[str, Any]
    original_image_url: str
    thumbnail_url: str


@dataclass
class UserQuotaResponse:
    """DTO for user quota information."""

    user_id: str
    role: UserRole
    images_used: int
    images_quota: int
    quota_remaining: int
    reset_date: Optional[datetime] = None  # For monthly quotas


@dataclass
class ProcessReceiptRequest:
    """DTO for receipt processing request."""

    receipt_id: str
    s3_bucket: str
    s3_key: str


@dataclass
class ProcessReceiptResponse:
    """DTO for receipt processing response."""

    receipt_id: str
    success: bool
    extracted_text: str
    structured_data: dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class DeleteReceiptsRequest:
    """DTO for bulk delete receipts request."""

    user_id: str
    receipt_ids: list[str]


@dataclass
class DeleteReceiptsResponse:
    """DTO for bulk delete receipts response."""

    deleted_count: int
    failed_ids: list[str]
    quota_restored: int
