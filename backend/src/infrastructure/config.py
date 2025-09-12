"""Infrastructure configuration and service factory."""

import os
import logging
from typing import Optional

from src.infrastructure.aws.dynamodb_service import DynamoDBService
from src.infrastructure.aws.s3_service import S3Service
from src.infrastructure.aws.textract_service import TextractService
from src.infrastructure.aws.sqs_service import SQSService
from src.infrastructure.auth.cognito_service import CognitoService
from src.infrastructure.search.meilisearch_service import MeilisearchService

from src.infrastructure.repositories.dynamodb_receipt_repository import (
    DynamoDBReceiptRepository,
)
from src.infrastructure.repositories.dynamodb_user_repository import (
    DynamoDBUserRepository,
)
from src.infrastructure.repositories.meilisearch_search_repository import (
    MeilisearchSearchRepository,
)

from src.domain.config import DOMAIN_CONFIG

logger = logging.getLogger(__name__)


class InfrastructureConfig:
    """Infrastructure configuration and dependency injection container."""

    def __init__(self):
        """Initialize infrastructure configuration."""
        self._dynamodb_service: Optional[DynamoDBService] = None
        self._s3_service: Optional[S3Service] = None
        self._textract_service: Optional[TextractService] = None
        self._sqs_service: Optional[SQSService] = None
        self._cognito_service: Optional[CognitoService] = None
        self._meilisearch_service: Optional[MeilisearchService] = None

        # Repository instances
        self._receipt_repository: Optional[DynamoDBReceiptRepository] = None
        self._user_repository: Optional[DynamoDBUserRepository] = None
        self._search_repository: Optional[MeilisearchSearchRepository] = None

    def get_aws_region(self) -> str:
        """Get AWS region from environment or default."""
        return os.getenv("AWS_REGION", "ap-southeast-1")

    def get_dynamodb_service(self) -> DynamoDBService:
        """Get DynamoDB service instance."""
        if self._dynamodb_service is None:
            self._dynamodb_service = DynamoDBService(region_name=self.get_aws_region())
            logger.info("Initialized DynamoDB service")
        return self._dynamodb_service

    def get_s3_service(self) -> S3Service:
        """Get S3 service instance."""
        if self._s3_service is None:
            bucket_name = os.getenv("S3_BUCKET_NAME", DOMAIN_CONFIG.S3_BUCKET_NAME)
            self._s3_service = S3Service(region_name=self.get_aws_region())
            logger.info(f"Initialized S3 service with bucket: {bucket_name}")
        return self._s3_service

    def get_textract_service(self) -> TextractService:
        """Get Textract service instance."""
        if self._textract_service is None:
            self._textract_service = TextractService(region_name=self.get_aws_region())
            logger.info("Initialized Textract service")
        return self._textract_service

    def get_sqs_service(self) -> SQSService:
        """Get SQS service instance."""
        if self._sqs_service is None:
            self._sqs_service = SQSService(region_name=self.get_aws_region())
            logger.info("Initialized SQS service")
        return self._sqs_service

    def get_cognito_service(self) -> CognitoService:
        """Get Cognito service instance."""
        if self._cognito_service is None:
            user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
            client_id = os.getenv("COGNITO_CLIENT_ID")
            client_secret = os.getenv("COGNITO_CLIENT_SECRET")

            if not user_pool_id or not client_id:
                raise ValueError(
                    "Cognito configuration missing: COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID required"
                )

            self._cognito_service = CognitoService(
                user_pool_id=user_pool_id,
                client_id=client_id,
                client_secret=client_secret,
                region=self.get_aws_region(),
            )
            logger.info(f"Initialized Cognito service with user pool: {user_pool_id}")
        return self._cognito_service

    def get_meilisearch_service(self) -> MeilisearchService:
        """Get Meilisearch service instance."""
        if self._meilisearch_service is None:
            host = os.getenv("MEILISEARCH_HOST")
            api_key = os.getenv("MEILISEARCH_API_KEY")
            index_name = os.getenv(
                "MEILISEARCH_INDEX_NAME", DOMAIN_CONFIG.SEARCH_INDEX_NAME
            )

            if not host or not api_key:
                raise ValueError(
                    "Meilisearch configuration missing: MEILISEARCH_HOST and MEILISEARCH_API_KEY required"
                )

            self._meilisearch_service = MeilisearchService(
                host=host, api_key=api_key, index_name=index_name
            )
            logger.info(f"Initialized Meilisearch service at: {host}")
        return self._meilisearch_service

    def get_receipt_repository(self) -> DynamoDBReceiptRepository:
        """Get receipt repository instance."""
        if self._receipt_repository is None:
            dynamodb_service = self.get_dynamodb_service()
            self._receipt_repository = DynamoDBReceiptRepository(dynamodb_service)
            logger.info("Initialized DynamoDB receipt repository")
        return self._receipt_repository

    def get_user_repository(self) -> DynamoDBUserRepository:
        """Get user repository instance."""
        if self._user_repository is None:
            dynamodb_service = self.get_dynamodb_service()
            self._user_repository = DynamoDBUserRepository(dynamodb_service)
            logger.info("Initialized DynamoDB user repository")
        return self._user_repository

    def get_search_repository(self) -> MeilisearchSearchRepository:
        """Get search repository instance."""
        if self._search_repository is None:
            meilisearch_service = self.get_meilisearch_service()
            self._search_repository = MeilisearchSearchRepository(meilisearch_service)
            logger.info("Initialized Meilisearch search repository")
        return self._search_repository

    async def initialize_services(self):
        """Initialize all services and perform health checks."""
        try:
            logger.info("Initializing infrastructure services...")

            # Initialize AWS services
            dynamodb = self.get_dynamodb_service()
            s3 = self.get_s3_service()
            textract = self.get_textract_service()
            sqs = self.get_sqs_service()

            # Initialize repositories
            receipt_repo = self.get_receipt_repository()
            user_repo = self.get_user_repository()

            # Initialize search service (optional - may not be available in all environments)
            try:
                search_repo = self.get_search_repository()
                logger.info("Search service initialized successfully")
            except Exception as e:
                logger.warning(f"Search service initialization failed: {e}")

            # Initialize Cognito service (optional - may not be available in development)
            try:
                cognito = self.get_cognito_service()
                logger.info("Cognito service initialized successfully")
            except Exception as e:
                logger.warning(f"Cognito service initialization failed: {e}")

            logger.info("Infrastructure services initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize infrastructure services: {e}")
            raise

    async def health_check(self) -> dict:
        """Perform health check on all services."""
        health_status = {"status": "healthy", "services": {}}

        # Check DynamoDB
        try:
            dynamodb = self.get_dynamodb_service()
            # Try to describe a table to check connectivity
            health_status["services"]["dynamodb"] = "healthy"
        except Exception as e:
            health_status["services"]["dynamodb"] = f"unhealthy: {e}"
            health_status["status"] = "unhealthy"

        # Check S3
        try:
            s3 = self.get_s3_service()
            # Try to list bucket to check connectivity
            health_status["services"]["s3"] = "healthy"
        except Exception as e:
            health_status["services"]["s3"] = f"unhealthy: {e}"
            health_status["status"] = "unhealthy"

        # Check Textract
        try:
            textract = self.get_textract_service()
            health_status["services"]["textract"] = "healthy"
        except Exception as e:
            health_status["services"]["textract"] = f"unhealthy: {e}"
            health_status["status"] = "unhealthy"

        # Check SQS
        try:
            sqs = self.get_sqs_service()
            health_status["services"]["sqs"] = "healthy"
        except Exception as e:
            health_status["services"]["sqs"] = f"unhealthy: {e}"
            health_status["status"] = "unhealthy"

        # Check Meilisearch (optional)
        try:
            meilisearch = self.get_meilisearch_service()
            stats = await meilisearch.get_index_stats()
            health_status["services"]["meilisearch"] = "healthy"
        except Exception as e:
            health_status["services"]["meilisearch"] = f"unavailable: {e}"
            # Don't mark overall status as unhealthy for optional service

        # Check Cognito (optional)
        try:
            cognito = self.get_cognito_service()
            health_status["services"]["cognito"] = "healthy"
        except Exception as e:
            health_status["services"]["cognito"] = f"unavailable: {e}"
            # Don't mark overall status as unhealthy for optional service

        return health_status

    def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up infrastructure resources...")
        # Add any cleanup logic here if needed
        logger.info("Infrastructure cleanup completed")


# Global infrastructure configuration instance
infrastructure_config = InfrastructureConfig()
