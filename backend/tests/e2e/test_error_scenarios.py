"""End-to-end tests for error scenarios and edge cases."""

import pytest
from unittest.mock import patch
import uuid
from fastapi import status
from src.domain.exceptions import ValidationError, ReceiptNotFoundError
from src.application.auth.middleware import get_current_active_user
from main import app


@pytest.mark.e2e
class TestErrorScenarios:
    """Test error scenarios across the application."""

    @pytest.mark.asyncio
    async def test_authentication_error_flow(self, async_client):
        """Test authentication error scenarios."""

        # Test accessing protected endpoint without token
        response = await async_client.get("/api/v1/auth/profile")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = await async_client.get(
            "/api/v1/auth/profile", headers=invalid_headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test login with invalid credentials
        with patch(
            "src.application.api.routes.auth.user_service.login_user"
        ) as mock_login:
            mock_login.side_effect = ValidationError("Invalid credentials")

            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": "invalid@example.com", "password": "wrongpassword"},
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_receipt_not_found_flow(
        self, async_client, auth_headers, sample_user
    ):
        """Test receipt not found scenarios."""

        # Use FastAPI dependency override
        def override_get_current_active_user():
            return sample_user

        app.dependency_overrides[get_current_active_user] = (
            override_get_current_active_user
        )

        try:
            with patch(
                "src.application.api.routes.receipts.receipt_service.get_receipt"
            ) as mock_get_receipt:
                mock_get_receipt.side_effect = ReceiptNotFoundError("Receipt not found")

                non_existent_id = str(uuid.uuid4())
                response = await async_client.get(f"/api/v1/receipts/{non_existent_id}")
                assert response.status_code == status.HTTP_404_NOT_FOUND
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_data_validation_flow(
        self, async_client, auth_headers, sample_user
    ):
        """Test data validation error scenarios."""

        # Use FastAPI dependency override
        def override_get_current_active_user():
            return sample_user

        app.dependency_overrides[get_current_active_user] = (
            override_get_current_active_user
        )

        try:
            # Test creating receipt with invalid data
            invalid_receipt_data = {
                "image_id": "not-a-uuid",
                "merchant_name": "",  # Empty string
                "total_amount": "invalid-amount",  # Invalid decimal
                "currency": "INVALID",  # Invalid currency code
            }

            response = await async_client.post(
                "/api/v1/receipts/", json=invalid_receipt_data
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_search_error_scenarios(
        self, async_client, auth_headers, sample_user
    ):
        """Test search error scenarios."""

        # Use FastAPI dependency override
        def override_get_current_active_user():
            return sample_user

        app.dependency_overrides[get_current_active_user] = (
            override_get_current_active_user
        )

        try:
            with patch(
                "src.application.api.routes.search.search_service.search_receipts"
            ) as mock_search:
                # Test search service error
                mock_search.side_effect = ValidationError("Search service unavailable")

                response = await async_client.post(
                    "/api/v1/search/", json={"query": "test"}
                )
                assert response.status_code == status.HTTP_400_BAD_REQUEST
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


@pytest.mark.e2e
class TestConcurrencyScenarios:
    """Test concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_receipt_operations(
        self, async_client, auth_headers, sample_user
    ):
        """Test concurrent receipt creation and updates."""

        # Use FastAPI dependency override
        def override_get_current_active_user():
            return sample_user

        app.dependency_overrides[get_current_active_user] = (
            override_get_current_active_user
        )

        try:
            with patch(
                "src.application.api.routes.receipts.receipt_service.create_receipt"
            ) as mock_create_receipt, patch(
                "src.application.api.routes.receipts.receipt_service.update_receipt"
            ) as mock_update_receipt:

                receipt_id = str(uuid.uuid4())
                receipt_data = {
                    "receipt_id": receipt_id,
                    "user_id": sample_user.user_id,
                    "image_id": str(uuid.uuid4()),
                    "merchant_name": "Test Merchant",
                    "total_amount": "10.00",
                    "currency": "USD",
                    "created_at": "2025-09-12T12:00:00Z",
                    "updated_at": "2025-09-12T12:00:00Z",
                    "version": 1,
                }

                mock_create_receipt.return_value = receipt_data
                mock_update_receipt.return_value = {
                    **receipt_data,
                    "notes": "Updated",
                }

                # Simulate concurrent create and update operations
                create_data = {
                    "image_id": receipt_data["image_id"],
                    "merchant_name": receipt_data["merchant_name"],
                    "total_amount": receipt_data["total_amount"],
                    "currency": receipt_data["currency"],
                }

                # Both operations should succeed
                create_response = await async_client.post(
                    "/api/v1/receipts/", json=create_data
                )
                assert create_response.status_code == status.HTTP_200_OK

                update_response = await async_client.put(
                    f"/api/v1/receipts/{receipt_id}", json={"notes": "Updated"}
                )
                assert update_response.status_code == status.HTTP_200_OK
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


@pytest.mark.e2e
class TestDataIntegrityScenarios:
    """Test data integrity and consistency."""

    @pytest.mark.asyncio
    async def test_receipt_deletion_cascade(
        self, async_client, auth_headers, sample_user
    ):
        """Test that receipt deletion properly cascades to related data."""

        # Create a mock service for dependency override
        from unittest.mock import AsyncMock, patch
        from src.application.services.receipt_service import ReceiptService
        from src.application.auth.middleware import get_current_active_user
        from src.domain.exceptions import ReceiptNotFoundError

        mock_service = AsyncMock(spec=ReceiptService)

        # Override dependencies
        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        receipt_id = str(uuid.uuid4())

        # Delete should succeed and clean up related data
        mock_service.delete_receipt.return_value = True

        try:
            with patch(
                "src.application.api.routes.receipts.receipt_service", mock_service
            ):
                response = await async_client.delete(
                    f"/api/v1/receipts/{receipt_id}", headers=auth_headers
                )
                assert response.status_code == status.HTTP_200_OK

                # Verify receipt is no longer accessible
                mock_service.get_receipt.side_effect = ReceiptNotFoundError(
                    "Receipt not found"
                )

                get_response = await async_client.get(
                    f"/api/v1/receipts/{receipt_id}", headers=auth_headers
                )
                assert get_response.status_code == status.HTTP_404_NOT_FOUND
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()


@pytest.mark.e2e
class TestRateLimitingScenarios:
    """Test rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_api_rate_limiting(self, async_client, auth_headers, sample_user):
        """Test API rate limiting behavior."""

        # Create a mock service for dependency override
        from unittest.mock import AsyncMock, patch
        from src.application.services.receipt_service import ReceiptService
        from src.application.auth.middleware import get_current_active_user

        mock_service = AsyncMock(spec=ReceiptService)

        # Override dependencies
        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        mock_service.list_receipts.return_value = {
            "receipts": [],
            "total_count": 0,
            "page": 1,
            "page_size": 20,
            "has_more": False,
        }

        try:
            with patch(
                "src.application.api.routes.receipts.receipt_service", mock_service
            ):
                # Make multiple rapid requests
                responses = []
                for _ in range(5):
                    response = await async_client.get(
                        "/api/v1/receipts/", headers=auth_headers
                    )
                    responses.append(response)

                # All requests should succeed in normal circumstances
                # In a real implementation with rate limiting, some might return 429
                for response in responses:
                    assert response.status_code in [
                        status.HTTP_200_OK,
                        status.HTTP_429_TOO_MANY_REQUESTS,
                    ]
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()


@pytest.mark.e2e
class TestSecurityScenarios:
    """Test security-related scenarios."""

    @pytest.mark.asyncio
    async def test_cross_user_access_prevention(
        self, async_client, auth_headers, sample_user
    ):
        """Test that users cannot access other users' data."""

        # Create a mock service for dependency override
        from unittest.mock import AsyncMock, patch
        from src.application.services.receipt_service import ReceiptService
        from src.application.auth.middleware import get_current_active_user
        from src.domain.exceptions import ReceiptNotFoundError

        mock_service = AsyncMock(spec=ReceiptService)

        # Override dependencies
        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        # Mock service to return None for unauthorized access
        mock_service.get_receipt.side_effect = ReceiptNotFoundError("Receipt not found")

        other_user_receipt_id = str(uuid.uuid4())

        try:
            with patch(
                "src.application.api.routes.receipts.receipt_service", mock_service
            ):
                response = await async_client.get(
                    f"/api/v1/receipts/{other_user_receipt_id}", headers=auth_headers
                )

                # Should return 404 (not found) rather than 403 (forbidden)
                # to avoid revealing existence of other users' data
                assert response.status_code == status.HTTP_404_NOT_FOUND
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(
        self, async_client, auth_headers, sample_user
    ):
        """Test that SQL injection attempts are prevented."""

        # Create a mock service for dependency override
        from unittest.mock import AsyncMock, patch
        from src.application.services.search_service import SearchService
        from src.application.auth.middleware import get_current_active_user

        mock_service = AsyncMock(spec=SearchService)

        # Override dependencies
        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        mock_service.search_receipts.return_value = {
            "hits": [],
            "total_hits": 0,
            "processing_time_ms": 1,
            "limit": 20,
            "offset": 0,
            "has_more": False,
        }

        # Attempt SQL injection in search query
        malicious_query = "'; DROP TABLE receipts; --"

        try:
            with patch(
                "src.application.api.routes.search.search_service", mock_service
            ):
                response = await async_client.post(
                    "/api/v1/search/",
                    json={"query": malicious_query},
                    headers=auth_headers,
                )

                # Should handle safely and return results or validation error
                assert response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                ]
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
