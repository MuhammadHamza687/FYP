# FYP Multi-Channel Inventory & Order Sync Engine

A real-time, bi-directional inventory and order synchronization system connecting **eBay Sandbox** and **Shopify Storefront** with an interactive live control panel.

---

## ⚡ Quick Start (After PC Restart)

If you turn off or restart your computer, follow these simple steps to start everything back up:

### Step 1: Open PowerShell or Terminal in `e:\FYP`
```powershell
cd e:\FYP
```

### Step 2: Run the One-Click Server Launcher
```powershell
python scripts/start_server.py
```

This single command automatically starts:
1. **FastAPI Backend Server** on `http://localhost:8000`
2. **ngrok Tunnel** for HTTPS public access (used by Shopify & Webhooks)

---

## 🌐 Access Points

| Service | Access URL | Purpose |
|---|---|---|
| **Local Dashboard** | `http://localhost:8000` | Full glassmorphism control panel |
| **API Documentation** | `http://localhost:8000/docs` | Interactive FastAPI Swagger UI |
| **Shopify Embedded App** | `https://admin.shopify.com/store/fyp-sync/apps/fyp-inventory-sync` | App UI embedded in Shopify Admin |

---

## 📚 Project Documentation

All detailed project documents are located in the [`docs/`](file:///e:/FYP/docs/) directory:

- 🗺️ **[docs/ROADMAP.md](file:///e:/FYP/docs/ROADMAP.md)** — Architectural design, system proposal requirements & multi-AI handoff guide.
- 📋 **[docs/TASK.md](file:///e:/FYP/docs/TASK.md)** — Phase-by-phase task checklist tracking completed & upcoming features.
- 📖 **[docs/WALKTHROUGH.md](file:///e:/FYP/docs/WALKTHROUGH.md)** — Detailed setup, connection test results & platform verification steps.

---

## 🔑 Authentication Architecture

- **eBay**: Uses OAuth 2.0 Refresh Token flow with in-memory caching.
- **Shopify**: Uses OAuth `client_credentials` grant on `https://fyp-sync.myshopify.com/admin/oauth/access_token` with automatic token rotation & 401 retry handling.
