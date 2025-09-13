"""User entity implementation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .enums import UserRole


@dataclass
class User:
    """User entity representing a user in the system."""

    user_id: str
    email: str
    role: UserRole
    image_count: int
    image_quota: int
    last_active_date: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert user to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role.value,
            "image_count": self.image_count,
            "image_quota": self.image_quota,
            "last_active_date": (
                self.last_active_date.isoformat() if self.last_active_date else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Create user from dictionary."""
        role = UserRole(data["role"])
        return cls(
            user_id=data["user_id"],
            email=data["email"],
            role=role,
            image_count=data.get("image_count", 0),
            image_quota=data.get("image_quota", role.image_quota),
            last_active_date=(
                datetime.fromisoformat(data["last_active_date"])
                if data.get("last_active_date")
                else None
            ),
        )

    def can_upload(self, num_images: int = 1) -> bool:
        """Check if user can upload the specified number of images."""
        return self.image_count + num_images <= self.image_quota

    def increment_image_count(self, count: int = 1) -> None:
        """Increment the user's image count."""
        self.image_count += count

    def decrement_image_count(self, count: int = 1) -> None:
        """Decrement the user's image count."""
        self.image_count = max(0, self.image_count - count)

    def update_last_active(self, timestamp: Optional[datetime] = None) -> None:
        """Update the user's last active timestamp."""
        self.last_active_date = timestamp or datetime.utcnow()

    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == UserRole.ADMIN

    def is_inactive_free_user(self, days_threshold: int = None) -> bool:
        """Check if this is a free user who has been inactive for the specified days."""
        if self.role != UserRole.FREE or self.last_active_date is None:
            return False

        if days_threshold is None:
            from ..config import DOMAIN_CONFIG

            days_threshold = (
                DOMAIN_CONFIG.data_retention.INACTIVE_FREE_USER_THRESHOLD_DAYS
            )

        days_since_active = (datetime.utcnow() - self.last_active_date).days
        return days_since_active > days_threshold

    def get_available_quota(self) -> int:
        """Get the number of images the user can still upload."""
        return max(0, self.image_quota - self.image_count)
