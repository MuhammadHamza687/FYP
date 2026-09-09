# FYP Inventory Sync — Task Tracker

## Phase 0 — Launch Control & Dashboard

### Setup
- [x] Create project directory structure (`core/`, `platforms/ebay/`, `platforms/shopify/`, `api/`, `scripts/`)
- [x] Install all dependencies (fastapi, uvicorn, pydantic-settings, requests, websockets)
- [x] Create `core/config.py` — typed Pydantic settings from .env
- [x] Create `platforms/base.py` — abstract PlatformAdapter interface

### eBay Platform
- [x] Create `platforms/ebay/auth.py` — token refresh with caching
- [x] Create `platforms/ebay/inventory.py` — full listing flow (location → item → policies → offer → publish)
- [x] Add buyer-side `verify_listing()` using eBay Browse API

### Shopify Platform
- [x] Create `platforms/shopify/auth.py` — static token connection test
- [x] Create `platforms/shopify/inventory.py` — create, verify (storefront API), fetch all, update

### API & Server
- [x] Create `api/dashboard_routes.py` — all dashboard endpoints
- [x] Rebuild `main.py` — dashboard serving + router mounts
- [x] Create `scripts/start_server.py` — one-click FastAPI + ngrok launcher
- [x] Create `dashboard.html` — premium glassmorphism control panel

### Verification
- [x] Start server and confirm dashboard loads at `http://localhost:8000` ✅ (49KB HTML served)
- [x] All 24 routes loaded and responding ✅
- [x] eBay connection confirmed ✅ — token refresh working, connected to Sandbox
- [x] Shopify 401 ⚠️ — access token in .env is expired/invalid, needs new token from Shopify Admin
- [ ] List product on both platforms via dashboard form
- [ ] Verify buyer-side visibility for eBay listing
- [ ] Verify customer-side visibility for Shopify product

> **ACTION NEEDED:** Shopify access token is invalid (401). Go to Shopify Admin > Apps > Private Apps and regenerate a new `SHOPIFY_ACCESS_TOKEN` then update `.env`.

---

## Phase 1 — Platform Connection & Auth ⬜

- [ ] Confirm token auto-refresh cache works (no re-login needed)
- [ ] Add `platforms/ebay/__init__.py` exports
- [ ] Add `platforms/shopify/__init__.py` exports
- [ ] Token expiry warning in dashboard (< 10 min remaining)

---

## Phase 2 — List a Product (Both Platforms) ⬜

- [ ] Test full eBay listing from dashboard form
- [ ] Test full Shopify product creation from dashboard form
- [ ] Buyer-side eBay verify button working
- [ ] Customer-side Shopify verify button working
- [ ] SKU collision handling (update instead of re-create)

---

## Phase 3 — View & Manage Listings ⬜

- [ ] GET /api/listings — unified endpoint with SKU matching
- [ ] Unified table in dashboard (both platforms side-by-side)
- [ ] Per-listing verify button in listings table
- [ ] Edit modal for price/quantity updates

---

## Phase 4 — Update Inventory (Quantity/Price Sync) ⬜

- [ ] PUT /api/sync/{sku} — atomic update on both platforms
- [ ] Dashboard update modal with before/after diff
- [ ] Confirm update visible on buyer/customer side

---

## Phase 5 — PostgreSQL Master Inventory ⬜

- [ ] Set up PostgreSQL (local or Docker)
- [ ] Create `core/database.py` (SQLAlchemy)
- [ ] Create `core/models.py` (all 6 tables from proposal)
- [ ] Alembic migrations
- [ ] `core/sync_engine.py` with `SELECT FOR UPDATE` row lock
- [ ] Products tab in dashboard showing master inventory

---

## Phase 6 — Webhooks ⬜

- [ ] `platforms/shopify/webhooks.py` — HMAC validation
- [ ] `platforms/ebay/webhooks.py` — eBay notification handler
- [ ] `POST /webhooks/shopify` and `/webhooks/ebay` routes
- [ ] Webhook connects to sync engine
- [ ] "Simulate Order" button in dashboard
- [ ] Live feed tab shows real-time webhook events

---

## Phase 7 — Celery + Redis ⬜

- [ ] Redis setup
- [ ] `celery_app.py` config
- [ ] Sync tasks converted to Celery
- [ ] Exponential backoff (1s → 2s → 4s → 8s → 16s, max 5 retries)
- [ ] Dead-letter queue
- [ ] Queue tab in dashboard

---

## Phase 8 — Monitoring & AI Reports ⬜

- [ ] Real-time metrics (API success rate, sync latency)
- [ ] Sync latency graph (target: <30s per proposal)
- [ ] Alert panel (oversell, rate-limit, token expiry)
- [ ] AI inventory suggestions (low stock warnings)
- [ ] CSV export for sync logs

---

## Phase 9 — Load Testing & QA ⬜

- [ ] pytest suite for each platform adapter
- [ ] Integration test: list → verify → update → verify cycle
- [ ] 50 concurrent order simulation (zero oversell)
- [ ] "Run Tests" button in dashboard
- [ ] All FYP success criteria validated
