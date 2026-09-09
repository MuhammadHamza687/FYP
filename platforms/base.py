"""
platforms/base.py
Abstract base class that every platform adapter must implement.
This enforces a consistent interface so the sync engine is platform-agnostic.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class ConnectionStatus:
    connected: bool
    platform: str
    account_name: str = ""
    message: str = ""
    extra: dict = None

    def to_dict(self):
        return {
            "connected": self.connected,
            "platform": self.platform,
            "account_name": self.account_name,
            "message": self.message,
            **(self.extra or {}),
        }


@dataclass
class ListingResult:
    success: bool
    platform: str
    listing_id: str = ""
    listing_url: str = ""
    sku: str = ""
    message: str = ""

    def to_dict(self):
        return {
            "success": self.success,
            "platform": self.platform,
            "listing_id": self.listing_id,
            "listing_url": self.listing_url,
            "sku": self.sku,
            "message": self.message,
        }


@dataclass
class VerifyResult:
    visible: bool
    platform: str
    listing_id: str = ""
    buyer_url: str = ""
    title: str = ""
    price: str = ""
    quantity: int = 0
    message: str = ""

    def to_dict(self):
        return {
            "visible": self.visible,
            "platform": self.platform,
            "listing_id": self.listing_id,
            "buyer_url": self.buyer_url,
            "title": self.title,
            "price": self.price,
            "quantity": self.quantity,
            "message": self.message,
        }


class PlatformAdapter(ABC):
    """
    Every platform (eBay, Shopify, Amazon, ...) implements this interface.
    The sync engine only talks to PlatformAdapter — never directly to platform APIs.
    """

    platform_name: str = "unknown"

    @abstractmethod
    def test_connection(self) -> ConnectionStatus:
        """Test auth and return connection status."""
        ...

    @abstractmethod
    def create_listing(
        self,
        title: str,
        description: str,
        price: float,
        quantity: int,
        sku: str,
        category_id: str = "",
        condition: str = "NEW",
    ) -> ListingResult:
        """Create a product listing on this platform."""
        ...

    @abstractmethod
    def verify_listing(self, listing_id: str) -> VerifyResult:
        """
        Verify the listing is visible to buyers (customer-facing API).
        This is NOT the seller-side check — it uses the buyer/browse API.
        """
        ...

    @abstractmethod
    def get_all_listings(self) -> list[dict]:
        """Fetch all active listings from this platform."""
        ...

    @abstractmethod
    def update_quantity(self, listing_id: str, new_quantity: int) -> bool:
        """Update the available quantity for a listing."""
        ...

    @abstractmethod
    def update_price(self, listing_id: str, new_price: float) -> bool:
        """Update the price for a listing."""
        ...
