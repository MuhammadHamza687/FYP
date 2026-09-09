# Phase 0 Walkthrough — FYP Inventory Sync Dashboard

## What Was Built

**Phase 0 is complete.** The project now has a full modular foundation with a premium live dashboard.

---

## New File Structure

```
e:\FYP\
├── main.py                    ← Rebuilt: serves dashboard + mounts API routers
├── dashboard.html             ← NEW: premium glassmorphism control panel (49KB)
├── core/
│   └── config.py              ← NEW: typed Pydantic settings from .env
├── platforms/
│   ├── base.py                ← NEW: abstract PlatformAdapter interface
│   ├── ebay/
│   │   ├── auth.py            ← NEW: token refresh with in-memory caching
│   │   └── inventory.py       ← NEW: full listing flow + buyer-side verify
│   └── shopify/
│       ├── auth.py            ← NEW: static token + connection test
│       └── inventory.py       ← NEW: product create/verify/fetch/update
├── api/
│   └── dashboard_routes.py    ← NEW: 24 API routes for the dashboard
└── scripts/
    └── start_server.py        ← NEW: one-click FastAPI + ngrok launcher
```

---

## How to Start (Two Ways)

### Option A — One-click launcher (FastAPI + ngrok together)
```bash
python scripts/start_server.py
```

### Option B — FastAPI only (for dev)
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open: **http://localhost:8000**

---

## Verification Results

| Check | Result |
|---|---|
| FastAPI starts | ✅ Running on port 8000 |
| Dashboard HTML served at `/` | ✅ 49,097 chars |
| All 24 API routes registered | ✅ |
| `/health` returns 200 | ✅ |
| eBay token refresh | ✅ Connected to Sandbox |
| Shopify connection | ⚠️ 401 — token needs refresh (see below) |

---

## ⚠️ Action Required: Shopify Token

The `SHOPIFY_ACCESS_TOKEN` in `.env` is returning a 401 (unauthorized). This means the token was either revoked or expired.

**How to fix:**
1. Go to your Shopify Admin: `https://fyp-sync.myshopify.com/admin`
2. Navigate to: **Settings → Apps and sales channels → Develop apps**
3. Find or create a **Private App / Custom App**
4. Under **Admin API access scopes**, enable: `read_products`, `write_products`, `read_inventory`, `write_inventory`, `read_orders`
5. Click **Install app** → copy the **Admin API access token**
6. Update `.env`:
   ```
   SHOPIFY_ACCESS_TOKEN=shpat_YOURNEWTOKEN
   ```

The server auto-reloads (--reload flag), so just save `.env` and click "Test Shopify" in the dashboard.

---

## Dashboard Features (Ready to Use)

| Feature | Where | What it does |
|---|---|---|
| eBay connection test | Dashboard > "Test eBay" | Refreshes token, shows expiry |
| Shopify connection test | Dashboard > "Test Shopify" | Fetches shop name/plan |
| List on both platforms | List Product page | Fills form → creates on eBay + Shopify |
| List eBay only | List Product page | eBay-only listing |
| List Shopify only | List Product page | Shopify-only product |
| Verify buyer visibility | After listing / Verify page | Calls buyer/storefront API |
| View all listings | All Listings page | Unified view + per-platform tables |
| Activity log | Dashboard / Logs page | Real-time action log |
| ngrok URL display | Header pill | Auto-fetches from ngrok API |

---

## Key Design Decisions

- **`core/config.py`** — single source of truth for all credentials. Every module imports `settings`, never reads `.env` directly. Makes credential rotation trivial.
- **`platforms/base.py`** — abstract interface means adding Amazon SP-API later is just writing one new adapter class, nothing else changes.
- **Buyer-side verification** — every listing action has a matching verify endpoint that calls the **customer-facing API** (not seller API), solving the gap in `s2.py`.
- **Modular routers** — `api/dashboard_routes.py` is the only place that handles HTTP. Platform code has zero FastAPI knowledge.

---

## Next Steps (Phase 1 → 2)

Once Shopify token is fixed, the immediate next actions are:
1. Click **"List on Both Platforms"** with a test product
2. Click **"Verify Buyer Can See It"** for both results
3. Navigate to **All Listings** to confirm both appear in the unified view

These three steps complete Phase 2 verification.
