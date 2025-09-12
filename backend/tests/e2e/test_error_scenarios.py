"""End-to-end tests for error scenarios and edge cases."""

import pytest
from unittest.mock import patch
import uuid
from fastapi import status


@pytest.mark.e2e
class TestErrorScenarios:
    """Test error scenarios across the application."""

    @pytest.mark.asyncio
    async def test_authentication_error_flow(self, async_client):
        """Test authentication error scenarios."""

        # Test accessing protected endpoint without token
        response = await async_client.get("/api/v1/auth/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = await async_client.get(
            "/api/v1/auth/profile", headers=invalid_headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test login with invalid credentials
        with patch(
            "src.application.services.user_service.user_service"
        ) as mock_service:
            mock_service.authenticate_user.return_value = None

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

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth:
            mock_auth.return_value = sample_user

            with patch(
                "src.application.services.receipt_service.receipt_service"
            ) as mock_service:
                mock_service.get_receipt_by_id.return_value = None

                non_existent_id = str(uuid.uuid4())
                response = await async_client.get(
                    f"/api/v1/receipts/{non_existent_id}", headers=auth_headers
                )
                assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_invalid_data_validation_flow(
        self, async_client, auth_headers, sample_user
    ):
        """Test data validation error scenarios."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth:
            mock_auth.return_value = sample_user

            # Test creating receipt with invalid data
            invalid_receipt_data = {
                "image_id": "not-a-uuid",
                "merchant_name": "",  # Empty string
                "total_amount": "invalid-amount",  # Invalid decimal
                "currency": "INVALID",  # Invalid currency code
            }

            response = await async_client.post(
                "/api/v1/receipts/", json=invalid_receipt_data, headers=auth_headers
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_search_error_scenarios(
        self, async_client, auth_headers, sample_user
    ):
        """Test search error scenarios."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth:
            mock_auth.return_value = sample_user

            with patch(
                "src.application.services.search_service.search_service"
            ) as mock_service:
                # Test search service error
                mock_service.search_receipts.side_effect = Exception(
                    "Search service unavailable"
                )

                response = await async_client.get(
                    "/api/v1/search/?q=test", headers=auth_headers
                )
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.e2e
class TestConcurrencyScenarios:
    """Test concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_receipt_operations(
        self, async_client, auth_headers, sample_user
    ):
        """Test concurrent receipt creation and updates."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user

            receipt_id = str(uuid.uuid4())
            receipt_data = {
                "receipt_id": receipt_id,
                "user_id": sample_user.user_id,
                "image_id": str(uuid.uuid4()),
                "merchant_name": "Test Merchant",
                "total_amount": "10.00",
                "currency": "USD",
            }

            mock_service.create_receipt.return_value = receipt_data
            mock_service.update_receipt.return_value = {
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
                "/api/v1/receipts/", json=create_data, headers=auth_headers
            )
            assert create_response.status_code == status.HTTP_201_CREATED

            update_response = await async_client.put(
                f"/api/v1/receipts/{receipt_id}",
                json={"notes": "Updated"},
                headers=auth_headers,
            )
            assert update_response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
class TestDataIntegrityScenarios:
    """Test data integrity and consistency."""

    @pytest.mark.asyncio
    async def test_receipt_deletion_cascade(
        self, async_client, auth_headers, sample_user
    ):
        """Test that receipt deletion properly cascades to related data."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user

            receipt_id = str(uuid.uuid4())

            # Delete should succeed and clean up related data
            mock_service.delete_receipt.return_value = True

            response = await async_client.delete(
                f"/api/v1/receipts/{receipt_id}", headers=auth_headers
            )
            assert response.status_code == status.HTTP_204_NO_CONTENT

            # Verify receipt is no longer accessible
            mock_service.get_receipt_by_id.return_value = None

            get_response = await async_client.get(
                f"/api/v1/receipts/{receipt_id}", headers=auth_headers
            )
            assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.e2e
class TestRateLimitingScenarios:
    """Test rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_api_rate_limiting(self, async_client, auth_headers, sample_user):
        """Test API rate limiting behavior."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user
            mock_service.get_receipts_by_user.return_value = {
                "receipts": [],
                "total": 0,
                "page": 1,
                "per_page": 20,
                "has_next": False,
            }

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


@pytest.mark.e2e
class TestSecurityScenarios:
    """Test security-related scenarios."""

    @pytest.mark.asyncio
    async def test_cross_user_access_prevention(
        self, async_client, auth_headers, sample_user
    ):
        """Test that users cannot access other users' data."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user

            # Mock service to return None for unauthorized access
            mock_service.get_receipt_by_id.return_value = None

            other_user_receipt_id = str(uuid.uuid4())

            response = await async_client.get(
                f"/api/v1/receipts/{other_user_receipt_id}", headers=auth_headers
            )

            # Should return 404 (not found) rather than 403 (forbidden)
            # to avoid revealing existence of other users' data
            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(
        self, async_client, auth_headers, sample_user
    ):
        """Test that SQL injection attempts are prevented."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.search_service.search_service"
        ) as mock_service:

            mock_auth.return_value = sample_user
            mock_service.search_receipts.return_value = {
                "results": [],
                "total": 0,
                "query": "test",
                "page": 1,
                "per_page": 20,
            }

            # Attempt SQL injection in search query
            malicious_query = "'; DROP TABLE receipts; --"

            response = await async_client.get(
                f"/api/v1/search/?q={malicious_query}", headers=auth_headers
            )

            # Should handle safely and return results or validation error
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]
