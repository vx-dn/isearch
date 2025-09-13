"""User repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities import User


class UserRepository(ABC):
    """Abstract repository interface for user operations."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save a user to the repository."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email address."""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user."""
        pass

    @abstractmethod
    async def update_last_active(self, user_id: str) -> bool:
        """Update the user's last active timestamp to now."""
        pass

    @abstractmethod
    async def get_inactive_free_users(self, days_threshold: int = 30) -> list[User]:
        """Get free users who have been inactive for more than the threshold days."""
        pass

    @abstractmethod
    async def increment_image_count(self, user_id: str, count: int = 1) -> bool:
        """Increment a user's image count."""
        pass

    @abstractmethod
    async def decrement_image_count(self, user_id: str, count: int = 1) -> bool:
        """Decrement a user's image count."""
        pass
