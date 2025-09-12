"""Receipt entity implementation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from decimal import Decimal


@dataclass
class ReceiptItem:
    """Individual item on a receipt."""

    name: str
    category: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Receipt:
    """Receipt entity representing a user's receipt."""

    receipt_id: str
    user_id: str
    image_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_address: Optional[str] = None
    purchase_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    receipt_type: Optional[str] = None
    raw_text: Optional[str] = None
    confidence_score: Optional[float] = None
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    items: Optional[List[ReceiptItem]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary for serialization."""
        return {
            "receipt_id": self.receipt_id,
            "user_id": self.user_id,
            "image_id": self.image_id,
            "merchant_name": self.merchant_name,
            "merchant_address": self.merchant_address,
            "purchase_date": (
                self.purchase_date.isoformat() if self.purchase_date else None
            ),
            "total_amount": str(self.total_amount) if self.total_amount else None,
            "currency": self.currency,
            "receipt_type": self.receipt_type,
            "raw_text": self.raw_text,
            "confidence_score": self.confidence_score,
            "extraction_metadata": self.extraction_metadata,
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
                    for item in self.items
                ]
                if self.items
                else []
            ),
            "tags": self.tags or [],
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_deleted": self.is_deleted,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Receipt":
        """Create receipt from dictionary."""
        # Convert items
        items = []
        if data.get("items"):
            for item_data in data["items"]:
                item = ReceiptItem(
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
                items.append(item)

        return cls(
            receipt_id=data["receipt_id"],
            user_id=data["user_id"],
            image_id=data.get("image_id"),
            merchant_name=data.get("merchant_name"),
            merchant_address=data.get("merchant_address"),
            purchase_date=(
                datetime.fromisoformat(data["purchase_date"])
                if data.get("purchase_date")
                else None
            ),
            total_amount=(
                Decimal(data["total_amount"]) if data.get("total_amount") else None
            ),
            currency=data.get("currency"),
            receipt_type=data.get("receipt_type"),
            raw_text=data.get("raw_text"),
            confidence_score=data.get("confidence_score"),
            extraction_metadata=data.get("extraction_metadata", {}),
            items=items if items else None,
            tags=data.get("tags", []),
            notes=data.get("notes"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            is_deleted=data.get("is_deleted", False),
            version=data.get("version", 1),
        )
