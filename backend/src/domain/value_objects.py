"""Domain value objects."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
import uuid


@dataclass(frozen=True)
class UserId:
    """User identifier value object."""

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("UserId cannot be empty")
        if not isinstance(self.value, str):
            raise ValueError("UserId must be a string")

    @classmethod
    def generate(cls) -> "UserId":
        """Generate a new unique user ID."""
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ReceiptId:
    """Receipt identifier value object."""

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("ReceiptId cannot be empty")
        if not isinstance(self.value, str):
            raise ValueError("ReceiptId must be a string")

    @classmethod
    def generate(cls) -> "ReceiptId":
        """Generate a new unique receipt ID."""
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money:
    """Money value object."""

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency cannot be empty")
        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code")

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money with different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, multiplier: float) -> "Money":
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")
        return self.amount >= other.amount
