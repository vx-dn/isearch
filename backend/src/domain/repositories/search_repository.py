"""Search repository interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from ..entities import Receipt


class SearchRepository(ABC):
    """Abstract repository interface for search operations."""

    @abstractmethod
    async def index_document(self, receipt: Receipt) -> bool:
        """Index a receipt document for searching."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for receipts.

        Args:
            query: Search query string
            user_id: User ID to filter results
            filters: Additional filters (date ranges, etc.)
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by

        Returns:
            Dictionary containing search results and metadata
        """
        pass

    @abstractmethod
    async def delete_document(self, receipt_id: str) -> bool:
        """Delete a receipt document from the search index."""
        pass

    @abstractmethod
    async def bulk_delete(self, receipt_ids: List[str]) -> int:
        """Delete multiple receipt documents. Returns count of deleted documents."""
        pass

    @abstractmethod
    async def update_document(self, receipt: Receipt) -> bool:
        """Update a receipt document in the search index."""
        pass

    @abstractmethod
    async def get_search_suggestions(self, query: str, user_id: str) -> List[str]:
        """Get search suggestions based on partial query."""
        pass

    @abstractmethod
    async def rebuild_user_index(self, user_id: str, receipts: List[Receipt]) -> bool:
        """Rebuild search index for a specific user."""
        pass
