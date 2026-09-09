import requests
import base64
import socket

# Test DNS resolution
try:
    ip = socket.gethostbyname("api.sandbox.ebay.com")
    print(f"✅ DNS resolved: api.sandbox.ebay.com -> {ip}")
except:
    print("❌ DNS resolution failed. Check your internet connection.")
    exit(1)

client_id = "Muhammad-FYPInven-SBX-7650e493c-bccee85a"
client_secret = "SBX-650e493ca76f-c2e6-41cb-8836-a935"

# URL-encoded authorization code
auth_code = "v%5E1.1%23i%5E1%23I%5E3%23f%5E0%23r%5E1%23p%5E3%23t%5EUl41XzEwOkJEQTlBODBGOEY5QjIxRkI5RkExQkQ0MTVCQTU4RTlBXzFfMSNFXjEyODQ%3D"

auth_string = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {auth_string}"
}
data = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "redirect_uri": "https://scanning-onstage-scrambled.ngrok-free.dev/ebay/callback"
}

try:
    response = requests.post(url, headers=headers, data=data, timeout=30)
    print("Status:", response.status_code)
    print("Response:", response.json())
    
    if response.status_code == 200:
        tokens = response.json()
        print("\n✅ ACCESS TOKEN:", tokens.get("access_token"))
        print("✅ REFRESH TOKEN:", tokens.get("refresh_token"))
        print("✅ EXPIRES IN:", tokens.get("expires_in"), "seconds")
except requests.exceptions.ConnectionError:
    print("❌ Connection error. Check your internet connection.")
except Exception as e:
    print(f"❌ Error: {e}")