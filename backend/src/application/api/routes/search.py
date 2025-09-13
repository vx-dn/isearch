"""Search API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.api.dto import (
    AmountRangeSearchRequest,
    DateRangeSearchRequest,
    SearchRequest,
    SearchResponse,
    TagSearchRequest,
)
from src.application.auth.middleware import get_current_active_user
from src.application.services.search_service import search_service
from src.domain.entities.user import User
from src.domain.exceptions import ValidationError

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_receipts(
    request: SearchRequest, current_user: User = Depends(get_current_active_user)
):
    """Search receipts using text query."""
    try:
        results = await search_service.search_receipts(current_user.user_id, request)
        return results
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/merchant/{merchant_name}", response_model=SearchResponse)
async def search_by_merchant(
    merchant_name: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
):
    """Search receipts by merchant name."""
    try:
        results = await search_service.search_by_merchant(
            current_user.user_id, merchant_name, limit, offset
        )
        return results
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/date-range", response_model=SearchResponse)
async def search_by_date_range(
    request: DateRangeSearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Search receipts by date range."""
    try:
        results = await search_service.search_by_date_range(
            current_user.user_id, request
        )
        return results
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/amount-range", response_model=SearchResponse)
async def search_by_amount_range(
    request: AmountRangeSearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Search receipts by amount range."""
    try:
        results = await search_service.search_by_amount_range(
            current_user.user_id, request
        )
        return results
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tags", response_model=SearchResponse)
async def search_by_tags(
    request: TagSearchRequest, current_user: User = Depends(get_current_active_user)
):
    """Search receipts by tags."""
    try:
        results = await search_service.search_by_tags(current_user.user_id, request)
        return results
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/suggestions", response_model=list[str])
async def get_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
):
    """Get search suggestions based on partial query."""
    try:
        suggestions = await search_service.get_suggestions(
            current_user.user_id, query, limit
        )
        return suggestions
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/popular-merchants", response_model=list[dict[str, Any]])
async def get_popular_merchants(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
):
    """Get popular merchants for user."""
    try:
        merchants = await search_service.get_popular_merchants(
            current_user.user_id, limit
        )
        return merchants
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/popular-tags", response_model=list[dict[str, Any]])
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """Get popular tags for user."""
    try:
        tags = await search_service.get_popular_tags(current_user.user_id, limit)
        return tags
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
