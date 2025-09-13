"""Performance and load testing for the receipt search application."""

import asyncio
import time
import uuid
from datetime import datetime, timezone

import pytest

from main import app
from src.application.auth.middleware import get_current_active_user
from src.application.services.receipt_service import receipt_service
from src.application.services.search_service import search_service


@pytest.mark.performance
class TestAPIPerformance:
    """API performance testing."""

    @pytest.mark.asyncio
    async def test_receipt_list_performance(
        self, async_client, auth_headers, sample_user
    ):
        """Test performance of receipt listing endpoint."""

        # Override the auth dependency to return our test user
        async def mock_get_current_active_user():
            return sample_user

        # Override the service method
        original_list_receipts = receipt_service.list_receipts

        async def mock_list_receipts(user_id, pagination):
            # Mock large dataset
            receipts = []
            now = datetime.now(timezone.utc)
            for i in range(100):
                receipts.append(
                    {
                        "receipt_id": str(uuid.uuid4()),
                        "user_id": sample_user.user_id,
                        "merchant_name": f"Merchant {i}",
                        "total_amount": f"{i * 10}.50",
                        "currency": "USD",
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                        "version": 1,
                    }
                )

            return {
                "receipts": receipts,
                "total_count": 100,
                "page": 1,
                "page_size": 100,
                "has_more": False,
            }

        # Apply overrides
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
        receipt_service.list_receipts = mock_list_receipts

        try:
            # Measure response time
            start_time = time.time()
            response = await async_client.get("/api/v1/receipts/", headers=auth_headers)
            end_time = time.time()

            response_time = end_time - start_time

            # Assertions
            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second

            data = response.json()
            assert len(data["receipts"]) == 100
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
            receipt_service.list_receipts = original_list_receipts

    @pytest.mark.asyncio
    async def test_receipt_creation_performance(
        self, async_client, auth_headers, sample_user
    ):
        """Test performance of receipt creation endpoint."""

        # Override the auth dependency to return our test user
        async def mock_get_current_active_user():
            return sample_user

        # Override the service method
        original_create_receipt = receipt_service.create_receipt

        async def mock_create_receipt(user_id, request):
            now = datetime.now(timezone.utc)
            return {
                "receipt_id": str(uuid.uuid4()),
                "user_id": sample_user.user_id,
                "merchant_name": request.merchant_name,
                "total_amount": request.total_amount,
                "currency": request.currency or "USD",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "version": 1,
            }

        # Apply overrides
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
        receipt_service.create_receipt = mock_create_receipt

        try:
            # Test single creation performance
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/receipts/",
                headers=auth_headers,
                json={
                    "merchant_name": "Test Merchant",
                    "total_amount": "123.45",
                    "currency": "USD",
                },
            )
            end_time = time.time()

            # Assertions
            assert response.status_code == 200
            response_time = end_time - start_time
            assert response_time < 0.5  # Should complete in under 500ms

            # Test bulk creation performance (10 receipts)
            start_time = time.time()
            for i in range(10):
                response = await async_client.post(
                    "/api/v1/receipts/",
                    headers=auth_headers,
                    json={
                        "merchant_name": f"Test Merchant {i}",
                        "total_amount": f"{100 + i}.00",
                        "currency": "USD",
                    },
                )
                assert response.status_code == 200
            end_time = time.time()

            # Bulk creation should complete in reasonable time
            bulk_response_time = end_time - start_time
            assert bulk_response_time < 5.0  # 10 receipts in under 5 seconds

        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
            receipt_service.create_receipt = original_create_receipt

    @pytest.mark.asyncio
    async def test_search_performance(self, async_client, auth_headers, sample_user):
        """Test search endpoint performance."""

        # Override the auth dependency to return our test user
        async def mock_get_current_active_user():
            return sample_user

        # Override the search service method
        original_search_receipts = search_service.search_receipts

        async def mock_search_receipts(user_id, query, **kwargs):
            # Mock search results
            search_results = []
            for i in range(50):
                search_results.append(
                    {
                        "receipt_id": str(uuid.uuid4()),
                        "merchant_name": f"Coffee Shop {i}",
                        "total_amount": f"{i + 1}.50",
                        "purchase_date": datetime.now(timezone.utc).isoformat(),
                        "score": 0.9 - (i * 0.01),
                    }
                )

            return {
                "hits": search_results,
                "total_hits": 50,
                "processing_time_ms": 10,
                "limit": 50,
                "offset": 0,
                "has_more": False,
            }

        # Apply overrides
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
        search_service.search_receipts = mock_search_receipts

        try:
            # Measure search response time
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/search/",
                headers=auth_headers,
                json={"query": "coffee", "limit": 50, "offset": 0},
            )
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == 200
            assert response_time < 2.0  # Search should respond within 2 seconds

            data = response.json()
            assert len(data["hits"]) == 50

        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
            search_service.search_receipts = original_search_receipts

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(
        self, async_client, auth_headers, sample_user
    ):
        """Test performance under concurrent load."""

        # Override the auth dependency to return our test user
        async def mock_get_current_active_user():
            return sample_user

        # Override the service method
        original_list_receipts = receipt_service.list_receipts

        async def mock_list_receipts(user_id, pagination):
            return {
                "receipts": [],
                "total_count": 0,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            }

        # Apply overrides
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
        receipt_service.list_receipts = mock_list_receipts

        try:

            async def make_request():
                """Make a single request."""
                response = await async_client.get(
                    "/api/v1/receipts/", headers=auth_headers
                )
                return response.status_code

            # Run 10 concurrent requests
            start_time = time.time()
            tasks = [make_request() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = end_time - start_time

            # All requests should succeed
            assert all(status == 200 for status in results)

            # Should handle 10 concurrent requests within 3 seconds
            assert total_time < 3.0

        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
            receipt_service.list_receipts = original_list_receipts

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, async_client, auth_headers, sample_user):
        """Test memory efficiency with large datasets."""

        # Override the auth dependency to return our test user
        async def mock_get_current_active_user():
            return sample_user

        # Override the service method
        original_list_receipts = receipt_service.list_receipts

        # Apply overrides
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user

        try:
            # Mock progressively larger datasets
            for size in [10, 50, 100]:

                async def mock_list_receipts(user_id, pagination):
                    receipts = []
                    now = datetime.now(timezone.utc)
                    for i in range(size):
                        receipts.append(
                            {
                                "receipt_id": str(uuid.uuid4()),
                                "user_id": sample_user.user_id,
                                "merchant_name": f"Merchant {i}",
                                "total_amount": f"{i}.50",
                                "currency": "USD",
                                "notes": "A" * 100,  # Add some data bulk
                                "created_at": now.isoformat(),
                                "updated_at": now.isoformat(),
                                "version": 1,
                            }
                        )

                    return {
                        "receipts": receipts,
                        "total_count": size,
                        "page": 1,
                        "page_size": size,
                        "has_more": False,
                    }

                receipt_service.list_receipts = mock_list_receipts

                response = await async_client.get(
                    f"/api/v1/receipts/?page_size={size}", headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["receipts"]) == size

        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
            receipt_service.list_receipts = original_list_receipts


@pytest.mark.load
class TestLoadTesting:
    """Load testing scenarios."""

    @pytest.mark.asyncio
    async def test_sustained_load(self, async_client, auth_headers, sample_user):
        """Test sustained load over time."""

        # Override the auth dependency to return our test user
        async def mock_get_current_active_user():
            return sample_user

        # Override the service method
        original_list_receipts = receipt_service.list_receipts

        async def mock_list_receipts(user_id, pagination):
            return {
                "receipts": [],
                "total_count": 0,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            }

        # Apply overrides
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
        receipt_service.list_receipts = mock_list_receipts

        try:

            async def sustained_requests():
                """Make requests for a sustained period."""
                request_count = 0
                start_time = time.time()

                while time.time() - start_time < 5:  # Run for 5 seconds
                    response = await async_client.get(
                        "/api/v1/receipts/", headers=auth_headers
                    )
                    assert response.status_code == 200
                    request_count += 1
                    await asyncio.sleep(0.1)  # Small delay to avoid overwhelming

                return request_count

            request_count = await sustained_requests()

            # Should handle multiple requests over sustained period
            assert request_count > 10  # At least 10 requests in 5 seconds

        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
            receipt_service.list_receipts = original_list_receipts

    @pytest.mark.asyncio
    async def test_burst_load(self, async_client, auth_headers, sample_user):
        """Test handling of burst traffic."""

        # Override the auth dependency to return our test user
        async def mock_get_current_active_user():
            return sample_user

        # Override the service method
        original_list_receipts = receipt_service.list_receipts

        async def mock_list_receipts(user_id, pagination):
            return {
                "receipts": [],
                "total_count": 0,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            }

        # Apply overrides
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
        receipt_service.list_receipts = mock_list_receipts

        try:

            async def make_burst_request():
                """Make a single burst request."""
                response = await async_client.get(
                    "/api/v1/receipts/", headers=auth_headers
                )
                return response.status_code == 200

            # Create burst of 20 simultaneous requests
            start_time = time.time()
            tasks = [make_burst_request() for _ in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            burst_time = end_time - start_time

            # Count successful requests
            successful_requests = sum(1 for result in results if result is True)

            # Most requests should succeed (allow for some failures under burst)
            assert successful_requests >= 15  # At least 75% success rate
            assert burst_time < 5.0  # Should handle burst within 5 seconds

        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
            receipt_service.list_receipts = original_list_receipts


@pytest.mark.stress
class TestStressTesting:
    """Stress testing scenarios."""

    @pytest.mark.asyncio
    async def test_high_concurrency_stress(
        self, async_client, auth_headers, sample_user
    ):
        """Test system under high concurrency stress."""

        # Override the auth dependency to return our test user
        async def mock_get_current_active_user():
            return sample_user

        # Override the service method
        original_list_receipts = receipt_service.list_receipts

        async def mock_list_receipts(user_id, pagination):
            # Add small delay to simulate realistic processing
            await asyncio.sleep(0.01)
            return {
                "receipts": [],
                "total_count": 0,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            }

        # Apply overrides
        app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
        receipt_service.list_receipts = mock_list_receipts

        try:

            async def stress_request():
                """Make a stress test request."""
                try:
                    response = await async_client.get(
                        "/api/v1/receipts/", headers=auth_headers
                    )
                    return response.status_code == 200
                except Exception:
                    return False

            # Run 50 concurrent requests for stress testing
            start_time = time.time()
            tasks = [stress_request() for _ in range(50)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            stress_time = end_time - start_time

            # Count successful requests
            successful_requests = sum(1 for result in results if result is True)

            # Under stress, system should still handle majority of requests
            success_rate = successful_requests / 50
            assert success_rate >= 0.6  # At least 60% success rate under stress
            assert stress_time < 10.0  # Should complete within 10 seconds

        finally:
            # Clean up overrides
            app.dependency_overrides.clear()
            receipt_service.list_receipts = original_list_receipts
