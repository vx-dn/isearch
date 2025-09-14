"""Test configuration and fixtures."""

import os
import sys
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add the backend directory to the Python path to allow imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from main import app  # noqa: E402
from src.application.services.receipt_service import ReceiptService  # noqa: E402
from src.application.services.search_service import SearchService  # noqa: E402
from src.application.services.user_service import UserService  # noqa: E402
from src.domain.entities.receipt import Receipt, ReceiptItem  # noqa: E402
from src.domain.entities.user import User  # noqa: E402
from src.infrastructure.config import InfrastructureConfig  # noqa: E402

# Remove the custom event_loop fixture as it's deprecated
# pytest-asyncio will provide the default one


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client() -> TestClient:
    """Create HTTP client for testing."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_infrastructure_config():
    """Mock infrastructure configuration."""
    config = Mock(spec=InfrastructureConfig)

    # Mock AWS services
    config.get_dynamodb_service.return_value = Mock()
    config.get_s3_service.return_value = Mock()
    config.get_textract_service.return_value = Mock()
    config.get_sqs_service.return_value = Mock()
    config.get_cognito_service.return_value = Mock()
    config.get_meilisearch_service.return_value = Mock()

    # Mock repositories
    config.get_user_repository.return_value = AsyncMock()
    config.get_receipt_repository.return_value = AsyncMock()
    config.get_search_repository.return_value = AsyncMock()

    return config


@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    from src.domain.entities.enums import UserRole

    return User(
        user_id=str(uuid.uuid4()),
        email="test@example.com",
        role=UserRole.FREE,
        image_count=0,
        image_quota=100,
        last_active_date=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_receipt_item() -> ReceiptItem:
    """Create a sample receipt item for testing."""
    return ReceiptItem(
        name="Coffee",
        category="Beverages",
        quantity=1,
        unit_price=Decimal("4.50"),
        total_price=Decimal("4.50"),
        metadata={"size": "large"},
    )


@pytest.fixture
def sample_receipt(sample_user, sample_receipt_item) -> Receipt:
    """Create a sample receipt for testing."""
    return Receipt(
        receipt_id=str(uuid.uuid4()),
        user_id=sample_user.user_id,
        image_id=str(uuid.uuid4()),
        merchant_name="Coffee Shop",
        merchant_address="123 Main St",
        purchase_date=datetime.now(timezone.utc),
        total_amount=Decimal("4.50"),
        currency="USD",
        receipt_type="food",
        raw_text="Coffee Shop Receipt...",
        confidence_score=0.95,
        items=[sample_receipt_item],
        tags=["coffee", "food"],
        notes="Morning coffee",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_user_service():
    """Mock user service."""
    service = Mock(spec=UserService)
    service.create_user = AsyncMock()
    service.get_user_by_id = AsyncMock()
    service.get_user_by_email = AsyncMock()
    service.update_user = AsyncMock()
    service.delete_user = AsyncMock()
    service.authenticate_user = AsyncMock()
    service.generate_tokens = AsyncMock()
    service.verify_token = AsyncMock()
    return service


@pytest.fixture
def mock_receipt_service():
    """Mock receipt service."""
    service = Mock(spec=ReceiptService)
    service.create_receipt = AsyncMock()
    service.get_receipt_by_id = AsyncMock()
    service.get_receipts_by_user = AsyncMock()
    service.update_receipt = AsyncMock()
    service.delete_receipt = AsyncMock()
    service.generate_upload_url = AsyncMock()
    service.process_receipt_image = AsyncMock()
    service.get_processing_status = AsyncMock()
    return service


@pytest.fixture
def mock_search_service():
    """Mock search service."""
    service = Mock(spec=SearchService)
    service.search_receipts = AsyncMock()
    service.search_by_merchant = AsyncMock()
    service.search_by_date_range = AsyncMock()
    service.search_by_amount_range = AsyncMock()
    service.search_by_tags = AsyncMock()
    service.get_search_suggestions = AsyncMock()
    service.get_popular_merchants = AsyncMock()
    service.get_popular_tags = AsyncMock()
    return service


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token for testing."""
    from datetime import datetime, timedelta

    import jwt

    payload = {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "type": "access",
    }

    # Use a test secret key
    return jwt.encode(payload, "test-secret-key", algorithm="HS256")


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


# Test data generators using Faker
@pytest.fixture
def fake_user_data():
    """Generate fake user data."""
    from faker import Faker

    fake = Faker()

    return {"email": fake.email(), "role": "free", "image_count": 0, "image_quota": 100}


@pytest.fixture
def fake_receipt_data():
    """Generate fake receipt data."""
    from faker import Faker

    fake = Faker()

    return {
        "merchant_name": fake.company(),
        "merchant_address": fake.address(),
        "purchase_date": fake.date_time_this_year(tzinfo=timezone.utc).isoformat(),
        "total_amount": float(
            fake.pydecimal(left_digits=3, right_digits=2, positive=True)
        ),
        "currency": fake.random_element(elements=("USD", "EUR", "GBP")),
        "receipt_type": fake.random_element(
            elements=(
                "grocery",
                "restaurant",
                "gas",
                "retail",
                "medical",
                "business",
                "other",
            )
        ),
        "notes": fake.sentence(),
    }
