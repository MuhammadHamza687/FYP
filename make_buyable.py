import requests

with open("ebay_token.txt", "r") as f:
    token = f.read().strip()

BASE_INVENTORY = "https://api.sandbox.ebay.com/sell/inventory/v1"
BASE_ACCOUNT = "https://api.sandbox.ebay.com/sell/account/v1"


def headers():
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }


def ebay_api_call(method, url, data=None, params=None):
    if method == "GET":
        return requests.get(url, headers=headers(), params=params)
    elif method == "POST":
        return requests.post(url, headers=headers(), json=data)
    elif method == "PUT":
        return requests.put(url, headers=headers(), json=data)
    elif method == "DELETE":
        return requests.delete(url, headers=headers())
    return None


def print_ebay_error(response):
    """Print the actual eBay error payload instead of raw text."""
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


print("=" * 50)
print("🚀 EBAY LISTING CREATION (BUYER FLOW TEST)")
print("=" * 50)

# CONFIGURATION
location_key = "MY_WAREHOUSE"
sku = "TEST-SKU-001"
category_id = "9355"  # <-- set this to a real leaf category ID for your item type

# ---------------------------------------------------------------------------
# STEP 1: CREATE LOCATION
# ---------------------------------------------------------------------------
print("\n📍 Step 1: Creating location...")
location_data = {
    "location": {
        "address": {
            "addressLine1": "123 Main Street",
            "city": "San Jose",
            "stateOrProvince": "CA",
            "postalCode": "95101",
            "country": "US"
        }
    },
    "name": "Main Warehouse",
    "merchantLocationStatus": "ENABLED",
    "locationTypes": ["WAREHOUSE"]
}
response = ebay_api_call("PUT", f"{BASE_INVENTORY}/location/{location_key}", location_data)
if response.status_code == 204:
    print("✅ Location created successfully!")
elif response.status_code == 400 and 25802 in get_error_ids(response):
    # 25802 = "The merchant location ... already exists"
    print("ℹ️ Location already exists, continuing...")
else:
    print(f"⚠️ Location status: {response.status_code}")
    print_ebay_error(response)
    print("\nStopping here — fix the location error above before continuing.")
    exit(1)

# ---------------------------------------------------------------------------
# STEP 2: CREATE INVENTORY ITEM
# ---------------------------------------------------------------------------
print("\n📦 Step 2: Creating inventory item...")
inventory_data = {
    "product": {
        "title": "Test Product - FYP Sync",
        "description": "Test product for inventory synchronization demo"
    },
    "condition": "NEW",
    "availability": {
        "shipToLocationAvailability": {
            "quantity": 10
        }
    }
}
response = ebay_api_call("PUT", f"{BASE_INVENTORY}/inventory_item/{sku}", inventory_data)
if response.status_code == 204:
    print("✅ Inventory item created successfully!")
else:
    print(f"⚠️ Inventory status: {response.status_code}")
    print_ebay_error(response)
    exit(1)

# ---------------------------------------------------------------------------
# STEP 2b: FETCH BUSINESS POLICIES (required for creating an offer)
# ---------------------------------------------------------------------------
print("\n📋 Step 2b: Fetching business policies...")


def get_first_policy_id(policy_type_path, response_key):
    resp = ebay_api_call(
        "GET",
        f"{BASE_ACCOUNT}/{policy_type_path}",
        params={"marketplace_id": "EBAY_US"}
    )
    if resp.status_code != 200:
        print(f"⚠️ Could not fetch {policy_type_path}: {resp.status_code}")
        print_ebay_error(resp)
        return None
    items = resp.json().get(response_key, [])
    if not items:
        print(f"⚠️ No {policy_type_path.replace('_', ' ')} found on this sandbox account.")
        return None
    return items[0].get(
        {
            "payment_policy": "paymentPolicyId",
            "return_policy": "returnPolicyId",
            "fulfillment_policy": "fulfillmentPolicyId",
        }[policy_type_path]
    )


payment_policy_id = get_first_policy_id("payment_policy", "paymentPolicies")
return_policy_id = get_first_policy_id("return_policy", "returnPolicies")
fulfillment_policy_id = get_first_policy_id("fulfillment_policy", "fulfillmentPolicies")

if not all([payment_policy_id, return_policy_id, fulfillment_policy_id]):
    print("\n❌ Missing one or more business policies (payment/return/fulfillment).")
    print("   Create default policies for your sandbox seller account, either:")
    print("   - In Seller Hub (sandbox) under Account > Business Policies, or")
    print("   - Via POST /sell/account/v1/payment_policy (and return_policy, fulfillment_policy)")
    exit(1)

print(f"✅ Using paymentPolicyId={payment_policy_id}, returnPolicyId={return_policy_id}, "
      f"fulfillmentPolicyId={fulfillment_policy_id}")

# ---------------------------------------------------------------------------
# STEP 3: CREATE (OR UPDATE) OFFER
# ---------------------------------------------------------------------------
print("\n🛒 Step 3: Creating offer...")

offer_data = {
    "sku": sku,
    "marketplaceId": "EBAY_US",
    "format": "FIXED_PRICE",
    "quantity": 10,
    "categoryId": category_id,
    "price": {
        "value": "19.99",
        "currency": "USD"
    },
    "listingDescription": "Test product for FYP inventory sync - Buy now!",
    "merchantLocationKey": location_key,
    "listingPolicies": {
        "paymentPolicyId": payment_policy_id,
        "returnPolicyId": return_policy_id,
        "fulfillmentPolicyId": fulfillment_policy_id
    }
}

response = ebay_api_call("POST", f"{BASE_INVENTORY}/offer", offer_data)
offer_id = None

if response.status_code == 201:
    offer_id = response.json().get("offerId")
    print(f"✅ Offer created! Offer ID: {offer_id}")
elif response.status_code == 400 and 25002 in get_error_ids(response):
    # 25002 = "Offer entity already exists" -> look it up and update instead
    print("ℹ️ Offer already exists for this SKU/marketplace, fetching it...")
    lookup = ebay_api_call(
        "GET", f"{BASE_INVENTORY}/offer", params={"sku": sku, "marketplace_id": "EBAY_US"}
    )
    offers = lookup.json().get("offers", []) if lookup.status_code == 200 else []
    if offers:
        offer_id = offers[0]["offerId"]
        update_resp = ebay_api_call("PUT", f"{BASE_INVENTORY}/offer/{offer_id}", offer_data)
        if update_resp.status_code == 200:
            print(f"✅ Existing offer updated! Offer ID: {offer_id}")
        else:
            print(f"❌ Offer update failed: {update_resp.status_code}")
            print_ebay_error(update_resp)
            exit(1)
    else:
        print("❌ Could not find the existing offer to update.")
        print_ebay_error(lookup)
        exit(1)
else:
    print(f"❌ Offer creation failed: {response.status_code}")
    print_ebay_error(response)
    exit(1)

# ---------------------------------------------------------------------------
# STEP 4: PUBLISH OFFER
# ---------------------------------------------------------------------------
print("\n🚀 Step 4: Publishing offer...")
response = ebay_api_call("POST", f"{BASE_INVENTORY}/offer/{offer_id}/publish")
if response.status_code == 200:
    listing_id = response.json().get("listingId")
    print("=" * 50)
    print("🎉 SUCCESS! LISTING IS LIVE!")
    print("=" * 50)
    print(f"📋 Listing ID: {listing_id}")
    print(f"🔗 View as BUYER: https://sandbox.ebay.com/itm/{listing_id}")
    print("=" * 50)
    print("\n🛒 To place a test order:")
    print("1. Go to: https://sandbox.ebay.com")
    print("2. Sign in with BUYER account:")
    print("   Username: TESTUSER_TESTUSER_hamza-buyer")
    print("   Password: Test@123456")
    print("3. Search for: Test Product - FYP Sync")
    print("4. Click 'Buy It Now' and complete checkout")
    print("=" * 50)
else:
    print(f"❌ Publishing failed: {response.status_code}")
    print_ebay_error(response)