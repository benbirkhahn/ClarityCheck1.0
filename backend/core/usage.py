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
    
    # --- Redis / Memory Helpers (Anonymous) ---

    def _get_month_key(self, user_id: str) -> str:
        """Generate Redis key for current month's usage."""
        month = datetime.now().strftime("%Y-%m")
        return f"usage:{user_id}:{month}"
    
    def _get_credits_key(self, user_id: str) -> str:
        return f"credits:{user_id}:{datetime.now().strftime('%Y-%m')}"
    
    def _get_plan_key(self, user_id: str) -> str:
        return f"plan:{user_id}"

    # --- Core Logic ---

    def get_user_plan(self, user_id: str, db_user: Optional[object] = None) -> Plan:
        """Get user's current plan."""
        # 1. DB User
        if db_user:
            try:
                return Plan(db_user.plan)
            except ValueError:
                return Plan.FREE_EMAIL

        # 2. Redis/Memory (Anon)
        if self.redis:
            plan_str = self.redis.get(self._get_plan_key(user_id))
            if plan_str:
                try:
                    return Plan(plan_str)
                except ValueError:
                    pass
        else:
            plan_str = self._memory_store.get(self._get_plan_key(user_id))
            if plan_str:
                return Plan(plan_str)
        
        # Default
        if user_id.startswith("anon_"):
            return Plan.FREE_ANON
        return Plan.FREE_EMAIL
    
    async def set_user_plan(self, user_id: str, plan: Plan, session: Optional[object] = None):
        """Set user's plan (after subscription)."""
        # 1. DB User
        if session:
            # We need to fetch the user if not passed (or assume session is active)
            # But usually we'd pass the DB object. For now let's assume calling code handles DB update 
            # OR we execute a query here. 
            # BETTER: The caller (webhook) should update the user object directly.
            # But to keep interface confirming, let's try to update if session is passed.
            from backend.core.models import DBUser
            from sqlmodel import select
            
            statement = select(DBUser).where(DBUser.id == user_id)
            result = await session.execute(statement)
            user = result.scalar_one_or_none()
            if user:
                user.plan = plan.value
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return

        # 2. Redis/Memory (Anon or fallback)
        if self.redis:
            self.redis.set(self._get_plan_key(user_id), plan.value)
        else:
            self._memory_store[self._get_plan_key(user_id)] = plan.value
    
    def get_monthly_usage(self, user_id: str, db_user: Optional[object] = None) -> int:
        """Get user's upload count this month."""
        # 1. DB User
        if db_user:
            # Check if billing cycle reset is needed? 
            # For simplicity, we just return the stored value. 
            # The reset logic should happen on first access of new month, similar to Redis.
            
            # Simple check: if billing_cycle_start month != current month, usage is effectively 0
            # BUT we need to persist the reset.
            # For read-only (get), we can just return 0 if stale.
            now = datetime.utcnow()
            if (db_user.billing_cycle_start.month != now.month or 
                db_user.billing_cycle_start.year != now.year):
                return 0
            return db_user.monthly_usage

        # 2. Redis/Memory
        month_key = self._get_month_key(user_id)
        if self.redis:
            usage = self.redis.get(month_key)
            return int(usage) if usage else 0
        else:
            return self._memory_store.get(month_key, 0)
    
    async def can_upload(self, user_id: str, db_user: Optional[object] = None, session: Optional[object] = None) -> Tuple[bool, int, Plan]:
        """Check if user can upload. Handles reset logic for DB users."""
        # Admin bypass
        if db_user and getattr(db_user, 'is_admin', False):
            plan = self.get_user_plan(user_id, db_user)
            return True, -1, plan

        plan = self.get_user_plan(user_id, db_user)
        limit = PLAN_LIMITS[plan]
        
        # Unlimited
        if limit == -1:
            return True, -1, plan
        
        # Check usage
        usage = self.get_monthly_usage(user_id, db_user)
        
        # Check for DB reset (write operation if needed)
        if db_user and session:
            now = datetime.utcnow()
            if (db_user.billing_cycle_start.month != now.month or 
                db_user.billing_cycle_start.year != now.year):
                # Reset needed
                db_user.monthly_usage = 0
                db_user.billing_cycle_start = now
                session.add(db_user)
                await session.commit()
                usage = 0 # Updates local var
        
        remaining = limit - usage
        
        if remaining > 0:
            return True, remaining, plan
        else:
            return False, 0, plan
    
    async def track_upload(self, user_id: str, db_user: Optional[object] = None, session: Optional[object] = None) -> int:
        """Track upload. Updates DB or Redis."""
        # 1. DB User
        if db_user and session:
            # Ensure reset has happened (can_upload should have been called, but let's be safe)
            now = datetime.utcnow()
            if (db_user.billing_cycle_start.month != now.month or 
                db_user.billing_cycle_start.year != now.year):
                db_user.monthly_usage = 0
                db_user.billing_cycle_start = now
            
            db_user.monthly_usage += 1
            session.add(db_user)
            await session.commit()
            return db_user.monthly_usage

        # 2. Redis/Memory
        month_key = self._get_month_key(user_id)
        if self.redis:
            new_count = self.redis.incr(month_key)
            if new_count == 1:
                end_of_next_month = self._get_end_of_next_month()
                self.redis.expireat(month_key, int(end_of_next_month.timestamp()))
            return new_count
        else:
            current = self._memory_store.get(month_key, 0)
            new_count = current + 1
            self._memory_store[month_key] = new_count
            return new_count
    
    async def add_credits(self, user_id: str, count: int, session: Optional[object] = None):
        """Add one-time credits."""
        # 1. DB User
        if session:
            from backend.core.models import DBUser
            from sqlmodel import select
            statement = select(DBUser).where(DBUser.id == user_id)
            result = await session.execute(statement)
            user = result.scalar_one_or_none()
            if user:
                user.credits += count
                session.add(user)
                await session.commit()
                return

        # 2. Redis/Memory
        credits_key = self._get_credits_key(user_id)
        if self.redis:
            self.redis.incrby(credits_key, count)
            end_of_next_month = self._get_end_of_next_month()
            self.redis.expireat(credits_key, int(end_of_next_month.timestamp()))
        else:
            current = self._memory_store.get(credits_key, 0)
            self._memory_store[credits_key] = current + count
    
    def get_credits(self, user_id: str, db_user: Optional[object] = None) -> int:
        """Get user's one-time credits."""
        # 1. DB User
        if db_user:
            return db_user.credits

        # 2. Redis/Memory
        credits_key = self._get_credits_key(user_id)
        if self.redis:
            credits = self.redis.get(credits_key)
            return int(credits) if credits else 0
        else:
            return self._memory_store.get(credits_key, 0)
    
    async def get_usage_stats(self, user_id: str, db_user: Optional[object] = None, session: Optional[object] = None) -> dict:
        """Get comprehensive usage statistics."""
        # Ensure we trigger reset check if DB user
        if db_user and session:
             # Just running can_upload to trigger reset logic if needed
             await self.can_upload(user_id, db_user, session)
             await session.refresh(db_user)

        plan = self.get_user_plan(user_id, db_user)
        usage = self.get_monthly_usage(user_id, db_user)
        credits = self.get_credits(user_id, db_user)
        limit = PLAN_LIMITS[plan]
        is_admin = db_user and getattr(db_user, 'is_admin', False)
        
        if is_admin:
            effective_limit = -1
            effective_remaining = -1
        else:
            effective_limit = limit + credits if limit != -1 else -1
            effective_remaining = effective_limit - usage if effective_limit != -1 else -1
        
        return {
            "plan": "admin" if is_admin else plan.value,
            "limit": -1 if is_admin else limit,
            "usage": usage,
            "credits": credits,
            "effective_limit": effective_limit,
            "effective_remaining": effective_remaining,
            "is_unlimited": is_admin or limit == -1,
            "can_upload": is_admin or effective_remaining > 0 or limit == -1,
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
