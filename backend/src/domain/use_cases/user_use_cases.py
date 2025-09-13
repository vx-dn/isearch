"""User use cases implementation."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from src.domain.entities.user import User
from src.domain.exceptions import UserNotFoundError, ValidationError
from src.domain.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class CreateUserUseCase:
    """Use case for creating a new user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_data: dict[str, Any]) -> User:
        """Execute create user use case."""
        try:
            # Generate user ID
            user_id = str(uuid.uuid4())

            # Create user entity
            from src.domain.entities.enums import UserRole

            role = UserRole(user_data.get("role", "free"))

            user = User(
                user_id=user_id,
                email=user_data["email"],
                role=role,
                image_count=user_data.get("image_count", 0),
                image_quota=user_data.get("image_quota", role.image_quota),
                last_active_date=datetime.now(timezone.utc),
            )

            # Save to repository
            saved_user = await self.user_repository.save(user)
            logger.info(f"Created user {user_id} with email {user.email}")
            return saved_user

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise ValidationError(f"Failed to create user: {e}")


class GetUserUseCase:
    """Use case for retrieving a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str) -> User:
        """Execute get user use case."""
        try:
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            return user

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise ValidationError(f"Failed to get user: {e}")


class UpdateUserUseCase:
    """Use case for updating a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, update_data: dict[str, Any]) -> User:
        """Execute update user use case."""
        try:
            # Get existing user
            user = await self.user_repository.find_by_id(user_id)
            if not user or not user.is_active:
                raise UserNotFoundError(f"User {user_id} not found")

            # Update fields
            if "username" in update_data:
                user.username = update_data["username"]
            if "display_name" in update_data:
                user.display_name = update_data["display_name"]
            if "preferences" in update_data:
                user.preferences = update_data["preferences"]
            if "subscription_tier" in update_data:
                user.subscription_tier = update_data["subscription_tier"]

            # Save updated user
            updated_user = await self.user_repository.update(user)
            logger.info(f"Updated user {user_id}")
            return updated_user

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise ValidationError(f"Failed to update user: {e}")


class DeleteUserUseCase:
    """Use case for deleting a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str) -> bool:
        """Execute delete user use case."""
        try:
            # Check if user exists
            user = await self.user_repository.find_by_id(user_id)
            if not user or not user.is_active:
                raise UserNotFoundError(f"User {user_id} not found")

            # Soft delete
            success = await self.user_repository.delete(user_id)
            if success:
                logger.info(f"Deleted user {user_id}")
            return success

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise ValidationError(f"Failed to delete user: {e}")


class AuthenticateUserUseCase:
    """Use case for authenticating a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, email: str) -> User:
        """Execute authenticate user use case."""
        try:
            user = await self.user_repository.find_by_email(email)
            if not user:
                raise UserNotFoundError("Invalid credentials")

            if not user.is_active:
                raise UserNotFoundError("User account is deactivated")

            return user

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to authenticate user {email}: {e}")
            raise ValidationError(f"Authentication failed: {e}")
