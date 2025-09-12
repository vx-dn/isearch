"""Receipt repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from ..entities import Receipt


class ReceiptRepository(ABC):
    """Abstract repository interface for receipt operations."""

    @abstractmethod
    async def save(self, receipt: Receipt) -> Receipt:
        """Save a receipt to the repository."""
        pass

    @abstractmethod
    async def get_by_id(self, receipt_id: str) -> Optional[Receipt]:
        """Get a receipt by its ID."""
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: str,
        limit: Optional[int] = None,
        last_evaluated_key: Optional[str] = None,
    ) -> List[Receipt]:
        """Get all receipts for a specific user with pagination."""
        pass

    @abstractmethod
    async def update(self, receipt: Receipt) -> Receipt:
        """Update an existing receipt."""
        pass

    @abstractmethod
    async def delete(self, receipt_id: str) -> bool:
        """Delete a receipt by its ID."""
        pass

    @abstractmethod
    async def bulk_delete(self, receipt_ids: List[str]) -> int:
        """Delete multiple receipts by their IDs. Returns count of deleted receipts."""
        pass

    @abstractmethod
    async def get_inactive_receipts(
        self, days_threshold: int = 30, limit: Optional[int] = None
    ) -> List[Receipt]:
        """Get receipts from inactive free users older than threshold days."""
        pass

    @abstractmethod
    async def get_by_processing_status(
        self, status: str, limit: Optional[int] = None
    ) -> List[Receipt]:
        """Get receipts by processing status."""
        pass

    @abstractmethod
    async def count_by_user_id(self, user_id: str) -> int:
        """Count total receipts for a user."""
        pass
