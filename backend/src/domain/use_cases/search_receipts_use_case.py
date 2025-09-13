"""Search receipts use case implementation."""

from datetime import datetime
from typing import Protocol

from ..config import DOMAIN_CONFIG
from ..dtos import ReceiptSearchRequest, ReceiptSearchResponse, ReceiptSearchResult
from ..exceptions import ResourceNotFoundError, ValidationError
from ..repositories import SearchRepository, UserRepository


class S3Service(Protocol):
    """Protocol for S3 service operations."""

    async def generate_thumbnail_url(self, bucket: str, key: str) -> str:
        """Generate URL for thumbnail image."""
        ...


class SearchReceiptsUseCase:
    """Use case for searching receipts."""

    def __init__(
        self,
        search_repository: SearchRepository,
        user_repository: UserRepository,
        s3_service: S3Service,
        s3_bucket: str,
    ):
        self.search_repository = search_repository
        self.user_repository = user_repository
        self.s3_service = s3_service
        self.s3_bucket = s3_bucket

    async def execute(self, request: ReceiptSearchRequest) -> ReceiptSearchResponse:
        """Execute the search receipts use case."""
        # Validate user exists
        user = await self.user_repository.get_by_id(request.user_id)
        if not user:
            raise ResourceNotFoundError(f"User {request.user_id} not found")

        # Update user last active
        await self.user_repository.update_last_active(request.user_id)

        # Validate search parameters
        if request.limit <= 0 or request.limit > DOMAIN_CONFIG.search.MAX_SEARCH_LIMIT:
            raise ValidationError(
                f"Limit must be between 1 and {DOMAIN_CONFIG.search.MAX_SEARCH_LIMIT}"
            )

        if request.offset < 0:
            raise ValidationError("Offset must be non-negative")

        # Build search filters
        filters = {}

        if request.date_added_from or request.date_added_to:
            filters["upload_date"] = {}
            if request.date_added_from:
                filters["upload_date"]["gte"] = request.date_added_from.timestamp()
            if request.date_added_to:
                filters["upload_date"]["lte"] = request.date_added_to.timestamp()

        if request.date_extracted_from or request.date_extracted_to:
            # This would filter by dates found in the extracted text
            # Implementation depends on how dates are extracted and stored
            filters["extracted_date"] = {}
            if request.date_extracted_from:
                filters["extracted_date"]["gte"] = (
                    request.date_extracted_from.timestamp()
                )
            if request.date_extracted_to:
                filters["extracted_date"]["lte"] = request.date_extracted_to.timestamp()

        # Execute search
        start_time = datetime.utcnow()

        search_results = await self.search_repository.search(
            query=request.query,
            user_id=request.user_id,
            filters=filters,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
        )

        end_time = datetime.utcnow()
        query_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Convert search results to DTOs
        results = []
        for hit in search_results.get("hits", []):
            # Generate thumbnail URL
            thumbnail_url = await self.s3_service.generate_thumbnail_url(
                bucket=self.s3_bucket, key=hit["s3_keys"]["thumbnail"]
            )

            result = ReceiptSearchResult(
                receipt_id=hit["image_id"],
                file_name=hit["file_name"],
                upload_date=datetime.fromtimestamp(hit["upload_date"]),
                thumbnail_url=thumbnail_url,
                extracted_text_snippet=hit.get("_formatted", {}).get(
                    "extracted_text", ""
                )[: DOMAIN_CONFIG.search.MAX_EXTRACTED_TEXT_SNIPPET_LENGTH],
                processing_status=hit["processing_status"],
                relevance_score=hit.get("_rankingScore", 0.0),
            )
            results.append(result)

        total_count = search_results.get("estimatedTotalHits", 0)
        has_more = request.offset + len(results) < total_count

        return ReceiptSearchResponse(
            results=results,
            total_count=total_count,
            query_time_ms=query_time_ms,
            has_more=has_more,
        )
