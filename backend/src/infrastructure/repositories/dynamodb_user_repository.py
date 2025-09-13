"""DynamoDB implementation of user repository."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService
from src.domain.exceptions import DatabaseError
from src.domain.config import DOMAIN_CONFIG

logger = logging.getLogger(__name__)


class DynamoDBUserRepository(UserRepository):
    """DynamoDB implementation of user repository."""

    def __init__(self, dynamodb_service: DynamoDBService):
        """Initialize repository with DynamoDB service."""
        self.dynamodb_service = dynamodb_service
        self.table_name = DOMAIN_CONFIG.USER_TABLE_NAME

    def _to_dynamodb_item(self, user: User) -> Dict[str, Any]:
        """Convert User entity to DynamoDB item."""
        return {
            "user_id": user.user_id,
            "cognito_user_id": user.cognito_user_id,
            "email": user.email,
            "username": user.username,
            "display_name": user.display_name,
            "preferences": user.preferences or {},
            "subscription_tier": user.subscription_tier,
            "receipt_count": user.receipt_count,
            "storage_used_bytes": user.storage_used_bytes,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "is_active": user.is_active,
            "version": user.version,
        }

    def _from_dynamodb_item(self, item: Dict[str, Any]) -> User:
        """Convert DynamoDB item to User entity."""
        return User(
            user_id=item["user_id"],
            cognito_user_id=item["cognito_user_id"],
            email=item["email"],
            username=item.get("username"),
            display_name=item.get("display_name"),
            preferences=item.get("preferences", {}),
            subscription_tier=item.get("subscription_tier", "free"),
            receipt_count=item.get("receipt_count", 0),
            storage_used_bytes=item.get("storage_used_bytes", 0),
            last_login=(
                datetime.fromisoformat(item["last_login"])
                if item.get("last_login")
                else None
            ),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            is_active=item.get("is_active", True),
            version=item.get("version", 1),
        )

    async def save(self, user: User) -> User:
        """Save user to DynamoDB."""
        try:
            item = self._to_dynamodb_item(user)
            success = await self.dynamodb_service.put_item(self.table_name, item)

            if not success:
                raise DatabaseError("Failed to save user to database")

            logger.info(f"Saved user {user.user_id} ({user.email})")
            return user
        except Exception as e:
            logger.error(f"Failed to save user {user.user_id}: {e}")
            raise DatabaseError(f"Failed to save user: {e}")

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID."""
        try:
            item = await self.dynamodb_service.get_item(
                self.table_name, {"user_id": user_id}
            )

            if not item:
                return None

            return self._from_dynamodb_item(item)
        except Exception as e:
            logger.error(f"Failed to find user {user_id}: {e}")
            raise DatabaseError(f"Failed to find user: {e}")

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        try:
            # Use GSI to query by email
            items = await self.dynamodb_service.query_items(
                table_name=self.table_name,
                index_name="email-index",  # Assume we have this GSI
                key_condition_expression="email = :email",
                expression_attribute_values={":email": email},
                limit=1,
            )

            if not items:
                return None

            return self._from_dynamodb_item(items[0])
        except Exception as e:
            logger.error(f"Failed to find user by email {email}: {e}")
            raise DatabaseError(f"Failed to find user by email: {e}")

    async def find_by_cognito_user_id(self, cognito_user_id: str) -> Optional[User]:
        """Find user by Cognito user ID."""
        try:
            # Use GSI to query by cognito_user_id
            items = await self.dynamodb_service.query_items(
                table_name=self.table_name,
                index_name="cognito-user-id-index",  # Assume we have this GSI
                key_condition_expression="cognito_user_id = :cognito_user_id",
                expression_attribute_values={":cognito_user_id": cognito_user_id},
                limit=1,
            )

            if not items:
                return None

            return self._from_dynamodb_item(items[0])
        except Exception as e:
            logger.error(f"Failed to find user by Cognito ID {cognito_user_id}: {e}")
            raise DatabaseError(f"Failed to find user by Cognito ID: {e}")

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        try:
            # Use GSI to query by username
            items = await self.dynamodb_service.query_items(
                table_name=self.table_name,
                index_name="username-index",  # Assume we have this GSI
                key_condition_expression="username = :username",
                expression_attribute_values={":username": username},
                limit=1,
            )

            if not items:
                return None

            return self._from_dynamodb_item(items[0])
        except Exception as e:
            logger.error(f"Failed to find user by username {username}: {e}")
            raise DatabaseError(f"Failed to find user by username: {e}")

    async def update(self, user: User) -> User:
        """Update user in DynamoDB."""
        try:
            # Update timestamp and version
            user.updated_at = datetime.now(timezone.utc)
            user.version += 1

            # Prepare update expression
            update_expression = """
                SET 
                    email = :email,
                    username = :username,
                    display_name = :display_name,
                    preferences = :preferences,
                    subscription_tier = :subscription_tier,
                    receipt_count = :receipt_count,
                    storage_used_bytes = :storage_used_bytes,
                    last_login = :last_login,
                    updated_at = :updated_at,
                    is_active = :is_active,
                    version = :version
            """.strip()

            item = self._to_dynamodb_item(user)
            expression_attribute_values = {
                ":email": item["email"],
                ":username": item["username"],
                ":display_name": item["display_name"],
                ":preferences": item["preferences"],
                ":subscription_tier": item["subscription_tier"],
                ":receipt_count": item["receipt_count"],
                ":storage_used_bytes": item["storage_used_bytes"],
                ":last_login": item["last_login"],
                ":updated_at": item["updated_at"],
                ":is_active": item["is_active"],
                ":version": item["version"],
            }

            success = await self.dynamodb_service.update_item(
                table_name=self.table_name,
                key={"user_id": user.user_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )

            if not success:
                raise DatabaseError("Failed to update user in database")

            logger.info(f"Updated user {user.user_id}")
            return user
        except Exception as e:
            logger.error(f"Failed to update user {user.user_id}: {e}")
            raise DatabaseError(f"Failed to update user: {e}")

    async def delete(self, user_id: str) -> bool:
        """Soft delete user (deactivate)."""
        try:
            # Soft delete by setting is_active flag
            update_expression = "SET is_active = :is_active, updated_at = :updated_at"
            expression_attribute_values = {
                ":is_active": False,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            }

            success = await self.dynamodb_service.update_item(
                table_name=self.table_name,
                key={"user_id": user_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )

            if success:
                logger.info(f"Deactivated user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise DatabaseError(f"Failed to deactivate user: {e}")

    async def hard_delete(self, user_id: str) -> bool:
        """Hard delete user from database."""
        try:
            success = await self.dynamodb_service.delete_item(
                self.table_name, {"user_id": user_id}
            )

            if success:
                logger.info(f"Hard deleted user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to hard delete user {user_id}: {e}")
            raise DatabaseError(f"Failed to hard delete user: {e}")

    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            update_expression = "SET last_login = :last_login, updated_at = :updated_at"
            expression_attribute_values = {
                ":last_login": datetime.now(timezone.utc).isoformat(),
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            }

            success = await self.dynamodb_service.update_item(
                table_name=self.table_name,
                key={"user_id": user_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )

            if success:
                logger.debug(f"Updated last login for user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {e}")
            raise DatabaseError(f"Failed to update last login: {e}")

    async def update_receipt_count(self, user_id: str, count_delta: int) -> bool:
        """Update user's receipt count."""
        try:
            update_expression = """
                SET receipt_count = receipt_count + :count_delta,
                    updated_at = :updated_at
            """.strip()

            expression_attribute_values = {
                ":count_delta": count_delta,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            }

            success = await self.dynamodb_service.update_item(
                table_name=self.table_name,
                key={"user_id": user_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )

            if success:
                logger.debug(
                    f"Updated receipt count for user {user_id} by {count_delta}"
                )
            return success
        except Exception as e:
            logger.error(f"Failed to update receipt count for user {user_id}: {e}")
            raise DatabaseError(f"Failed to update receipt count: {e}")

    async def update_storage_used(self, user_id: str, bytes_delta: int) -> bool:
        """Update user's storage used."""
        try:
            update_expression = """
                SET storage_used_bytes = storage_used_bytes + :bytes_delta,
                    updated_at = :updated_at
            """.strip()

            expression_attribute_values = {
                ":bytes_delta": bytes_delta,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            }

            success = await self.dynamodb_service.update_item(
                table_name=self.table_name,
                key={"user_id": user_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )

            if success:
                logger.debug(
                    f"Updated storage used for user {user_id} by {bytes_delta} bytes"
                )
            return success
        except Exception as e:
            logger.error(f"Failed to update storage used for user {user_id}: {e}")
            raise DatabaseError(f"Failed to update storage used: {e}")

    async def update_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences."""
        try:
            update_expression = (
                "SET preferences = :preferences, updated_at = :updated_at"
            )
            expression_attribute_values = {
                ":preferences": preferences,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            }

            success = await self.dynamodb_service.update_item(
                table_name=self.table_name,
                key={"user_id": user_id},
                update_expression=update_expression,
                expression_attribute_values=expression_attribute_values,
            )

            if success:
                logger.debug(f"Updated preferences for user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            raise DatabaseError(f"Failed to update preferences: {e}")

    async def get_active_users_count(self) -> int:
        """Get count of active users."""
        try:
            # Use scan with filter for active users (not ideal for large datasets)
            items = await self.dynamodb_service.scan_items(
                table_name=self.table_name,
                filter_expression="is_active = :is_active",
                expression_attribute_values={":is_active": True},
                select="COUNT",
            )

            return len(items) if isinstance(items, list) else items.get("Count", 0)
        except Exception as e:
            logger.error(f"Failed to get active users count: {e}")
            raise DatabaseError(f"Failed to get active users count: {e}")

    async def list_users(
        self,
        limit: Optional[int] = None,
        last_evaluated_key: Optional[Dict[str, Any]] = None,
    ) -> List[User]:
        """List users (admin function)."""
        try:
            items = await self.dynamodb_service.scan_items(
                table_name=self.table_name,
                limit=limit,
                exclusive_start_key=last_evaluated_key,
            )

            users = []
            for item in items:
                users.append(self._from_dynamodb_item(item))

            logger.debug(f"Listed {len(users)} users")
            return users
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise DatabaseError(f"Failed to list users: {e}")

    # Interface compatibility methods
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their ID - interface compatibility."""
        return await self.find_by_id(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email address - interface compatibility."""
        return await self.find_by_email(email)

    async def update_last_active(self, user_id: str) -> bool:
        """Update the user's last active timestamp to now - interface compatibility."""
        return await self.update_last_login(user_id)

    async def get_inactive_free_users(self, days_threshold: int = 30) -> List[User]:
        """Get free users who have been inactive for more than the threshold days."""
        # This is a placeholder implementation
        # In a real application, you would query based on last_active_date and subscription_tier
        return []

    async def increment_image_count(self, user_id: str, count: int = 1) -> bool:
        """Increment a user's image count."""
        return await self.update_receipt_count(user_id, count)

    async def decrement_image_count(self, user_id: str, count: int = 1) -> bool:
        """Decrement a user's image count."""
        return await self.update_receipt_count(user_id, -count)
