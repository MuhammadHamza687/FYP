"""
api/dashboard_routes.py
All API routes called by the dashboard frontend.
"""
import subprocess
import sys
import psutil
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import requests

router = APIRouter(prefix="/api", tags=["dashboard"])


# ─── System Status ────────────────────────────────────────────────────────────

@router.get("/status")
def get_status():
    """Overall system status: server, ngrok, platform connections."""
    ngrok_url = _get_ngrok_url()
    return {
        "server": "running",
        "ngrok_url": ngrok_url,
        "ngrok_connected": bool(ngrok_url),
        "timestamp": _now(),
    }


@router.get("/ngrok/url")
def get_ngrok_url():
    """Get the current ngrok public URL from ngrok's local API."""
    url = _get_ngrok_url()
    return {"url": url, "connected": bool(url)}


def _get_ngrok_url() -> str:
    """Fetch ngrok URL from its local admin API (port 4040)."""
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        if resp.status_code == 200:
            tunnels = resp.json().get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    return t.get("public_url", "")
            if tunnels:
                return tunnels[0].get("public_url", "")
    except Exception:
        pass
    return ""


def _now():
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


# ─── eBay Routes ──────────────────────────────────────────────────────────────

@router.get("/ebay/status")
def ebay_status():
    """Test eBay connection and return token info."""
    try:
        from platforms.ebay.auth import get_access_token, token_info
        token = get_access_token(force_refresh=True)
        info = token_info()
        return {
            "connected": True,
            "platform": "ebay",
            "environment": "sandbox",
            "seller": "TESTUSER_TESTUSER_hamza-seller",
            "token_expires_in_minutes": info["expires_in_minutes"],
            "message": "eBay connected ✅",
        }
    except Exception as e:
        return JSONResponse(status_code=200, content={
            "connected": False, "platform": "ebay",
            "message": f"eBay connection failed: {str(e)}"
        })


@router.post("/ebay/listings")
def create_ebay_listing(data: dict):
    """
    Create a new eBay listing.
    Body: {title, description, price, quantity, sku, category_id, condition}
    """
    from platforms.ebay.inventory import create_listing
    try:
        result = create_listing(
            title=data.get("title", "Test Product"),
            description=data.get("description", ""),
            price=float(data.get("price", 19.99)),
            quantity=int(data.get("quantity", 10)),
            sku=data.get("sku", "SKU-001"),
            category_id=data.get("category_id", "9355"),
            condition=data.get("condition", "NEW"),
        )
        return result.to_dict()
    except Exception as e:
        return {"success": False, "platform": "ebay", "message": str(e)}


@router.get("/ebay/listings/{listing_id}/verify")
def verify_ebay_listing(listing_id: str):
    """Verify an eBay listing is visible from the BUYER side."""
    from platforms.ebay.inventory import verify_listing
    try:
        return verify_listing(listing_id).to_dict()
    except Exception as e:
        return {"visible": False, "platform": "ebay", "listing_id": listing_id, "message": str(e)}


@router.get("/ebay/listings")
def get_ebay_listings():
    """Get all eBay inventory items."""
    from platforms.ebay.inventory import get_all_listings
    return {"listings": get_all_listings(), "platform": "ebay"}


@router.put("/ebay/listings/{sku}/quantity")
def update_ebay_quantity(sku: str, data: dict):
    """Update quantity for an eBay listing."""
    from platforms.ebay.inventory import update_quantity
    success = update_quantity(sku, int(data.get("quantity", 0)))
    return {"success": success, "platform": "ebay", "sku": sku}


# ─── Shopify Routes ───────────────────────────────────────────────────────────

@router.get("/shopify/status")
def shopify_status():
    """Test Shopify connection and return shop info."""
    from platforms.shopify.auth import test_connection
    result = test_connection()
    result["platform"] = "shopify"
    return result


@router.post("/shopify/listings")
def create_shopify_listing(data: dict):
    """
    Create a new Shopify product.
    Body: {title, description, price, quantity, sku, condition}
    """
    from platforms.shopify.inventory import create_listing
    try:
        result = create_listing(
            title=data.get("title", "Test Product"),
            description=data.get("description", ""),
            price=float(data.get("price", 19.99)),
            quantity=int(data.get("quantity", 10)),
            sku=data.get("sku", "SKU-001"),
            condition=data.get("condition", "NEW"),
        )
        return result.to_dict()
    except Exception as e:
        return {"success": False, "platform": "shopify", "message": str(e)}


@router.get("/shopify/listings/{product_id}/verify")
def verify_shopify_listing(product_id: str):
    """Verify a Shopify product is visible to customers (storefront API check)."""
    from platforms.shopify.inventory import verify_listing
    try:
        return verify_listing(product_id).to_dict()
    except Exception as e:
        return {"visible": False, "platform": "shopify", "listing_id": product_id, "message": str(e)}


@router.get("/shopify/listings")
def get_shopify_listings():
    """Get all Shopify active products."""
    from platforms.shopify.inventory import get_all_listings
    return {"listings": get_all_listings(), "platform": "shopify"}


@router.put("/shopify/listings/{product_id}/quantity")
def update_shopify_quantity(product_id: str, data: dict):
    """Update quantity for a Shopify product."""
    from platforms.shopify.inventory import update_quantity
    success = update_quantity(product_id, int(data.get("quantity", 0)))
    return {"success": success, "platform": "shopify", "product_id": product_id}


@router.put("/shopify/listings/{product_id}/price")
def update_shopify_price(product_id: str, data: dict):
    """Update price for a Shopify product."""
    from platforms.shopify.inventory import update_price
    success = update_price(product_id, float(data.get("price", 0)))
    return {"success": success, "platform": "shopify", "product_id": product_id}


# ─── Sync Routes (Both Platforms) ────────────────────────────────────────────

@router.post("/sync/listings")
def sync_listing_both_platforms(data: dict):
    """
    List the same product on BOTH eBay and Shopify simultaneously.
    Returns results for both platforms in one response.
    """
    from platforms.base import ListingResult
    from platforms.ebay.inventory import create_listing as ebay_create
    from platforms.shopify.inventory import create_listing as shopify_create

    payload = dict(
        title=data.get("title", "Test Product"),
        description=data.get("description", ""),
        price=float(data.get("price", 19.99)),
        quantity=int(data.get("quantity", 10)),
        sku=data.get("sku", "SKU-001"),
        condition=data.get("condition", "NEW"),
    )

    try:
        ebay_result = ebay_create(**payload, category_id=data.get("category_id", "9355"))
    except Exception as e:
        ebay_result = ListingResult(success=False, platform="ebay", sku=payload["sku"], message=str(e))

    try:
        shopify_result = shopify_create(**payload)
    except Exception as e:
        shopify_result = ListingResult(success=False, platform="shopify", sku=payload["sku"], message=str(e))

    return {
        "ebay": ebay_result.to_dict(),
        "shopify": shopify_result.to_dict(),
        "both_success": ebay_result.success and shopify_result.success,
    }


@router.get("/listings")
def get_all_listings():
    """Get all listings from both platforms, matched by SKU where possible."""
    from platforms.ebay.inventory import get_all_listings as ebay_listings
    from platforms.shopify.inventory import get_all_listings as shopify_listings

    ebay = ebay_listings()
    shopify = shopify_listings()

    # Build SKU index
    ebay_by_sku = {item["sku"]: item for item in ebay if item.get("sku")}
    shopify_by_sku = {item["sku"]: item for item in shopify if item.get("sku")}

    all_skus = set(ebay_by_sku.keys()) | set(shopify_by_sku.keys())

    unified = []
    for sku in all_skus:
        unified.append({
            "sku": sku,
            "ebay": ebay_by_sku.get(sku),
            "shopify": shopify_by_sku.get(sku),
            "synced": sku in ebay_by_sku and sku in shopify_by_sku,
        })

    return {"listings": unified, "ebay_count": len(ebay), "shopify_count": len(shopify)}
