"""DynamoDB implementation of receipt repository."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import logging

from src.domain.entities.receipt import Receipt
from src.domain.repositories.receipt_repository import ReceiptRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService
from src.domain.exceptions import ReceiptNotFoundError, DatabaseError
from src.domain.config import DOMAIN_CONFIG

logger = logging.getLogger(__name__)


class DynamoDBReceiptRepository(ReceiptRepository):
    """DynamoDB implementation of receipt repository."""

    def __init__(self, dynamodb_service: DynamoDBService):
        """Initialize repository with DynamoDB service."""
        self.dynamodb_service = dynamodb_service
        self.table_name = DOMAIN_CONFIG.RECEIPT_TABLE_NAME

    def _to_dynamodb_item(self, receipt: Receipt) -> Dict[str, Any]:
        """Convert Receipt entity to DynamoDB item."""
        return {
            "receipt_id": receipt.receipt_id,
            "user_id": receipt.user_id,
            "image_id": receipt.image_id,
            "merchant_name": receipt.merchant_name,
            "merchant_address": receipt.merchant_address,
            "purchase_date": (
                receipt.purchase_date.isoformat() if receipt.purchase_date else None
            ),
            "total_amount": str(receipt.total_amount) if receipt.total_amount else None,
            "currency": receipt.currency,
            "receipt_type": receipt.receipt_type,
            "raw_text": receipt.raw_text,
            "confidence_score": receipt.confidence_score,
            "extraction_metadata": receipt.extraction_metadata,
            "items": (
                [
                    {
                        "name": item.name,
                        "category": item.category,
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price) if item.unit_price else None,
                        "total_price": (
                            str(item.total_price) if item.total_price else None
                        ),
                        "metadata": item.metadata,
                    }
                    for item in receipt.items
                ]
                if receipt.items
                else []
            ),
            "tags": receipt.tags or [],
            "notes": receipt.notes,
            "created_at": receipt.created_at.isoformat(),
            "updated_at": receipt.updated_at.isoformat(),
            "is_deleted": receipt.is_deleted,
            "version": receipt.version,
        }

    def _from_dynamodb_item(self, item: Dict[str, Any]) -> Receipt:
        """Convert DynamoDB item to Receipt entity."""
        from domain.entities.receipt import ReceiptItem
        from decimal import Decimal

        # Convert items
        items = []
        if item.get("items"):
            for item_data in item["items"]:
                receipt_item = ReceiptItem(
                    name=item_data["name"],
                    category=item_data.get("category"),
                    quantity=item_data.get("quantity"),
                    unit_price=(
                        Decimal(item_data["unit_price"])
                        if item_data.get("unit_price")
                        else None
                    ),
                    total_price=(
                        Decimal(item_data["total_price"])
                        if item_data.get("total_price")
                        else None
                    ),
                    metadata=item_data.get("metadata", {}),
                )
                items.append(receipt_item)

        return Receipt(
            receipt_id=item["receipt_id"],
            user_id=item["user_id"],
            image_id=item["image_id"],
            merchant_name=item.get("merchant_name"),
            merchant_address=item.get("merchant_address"),
            purchase_date=(
                datetime.fromisoformat(item["purchase_date"])
                if item.get("purchase_date")
                else None
            ),
            total_amount=(
                Decimal(item["total_amount"]) if item.get("total_amount") else None
            ),
            currency=item.get("currency"),
            receipt_type=item.get("receipt_type"),
            raw_text=item.get("raw_text"),
            confidence_score=item.get("confidence_score"),
            extraction_metadata=item.get("extraction_metadata", {}),
            items=items,
            tags=item.get("tags", []),
            notes=item.get("notes"),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            is_deleted=item.get("is_deleted", False),
            version=item.get("version", 1),
        )

    async def save(self, receipt: Receipt) -> Receipt:
        """Save receipt to DynamoDB."""
        try:
            item = self._to_dynamodb_item(receipt)
            success = await self.dynamodb_service.put_item(self.table_name, item)

            if not success:
                raise DatabaseError("Failed to save receipt to database")

            logger.info(
                f"Saved receipt {receipt.receipt_id} for user {receipt.user_id}"
            )
            return receipt
        except Exception as e:
            logger.error(f"Failed to save receipt {receipt.receipt_id}: {e}")
            raise DatabaseError(f"Failed to save receipt: {e}")

    async def find_by_id(self, receipt_id: str) -> Optional[Receipt]:
        """Find receipt by ID."""
        try:
            item = await self.dynamodb_service.get_item(
                self.table_name, {"receipt_id": receipt_id}
            )

            if not item:
                return None

            return self._from_dynamodb_item(item)
        except Exception as e:
            logger.error(f"Failed to find receipt {receipt_id}: {e}")
            raise DatabaseError(f"Failed to find receipt: {e}")

    async def find_by_user_id(
        self,
        user_id: str,
        limit: Optional[int] = None,
        last_evaluated_key: Optional[Dict[str, Any]] = None,
    ) -> List[Receipt]:
        """Find receipts by user ID."""
        try:
            # Use GSI to query by user_id
            items = await self.dynamodb_service.query_items(
                table_name=self.table_name,
                index_name="user-id-index",  # Assume we have this GSI
                key_condition_expression="user_id = :user_id",
                expression_attribute_values={":user_id": user_id},
                limit=limit,
                exclusive_start_key=last_evaluated_key,
            )

            receipts = []
            for item in items:
                if not item.get("is_deleted", False):  # Filter out deleted receipts
                    receipts.append(self._from_dynamodb_item(item))

            logger.debug(f"Found {len(receipts)} receipts for user {user_id}")
            return receipts
        except Exception as e:
            logger.error(f"Failed to find receipts for user {user_id}: {e}")
            raise DatabaseError(f"Failed to find receipts: {e}")

    async def find_by_image_id(self, image_id: str) -> Optional[Receipt]:
        """Find receipt by image ID."""
        try:
            # Use GSI to query by image_id
            items = await self.dynamodb_service.query_items(
                table_name=self.table_name,
                index_name="image-id-index",  # Assume we have this GSI
                key_condition_expression="image_id = :image_id",
                expression_attribute_values={":image_id": image_id},
                limit=1,
            )

            if not items:
                return None

            return self._from_dynamodb_item(items[0])
        except Exception as e:
            logger.error(f"Failed to find receipt by image {image_id}: {e}")
            raise DatabaseError(f"Failed to find receipt: {e}")

    async def update(self, receipt: Receipt) -> Receipt:
        """Update receipt in DynamoDB."""
        try:
            # Update timestamp and version
            receipt.updated_at = datetime.now(timezone.utc)
            receipt.version += 1

            # Prepare update expression
            update_expression = """
                SET 
                    merchant_name = :merchant_name,
                    merchant_address = :merchant_address,
                    purchase_date = :purchase_date,
                    total_amount = :total_amount,
                    currency = :currency,
                    receipt_type = :receipt_type,
                    raw_text = :raw_text,
                    confidence_score = :confidence_score,
                    extraction_metadata = :extraction_metadata,
                    items = :items,
                    tags = :tags,
                    notes = :notes,
                    updated_at = :updated_at,
                    version = :version
            """.strip()

            item = self._to_dynamodb_item(receipt)
            expression_attribute_values = {
                ":merchant_name": item["merchant_name"],
                ":merchant_address": item["merchant_address"],
                ":purchase_date": item["purchase_date"],
                ":total_amount": item["total_amount"],
                ":currency": item["currency"],
                ":receipt_type": item["receipt_type"],
                ":raw_text": item["raw_text"],
                ":confidence_score": item["confidence_score"],
                ":extraction_metadata": item["extraction_metadata"],
                ":items": item["items"],
                ":tags": item["tags"],
                ":notes": item["notes"],
                ":updated_at": item["updated_at"],
                ":version": item["version"],
            }

            success = await self.dynamodb_service.update_item(
                table_name=self.table_name,
                key={"receipt_id": receipt.receipt_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )

            if not success:
                raise DatabaseError("Failed to update receipt in database")

            logger.info(f"Updated receipt {receipt.receipt_id}")
            return receipt
        except Exception as e:
            logger.error(f"Failed to update receipt {receipt.receipt_id}: {e}")
            raise DatabaseError(f"Failed to update receipt: {e}")

    async def delete(self, receipt_id: str) -> bool:
        """Soft delete receipt (mark as deleted)."""
        try:
            # Soft delete by setting is_deleted flag
            update_expression = "SET is_deleted = :is_deleted, updated_at = :updated_at"
            expression_attribute_values = {
                ":is_deleted": True,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            }

            success = await self.dynamodb_service.update_item(
                table_name=self.table_name,
                key={"receipt_id": receipt_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )

            if success:
                logger.info(f"Soft deleted receipt {receipt_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete receipt {receipt_id}: {e}")
            raise DatabaseError(f"Failed to delete receipt: {e}")

    async def hard_delete(self, receipt_id: str) -> bool:
        """Hard delete receipt from database."""
        try:
            success = await self.dynamodb_service.delete_item(
                self.table_name, {"receipt_id": receipt_id}
            )

            if success:
                logger.info(f"Hard deleted receipt {receipt_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to hard delete receipt {receipt_id}: {e}")
            raise DatabaseError(f"Failed to hard delete receipt: {e}")

    async def find_by_date_range(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> List[Receipt]:
        """Find receipts by date range."""
        try:
            # This would typically use a GSI with user_id as partition key
            # and purchase_date as sort key for efficient querying
            receipts = await self.find_by_user_id(user_id)

            # Filter by date range in memory (not ideal for large datasets)
            filtered_receipts = []
            for receipt in receipts:
                if (
                    receipt.purchase_date
                    and start_date <= receipt.purchase_date <= end_date
                ):
                    filtered_receipts.append(receipt)

            logger.debug(
                f"Found {len(filtered_receipts)} receipts for user {user_id} in date range"
            )
            return filtered_receipts
        except Exception as e:
            logger.error(f"Failed to find receipts by date range: {e}")
            raise DatabaseError(f"Failed to find receipts by date range: {e}")

    async def find_by_merchant(self, user_id: str, merchant_name: str) -> List[Receipt]:
        """Find receipts by merchant name."""
        try:
            receipts = await self.find_by_user_id(user_id)

            # Filter by merchant name in memory
            filtered_receipts = []
            for receipt in receipts:
                if (
                    receipt.merchant_name
                    and merchant_name.lower() in receipt.merchant_name.lower()
                ):
                    filtered_receipts.append(receipt)

            logger.debug(
                f"Found {len(filtered_receipts)} receipts for merchant {merchant_name}"
            )
            return filtered_receipts
        except Exception as e:
            logger.error(f"Failed to find receipts by merchant: {e}")
            raise DatabaseError(f"Failed to find receipts by merchant: {e}")

    async def count_by_user_id(self, user_id: str) -> int:
        """Count receipts for a user."""
        try:
            # Use count query for efficiency
            response = await self.dynamodb_service.query_items(
                table_name=self.table_name,
                index_name="user-id-index",
                key_condition_expression="user_id = :user_id",
                expression_attribute_values={":user_id": user_id},
                select="COUNT",
            )

            return response.get("Count", 0)
        except Exception as e:
            logger.error(f"Failed to count receipts for user {user_id}: {e}")
            raise DatabaseError(f"Failed to count receipts: {e}")

    async def batch_save(self, receipts: List[Receipt]) -> List[Receipt]:
        """Save multiple receipts in batch."""
        try:
            items = [self._to_dynamodb_item(receipt) for receipt in receipts]

            success_count = await self.dynamodb_service.batch_write_items(
                self.table_name, items
            )

            if success_count != len(receipts):
                logger.warning(
                    f"Only {success_count}/{len(receipts)} receipts saved in batch"
                )

            logger.info(f"Batch saved {success_count} receipts")
            return receipts[:success_count]
        except Exception as e:
            logger.error(f"Failed to batch save receipts: {e}")
            raise DatabaseError(f"Failed to batch save receipts: {e}")

    # Interface compatibility methods
    async def get_by_id(self, receipt_id: str) -> Optional[Receipt]:
        """Get a receipt by its ID - interface compatibility."""
        return await self.find_by_id(receipt_id)

    async def get_by_user_id(
        self,
        user_id: str,
        limit: Optional[int] = None,
        last_evaluated_key: Optional[str] = None,
    ) -> List[Receipt]:
        """Get all receipts for a specific user - interface compatibility."""
        return await self.find_by_user_id(user_id, limit, last_evaluated_key)

    async def bulk_delete(self, receipt_ids: List[str]) -> int:
        """Delete multiple receipts by their IDs. Returns count of deleted receipts."""
        # Placeholder implementation
        count = 0
        for receipt_id in receipt_ids:
            if await self.delete(receipt_id):
                count += 1
        return count

    async def get_inactive_receipts(
        self, days_threshold: int = 30, limit: Optional[int] = None
    ) -> List[Receipt]:
        """Get receipts from inactive free users older than threshold days."""
        # Placeholder implementation
        return []

    async def get_by_processing_status(
        self, status: str, limit: Optional[int] = None
    ) -> List[Receipt]:
        """Get receipts by processing status."""
        # Placeholder implementation
        return []
