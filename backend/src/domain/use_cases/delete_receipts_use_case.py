"""Delete receipts use case implementation."""

from typing import Protocol

from ..dtos import DeleteReceiptsRequest, DeleteReceiptsResponse
from ..exceptions import ResourceNotFoundError
from ..repositories import ReceiptRepository, SearchRepository, UserRepository


class S3Service(Protocol):
    """Protocol for S3 service operations."""

    async def delete_objects(self, bucket: str, keys: list[str]) -> int:
        """Delete multiple objects from S3."""
        ...


class DeleteReceiptsUseCase:
    """Use case for deleting receipts."""

    def __init__(
        self,
        receipt_repository: ReceiptRepository,
        user_repository: UserRepository,
        search_repository: SearchRepository,
        s3_service: S3Service,
        s3_bucket: str,
    ):
        self.receipt_repository = receipt_repository
        self.user_repository = user_repository
        self.search_repository = search_repository
        self.s3_service = s3_service
        self.s3_bucket = s3_bucket

    async def execute(self, request: DeleteReceiptsRequest) -> DeleteReceiptsResponse:
        """Execute the delete receipts use case."""
        if not request.receipt_ids:
            return DeleteReceiptsResponse(
                deleted_count=0, failed_ids=[], quota_restored=0
            )

        # Verify user exists
        user = await self.user_repository.get_by_id(request.user_id)
        if not user:
            raise ResourceNotFoundError(f"User {request.user_id} not found")

        # Get all receipts and verify ownership
        receipts = []
        failed_ids = []

        for receipt_id in request.receipt_ids:
            receipt = await self.receipt_repository.get_by_id(receipt_id)
            if not receipt:
                failed_ids.append(receipt_id)
                continue

            # Verify ownership (unless user is admin)
            if not user.is_admin() and receipt.user_id != request.user_id:
                failed_ids.append(receipt_id)
                continue

            receipts.append(receipt)

        if not receipts:
            return DeleteReceiptsResponse(
                deleted_count=0, failed_ids=failed_ids, quota_restored=0
            )

        # Collect S3 keys for deletion
        s3_keys_to_delete = []
        receipt_ids_to_delete = []

        for receipt in receipts:
            receipt_ids_to_delete.append(receipt.image_id)

            # Add all S3 keys for this receipt
            for key in receipt.s3_keys.values():
                if key:  # Only add non-empty keys
                    s3_keys_to_delete.append(key)

        # Delete from S3
        try:
            await self.s3_service.delete_objects(
                bucket=self.s3_bucket, keys=s3_keys_to_delete
            )
        except Exception:
            # If S3 deletion fails, still proceed with database cleanup
            # S3 cleanup can be handled by a separate maintenance job
            pass

        # Delete from search index
        await self.search_repository.bulk_delete(receipt_ids_to_delete)

        # Delete from database
        db_deleted_count = await self.receipt_repository.bulk_delete(
            receipt_ids_to_delete
        )

        # Update user quota (only for receipts owned by the requesting user)
        quota_restored = 0
        if not user.is_admin():  # Admin deletions don't affect user quotas
            user_receipts = [r for r in receipts if r.user_id == request.user_id]
            quota_restored = len(user_receipts)
            if quota_restored > 0:
                await self.user_repository.decrement_image_count(
                    request.user_id, quota_restored
                )

        # Update user last active
        await self.user_repository.update_last_active(request.user_id)

        return DeleteReceiptsResponse(
            deleted_count=db_deleted_count,
            failed_ids=failed_ids,
            quota_restored=quota_restored,
        )
