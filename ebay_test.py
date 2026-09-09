import requests

def ebay_api_call(method, endpoint, token, data=None, marketplace_id="EBAY_US"):
    """Helper function to make eBay API calls with required headers"""
    url = f"https://api.sandbox.ebay.com/sell/inventory/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
        "X-EBAY-C-MARKETPLACE-ID": marketplace_id
    }
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    return response

# Load token
with open("ebay_token.txt", "r") as f:
    token = f.read().strip()

# 1. Create a product
print("Creating product...")
data = {
    "product": {
        "title": "Test Product - FYP Sync",
        "description": "Test product for inventory sync"
    },
    "condition": "NEW",
    "availability": {
        "shipToLocationAvailability": {
            "quantity": 10
        }
    }
}
response = ebay_api_call("PUT", "inventory_item/TEST-SKU-001", token, data)
print(f"Create Status: {response.status_code}")

# Handle 204 (No Content - success, but no body)
if response.status_code == 204:
    print("✅ Product created successfully (SKU: TEST-SKU-001)")
else:
    try:
        print(response.json())
    except:
        print(response.text)

# 2. Get the product (should now exist)
print("\nGetting product...")
response = ebay_api_call("GET", "inventory_item/TEST-SKU-001", token)
print(f"Get Status: {response.status_code}")
if response.status_code == 200:
    print("Product details:")
    print(response.json())
else:
    print(response.text)

# 3. List all products
print("\nListing all products...")
response = ebay_api_call("GET", "inventory_item", token)
print(f"List Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Total products: {data.get('total', 0)}")
    print("Products:", data)
else:
    print(response.text)