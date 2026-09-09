"""
ebay_full.py

All-in-one eBay Sandbox listing script.

What it does, in order:
  0. Uses your REFRESH_TOKEN to silently get a fresh access token (no browser
     login needed -- refresh tokens last ~18 months).
  1. Creates (or reuses) an inventory location.
  2. Creates (or updates) an inventory item.
  3. Fetches your payment / return / fulfillment business policies.
  4. Creates (or updates) an offer using those policies.
  5. Publishes the offer so it's live and buyable in sandbox.

Fill in the CONFIG block below, then just run:
    python ebay_full.py
"""

import base64
import requests

# =============================================================================
# CONFIG -- fill these in from your eBay Developer Portal / keyset
# =============================================================================
CLIENT_ID = "Muhammad-FYPInven-SBX-7650e493c-bccee85a"
CLIENT_SECRET = "SBX-650e493ca76f-c2e6-41cb-8836-a935"  # your full Cert ID
REFRESH_TOKEN = "v^1.1#i^1#f^0#I^3#r^1#p^3#t^Ul4xMF81OjY4NTgwOUEwRjIzRjE1RjAwMDgxMjc4NUI0QjUyQzNEXzJfMSNFXjEyODQ="
LOCATION_KEY = "MY_WAREHOUSE"
SKU = "TEST-SKU-001"
CATEGORY_ID = "9355"  # <-- set to a real leaf category ID for your item

MARKETPLACE_ID = "EBAY_US"

# =============================================================================
BASE_IDENTITY = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
BASE_INVENTORY = "https://api.sandbox.ebay.com/sell/inventory/v1"
BASE_ACCOUNT = "https://api.sandbox.ebay.com/sell/account/v1"

SCOPES = (
    "https://api.ebay.com/oauth/api_scope/sell.inventory "
    "https://api.ebay.com/oauth/api_scope/sell.account"
)


# -----------------------------------------------------------------------------
# TOKEN REFRESH
# -----------------------------------------------------------------------------
def get_fresh_access_token():
    if "PASTE_" in REFRESH_TOKEN:
        raise SystemExit("Fill in REFRESH_TOKEN in the CONFIG block before running.")

    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_credentials}",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "scope": SCOPES,
    }
    resp = requests.post(BASE_IDENTITY, headers=headers, data=data)
    if resp.status_code != 200:
        print(f"❌ Token refresh failed: {resp.status_code}")
        print(resp.text)
        raise SystemExit(1)

    token = resp.json()["access_token"]
    print("✅ Access token refreshed")
    return token


# -----------------------------------------------------------------------------
# HTTP HELPERS
# -----------------------------------------------------------------------------
def make_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
        "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE_ID,
    }


def api_call(method, url, token, data=None, params=None):
    h = make_headers(token)
    if method == "GET":
        return requests.get(url, headers=h, params=params)
    elif method == "POST":
        return requests.post(url, headers=h, json=data)
    elif method == "PUT":
        return requests.put(url, headers=h, json=data)
    elif method == "DELETE":
        return requests.delete(url, headers=h)
    raise ValueError(f"Unsupported method: {method}")


def print_ebay_error(response):
    try:
        body = response.json()
        for err in body.get("errors", []):
            print(f"   errorId: {err.get('errorId')}")
            print(f"   message: {err.get('message')}")
            if err.get("longMessage"):
                print(f"   longMessage: {err.get('longMessage')}")
            if err.get("parameters"):
                print(f"   parameters: {err.get('parameters')}")
    except Exception:
        print("   raw:", response.text)


def get_error_ids(response):
    try:
        return {e.get("errorId") for e in response.json().get("errors", [])}
    except Exception:
        return set()


# -----------------------------------------------------------------------------
# STEP 1: LOCATION
# -----------------------------------------------------------------------------
def create_location(token):
    print("\n📍 Step 1: Creating location...")
    location_data = {
        "location": {
            "address": {
                "addressLine1": "123 Main Street",
                "city": "San Jose",
                "stateOrProvince": "CA",
                "postalCode": "95101",
                "country": "US",
            }
        },
        "name": "Main Warehouse",
        "merchantLocationStatus": "ENABLED",
        "locationTypes": ["WAREHOUSE"],
    }
    # createInventoryLocation is a POST call, not PUT.
    resp = api_call("POST", f"{BASE_INVENTORY}/location/{LOCATION_KEY}", token, location_data)
    if resp.status_code == 204:
        print("✅ Location created successfully!")
    elif resp.status_code == 400 and get_error_ids(resp) & {25802, 25803}:
        print("ℹ️ Location already exists, continuing...")
    else:
        print(f"⚠️ Location status: {resp.status_code}")
        print_ebay_error(resp)
        raise SystemExit(1)


# -----------------------------------------------------------------------------
# STEP 2: INVENTORY ITEM
# -----------------------------------------------------------------------------
def create_inventory_item(token):
    print("\n📦 Step 2: Creating inventory item...")
    inventory_data = {
        "product": {
            "title": "Test Product - FYP Sync",
            "description": "Test product for inventory synchronization demo",
        },
        "condition": "NEW",
        "availability": {"shipToLocationAvailability": {"quantity": 10}},
    }
    resp = api_call("PUT", f"{BASE_INVENTORY}/inventory_item/{SKU}", token, inventory_data)
    if resp.status_code == 204:
        print("✅ Inventory item created successfully!")
    else:
        print(f"⚠️ Inventory status: {resp.status_code}")
        print_ebay_error(resp)
        raise SystemExit(1)


# -----------------------------------------------------------------------------
# STEP 2b: OPT IN TO BUSINESS POLICIES
# -----------------------------------------------------------------------------
def opt_in_to_business_policies(token):
    print("\n🔑 Step 2b: Opting in to Business Policies program...")
    resp = api_call(
        "POST",
        f"{BASE_ACCOUNT}/program/opt_in",
        token,
        {"programType": "SELLING_POLICY_MANAGEMENT"},
    )
    if resp.status_code == 200:
        print("✅ Opted in to Business Policies.")
    elif resp.status_code == 400 and 20401 in get_error_ids(resp):
        print("ℹ️ Already opted in, continuing...")
    else:
        # Some sandbox accounts return other codes when already opted in;
        # don't hard-fail here, just report and continue -- the policy
        # fetch/create step below will fail clearly if opt-in truly didn't work.
        print(f"⚠️ Opt-in status: {resp.status_code}")
        print_ebay_error(resp)


# -----------------------------------------------------------------------------
# STEP 2c: BUSINESS POLICIES (fetch, or create defaults if missing)
# -----------------------------------------------------------------------------
def get_first_policy_id(token, policy_type_path, response_key, id_field):
    resp = api_call(
        "GET",
        f"{BASE_ACCOUNT}/{policy_type_path}",
        token,
        params={"marketplace_id": MARKETPLACE_ID},
    )
    if resp.status_code != 200:
        print(f"⚠️ Could not fetch {policy_type_path}: {resp.status_code}")
        print_ebay_error(resp)
        return None
    items = resp.json().get(response_key, [])
    if not items:
        return None
    return items[0].get(id_field)


def create_payment_policy(token):
    print("   Creating default payment policy...")
    payload = {
        "name": "Default Payment Policy",
        "marketplaceId": MARKETPLACE_ID,
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
        "immediatePay": True,
    }
    resp = api_call("POST", f"{BASE_ACCOUNT}/payment_policy", token, payload)
    if resp.status_code == 201:
        policy_id = resp.json().get("paymentPolicyId")
        print(f"   ✅ Payment policy created: {policy_id}")
        return policy_id
    print(f"   ❌ Payment policy creation failed: {resp.status_code}")
    print_ebay_error(resp)
    return None


def create_return_policy(token):
    print("   Creating default return policy...")
    payload = {
        "name": "Default Return Policy",
        "marketplaceId": MARKETPLACE_ID,
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
        "returnsAccepted": True,
        "returnPeriod": {"value": 30, "unit": "DAY"},
        "refundMethod": "MONEY_BACK",
        "returnShippingCostPayer": "BUYER",
    }
    resp = api_call("POST", f"{BASE_ACCOUNT}/return_policy", token, payload)
    if resp.status_code == 201:
        policy_id = resp.json().get("returnPolicyId")
        print(f"   ✅ Return policy created: {policy_id}")
        return policy_id
    print(f"   ❌ Return policy creation failed: {resp.status_code}")
    print_ebay_error(resp)
    return None


def create_fulfillment_policy(token):
    print("   Creating default fulfillment policy...")
    payload = {
        "name": "Default Fulfillment Policy",
        "marketplaceId": MARKETPLACE_ID,
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
        "handlingTime": {"value": 1, "unit": "DAY"},
        "shippingOptions": [
            {
                "optionType": "DOMESTIC",
                "costType": "FLAT_RATE",
                "shippingServices": [
                    {
                        "sortOrder": 1,
                        "shippingCarrierCode": "USPS",
                        "shippingServiceCode": "USPSPriorityFlatRateBox",
                        "shippingCost": {"value": "0.00", "currency": "USD"},
                        "freeShipping": True,
                        "buyerResponsibleForShipping": False,
                    }
                ],
            }
        ],
    }
    resp = api_call("POST", f"{BASE_ACCOUNT}/fulfillment_policy", token, payload)
    if resp.status_code == 201:
        policy_id = resp.json().get("fulfillmentPolicyId")
        print(f"   ✅ Fulfillment policy created: {policy_id}")
        return policy_id
    print(f"   ❌ Fulfillment policy creation failed: {resp.status_code}")
    print_ebay_error(resp)
    return None


def get_business_policies(token):
    print("\n📋 Step 2c: Fetching (or creating) business policies...")

    payment_id = get_first_policy_id(token, "payment_policy", "paymentPolicies", "paymentPolicyId")
    if not payment_id:
        payment_id = create_payment_policy(token)

    return_id = get_first_policy_id(token, "return_policy", "returnPolicies", "returnPolicyId")
    if not return_id:
        return_id = create_return_policy(token)

    fulfillment_id = get_first_policy_id(
        token, "fulfillment_policy", "fulfillmentPolicies", "fulfillmentPolicyId"
    )
    if not fulfillment_id:
        fulfillment_id = create_fulfillment_policy(token)

    if not all([payment_id, return_id, fulfillment_id]):
        print("\n❌ Still missing one or more business policies after attempting to create them.")
        print("   Double-check that Step 2b (opt-in) succeeded above.")
        raise SystemExit(1)

    print(f"✅ Using paymentPolicyId={payment_id}, returnPolicyId={return_id}, "
          f"fulfillmentPolicyId={fulfillment_id}")
    return payment_id, return_id, fulfillment_id


# -----------------------------------------------------------------------------
# STEP 3: OFFER
# -----------------------------------------------------------------------------
def create_or_update_offer(token, payment_id, return_id, fulfillment_id):
    print("\n🛒 Step 3: Creating offer...")
    offer_data = {
        "sku": SKU,
        "marketplaceId": MARKETPLACE_ID,
        "format": "FIXED_PRICE",
        "quantity": 10,
        "categoryId": CATEGORY_ID,
        "price": {"value": "19.99", "currency": "USD"},
        "listingDescription": "Test product for FYP inventory sync - Buy now!",
        "merchantLocationKey": LOCATION_KEY,
        "listingPolicies": {
            "paymentPolicyId": payment_id,
            "returnPolicyId": return_id,
            "fulfillmentPolicyId": fulfillment_id,
        },
    }

    resp = api_call("POST", f"{BASE_INVENTORY}/offer", token, offer_data)

    if resp.status_code == 201:
        offer_id = resp.json().get("offerId")
        print(f"✅ Offer created! Offer ID: {offer_id}")
        return offer_id

    if resp.status_code == 400 and 25002 in get_error_ids(resp):
        print("ℹ️ Offer already exists for this SKU/marketplace, fetching it...")
        lookup = api_call(
            "GET", f"{BASE_INVENTORY}/offer", token,
            params={"sku": SKU, "marketplace_id": MARKETPLACE_ID},
        )
        offers = lookup.json().get("offers", []) if lookup.status_code == 200 else []
        if offers:
            offer_id = offers[0]["offerId"]
            update_resp = api_call("PUT", f"{BASE_INVENTORY}/offer/{offer_id}", token, offer_data)
            if update_resp.status_code == 200:
                print(f"✅ Existing offer updated! Offer ID: {offer_id}")
                return offer_id
            print(f"❌ Offer update failed: {update_resp.status_code}")
            print_ebay_error(update_resp)
            raise SystemExit(1)
        print("❌ Could not find the existing offer to update.")
        print_ebay_error(lookup)
        raise SystemExit(1)

    print(f"❌ Offer creation failed: {resp.status_code}")
    print_ebay_error(resp)
    raise SystemExit(1)


# -----------------------------------------------------------------------------
# STEP 4: PUBLISH
# -----------------------------------------------------------------------------
def publish_offer(token, offer_id):
    print("\n🚀 Step 4: Publishing offer...")
    resp = api_call("POST", f"{BASE_INVENTORY}/offer/{offer_id}/publish", token)
    if resp.status_code == 200:
        listing_id = resp.json().get("listingId")
        print("=" * 50)
        print("🎉 SUCCESS! LISTING IS LIVE!")
        print("=" * 50)
        print(f"📋 Listing ID: {listing_id}")
        print(f"🔗 View as BUYER: https://sandbox.ebay.com/itm/{listing_id}")
        print("=" * 50)
        print("\n🛒 To place a test order:")
        print("1. Go to: https://sandbox.ebay.com")
        print("2. Sign in with your BUYER sandbox test user")
        print("3. Search for: Test Product - FYP Sync")
        print("4. Click 'Buy It Now' and complete checkout")
        print("=" * 50)
    elif resp.status_code == 400 and 25002 in get_error_ids(resp):
        print("ℹ️ Offer is already published.")
    else:
        print(f"❌ Publishing failed: {resp.status_code}")
        print_ebay_error(resp)
        raise SystemExit(1)


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main():
    print("=" * 50)
    print("🚀 EBAY LISTING CREATION (BUYER FLOW TEST)")
    print("=" * 50)

    token = get_fresh_access_token()
    create_location(token)
    create_inventory_item(token)
    opt_in_to_business_policies(token)
    payment_id, return_id, fulfillment_id = get_business_policies(token)
    offer_id = create_or_update_offer(token, payment_id, return_id, fulfillment_id)
    publish_offer(token, offer_id)


if __name__ == "__main__":
    main()