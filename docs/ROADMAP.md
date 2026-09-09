# FYP: Multi-Channel Inventory & Order Sync — Implementation Plan & AI Handoff Roadmap

> **Design Principle:** Modular platform adapters. Every platform (eBay, Shopify, future Amazon) is a drop-in adapter. The core engine never knows which platform it's talking to.

---

## Current State (What's Already Working)

| File | Status | What it does |
|---|---|---|
| `s2.py` | ✅ Working | eBay: token refresh → location → inventory item → policies → offer → publish |
| `s1.py` | ✅ Working | eBay: token refresh only |
| `main.py` | ✅ Rebuilt | FastAPI app serving dashboard + all API routes |
| `dashboard.html` | ✅ Built | Premium glassmorphism control panel |
| `core/config.py` | ✅ Built | Typed Pydantic settings from .env |
| `platforms/ebay/auth.py` | ✅ Built | Token refresh with caching |
| `platforms/ebay/inventory.py` | ✅ Built | Full listing + buyer-side verify |
| `platforms/shopify/auth.py` | ✅ Built | Shopify static token auth |
| `platforms/shopify/inventory.py` | ✅ Built | Create/verify/fetch/update |
| `api/dashboard_routes.py` | ✅ Built | 24 API routes |
| `scripts/start_server.py` | ✅ Built | One-click FastAPI + ngrok launcher |
| `.env` | ✅ Set | Shopify + eBay Sandbox credentials + ngrok URL |

> [!IMPORTANT]
> **Shopify access token is 401 (expired/invalid).** Update `SHOPIFY_ACCESS_TOKEN` in `.env` before proceeding. See `docs/WALKTHROUGH.md` for exact steps.

---

## Architecture: Modular Platform Design

```
e:\FYP\
├── main.py                    ← FastAPI app (routes, dashboard serve)
├── dashboard.html             ← Single-file control dashboard (served by FastAPI)
├── .env                       ← All credentials
│
├── core/
│   ├── config.py              ← Load .env, shared settings (DONE)
│   ├── database.py            ← PostgreSQL connection (Phase 5)
│   ├── models.py              ← DB models (Phase 5)
│   └── sync_engine.py         ← Central sync logic (Phase 5)
│
├── platforms/
│   ├── base.py                ← Abstract PlatformAdapter class (DONE)
│   ├── ebay/
│   │   ├── auth.py            ← Token refresh (DONE)
│   │   ├── inventory.py       ← List, fetch, update, verify (DONE)
│   │   ├── orders.py          ← Fetch orders (Phase 6)
│   │   └── webhooks.py        ← eBay webhook handler (Phase 6)
│   └── shopify/
│       ├── auth.py            ← Shopify token (DONE)
│       ├── inventory.py       ← List, fetch, update, verify (DONE)
│       ├── orders.py          ← Fetch orders (Phase 6)
│       └── webhooks.py        ← Shopify HMAC webhook handler (Phase 6)
│
├── api/
│   ├── dashboard_routes.py    ← All dashboard routes (DONE)
│   ├── webhook_routes.py      ← /webhooks/shopify, /webhooks/ebay (Phase 6)
│   └── test_routes.py         ← Test trigger endpoints (Phase 9)
│
├── scripts/
│   ├── start_server.py        ← Starts FastAPI + ngrok together (DONE)
│   └── run_tests.py           ← Quick integration tests (Phase 9)
│
└── docs/                      ← AI handoff documents (THIS FOLDER)
    ├── ROADMAP.md             ← This file
    ├── TASKS.md               ← Phase-by-phase task tracker
    └── WALKTHROUGH.md         ← What was built + how to run
```

---

## Platform Credentials Summary

| Credential | eBay (Sandbox) | Shopify |
|---|---|---|
| Store / App | `Muhammad-FYPInven-SBX-*` | `fyp-sync.myshopify.com` |
| Auth | Refresh token → access token | Static access token (needs refresh!) |
| Environment | **SANDBOX** (safe to test) | Production store |
| Buyer Test URL | `sandbox.ebay.com/itm/{id}` | `fyp-sync.myshopify.com/products/{handle}` |

---

## Phased Feature Milestones

Each phase implements the **same feature on BOTH platforms in parallel**, then verifies end-to-end before moving on. Every phase ends with a dashboard button that proves it works.

---

### ✅ Phase 0 — Launch Control (COMPLETE)

**Goal:** One-click server start (FastAPI + ngrok), dashboard showing system status.

**Completed:**
- Modular project structure built
- All platform modules created
- 24 API routes live
- Premium dashboard served at `http://localhost:8000`
- eBay: token refresh working ✅
- Shopify: needs new access token ⚠️

---

### Phase 1 — Platform Connection & Auth

**Goal:** Both platforms authenticated, verified, and shown live in dashboard.

**Pending:**
- Fix Shopify token (401 error) → update `.env` → click "Test Shopify"
- Confirm token auto-refresh cache works (eBay)
- Token expiry warning in dashboard (< 10 min remaining)

**Verification:**
- Press "Test eBay" → token refreshes, expiry shown ✅
- Press "Test Shopify" → shop name appears ✅
- Both shown as ✅ in dashboard simultaneously

---

### Phase 2 — List a Product (Both Platforms)

**Goal:** Dashboard form creates a product listing on BOTH platforms simultaneously.

**Form Fields:** Title | Description | Price | Quantity | SKU | Condition | Category

**eBay Tasks:**
- `platforms/ebay/inventory.py`: `create_listing()` — wraps all s2.py steps (DONE)
- `POST /api/ebay/listings` — create listing (DONE)
- `GET /api/ebay/listings/{listing_id}/verify` — buyer-side verify (DONE)

**Shopify Tasks:**
- `platforms/shopify/inventory.py`: `create_listing()` (DONE)
- `POST /api/shopify/listings` (DONE)
- `GET /api/shopify/listings/{product_id}/verify` — storefront verify (DONE)

> [!IMPORTANT]
> **Buyer-side verification is mandatory.** s2.py listed on eBay but never confirmed the buyer could see it. Every listing must be followed by a fetch from the customer-facing API. This is already implemented — just needs to be tested end-to-end.

**Verification:**
- Fill form → "List on Both Platforms" → eBay ID ✅ + Shopify ID ✅
- Click "Verify Buyer Can See It" on both → confirmed visible

---

### Phase 3 — View & Manage Listings

**Goal:** Dashboard shows all active listings from both platforms side-by-side.

**Tasks:**
- `GET /api/listings` — unified endpoint merged by SKU (DONE)
- Unified table in dashboard — left eBay, right Shopify, synced rows highlighted (DONE)
- "Edit" button per row → modal for price/quantity update

**Verification:**
- Dashboard loads, shows products from both platforms
- SKU-matched products show "🔗 Synced" badge

---

### Phase 4 — Update Inventory (Quantity/Price Sync)

**Goal:** Change quantity or price in one place → both platforms update.

**Tasks:**
- `PUT /api/ebay/listings/{sku}/quantity` (DONE)
- `PUT /api/shopify/listings/{product_id}/quantity` (DONE)
- `PUT /api/shopify/listings/{product_id}/price` (DONE)
- `PUT /api/sync/{sku}` — calls both atomically (TODO)
- Dashboard: per-listing "Update" modal with before/after diff (TODO)

**Verification:**
- Change quantity via dashboard → verify on eBay buyer view + Shopify customer view

---

### Phase 5 — PostgreSQL Master Inventory

**Goal:** Introduce the DB as single source of truth.

**Schema (from proposal):**
```sql
products (id, sku, name, quantity, reserved_quantity, created_at, updated_at)
platform_listings (id, product_id, platform, platform_product_id, is_active)
platform_credentials (id, platform, encrypted_api_key, refresh_token, token_expires_at)
orders (id, platform, platform_order_id, product_id, quantity_ordered, status, received_at)
sync_logs (id, order_id, target_platform, action, status, error_message, attempted_at)
```

**Tasks:**
- `core/database.py` + `core/models.py` — SQLAlchemy models
- Alembic migrations
- `core/sync_engine.py` — `deduct_stock(sku, qty)` with `SELECT FOR UPDATE` row lock
- Products tab in dashboard showing master inventory

---

### Phase 6 — Webhooks (Real-time Order Events)

**Goal:** Order on either platform → stock deducts → other platform updates.

**Tasks:**
- `platforms/shopify/webhooks.py` — HMAC/SHA-256 validation
- `platforms/ebay/webhooks.py` — eBay notification handler
- `POST /webhooks/shopify` and `POST /webhooks/ebay` routes
- "Simulate Order" button → POST fake webhook → watch sync happen live

**Verification:**
- Click "Simulate Shopify Order (qty=1)" → eBay qty decrements → sync log appears

---

### Phase 7 — Celery + Redis Task Queue

**Goal:** Async background processing, retries, dead-letter queue.

**Tasks:**
- Redis setup (local or Docker)
- `celery_app.py` — Celery config with Redis broker
- Convert sync_engine calls to Celery tasks
- Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 retries)
- Dead-letter queue for permanent failures
- Queue tab in dashboard

---

### Phase 8 — Monitoring, Alerts & AI Reports

**Tasks:**
- Real-time metrics: API call success rate, avg sync latency, error rate
- Sync latency graph (target: <30 seconds per proposal)
- Alert panel: oversell attempts, rate-limit hits, token expiry warnings
- AI-generated inventory suggestions (low stock warnings)
- Export sync logs as CSV

---

### Phase 9 — Load Testing & Quality Validation

**Tasks:**
- pytest suite: unit tests for each platform adapter
- Integration tests: list → verify → update → verify cycle
- Concurrent order simulation (50 simultaneous orders, zero oversell)
- "Run Tests" button in dashboard → shows pass/fail per test case

---

## How Any AI Can Pick Up From Here

1. **Read `docs/TASKS.md`** — exact current phase and unchecked tasks
2. **Read `core/config.py`** — all credentials in one typed object
3. **Read `platforms/base.py`** — abstract adapter contract every platform implements
4. **Start the server:** `python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
5. **Open `http://localhost:8000`** — the dashboard button that's failing = the next task

> [!NOTE]
> **Verification Rule:** Every feature must be testable by pressing a dashboard button that calls the real API. If a button is missing or broken, the phase is incomplete.

---

## Design Decisions (for reference)

| Question | Decision |
|---|---|
| Which platforms? | eBay Sandbox + Shopify (modular — add Amazon later as one adapter file) |
| Build order? | Parallel — same feature on both platforms simultaneously |
| Dashboard tech? | Single HTML/JS now → React.js migration after all features done |
| Credential management | `.env` file, loaded via `core/config.py` (Pydantic BaseSettings) |
| DB? | PostgreSQL (Phase 5 onwards) — skip for Phases 0–4 to move fast |
