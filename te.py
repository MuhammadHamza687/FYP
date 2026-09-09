import requests
import base64

client_id = "Muhammad-FYPInven-SBX-7650e493c-bccee85a"
client_secret = "SBX-650e493ca76f-c2e6-41cb-8836-a935"

# Use the URL‑encoded code (copy it exactly as it appears in the callback URL)
auth_code = "v%5E1.1%23i%5E1%23p%5E3%23f%5E0%23I%5E3%23r%5E1%23t%5EUl41XzEwOkE2NzVDNDY0MTU1MDk3MUZEOTNEQTIzOEFGMkI5MDI1XzBfMSNFXjEyODQ%3D"

# Encode client_id:client_secret in Base64
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

response = requests.post(url, headers=headers, data=data)
print(response.status_code)
print(response.json())