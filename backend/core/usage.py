"""Usage tracking and limit enforcement for subscription system."""

from datetime import datetime, timedelta
from typing import Tuple, Optional
from enum import Enum
import redis
import os


# Plan definitions
class Plan(str, Enum):
    FREE_ANON = "free_anon"        # 5 PDFs/month, no account
    FREE_EMAIL = "free_email"       # 10 PDFs/month, with email
    STUDENT_MONTHLY = "student_monthly"   # 50 PDFs/month, $4.99
    STUDENT_ANNUAL = "student_annual"     # 50 PDFs/month, $35.99/year
    PRO_MONTHLY = "pro_monthly"     # Unlimited, $9.99
    PRO_ANNUAL = "pro_annual"       # Unlimited, $71.99/year


PLAN_LIMITS = {
    Plan.FREE_ANON: 5,
    Plan.FREE_EMAIL: 10,
    Plan.STUDENT_MONTHLY: 50,
    Plan.STUDENT_ANNUAL: 50,
    Plan.PRO_MONTHLY: -1,  # Unlimited
    Plan.PRO_ANNUAL: -1,   # Unlimited
}


class UsageTracker:
    """Track and enforce usage limits per user."""
    
    def __init__(self):
        """Initialize Redis connection."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
        except Exception as e:
            print(f"Warning: Redis not available: {e}")
            print("Using in-memory fallback (will reset on restart)")
            self.redis = None
            self._memory_store = {}
    
    def _get_month_key(self, user_id: str) -> str:
        """Generate Redis key for current month's usage."""
        month = datetime.now().strftime("%Y-%m")
        return f"usage:{user_id}:{month}"
    
    def _get_plan_key(self, user_id: str) -> str:
        """Generate Redis key for user's plan."""
        return f"plan:{user_id}"
    
    def get_user_plan(self, user_id: str) -> Plan:
        """Get user's current plan."""
        if self.redis:
            plan_str = self.redis.get(self._get_plan_key(user_id))
            if plan_str:
                try:
                    return Plan(plan_str)
                except ValueError:
                    pass
        else:
            # Memory fallback
            plan_str = self._memory_store.get(self._get_plan_key(user_id))
            if plan_str:
                return Plan(plan_str)
        
        # Default plan for anonymous users
        if user_id.startswith("anon_"):
            return Plan.FREE_ANON
        return Plan.FREE_EMAIL
    
    def set_user_plan(self, user_id: str, plan: Plan):
        """Set user's plan (after subscription)."""
        if self.redis:
            self.redis.set(self._get_plan_key(user_id), plan.value)
        else:
            self._memory_store[self._get_plan_key(user_id)] = plan.value
    
    def get_monthly_usage(self, user_id: str) -> int:
        """Get user's upload count this month."""
        month_key = self._get_month_key(user_id)
        
        if self.redis:
            usage = self.redis.get(month_key)
            return int(usage) if usage else 0
        else:
            return self._memory_store.get(month_key, 0)
    
    def can_upload(self, user_id: str) -> Tuple[bool, int, Plan]:
        """
        Check if user can upload.
        
        Returns:
            (can_upload, remaining_uploads, current_plan)
        """
        plan = self.get_user_plan(user_id)
        limit = PLAN_LIMITS[plan]
        
        # Unlimited plans
        if limit == -1:
            return True, -1, plan
        
        # Check usage
        usage = self.get_monthly_usage(user_id)
        remaining = limit - usage
        
        if remaining > 0:
            return True, remaining, plan
        else:
            return False, 0, plan
    
    def track_upload(self, user_id: str) -> int:
        """
        Track a PDF upload and return new usage count.
        
        Returns:
            Updated usage count for this month
        """
        month_key = self._get_month_key(user_id)
        
        if self.redis:
            # Increment counter
            new_count = self.redis.incr(month_key)
            
            # Set expiry at end of next month (auto-cleanup)
            if new_count == 1:  # First upload this month
                end_of_next_month = self._get_end_of_next_month()
                self.redis.expireat(month_key, int(end_of_next_month.timestamp()))
            
            return new_count
        else:
            # Memory fallback
            current = self._memory_store.get(month_key, 0)
            new_count = current + 1
            self._memory_store[month_key] = new_count
            return new_count
    
    def add_credits(self, user_id: str, count: int):
        """
        Add one-time credits (top-up purchases).
        
        This increases the user's limit for the current month only.
        """
        credits_key = f"credits:{user_id}:{datetime.now().strftime('%Y-%m')}"
        
        if self.redis:
            self.redis.incrby(credits_key, count)
            # Expire at end of next month
            end_of_next_month = self._get_end_of_next_month()
            self.redis.expireat(credits_key, int(end_of_next_month.timestamp()))
        else:
            current = self._memory_store.get(credits_key, 0)
            self._memory_store[credits_key] = current + count
    
    def get_credits(self, user_id: str) -> int:
        """Get user's one-time credits for this month."""
        credits_key = f"credits:{user_id}:{datetime.now().strftime('%Y-%m')}"
        
        if self.redis:
            credits = self.redis.get(credits_key)
            return int(credits) if credits else 0
        else:
            return self._memory_store.get(credits_key, 0)
    
    def get_usage_stats(self, user_id: str) -> dict:
        """Get comprehensive usage statistics for a user."""
        plan = self.get_user_plan(user_id)
        usage = self.get_monthly_usage(user_id)
        credits = self.get_credits(user_id)
        limit = PLAN_LIMITS[plan]
        
        # Calculate effective limit (plan limit + one-time credits)
        effective_limit = limit + credits if limit != -1 else -1
        effective_usage = usage
        effective_remaining = effective_limit - effective_usage if effective_limit != -1 else -1
        
        return {
            "plan": plan.value,
            "limit": limit,
            "usage": usage,
            "credits": credits,
            "effective_limit": effective_limit,
            "effective_remaining": effective_remaining,
            "is_unlimited": limit == -1,
            "can_upload": effective_remaining > 0 or limit == -1,
            "reset_date": self._get_next_month_start().isoformat()
        }
    
    def _get_end_of_next_month(self) -> datetime:
        """Get timestamp for end of next month (for Redis expiry)."""
        now = datetime.now()
        # Go to next month
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        
        # Go to month after that
        if next_month.month == 12:
            month_after = datetime(next_month.year + 1, 1, 1)
        else:
            month_after = datetime(next_month.year, next_month.month + 1, 1)
        
        return month_after
    
    def _get_next_month_start(self) -> datetime:
        """Get timestamp for start of next month (for UI display)."""
        now = datetime.now()
        if now.month == 12:
            return datetime(now.year + 1, 1, 1)
        else:
            return datetime(now.year, now.month + 1, 1)


# Global instance
usage_tracker = UsageTracker()
