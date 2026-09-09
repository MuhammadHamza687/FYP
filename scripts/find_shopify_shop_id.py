"""
scripts/find_shopify_shop_id.py
Inspects Shopify store to find numeric shop_id and tests Client Credentials token exchange.
"""
import requests
import re
from core.config import settings

def find_shop_id():
    url = f"https://{settings.shopify_store}"
    print(f"Fetching {url}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    print("Status:", resp.status_code)
    
    # Check common JS objects in Shopify themes: BOOMR.shopId = '123456';
    patterns = [
        r"BOOMR\.shopId\s*=\s*['\"](\d+)['\"]",
        r"\"shopId\":\s*(\d+)",
        r"Shopify\.shop\s*=\s*['\"][^'\"]*['\"];\s*Shopify\.theme\s*=\s*\{[^}]*\"id\":(\d+)",
        r"myshopify\.com[^\"]*\"id\":\s*(\d+)",
        r"cdn\.shopify\.com/s/files/1/(\d+)/",
    ]
    
    found = set()
    for p in patterns:
        matches = re.findall(p, resp.text)
        found.update(matches)
        
    print("Found potential Shop IDs:", found)
    return list(found)

def test_client_credentials(shop_id):
    endpoint = f"https://shopify.com/{shop_id}/auth/oauth/access_token"
    print(f"\nTesting client_credentials at {endpoint}...")
    payload = {
        "client_id": settings.shopify_api_key,
        "client_secret": settings.shopify_api_secret,
        "grant_type": "client_credentials"
    }
    resp = requests.post(endpoint, json=payload)
    print("Status:", resp.status_code)
    print("Response:", resp.text)
    return resp.json() if resp.status_code == 200 else None

if __name__ == "__main__":
    ids = find_shop_id()
    for sid in ids:
        test_client_credentials(sid)
