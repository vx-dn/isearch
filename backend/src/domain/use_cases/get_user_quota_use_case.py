"""Get user quota use case implementation."""

from ..dtos import UserQuotaResponse
from ..exceptions import ResourceNotFoundError
from ..repositories import UserRepository


class GetUserQuotaUseCase:
    """Use case for getting user quota information."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str) -> UserQuotaResponse:
        """Execute the get user quota use case."""
        # Get the user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        # Update user last active
        await self.user_repository.update_last_active(user_id)

        return UserQuotaResponse(
            user_id=user.user_id,
            role=user.role,
            images_used=user.image_count,
            images_quota=user.image_quota,
            quota_remaining=user.get_available_quota(),
            reset_date=None,  # For monthly quotas, implement when needed
        )
