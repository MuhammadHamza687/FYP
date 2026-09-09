# Phase 0 & Phase 1 Walkthrough — FYP Inventory Sync Dashboard

## What Was Built & Verified

**Phases 0 and 1 are 100% complete.** Both eBay Sandbox and Shopify custom app authentication are connected and verified via dynamic token retrieval.

---

## Verification Results

| Check | Result | Details |
|---|---|---|
| FastAPI Server | ✅ ONLINE | Running on port 8000 |
| ngrok Tunnel | ✅ ONLINE | Tunneling via dynamic HTTPS URL |
| All 24 API routes | ✅ REGISTERED | Responding clean 200 OK |
| **eBay Sandbox Connection** | ✅ CONNECTED | Token auto-refreshed, Sandbox seller account active |
| **Shopify Admin API Connection** | ✅ CONNECTED | Client Credentials Grant token retrieval connected (`fyp-sync.myshopify.com`, Basic App Development plan) |

---

## File Structure

```
e:\FYP\
├── main.py                    ← Dashboard server + router mounts
├── dashboard.html             ← Premium glassmorphism control panel (49KB)
├── core/
│   └── config.py              ← Single source of truth for credentials
├── platforms/
│   ├── base.py                ← Abstract PlatformAdapter interface
│   ├── ebay/
│   │   ├── auth.py            ← Token refresh with in-memory caching
│   │   └── inventory.py       ← Listing flow + buyer-side verify
│   └── shopify/
│       ├── auth.py            ← Client Credentials Grant auto-token fetch
│       └── inventory.py       ← Product create/verify/fetch/update
├── api/
│   └── dashboard_routes.py    ← 24 API routes for the dashboard
├── docs/
│   ├── ROADMAP.md             ← Master architecture plan
│   ├── TASK.md                ← Phase-by-phase tracker
│   └── WALKTHROUGH.md         ← Live setup & verification status
└── scripts/
    ├── start_server.py        ← One-click FastAPI + ngrok launcher
    └── test_shopify_credentials_grant.py ← Verification test script
```

---

## How to Run

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open: **`http://localhost:8000`** or embedded in Shopify Admin app iframe.

---

## Platform Auth Implementation Details

1. **eBay**: Uses OAuth 2.0 Refresh Token flow to obtain short-lived access tokens, cached automatically in memory.
2. **Shopify**: Uses OAuth `client_credentials` grant on `https://fyp-sync.myshopify.com/admin/oauth/access_token` with form-encoded data (`application/x-www-form-urlencoded`). Auto-refreshes on 401 response seamlessly.
