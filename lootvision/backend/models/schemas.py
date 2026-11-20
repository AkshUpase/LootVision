"""
Pydantic schemas for LootVision's API.

These are the contracts between frontend <-> backend. Keeping them in one file
makes it easy to see the full shape of a scan result at a glance.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: float  # normalized 0-1, top-left
    y: float
    width: float
    height: float


class DetectedObject(BaseModel):
    detection_id: str
    bbox: BoundingBox
    category: str
    detection_confidence: float = Field(..., ge=0, le=1)


class ProductMatch(BaseModel):
    product_id: str
    product_name: str
    brand: Optional[str] = None
    category: str
    image_url: Optional[str] = None
    similarity: float = Field(..., ge=0, le=1)
    marketplace_price: float
    source: str  # e.g. "mock_catalog", "ebay_sold_listings"


class ConditionAssessment(BaseModel):
    score: int = Field(..., ge=0, le=100)
    label: Literal["Poor", "Fair", "Good", "Excellent"]
    visible_damage: list[str]
    method: Literal["baseline_heuristic", "trained_model"]
    note: str = (
        "Condition reflects only visible surface damage in the photo. "
        "Internal or functional defects cannot be assessed from an image."
    )


class MatchConfidence(BaseModel):
    level: Literal["low", "medium", "high", "none"]
    threshold_used: float


class PricingBreakdown(BaseModel):
    estimated_resale_price: float
    condition_adjustment: float
    estimated_fees: float
    purchase_price: float
    estimated_profit: float
    roi_percent: float
    is_profitable: bool
    price_source: Literal["mock", "ebay_browse_api"]
    disclaimer: str = "Pricing is an estimate; see price_source for data origin."


class ScanResultItem(BaseModel):
    detection: DetectedObject
    best_match: Optional[ProductMatch] = None
    alternatives: list[ProductMatch] = []
    condition: Optional[ConditionAssessment] = None
    pricing: Optional[PricingBreakdown] = None
    confidence: MatchConfidence


class ScanResponse(BaseModel):
    scan_id: str
    timestamp: datetime
    items: list[ScanResultItem]
    processing_time_ms: float


class ScanHistoryEntry(BaseModel):
    scan_id: str
    timestamp: datetime
    product_name: str
    estimated_profit: float
    condition_score: int
    thumbnail_url: Optional[str] = None


class UserSettings(BaseModel):
    currency: str = "INR"
    marketplace: str = "mock_catalog"
    default_purchase_price: float = 0.0
    confidence_threshold: float = 0.65
    marketplace_fee_percent: float = 0.10
    shipping_estimate: float = 100.0
