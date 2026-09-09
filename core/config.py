"""
core/config.py
Loads all .env values into a typed Pydantic Settings object.
Every other module imports `settings` from here — never reads .env directly.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Shopify ──────────────────────────────────────────────────────────────
    shopify_store: str = Field(default="")
    shopify_access_token: str = Field(default="")
    shopify_api_key: str = Field(default="")
    shopify_api_secret: str = Field(default="")

    # ── eBay ─────────────────────────────────────────────────────────────────
    ebay_app_id: str = Field(default="")
    ebay_dev_id: str = Field(default="")
    ebay_cert_id: str = Field(default="")
    ebay_runame: str = Field(default="")
    ebay_refresh_token: str = Field(default="")
    ebay_sandbox_seller: str = Field(default="")
    ebay_sandbox_buyer: str = Field(default="")
    ebay_sandbox_password: str = Field(default="")

    # ── Common ────────────────────────────────────────────────────────────────
    public_url: str = Field(default="http://localhost:8000")
    fastapi_port: int = Field(default=8000)

    # ── Computed helpers ──────────────────────────────────────────────────────
    @property
    def shopify_base_url(self) -> str:
        return f"https://{self.shopify_store}/admin/api/2024-01"

    @property
    def ebay_sandbox(self) -> bool:
        return "SBX" in self.ebay_app_id or "sandbox" in self.ebay_app_id.lower()

    @property
    def ebay_base_inventory(self) -> str:
        return "https://api.sandbox.ebay.com/sell/inventory/v1"

    @property
    def ebay_base_account(self) -> str:
        return "https://api.sandbox.ebay.com/sell/account/v1"

    @property
    def ebay_base_identity(self) -> str:
        return "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

    @property
    def ebay_browse_base(self) -> str:
        """Browse API for buyer-side verification."""
        return "https://api.sandbox.ebay.com/buy/browse/v1"


# Singleton — import this everywhere
settings = Settings()
