"""Integration tests for API endpoints - Fixed version."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import status

from src.application.api.dto import UserResponse


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client):
        """Test root endpoint."""
        response = await async_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Receipt Search API is running"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client):
        """Test basic health endpoint."""
        response = await async_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_health_endpoint(self, async_client):
        """Test API health endpoint."""
        response = await async_client.get("/api/v1/health/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
        assert "version" in data
        assert data["version"] == "1.0.0"


@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_endpoint(self, async_client, fake_user_data):
        """Test user registration endpoint."""
        with patch(
            "src.application.api.routes.auth.user_service.register_user"
        ) as mock_register:
            # Setup mock
            mock_user = UserResponse(
                user_id="test-id",
                email=fake_user_data["email"],
                subscription_tier="free",
                receipt_count=0,
                storage_used_bytes=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_active=True,
            )
            mock_register.return_value = mock_user

            # Test request
            request_data = {"email": fake_user_data["email"], "password": "testpass123"}
            response = await async_client.post(
                "/api/v1/auth/register", json=request_data
            )

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["email"] == fake_user_data["email"]
            assert response_data["subscription_tier"] == "free"
            mock_register.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client, fake_user_data):
        """Test registration with invalid email."""
        fake_user_data["email"] = "invalid-email"

        response = await async_client.post("/api/v1/auth/register", json=fake_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_profile_endpoint_unauthorized(self, async_client):
        """Test profile endpoint without authentication."""
        response = await async_client.get("/api/v1/auth/profile")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
class TestReceiptEndpoints:
    """Integration tests for receipt endpoints."""

    @pytest.mark.asyncio
    async def test_create_receipt_unauthorized(self, async_client, fake_receipt_data):
        """Test creating receipt without authentication."""
        response = await async_client.post("/api/v1/receipts/", json=fake_receipt_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
class TestSearchEndpoints:
    """Integration tests for search endpoints."""

    @pytest.mark.asyncio
    async def test_search_receipts_unauthorized(self, async_client):
        """Test searching receipts without authentication."""
        response = await async_client.post("/api/v1/search/", json={"query": "coffee"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
