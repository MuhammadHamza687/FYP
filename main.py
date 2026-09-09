"""
main.py
FastAPI application entry point.
Serves the dashboard HTML at / and mounts all API routers.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from api.dashboard_routes import router as dashboard_router

app = FastAPI(
    title="FYP Inventory Sync System",
    description="Multi-Channel Inventory & Order Synchronization — Shopify + eBay",
    version="1.0.0",
)

# Allow dashboard to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(dashboard_router)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serve the main control dashboard."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


# ─── System Routes ────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "FYP Inventory Sync"}


@app.get("/privacy")
def privacy():
    return {"message": "Privacy Policy — FYP Inventory Sync System"}


@app.get("/terms")
def terms():
    return {"message": "Terms of Service — FYP Inventory Sync System"}


@app.get("/ebay/callback")
def ebay_callback(code: str = None):
    if code:
        return {"code": code, "message": "eBay OAuth callback received successfully!"}
    return {"message": "No code received"}


@app.get("/auth/callback")
def auth_callback(code: str = None):
    if code:
        return {"code": code, "message": "Shopify OAuth callback received successfully!"}
    return {"message": "No code received"}