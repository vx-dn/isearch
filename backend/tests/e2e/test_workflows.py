"""End-to-end tests for complete user workflows."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status

from main import app
from src.application.auth.middleware import get_current_active_user


@pytest.mark.e2e
class TestUserRegistrationAndLogin:
    """End-to-end tests for user registration and login workflow."""

    @pytest.mark.asyncio
    async def test_complete_user_registration_login_flow(
        self, async_client, fake_user_data
    ):
        """Test complete user registration and login flow."""

        # Step 1: Register a new user
        with patch("src.application.api.routes.auth.user_service") as mock_user_service:
            # Make service methods async
            mock_user_service.register_user = AsyncMock()
            mock_user_service.login_user = AsyncMock()
            mock_user_service.get_user_profile = AsyncMock()

            user_id = str(uuid.uuid4())
            mock_user_service.register_user.return_value = {
                "user_id": user_id,
                "email": fake_user_data["email"],
                "is_active": True,
                "subscription_tier": "free",
                "receipt_count": 0,
                "storage_used_bytes": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Register user
            register_data = {
                "email": fake_user_data["email"],
                "password": "testpassword123",  # Meet minimum requirement
            }
            register_response = await async_client.post(
                "/api/v1/auth/register", json=register_data
            )

            assert register_response.status_code == status.HTTP_200_OK
            user_data = register_response.json()
            assert user_data["email"] == register_data["email"]

            # Step 2: Login with the registered user
            mock_user_service.login_user.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": user_data,
            }

            login_data = {
                "email": fake_user_data["email"],
                "password": "testpassword123",
            }

            login_response = await async_client.post(
                "/api/v1/auth/login", json=login_data
            )

            assert login_response.status_code == status.HTTP_200_OK
            token_data = login_response.json()
            assert "access_token" in token_data
            assert token_data["token_type"] == "bearer"

            # Step 3: Access protected profile endpoint
            from src.domain.entities.enums import UserRole
            from src.domain.entities.user import User

            mock_user = User(
                user_id=user_id,
                email=fake_user_data["email"],
                role=UserRole.FREE,
                image_count=fake_user_data["image_count"],
                image_quota=fake_user_data["image_quota"],
            )

            # Use FastAPI dependency override for authentication
            app.dependency_overrides[get_current_active_user] = lambda: mock_user

            # Mock the profile service call
            mock_user_service.get_user_profile.return_value = {
                "user_id": user_id,
                "email": fake_user_data["email"],
                "is_active": True,
                "subscription_tier": "free",
                "receipt_count": 0,
                "storage_used_bytes": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            try:
                auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                profile_response = await async_client.get(
                    "/api/v1/auth/profile", headers=auth_headers
                )

                assert profile_response.status_code == status.HTTP_200_OK
                profile_data = profile_response.json()
                assert profile_data["email"] == fake_user_data["email"]
            finally:
                # Clean up dependency overrides
                app.dependency_overrides.clear()


@pytest.mark.e2e
class TestReceiptWorkflow:
    """End-to-end tests for receipt management workflow."""

    @pytest.mark.asyncio
    async def test_complete_receipt_lifecycle(
        self, async_client, auth_headers, sample_user, fake_receipt_data
    ):
        """Test complete receipt lifecycle: upload, create, update, search, delete."""

        # Use FastAPI dependency override for authentication
        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        try:
            # Step 1: Get upload URL
            with patch(
                "src.application.api.routes.receipts.receipt_service"
            ) as mock_receipt_service:
                # Make service methods async
                mock_receipt_service.generate_upload_url = AsyncMock()
                mock_receipt_service.create_receipt = AsyncMock()
                mock_receipt_service.get_receipt = AsyncMock()
                mock_receipt_service.update_receipt = AsyncMock()
                mock_receipt_service.delete_receipt = AsyncMock()
                mock_receipt_service.list_receipts = AsyncMock()

                image_id = str(uuid.uuid4())
                mock_receipt_service.generate_upload_url.return_value = {
                    "upload_url": "https://s3.amazonaws.com/bucket/receipts/test.jpg?signed",
                    "image_id": image_id,
                    "fields": {"key": "test-key", "policy": "test-policy"},
                    "expires_in": 3600,
                }

                upload_response = await async_client.post(
                    "/api/v1/receipts/upload-url", headers=auth_headers
                )

                assert upload_response.status_code == status.HTTP_200_OK
                upload_data = upload_response.json()
                assert "upload_url" in upload_data
                assert "image_id" in upload_data

                # Step 2: Create receipt
                receipt_id = str(uuid.uuid4())
                created_receipt = {
                    "receipt_id": receipt_id,
                    "user_id": sample_user.user_id,
                    "image_id": image_id,
                    "merchant_name": fake_receipt_data["merchant_name"],
                    "merchant_address": "123 Test St",
                    "purchase_date": datetime.now(timezone.utc).isoformat(),
                    "total_amount": str(fake_receipt_data["total_amount"]),
                    "currency": fake_receipt_data["currency"],
                    "receipt_type": fake_receipt_data["receipt_type"],
                    "raw_text": "Sample receipt text",
                    "confidence_score": 0.95,
                    "extraction_metadata": {"processing_time": 1.2},
                    "items": [],
                    "tags": [],
                    "notes": fake_receipt_data["notes"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "version": 1,
                }

                mock_receipt_service.create_receipt.return_value = created_receipt

                # Don't include image_id in the receipt creation request as it's not part of ReceiptCreateRequest
                receipt_create_data = fake_receipt_data

                create_response = await async_client.post(
                    "/api/v1/receipts/", json=receipt_create_data, headers=auth_headers
                )

                assert create_response.status_code == status.HTTP_200_OK
                receipt_data = create_response.json()
                assert receipt_data["receipt_id"] == receipt_id
                assert (
                    receipt_data["merchant_name"] == fake_receipt_data["merchant_name"]
                )

                # Step 3: Get receipt by ID
                mock_receipt_service.get_receipt.return_value = created_receipt

                get_response = await async_client.get(
                    f"/api/v1/receipts/{receipt_id}", headers=auth_headers
                )

                assert get_response.status_code == status.HTTP_200_OK
                get_data = get_response.json()
                assert get_data["receipt_id"] == receipt_id

                # Step 4: Update receipt
                updated_receipt = {**created_receipt}
                updated_receipt["notes"] = "Updated notes"
                updated_receipt["updated_at"] = datetime.now(timezone.utc).isoformat()
                updated_receipt["version"] = 2

                mock_receipt_service.update_receipt.return_value = updated_receipt

                update_data = {"notes": "Updated notes"}
                update_response = await async_client.put(
                    f"/api/v1/receipts/{receipt_id}",
                    json=update_data,
                    headers=auth_headers,
                )

                assert update_response.status_code == status.HTTP_200_OK
                update_result = update_response.json()
                assert update_result["notes"] == "Updated notes"

                # Step 5: List user receipts
                mock_receipt_service.list_receipts.return_value = {
                    "receipts": [updated_receipt],
                    "total_count": 1,
                    "page": 1,
                    "page_size": 20,
                    "has_more": False,
                }

                list_response = await async_client.get(
                    "/api/v1/receipts/", headers=auth_headers
                )

                assert list_response.status_code == status.HTTP_200_OK
                list_data = list_response.json()
                assert list_data["total_count"] == 1
                assert len(list_data["receipts"]) == 1
                assert list_data["receipts"][0]["receipt_id"] == receipt_id

                # Step 6: Delete receipt
                mock_receipt_service.delete_receipt.return_value = True

                delete_response = await async_client.delete(
                    f"/api/v1/receipts/{receipt_id}", headers=auth_headers
                )

                assert delete_response.status_code == status.HTTP_200_OK
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()


@pytest.mark.e2e
class TestSearchWorkflow:
    """End-to-end tests for search functionality."""

    @pytest.mark.asyncio
    async def test_complete_search_workflow(
        self, async_client, auth_headers, sample_user
    ):
        """Test complete search workflow: create receipts, search, filter."""

        # Use FastAPI dependency override for authentication
        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        try:
            with patch(
                "src.application.api.routes.search.search_service"
            ) as mock_search_service:
                # Make service methods async
                mock_search_service.search_receipts = AsyncMock()
                mock_search_service.search_by_merchant = AsyncMock()
                mock_search_service.search_by_date_range = AsyncMock()
                mock_search_service.get_suggestions = AsyncMock()
                mock_search_service.get_popular_merchants = AsyncMock()

                # Step 1: Search for receipts
                search_results = {
                    "hits": [
                        {
                            "receipt_id": str(uuid.uuid4()),
                            "merchant_name": "Coffee Shop",
                            "total_amount": "4.50",
                            "purchase_date": "2025-09-10T10:00:00Z",
                            "score": 0.95,
                        },
                        {
                            "receipt_id": str(uuid.uuid4()),
                            "merchant_name": "Another Coffee Place",
                            "total_amount": "5.25",
                            "purchase_date": "2025-09-09T15:30:00Z",
                            "score": 0.87,
                        },
                    ],
                    "total_hits": 2,
                    "processing_time_ms": 15,
                    "limit": 20,
                    "offset": 0,
                    "has_more": False,
                }

                mock_search_service.search_receipts.return_value = search_results

                search_response = await async_client.post(
                    "/api/v1/search/", json={"query": "coffee"}, headers=auth_headers
                )

                assert search_response.status_code == status.HTTP_200_OK
                search_data = search_response.json()
                assert search_data["total_hits"] == 2
                assert len(search_data["hits"]) == 2

                # Step 2: Search by merchant
                merchant_results = {
                    "hits": [search_results["hits"][0]],
                    "total_hits": 1,
                    "processing_time_ms": 10,
                    "limit": 20,
                    "offset": 0,
                    "has_more": False,
                }

                mock_search_service.search_by_merchant.return_value = merchant_results

                merchant_response = await async_client.get(
                    "/api/v1/search/merchant/Coffee%20Shop", headers=auth_headers
                )

                assert merchant_response.status_code == status.HTTP_200_OK
                merchant_data = merchant_response.json()
                assert merchant_data["total_hits"] == 1

                # Step 3: Search by date range
                date_range_results = {
                    "hits": search_results["hits"],
                    "total_hits": 2,
                    "processing_time_ms": 12,
                    "limit": 20,
                    "offset": 0,
                    "has_more": False,
                }

                mock_search_service.search_by_date_range.return_value = (
                    date_range_results
                )

                date_range_data = {"start_date": "2025-09-01", "end_date": "2025-09-30"}

                date_response = await async_client.post(
                    "/api/v1/search/date-range",
                    json=date_range_data,
                    headers=auth_headers,
                )

                assert date_response.status_code == status.HTTP_200_OK
                date_data = date_response.json()
                assert date_data["total_hits"] == 2

                # Step 4: Get search suggestions
                suggestions = ["coffee", "coffee shop", "starbucks", "dunkin"]

                mock_search_service.get_suggestions.return_value = suggestions

                suggestions_response = await async_client.get(
                    "/api/v1/search/suggestions?query=cof", headers=auth_headers
                )

                assert suggestions_response.status_code == status.HTTP_200_OK
                suggestions_data = suggestions_response.json()
                assert isinstance(suggestions_data, list)
                assert "coffee" in suggestions_data

                # Step 5: Get popular merchants
                popular_merchants = [
                    {"name": "Starbucks", "count": 15},
                    {"name": "McDonald's", "count": 12},
                    {"name": "Walmart", "count": 8},
                ]

                mock_search_service.get_popular_merchants.return_value = (
                    popular_merchants
                )

                popular_response = await async_client.get(
                    "/api/v1/search/popular-merchants", headers=auth_headers
                )

                assert popular_response.status_code == status.HTTP_200_OK
                popular_data = popular_response.json()
                assert isinstance(popular_data, list)
                assert len(popular_data) == 3
                assert popular_data[0]["name"] == "Starbucks"
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()


@pytest.mark.e2e
@pytest.mark.slow
class TestImageProcessingWorkflow:
    """End-to-end tests for image processing workflow."""

    @pytest.mark.asyncio
    async def test_receipt_image_processing_flow(
        self, async_client, auth_headers, sample_user
    ):
        """Test complete image processing flow: upload, process, check status."""

        try:
            # Use FastAPI dependency override for authentication
            app.dependency_overrides[get_current_active_user] = lambda: sample_user

            with patch(
                "src.application.api.routes.receipts.receipt_service"
            ) as mock_receipt_service:
                # Make service methods async
                mock_receipt_service.generate_upload_url = AsyncMock()
                mock_receipt_service.process_uploaded_image = AsyncMock()
                mock_receipt_service.process_receipt_image = AsyncMock()
                mock_receipt_service.get_processing_status = AsyncMock()

                image_id = str(uuid.uuid4())

                # Step 1: Get upload URL
                mock_receipt_service.generate_upload_url.return_value = {
                    "upload_url": "https://s3.amazonaws.com/bucket/receipts/test.jpg?signed",
                    "image_id": image_id,
                    "fields": {"key": "test-key", "policy": "test-policy"},
                    "expires_in": 3600,
                }

                upload_response = await async_client.post(
                    "/api/v1/receipts/upload-url", headers=auth_headers
                )

                assert upload_response.status_code == status.HTTP_200_OK

                # Step 2: Simulate image upload (would be done directly to S3 in real scenario)
                # Then trigger processing
                mock_receipt_service.process_uploaded_image.return_value = {
                    "image_id": image_id,
                    "status": "processing",
                    "message": "Image processing started",
                }

                process_response = await async_client.post(
                    f"/api/v1/receipts/process-image/{image_id}", headers=auth_headers
                )

                assert process_response.status_code == status.HTTP_200_OK
                process_data = process_response.json()
                assert process_data["status"] == "processing"

                # Step 3: Check processing status
                mock_receipt_service.get_processing_status.return_value = {
                    "image_id": image_id,
                    "status": "completed",
                    "receipt": {
                        "receipt_id": str(uuid.uuid4()),
                        "user_id": sample_user.user_id,
                        "image_id": image_id,
                        "merchant_name": "Coffee Shop",
                        "total_amount": 4.50,
                        "currency": "USD",
                        "raw_text": "Coffee Shop Receipt\nCoffee $4.50\nTotal: $4.50",
                        "confidence_score": 0.95,
                        "items": [{"name": "Coffee", "price": 4.50}],
                        "created_at": "2023-01-01T00:00:00",
                        "updated_at": "2023-01-01T00:00:00",
                        "version": 1,
                    },
                }

                status_response = await async_client.get(
                    f"/api/v1/receipts/processing-status/{image_id}",
                    headers=auth_headers,
                )

                assert status_response.status_code == status.HTTP_200_OK
                status_data = status_response.json()
                assert status_data["status"] == "completed"
                assert status_data["receipt"]["confidence_score"] == 0.95
                assert "raw_text" in status_data["receipt"]
                assert status_data["receipt"]["merchant_name"] == "Coffee Shop"
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
