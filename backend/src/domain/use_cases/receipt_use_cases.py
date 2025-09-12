"""Receipt use cases implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from src.domain.entities.receipt import Receipt, ReceiptItem
from src.domain.repositories.receipt_repository import ReceiptRepository
from src.domain.exceptions import ValidationError, ReceiptNotFoundError
from decimal import Decimal

logger = logging.getLogger(__name__)


class CreateReceiptUseCase:
    """Use case for creating a new receipt."""

    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository

    async def execute(self, receipt_data: Dict[str, Any]) -> Receipt:
        """Execute create receipt use case."""
        try:
            # Generate receipt ID
            receipt_id = str(uuid.uuid4())

            # Process items
            items = []
            if receipt_data.get("items"):
                for item_data in receipt_data["items"]:
                    item = ReceiptItem(
                        name=item_data["name"],
                        category=item_data.get("category"),
                        quantity=item_data.get("quantity"),
                        unit_price=item_data.get("unit_price"),
                        total_price=item_data.get("total_price"),
                        metadata=item_data.get("metadata", {}),
                    )
                    items.append(item)

            # Create receipt entity
            receipt = Receipt(
                receipt_id=receipt_id,
                user_id=receipt_data["user_id"],
                image_id=receipt_data.get("image_id"),
                merchant_name=receipt_data.get("merchant_name"),
                merchant_address=receipt_data.get("merchant_address"),
                purchase_date=receipt_data.get("purchase_date"),
                total_amount=receipt_data.get("total_amount"),
                currency=receipt_data.get("currency"),
                receipt_type=receipt_data.get("receipt_type"),
                raw_text=receipt_data.get("raw_text"),
                confidence_score=receipt_data.get("confidence_score"),
                extraction_metadata=receipt_data.get("extraction_metadata", {}),
                items=items,
                tags=receipt_data.get("tags", []),
                notes=receipt_data.get("notes"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # Save to repository
            saved_receipt = await self.receipt_repository.save(receipt)
            logger.info(f"Created receipt {receipt_id}")
            return saved_receipt

        except Exception as e:
            logger.error(f"Failed to create receipt: {e}")
            raise ValidationError(f"Failed to create receipt: {e}")


class GetReceiptUseCase:
    """Use case for retrieving a receipt."""

    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository

    async def execute(self, receipt_id: str) -> Receipt:
        """Execute get receipt use case."""
        try:
            receipt = await self.receipt_repository.find_by_id(receipt_id)
            if not receipt:
                raise ReceiptNotFoundError(f"Receipt {receipt_id} not found")

            if receipt.is_deleted:
                raise ReceiptNotFoundError(f"Receipt {receipt_id} not found")

            return receipt

        except ReceiptNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get receipt {receipt_id}: {e}")
            raise ValidationError(f"Failed to get receipt: {e}")


class UpdateReceiptUseCase:
    """Use case for updating a receipt."""

    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository

    async def execute(self, receipt_id: str, update_data: Dict[str, Any]) -> Receipt:
        """Execute update receipt use case."""
        try:
            # Get existing receipt
            receipt = await self.receipt_repository.find_by_id(receipt_id)
            if not receipt or receipt.is_deleted:
                raise ReceiptNotFoundError(f"Receipt {receipt_id} not found")

            # Update fields
            if "merchant_name" in update_data:
                receipt.merchant_name = update_data["merchant_name"]
            if "merchant_address" in update_data:
                receipt.merchant_address = update_data["merchant_address"]
            if "purchase_date" in update_data:
                receipt.purchase_date = update_data["purchase_date"]
            if "total_amount" in update_data:
                receipt.total_amount = update_data["total_amount"]
            if "currency" in update_data:
                receipt.currency = update_data["currency"]
            if "receipt_type" in update_data:
                receipt.receipt_type = update_data["receipt_type"]
            if "tags" in update_data:
                receipt.tags = update_data["tags"]
            if "notes" in update_data:
                receipt.notes = update_data["notes"]

            # Update items if provided
            if "items" in update_data:
                items = []
                for item_data in update_data["items"]:
                    item = ReceiptItem(
                        name=item_data["name"],
                        category=item_data.get("category"),
                        quantity=item_data.get("quantity"),
                        unit_price=item_data.get("unit_price"),
                        total_price=item_data.get("total_price"),
                        metadata=item_data.get("metadata", {}),
                    )
                    items.append(item)
                receipt.items = items

            # Save updated receipt
            updated_receipt = await self.receipt_repository.update(receipt)
            logger.info(f"Updated receipt {receipt_id}")
            return updated_receipt

        except ReceiptNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update receipt {receipt_id}: {e}")
            raise ValidationError(f"Failed to update receipt: {e}")


class DeleteReceiptUseCase:
    """Use case for deleting a receipt."""

    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository

    async def execute(self, receipt_id: str) -> bool:
        """Execute delete receipt use case."""
        try:
            # Check if receipt exists
            receipt = await self.receipt_repository.find_by_id(receipt_id)
            if not receipt or receipt.is_deleted:
                raise ReceiptNotFoundError(f"Receipt {receipt_id} not found")

            # Soft delete
            success = await self.receipt_repository.delete(receipt_id)
            if success:
                logger.info(f"Deleted receipt {receipt_id}")
            return success

        except ReceiptNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete receipt {receipt_id}: {e}")
            raise ValidationError(f"Failed to delete receipt: {e}")


class ProcessReceiptImageUseCase:
    """Use case for processing receipt images and extracting data."""

    def __init__(
        self, receipt_repository: ReceiptRepository, s3_service, textract_service
    ):
        self.receipt_repository = receipt_repository
        self.s3_service = s3_service
        self.textract_service = textract_service

    async def execute(self, image_data: Dict[str, Any]) -> Receipt:
        """Execute process receipt image use case."""
        try:
            user_id = image_data["user_id"]
            image_id = image_data["image_id"]
            object_key = image_data["object_key"]

            logger.info(f"Processing receipt image {image_id} for user {user_id}")

            # Extract text from image using Textract
            extraction_result = await self.textract_service.extract_expense_data(
                bucket_name=self.s3_service.bucket_name, object_key=object_key
            )

            # Parse extraction results
            extracted_data = self._parse_textract_results(extraction_result)

            # Create receipt from extracted data
            receipt_data = {
                "user_id": user_id,
                "image_id": image_id,
                "merchant_name": extracted_data.get("merchant_name"),
                "merchant_address": extracted_data.get("merchant_address"),
                "purchase_date": extracted_data.get("purchase_date"),
                "total_amount": extracted_data.get("total_amount"),
                "currency": extracted_data.get("currency", "USD"),
                "receipt_type": "other",  # Default type
                "raw_text": extracted_data.get("raw_text"),
                "confidence_score": extracted_data.get("confidence_score"),
                "extraction_metadata": {
                    "textract_job_id": extraction_result.get("job_id"),
                    "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                    "extraction_method": "aws_textract",
                },
                "items": extracted_data.get("items", []),
                "tags": [],
                "notes": f"Automatically extracted from image {image_id}",
            }

            # Create receipt using the create use case
            create_use_case = CreateReceiptUseCase(self.receipt_repository)
            receipt = await create_use_case.execute(receipt_data)

            logger.info(f"Successfully processed receipt image {image_id}")
            return receipt

        except Exception as e:
            logger.error(f"Failed to process receipt image: {e}")
            raise ValidationError(f"Failed to process receipt image: {e}")

    def _parse_textract_results(
        self, textract_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse Textract results and extract structured data."""
        extracted_data = {
            "raw_text": "",
            "confidence_score": 0.0,
            "merchant_name": None,
            "merchant_address": None,
            "purchase_date": None,
            "total_amount": None,
            "currency": "USD",
            "items": [],
        }

        try:
            # Extract expense summary if available
            expense_summary = textract_result.get("expense_summary", {})

            if expense_summary:
                # Extract structured data from Textract expense analysis
                extracted_data["merchant_name"] = expense_summary.get("vendor_name")
                extracted_data["total_amount"] = expense_summary.get("total_amount")

                # Parse date
                date_str = expense_summary.get("invoice_date")
                if date_str:
                    try:
                        from dateutil import parser

                        extracted_data["purchase_date"] = parser.parse(date_str)
                    except:
                        pass

                # Extract line items
                line_items = expense_summary.get("line_items", [])
                for item in line_items:
                    receipt_item = {
                        "name": item.get("description", "Unknown Item"),
                        "category": None,
                        "quantity": item.get("quantity", 1),
                        "unit_price": item.get("unit_price"),
                        "total_price": item.get("total_price"),
                        "metadata": {"confidence": item.get("confidence", 0.0)},
                    }
                    extracted_data["items"].append(receipt_item)

            # Extract raw text
            extracted_data["raw_text"] = textract_result.get("raw_text", "")

            # Calculate average confidence
            confidences = []
            if "blocks" in textract_result:
                for block in textract_result["blocks"]:
                    if "confidence" in block:
                        confidences.append(block["confidence"])

            if confidences:
                extracted_data["confidence_score"] = (
                    sum(confidences) / len(confidences) / 100.0
                )

            return extracted_data

        except Exception as e:
            logger.warning(f"Error parsing Textract results: {e}")
            return extracted_data
