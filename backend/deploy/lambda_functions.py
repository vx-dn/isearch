"""Lambda function handlers for the Receipt Search application."""

import json
import logging
import os
import sys
import asyncio
from typing import Dict, Any, Optional
from functools import lru_cache

# Add src to path for imports
sys.path.append("/opt/src")
sys.path.append("./src")

import boto3

# Import existing FastAPI services and DTOs
try:
    from src.application.services.user_service import UserService
    from src.application.services.receipt_service import ReceiptService
    from src.application.services.search_service import SearchService
    from src.application.api.dto import (
        UserCreateRequest,
        LoginRequest,
        ReceiptCreateRequest,
        SearchRequest,
        ForgotPasswordRequest,
        ResetPasswordRequest,
        ReceiptUpdateRequest,
        PaginationParams,
    )
    from src.domain.exceptions import (
        ValidationError,
        UserNotFoundError,
        ReceiptNotFoundError,
        AuthenticationError,
        AuthorizationError,
    )
except ImportError as e:
    logging.warning(f"Could not import FastAPI services: {e}")
    # Fallback imports for basic functionality
    UserService = None
    ReceiptService = None
    SearchService = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# AWS service clients (initialized once per container)
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
textract_client = boto3.client("textract")
sqs_client = boto3.client("sqs")
cognito_client = boto3.client("cognito-idp")

# Environment variables
RECEIPTS_TABLE = os.environ.get("RECEIPTS_TABLE")
USERS_TABLE = os.environ.get("USERS_TABLE")
RECEIPTS_BUCKET = os.environ.get("RECEIPTS_BUCKET")
PROCESSING_QUEUE_URL = os.environ.get("PROCESSING_QUEUE_URL")
MEILISEARCH_URL = os.environ.get("MEILISEARCH_URL")
MEILISEARCH_KEY = os.environ.get("MEILISEARCH_KEY")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")

# Global service instances (initialized once per container)
_user_service = None
_receipt_service = None
_search_service = None


# Service initialization with connection pooling and caching
@lru_cache(maxsize=1)
def get_user_service():
    """Get cached user service instance."""
    global _user_service
    if _user_service is None and UserService is not None:
        try:
            _user_service = UserService()
            logger.info("UserService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize UserService: {e}")
            _user_service = None
    return _user_service


@lru_cache(maxsize=1)
def get_receipt_service():
    """Get cached receipt service instance."""
    global _receipt_service
    if _receipt_service is None and ReceiptService is not None:
        try:
            _receipt_service = ReceiptService()
            logger.info("ReceiptService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ReceiptService: {e}")
            _receipt_service = None
    return _receipt_service


@lru_cache(maxsize=1)
def get_search_service():
    """Get cached search service instance."""
    global _search_service
    if _search_service is None and SearchService is not None:
        try:
            _search_service = SearchService()
            logger.info("SearchService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SearchService: {e}")
            _search_service = None
    return _search_service


def run_async(coro):
    """Helper to run async functions in Lambda."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


def api_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main API handler for all HTTP requests.
    Routes requests to appropriate functions based on path and method.
    Uses existing FastAPI services with Lambda optimizations.
    """
    try:
        # Extract request information
        http_method = event.get("httpMethod", "")
        path = event.get("path", "")
        headers = event.get("headers", {})
        body = event.get("body", "")
        query_params = event.get("queryStringParameters") or {}
        path_params = event.get("pathParameters") or {}

        logger.info(f"Processing {http_method} {path}")

        # Handle CORS preflight
        if http_method == "OPTIONS":
            return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}

        # Parse body if present
        request_body = {}
        if body:
            try:
                request_body = json.loads(body)
            except json.JSONDecodeError:
                return create_error_response(400, "Invalid JSON in request body")

        # Extract user context from headers (JWT/Cognito)
        user_context = extract_user_context(headers)

        # Route to appropriate handler
        if path.startswith("/api/v1/health") or path == "/health":
            return handle_health_check(event, context)
        elif path.startswith("/api/v1/auth"):
            return handle_auth(event, context, request_body, path, http_method)
        elif path.startswith("/api/v1/receipts"):
            return handle_receipts(
                event,
                context,
                request_body,
                path,
                http_method,
                query_params,
                path_params,
                user_context,
            )
        elif path.startswith("/api/v1/search"):
            return handle_search(
                event,
                context,
                request_body,
                path,
                http_method,
                query_params,
                user_context,
            )
        else:
            return create_error_response(404, "Endpoint not found")

    except Exception as e:
        logger.error(f"API handler error: {str(e)}", exc_info=True)
        return create_error_response(500, "Internal server error")


def image_processor_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process uploaded receipt images using existing ReceiptService.
    Triggered by S3 uploads, extracts metadata and queues for text extraction.
    """
    try:
        logger.info("Processing image upload event")

        receipt_service = get_receipt_service()
        if not receipt_service:
            logger.error("ReceiptService not available")
            raise Exception("Receipt service unavailable")

        # Parse S3 event
        for record in event.get("Records", []):
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
            event_name = record["eventName"]

            logger.info(f"Processing S3 event: {event_name} for s3://{bucket}/{key}")

            # Only process object creation events
            if not event_name.startswith("ObjectCreated"):
                logger.info(f"Skipping non-creation event: {event_name}")
                continue

            try:
                # Extract receipt ID and user ID from key
                # Expected format: receipts/{user_id}/{receipt_id}/original.{ext}
                key_parts = key.split("/")
                if len(key_parts) < 4 or key_parts[0] != "receipts":
                    logger.warning(f"Unexpected S3 key format: {key}")
                    continue

                user_id = key_parts[1]
                receipt_id = key_parts[2]

                logger.info(f"Processing receipt {receipt_id} for user {user_id}")

                # Use existing receipt service to handle image processing
                run_async(
                    receipt_service.process_uploaded_image(
                        receipt_id=receipt_id, user_id=user_id, bucket=bucket, key=key
                    )
                )

                logger.info(f"Image processing initiated for receipt {receipt_id}")

            except Exception as e:
                logger.error(f"Failed to process image {key}: {e}", exc_info=True)
                # Continue processing other records
                continue

        return {"statusCode": 200, "body": "Image processing completed"}

    except Exception as e:
        logger.error(f"Image processor error: {str(e)}", exc_info=True)
        raise


def text_extractor_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Extract text from receipt images using existing ReceiptService + Textract.
    Triggered by SQS messages from image processor.
    """
    try:
        logger.info("Processing text extraction job")

        receipt_service = get_receipt_service()
        if not receipt_service:
            logger.error("ReceiptService not available")
            raise Exception("Receipt service unavailable")

        # Parse SQS event
        for record in event.get("Records", []):
            try:
                message_body = json.loads(record["body"])
                receipt_id = message_body.get("receipt_id")
                user_id = message_body.get("user_id")
                bucket = message_body.get("bucket")
                key = message_body.get("key")
                action = message_body.get("action")

                if action != "extract_text":
                    logger.warning(f"Unexpected action: {action}")
                    continue

                if not all([receipt_id, bucket, key]):
                    logger.error(f"Missing required fields in message: {message_body}")
                    continue

                logger.info(f"Extracting text from: s3://{bucket}/{key}")

                # Use existing receipt service for text extraction
                result = run_async(
                    receipt_service.extract_text_from_receipt(
                        receipt_id=receipt_id, user_id=user_id, bucket=bucket, key=key
                    )
                )

                logger.info(f"Text extraction completed for receipt {receipt_id}")

                # Index in search service if available
                search_service = get_search_service()
                if search_service and result.get("extracted_text"):
                    try:
                        run_async(
                            search_service.index_receipt(
                                receipt_id=receipt_id,
                                user_id=user_id,
                                text_content=result["extracted_text"],
                                metadata=result.get("metadata", {}),
                            )
                        )
                        logger.info(f"Receipt {receipt_id} indexed in search")
                    except Exception as e:
                        logger.warning(f"Failed to index receipt {receipt_id}: {e}")

            except Exception as e:
                logger.error(f"Failed to process message: {e}", exc_info=True)
                # Continue processing other messages
                continue

        return {"statusCode": 200, "body": "Text extraction completed"}

    except Exception as e:
        logger.error(f"Text extractor error: {str(e)}", exc_info=True)
        raise


def cleanup_worker_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Clean up expired receipts and unused files using existing services.
    Triggered by CloudWatch Events (scheduled).
    """
    try:
        logger.info("Starting cleanup process")

        receipt_service = get_receipt_service()
        user_service = get_user_service()

        cleanup_stats = {
            "expired_receipts": 0,
            "orphaned_files": 0,
            "cleaned_users": 0,
            "errors": 0,
        }

        # Cleanup expired receipts based on user subscription tiers
        if receipt_service:
            try:
                result = run_async(receipt_service.cleanup_expired_receipts())
                cleanup_stats["expired_receipts"] = result.get("cleaned_count", 0)
                logger.info(
                    f"Cleaned up {cleanup_stats['expired_receipts']} expired receipts"
                )
            except Exception as e:
                logger.error(f"Failed to cleanup expired receipts: {e}")
                cleanup_stats["errors"] += 1

        # Cleanup orphaned S3 objects
        try:
            orphaned_count = cleanup_orphaned_s3_objects()
            cleanup_stats["orphaned_files"] = orphaned_count
            logger.info(f"Cleaned up {orphaned_count} orphaned S3 objects")
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned S3 objects: {e}")
            cleanup_stats["errors"] += 1

        # Cleanup inactive users (if needed)
        if user_service:
            try:
                result = run_async(user_service.cleanup_inactive_users())
                cleanup_stats["cleaned_users"] = result.get("cleaned_count", 0)
                logger.info(
                    f"Cleaned up {cleanup_stats['cleaned_users']} inactive users"
                )
            except Exception as e:
                logger.error(f"Failed to cleanup inactive users: {e}")
                cleanup_stats["errors"] += 1

        # Cleanup old CloudWatch logs (if configured)
        try:
            log_cleanup_count = cleanup_old_logs()
            cleanup_stats["cleaned_logs"] = log_cleanup_count
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            cleanup_stats["errors"] += 1

        logger.info(f"Cleanup completed. Stats: {cleanup_stats}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Cleanup completed", "stats": cleanup_stats}
            ),
        }

    except Exception as e:
        logger.error(f"Cleanup worker error: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Cleanup failed", "error": str(e)}),
        }


def cleanup_orphaned_s3_objects() -> int:
    """Clean up S3 objects that don't have corresponding database records."""
    try:
        if not RECEIPTS_BUCKET:
            return 0

        cleaned_count = 0
        receipts_table = dynamodb.Table(RECEIPTS_TABLE)

        # List objects in S3 bucket
        paginator = s3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=RECEIPTS_BUCKET, Prefix="receipts/"):
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]

                # Extract receipt ID from key
                try:
                    key_parts = key.split("/")
                    if len(key_parts) >= 3:
                        receipt_id = key_parts[2]

                        # Check if receipt exists in database
                        response = receipts_table.get_item(
                            Key={"receipt_id": receipt_id},
                            ProjectionExpression="receipt_id",
                        )

                        if "Item" not in response:
                            # Orphaned file - delete it
                            s3_client.delete_object(Bucket=RECEIPTS_BUCKET, Key=key)
                            cleaned_count += 1
                            logger.info(f"Deleted orphaned S3 object: {key}")

                except Exception as e:
                    logger.warning(f"Failed to process S3 object {key}: {e}")
                    continue

        return cleaned_count

    except Exception as e:
        logger.error(f"S3 cleanup error: {e}")
        return 0


def cleanup_old_logs() -> int:
    """Clean up old CloudWatch log streams."""
    try:
        logs_client = boto3.client("logs")
        cleaned_count = 0

        # List log groups for this application
        log_groups = [
            f"/aws/lambda/receipt-search-{os.environ.get('ENVIRONMENT', 'dev')}-api",
            f"/aws/lambda/receipt-search-{os.environ.get('ENVIRONMENT', 'dev')}-image-processor",
            f"/aws/lambda/receipt-search-{os.environ.get('ENVIRONMENT', 'dev')}-text-extractor",
            f"/aws/lambda/receipt-search-{os.environ.get('ENVIRONMENT', 'dev')}-cleanup-worker",
        ]

        # Calculate cutoff date (30 days ago)
        import time

        cutoff_time = int(
            (time.time() - 30 * 24 * 60 * 60) * 1000
        )  # 30 days in milliseconds

        for log_group in log_groups:
            try:
                # List old log streams
                paginator = logs_client.get_paginator("describe_log_streams")

                for page in paginator.paginate(
                    logGroupName=log_group, orderBy="LastEventTime"
                ):
                    for stream in page.get("logStreams", []):
                        if stream.get("lastEventTime", 0) < cutoff_time:
                            try:
                                logs_client.delete_log_stream(
                                    logGroupName=log_group,
                                    logStreamName=stream["logStreamName"],
                                )
                                cleaned_count += 1
                            except Exception as e:
                                logger.warning(
                                    f"Failed to delete log stream {stream['logStreamName']}: {e}"
                                )

            except logs_client.exceptions.ResourceNotFoundException:
                # Log group doesn't exist, skip
                continue
            except Exception as e:
                logger.warning(f"Failed to cleanup logs for {log_group}: {e}")
                continue

        return cleaned_count

    except Exception as e:
        logger.error(f"Log cleanup error: {e}")
        return 0


# Remove the old placeholder function
def index_in_meilisearch(receipt_id: str, text: str) -> None:
    """Index receipt text in Meilisearch (deprecated - use SearchService instead)."""
    logger.warning("index_in_meilisearch is deprecated, use SearchService instead")
    pass


# Helper functions
def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for API responses."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Content-Type": "application/json",
    }


def create_error_response(
    status_code: int, message: str, details: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized error response matching FastAPI format."""
    error_body = {"error": message}
    if details:
        error_body["details"] = details

    return {
        "statusCode": status_code,
        "headers": get_cors_headers(),
        "body": json.dumps(error_body),
    }


def create_success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """Create standardized success response matching FastAPI format."""
    # Handle Pydantic models
    if hasattr(data, "dict"):
        body = data.dict()
    elif hasattr(data, "model_dump"):
        body = data.model_dump()
    else:
        body = data

    return {
        "statusCode": status_code,
        "headers": get_cors_headers(),
        "body": json.dumps(body, default=str),  # default=str handles datetime objects
    }


def extract_user_context(headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Extract user context from headers (JWT/Cognito token)."""
    try:
        # Look for Authorization header
        auth_header = headers.get("Authorization") or headers.get("authorization")
        if not auth_header:
            return None

        # Extract JWT token
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # TODO: Validate JWT token with Cognito
            # For now, return basic context
            return {"token": token, "authenticated": True}

        return None
    except Exception as e:
        logger.warning(f"Failed to extract user context: {e}")
        return None


def require_auth(user_context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Check if user is authenticated, return error response if not."""
    if not user_context or not user_context.get("authenticated"):
        return create_error_response(401, "Authentication required")
    return None


def handle_health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle health check endpoints."""
    path = event.get("path", "")

    if path.endswith("/health") or path == "/health":
        return create_success_response(
            {
                "status": "healthy",
                "timestamp": context.aws_request_id,
                "version": "1.0.0",
                "environment": os.environ.get("ENVIRONMENT", "dev"),
            }
        )

    return create_error_response(404, "Health endpoint not found")


def handle_auth(
    event: Dict[str, Any], context: Any, body: Dict[str, Any], path: str, method: str
) -> Dict[str, Any]:
    """Handle authentication endpoints using Cognito + UserService."""
    try:
        user_service = get_user_service()
        if not user_service:
            return create_error_response(503, "User service unavailable")

        # Extract endpoint from path
        endpoint = path.replace("/api/v1/auth", "").strip("/")

        if method == "POST" and endpoint == "register":
            return handle_user_registration(user_service, body)
        elif method == "POST" and endpoint == "login":
            return handle_user_login(user_service, body)
        elif method == "POST" and endpoint == "forgot-password":
            return handle_forgot_password(user_service, body)
        elif method == "POST" and endpoint == "reset-password":
            return handle_reset_password(user_service, body)
        elif method == "GET" and endpoint == "profile":
            user_context = extract_user_context(event.get("headers", {}))
            auth_error = require_auth(user_context)
            if auth_error:
                return auth_error
            return handle_get_profile(user_service, user_context)
        else:
            return create_error_response(
                404, f"Auth endpoint not found: {method} {endpoint}"
            )

    except ValidationError as e:
        return create_error_response(400, str(e))
    except AuthenticationError as e:
        return create_error_response(401, str(e))
    except Exception as e:
        logger.error(f"Auth handler error: {e}", exc_info=True)
        return create_error_response(500, "Authentication service error")


def handle_user_registration(user_service, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user registration."""
    try:
        # Validate request
        if not body.get("email") or not body.get("password"):
            return create_error_response(400, "Email and password are required")

        # Create request object
        request = UserCreateRequest(**body)

        # Register user using existing service
        result = run_async(user_service.register_user(request))

        return create_success_response(result, 201)

    except ValidationError as e:
        return create_error_response(400, str(e))
    except Exception as e:
        if "already exists" in str(e).lower():
            return create_error_response(409, "Email already registered")
        raise


def handle_user_login(user_service, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user login."""
    try:
        # Validate request
        if not body.get("email") or not body.get("password"):
            return create_error_response(400, "Email and password are required")

        # Create request object
        request = LoginRequest(**body)

        # Login user using existing service
        result = run_async(user_service.login_user(request))

        return create_success_response(result)

    except AuthenticationError as e:
        return create_error_response(401, str(e))
    except ValidationError as e:
        return create_error_response(400, str(e))


def handle_forgot_password(user_service, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle forgot password request."""
    try:
        if not body.get("email"):
            return create_error_response(400, "Email is required")

        request = ForgotPasswordRequest(**body)
        run_async(user_service.forgot_password(request))

        return create_success_response({"message": "Password reset email sent"})

    except UserNotFoundError as e:
        return create_error_response(404, str(e))
    except ValidationError as e:
        return create_error_response(400, str(e))


def handle_reset_password(user_service, body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle password reset."""
    try:
        required_fields = ["email", "reset_code", "new_password"]
        for field in required_fields:
            if not body.get(field):
                return create_error_response(400, f"{field} is required")

        request = ResetPasswordRequest(**body)
        run_async(user_service.reset_password(request))

        return create_success_response({"message": "Password reset successful"})

    except ValidationError as e:
        return create_error_response(400, str(e))
    except AuthenticationError as e:
        return create_error_response(401, str(e))


def handle_get_profile(user_service, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user profile."""
    try:
        # Extract user ID from token (simplified for now)
        user_id = user_context.get("user_id")  # TODO: Extract from JWT
        if not user_id:
            return create_error_response(400, "Unable to identify user")

        result = run_async(user_service.get_user_profile(user_id))
        return create_success_response(result)

    except UserNotFoundError as e:
        return create_error_response(404, str(e))
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return create_error_response(500, "Failed to get user profile")


def handle_receipts(
    event: Dict[str, Any],
    context: Any,
    body: Dict[str, Any],
    path: str,
    method: str,
    query_params: Dict[str, Any],
    path_params: Dict[str, Any],
    user_context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Handle receipt management endpoints using ReceiptService."""
    try:
        # Require authentication for all receipt endpoints
        auth_error = require_auth(user_context)
        if auth_error:
            return auth_error

        receipt_service = get_receipt_service()
        if not receipt_service:
            return create_error_response(503, "Receipt service unavailable")

        # Extract endpoint from path
        endpoint_parts = path.replace("/api/v1/receipts", "").strip("/").split("/")
        endpoint = endpoint_parts[0] if endpoint_parts and endpoint_parts[0] else ""
        receipt_id = endpoint_parts[1] if len(endpoint_parts) > 1 else None

        # Route to specific handlers
        if method == "GET" and not endpoint:
            return handle_list_receipts(receipt_service, query_params, user_context)
        elif method == "POST" and not endpoint:
            return handle_create_receipt(receipt_service, body, user_context)
        elif method == "GET" and receipt_id:
            return handle_get_receipt(receipt_service, receipt_id, user_context)
        elif method == "PUT" and receipt_id:
            return handle_update_receipt(
                receipt_service, receipt_id, body, user_context
            )
        elif method == "DELETE" and receipt_id:
            return handle_delete_receipt(receipt_service, receipt_id, user_context)
        elif method == "POST" and endpoint == "upload":
            return handle_upload_request(receipt_service, body, user_context)
        elif method == "GET" and endpoint and endpoint.endswith("status"):
            status_receipt_id = endpoint.replace("/status", "")
            return handle_processing_status(
                receipt_service, status_receipt_id, user_context
            )
        else:
            return create_error_response(
                404, f"Receipt endpoint not found: {method} {path}"
            )

    except ValidationError as e:
        return create_error_response(400, str(e))
    except ReceiptNotFoundError as e:
        return create_error_response(404, str(e))
    except AuthorizationError as e:
        return create_error_response(403, str(e))
    except Exception as e:
        logger.error(f"Receipt handler error: {e}", exc_info=True)
        return create_error_response(500, "Receipt service error")


def handle_list_receipts(
    receipt_service, query_params: Dict[str, Any], user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle listing user receipts with pagination."""
    try:
        # Extract user ID (TODO: from JWT)
        user_id = user_context.get("user_id", "default-user-id")

        # Parse pagination parameters
        page = int(query_params.get("page", 1))
        page_size = int(query_params.get("page_size", 20))
        sort_by = query_params.get("sort_by", "created_at")
        sort_order = query_params.get("sort_order", "desc")

        # Additional filters
        merchant = query_params.get("merchant")
        category = query_params.get("category")
        date_from = query_params.get("date_from")
        date_to = query_params.get("date_to")

        pagination = PaginationParams(
            page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
        )

        result = run_async(
            receipt_service.get_user_receipts(
                user_id, pagination, merchant, category, date_from, date_to
            )
        )

        return create_success_response(result)

    except ValidationError as e:
        return create_error_response(400, str(e))


def handle_create_receipt(
    receipt_service, body: Dict[str, Any], user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle creating a new receipt."""
    try:
        # Extract user ID
        user_id = user_context.get("user_id", "default-user-id")

        # Add user_id to request
        body["user_id"] = user_id

        request = ReceiptCreateRequest(**body)
        result = run_async(receipt_service.create_receipt(request))

        return create_success_response(result, 201)

    except ValidationError as e:
        return create_error_response(400, str(e))


def handle_get_receipt(
    receipt_service, receipt_id: str, user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle getting a specific receipt."""
    try:
        user_id = user_context.get("user_id", "default-user-id")

        result = run_async(receipt_service.get_receipt(receipt_id, user_id))
        return create_success_response(result)

    except ReceiptNotFoundError as e:
        return create_error_response(404, str(e))


def handle_update_receipt(
    receipt_service, receipt_id: str, body: Dict[str, Any], user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle updating a receipt."""
    try:
        user_id = user_context.get("user_id", "default-user-id")

        request = ReceiptUpdateRequest(**body)
        result = run_async(receipt_service.update_receipt(receipt_id, request, user_id))

        return create_success_response(result)

    except ValidationError as e:
        return create_error_response(400, str(e))
    except ReceiptNotFoundError as e:
        return create_error_response(404, str(e))


def handle_delete_receipt(
    receipt_service, receipt_id: str, user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle deleting a receipt."""
    try:
        user_id = user_context.get("user_id", "default-user-id")

        run_async(receipt_service.delete_receipt(receipt_id, user_id))
        return create_success_response({"message": "Receipt deleted successfully"})

    except ReceiptNotFoundError as e:
        return create_error_response(404, str(e))


def handle_upload_request(
    receipt_service, body: Dict[str, Any], user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle receipt image upload request (presigned URL)."""
    try:
        user_id = user_context.get("user_id", "default-user-id")

        filename = body.get("filename")
        content_type = body.get("content_type", "image/jpeg")

        if not filename:
            return create_error_response(400, "Filename is required")

        result = run_async(
            receipt_service.generate_upload_url(user_id, filename, content_type)
        )
        return create_success_response(result)

    except ValidationError as e:
        return create_error_response(400, str(e))


def handle_processing_status(
    receipt_service, receipt_id: str, user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle getting receipt processing status."""
    try:
        user_id = user_context.get("user_id", "default-user-id")

        result = run_async(receipt_service.get_processing_status(receipt_id, user_id))
        return create_success_response(result)

    except ReceiptNotFoundError as e:
        return create_error_response(404, str(e))


def handle_search(
    event: Dict[str, Any],
    context: Any,
    body: Dict[str, Any],
    path: str,
    method: str,
    query_params: Dict[str, Any],
    user_context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Handle search endpoints using SearchService."""
    try:
        # Require authentication for search
        auth_error = require_auth(user_context)
        if auth_error:
            return auth_error

        search_service = get_search_service()
        if not search_service:
            return create_error_response(503, "Search service unavailable")

        # Extract endpoint from path
        endpoint = path.replace("/api/v1/search", "").strip("/")
        user_id = user_context.get("user_id", "default-user-id")

        if method == "GET" and (not endpoint or endpoint == "receipts"):
            return handle_search_receipts(search_service, query_params, user_id)
        elif method == "POST" and endpoint == "receipts":
            return handle_advanced_search(search_service, body, user_id)
        elif method == "GET" and endpoint == "suggestions":
            return handle_search_suggestions(search_service, query_params, user_id)
        elif method == "GET" and endpoint == "stats":
            return handle_search_stats(search_service, user_id)
        else:
            return create_error_response(
                404, f"Search endpoint not found: {method} {endpoint}"
            )

    except ValidationError as e:
        return create_error_response(400, str(e))
    except Exception as e:
        logger.error(f"Search handler error: {e}", exc_info=True)
        return create_error_response(500, "Search service error")


def handle_search_receipts(
    search_service, query_params: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle basic receipt search."""
    try:
        query = query_params.get("q", "")
        page = int(query_params.get("page", 1))
        page_size = int(query_params.get("page_size", 20))

        # Additional filters
        merchant = query_params.get("merchant")
        category = query_params.get("category")
        date_from = query_params.get("date_from")
        date_to = query_params.get("date_to")
        min_amount = query_params.get("min_amount")
        max_amount = query_params.get("max_amount")

        # Build search parameters
        search_params = {
            "query": query,
            "user_id": user_id,
            "page": page,
            "page_size": page_size,
        }

        # Add filters if provided
        if merchant:
            search_params["merchant"] = merchant
        if category:
            search_params["category"] = category
        if date_from:
            search_params["date_from"] = date_from
        if date_to:
            search_params["date_to"] = date_to
        if min_amount:
            search_params["min_amount"] = float(min_amount)
        if max_amount:
            search_params["max_amount"] = float(max_amount)

        result = run_async(search_service.search_receipts(**search_params))
        return create_success_response(result)

    except ValidationError as e:
        return create_error_response(400, str(e))
    except ValueError as e:
        return create_error_response(400, f"Invalid parameter: {e}")


def handle_advanced_search(
    search_service, body: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle advanced search with complex filters."""
    try:
        # Add user_id to search request
        body["user_id"] = user_id

        request = SearchRequest(**body)
        result = run_async(search_service.advanced_search(request))

        return create_success_response(result)

    except ValidationError as e:
        return create_error_response(400, str(e))


def handle_search_suggestions(
    search_service, query_params: Dict[str, Any], user_id: str
) -> Dict[str, Any]:
    """Handle search suggestions/autocomplete."""
    try:
        query = query_params.get("q", "")
        suggestion_type = query_params.get(
            "type", "all"
        )  # merchants, categories, items, all

        if not query:
            return create_error_response(400, "Query parameter 'q' is required")

        result = run_async(
            search_service.get_suggestions(user_id, query, suggestion_type)
        )
        return create_success_response(result)

    except ValidationError as e:
        return create_error_response(400, str(e))


def handle_search_stats(search_service, user_id: str) -> Dict[str, Any]:
    """Handle getting user's search and spending statistics."""
    try:
        result = run_async(search_service.get_user_stats(user_id))
        return create_success_response(result)

    except Exception as e:
        logger.error(f"Search stats error: {e}")
        return create_error_response(500, "Failed to get search statistics")
