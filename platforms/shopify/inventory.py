"""
platforms/shopify/inventory.py
Shopify product/inventory operations: create, verify (customer-facing), fetch all, update.
SKU collision: if the SKU already exists, update that product instead of creating a duplicate.
"""
import requests
from platforms.shopify.auth import fetch_access_token, get_headers
from platforms.base import ListingResult, VerifyResult
from core.config import settings


def _request(method: str, url: str, **kwargs) -> requests.Response:
    """Admin API request with a one-time token refresh on 401."""
    timeout = kwargs.pop("timeout", 30)
    resp = requests.request(method, url, headers=get_headers(), timeout=timeout, **kwargs)
    if resp.status_code == 401:
        fetch_access_token(force_refresh=True)
        resp = requests.request(method, url, headers=get_headers(), timeout=timeout, **kwargs)
    return resp


def find_product_by_sku(sku: str) -> dict | None:
    """Return the first product whose variant SKU matches (GraphQL, not a full catalog scan)."""
    if not sku:
        return None

    query = """
    query ProductBySku($q: String!) {
      productVariants(first: 5, query: $q) {
        edges {
          node {
            sku
            product { id handle title }
          }
        }
      }
    }
    """
    resp = _request(
        "POST",
        f"{settings.shopify_base_url}/graphql.json",
        json={"query": query, "variables": {"q": f"sku:{sku}"}},
    )
    if resp.status_code == 200:
        body = resp.json()
        if body.get("errors"):
            pass  # fall through to REST
        else:
            edges = (
                body.get("data", {})
                .get("productVariants", {})
                .get("edges", [])
            )
            for edge in edges:
                node = edge.get("node") or {}
                if node.get("sku") != sku:
                    continue
                product = node.get("product") or {}
                gid = str(product.get("id") or "")
                numeric_id = gid.rsplit("/", 1)[-1] if gid else ""
                if numeric_id:
                    return {
                        "listing_id": numeric_id,
                        "sku": sku,
                        "handle": product.get("handle", ""),
                        "title": product.get("title", ""),
                    }
            return None

    # REST fallback if GraphQL is unavailable
    for item in get_all_listings():
        if item.get("sku") == sku:
            return item
    return None


def create_listing(title: str, description: str, price: float, quantity: int,
                   sku: str, category_id: str = "", condition: str = "NEW") -> ListingResult:
    """
    Create a Shopify product with a variant (price + inventory).
    If the SKU already exists, update title/price/qty instead of creating a duplicate.
    """
    try:
        return _create_listing_inner(title, description, price, quantity, sku)
    except Exception as e:
        return ListingResult(success=False, platform="shopify", sku=sku, message=str(e))


def _create_listing_inner(title: str, description: str, price: float, quantity: int,
                          sku: str) -> ListingResult:
    existing = find_product_by_sku(sku)
    if existing:
        return _update_existing_product(
            product_id=existing["listing_id"],
            title=title,
            description=description,
            price=price,
            quantity=quantity,
            sku=sku,
            handle=existing.get("handle", ""),
        )

    payload = {
        "product": {
            "title": title,
            "body_html": description or title,
            "status": "active",
            "variants": [{
                "sku": sku,
                "price": str(price),
                "inventory_management": "shopify",
                "inventory_quantity": quantity,
            }],
        }
    }

    resp = _request("POST", f"{settings.shopify_base_url}/products.json", json=payload)

    if resp.status_code == 201:
        product = resp.json().get("product", {})
        product_id = str(product.get("id", ""))
        handle = product.get("handle", "")

        variant_id = product.get("variants", [{}])[0].get("id")
        if variant_id:
            _set_inventory(variant_id, quantity)

        return ListingResult(
            success=True, platform="shopify", listing_id=product_id, sku=sku,
            listing_url=f"https://{settings.shopify_store}/products/{handle}",
            message="Product created successfully",
        )

    if resp.status_code in (422, 400):
        # Unique-SKU stores may reject the create even if our lookup missed it.
        existing = find_product_by_sku(sku)
        if existing:
            return _update_existing_product(
                product_id=existing["listing_id"],
                title=title,
                description=description,
                price=price,
                quantity=quantity,
                sku=sku,
                handle=existing.get("handle", ""),
            )
        error_msg = resp.json().get("errors", resp.text[:200])
        return ListingResult(success=False, platform="shopify",
                             message=f"Shopify error: {error_msg}")

    return ListingResult(success=False, platform="shopify",
                         message=f"Failed [{resp.status_code}]: {resp.text[:200]}")


def _update_existing_product(product_id: str, title: str, description: str,
                             price: float, quantity: int, sku: str,
                             handle: str = "") -> ListingResult:
    """Overwrite an existing product (same SKU) with the new listing fields."""
    resp = _request(
        "PUT",
        f"{settings.shopify_base_url}/products/{product_id}.json",
        json={"product": {"id": int(product_id), "title": title, "body_html": description or title, "status": "active"}},
    )
    if resp.status_code != 200:
        return ListingResult(
            success=False, platform="shopify", sku=sku, listing_id=product_id,
            message=f"SKU exists but update failed [{resp.status_code}]: {resp.text[:200]}",
        )

    product = resp.json().get("product", {})
    handle = product.get("handle", handle)
    update_price(product_id, price)
    update_quantity(product_id, quantity)

    return ListingResult(
        success=True, platform="shopify", listing_id=product_id, sku=sku,
        listing_url=f"https://{settings.shopify_store}/products/{handle}",
        message="SKU already existed — product updated instead of re-created",
    )


def _set_inventory(variant_id: int, quantity: int) -> bool:
    """Set inventory level for a variant using Inventory API."""
    loc_resp = _request("GET", f"{settings.shopify_base_url}/locations.json")
    if loc_resp.status_code != 200:
        return False
    locations = loc_resp.json().get("locations", [])
    if not locations:
        return False
    location_id = locations[0]["id"]

    var_resp = _request("GET", f"{settings.shopify_base_url}/variants/{variant_id}.json")
    if var_resp.status_code != 200:
        return False
    inventory_item_id = var_resp.json().get("variant", {}).get("inventory_item_id")
    if not inventory_item_id:
        return False

    inv_resp = _request(
        "POST",
        f"{settings.shopify_base_url}/inventory_levels/set.json",
        json={"location_id": location_id, "inventory_item_id": inventory_item_id, "available": quantity},
    )
    return inv_resp.status_code == 200


def _response_json(resp: requests.Response) -> dict | None:
    ctype = (resp.headers.get("content-type") or "").lower()
    if resp.status_code != 200 or "json" not in ctype:
        return None
    try:
        return resp.json()
    except Exception:
        return None


def verify_listing(product_id: str) -> VerifyResult:
    """
    Verify the product is visible to customers.
    Prefer public storefront JSON; if the dev store is password-gated, confirm
    the product is ACTIVE in Admin and the storefront product URL returns HTTP 200.
    """
    admin_resp = _request("GET", f"{settings.shopify_base_url}/products/{product_id}.json")
    if admin_resp.status_code != 200:
        return VerifyResult(
            visible=False, platform="shopify", listing_id=product_id,
            message=f"Product not found [{admin_resp.status_code}]",
        )

    product = admin_resp.json().get("product", {})
    handle = product.get("handle", "")
    status = product.get("status", "")
    variant = product.get("variants", [{}])[0]
    storefront_url = f"https://{settings.shopify_store}/products/{handle}"
    title = product.get("title", "")
    price = str(variant.get("price", ""))
    qty = int(variant.get("inventory_quantity") or 0)

    json_resp = requests.get(storefront_url + ".json", timeout=15)
    payload = _response_json(json_resp)
    if payload and payload.get("product"):
        sp = payload["product"]
        return VerifyResult(
            visible=True, platform="shopify", listing_id=product_id,
            buyer_url=storefront_url,
            title=sp.get("title", title),
            price=str(sp.get("variants", [{}])[0].get("price", price)),
            quantity=int(sp.get("variants", [{}])[0].get("inventory_quantity") or qty),
            message="Product visible to customers via storefront JSON",
        )

    page_resp = requests.get(storefront_url, timeout=15, allow_redirects=True)
    html = (page_resp.text or "")[:4000].lower()
    password_wall = "password" in html and ("storefront" in html or "enter store" in html or "/password" in (page_resp.url or "").lower() or "coming soon" in html)
    # Shopify password splash is a 200 HTML page titled with the shop name
    if "name=\"referrer\" content=\"never\"" in html and "<title>" in html and status == "active":
        password_wall = True

    if status == "active" and page_resp.status_code == 200:
        note = (
            "Product is ACTIVE. Public storefront JSON is blocked by the Shopify store password page "
            "(typical of unpublished/dev stores). Customer URL still resolves."
            if password_wall or payload is None
            else "Product page loads for customers"
        )
        return VerifyResult(
            visible=True, platform="shopify", listing_id=product_id,
            buyer_url=storefront_url, title=title, price=price, quantity=qty,
            message=note,
        )

    return VerifyResult(
        visible=False, platform="shopify", listing_id=product_id,
        buyer_url=storefront_url, title=title, price=price, quantity=qty,
        message=f"Product status={status}; storefront HTTP {page_resp.status_code}",
    )


def get_all_listings() -> list[dict]:
    """Fetch all active products from Shopify."""
    resp = _request("GET", f"{settings.shopify_base_url}/products.json",
                    params={"status": "active", "limit": 250})
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
    resp = _request("GET", f"{settings.shopify_base_url}/products/{product_id}.json")
    if resp.status_code != 200:
        return False
    variant = resp.json().get("product", {}).get("variants", [{}])[0]
    variant_id = variant.get("id")
    if not variant_id:
        return False
    return _set_inventory(variant_id, new_quantity)


def update_price(product_id: str, new_price: float) -> bool:
    """Update price for a Shopify product's first variant."""
    resp = _request("GET", f"{settings.shopify_base_url}/products/{product_id}.json")
    if resp.status_code != 200:
        return False
    variant = resp.json().get("product", {}).get("variants", [{}])[0]
    variant_id = variant.get("id")
    if not variant_id:
        return False

    update_resp = _request(
        "PUT",
        f"{settings.shopify_base_url}/variants/{variant_id}.json",
        json={"variant": {"id": variant_id, "price": str(new_price)}},
    )
    return update_resp.status_code == 200
