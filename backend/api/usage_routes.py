"""API endpoints for usage statistics."""

from fastapi import APIRouter, Request, HTTPException, Depends
from backend.core.usage import usage_tracker
from backend.core.fingerprint import get_user_id_from_request
from backend.api.auth_routes import get_optional_current_user
from backend.core.models import DBUser
from typing import Optional

router = APIRouter()


from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_session

@router.get("/usage")
async def get_usage(
    request: Request, 
    current_user: Optional[DBUser] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get current user's usage statistics."""
    user_id = current_user.id if current_user else get_user_id_from_request(request)
    stats = await usage_tracker.get_usage_stats(user_id, current_user, session)
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/health")
async def health_check():
    """Check if usage tracking service is healthy."""
    try:
        # Try to get stats for a test user
        stats = usage_tracker.get_usage_stats("health_check_test")
        return {"status": "healthy", "redis_connected": usage_tracker.redis is not None}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Usage tracking unhealthy: {e}")
