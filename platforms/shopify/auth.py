"""
platforms/shopify/auth.py
Shopify authentication with automatic Client Credentials Grant token retrieval and caching.
"""
import requests
from core.config import settings

# In-memory cache for dynamic access token
_cached_token: str = settings.shopify_access_token


def fetch_access_token(force_refresh: bool = False) -> str:
    """
    Fetch access token via Shopify Client Credentials Grant.
    Uses POST https://{shopify_store}/admin/oauth/access_token
    """
    global _cached_token
    if _cached_token and not force_refresh:
        return _cached_token

    url = f"https://{settings.shopify_store}/admin/oauth/access_token"
    payload = {
        "client_id": settings.shopify_api_key,
        "client_secret": settings.shopify_api_secret,
        "grant_type": "client_credentials",
    }
    
    resp = requests.post(
        url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        if token:
            _cached_token = token
            return token
            
    raise RuntimeError(f"Shopify token fetch failed [{resp.status_code}]: {resp.text[:200]}")


def get_headers() -> dict:
    """Return Shopify Admin API auth headers with valid token."""
    token = fetch_access_token()
    return {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }


def test_connection() -> dict:
    """
    Test Shopify connection by fetching shop info.
    Auto-refreshes token if expired.
    Returns status dict for the dashboard.
    """
    global _cached_token
    try:
        token = fetch_access_token()
        headers = {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        }
        resp = requests.get(f"{settings.shopify_base_url}/shop.json", headers=headers, timeout=10)
        
        # If 401, force refresh token and retry once
        if resp.status_code == 401:
            token = fetch_access_token(force_refresh=True)
            headers["X-Shopify-Access-Token"] = token
            resp = requests.get(f"{settings.shopify_base_url}/shop.json", headers=headers, timeout=10)

        if resp.status_code == 200:
            shop = resp.json().get("shop", {})
            return {
                "connected": True,
                "shop_name": shop.get("name", ""),
                "domain": shop.get("domain", ""),
                "plan": shop.get("plan_name", ""),
                "email": shop.get("email", ""),
                "message": "Connected ✅",
            }
        return {
            "connected": False,
            "message": f"Connection failed [{resp.status_code}]: {resp.text[:200]}",
        }
    except Exception as e:
        return {
            "connected": False,
            "message": f"Connection error: {str(e)}",
        }
