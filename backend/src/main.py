"""FastAPI application setup and configuration."""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from application.api.dto import ErrorDetail, ErrorResponse
from application.api.routes import (
    auth_router,
    health_router,
    receipt_router,
    search_router,
)
from domain.exceptions import (
    DomainError,
    ReceiptNotFoundError,
    SearchError,
    UserNotFoundError,
    ValidationError,
)
from infrastructure.config import infrastructure_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Receipt Search API...")
    try:
        await infrastructure_config.initialize_services()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Receipt Search API...")
    try:
        infrastructure_config.cleanup()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# Create FastAPI app
app = FastAPI(
    title="Receipt Search API",
    description="API for receipt management and search functionality",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="ValidationError",
            message=str(exc),
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    """Handle user not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error="UserNotFound",
            message=str(exc),
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


@app.exception_handler(ReceiptNotFoundError)
async def receipt_not_found_handler(request: Request, exc: ReceiptNotFoundError):
    """Handle receipt not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error="ReceiptNotFound",
            message=str(exc),
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


@app.exception_handler(SearchError)
async def search_error_handler(request: Request, exc: SearchError):
    """Handle search errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="SearchError",
            message=str(exc),
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    """Handle domain errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="DomainError",
            message=str(exc),
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    error_details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
        error_details.append(
            ErrorDetail(field=field, message=error["msg"], error_code=error["type"])
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            details=error_details,
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPError",
            message=exc.detail,
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests."""
    import uuid

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Include routers
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(receipt_router, prefix="/api/v1/receipts", tags=["Receipts"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Receipt Search API", "version": "1.0.0", "docs": "/docs"}


if __name__ == "__main__":
    # Development server
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
