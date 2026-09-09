"""
platforms/shopify/auth.py
Shopify authentication using static access token from .env.
"""
import requests
from core.config import settings


def get_headers() -> dict:
    """Return Shopify Admin API auth headers."""
    return {
        "X-Shopify-Access-Token": settings.shopify_access_token,
        "Content-Type": "application/json",
    }


def test_connection() -> dict:
    """
    Test Shopify connection by fetching shop info.
    Returns status dict for the dashboard.
    """
    resp = requests.get(f"{settings.shopify_base_url}/shop.json", headers=get_headers())
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
