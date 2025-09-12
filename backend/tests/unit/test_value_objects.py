"""Unit tests for domain value objects."""

import pytest
from decimal import Decimal
import uuid

from src.domain.value_objects import UserId, ReceiptId, Money


class TestUserId:
    """Test cases for UserId value object."""

    def test_user_id_creation(self):
        """Test creating a valid UserId."""
        user_id_str = str(uuid.uuid4())
        user_id = UserId(user_id_str)

        assert user_id.value == user_id_str
        assert str(user_id) == user_id_str

    def test_user_id_generate(self):
        """Test generating a new UserId."""
        user_id = UserId.generate()

        assert isinstance(user_id.value, str)
        assert len(user_id.value) == 36  # UUID length

    def test_user_id_empty_validation(self):
        """Test UserId validation with empty value."""
        with pytest.raises(ValueError, match="UserId cannot be empty"):
            UserId("")

    def test_user_id_none_validation(self):
        """Test UserId validation with None value."""
        with pytest.raises(ValueError, match="UserId cannot be empty"):
            UserId(None)

    def test_user_id_type_validation(self):
        """Test UserId validation with wrong type."""
        with pytest.raises(ValueError, match="UserId must be a string"):
            UserId(123)

    def test_user_id_equality(self):
        """Test UserId equality comparison."""
        user_id_str = str(uuid.uuid4())
        user_id1 = UserId(user_id_str)
        user_id2 = UserId(user_id_str)
        user_id3 = UserId(str(uuid.uuid4()))

        assert user_id1 == user_id1  # Same instance
        assert user_id1 == user_id2  # Same value
        assert user_id1 != user_id3  # Different value


class TestReceiptId:
    """Test cases for ReceiptId value object."""

    def test_receipt_id_creation(self):
        """Test creating a valid ReceiptId."""
        receipt_id_str = str(uuid.uuid4())
        receipt_id = ReceiptId(receipt_id_str)

        assert receipt_id.value == receipt_id_str
        assert str(receipt_id) == receipt_id_str

    def test_receipt_id_generate(self):
        """Test generating a new ReceiptId."""
        receipt_id = ReceiptId.generate()

        assert isinstance(receipt_id.value, str)
        assert len(receipt_id.value) == 36  # UUID length

    def test_receipt_id_validation(self):
        """Test ReceiptId validation."""
        with pytest.raises(ValueError, match="ReceiptId cannot be empty"):
            ReceiptId("")

        with pytest.raises(ValueError, match="ReceiptId must be a string"):
            ReceiptId(123)


class TestMoney:
    """Test cases for Money value object."""

    def test_money_creation(self):
        """Test creating a valid Money object."""
        money = Money(Decimal("10.50"), "USD")

        assert money.amount == Decimal("10.50")
        assert money.currency == "USD"

    def test_money_default_currency(self):
        """Test Money with default currency."""
        money = Money(Decimal("20.00"))

        assert money.amount == Decimal("20.00")
        assert money.currency == "USD"

    def test_money_string_amount_conversion(self):
        """Test Money with string amount."""
        money = Money("15.75", "EUR")

        assert money.amount == Decimal("15.75")
        assert money.currency == "EUR"

    def test_money_int_amount_conversion(self):
        """Test Money with integer amount."""
        money = Money(25, "GBP")

        assert money.amount == Decimal("25")
        assert money.currency == "GBP"

    def test_money_float_amount_conversion(self):
        """Test Money with float amount."""
        money = Money(12.99, "CAD")

        assert money.amount == Decimal("12.99")
        assert money.currency == "CAD"

    def test_money_negative_amount_validation(self):
        """Test Money validation with negative amount."""
        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money(Decimal("-10.00"))

    def test_money_empty_currency_validation(self):
        """Test Money validation with empty currency."""
        with pytest.raises(ValueError, match="Currency cannot be empty"):
            Money(Decimal("10.00"), "")

    def test_money_invalid_currency_length_validation(self):
        """Test Money validation with invalid currency length."""
        with pytest.raises(ValueError, match="Currency must be a 3-letter code"):
            Money(Decimal("10.00"), "USDD")

        with pytest.raises(ValueError, match="Currency must be a 3-letter code"):
            Money(Decimal("10.00"), "US")

    def test_money_string_representation(self):
        """Test Money string representation."""
        money = Money(Decimal("10.50"), "USD")

        assert str(money) == "10.50 USD"

    def test_money_addition(self):
        """Test Money addition."""
        money1 = Money(Decimal("10.50"), "USD")
        money2 = Money(Decimal("5.25"), "USD")
        result = money1 + money2

        assert result.amount == Decimal("15.75")
        assert result.currency == "USD"

    def test_money_addition_different_currencies(self):
        """Test Money addition with different currencies."""
        money1 = Money(Decimal("10.50"), "USD")
        money2 = Money(Decimal("5.25"), "EUR")

        with pytest.raises(
            ValueError, match="Cannot add money with different currencies"
        ):
            money1 + money2

    def test_money_subtraction(self):
        """Test Money subtraction."""
        money1 = Money(Decimal("10.50"), "USD")
        money2 = Money(Decimal("5.25"), "USD")
        result = money1 - money2

        assert result.amount == Decimal("5.25")
        assert result.currency == "USD"

    def test_money_subtraction_different_currencies(self):
        """Test Money subtraction with different currencies."""
        money1 = Money(Decimal("10.50"), "USD")
        money2 = Money(Decimal("5.25"), "EUR")

        with pytest.raises(
            ValueError, match="Cannot subtract money with different currencies"
        ):
            money1 - money2

    def test_money_multiplication(self):
        """Test Money multiplication."""
        money = Money(Decimal("10.50"), "USD")
        result = money * 2

        assert result.amount == Decimal("21.00")
        assert result.currency == "USD"

    def test_money_multiplication_float(self):
        """Test Money multiplication with float."""
        money = Money(Decimal("10.00"), "USD")
        result = money * 1.5

        assert result.amount == Decimal("15.0")
        assert result.currency == "USD"

    def test_money_equality(self):
        """Test Money equality."""
        money1 = Money(Decimal("10.50"), "USD")
        money2 = Money(Decimal("10.50"), "USD")
        money3 = Money(Decimal("10.50"), "EUR")
        money4 = Money(Decimal("15.00"), "USD")

        assert money1 == money2
        assert money1 != money3  # Different currency
        assert money1 != money4  # Different amount
        assert money1 != "not money"  # Different type

    def test_money_comparison(self):
        """Test Money comparison operators."""
        money1 = Money(Decimal("10.50"), "USD")
        money2 = Money(Decimal("15.00"), "USD")
        money3 = Money(Decimal("10.50"), "EUR")

        assert money1 < money2
        assert money2 > money1
        assert money1 <= money2
        assert money2 >= money1
        assert money1 <= Money(Decimal("10.50"), "USD")
        assert money1 >= Money(Decimal("10.50"), "USD")

        # Different currencies should raise error
        with pytest.raises(
            ValueError, match="Cannot compare money with different currencies"
        ):
            money1 < money3

        with pytest.raises(
            ValueError, match="Cannot compare money with different currencies"
        ):
            money1 <= money3

        with pytest.raises(
            ValueError, match="Cannot compare money with different currencies"
        ):
            money1 > money3

        with pytest.raises(
            ValueError, match="Cannot compare money with different currencies"
        ):
            money1 >= money3
