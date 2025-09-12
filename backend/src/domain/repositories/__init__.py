"""Repository interfaces for the receipt search application."""

from .receipt_repository import ReceiptRepository
from .user_repository import UserRepository
from .search_repository import SearchRepository

__all__ = ["ReceiptRepository", "UserRepository", "SearchRepository"]
