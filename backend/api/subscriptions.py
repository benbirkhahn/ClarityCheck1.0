from fastapi import APIRouter, HTTPException, Request
from backend.core.config import settings
import stripe
from backend.core.usage import usage_tracker
from backend.core.fingerprint import get_user_id_from_request
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

class CheckoutSessionRequest(BaseModel):
    price_id: str
    user_id: Optional[str] = None

@router.post("/create-checkout-session")
async def create_checkout_session(request: Request, data: CheckoutSessionRequest):
    try:
        user_id = data.user_id or get_user_id_from_request(request)
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': data.price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription', # or 'payment' for one-time
            success_url=f"{settings.CORS_ORIGINS[0]}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.CORS_ORIGINS[0]}/cancel",
            client_reference_id=user_id,
            metadata={
                "user_id": user_id 
            }
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
