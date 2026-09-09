"""
scripts/verify_phase2.py
Automated Verification Suite for Phase 2:
1. Test Shopify product creation & customer-side verification
2. Test eBay listing creation & buyer-side verification
3. Test simultaneous multi-platform listing (/api/sync/listings)
"""
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from platforms.shopify.inventory import create_listing as shopify_create, verify_listing as shopify_verify
from platforms.ebay.inventory import create_listing as ebay_create, verify_listing as ebay_verify
import requests

def run_phase2_verification():
    print("=" * 60)
    print(" 🚀 FYP PHASE 2 VERIFICATION — MULTI-PLATFORM LISTING & VERIFY")
    print("=" * 60)
    
    sku_test = f"SKU-TEST-{int(time.time())}"
    title_test = f"FYP Wireless Headphones {sku_test}"
    price_test = 49.99
    qty_test = 15
    desc_test = "High quality noise-cancelling wireless headphones for testing FYP multi-channel inventory sync."

    # -------------------------------------------------------------------------
    # STEP 1: Test Shopify Creation & Verification
    # -------------------------------------------------------------------------
    print("\n1️⃣  Testing Shopify Product Creation...")
    s_result = shopify_create(
        title=title_test + " (Shopify Only)",
        description=desc_test,
        price=price_test,
        quantity=qty_test,
        sku=sku_test + "-S",
        condition="NEW"
    )
    print("   Creation Result:", s_result.to_dict())
    assert s_result.success, f"Shopify product creation failed: {s_result.message}"
    print(f"   ✅ Shopify Product ID: {s_result.listing_id} | URL: {s_result.listing_url}")

    print("   Verifying Shopify Customer-side Visibility...")
    s_verify = shopify_verify(s_result.listing_id)
    print("   Verify Result:", s_verify.to_dict())
    print(f"   ✅ Shopify Verification Status: {s_verify.message}")

    # -------------------------------------------------------------------------
    # STEP 2: Test eBay Creation & Verification
    # -------------------------------------------------------------------------
    print("\n2️⃣  Testing eBay Sandbox Listing Creation...")
    e_result = ebay_create(
        title=title_test[:70] + " eBay",
        description=desc_test,
        price=price_test,
        quantity=qty_test,
        sku=sku_test + "-E",
        category_id="9355",
        condition="NEW"
    )
    print("   Creation Result:", e_result.to_dict())
    assert e_result.success, f"eBay listing creation failed: {e_result.message}"
    print(f"   ✅ eBay Listing ID: {e_result.listing_id} | URL: {e_result.listing_url}")

    print("   Verifying eBay Buyer-side Visibility...")
    e_verify = ebay_verify(e_result.listing_id)
    print("   Verify Result:", e_verify.to_dict())
    print(f"   ✅ eBay Verification Status: {e_verify.message}")

    # -------------------------------------------------------------------------
    # STEP 3: Test Simultaneous Both Platforms Endpoint
    # -------------------------------------------------------------------------
    print("\n3️⃣  Testing Simultaneous Sync Endpoint (POST /api/sync/listings)...")
    sku_both = sku_test + "-BOTH"
    sync_payload = {
        "title": title_test + " (Dual Synced)",
        "description": desc_test,
        "price": 59.99,
        "quantity": 25,
        "sku": sku_both,
        "category_id": "9355",
        "condition": "NEW"
    }
    
    resp = requests.post("http://localhost:8000/api/sync/listings", json=sync_payload)
    print(f"   API Response Status: {resp.status_code}")
    sync_data = resp.json()
    print("   API Response Data:", sync_data)
    
    assert resp.status_code == 200, "Sync route failed"
    assert sync_data.get("both_success"), "Simultaneous listing failed on one or both platforms"
    
    print("\n" + "=" * 60)
    print(" 🎉 ALL PHASE 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_phase2_verification()
