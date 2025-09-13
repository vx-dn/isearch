"""Meilisearch implementation of search repository."""

import logging
from typing import Any, Optional

from src.domain.config import DOMAIN_CONFIG
from src.domain.entities.receipt import Receipt
from src.domain.exceptions import SearchError
from src.domain.repositories.search_repository import SearchRepository
from src.infrastructure.search.meilisearch_service import MeilisearchService

logger = logging.getLogger(__name__)


class MeilisearchSearchRepository(SearchRepository):
    """Meilisearch implementation of search repository."""

    def __init__(self, meilisearch_service: MeilisearchService):
        """Initialize repository with Meilisearch service."""
        self.meilisearch_service = meilisearch_service
        self.index_name = DOMAIN_CONFIG.SEARCH_INDEX_NAME

    def _to_search_document(self, receipt: Receipt) -> dict[str, Any]:
        """Convert Receipt entity to search document."""
        # Create searchable text content
        searchable_text = []

        if receipt.merchant_name:
            searchable_text.append(receipt.merchant_name)

        if receipt.merchant_address:
            searchable_text.append(receipt.merchant_address)

        if receipt.raw_text:
            searchable_text.append(receipt.raw_text)

        if receipt.notes:
            searchable_text.append(receipt.notes)

        # Add item names and categories
        if receipt.items:
            for item in receipt.items:
                if item.name:
                    searchable_text.append(item.name)
                if item.category:
                    searchable_text.append(item.category)

        # Add tags
        if receipt.tags:
            searchable_text.extend(receipt.tags)

        return {
            "id": receipt.receipt_id,
            "receipt_id": receipt.receipt_id,
            "user_id": receipt.user_id,
            "image_id": receipt.image_id,
            "merchant_name": receipt.merchant_name or "",
            "merchant_address": receipt.merchant_address or "",
            "purchase_date": (
                receipt.purchase_date.isoformat() if receipt.purchase_date else None
            ),
            "purchase_date_timestamp": (
                int(receipt.purchase_date.timestamp())
                if receipt.purchase_date
                else None
            ),
            "total_amount": (
                float(receipt.total_amount) if receipt.total_amount else None
            ),
            "currency": receipt.currency or "",
            "receipt_type": receipt.receipt_type or "",
            "confidence_score": receipt.confidence_score,
            "items": (
                [
                    {
                        "name": item.name or "",
                        "category": item.category or "",
                        "quantity": item.quantity,
                        "unit_price": (
                            float(item.unit_price) if item.unit_price else None
                        ),
                        "total_price": (
                            float(item.total_price) if item.total_price else None
                        ),
                    }
                    for item in receipt.items
                ]
                if receipt.items
                else []
            ),
            "tags": receipt.tags or [],
            "notes": receipt.notes or "",
            "created_at": receipt.created_at.isoformat(),
            "created_at_timestamp": int(receipt.created_at.timestamp()),
            "updated_at": receipt.updated_at.isoformat(),
            "updated_at_timestamp": int(receipt.updated_at.timestamp()),
            "is_deleted": receipt.is_deleted,
            "searchable_text": " ".join(searchable_text),
        }

    async def index_receipt(self, receipt: Receipt) -> bool:
        """Index a receipt for search."""
        try:
            if receipt.is_deleted:
                # Remove from index if deleted
                return await self.remove_receipt(receipt.receipt_id)

            document = self._to_search_document(receipt)
            success = await self.meilisearch_service.index_document(document)

            if success:
                logger.debug(f"Indexed receipt {receipt.receipt_id} for search")
            return success
        except Exception as e:
            logger.error(f"Failed to index receipt {receipt.receipt_id}: {e}")
            raise SearchError(f"Failed to index receipt: {e}")

    async def index_receipts(self, receipts: list[Receipt]) -> int:
        """Index multiple receipts for search."""
        try:
            # Filter out deleted receipts and convert to documents
            documents = []
            for receipt in receipts:
                if not receipt.is_deleted:
                    documents.append(self._to_search_document(receipt))

            if not documents:
                return 0

            success = await self.meilisearch_service.index_documents(documents)
            if success:
                logger.info(f"Indexed {len(documents)} receipts for search")
                return len(documents)
            return 0
        except Exception as e:
            logger.error(f"Failed to index receipts: {e}")
            raise SearchError(f"Failed to index receipts: {e}")

    async def search_receipts(
        self,
        user_id: str,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """Search receipts."""
        try:
            # Add user filter to ensure users only see their receipts
            search_filters = {"user_id": user_id}

            # Add custom filters
            if filters:
                search_filters.update(filters)

            # Convert sort options
            sort_options = None
            if sort_by:
                sort_direction = "asc" if sort_order.lower() == "asc" else "desc"
                sort_options = [f"{sort_by}:{sort_direction}"]

            # Perform search
            response = await self.meilisearch_service.search(
                query=query,
                filters=search_filters,
                limit=limit,
                offset=offset,
                sort=sort_options,
                attributes_to_highlight=["merchant_name", "searchable_text"],
                attributes_to_crop=["searchable_text"],
            )

            # Process results
            hits = response.get("hits", [])
            total_hits = response.get("estimatedTotalHits", 0)
            processing_time = response.get("processingTimeMs", 0)

            logger.debug(f"Search for '{query}' returned {len(hits)} results")

            return {
                "hits": hits,
                "total_hits": total_hits,
                "processing_time_ms": processing_time,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(hits) < total_hits,
            }
        except Exception as e:
            logger.error(f"Failed to search receipts: {e}")
            raise SearchError(f"Failed to search receipts: {e}")

    async def search_by_merchant(
        self, user_id: str, merchant_name: str, limit: int = 20, offset: int = 0
    ) -> dict[str, Any]:
        """Search receipts by merchant name."""
        try:
            filters = {"user_id": user_id, "merchant_name": merchant_name}

            response = await self.meilisearch_service.search(
                query="",  # Empty query to get all documents matching filters
                filters=filters,
                limit=limit,
                offset=offset,
                sort=["created_at_timestamp:desc"],
            )

            return {
                "hits": response.get("hits", []),
                "total_hits": response.get("estimatedTotalHits", 0),
                "processing_time_ms": response.get("processingTimeMs", 0),
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Failed to search by merchant: {e}")
            raise SearchError(f"Failed to search by merchant: {e}")

    async def search_by_date_range(
        self,
        user_id: str,
        start_timestamp: int,
        end_timestamp: int,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search receipts by date range."""
        try:
            filters = {
                "user_id": user_id,
                "purchase_date_timestamp": {
                    "gte": start_timestamp,
                    "lte": end_timestamp,
                },
            }

            response = await self.meilisearch_service.search(
                query="",
                filters=filters,
                limit=limit,
                offset=offset,
                sort=["purchase_date_timestamp:desc"],
            )

            return {
                "hits": response.get("hits", []),
                "total_hits": response.get("estimatedTotalHits", 0),
                "processing_time_ms": response.get("processingTimeMs", 0),
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Failed to search by date range: {e}")
            raise SearchError(f"Failed to search by date range: {e}")

    async def search_by_amount_range(
        self,
        user_id: str,
        min_amount: float,
        max_amount: float,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search receipts by amount range."""
        try:
            filters = {
                "user_id": user_id,
                "total_amount": {"gte": min_amount, "lte": max_amount},
            }

            response = await self.meilisearch_service.search(
                query="",
                filters=filters,
                limit=limit,
                offset=offset,
                sort=["total_amount:desc"],
            )

            return {
                "hits": response.get("hits", []),
                "total_hits": response.get("estimatedTotalHits", 0),
                "processing_time_ms": response.get("processingTimeMs", 0),
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Failed to search by amount range: {e}")
            raise SearchError(f"Failed to search by amount range: {e}")

    async def search_by_tags(
        self, user_id: str, tags: list[str], limit: int = 20, offset: int = 0
    ) -> dict[str, Any]:
        """Search receipts by tags."""
        try:
            # Create filter for tags (documents that contain any of the specified tags)
            tag_filters = []
            for tag in tags:
                tag_filters.append(f"tags = {tag}")

            filters = {"user_id": user_id}

            # Join tag filters with OR
            if tag_filters:
                filters["_filter"] = f"({' OR '.join(tag_filters)})"

            response = await self.meilisearch_service.search(
                query="",
                filters=filters,
                limit=limit,
                offset=offset,
                sort=["created_at_timestamp:desc"],
            )

            return {
                "hits": response.get("hits", []),
                "total_hits": response.get("estimatedTotalHits", 0),
                "processing_time_ms": response.get("processingTimeMs", 0),
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            logger.error(f"Failed to search by tags: {e}")
            raise SearchError(f"Failed to search by tags: {e}")

    async def remove_receipt(self, receipt_id: str) -> bool:
        """Remove receipt from search index."""
        try:
            success = await self.meilisearch_service.delete_document(receipt_id)
            if success:
                logger.debug(f"Removed receipt {receipt_id} from search index")
            return success
        except Exception as e:
            logger.error(f"Failed to remove receipt {receipt_id} from search: {e}")
            raise SearchError(f"Failed to remove receipt from search: {e}")

    async def remove_receipts(self, receipt_ids: list[str]) -> int:
        """Remove multiple receipts from search index."""
        try:
            if not receipt_ids:
                return 0

            count = await self.meilisearch_service.delete_documents(receipt_ids)
            if count > 0:
                logger.info(f"Removed {count} receipts from search index")
            return count
        except Exception as e:
            logger.error(f"Failed to remove receipts from search: {e}")
            raise SearchError(f"Failed to remove receipts from search: {e}")

    async def clear_user_receipts(self, user_id: str) -> bool:
        """Clear all receipts for a user from search index."""
        try:
            # First, search for all user receipts to get their IDs
            response = await self.meilisearch_service.search(
                query="",
                filters={"user_id": user_id},
                limit=10000,  # Large limit to get all user receipts
            )

            receipt_ids = [hit["receipt_id"] for hit in response.get("hits", [])]

            if receipt_ids:
                count = await self.remove_receipts(receipt_ids)
                logger.info(
                    f"Cleared {count} receipts for user {user_id} from search index"
                )
                return count > 0

            return True
        except Exception as e:
            logger.error(f"Failed to clear receipts for user {user_id}: {e}")
            raise SearchError(f"Failed to clear user receipts: {e}")

    async def get_search_stats(self) -> dict[str, Any]:
        """Get search index statistics."""
        try:
            stats = await self.meilisearch_service.get_index_stats()
            return stats
        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")
            raise SearchError(f"Failed to get search stats: {e}")

    async def update_search_settings(self, settings: dict[str, Any]) -> bool:
        """Update search index settings."""
        try:
            success = await self.meilisearch_service.update_settings(settings)
            if success:
                logger.info("Updated search index settings")
            return success
        except Exception as e:
            logger.error(f"Failed to update search settings: {e}")
            raise SearchError(f"Failed to update search settings: {e}")
