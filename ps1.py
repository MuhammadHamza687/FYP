import requests

with open("ebay_token.txt", "r") as f:
    token = f.read().strip()

def ebay_api_call(method, endpoint, token, data=None, marketplace_id="EBAY_US"):
    url = f"https://api.sandbox.ebay.com/sell/account/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
        "X-EBAY-C-MARKETPLACE-ID": marketplace_id
    }
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    return response

# 1. Get fulfillment policies
print("Getting fulfillment policies...")
response = ebay_api_call("GET", "fulfillment_policy", token)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(response.json())
else:
    print(response.text)

# 2. Get payment policies
print("\nGetting payment policies...")
response = ebay_api_call("GET", "payment_policy", token)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(response.json())
else:
    print(response.text)

# 3. Get return policies
print("\nGetting return policies...")
response = ebay_api_call("GET", "return_policy", token)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(response.json())
else:
    print(response.text)