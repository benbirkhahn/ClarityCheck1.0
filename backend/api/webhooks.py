from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_session
from backend.core.config import settings
from backend.core.usage import usage_tracker, Plan
import stripe
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/webhook")
async def stripe_webhook(
    request: Request, 
    stripe_signature: str = Header(None),
    db_session: AsyncSession = Depends(get_session)
):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_checkout_completed(session, db_session)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        # handle_subscription_updated(subscription)
        pass # Todo: Handle recurring payments if logic differs
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # handle_subscription_deleted(subscription)
        pass # Todo: Downgrade user

    return {"status": "success"}

async def handle_checkout_completed(session, db_session: AsyncSession):
    user_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")
    
    if not user_id:
        logger.error("No user_id found in session")
        return

    # Determine what they bought
    # logic depends on your Price setup. 
    # For now, let's assume metadata 'plan' or line items.
    # In a real app, you'd match Price ID to Plan.
    
    # Simple logic: If mode is subscription, set to PRO_MONTHLY (default for now)
    # If mode is payment, add credits.
    
    mode = session.get("mode")
    if mode == "subscription":
        # TODO: Map price_id to actual plan (Student vs Pro)
        # For prototype, we'll look at the price amount or ID if needed, 
        # but let's just default to PRO_MONTHLY for testing first cycle.
        await usage_tracker.set_user_plan(user_id, Plan.PRO_MONTHLY, db_session)
        logger.info(f"Upgraded user {user_id} to PRO_MONTHLY")
        
    elif mode == "payment":
        # One-time payment (credits)
        amount_total = session.get("amount_total")
        # Example: $2.99 (299 cents) = 10 credits
        if amount_total == 299:
             await usage_tracker.add_credits(user_id, 10, db_session)
             logger.info(f"Added 10 credits to user {user_id}")
        elif amount_total == 499:
             await usage_tracker.add_credits(user_id, 25, db_session)
             logger.info(f"Added 25 credits to user {user_id}")
