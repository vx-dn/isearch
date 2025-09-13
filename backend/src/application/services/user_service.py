"""User service for application layer."""

import logging
from typing import Dict, Any

from src.domain.entities.user import User
from src.domain.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
)
from src.application.api.dto import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from src.application.auth.middleware import auth_middleware
from src.infrastructure.config import infrastructure_config
from src.domain.exceptions import UserNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class UserService:
    """Application service for user operations."""

    def __init__(self):
        """Initialize user service."""
        self.user_repository = infrastructure_config.get_user_repository()
        self.cognito_service = None

        # Use cases
        self.create_user_use_case = CreateUserUseCase(self.user_repository)
        self.get_user_use_case = GetUserUseCase(self.user_repository)
        self.update_user_use_case = UpdateUserUseCase(self.user_repository)
        self.delete_user_use_case = DeleteUserUseCase(self.user_repository)

    def _get_cognito_service(self):
        """Get Cognito service (lazy initialization)."""
        if self.cognito_service is None:
            try:
                self.cognito_service = infrastructure_config.get_cognito_service()
            except Exception as e:
                logger.warning(f"Cognito service not available: {e}")
        return self.cognito_service

    def _to_user_response(self, user: User) -> UserResponse:
        """Convert User entity to response DTO."""
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            subscription_tier=user.subscription_tier,
            receipt_count=user.receipt_count,
            storage_used_bytes=user.storage_used_bytes,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
        )

    async def register_user(self, request: UserCreateRequest) -> UserResponse:
        """Register a new user."""
        try:
            cognito_service = self._get_cognito_service()

            # Check if user already exists
            existing_user = await self.user_repository.find_by_email(request.email)
            if existing_user:
                raise ValidationError("User with this email already exists")

            if request.username:
                existing_username = await self.user_repository.find_by_username(
                    request.username
                )
                if existing_username:
                    raise ValidationError("Username already taken")

            # Create user in Cognito (if available)
            cognito_user_id = None
            if cognito_service:
                cognito_result = await cognito_service.sign_up(
                    username=request.email,
                    password=request.password,
                    email=request.email,
                    attributes={
                        "name": request.display_name
                        or request.username
                        or request.email
                    },
                )

                if not cognito_result.get("success"):
                    raise ValidationError(
                        f"User registration failed: {cognito_result.get('error_message')}"
                    )

                cognito_user_id = cognito_result.get("user_sub")

            # Create user in our database
            user_data = {
                "email": request.email,
                "username": request.username,
                "display_name": request.display_name,
                "cognito_user_id": cognito_user_id,
            }

            user = await self.create_user_use_case.execute(user_data)

            logger.info(f"User registered successfully: {user.email}")
            return self._to_user_response(user)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            raise ValidationError(f"Registration failed: {e}")

    async def login_user(self, request: LoginRequest) -> LoginResponse:
        """Authenticate user and return tokens."""
        try:
            cognito_service = self._get_cognito_service()

            # Find user by email
            user = await self.user_repository.find_by_email(request.email)
            if not user:
                raise ValidationError("Invalid email or password")

            if not user.is_active:
                raise ValidationError("User account is deactivated")

            # Authenticate with Cognito (if available)
            access_token = None
            id_token = None
            refresh_token = None
            expires_in = 3600

            if cognito_service:
                auth_result = await cognito_service.initiate_auth(
                    username=request.email, password=request.password
                )

                if not auth_result.get("success"):
                    raise ValidationError("Invalid email or password")

                access_token = auth_result.get("access_token")
                id_token = auth_result.get("id_token")
                refresh_token = auth_result.get("refresh_token")
                expires_in = auth_result.get("expires_in", 3600)
            else:
                # Development mode - create simple JWT
                access_token = auth_middleware.create_access_token(user, expires_in)

            # Update last login
            await self.user_repository.update_last_login(user.user_id)

            logger.info(f"User logged in successfully: {user.email}")

            return LoginResponse(
                access_token=access_token,
                id_token=id_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                user=self._to_user_response(user),
            )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"User login failed: {e}")
            raise ValidationError(f"Login failed: {e}")

    async def get_user_profile(self, user_id: str) -> UserResponse:
        """Get user profile."""
        try:
            user = await self.get_user_use_case.execute(user_id)
            return self._to_user_response(user)
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            raise ValidationError(f"Failed to get user profile: {e}")

    async def update_user_profile(
        self, user_id: str, request: UserUpdateRequest
    ) -> UserResponse:
        """Update user profile."""
        try:
            # Get current user
            user = await self.get_user_use_case.execute(user_id)

            # Check username uniqueness if changing
            if request.username and request.username != user.username:
                existing_username = await self.user_repository.find_by_username(
                    request.username
                )
                if existing_username:
                    raise ValidationError("Username already taken")

            # Update user data
            update_data = {}
            if request.username is not None:
                update_data["username"] = request.username
            if request.display_name is not None:
                update_data["display_name"] = request.display_name
            if request.preferences is not None:
                update_data["preferences"] = request.preferences

            updated_user = await self.update_user_use_case.execute(user_id, update_data)

            logger.info(f"User profile updated: {user_id}")
            return self._to_user_response(updated_user)

        except (UserNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            raise ValidationError(f"Failed to update user profile: {e}")

    async def change_password(self, user: User, request: ChangePasswordRequest) -> bool:
        """Change user password."""
        try:
            cognito_service = self._get_cognito_service()

            if not cognito_service:
                raise ValidationError(
                    "Password change not supported in development mode"
                )

            # We need the user's current access token for this operation
            # This should be handled by the API endpoint
            raise NotImplementedError(
                "Change password requires access token from request"
            )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            raise ValidationError(f"Password change failed: {e}")

    async def forgot_password(self, request: ForgotPasswordRequest) -> bool:
        """Initiate forgot password flow."""
        try:
            cognito_service = self._get_cognito_service()

            if not cognito_service:
                raise ValidationError(
                    "Password reset not supported in development mode"
                )

            # Check if user exists
            user = await self.user_repository.find_by_email(request.email)
            if not user:
                # For security, don't reveal if email exists
                logger.info(
                    f"Password reset requested for non-existent email: {request.email}"
                )
                return True

            # Initiate forgot password flow
            result = await cognito_service.forgot_password(request.email)

            if not result.get("success"):
                logger.error(f"Forgot password failed: {result.get('error_message')}")
                raise ValidationError("Password reset failed")

            logger.info(f"Password reset initiated for: {request.email}")
            return True

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Forgot password failed: {e}")
            raise ValidationError(f"Password reset failed: {e}")

    async def reset_password(self, request: ResetPasswordRequest) -> bool:
        """Reset password with confirmation code."""
        try:
            cognito_service = self._get_cognito_service()

            if not cognito_service:
                raise ValidationError(
                    "Password reset not supported in development mode"
                )

            # Confirm forgot password
            result = await cognito_service.confirm_forgot_password(
                username=request.email,
                confirmation_code=request.confirmation_code,
                new_password=request.new_password,
            )

            if not result.get("success"):
                raise ValidationError(
                    f"Password reset failed: {result.get('error_message')}"
                )

            logger.info(f"Password reset completed for: {request.email}")
            return True

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            raise ValidationError(f"Password reset failed: {e}")

    async def delete_user_account(self, user_id: str) -> bool:
        """Delete user account (soft delete)."""
        try:
            success = await self.delete_user_use_case.execute(user_id)
            if success:
                logger.info(f"User account deleted: {user_id}")
            return success
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete user account: {e}")
            raise ValidationError(f"Account deletion failed: {e}")

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            user = await self.get_user_use_case.execute(user_id)

            return {
                "receipt_count": user.receipt_count,
                "storage_used_bytes": user.storage_used_bytes,
                "subscription_tier": user.subscription_tier,
                "member_since": user.created_at,
                "last_login": user.last_login,
            }
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            raise ValidationError(f"Failed to get user stats: {e}")


# Global user service instance
user_service = UserService()
