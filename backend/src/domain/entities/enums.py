"""Enums for the receipt search application."""

from enum import Enum


class ProcessingStatus(Enum):
    """Enum for receipt processing status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class UserRole(Enum):
    """Enum for user roles."""

    FREE = "free"
    PAID = "paid"
    ADMIN = "admin"

    @property
    def image_quota(self) -> int:
        """Get the default image quota for this role."""
        from ..config import DOMAIN_CONFIG

        if self == UserRole.FREE:
            return DOMAIN_CONFIG.user_quotas.FREE_USER_QUOTA
        elif self in (UserRole.PAID, UserRole.ADMIN):
            return DOMAIN_CONFIG.user_quotas.PAID_USER_QUOTA
        return 0
