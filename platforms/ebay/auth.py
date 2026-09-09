"""
platforms/ebay/auth.py
eBay Sandbox OAuth2 token management.
Refactored from s2.py — all logic here, nothing hardcoded.
"""
import base64
import time
import requests
from core.config import settings

_token_cache = {"access_token": None, "expires_at": 0}

SCOPES = (
    "https://api.ebay.com/oauth/api_scope/sell.inventory "
    "https://api.ebay.com/oauth/api_scope/sell.account "
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
)


def get_access_token(force_refresh: bool = False) -> str:
    """
    Return a valid eBay access token.
    Caches the token in memory; refreshes automatically when it expires.
    """
    now = time.time()

    # Return cached token if still valid (with 60s buffer)
    if not force_refresh and _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    credentials = f"{settings.ebay_app_id}:{settings.ebay_cert_id}"
    b64 = base64.b64encode(credentials.encode()).decode()

    resp = requests.post(
        settings.ebay_base_identity,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {b64}",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": settings.ebay_refresh_token,
            "scope": SCOPES,
        },
    )

    if resp.status_code != 200:
        raise RuntimeError(f"eBay token refresh failed [{resp.status_code}]: {resp.text}")

    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 7200)

    return _token_cache["access_token"]


def get_auth_headers(token: str = None) -> dict:
    """Return eBay API auth headers with a fresh token."""
    token = token or get_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    }


def token_info() -> dict:
    """Return token status info for the dashboard."""
    now = time.time()
    has_token = bool(_token_cache["access_token"])
    expires_in = max(0, int(_token_cache["expires_at"] - now)) if has_token else 0
    return {
        "has_token": has_token,
        "expires_in_seconds": expires_in,
        "expires_in_minutes": round(expires_in / 60, 1),
    }
