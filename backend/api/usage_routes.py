"""API endpoints for usage statistics."""

from fastapi import APIRouter, Request, HTTPException
from backend.core.usage import usage_tracker
from backend.core.fingerprint import get_user_id_from_request

router = APIRouter()


@router.get("/usage")
async def get_usage(request: Request):
    """Get current user's usage statistics."""
    user_id = get_user_id_from_request(request)
    stats = usage_tracker.get_usage_stats(user_id)
    
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
