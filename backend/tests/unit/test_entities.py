"""Unit tests for domain entities."""

from datetime import datetime, timezone
from decimal import Decimal
import uuid

from src.domain.entities.user import User
from src.domain.entities.receipt import Receipt, ReceiptItem


class TestUser:
    """Test cases for User entity."""

    def test_user_creation(self):
        """Test creating a valid user."""
        from src.domain.entities.enums import UserRole

        user = User(
            user_id=str(uuid.uuid4()),
            email="test@example.com",
            role=UserRole.FREE,
            image_count=0,
            image_quota=100,
            last_active_date=datetime.now(timezone.utc),
        )

        assert user.email == "test@example.com"
        assert user.role == UserRole.FREE
        assert user.image_count == 0
        assert user.image_quota == 100
        assert user.last_active_date is not None
        assert user.is_admin() is False

    def test_user_to_dict(self, sample_user):
        """Test user serialization to dictionary."""
        user_dict = sample_user.to_dict()

        assert isinstance(user_dict, dict)
        assert user_dict["user_id"] == sample_user.user_id
        assert user_dict["email"] == sample_user.email
        assert user_dict["role"] == sample_user.role.value
        assert user_dict["image_count"] == sample_user.image_count
        assert user_dict["image_quota"] == sample_user.image_quota
        assert "last_active_date" in user_dict

    def test_user_from_dict(self, sample_user):
        """Test user creation from dictionary."""
        user_dict = sample_user.to_dict()
        recreated_user = User.from_dict(user_dict)

        assert recreated_user.user_id == sample_user.user_id
        assert recreated_user.email == sample_user.email
        assert recreated_user.role == sample_user.role
        assert recreated_user.image_count == sample_user.image_count
        assert recreated_user.image_quota == sample_user.image_quota

    def test_user_can_upload_receipt(self, sample_user):
        """Test user upload permissions."""
        # Free user with no images should be able to upload
        assert sample_user.can_upload() is True
        assert sample_user.can_upload(5) is True  # Can upload 5 images

        # Test with image count at limit
        sample_user.image_count = sample_user.image_quota
        assert sample_user.can_upload() is False  # At quota limit

        # Test available quota
        sample_user.image_count = 10
        assert sample_user.get_available_quota() == sample_user.image_quota - 10

    def test_user_update_last_active(self, sample_user):
        """Test updating user's last active timestamp."""
        original_time = sample_user.last_active_date
        sample_user.update_last_active()

        # Should update the timestamp
        assert sample_user.last_active_date != original_time


class TestReceiptItem:
    """Test cases for ReceiptItem entity."""

    def test_receipt_item_creation(self):
        """Test creating a valid receipt item."""
        item = ReceiptItem(
            name="Coffee",
            category="Beverages",
            quantity=2,
            unit_price=Decimal("4.50"),
            total_price=Decimal("9.00"),
        )

        assert item.name == "Coffee"
        assert item.category == "Beverages"
        assert item.quantity == 2
        assert item.unit_price == Decimal("4.50")
        assert item.total_price == Decimal("9.00")

    def test_receipt_item_minimal(self):
        """Test creating a receipt item with minimal data."""
        item = ReceiptItem(name="Unknown Item")

        assert item.name == "Unknown Item"
        assert item.category is None
        assert item.quantity is None
        assert item.unit_price is None
        assert item.total_price is None
        assert item.metadata == {}


class TestReceipt:
    """Test cases for Receipt entity."""

    def test_receipt_creation(self, sample_receipt):
        """Test creating a valid receipt."""
        assert sample_receipt.merchant_name == "Coffee Shop"
        assert sample_receipt.total_amount == Decimal("4.50")
        assert sample_receipt.currency == "USD"
        assert len(sample_receipt.items) == 1
        assert len(sample_receipt.tags) == 2

    def test_receipt_to_dict(self, sample_receipt):
        """Test receipt serialization to dictionary."""
        receipt_dict = sample_receipt.to_dict()

        assert isinstance(receipt_dict, dict)
        assert receipt_dict["receipt_id"] == sample_receipt.receipt_id
        assert receipt_dict["merchant_name"] == sample_receipt.merchant_name
        assert receipt_dict["total_amount"] == str(sample_receipt.total_amount)
        assert isinstance(receipt_dict["items"], list)
        assert len(receipt_dict["items"]) == 1
        assert receipt_dict["items"][0]["name"] == "Coffee"

    def test_receipt_from_dict(self, sample_receipt):
        """Test receipt creation from dictionary."""
        receipt_dict = sample_receipt.to_dict()
        recreated_receipt = Receipt.from_dict(receipt_dict)

        assert recreated_receipt.receipt_id == sample_receipt.receipt_id
        assert recreated_receipt.merchant_name == sample_receipt.merchant_name
        assert recreated_receipt.total_amount == sample_receipt.total_amount
        assert len(recreated_receipt.items) == len(sample_receipt.items)
        assert recreated_receipt.items[0].name == sample_receipt.items[0].name

    def test_receipt_with_no_items(self):
        """Test receipt without items."""
        receipt = Receipt(
            receipt_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            merchant_name="Test Store",
            total_amount=Decimal("10.00"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert receipt.items is None

        receipt_dict = receipt.to_dict()
        assert receipt_dict["items"] == []

    def test_receipt_currency_validation(self):
        """Test receipt with different currencies."""
        receipt = Receipt(
            receipt_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            merchant_name="Test Store",
            total_amount=Decimal("10.00"),
            currency="EUR",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert receipt.currency == "EUR"

    def test_receipt_tags_management(self, sample_receipt):
        """Test receipt tags functionality."""
        # Test initial tags
        assert "coffee" in sample_receipt.tags
        assert "food" in sample_receipt.tags

        # Test adding unique tags only
        if sample_receipt.tags is None:
            sample_receipt.tags = []

        original_length = len(sample_receipt.tags)
        sample_receipt.tags.append("new_tag")
        assert len(sample_receipt.tags) == original_length + 1
