"""
Marketplace pricing service.

Per the brief: never fabricate live prices. This module provides:

1. `MockPricingService`  — a CLEARLY LABELED mock catalog with realistic,
   hand-set sample prices so the whole app is demoable without any API key.
   Every result from this service carries `source="mock"`.

2. `EbayPricingService`  — a real adapter for the eBay Browse API (sold /
   active listings search). Disabled until you provide an eBay App ID via
   the EBAY_APP_ID environment variable. Raises clearly if called without
   credentials rather than silently falling back to fake numbers.

The API layer decides which one to use and always surfaces `price_source` to
the frontend, so estimates vs. real marketplace data are never conflated.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Protocol


@dataclass
class PriceQuote:
    estimated_price: float
    currency: str
    source: str  # "mock" | "ebay_browse_api"
    sample_size: int | None = None  # how many listings the estimate is based on


class PricingService(Protocol):
    def get_price(self, product_name: str, category: str, currency: str = "INR") -> PriceQuote: ...


# A small, explicitly-fake reference catalog. Prices are illustrative sample
# data for demo purposes only, in INR, roughly plausible for the category.
_MOCK_CATALOG: dict[str, tuple[float, float]] = {
    "sneakers": (2500, 9000),
    "vintage t-shirt": (600, 4500),
    "camera": (1500, 15000),
    "gaming controller": (800, 3500),
    "headphones": (700, 6000),
    "watch": (1200, 12000),
    "jacket": (900, 5000),
    "bag": (700, 6500),
    "item": (500, 3000),
}


class MockPricingService:
    """Deterministic-ish mock pricing. NEVER present this as real market data."""

    def get_price(self, product_name: str, category: str, currency: str = "INR") -> PriceQuote:
        low, high = _MOCK_CATALOG.get(category.lower(), _MOCK_CATALOG["item"])
        # seed on product_name so repeated scans of the "same" item are stable
        rng = random.Random(hash(product_name) % (2**32))
        price = round(rng.uniform(low, high), -1)  # round to nearest 10
        return PriceQuote(estimated_price=price, currency=currency, source="mock")


class EbayPricingService:
    """
    Real adapter for eBay's Browse API. Requires EBAY_APP_ID (and a valid
    OAuth flow) - see https://developer.ebay.com/api-docs/buy/browse/overview.html

    Deliberately NOT implemented with a hardcoded token. Wire in your own
    OAuth client-credentials flow before enabling this in production; raising
    here is intentional so the app never silently substitutes fabricated
    numbers if credentials are missing.
    """

    def __init__(self):
        self.app_id = os.environ.get("EBAY_APP_ID")
        if not self.app_id:
            raise RuntimeError(
                "EBAY_APP_ID not set. EbayPricingService requires real eBay "
                "developer credentials - see backend/services/pricing.py docstring. "
                "Use MockPricingService for local development/demo."
            )

    def get_price(self, product_name: str, category: str, currency: str = "INR") -> PriceQuote:
        raise NotImplementedError(
            "Implement the eBay Browse API 'item_summary/search' call here "
            "once EBAY_APP_ID / OAuth token handling is wired up. This stub "
            "exists to define the interface, not to fabricate results."
        )


def get_pricing_service() -> PricingService:
    if os.environ.get("EBAY_APP_ID"):
        return EbayPricingService()
    return MockPricingService()
