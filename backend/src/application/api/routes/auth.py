"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from src.application.api.dto import (
    UserCreateRequest,
    UserResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    SuccessResponse,
)
from src.application.services.user_service import user_service
from src.application.auth.middleware import get_current_active_user
from src.domain.entities.user import User
from src.domain.exceptions import ValidationError

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(request: UserCreateRequest):
    """Register a new user."""
    try:
        user = await user_service.register_user(request)
        return user
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login user."""
    try:
        response = await user_service.login_user(request)
        return response
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile."""
    try:
        profile = await user_service.get_user_profile(current_user.user_id)
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """Initiate forgot password flow."""
    try:
        success = await user_service.forgot_password(request)
        return SuccessResponse(
            success=success, message="Password reset instructions sent to your email"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(request: ResetPasswordRequest):
    """Reset password with confirmation code."""
    try:
        success = await user_service.reset_password(request)
        return SuccessResponse(success=success, message="Password reset successfully")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (placeholder - token invalidation would happen client-side)."""
    # In a full implementation, you might:
    # 1. Add token to blacklist
    # 2. Revoke refresh tokens
    # 3. Clear server-side sessions
    return SuccessResponse(success=True, message="Logged out successfully")
