"""
Profit estimation engine.

The formula is intentionally centralized and configurable (see ProfitConfig)
rather than hard-coded across the app, per the brief's requirement.

    condition_adjustment = base_price * (condition_score/100 - 1) * condition_weight
    adjusted_resale       = base_price + condition_adjustment
    fees                  = adjusted_resale * fee_percent
    total_cost            = purchase_price + fees + shipping_estimate
    profit                = adjusted_resale - total_cost
    roi_percent           = profit / max(purchase_price, epsilon) * 100
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.models.schemas import PricingBreakdown


@dataclass
class ProfitConfig:
    fee_percent: float = 0.10       # marketplace cut
    shipping_estimate: float = 100  # flat estimate in local currency
    condition_weight: float = 1.0   # how strongly condition scales adjustment
    min_purchase_price: float = 1.0  # avoid divide-by-zero on ROI


def estimate_profit(
    base_resale_price: float,
    condition_score: int,
    purchase_price: float,
    price_source: str,
    config: ProfitConfig | None = None,
) -> PricingBreakdown:
    cfg = config or ProfitConfig()

    condition_adjustment = round(
        base_resale_price * ((condition_score / 100) - 1) * cfg.condition_weight, 2
    )
    adjusted_resale = round(base_resale_price + condition_adjustment, 2)
    fees = round(adjusted_resale * cfg.fee_percent, 2)
    total_cost = purchase_price + fees + cfg.shipping_estimate
    profit = round(adjusted_resale - total_cost, 2)
    roi = round(profit / max(purchase_price, cfg.min_purchase_price) * 100, 1)

    return PricingBreakdown(
        estimated_resale_price=adjusted_resale,
        condition_adjustment=condition_adjustment,
        estimated_fees=fees,
        purchase_price=purchase_price,
        estimated_profit=profit,
        roi_percent=roi,
        is_profitable=profit > 0,
        price_source="mock" if price_source == "mock" else "ebay_browse_api",
    )
