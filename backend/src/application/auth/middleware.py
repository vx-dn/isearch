"""Authentication middleware and utilities."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain.entities.user import User
from src.infrastructure.config import infrastructure_config

logger = logging.getLogger(__name__)

# JWT configuration (should be in environment variables)
JWT_SECRET_KEY = "your-secret-key"  # This should come from environment
JWT_ALGORITHM = "HS256"

security = HTTPBearer()


class AuthenticationError(Exception):
    """Authentication error."""

    pass


class AuthMiddleware:
    """Authentication middleware."""

    def __init__(self):
        self.cognito_service = None
        self.user_repository = None

    def _get_services(self):
        """Get services (lazy initialization)."""
        if self.cognito_service is None:
            try:
                self.cognito_service = infrastructure_config.get_cognito_service()
            except Exception as e:
                logger.warning(f"Cognito service not available: {e}")

        if self.user_repository is None:
            self.user_repository = infrastructure_config.get_user_repository()

    async def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate JWT token."""
        try:
            # For development, we'll use simple JWT
            # In production, this should validate Cognito JWT tokens
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

    async def validate_cognito_token(self, token: str) -> dict[str, Any]:
        """Validate Cognito JWT token."""
        self._get_services()

        if not self.cognito_service:
            # Fallback to simple JWT for development
            return await self.decode_token(token)

        try:
            # Use Cognito service to get user info
            result = await self.cognito_service.get_user(token)
            if not result.get("success"):
                raise AuthenticationError(
                    f"Token validation failed: {result.get('error_message')}"
                )

            return {
                "sub": result.get("username"),
                "email": result.get("attributes", {}).get("email"),
                "username": result.get("username"),
                "user_status": result.get("user_status"),
            }
        except Exception as e:
            logger.error(f"Cognito token validation failed: {e}")
            raise AuthenticationError(f"Token validation failed: {e}")

    async def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        self._get_services()

        try:
            # Validate token and get payload
            if self.cognito_service:
                payload = await self.validate_cognito_token(token)
                cognito_user_id = payload.get("sub")

                # Find user by Cognito ID
                user = await self.user_repository.find_by_cognito_user_id(
                    cognito_user_id
                )
            else:
                # Development mode - use simple JWT
                payload = await self.decode_token(token)
                user_id = payload.get("user_id")

                if not user_id:
                    raise AuthenticationError("Invalid token payload")

                # Find user by ID
                user = await self.user_repository.find_by_id(user_id)

            if not user:
                raise AuthenticationError("User not found")

            if not user.is_active:
                raise AuthenticationError("User account is deactivated")

            # Update last login
            await self.user_repository.update_last_login(user.user_id)

            return user
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")

    def create_access_token(
        self, user: User, expires_delta: Optional[int] = None
    ) -> str:
        """Create access token for user (development mode)."""
        if expires_delta is None:
            expires_delta = 3600  # 1 hour

        expire = datetime.now(timezone.utc).timestamp() + expires_delta
        payload = {
            "user_id": user.user_id,
            "email": user.email,
            "exp": expire,
            "iat": datetime.now(timezone.utc).timestamp(),
        }

        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# Global auth middleware instance
auth_middleware = AuthMiddleware()


# FastAPI dependency functions
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """FastAPI dependency to get current authenticated user."""
    try:
        token = credentials.credentials
        user = await auth_middleware.get_current_user(token)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """FastAPI dependency to get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[User]:
    """FastAPI dependency to get optional authenticated user."""
    if not credentials:
        return None

    try:
        token = credentials.credentials
        user = await auth_middleware.get_current_user(token)
        return user
    except Exception:
        return None


# Admin user dependency
async def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """FastAPI dependency to get admin user."""
    if current_user.subscription_tier != "enterprise":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user
