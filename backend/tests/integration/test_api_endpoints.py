"""Integration tests for API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
import json
from datetime import datetime, timezone
from decimal import Decimal
import uuid

fr        ) as mock_create:

            mock_auth.return_value = sample_user
            
            # Create a mock receipt entity
            from src.domain.entities.receipt import Receipt
            mock_receipt = Receipt(
                receipt_id=str(uuid.uuid4()),
                user_id=sample_user.user_id,
                merchant_name=fake_receipt_data["merchant_name"],
                total_amount=Decimal(str(fake_receipt_data["total_amount"])),
                currency=fake_receipt_data["currency"],
                receipt_type=fake_receipt_data["receipt_type"],
            )
            mock_create.return_value = mock_receipt

            response = await async_client.post(
                "/api/v1/receipts/", json=fake_receipt_data, headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["merchant_name"] == fake_receipt_data["merchant_name"]
            assert data["user_id"] == sample_user.user_idport status


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

    @pytest.mark.asyncio
    async def test_health_ready_endpoint(self, async_client):
        """Test health readiness endpoint."""
        response = await async_client.get("/api/v1/health/ready")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_health_live_endpoint(self, async_client):
        """Test health liveness endpoint."""
        response = await async_client.get("/api/v1/health/live")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data


@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_endpoint(self, async_client, fake_user_data):
        """Test user registration endpoint."""
        with patch(
            "src.application.services.user_service.user_service.create_user"
        ) as mock_create:
            # Mock the create_user method to return a User entity
            from src.domain.entities.user import User
            from src.domain.entities.enums import UserRole
            
            mock_user = User(
                user_id=str(uuid.uuid4()),
                email=fake_user_data["email"],
                role=UserRole.FREE,
                image_count=0,
                image_quota=100,
                last_active_date=datetime.now(timezone.utc),
            )
            mock_create.return_value = mock_user

            response = await async_client.post(
                "/api/v1/auth/register", json=fake_user_data
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["email"] == fake_user_data["email"]
            assert data["role"] == "free"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client, fake_user_data):
        """Test registration with invalid email."""
        fake_user_data["email"] = "invalid-email"

        response = await async_client.post("/api/v1/auth/register", json=fake_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_endpoint(self, async_client):
        """Test user login endpoint."""
        login_data = {"email": "test@example.com", "password": "testpassword"}

        with patch(
            "src.application.services.user_service.user_service.authenticate_user"
        ) as mock_auth:
            mock_auth.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "token_type": "bearer",
                "expires_in": 3600,
            }

            response = await async_client.post("/api/v1/auth/login", json=login_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client):
        """Test login with invalid credentials."""
        login_data = {"email": "test@example.com", "password": "wrongpassword"}

        with patch(
            "src.application.services.user_service.user_service.authenticate_user"
        ) as mock_auth:
            mock_auth.side_effect = Exception(
                "Invalid credentials"
            )

            response = await async_client.post("/api/v1/auth/login", json=login_data)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_profile_endpoint_unauthorized(self, async_client):
        """Test profile endpoint without authentication."""
        response = await async_client.get("/api/v1/auth/profile")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_profile_endpoint_authorized(
        self, async_client, auth_headers, sample_user
    ):
        """Test profile endpoint with authentication."""
        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth:
            mock_auth.return_value = sample_user

            response = await async_client.get(
                "/api/v1/auth/profile", headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == sample_user.email


@pytest.mark.integration
class TestReceiptEndpoints:
    """Integration tests for receipt endpoints."""

    @pytest.mark.asyncio
    async def test_create_receipt_unauthorized(self, async_client, fake_receipt_data):
        """Test creating receipt without authentication."""
        response = await async_client.post("/api/v1/receipts/", json=fake_receipt_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_receipt_authorized(
        self, async_client, auth_headers, sample_user, fake_receipt_data
    ):
        """Test creating receipt with authentication."""
        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service.create_receipt"
        ) as mock_create:

            mock_auth.return_value = sample_user
            
            # Create a mock receipt entity
            from src.domain.entities.receipt import Receipt
            mock_receipt = Receipt(
                receipt_id=str(uuid.uuid4()),
                user_id=sample_user.user_id,
                "merchant_name": fake_receipt_data["merchant_name"],
                "total_amount": str(fake_receipt_data["total_amount"]),
                "currency": fake_receipt_data["currency"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            response = await async_client.post(
                "/api/v1/receipts/", json=fake_receipt_data, headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["merchant_name"] == fake_receipt_data["merchant_name"]
            assert data["user_id"] == sample_user.user_id

    @pytest.mark.asyncio
    async def test_get_receipts_authorized(
        self, async_client, auth_headers, sample_user
    ):
        """Test getting user receipts with authentication."""
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

            response = await async_client.get("/api/v1/receipts/", headers=auth_headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "receipts" in data
            assert "total" in data

    @pytest.mark.asyncio
    async def test_get_receipt_by_id_not_found(
        self, async_client, auth_headers, sample_user
    ):
        """Test getting receipt by ID when not found."""
        receipt_id = str(uuid.uuid4())

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user
            mock_service.get_receipt_by_id.side_effect = Exception("Receipt not found")

            response = await async_client.get(
                f"/api/v1/receipts/{receipt_id}", headers=auth_headers
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_upload_url_endpoint(self, async_client, auth_headers, sample_user):
        """Test getting upload URL."""
        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user
            mock_service.generate_upload_url.return_value = {
                "upload_url": "https://s3.amazonaws.com/bucket/key?signed",
                "image_id": str(uuid.uuid4()),
                "expires_in": 3600,
            }

            response = await async_client.get(
                "/api/v1/receipts/upload-url", headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "upload_url" in data
            assert "image_id" in data
            assert "expires_in" in data


@pytest.mark.integration
class TestSearchEndpoints:
    """Integration tests for search endpoints."""

    @pytest.mark.asyncio
    async def test_search_receipts_unauthorized(self, async_client):
        """Test searching receipts without authentication."""
        response = await async_client.get("/api/v1/search/?q=coffee")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_search_receipts_authorized(
        self, async_client, auth_headers, sample_user
    ):
        """Test searching receipts with authentication."""
        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.search_service.search_service"
        ) as mock_service:

            mock_auth.return_value = sample_user
            mock_service.search_receipts.return_value = {
                "results": [],
                "total": 0,
                "query": "coffee",
                "page": 1,
                "per_page": 20,
            }

            response = await async_client.get(
                "/api/v1/search/?q=coffee", headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "results" in data
            assert "total" in data
            assert data["query"] == "coffee"

    @pytest.mark.asyncio
    async def test_search_suggestions_endpoint(
        self, async_client, auth_headers, sample_user
    ):
        """Test getting search suggestions."""
        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.search_service.search_service"
        ) as mock_service:

            mock_auth.return_value = sample_user
            mock_service.get_search_suggestions.return_value = {
                "suggestions": ["coffee", "restaurant", "grocery"]
            }

            response = await async_client.get(
                "/api/v1/search/suggestions?q=cof", headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "suggestions" in data
            assert isinstance(data["suggestions"], list)

    @pytest.mark.asyncio
    async def test_popular_merchants_endpoint(
        self, async_client, auth_headers, sample_user
    ):
        """Test getting popular merchants."""
        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.search_service.search_service"
        ) as mock_service:

            mock_auth.return_value = sample_user
            mock_service.get_popular_merchants.return_value = {
                "merchants": [
                    {"name": "Starbucks", "count": 15},
                    {"name": "McDonald's", "count": 10},
                ]
            }

            response = await async_client.get(
                "/api/v1/search/popular-merchants", headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "merchants" in data
            assert isinstance(data["merchants"], list)
