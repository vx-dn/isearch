"""End-to-end tests for complete user workflows."""

import pytest
from unittest.mock import patch, AsyncMock
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import status


@pytest.mark.e2e
class TestUserRegistrationAndLogin:
    """End-to-end tests for user registration and login workflow."""

    @pytest.mark.asyncio
    async def test_complete_user_registration_login_flow(
        self, async_client, fake_user_data
    ):
        """Test complete user registration and login flow."""

        # Step 1: Register a new user
        with patch(
            "src.application.services.user_service.user_service"
        ) as mock_user_service:
            user_id = str(uuid.uuid4())
            mock_user_service.create_user.return_value = {
                "user_id": user_id,
                "username": fake_user_data["username"],
                "email": fake_user_data["email"],
                "full_name": fake_user_data["full_name"],
                "is_active": True,
                "subscription_tier": "free",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Register user
            register_response = await async_client.post(
                "/api/v1/auth/register", json=fake_user_data
            )

            assert register_response.status_code == status.HTTP_201_CREATED
            user_data = register_response.json()
            assert user_data["email"] == fake_user_data["email"]

            # Step 2: Login with the registered user
            mock_user_service.authenticate_user.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": user_data,
            }

            login_data = {
                "email": fake_user_data["email"],
                "password": fake_user_data["password"],
            }

            login_response = await async_client.post(
                "/api/v1/auth/login", json=login_data
            )

            assert login_response.status_code == status.HTTP_200_OK
            token_data = login_response.json()
            assert "access_token" in token_data
            assert token_data["token_type"] == "bearer"

            # Step 3: Access protected profile endpoint
            from src.domain.entities.user import User

            mock_user = User(
                user_id=user_id,
                username=fake_user_data["username"],
                email=fake_user_data["email"],
                full_name=fake_user_data["full_name"],
                is_active=True,
                subscription_tier="free",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            with patch(
                "src.application.auth.middleware.get_current_active_user"
            ) as mock_auth:
                mock_auth.return_value = mock_user

                auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                profile_response = await async_client.get(
                    "/api/v1/auth/profile", headers=auth_headers
                )

                assert profile_response.status_code == status.HTTP_200_OK
                profile_data = profile_response.json()
                assert profile_data["email"] == fake_user_data["email"]


@pytest.mark.e2e
class TestReceiptWorkflow:
    """End-to-end tests for receipt management workflow."""

    @pytest.mark.asyncio
    async def test_complete_receipt_lifecycle(
        self, async_client, auth_headers, sample_user, fake_receipt_data
    ):
        """Test complete receipt lifecycle: upload, create, update, search, delete."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth:
            mock_auth.return_value = sample_user

            # Step 1: Get upload URL
            with patch(
                "src.application.services.receipt_service.receipt_service"
            ) as mock_receipt_service:
                image_id = str(uuid.uuid4())
                mock_receipt_service.generate_upload_url.return_value = {
                    "upload_url": "https://s3.amazonaws.com/bucket/receipts/test.jpg?signed",
                    "image_id": image_id,
                    "expires_in": 3600,
                }

                upload_response = await async_client.get(
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
                    "total_amount": str(fake_receipt_data["total_amount"]),
                    "currency": fake_receipt_data["currency"],
                    "receipt_type": fake_receipt_data["receipt_type"],
                    "notes": fake_receipt_data["notes"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }

                mock_receipt_service.create_receipt.return_value = created_receipt

                receipt_create_data = {"image_id": image_id, **fake_receipt_data}

                create_response = await async_client.post(
                    "/api/v1/receipts/", json=receipt_create_data, headers=auth_headers
                )

                assert create_response.status_code == status.HTTP_201_CREATED
                receipt_data = create_response.json()
                assert receipt_data["receipt_id"] == receipt_id
                assert (
                    receipt_data["merchant_name"] == fake_receipt_data["merchant_name"]
                )

                # Step 3: Get receipt by ID
                mock_receipt_service.get_receipt_by_id.return_value = created_receipt

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
                mock_receipt_service.get_receipts_by_user.return_value = {
                    "receipts": [updated_receipt],
                    "total": 1,
                    "page": 1,
                    "per_page": 20,
                    "has_next": False,
                }

                list_response = await async_client.get(
                    "/api/v1/receipts/", headers=auth_headers
                )

                assert list_response.status_code == status.HTTP_200_OK
                list_data = list_response.json()
                assert list_data["total"] == 1
                assert len(list_data["receipts"]) == 1
                assert list_data["receipts"][0]["receipt_id"] == receipt_id

                # Step 6: Delete receipt
                mock_receipt_service.delete_receipt.return_value = True

                delete_response = await async_client.delete(
                    f"/api/v1/receipts/{receipt_id}", headers=auth_headers
                )

                assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.e2e
class TestSearchWorkflow:
    """End-to-end tests for search functionality."""

    @pytest.mark.asyncio
    async def test_complete_search_workflow(
        self, async_client, auth_headers, sample_user
    ):
        """Test complete search workflow: create receipts, search, filter."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.search_service.search_service"
        ) as mock_search_service:

            mock_auth.return_value = sample_user

            # Step 1: Search for receipts
            search_results = {
                "results": [
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
                "total": 2,
                "query": "coffee",
                "page": 1,
                "per_page": 20,
            }

            mock_search_service.search_receipts.return_value = search_results

            search_response = await async_client.get(
                "/api/v1/search/?q=coffee&page=1&per_page=20", headers=auth_headers
            )

            assert search_response.status_code == status.HTTP_200_OK
            search_data = search_response.json()
            assert search_data["total"] == 2
            assert len(search_data["results"]) == 2
            assert search_data["query"] == "coffee"

            # Step 2: Search by merchant
            merchant_results = {
                "results": [search_results["results"][0]],
                "total": 1,
                "merchant": "Coffee Shop",
            }

            mock_search_service.search_by_merchant.return_value = merchant_results

            merchant_response = await async_client.get(
                "/api/v1/search/merchant/Coffee%20Shop", headers=auth_headers
            )

            assert merchant_response.status_code == status.HTTP_200_OK
            merchant_data = merchant_response.json()
            assert merchant_data["total"] == 1
            assert merchant_data["merchant"] == "Coffee Shop"

            # Step 3: Search by date range
            date_range_results = {
                "results": search_results["results"],
                "total": 2,
                "start_date": "2025-09-01",
                "end_date": "2025-09-30",
            }

            mock_search_service.search_by_date_range.return_value = date_range_results

            date_range_data = {"start_date": "2025-09-01", "end_date": "2025-09-30"}

            date_response = await async_client.post(
                "/api/v1/search/date-range", json=date_range_data, headers=auth_headers
            )

            assert date_response.status_code == status.HTTP_200_OK
            date_data = date_response.json()
            assert date_data["total"] == 2

            # Step 4: Get search suggestions
            suggestions = {
                "suggestions": ["coffee", "coffee shop", "starbucks", "dunkin"]
            }

            mock_search_service.get_search_suggestions.return_value = suggestions

            suggestions_response = await async_client.get(
                "/api/v1/search/suggestions?q=cof", headers=auth_headers
            )

            assert suggestions_response.status_code == status.HTTP_200_OK
            suggestions_data = suggestions_response.json()
            assert "suggestions" in suggestions_data
            assert "coffee" in suggestions_data["suggestions"]

            # Step 5: Get popular merchants
            popular_merchants = {
                "merchants": [
                    {"name": "Starbucks", "count": 15},
                    {"name": "McDonald's", "count": 12},
                    {"name": "Walmart", "count": 8},
                ]
            }

            mock_search_service.get_popular_merchants.return_value = popular_merchants

            popular_response = await async_client.get(
                "/api/v1/search/popular-merchants", headers=auth_headers
            )

            assert popular_response.status_code == status.HTTP_200_OK
            popular_data = popular_response.json()
            assert "merchants" in popular_data
            assert len(popular_data["merchants"]) == 3
            assert popular_data["merchants"][0]["name"] == "Starbucks"


@pytest.mark.e2e
@pytest.mark.slow
class TestImageProcessingWorkflow:
    """End-to-end tests for image processing workflow."""

    @pytest.mark.asyncio
    async def test_receipt_image_processing_flow(
        self, async_client, auth_headers, sample_user
    ):
        """Test complete image processing flow: upload, process, check status."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth:
            mock_auth.return_value = sample_user

            with patch(
                "src.application.services.receipt_service.receipt_service"
            ) as mock_receipt_service:
                image_id = str(uuid.uuid4())

                # Step 1: Get upload URL
                mock_receipt_service.generate_upload_url.return_value = {
                    "upload_url": "https://s3.amazonaws.com/bucket/receipts/test.jpg?signed",
                    "image_id": image_id,
                    "expires_in": 3600,
                }

                upload_response = await async_client.get(
                    "/api/v1/receipts/upload-url", headers=auth_headers
                )

                assert upload_response.status_code == status.HTTP_200_OK
                upload_data = upload_response.json()

                # Step 2: Simulate image upload (would be done directly to S3 in real scenario)
                # Then trigger processing
                mock_receipt_service.process_receipt_image.return_value = {
                    "image_id": image_id,
                    "status": "processing",
                    "message": "Image processing started",
                }

                process_response = await async_client.post(
                    f"/api/v1/receipts/process-image/{image_id}", headers=auth_headers
                )

                assert process_response.status_code == status.HTTP_202_ACCEPTED
                process_data = process_response.json()
                assert process_data["status"] == "processing"

                # Step 3: Check processing status
                mock_receipt_service.get_processing_status.return_value = {
                    "image_id": image_id,
                    "status": "completed",
                    "confidence_score": 0.95,
                    "extracted_text": "Coffee Shop Receipt\nCoffee $4.50\nTotal: $4.50",
                    "structured_data": {
                        "merchant": "Coffee Shop",
                        "total": "4.50",
                        "items": [{"name": "Coffee", "price": "4.50"}],
                    },
                }

                status_response = await async_client.get(
                    f"/api/v1/receipts/processing-status/{image_id}",
                    headers=auth_headers,
                )

                assert status_response.status_code == status.HTTP_200_OK
                status_data = status_response.json()
                assert status_data["status"] == "completed"
                assert status_data["confidence_score"] == 0.95
                assert "extracted_text" in status_data
                assert "structured_data" in status_data
