"""
scripts/verify_phase2.py
Automated Verification Suite for Phase 2:
1. Shopify product creation & customer-side verification
2. Shopify SKU collision (update instead of duplicate)
3. eBay listing creation & buyer-side verification
4. eBay SKU collision (reuse offer/listing)
5. Simultaneous multi-platform listing (POST /api/sync/listings)
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from platforms.shopify.inventory import create_listing as shopify_create, verify_listing as shopify_verify
from platforms.ebay.inventory import create_listing as ebay_create, verify_listing as ebay_verify

API = "http://127.0.0.1:8000"
FAILED = []


def _ok(name: str, cond: bool, detail: str = ""):
    if cond:
        print(f"   PASS {name}" + (f" -- {detail}" if detail else ""))
    else:
        print(f"   FAIL {name}" + (f" -- {detail}" if detail else ""))
        FAILED.append(f"{name}: {detail}")


def run_phase2_verification():
    print("=" * 60)
    print(" FYP PHASE 2 — LIST + VERIFY + SKU COLLISION")
    print("=" * 60)

    sku_base = f"SKU-P2-{int(time.time())}"
    title = f"FYP Phase2 Headphones {sku_base}"
    desc = "FYP multi-channel listing verification product."
    price = 49.99
    qty = 15

    # -------------------------------------------------------------------------
    print("\n1) Shopify create + customer-side verify")
    s_sku = sku_base + "-S"
    s_result = shopify_create(
        title=title + " Shopify",
        description=desc,
        price=price,
        quantity=qty,
        sku=s_sku,
        condition="NEW",
    )
    print("   create:", s_result.to_dict())
    _ok("Shopify create success", s_result.success, s_result.message)
    _ok("Shopify listing_id present", bool(s_result.listing_id), s_result.listing_id)

    s_verify = shopify_verify(s_result.listing_id)
    print("   verify:", s_verify.to_dict())
    _ok("Shopify storefront visible", s_verify.visible, s_verify.message)

    print("\n2) Shopify SKU collision (same SKU must update, not duplicate)")
    s_again = shopify_create(
        title=title + " Shopify UPDATED",
        description=desc,
        price=59.99,
        quantity=7,
        sku=s_sku,
        condition="NEW",
    )
    print("   collide:", s_again.to_dict())
    _ok("Shopify collision success", s_again.success, s_again.message)
    _ok(
        "Shopify same listing_id after collision",
        s_again.listing_id == s_result.listing_id,
        f"{s_result.listing_id} vs {s_again.listing_id}",
    )
    _ok(
        "Shopify collision message indicates update",
        "update" in s_again.message.lower() or "exist" in s_again.message.lower(),
        s_again.message,
    )
    s_verify2 = shopify_verify(s_again.listing_id)
    _ok("Shopify still visible after update", s_verify2.visible, s_verify2.message)
    if s_verify2.price:
        _ok("Shopify price updated on storefront", str(s_verify2.price).startswith("59.99"), str(s_verify2.price))

    # -------------------------------------------------------------------------
    print("\n3) eBay create + buyer-side verify")
    e_sku = sku_base + "-E"
    e_result = ebay_create(
        title=(title + " eBay")[:80],
        description=desc,
        price=price,
        quantity=qty,
        sku=e_sku,
        category_id="9355",
        condition="NEW",
    )
    print("   create:", e_result.to_dict())
    _ok("eBay create success", e_result.success, e_result.message)
    _ok("eBay listing_id present", bool(e_result.listing_id), e_result.listing_id)

    e_verify = ebay_verify(e_result.listing_id)
    print("   verify:", e_verify.to_dict())
    _ok("eBay listing published/visible", e_verify.visible, e_verify.message)

    print("\n4) eBay SKU collision (reuse existing offer/listing)")
    e_again = ebay_create(
        title=(title + " eBay UPDATED")[:80],
        description=desc,
        price=64.99,
        quantity=8,
        sku=e_sku,
        category_id="9355",
        condition="NEW",
    )
    print("   collide:", e_again.to_dict())
    _ok("eBay collision success", e_again.success, e_again.message)
    _ok(
        "eBay same listing_id after collision",
        e_again.listing_id == e_result.listing_id,
        f"{e_result.listing_id} vs {e_again.listing_id}",
    )
    e_verify2 = ebay_verify(e_again.listing_id)
    _ok("eBay still published after update", e_verify2.visible, e_verify2.message)

    # -------------------------------------------------------------------------
    print("\n5) Dashboard API: POST /api/sync/listings (both platforms)")
    sku_both = sku_base + "-BOTH"
    sync_payload = {
        "title": (title + " Dual")[:80],
        "description": desc,
        "price": 59.99,
        "quantity": 25,
        "sku": sku_both,
        "category_id": "9355",
        "condition": "NEW",
    }
    try:
        health = requests.get(f"{API}/health", timeout=5)
        _ok("FastAPI /health", health.status_code == 200, str(health.status_code))
    except Exception as e:
        _ok("FastAPI /health", False, str(e))
        print("\nStart the server with: python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        _finish()
        return

    resp = requests.post(f"{API}/api/sync/listings", json=sync_payload, timeout=120)
    print(f"   HTTP {resp.status_code}")
    try:
        sync_data = resp.json()
    except Exception:
        sync_data = {}
    print("   body:", sync_data)
    _ok("sync HTTP 200", resp.status_code == 200, str(resp.status_code))
    _ok("both_success", bool(sync_data.get("both_success")), str(sync_data))

    ebay_id = (sync_data.get("ebay") or {}).get("listing_id")
    shopify_id = (sync_data.get("shopify") or {}).get("listing_id")
    if ebay_id:
        ev = requests.get(f"{API}/api/ebay/listings/{ebay_id}/verify", timeout=60)
        print("   ebay verify API:", ev.json() if ev.ok else ev.text[:200])
        _ok("GET /api/ebay/listings/{id}/verify", ev.ok and ev.json().get("visible"), ev.text[:200])
    if shopify_id:
        sv = requests.get(f"{API}/api/shopify/listings/{shopify_id}/verify", timeout=60)
        print("   shopify verify API:", sv.json() if sv.ok else sv.text[:200])
        _ok("GET /api/shopify/listings/{id}/verify", sv.ok and sv.json().get("visible"), sv.text[:200])

    print("\n6) Dashboard API SKU collision via POST /api/shopify/listings")
    collide_api = requests.post(
        f"{API}/api/shopify/listings",
        json={**sync_payload, "title": sync_payload["title"] + " API-UPDATE", "price": 71.11},
        timeout=60,
    )
    collide_json = collide_api.json() if collide_api.ok else {}
    print("   collide API:", collide_json)
    _ok("API collision HTTP 200", collide_api.status_code == 200)
    _ok(
        "API collision kept same Shopify id",
        collide_json.get("listing_id") == shopify_id,
        f"{shopify_id} vs {collide_json.get('listing_id')}",
    )

    _finish()


def _finish():
    print("\n" + "=" * 60)
    if FAILED:
        print(f" PHASE 2 FAILED ({len(FAILED)} check(s))")
        for item in FAILED:
            print("  -", item)
        print("=" * 60)
        sys.exit(1)
    print(" ALL PHASE 2 VERIFICATION TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    run_phase2_verification()
