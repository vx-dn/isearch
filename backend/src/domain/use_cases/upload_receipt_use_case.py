"""Upload receipt use case implementation."""

import uuid
from datetime import datetime
from typing import Protocol
from ..entities import Receipt, ProcessingStatus
from ..repositories import ReceiptRepository, UserRepository
from ..dtos import UploadReceiptRequest, UploadReceiptResponse
from ..exceptions import QuotaExceededError, ValidationError, ResourceNotFoundError
from ..config import DOMAIN_CONFIG


class S3Service(Protocol):
    """Protocol for S3 service operations."""

    async def generate_presigned_url(
        self, bucket: str, key: str, file_size: int
    ) -> dict:
        """Generate presigned URL for file upload."""
        ...


class UploadReceiptUseCase:
    """Use case for uploading receipts."""

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

    async def execute(self, request: UploadReceiptRequest) -> UploadReceiptResponse:
        """Execute the upload receipt use case."""
        # Validate input
        if not request.file_names or not request.file_sizes:
            raise ValidationError("File names and sizes are required")

        if len(request.file_names) != len(request.file_sizes):
            raise ValidationError(
                "Number of file names must match number of file sizes"
            )

        num_files = len(request.file_names)

        # Get user and validate quota
        user = await self.user_repository.get_by_id(request.user_id)
        if not user:
            raise ResourceNotFoundError(f"User {request.user_id} not found")

        if not user.can_upload(num_files):
            raise QuotaExceededError(
                f"User quota exceeded. Can upload {user.get_available_quota()} more images"
            )

        # Create receipts and generate presigned URLs
        receipt_ids = []
        presigned_urls = []
        receipts = []

        for file_name, file_size in zip(request.file_names, request.file_sizes):
            # Validate file size using configuration
            if file_size > DOMAIN_CONFIG.file_constraints.MAX_FILE_SIZE_BYTES:
                max_size_mb = DOMAIN_CONFIG.file_constraints.MAX_FILE_SIZE_BYTES // (
                    1024 * 1024
                )
                raise ValidationError(
                    f"File {file_name} is too large (max {max_size_mb}MB)"
                )

            # Generate unique receipt ID
            receipt_id = str(uuid.uuid4())

            # Generate S3 keys
            s3_keys = {
                "original": f"receipts/{request.user_id}/{receipt_id}/original",
                "thumbnail": f"receipts/{request.user_id}/{receipt_id}/thumbnail",
                "resized": f"receipts/{request.user_id}/{receipt_id}/resized",
            }

            # Create receipt entity
            receipt = Receipt(
                image_id=receipt_id,
                user_id=request.user_id,
                file_name=file_name,
                file_size=file_size,
                upload_date=datetime.utcnow(),
                s3_keys=s3_keys,
                processing_status=ProcessingStatus.PENDING,
            )

            # Generate presigned URL for original file
            presigned_url = await self.s3_service.generate_presigned_url(
                bucket=self.s3_bucket, key=s3_keys["original"], file_size=file_size
            )

            receipts.append(receipt)
            receipt_ids.append(receipt_id)
            presigned_urls.append(presigned_url)

        # Save all receipts
        for receipt in receipts:
            await self.receipt_repository.save(receipt)

        # Update user image count
        await self.user_repository.increment_image_count(request.user_id, num_files)

        # Update user last active
        await self.user_repository.update_last_active(request.user_id)

        return UploadReceiptResponse(
            receipt_ids=receipt_ids,
            presigned_urls=presigned_urls,
            quota_remaining=user.get_available_quota() - num_files,
        )
