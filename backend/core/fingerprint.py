"""User identification and fingerprinting for usage tracking."""

from typing import Optional
from fastapi import Request
import hashlib
import json


def get_user_fingerprint(request: Request) -> str:
    """
    Generate a unique fingerprint for a user based on request data.
    
    Combines:
    - User-Agent header
    - IP address
    - Accept-Language header
    
    This provides reasonable user identification without cookies/accounts.
    Not perfect (VPN/incognito can reset) but good for free tier limits.
    """
    components = [
        request.headers.get("user-agent", "unknown"),
        request.client.host if request.client else "unknown",
        request.headers.get("accept-language", "en"),
    ]
    
    # Create hash from components
    fingerprint_data = "|".join(components)
    fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    return fingerprint


def get_user_id_from_request(request: Request) -> str:
    """
    Get user identifier from request.
    
    Priority:
    1. Authenticated user ID (from JWT token) - if logged in
    2. Browser fingerprint - for anonymous users
    """
    # TODO: Check for JWT token in Authorization header
    # For now, just use fingerprint
    return f"anon_{get_user_fingerprint(request)}"


def parse_fingerprint_header(fingerprint_header: Optional[str]) -> Optional[str]:
    """
    Parse fingerprint from custom X-Fingerprint header sent by frontend.
    
    Frontend can send a more sophisticated fingerprint using fingerprintjs.
    If available, use that. Otherwise fall back to server-side fingerprinting.
    """
    if not fingerprint_header:
        return None
    
    try:
        # Validate it's a reasonable hash
        if len(fingerprint_header) >= 8 and len(fingerprint_header) <= 64:
            return fingerprint_header
    except:
        pass
    
    return None
