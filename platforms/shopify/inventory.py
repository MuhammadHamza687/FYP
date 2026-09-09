"""
platforms/shopify/inventory.py
Shopify product/inventory operations: create, verify (customer-facing), fetch all, update.
"""
import requests
from platforms.shopify.auth import get_headers
from platforms.base import ListingResult, VerifyResult
from core.config import settings


def create_listing(title: str, description: str, price: float, quantity: int,
                   sku: str, category_id: str = "", condition: str = "NEW") -> ListingResult:
    """
    Create a Shopify product with a variant (price + inventory).
    Returns ListingResult with product_id and URL.
    """
    payload = {
        "product": {
            "title": title,
            "body_html": description,
            "status": "active",
            "variants": [{
                "sku": sku,
                "price": str(price),
                "inventory_management": "shopify",
                "inventory_quantity": quantity,
                "condition": condition.lower() if condition else "new",
            }],
        }
    }

    resp = requests.post(f"{settings.shopify_base_url}/products.json",
                         headers=get_headers(), json=payload)

    if resp.status_code == 201:
        product = resp.json().get("product", {})
        product_id = str(product.get("id", ""))
        handle = product.get("handle", "")

        # Set inventory quantity via Inventory API (more reliable)
        variant_id = product.get("variants", [{}])[0].get("id")
        if variant_id:
            _set_inventory(variant_id, quantity)

        return ListingResult(
            success=True, platform="shopify", listing_id=product_id, sku=sku,
            listing_url=f"https://{settings.shopify_store}/products/{handle}",
            message="Product created successfully",
        )

    # Check if SKU already exists
    if resp.status_code in (422, 400):
        error_msg = resp.json().get("errors", {})
        return ListingResult(success=False, platform="shopify",
                             message=f"Shopify error: {error_msg}")

    return ListingResult(success=False, platform="shopify",
                         message=f"Failed [{resp.status_code}]: {resp.text[:200]}")


def _set_inventory(variant_id: int, quantity: int) -> bool:
    """Set inventory level for a variant using Inventory API."""
    # Get location ID first
    loc_resp = requests.get(f"{settings.shopify_base_url}/locations.json", headers=get_headers())
    if loc_resp.status_code != 200:
        return False
    locations = loc_resp.json().get("locations", [])
    if not locations:
        return False
    location_id = locations[0]["id"]

    # Get inventory item ID from variant
    var_resp = requests.get(f"{settings.shopify_base_url}/variants/{variant_id}.json", headers=get_headers())
    if var_resp.status_code != 200:
        return False
    inventory_item_id = var_resp.json().get("variant", {}).get("inventory_item_id")
    if not inventory_item_id:
        return False

    # Set inventory level
    inv_resp = requests.post(
        f"{settings.shopify_base_url}/inventory_levels/set.json",
        headers=get_headers(),
        json={"location_id": location_id, "inventory_item_id": inventory_item_id, "available": quantity},
    )
    return inv_resp.status_code == 200


def verify_listing(product_id: str) -> VerifyResult:
    """
    Verify the product is visible to customers using the STOREFRONT API.
    This is the customer-facing endpoint — proves a buyer can see the product.
    """
    # Use the public storefront endpoint (no auth needed — just like a customer)
    storefront_resp = requests.get(
        f"https://{settings.shopify_store}/products/{product_id}.json"
    )

    if storefront_resp.status_code == 200:
        product = storefront_resp.json().get("product", {})
        return VerifyResult(
            visible=True, platform="shopify", listing_id=product_id,
            buyer_url=f"https://{settings.shopify_store}/products/{product.get('handle', product_id)}",
            title=product.get("title", ""),
            price=product.get("variants", [{}])[0].get("price", ""),
            message="Product visible to customers ✅",
        )

    # Try by handle via admin API
    admin_resp = requests.get(f"{settings.shopify_base_url}/products/{product_id}.json",
                              headers=get_headers())
    if admin_resp.status_code == 200:
        product = admin_resp.json().get("product", {})
        handle = product.get("handle", "")
        status = product.get("status", "")
        storefront_url = f"https://{settings.shopify_store}/products/{handle}"

        # Try storefront by handle
        handle_resp = requests.get(storefront_url + ".json")
        visible = handle_resp.status_code == 200

        return VerifyResult(
            visible=visible, platform="shopify", listing_id=product_id,
            buyer_url=storefront_url,
            title=product.get("title", ""),
            price=product.get("variants", [{}])[0].get("price", ""),
            message=f"Product status: {status} | Storefront visible: {visible}",
        )

    return VerifyResult(
        visible=False, platform="shopify", listing_id=product_id,
        message=f"Product not found [{admin_resp.status_code}]",
    )


def get_all_listings() -> list[dict]:
    """Fetch all active products from Shopify."""
    resp = requests.get(f"{settings.shopify_base_url}/products.json",
                        headers=get_headers(), params={"status": "active", "limit": 250})
    if resp.status_code != 200:
        return []
    products = resp.json().get("products", [])
    result = []
    for p in products:
        variant = p.get("variants", [{}])[0]
        result.append({
            "listing_id": str(p.get("id", "")),
            "title": p.get("title", ""),
            "sku": variant.get("sku", ""),
            "price": variant.get("price", "0"),
            "quantity": variant.get("inventory_quantity", 0),
            "status": p.get("status", ""),
            "handle": p.get("handle", ""),
            "url": f"https://{settings.shopify_store}/products/{p.get('handle', '')}",
            "platform": "shopify",
        })
    return result


def update_quantity(product_id: str, new_quantity: int) -> bool:
    """Update inventory quantity for a Shopify product's first variant."""
    # Get product variants
    resp = requests.get(f"{settings.shopify_base_url}/products/{product_id}.json",
                        headers=get_headers())
    if resp.status_code != 200:
        return False
    variant = resp.json().get("product", {}).get("variants", [{}])[0]
    variant_id = variant.get("id")
    if not variant_id:
        return False
    return _set_inventory(variant_id, new_quantity)


def update_price(product_id: str, new_price: float) -> bool:
    """Update price for a Shopify product's first variant."""
    resp = requests.get(f"{settings.shopify_base_url}/products/{product_id}.json",
                        headers=get_headers())
    if resp.status_code != 200:
        return False
    variant = resp.json().get("product", {}).get("variants", [{}])[0]
    variant_id = variant.get("id")
    if not variant_id:
        return False

    update_resp = requests.put(
        f"{settings.shopify_base_url}/variants/{variant_id}.json",
        headers=get_headers(),
        json={"variant": {"id": variant_id, "price": str(new_price)}},
    )
    return update_resp.status_code == 200
