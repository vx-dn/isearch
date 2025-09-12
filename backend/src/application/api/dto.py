"""API Data Transfer Objects for requests and responses."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum


class SubscriptionTier(str, Enum):
    """User subscription tiers."""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ReceiptType(str, Enum):
    """Receipt types."""

    GROCERY = "grocery"
    RESTAURANT = "restaurant"
    GAS = "gas"
    RETAIL = "retail"
    MEDICAL = "medical"
    BUSINESS = "business"
    OTHER = "other"


# === User API DTOs ===


class UserCreateRequest(BaseModel):
    """Request to create a new user."""

    email: EmailStr
    username: Optional[str] = None
    display_name: Optional[str] = None
    password: str = Field(..., min_length=8)


class UserUpdateRequest(BaseModel):
    """Request to update user information."""

    username: Optional[str] = None
    display_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """User information response."""

    user_id: str
    email: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    subscription_tier: SubscriptionTier
    receipt_count: int
    storage_used_bytes: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# === Authentication API DTOs ===


class LoginRequest(BaseModel):
    """Login request."""

    email: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str = "Bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""

    email: EmailStr
    confirmation_code: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str
    new_password: str = Field(..., min_length=8)


# === Receipt API DTOs ===


class ReceiptItemRequest(BaseModel):
    """Receipt item in request."""

    name: str
    category: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None


class ReceiptItemResponse(BaseModel):
    """Receipt item in response."""

    name: str
    category: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ReceiptCreateRequest(BaseModel):
    """Request to create a receipt manually."""

    merchant_name: Optional[str] = None
    merchant_address: Optional[str] = None
    purchase_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    receipt_type: Optional[ReceiptType] = None
    items: Optional[List[ReceiptItemRequest]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ReceiptUpdateRequest(BaseModel):
    """Request to update a receipt."""

    merchant_name: Optional[str] = None
    merchant_address: Optional[str] = None
    purchase_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    receipt_type: Optional[ReceiptType] = None
    items: Optional[List[ReceiptItemRequest]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ReceiptResponse(BaseModel):
    """Receipt information response."""

    receipt_id: str
    user_id: str
    image_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_address: Optional[str] = None
    purchase_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    receipt_type: Optional[str] = None
    raw_text: Optional[str] = None
    confidence_score: Optional[float] = None
    extraction_metadata: Optional[Dict[str, Any]] = None
    items: Optional[List[ReceiptItemResponse]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    version: int

    class Config:
        from_attributes = True


class ReceiptListResponse(BaseModel):
    """Paginated receipt list response."""

    receipts: List[ReceiptResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


# === Image Upload API DTOs ===


class ImageUploadResponse(BaseModel):
    """Image upload response."""

    image_id: str
    upload_url: str
    fields: Dict[str, str]
    expires_in: int


class ImageProcessingStatusResponse(BaseModel):
    """Image processing status response."""

    image_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: Optional[int] = None  # 0-100
    error_message: Optional[str] = None
    receipt: Optional[ReceiptResponse] = None


# === Search API DTOs ===


class SearchRequest(BaseModel):
    """Search request."""

    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class SearchResponse(BaseModel):
    """Search results response."""

    hits: List[Dict[str, Any]]
    total_hits: int
    processing_time_ms: int
    limit: int
    offset: int
    has_more: bool


class DateRangeSearchRequest(BaseModel):
    """Date range search request."""

    start_date: datetime
    end_date: datetime
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class AmountRangeSearchRequest(BaseModel):
    """Amount range search request."""

    min_amount: Decimal
    max_amount: Decimal
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TagSearchRequest(BaseModel):
    """Tag search request."""

    tags: List[str]
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# === Analytics API DTOs ===


class AnalyticsResponse(BaseModel):
    """Analytics response."""

    total_receipts: int
    total_amount: Decimal
    average_amount: Decimal
    receipts_by_month: Dict[str, int]
    spending_by_category: Dict[str, Decimal]
    top_merchants: List[Dict[str, Any]]


class MerchantStatsResponse(BaseModel):
    """Merchant statistics response."""

    merchant_name: str
    receipt_count: int
    total_spent: Decimal
    average_amount: Decimal
    first_visit: datetime
    last_visit: datetime


# === Error Response DTOs ===


class ErrorDetail(BaseModel):
    """Error detail."""

    field: Optional[str] = None
    message: str
    error_code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None


# === Health Check DTOs ===


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str  # "healthy", "unhealthy"
    timestamp: datetime
    services: Dict[str, str]
    version: Optional[str] = None


# === Common DTOs ===


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @validator("page_size")
    def validate_page_size(cls, v):
        if v > 100:
            raise ValueError("page_size cannot be greater than 100")
        return v

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
