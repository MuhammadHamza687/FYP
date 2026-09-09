from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FYP Inventory Sync is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/privacy")
def privacy():
    return {"message": "Privacy Policy - FYP Inventory Sync System"}

@app.get("/terms")
def terms():
    return {"message": "Terms of Service - FYP Inventory Sync System"}

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