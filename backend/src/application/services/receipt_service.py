"""Receipt service for application layer."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import asyncio

from src.domain.entities.receipt import Receipt
from src.domain.use_cases.receipt_use_cases import (
    CreateReceiptUseCase,
    GetReceiptUseCase,
    UpdateReceiptUseCase,
    DeleteReceiptUseCase,
    ProcessReceiptImageUseCase,
)
from src.application.api.dto import (
    ReceiptCreateRequest,
    ReceiptUpdateRequest,
    ReceiptResponse,
    ReceiptListResponse,
    ReceiptItemResponse,
    ImageUploadResponse,
    ImageProcessingStatusResponse,
    PaginationParams,
)
from src.infrastructure.config import infrastructure_config
from src.domain.exceptions import ReceiptNotFoundError, ValidationError
from src.domain.config import DOMAIN_CONFIG

logger = logging.getLogger(__name__)


class ReceiptService:
    """Application service for receipt operations."""

    def __init__(self):
        """Initialize receipt service."""
        self.receipt_repository = infrastructure_config.get_receipt_repository()
        self.search_repository = None
        self.s3_service = infrastructure_config.get_s3_service()
        self.textract_service = infrastructure_config.get_textract_service()
        self.sqs_service = infrastructure_config.get_sqs_service()

        # Use cases
        self.create_receipt_use_case = CreateReceiptUseCase(self.receipt_repository)
        self.get_receipt_use_case = GetReceiptUseCase(self.receipt_repository)
        self.update_receipt_use_case = UpdateReceiptUseCase(self.receipt_repository)
        self.delete_receipt_use_case = DeleteReceiptUseCase(self.receipt_repository)
        self.process_receipt_image_use_case = ProcessReceiptImageUseCase(
            self.receipt_repository, self.s3_service, self.textract_service
        )

    def _get_search_repository(self):
        """Get search repository (lazy initialization)."""
        if self.search_repository is None:
            try:
                self.search_repository = infrastructure_config.get_search_repository()
            except Exception as e:
                logger.warning(f"Search repository not available: {e}")
        return self.search_repository

    def _to_receipt_response(self, receipt: Receipt) -> ReceiptResponse:
        """Convert Receipt entity to response DTO."""
        items = None
        if receipt.items:
            items = [
                ReceiptItemResponse(
                    name=item.name,
                    category=item.category,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    metadata=item.metadata,
                )
                for item in receipt.items
            ]

        return ReceiptResponse(
            receipt_id=receipt.receipt_id,
            user_id=receipt.user_id,
            image_id=receipt.image_id,
            merchant_name=receipt.merchant_name,
            merchant_address=receipt.merchant_address,
            purchase_date=receipt.purchase_date,
            total_amount=receipt.total_amount,
            currency=receipt.currency,
            receipt_type=receipt.receipt_type,
            raw_text=receipt.raw_text,
            confidence_score=receipt.confidence_score,
            extraction_metadata=receipt.extraction_metadata,
            items=items,
            tags=receipt.tags,
            notes=receipt.notes,
            created_at=receipt.created_at,
            updated_at=receipt.updated_at,
            version=receipt.version,
        )

    async def create_receipt(
        self, user_id: str, request: ReceiptCreateRequest
    ) -> ReceiptResponse:
        """Create a receipt manually."""
        try:
            # Convert request to domain data
            items_data = []
            if request.items:
                items_data = [
                    {
                        "name": item.name,
                        "category": item.category,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                        "metadata": item.metadata or {},
                    }
                    for item in request.items
                ]

            receipt_data = {
                "user_id": user_id,
                "merchant_name": request.merchant_name,
                "merchant_address": request.merchant_address,
                "purchase_date": request.purchase_date,
                "total_amount": request.total_amount,
                "currency": request.currency,
                "receipt_type": request.receipt_type,
                "items": items_data,
                "tags": request.tags or [],
                "notes": request.notes,
            }

            receipt = await self.create_receipt_use_case.execute(receipt_data)

            # Index for search
            search_repo = self._get_search_repository()
            if search_repo:
                try:
                    await search_repo.index_receipt(receipt)
                except Exception as e:
                    logger.warning(f"Failed to index receipt for search: {e}")

            logger.info(f"Receipt created manually: {receipt.receipt_id}")
            return self._to_receipt_response(receipt)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create receipt: {e}")
            raise ValidationError(f"Receipt creation failed: {e}")

    async def get_receipt(self, receipt_id: str, user_id: str) -> ReceiptResponse:
        """Get a receipt by ID."""
        try:
            receipt = await self.get_receipt_use_case.execute(receipt_id)

            # Check ownership
            if receipt.user_id != user_id:
                raise ReceiptNotFoundError("Receipt not found")

            return self._to_receipt_response(receipt)
        except ReceiptNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get receipt: {e}")
            raise ValidationError(f"Failed to get receipt: {e}")

    async def update_receipt(
        self, receipt_id: str, user_id: str, request: ReceiptUpdateRequest
    ) -> ReceiptResponse:
        """Update a receipt."""
        try:
            # Get existing receipt and check ownership
            receipt = await self.get_receipt_use_case.execute(receipt_id)
            if receipt.user_id != user_id:
                raise ReceiptNotFoundError("Receipt not found")

            # Convert request to update data
            update_data = {}
            if request.merchant_name is not None:
                update_data["merchant_name"] = request.merchant_name
            if request.merchant_address is not None:
                update_data["merchant_address"] = request.merchant_address
            if request.purchase_date is not None:
                update_data["purchase_date"] = request.purchase_date
            if request.total_amount is not None:
                update_data["total_amount"] = request.total_amount
            if request.currency is not None:
                update_data["currency"] = request.currency
            if request.receipt_type is not None:
                update_data["receipt_type"] = request.receipt_type
            if request.tags is not None:
                update_data["tags"] = request.tags
            if request.notes is not None:
                update_data["notes"] = request.notes

            if request.items is not None:
                items_data = [
                    {
                        "name": item.name,
                        "category": item.category,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                        "metadata": item.metadata or {},
                    }
                    for item in request.items
                ]
                update_data["items"] = items_data

            updated_receipt = await self.update_receipt_use_case.execute(
                receipt_id, update_data
            )

            # Update search index
            search_repo = self._get_search_repository()
            if search_repo:
                try:
                    await search_repo.index_receipt(updated_receipt)
                except Exception as e:
                    logger.warning(f"Failed to update receipt in search index: {e}")

            logger.info(f"Receipt updated: {receipt_id}")
            return self._to_receipt_response(updated_receipt)

        except (ReceiptNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update receipt: {e}")
            raise ValidationError(f"Receipt update failed: {e}")

    async def delete_receipt(self, receipt_id: str, user_id: str) -> bool:
        """Delete a receipt."""
        try:
            # Get receipt and check ownership
            receipt = await self.get_receipt_use_case.execute(receipt_id)
            if receipt.user_id != user_id:
                raise ReceiptNotFoundError("Receipt not found")

            success = await self.delete_receipt_use_case.execute(receipt_id)

            if success:
                # Remove from search index
                search_repo = self._get_search_repository()
                if search_repo:
                    try:
                        await search_repo.remove_receipt(receipt_id)
                    except Exception as e:
                        logger.warning(
                            f"Failed to remove receipt from search index: {e}"
                        )

                # Delete image from S3 if exists
                if receipt.image_id:
                    try:
                        await self.s3_service.delete_object(receipt.image_id)
                    except Exception as e:
                        logger.warning(f"Failed to delete image from S3: {e}")

                logger.info(f"Receipt deleted: {receipt_id}")

            return success
        except ReceiptNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete receipt: {e}")
            raise ValidationError(f"Receipt deletion failed: {e}")

    async def list_receipts(
        self, user_id: str, pagination: PaginationParams
    ) -> ReceiptListResponse:
        """List receipts for a user."""
        try:
            receipts = await self.receipt_repository.find_by_user_id(
                user_id=user_id, limit=pagination.limit
            )

            # Get total count
            total_count = await self.receipt_repository.count_by_user_id(user_id)

            receipt_responses = [
                self._to_receipt_response(receipt) for receipt in receipts
            ]

            return ReceiptListResponse(
                receipts=receipt_responses,
                total_count=total_count,
                page=pagination.page,
                page_size=pagination.page_size,
                has_more=(pagination.offset + len(receipts)) < total_count,
            )
        except Exception as e:
            logger.error(f"Failed to list receipts: {e}")
            raise ValidationError(f"Failed to list receipts: {e}")

    async def generate_upload_url(self, user_id: str) -> ImageUploadResponse:
        """Generate presigned URL for image upload."""
        try:
            image_id = str(uuid.uuid4())
            key = f"uploads/{user_id}/{image_id}"

            # Generate presigned URL
            upload_data = await self.s3_service.generate_presigned_post(
                key=key,
                expires_in=DOMAIN_CONFIG.UPLOAD_URL_EXPIRES_IN,
                max_file_size=DOMAIN_CONFIG.MAX_FILE_SIZE_BYTES,
            )

            logger.info(f"Generated upload URL for user {user_id}, image {image_id}")

            return ImageUploadResponse(
                image_id=image_id,
                upload_url=upload_data["url"],
                fields=upload_data["fields"],
                expires_in=DOMAIN_CONFIG.UPLOAD_URL_EXPIRES_IN,
            )
        except Exception as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise ValidationError(f"Upload URL generation failed: {e}")

    async def process_uploaded_image(
        self, user_id: str, image_id: str
    ) -> ImageProcessingStatusResponse:
        """Process uploaded image and extract receipt data."""
        try:
            # Check if image exists in S3
            key = f"uploads/{user_id}/{image_id}"
            exists = await self.s3_service.object_exists(key)

            if not exists:
                return ImageProcessingStatusResponse(
                    image_id=image_id, status="failed", error_message="Image not found"
                )

            # Send processing message to SQS for async processing
            try:
                message = {
                    "user_id": user_id,
                    "image_id": image_id,
                    "object_key": key,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                queue_url = f"receipt-processing-queue"  # This should come from config
                await self.sqs_service.send_message(queue_url, message)

                logger.info(f"Queued image processing for {image_id}")

                return ImageProcessingStatusResponse(
                    image_id=image_id, status="pending", progress=0
                )
            except Exception as e:
                logger.warning(
                    f"Failed to queue image processing, processing synchronously: {e}"
                )

                # Fallback to synchronous processing
                receipt_data = {
                    "user_id": user_id,
                    "image_id": image_id,
                    "object_key": key,
                }

                receipt = await self.process_receipt_image_use_case.execute(
                    receipt_data
                )

                # Index for search
                search_repo = self._get_search_repository()
                if search_repo:
                    try:
                        await search_repo.index_receipt(receipt)
                    except Exception as e:
                        logger.warning(f"Failed to index receipt for search: {e}")

                return ImageProcessingStatusResponse(
                    image_id=image_id,
                    status="completed",
                    progress=100,
                    receipt=self._to_receipt_response(receipt),
                )

        except Exception as e:
            logger.error(f"Failed to process uploaded image: {e}")
            return ImageProcessingStatusResponse(
                image_id=image_id, status="failed", error_message=str(e)
            )

    async def get_processing_status(
        self, user_id: str, image_id: str
    ) -> ImageProcessingStatusResponse:
        """Get image processing status."""
        try:
            # Check if receipt exists
            receipt = await self.receipt_repository.find_by_image_id(image_id)

            if receipt:
                # Check ownership
                if receipt.user_id != user_id:
                    return ImageProcessingStatusResponse(
                        image_id=image_id,
                        status="failed",
                        error_message="Access denied",
                    )

                return ImageProcessingStatusResponse(
                    image_id=image_id,
                    status="completed",
                    progress=100,
                    receipt=self._to_receipt_response(receipt),
                )

            # Check if image exists (still processing)
            key = f"uploads/{user_id}/{image_id}"
            exists = await self.s3_service.object_exists(key)

            if exists:
                return ImageProcessingStatusResponse(
                    image_id=image_id, status="processing", progress=50
                )

            return ImageProcessingStatusResponse(
                image_id=image_id, status="failed", error_message="Image not found"
            )

        except Exception as e:
            logger.error(f"Failed to get processing status: {e}")
            return ImageProcessingStatusResponse(
                image_id=image_id, status="failed", error_message=str(e)
            )

    async def get_receipts_by_date_range(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        pagination: PaginationParams,
    ) -> ReceiptListResponse:
        """Get receipts by date range."""
        try:
            receipts = await self.receipt_repository.find_by_date_range(
                user_id=user_id, start_date=start_date, end_date=end_date
            )

            # Apply pagination in memory (not ideal for large datasets)
            paginated_receipts = receipts[
                pagination.offset : pagination.offset + pagination.limit
            ]
            receipt_responses = [
                self._to_receipt_response(receipt) for receipt in paginated_receipts
            ]

            return ReceiptListResponse(
                receipts=receipt_responses,
                total_count=len(receipts),
                page=pagination.page,
                page_size=pagination.page_size,
                has_more=(pagination.offset + len(paginated_receipts)) < len(receipts),
            )
        except Exception as e:
            logger.error(f"Failed to get receipts by date range: {e}")
            raise ValidationError(f"Failed to get receipts by date range: {e}")

    async def get_receipts_by_merchant(
        self, user_id: str, merchant_name: str, pagination: PaginationParams
    ) -> ReceiptListResponse:
        """Get receipts by merchant."""
        try:
            receipts = await self.receipt_repository.find_by_merchant(
                user_id=user_id, merchant_name=merchant_name
            )

            # Apply pagination in memory
            paginated_receipts = receipts[
                pagination.offset : pagination.offset + pagination.limit
            ]
            receipt_responses = [
                self._to_receipt_response(receipt) for receipt in paginated_receipts
            ]

            return ReceiptListResponse(
                receipts=receipt_responses,
                total_count=len(receipts),
                page=pagination.page,
                page_size=pagination.page_size,
                has_more=(pagination.offset + len(paginated_receipts)) < len(receipts),
            )
        except Exception as e:
            logger.error(f"Failed to get receipts by merchant: {e}")
            raise ValidationError(f"Failed to get receipts by merchant: {e}")


# Global receipt service instance
receipt_service = ReceiptService()
