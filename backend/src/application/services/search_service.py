"""Search service for application layer."""

import logging
from typing import Any

from src.application.api.dto import (
    AmountRangeSearchRequest,
    DateRangeSearchRequest,
    SearchRequest,
    SearchResponse,
    TagSearchRequest,
)
from src.domain.exceptions import SearchError, ValidationError
from src.infrastructure.config import infrastructure_config

logger = logging.getLogger(__name__)


class SearchService:
    """Application service for search operations."""

    def __init__(self):
        """Initialize search service."""
        self.search_repository = None

    def _get_search_repository(self):
        """Get search repository (lazy initialization)."""
        if self.search_repository is None:
            try:
                self.search_repository = infrastructure_config.get_search_repository()
            except Exception as e:
                logger.warning(f"Search repository not available: {e}")
                raise ValidationError("Search functionality is not available")
        return self.search_repository

    async def search_receipts(
        self, user_id: str, request: SearchRequest
    ) -> SearchResponse:
        """Search receipts using text query."""
        try:
            search_repo = self._get_search_repository()

            result = await search_repo.search_receipts(
                user_id=user_id,
                query=request.query,
                filters=request.filters,
                limit=request.limit,
                offset=request.offset,
                sort_by=request.sort_by,
                sort_order=request.sort_order,
            )

            logger.debug(
                f"Search returned {len(result['hits'])} results for user {user_id}"
            )

            return SearchResponse(
                hits=result["hits"],
                total_hits=result["total_hits"],
                processing_time_ms=result["processing_time_ms"],
                limit=request.limit,
                offset=request.offset,
                has_more=result["has_more"],
            )

        except SearchError as e:
            logger.error(f"Search failed: {e}")
            raise ValidationError(f"Search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            raise ValidationError(f"Search failed: {e}")

    async def search_by_merchant(
        self, user_id: str, merchant_name: str, limit: int = 20, offset: int = 0
    ) -> SearchResponse:
        """Search receipts by merchant name."""
        try:
            search_repo = self._get_search_repository()

            result = await search_repo.search_by_merchant(
                user_id=user_id, merchant_name=merchant_name, limit=limit, offset=offset
            )

            return SearchResponse(
                hits=result["hits"],
                total_hits=result["total_hits"],
                processing_time_ms=result["processing_time_ms"],
                limit=limit,
                offset=offset,
                has_more=(offset + len(result["hits"])) < result["total_hits"],
            )

        except SearchError as e:
            logger.error(f"Merchant search failed: {e}")
            raise ValidationError(f"Merchant search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected merchant search error: {e}")
            raise ValidationError(f"Merchant search failed: {e}")

    async def search_by_date_range(
        self, user_id: str, request: DateRangeSearchRequest
    ) -> SearchResponse:
        """Search receipts by date range."""
        try:
            search_repo = self._get_search_repository()

            start_timestamp = int(request.start_date.timestamp())
            end_timestamp = int(request.end_date.timestamp())

            result = await search_repo.search_by_date_range(
                user_id=user_id,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                limit=request.limit,
                offset=request.offset,
            )

            return SearchResponse(
                hits=result["hits"],
                total_hits=result["total_hits"],
                processing_time_ms=result["processing_time_ms"],
                limit=request.limit,
                offset=request.offset,
                has_more=(request.offset + len(result["hits"])) < result["total_hits"],
            )

        except SearchError as e:
            logger.error(f"Date range search failed: {e}")
            raise ValidationError(f"Date range search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected date range search error: {e}")
            raise ValidationError(f"Date range search failed: {e}")

    async def search_by_amount_range(
        self, user_id: str, request: AmountRangeSearchRequest
    ) -> SearchResponse:
        """Search receipts by amount range."""
        try:
            search_repo = self._get_search_repository()

            result = await search_repo.search_by_amount_range(
                user_id=user_id,
                min_amount=float(request.min_amount),
                max_amount=float(request.max_amount),
                limit=request.limit,
                offset=request.offset,
            )

            return SearchResponse(
                hits=result["hits"],
                total_hits=result["total_hits"],
                processing_time_ms=result["processing_time_ms"],
                limit=request.limit,
                offset=request.offset,
                has_more=(request.offset + len(result["hits"])) < result["total_hits"],
            )

        except SearchError as e:
            logger.error(f"Amount range search failed: {e}")
            raise ValidationError(f"Amount range search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected amount range search error: {e}")
            raise ValidationError(f"Amount range search failed: {e}")

    async def search_by_tags(
        self, user_id: str, request: TagSearchRequest
    ) -> SearchResponse:
        """Search receipts by tags."""
        try:
            search_repo = self._get_search_repository()

            result = await search_repo.search_by_tags(
                user_id=user_id,
                tags=request.tags,
                limit=request.limit,
                offset=request.offset,
            )

            return SearchResponse(
                hits=result["hits"],
                total_hits=result["total_hits"],
                processing_time_ms=result["processing_time_ms"],
                limit=request.limit,
                offset=request.offset,
                has_more=(request.offset + len(result["hits"])) < result["total_hits"],
            )

        except SearchError as e:
            logger.error(f"Tag search failed: {e}")
            raise ValidationError(f"Tag search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected tag search error: {e}")
            raise ValidationError(f"Tag search failed: {e}")

    async def get_suggestions(
        self, user_id: str, query: str, limit: int = 5
    ) -> list[str]:
        """Get search suggestions based on partial query."""
        try:
            search_repo = self._get_search_repository()

            # Get search results with limited fields for suggestions
            result = await search_repo.search_receipts(
                user_id=user_id, query=query, limit=limit, offset=0
            )

            # Extract suggestions from results
            suggestions = set()
            for hit in result["hits"]:
                # Add merchant names
                if hit.get("merchant_name"):
                    suggestions.add(hit["merchant_name"])

                # Add item names
                for item in hit.get("items", []):
                    if item.get("name"):
                        suggestions.add(item["name"])

                # Add categories
                for item in hit.get("items", []):
                    if item.get("category"):
                        suggestions.add(item["category"])

                # Add tags
                for tag in hit.get("tags", []):
                    suggestions.add(tag)

            # Filter suggestions that contain the query
            filtered_suggestions = [
                suggestion
                for suggestion in suggestions
                if query.lower() in suggestion.lower()
            ]

            return list(filtered_suggestions)[:limit]

        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return []

    async def get_popular_merchants(
        self, user_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get popular merchants for user."""
        try:
            search_repo = self._get_search_repository()

            # Get all receipts and aggregate by merchant
            result = await search_repo.search_receipts(
                user_id=user_id,
                query="",
                limit=1000,  # Large limit to get all receipts
            )

            merchant_stats = {}
            for hit in result["hits"]:
                merchant = hit.get("merchant_name")
                if merchant:
                    if merchant not in merchant_stats:
                        merchant_stats[merchant] = {
                            "name": merchant,
                            "count": 0,
                            "total_amount": 0.0,
                        }

                    merchant_stats[merchant]["count"] += 1
                    if hit.get("total_amount"):
                        merchant_stats[merchant]["total_amount"] += hit["total_amount"]

            # Sort by count and return top merchants
            sorted_merchants = sorted(
                merchant_stats.values(), key=lambda x: x["count"], reverse=True
            )

            return sorted_merchants[:limit]

        except Exception as e:
            logger.error(f"Failed to get popular merchants: {e}")
            return []

    async def get_popular_tags(
        self, user_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get popular tags for user."""
        try:
            search_repo = self._get_search_repository()

            # Get all receipts and aggregate by tags
            result = await search_repo.search_receipts(
                user_id=user_id,
                query="",
                limit=1000,  # Large limit to get all receipts
            )

            tag_stats = {}
            for hit in result["hits"]:
                for tag in hit.get("tags", []):
                    if tag not in tag_stats:
                        tag_stats[tag] = {"name": tag, "count": 0}
                    tag_stats[tag]["count"] += 1

            # Sort by count and return top tags
            sorted_tags = sorted(
                tag_stats.values(), key=lambda x: x["count"], reverse=True
            )

            return sorted_tags[:limit]

        except Exception as e:
            logger.error(f"Failed to get popular tags: {e}")
            return []


# Global search service instance
search_service = SearchService()
