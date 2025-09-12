"""Cleanup inactive receipts use case implementation."""

from typing import List, Protocol
from ..repositories import ReceiptRepository, UserRepository, SearchRepository
from ..exceptions import RepositoryError
from ..config import DOMAIN_CONFIG


class S3Service(Protocol):
    """Protocol for S3 service operations."""

    async def delete_objects(self, bucket: str, keys: List[str]) -> int:
        """Delete multiple objects from S3."""
        ...


class CleanupInactiveReceiptsUseCase:
    """Use case for cleaning up receipts from inactive free users."""

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

    async def execute(self, days_threshold: int = None) -> dict:
        """
        Execute cleanup of receipts from inactive free users.

        Args:
            days_threshold: Number of days of inactivity before cleanup.
                          If None, uses the default from domain config.

        Returns:
            Dictionary with cleanup statistics
        """
        if days_threshold is None:
            days_threshold = (
                DOMAIN_CONFIG.data_retention.INACTIVE_FREE_USER_THRESHOLD_DAYS
            )

        stats = {
            "inactive_users_found": 0,
            "receipts_deleted": 0,
            "s3_objects_deleted": 0,
            "errors": [],
        }

        try:
            # Get inactive free users
            inactive_users = await self.user_repository.get_inactive_free_users(
                days_threshold
            )
            stats["inactive_users_found"] = len(inactive_users)

            if not inactive_users:
                return stats

            # Get receipts for inactive users
            all_receipts_to_delete = []

            for user in inactive_users:
                try:
                    user_receipts = await self.receipt_repository.get_by_user_id(
                        user.user_id
                    )
                    all_receipts_to_delete.extend(user_receipts)
                except Exception as e:
                    stats["errors"].append(
                        f"Failed to get receipts for user {user.user_id}: {str(e)}"
                    )
                    continue

            if not all_receipts_to_delete:
                return stats

            # Collect S3 keys and receipt IDs
            s3_keys_to_delete = []
            receipt_ids_to_delete = []

            for receipt in all_receipts_to_delete:
                receipt_ids_to_delete.append(receipt.image_id)

                # Add all S3 keys for this receipt
                for key in receipt.s3_keys.values():
                    if key:  # Only add non-empty keys
                        s3_keys_to_delete.append(key)

            # Delete from S3 (in batches to avoid large requests)
            batch_size = DOMAIN_CONFIG.processing.S3_DELETE_BATCH_SIZE
            s3_deleted_total = 0

            for i in range(0, len(s3_keys_to_delete), batch_size):
                batch = s3_keys_to_delete[i : i + batch_size]
                try:
                    s3_deleted_count = await self.s3_service.delete_objects(
                        bucket=self.s3_bucket, keys=batch
                    )
                    s3_deleted_total += s3_deleted_count
                except Exception as e:
                    stats["errors"].append(f"Failed to delete S3 batch: {str(e)}")

            stats["s3_objects_deleted"] = s3_deleted_total

            # Delete from search index
            try:
                await self.search_repository.bulk_delete(receipt_ids_to_delete)
            except Exception as e:
                stats["errors"].append(f"Failed to delete from search index: {str(e)}")

            # Delete from database
            try:
                deleted_count = await self.receipt_repository.bulk_delete(
                    receipt_ids_to_delete
                )
                stats["receipts_deleted"] = deleted_count
            except Exception as e:
                stats["errors"].append(f"Failed to delete from database: {str(e)}")

            # Reset user image counts to 0 for cleaned up users
            for user in inactive_users:
                try:
                    user.image_count = 0
                    await self.user_repository.update(user)
                except Exception as e:
                    stats["errors"].append(
                        f"Failed to update user {user.user_id}: {str(e)}"
                    )

        except Exception as e:
            stats["errors"].append(f"Unexpected error during cleanup: {str(e)}")
            raise RepositoryError(f"Cleanup failed: {str(e)}")

        return stats
