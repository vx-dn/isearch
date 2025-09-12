"""Performance and load tests for the Receipt Search API."""

import pytest
import asyncio
import time
from unittest.mock import patch
import uuid
from datetime import datetime, timezone
from typing import List


@pytest.mark.performance
class TestAPIPerformance:
    """Test API endpoint performance."""

    @pytest.mark.asyncio
    async def test_receipt_list_performance(
        self, async_client, auth_headers, sample_user
    ):
        """Test performance of receipt listing endpoint."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user

            # Mock large dataset
            receipts = []
            for i in range(100):
                receipts.append(
                    {
                        "receipt_id": str(uuid.uuid4()),
                        "user_id": sample_user.user_id,
                        "merchant_name": f"Merchant {i}",
                        "total_amount": f"{i * 10}.50",
                        "currency": "USD",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

            mock_service.get_receipts_by_user.return_value = {
                "receipts": receipts,
                "total": 100,
                "page": 1,
                "per_page": 100,
                "has_next": False,
            }

            # Measure response time
            start_time = time.time()
            response = await async_client.get("/api/v1/receipts/", headers=auth_headers)
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second

            data = response.json()
            assert len(data["receipts"]) == 100

    @pytest.mark.asyncio
    async def test_search_performance(self, async_client, auth_headers, sample_user):
        """Test search endpoint performance."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.search_service.search_service"
        ) as mock_service:

            mock_auth.return_value = sample_user

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

            mock_service.search_receipts.return_value = {
                "results": search_results,
                "total": 50,
                "query": "coffee",
                "page": 1,
                "per_page": 50,
            }

            # Measure search response time
            start_time = time.time()
            response = await async_client.get(
                "/api/v1/search/?q=coffee&per_page=50", headers=auth_headers
            )
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == 200
            assert response_time < 2.0  # Search should respond within 2 seconds

            data = response.json()
            assert len(data["results"]) == 50

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(
        self, async_client, auth_headers, sample_user
    ):
        """Test performance under concurrent load."""

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

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, async_client, auth_headers, sample_user):
        """Test memory efficiency with large datasets."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user

            # Mock progressively larger datasets
            for size in [10, 50, 100]:
                receipts = []
                for i in range(size):
                    receipts.append(
                        {
                            "receipt_id": str(uuid.uuid4()),
                            "user_id": sample_user.user_id,
                            "merchant_name": f"Merchant {i}",
                            "total_amount": f"{i}.50",
                            "currency": "USD",
                            "notes": "A" * 100,  # Add some data bulk
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                mock_service.get_receipts_by_user.return_value = {
                    "receipts": receipts,
                    "total": size,
                    "page": 1,
                    "per_page": size,
                    "has_next": False,
                }

                response = await async_client.get(
                    f"/api/v1/receipts/?per_page={size}", headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["receipts"]) == size


@pytest.mark.load
class TestLoadTesting:
    """Load testing scenarios."""

    @pytest.mark.asyncio
    async def test_sustained_load(self, async_client, auth_headers, sample_user):
        """Test sustained load over time."""

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
                    await asyncio.sleep(0.1)  # Small delay between requests

                return request_count

            request_count = await sustained_requests()

            # Should handle at least 40 requests in 5 seconds (8 RPS)
            assert request_count >= 40

    @pytest.mark.asyncio
    async def test_burst_load(self, async_client, auth_headers, sample_user):
        """Test handling burst of simultaneous requests."""

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

            async def make_burst_request():
                """Make a single burst request."""
                start_time = time.time()
                response = await async_client.get(
                    "/api/v1/receipts/", headers=auth_headers
                )
                end_time = time.time()
                return response.status_code, end_time - start_time

            # Create 20 simultaneous requests
            start_time = time.time()
            tasks = [make_burst_request() for _ in range(20)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = end_time - start_time

            # All requests should succeed
            status_codes = [result[0] for result in results]
            response_times = [result[1] for result in results]

            assert all(status == 200 for status in status_codes)

            # Average response time should be reasonable
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 1.0

            # Total time for burst should be reasonable
            assert total_time < 5.0


@pytest.mark.stress
class TestStressTesting:
    """Stress testing scenarios."""

    @pytest.mark.asyncio
    async def test_high_concurrency_stress(
        self, async_client, auth_headers, sample_user
    ):
        """Test high concurrency stress scenarios."""

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

            async def stress_worker():
                """Worker function for stress testing."""
                successes = 0
                failures = 0

                for _ in range(5):  # Each worker makes 5 requests
                    try:
                        response = await async_client.get(
                            "/api/v1/receipts/", headers=auth_headers
                        )
                        if response.status_code == 200:
                            successes += 1
                        else:
                            failures += 1
                    except Exception:
                        failures += 1

                    await asyncio.sleep(0.01)  # Very small delay

                return successes, failures

            # Run 50 concurrent workers
            start_time = time.time()
            tasks = [stress_worker() for _ in range(50)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = end_time - start_time

            total_successes = sum(result[0] for result in results)
            total_failures = sum(result[1] for result in results)

            # Should have high success rate (at least 90%)
            success_rate = total_successes / (total_successes + total_failures)
            assert success_rate >= 0.9

            # Should complete within reasonable time
            assert total_time < 10.0

    @pytest.mark.asyncio
    async def test_large_payload_stress(self, async_client, auth_headers, sample_user):
        """Test stress with large payloads."""

        with patch(
            "src.application.auth.middleware.get_current_active_user"
        ) as mock_auth, patch(
            "src.application.services.receipt_service.receipt_service"
        ) as mock_service:

            mock_auth.return_value = sample_user

            # Create large receipt data
            large_notes = "x" * 10000  # 10KB of notes

            receipt_data = {
                "image_id": str(uuid.uuid4()),
                "merchant_name": "Large Data Merchant",
                "total_amount": "1000.00",
                "currency": "USD",
                "notes": large_notes,
            }

            mock_service.create_receipt.return_value = {
                "receipt_id": str(uuid.uuid4()),
                "user_id": sample_user.user_id,
                **receipt_data,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Test creating multiple receipts with large payloads
            start_time = time.time()

            tasks = []
            for _ in range(5):
                task = async_client.post(
                    "/api/v1/receipts/", json=receipt_data, headers=auth_headers
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = end_time - start_time

            # All requests should succeed
            assert all(response.status_code == 201 for response in responses)

            # Should handle large payloads within reasonable time
            assert total_time < 5.0
