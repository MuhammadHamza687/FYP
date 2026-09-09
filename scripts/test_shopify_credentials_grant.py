"""
scripts/test_shopify_credentials_grant.py
Test Shopify OAuth token endpoints with form-urlencoded.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from core.config import settings

def test_grant(url):
    print(f"\nTesting POST {url} ...")
    payload = {
        "client_id": settings.shopify_api_key,
        "client_secret": settings.shopify_api_secret,
        "grant_type": "client_credentials",
    }
    try:
        resp = requests.post(
            url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        print(f"Status Code: {resp.status_code}")
        print("Response text:", resp.text[:300])
        if resp.status_code == 200:
            token_data = resp.json()
            token = token_data.get("access_token")
            print("✅ SUCCESS! Access Token:", token)
            return token
    except Exception as e:
        print("Error:", e)
    return None

if __name__ == "__main__":
    shop_id = "73575071875"
    domain = settings.shopify_store
    
    endpoints = [
        f"https://{domain}/admin/oauth/access_token",
        f"https://shopify.com/{shop_id}/auth/oauth/access_token",
        f"https://admin.shopify.com/store/fyp-sync/oauth/access_token"
    ]
    
    for ep in endpoints:
        test_grant(ep)
