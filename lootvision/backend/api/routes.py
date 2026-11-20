from __future__ import annotations

import io

import numpy as np
from fastapi import APIRouter, File, Form, UploadFile
from PIL import Image

from backend.database.db import ScanHistory, UserSettingsRow, get_session
from backend.models.schemas import ScanHistoryEntry, ScanResponse, UserSettings
from backend.services.pipeline import get_pipeline
from backend.services.profit_engine import ProfitConfig

router = APIRouter(prefix="/api/v1")


@router.post("/scan", response_model=ScanResponse)
async def scan_frame(
    file: UploadFile = File(...),
    purchase_price: float = Form(0.0),
    confidence_threshold: float = Form(0.65),
    fee_percent: float = Form(0.10),
    shipping_estimate: float = Form(100.0),
) -> ScanResponse:
    image_bytes = await file.read()
    frame = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))

    pipeline = get_pipeline()
    result = pipeline.run(
        frame,
        purchase_price=purchase_price,
        confidence_threshold=confidence_threshold,
        profit_config=ProfitConfig(fee_percent=fee_percent, shipping_estimate=shipping_estimate),
    )

    # persist profitable / matched items to history
    session = get_session()
    try:
        for item in result.items:
            if item.best_match and item.pricing:
                session.add(
                    ScanHistory(
                        scan_id=result.scan_id,
                        product_id=item.best_match.product_id,
                        product_name=item.best_match.product_name,
                        category=item.best_match.category,
                        similarity=item.best_match.similarity,
                        condition_score=item.condition.score if item.condition else 0,
                        estimated_resale_price=item.pricing.estimated_resale_price,
                        estimated_profit=item.pricing.estimated_profit,
                        roi_percent=item.pricing.roi_percent,
                        price_source=item.pricing.price_source,
                    )
                )
        session.commit()
    finally:
        session.close()

    return result


@router.get("/history", response_model=list[ScanHistoryEntry])
def get_history(limit: int = 50) -> list[ScanHistoryEntry]:
    session = get_session()
    try:
        rows = (
            session.query(ScanHistory)
            .order_by(ScanHistory.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            ScanHistoryEntry(
                scan_id=r.scan_id,
                timestamp=r.timestamp,
                product_name=r.product_name,
                estimated_profit=r.estimated_profit,
                condition_score=r.condition_score,
            )
            for r in rows
        ]
    finally:
        session.close()


@router.get("/settings", response_model=UserSettings)
def get_settings() -> UserSettings:
    session = get_session()
    try:
        row = session.query(UserSettingsRow).first()
        if row is None:
            return UserSettings()
        return UserSettings(
            currency=row.currency,
            marketplace=row.marketplace,
            default_purchase_price=row.default_purchase_price,
            confidence_threshold=row.confidence_threshold,
            marketplace_fee_percent=row.marketplace_fee_percent,
            shipping_estimate=row.shipping_estimate,
        )
    finally:
        session.close()


@router.put("/settings", response_model=UserSettings)
def update_settings(settings: UserSettings) -> UserSettings:
    session = get_session()
    try:
        row = session.query(UserSettingsRow).first()
        if row is None:
            row = UserSettingsRow(id=1)
            session.add(row)
        row.currency = settings.currency
        row.marketplace = settings.marketplace
        row.default_purchase_price = settings.default_purchase_price
        row.confidence_threshold = settings.confidence_threshold
        row.marketplace_fee_percent = settings.marketplace_fee_percent
        row.shipping_estimate = settings.shipping_estimate
        session.commit()
        return settings
    finally:
        session.close()
