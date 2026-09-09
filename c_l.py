import requests

with open("ebay_token.txt", "r") as f:
    token = f.read().strip()

def ebay_api_call(method, endpoint, token, data=None):
    # Using the standard eBay Sandbox Inventory API base URL
    url = f"https://api.sandbox.ebay.com/sell/inventory/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    if method == "GET":
        return requests.get(url, headers=headers)
    elif method == "POST":
        return requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        return requests.put(url, headers=headers, json=data)
    return None

# Step 1: Create a location
print("Creating location...")

# FIX 1: Defined a clean, distinct identifier for your warehouse
merchant_location_key = "MAIN_WAREHOUSE_001" 

# FIX 2: Wrapped the data structure to meet eBay's exact specifications
location_data = {
    "location": {
        "address": {
            "addressLine1": "123 Test Street",
            "city": "San Jose",
            "stateOrProvince": "CA",
            "postalCode": "95101",
            "country": "US"
        }
    },
    "name": "Main Warehouse",
    "merchantLocationStatus": "ENABLED",
    "locationTypes": [
        "STORE"  # Note: "STORE" or "WAREHOUSE" are acceptable, but STORE is universally supported for inventory fulfillment
    ]
}

# The endpoint must end with your unique merchantLocationKey
endpoint = f"location/{merchant_location_key}"

response = ebay_api_call("PUT", endpoint, token, location_data)

if response is None:
    print("No response from API")
else:
    print(f"Location Status: {response.status_code}")
    # Treat any 2xx status as success
    if 200 <= response.status_code < 300:
        print(f"✅ Location '{merchant_location_key}' created/updated successfully!")
    else:
        print("Location error:", response.text)
