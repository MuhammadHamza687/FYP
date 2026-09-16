"""
platforms/ebay/inventory.py
eBay inventory operations: location, listing, verify (buyer-side), update, delete.
All logic extracted from s2.py and make_buyable.py, now fully modular.
"""
import requests
from platforms.ebay.auth import get_access_token, get_auth_headers
from platforms.base import ListingResult, VerifyResult
from core.config import settings

LOCATION_KEY = "FYP_WAREHOUSE"
MARKETPLACE_ID = "EBAY_US"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get(path: str, params: dict = None) -> requests.Response:
    token = get_access_token()
    url = f"{settings.ebay_base_inventory}{path}" if not path.startswith("http") else path
    return requests.get(url, headers=get_auth_headers(token), params=params)


def _post(path: str, data: dict = None, base: str = None) -> requests.Response:
    token = get_access_token()
    base_url = base or settings.ebay_base_inventory
    url = f"{base_url}{path}" if not path.startswith("http") else path
    return requests.post(url, headers=get_auth_headers(token), json=data)


def _put(path: str, data: dict) -> requests.Response:
    token = get_access_token()
    url = f"{settings.ebay_base_inventory}{path}" if not path.startswith("http") else path
    return requests.put(url, headers=get_auth_headers(token), json=data)


def _get_error_ids(response: requests.Response) -> set:
    try:
        return {e.get("errorId") for e in response.json().get("errors", [])}
    except Exception:
        return set()


def _format_errors(response: requests.Response) -> str:
    try:
        errors = response.json().get("errors", [])
        return " | ".join(f"[{e.get('errorId')}] {e.get('message')}" for e in errors)
    except Exception:
        return response.text[:200]


# ─── Location ─────────────────────────────────────────────────────────────────

def ensure_location() -> bool:
    """Create warehouse location if it doesn't exist yet."""
    token = get_access_token()
    resp = requests.post(
        f"{settings.ebay_base_inventory}/location/{LOCATION_KEY}",
        headers=get_auth_headers(token),
        json={
            "location": {
                "address": {
                    "addressLine1": "123 Main Street",
                    "city": "San Jose",
                    "stateOrProvince": "CA",
                    "postalCode": "95101",
                    "country": "US",
                }
            },
            "name": "FYP Main Warehouse",
            "merchantLocationStatus": "ENABLED",
            "locationTypes": ["WAREHOUSE"],
        },
    )
    if resp.status_code == 204:
        return True
    if resp.status_code == 400 and _get_error_ids(resp) & {25802, 25803}:
        return True  # Already exists
    return False


# ─── Business Policies ────────────────────────────────────────────────────────

def _get_policy_id(policy_path: str, response_key: str, id_field: str) -> str | None:
    token = get_access_token()
    resp = requests.get(
        f"{settings.ebay_base_account}/{policy_path}",
        headers=get_auth_headers(token),
        params={"marketplace_id": MARKETPLACE_ID},
    )
    if resp.status_code != 200:
        return None
    items = resp.json().get(response_key, [])
    return items[0].get(id_field) if items else None


def ensure_policies() -> tuple[str, str, str] | None:
    """Fetch or create all three required business policies."""
    token = get_access_token()

    def create_payment():
        r = requests.post(f"{settings.ebay_base_account}/payment_policy",
            headers=get_auth_headers(token),
            json={"name": "FYP Payment Policy", "marketplaceId": MARKETPLACE_ID,
                  "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}], "immediatePay": True})
        return r.json().get("paymentPolicyId") if r.status_code == 201 else None

    def create_return():
        r = requests.post(f"{settings.ebay_base_account}/return_policy",
            headers=get_auth_headers(token),
            json={"name": "FYP Return Policy", "marketplaceId": MARKETPLACE_ID,
                  "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                  "returnsAccepted": True, "returnPeriod": {"value": 30, "unit": "DAY"},
                  "refundMethod": "MONEY_BACK", "returnShippingCostPayer": "BUYER"})
        return r.json().get("returnPolicyId") if r.status_code == 201 else None

    def create_fulfillment():
        r = requests.post(f"{settings.ebay_base_account}/fulfillment_policy",
            headers=get_auth_headers(token),
            json={"name": "FYP Fulfillment Policy", "marketplaceId": MARKETPLACE_ID,
                  "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
                  "handlingTime": {"value": 1, "unit": "DAY"},
                  "shippingOptions": [{"optionType": "DOMESTIC", "costType": "FLAT_RATE",
                      "shippingServices": [{"sortOrder": 1, "shippingCarrierCode": "USPS",
                          "shippingServiceCode": "USPSPriorityFlatRateBox",
                          "shippingCost": {"value": "0.00", "currency": "USD"},
                          "freeShipping": True, "buyerResponsibleForShipping": False}]}]})
        return r.json().get("fulfillmentPolicyId") if r.status_code == 201 else None

    # Opt in to business policies
    requests.post(f"{settings.ebay_base_account}/program/opt_in",
        headers=get_auth_headers(token), json={"programType": "SELLING_POLICY_MANAGEMENT"})

    pay = _get_policy_id("payment_policy", "paymentPolicies", "paymentPolicyId") or create_payment()
    ret = _get_policy_id("return_policy", "returnPolicies", "returnPolicyId") or create_return()
    ful = _get_policy_id("fulfillment_policy", "fulfillmentPolicies", "fulfillmentPolicyId") or create_fulfillment()

    if not all([pay, ret, ful]):
        return None
    return pay, ret, ful


# ─── Main Listing Operations ───────────────────────────────────────────────────

def create_listing(title: str, description: str, price: float, quantity: int,
                   sku: str, category_id: str = "9355", condition: str = "NEW") -> ListingResult:
    """
    Full eBay listing flow:
    location → inventory item → policies → offer → publish
    Re-listing the same SKU updates the inventory item and reuses the existing offer.
    """
    try:
        return _create_listing_inner(title, description, price, quantity, sku, category_id, condition)
    except Exception as e:
        return ListingResult(success=False, platform="ebay", sku=sku, message=str(e))


def _create_listing_inner(title: str, description: str, price: float, quantity: int,
                          sku: str, category_id: str, condition: str) -> ListingResult:
    token = get_access_token()
    headers = get_auth_headers(token)

    # Step 1: Location
    ensure_location()

    # Step 2: Inventory item
    inv_resp = requests.put(
        f"{settings.ebay_base_inventory}/inventory_item/{sku}",
        headers=headers,
        json={
            "product": {"title": title, "description": description},
            "condition": condition,
            "availability": {"shipToLocationAvailability": {"quantity": quantity}},
        },
    )
    if inv_resp.status_code not in (200, 204):
        return ListingResult(success=False, platform="ebay",
                             message=f"Inventory item failed: {_format_errors(inv_resp)}")

    # Step 3: Business policies
    policies = ensure_policies()
    if not policies:
        return ListingResult(success=False, platform="ebay", message="Could not set up business policies")
    pay_id, ret_id, ful_id = policies

    # Step 4: Create or update offer
    offer_data = {
        "sku": sku, "marketplaceId": MARKETPLACE_ID, "format": "FIXED_PRICE",
        "quantity": quantity, "categoryId": category_id,
        "price": {"value": str(price), "currency": "USD"},
        "listingDescription": description,
        "merchantLocationKey": LOCATION_KEY,
        "listingPolicies": {
            "paymentPolicyId": pay_id, "returnPolicyId": ret_id, "fulfillmentPolicyId": ful_id,
        },
    }

    offer_resp = requests.post(f"{settings.ebay_base_inventory}/offer", headers=headers, json=offer_data)
    offer_id = None
    sku_collision = False

    if offer_resp.status_code == 201:
        offer_id = offer_resp.json().get("offerId")
    elif offer_resp.status_code == 400 and 25002 in _get_error_ids(offer_resp):
        # Offer exists — find and update it
        lookup = requests.get(f"{settings.ebay_base_inventory}/offer",
                              headers=headers, params={"sku": sku, "marketplace_id": MARKETPLACE_ID})
        offers = lookup.json().get("offers", []) if lookup.status_code == 200 else []
        if offers:
            offer_id = offers[0]["offerId"]
            requests.put(f"{settings.ebay_base_inventory}/offer/{offer_id}", headers=headers, json=offer_data)
            sku_collision = True
        else:
            return ListingResult(success=False, platform="ebay", message="Offer exists but couldn't retrieve it")
    else:
        return ListingResult(success=False, platform="ebay",
                             message=f"Offer creation failed: {_format_errors(offer_resp)}")

    # Step 5: Publish
    pub_resp = requests.post(f"{settings.ebay_base_inventory}/offer/{offer_id}/publish", headers=headers)
    if pub_resp.status_code == 200:
        listing_id = pub_resp.json().get("listingId")
        reused = "SKU already existed — inventory/offer updated and published" if sku_collision else "Published successfully"
        return ListingResult(
            success=True, platform="ebay", listing_id=listing_id, sku=sku,
            listing_url=f"https://sandbox.ebay.com/itm/{listing_id}",
            message=reused,
        )
    elif pub_resp.status_code == 400 and 25002 in _get_error_ids(pub_resp):
        # Already published — get listing ID from offer
        offer_detail = requests.get(f"{settings.ebay_base_inventory}/offer/{offer_id}", headers=headers)
        listing_id = offer_detail.json().get("listing", {}).get("listingId", offer_id)
        return ListingResult(
            success=True, platform="ebay", listing_id=listing_id, sku=sku,
            listing_url=f"https://sandbox.ebay.com/itm/{listing_id}",
            message="Already published (reused existing listing)",
        )
    else:
        return ListingResult(success=False, platform="ebay",
                             message=f"Publish failed: {_format_errors(pub_resp)}")


def verify_listing(listing_id: str) -> VerifyResult:
    """
    Verify the listing is visible from the BUYER side.
    Prefer eBay Browse API; fall back to published-offer lookup (sandbox Browse is often scoped out).
    """
    token = get_access_token()
    buyer_url = f"https://sandbox.ebay.com/itm/{listing_id}"
    resp = requests.get(
        f"{settings.ebay_browse_base}/item/v1|{listing_id}|0",
        headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE_ID,
        },
        timeout=20,
    )

    if resp.status_code == 200:
        data = resp.json()
        return VerifyResult(
            visible=True, platform="ebay", listing_id=listing_id,
            buyer_url=buyer_url,
            title=data.get("title", ""),
            price=str(data.get("price", {}).get("value", "")),
            quantity=data.get("estimatedAvailabilities", [{}])[0].get("estimatedAvailableQuantity", 0),
            message="Listing is visible to buyers ✅",
        )

    offer = _find_offer_by_listing_id(listing_id)
    if offer:
        listing = offer.get("listing") or {}
        status = offer.get("status", "")
        listing_status = listing.get("listingStatus", "")
        published = status == "PUBLISHED" or listing_status == "ACTIVE"
        price = (offer.get("pricingSummary") or {}).get("price") or offer.get("price") or {}
        return VerifyResult(
            visible=published, platform="ebay", listing_id=listing_id,
            buyer_url=buyer_url,
            title=offer.get("listingDescription", "")[:80],
            price=str(price.get("value", "")),
            quantity=int(offer.get("availableQuantity") or offer.get("quantity") or 0),
            message=(
                f"Published offer found (status={status or listing_status}). "
                f"Browse API returned {resp.status_code} in sandbox."
            ),
        )

    return VerifyResult(
        visible=False, platform="ebay", listing_id=listing_id,
        buyer_url=buyer_url,
        message=f"Listing not found on Browse API ({resp.status_code}) or in published offers",
    )


def _find_offer_by_listing_id(listing_id: str) -> dict | None:
    token = get_access_token()
    resp = requests.get(
        f"{settings.ebay_base_inventory}/offer",
        headers=get_auth_headers(token),
        params={"limit": "200", "offset": "0"},
        timeout=20,
    )
    if resp.status_code != 200:
        return None
    for offer in resp.json().get("offers", []):
        listing = offer.get("listing") or {}
        if str(listing.get("listingId", "")) == str(listing_id):
            return offer
        if str(offer.get("offerId", "")) == str(listing_id):
            return offer
    return None


def get_all_listings() -> list[dict]:
    """Fetch all inventory items from eBay seller account, merged with published listing IDs."""
    token = get_access_token()
    headers = get_auth_headers(token)
    resp = requests.get(f"{settings.ebay_base_inventory}/inventory_item",
                        headers=headers, params={"limit": "200"})
    if resp.status_code != 200:
        return []

    offers_by_sku: dict[str, dict] = {}
    offers_resp = requests.get(
        f"{settings.ebay_base_inventory}/offer",
        headers=headers,
        params={"limit": "200"},
        timeout=20,
    )
    if offers_resp.status_code == 200:
        for offer in offers_resp.json().get("offers", []):
            sku = offer.get("sku")
            if sku:
                offers_by_sku[sku] = offer

    result = []
    for item in resp.json().get("inventoryItems", []):
        sku = item.get("sku")
        offer = offers_by_sku.get(sku, {})
        listing = offer.get("listing") or {}
        price = (offer.get("pricingSummary") or {}).get("price") or offer.get("price") or {}
        result.append({
            "sku": sku,
            "listing_id": listing.get("listingId", ""),
            "title": item.get("product", {}).get("title", ""),
            "quantity": item.get("availability", {}).get("shipToLocationAvailability", {}).get("quantity", 0),
            "price": price.get("value", ""),
            "condition": item.get("condition"),
            "status": offer.get("status", listing.get("listingStatus", "")),
            "platform": "ebay",
        })
    return result


def update_quantity(sku: str, new_quantity: int) -> bool:
    """Update quantity for an existing eBay inventory item."""
    token = get_access_token()
    # First get existing item
    resp = requests.get(f"{settings.ebay_base_inventory}/inventory_item/{sku}",
                        headers=get_auth_headers(token))
    if resp.status_code != 200:
        return False

    item = resp.json()
    if "availability" not in item:
        item["availability"] = {}
    item["availability"]["shipToLocationAvailability"] = {"quantity": new_quantity}

    update_resp = requests.put(f"{settings.ebay_base_inventory}/inventory_item/{sku}",
                               headers=get_auth_headers(token), json=item)
    return update_resp.status_code in (200, 204)
