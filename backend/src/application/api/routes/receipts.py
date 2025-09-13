"""Receipt API routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.application.api.dto import (
    ReceiptCreateRequest,
    ReceiptUpdateRequest,
    ReceiptResponse,
    ReceiptListResponse,
    ImageUploadResponse,
    ImageProcessingStatusResponse,
    PaginationParams,
    SuccessResponse,
)
from src.application.services.receipt_service import receipt_service
from src.application.auth.middleware import get_current_active_user
from src.domain.entities.user import User
from src.domain.exceptions import ValidationError, ReceiptNotFoundError

router = APIRouter()


@router.post("/", response_model=ReceiptResponse)
async def create_receipt(
    request: ReceiptCreateRequest, current_user: User = Depends(get_current_active_user)
):
    """Create a new receipt manually."""
    try:
        receipt = await receipt_service.create_receipt(current_user.user_id, request)
        return receipt
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=ReceiptListResponse)
async def list_receipts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """List receipts for current user."""
    try:
        pagination = PaginationParams(page=page, page_size=page_size)
        receipts = await receipt_service.list_receipts(current_user.user_id, pagination)
        return receipts
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: str, current_user: User = Depends(get_current_active_user)
):
    """Get a specific receipt."""
    try:
        receipt = await receipt_service.get_receipt(receipt_id, current_user.user_id)
        return receipt
    except ReceiptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    receipt_id: str,
    request: ReceiptUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update a receipt."""
    try:
        receipt = await receipt_service.update_receipt(
            receipt_id, current_user.user_id, request
        )
        return receipt
    except ReceiptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{receipt_id}", response_model=SuccessResponse)
async def delete_receipt(
    receipt_id: str, current_user: User = Depends(get_current_active_user)
):
    """Delete a receipt."""
    try:
        success = await receipt_service.delete_receipt(receipt_id, current_user.user_id)
        return SuccessResponse(success=success, message="Receipt deleted successfully")
    except ReceiptNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/upload-url", response_model=ImageUploadResponse)
async def generate_upload_url(current_user: User = Depends(get_current_active_user)):
    """Generate presigned URL for image upload."""
    try:
        upload_response = await receipt_service.generate_upload_url(
            current_user.user_id
        )
        return upload_response
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/process-image/{image_id}", response_model=ImageProcessingStatusResponse)
async def process_image(
    image_id: str, current_user: User = Depends(get_current_active_user)
):
    """Process uploaded image and extract receipt data."""
    try:
        status_response = await receipt_service.process_uploaded_image(
            current_user.user_id, image_id
        )
        return status_response
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/processing-status/{image_id}", response_model=ImageProcessingStatusResponse
)
async def get_processing_status(
    image_id: str, current_user: User = Depends(get_current_active_user)
):
    """Get image processing status."""
    try:
        status_response = await receipt_service.get_processing_status(
            current_user.user_id, image_id
        )
        return status_response
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/by-date-range/", response_model=ReceiptListResponse)
async def get_receipts_by_date_range(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """Get receipts by date range."""
    try:
        pagination = PaginationParams(page=page, page_size=page_size)
        receipts = await receipt_service.get_receipts_by_date_range(
            current_user.user_id, start_date, end_date, pagination
        )
        return receipts
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/by-merchant/", response_model=ReceiptListResponse)
async def get_receipts_by_merchant(
    merchant_name: str = Query(..., description="Merchant name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """Get receipts by merchant."""
    try:
        pagination = PaginationParams(page=page, page_size=page_size)
        receipts = await receipt_service.get_receipts_by_merchant(
            current_user.user_id, merchant_name, pagination
        )
        return receipts
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
