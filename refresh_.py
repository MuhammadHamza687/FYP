import requests
import base64

client_id = "Muhammad-FYPInven-SBX-7650e493c-bccee85a"
client_secret = "SBX-650e493ca76f-c2e6-41cb-8836-a935"
refresh_token = "v^1.1#i^1#f^0#I^3#r^1#p^3#t^Ul4xMF81OjY4NTgwOUEwRjIzRjE1RjAwMDgxMjc4NUI0QjUyQzNEXzJfMSNFXjEyODQ="

auth_string = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {auth_string}"
}
data = {
    "grant_type": "refresh_token",
    "refresh_token": refresh_token
}

response = requests.post(url, headers=headers, data=data)
tokens = response.json()
print("Status:", response.status_code)
if response.status_code == 200:
    print("✅ ACCESS TOKEN:", tokens.get("access_token"))
    print("✅ REFRESH TOKEN (same):", tokens.get("refresh_token"))
    print("✅ EXPIRES IN:", tokens.get("expires_in"), "seconds")
else:
    print("Error:", tokens)