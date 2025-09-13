"""Get receipt details use case implementation."""

from typing import Protocol

from ..dtos import ReceiptDetailsResponse
from ..exceptions import ResourceNotFoundError, UnauthorizedAccessError
from ..repositories import ReceiptRepository, UserRepository


class S3Service(Protocol):
    """Protocol for S3 service operations."""

    async def generate_presigned_url_for_download(self, bucket: str, key: str) -> str:
        """Generate presigned URL for downloading/viewing image."""
        ...


class GetReceiptDetailsUseCase:
    """Use case for getting detailed receipt information."""

    def __init__(
        self,
        receipt_repository: ReceiptRepository,
        user_repository: UserRepository,
        s3_service: S3Service,
        s3_bucket: str,
    ):
        self.receipt_repository = receipt_repository
        self.user_repository = user_repository
        self.s3_service = s3_service
        self.s3_bucket = s3_bucket

    async def execute(
        self, receipt_id: str, requesting_user_id: str
    ) -> ReceiptDetailsResponse:
        """Execute the get receipt details use case."""
        # Get the receipt
        receipt = await self.receipt_repository.get_by_id(receipt_id)
        if not receipt:
            raise ResourceNotFoundError(f"Receipt {receipt_id} not found")

        # Get requesting user to check permissions
        user = await self.user_repository.get_by_id(requesting_user_id)
        if not user:
            raise ResourceNotFoundError(f"User {requesting_user_id} not found")

        # Check authorization (user can only see their own receipts, unless admin)
        if not user.is_admin() and receipt.user_id != requesting_user_id:
            raise UnauthorizedAccessError("You can only view your own receipts")

        # Generate URLs for images
        original_image_url = await self.s3_service.generate_presigned_url_for_download(
            bucket=self.s3_bucket, key=receipt.s3_keys["original"]
        )

        thumbnail_url = await self.s3_service.generate_presigned_url_for_download(
            bucket=self.s3_bucket, key=receipt.s3_keys["thumbnail"]
        )

        # Update user last active
        await self.user_repository.update_last_active(requesting_user_id)

        return ReceiptDetailsResponse(
            receipt_id=receipt.image_id,
            file_name=receipt.file_name,
            file_size=receipt.file_size,
            upload_date=receipt.upload_date,
            processing_status=receipt.processing_status,
            extracted_text=receipt.extracted_text,
            structured_data=receipt.structured_data,
            user_edits=receipt.user_edits,
            original_image_url=original_image_url,
            thumbnail_url=thumbnail_url,
        )
