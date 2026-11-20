"""
The full LootVision inference pipeline, wired end-to-end.

    Camera Frame
       -> ObjectDetector.detect()          (ml/detection)
       -> crop per detection
       -> VisualEmbedder.embed()           (ml/embeddings)
       -> ProductIndex.search()            (ml/retrieval)
       -> ConditionScorer.assess()         (ml/condition)
       -> PricingService.get_price()       (backend/services/pricing)
       -> estimate_profit()                (backend/services/profit_engine)
       -> ScanResultItem                   (backend/models/schemas)

Everything is instantiated once (models are expensive to load) and reused
across requests via `get_pipeline()`.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np

from backend.models.schemas import (
    BoundingBox,
    ConditionAssessment,
    DetectedObject,
    MatchConfidence,
    PricingBreakdown,
    ProductMatch,
    ScanResponse,
    ScanResultItem,
)
from backend.services.pricing import get_pricing_service
from backend.services.profit_engine import ProfitConfig, estimate_profit
from ml.condition.condition_scorer import get_condition_scorer
from ml.detection.detector import get_detector
from ml.embeddings.embedder import get_embedder
from ml.retrieval.vector_index import ProductIndex

INDEX_PATH = Path(__file__).resolve().parents[2] / "data" / "embeddings" / "product_index.faiss"
METADATA_PATH = Path(__file__).resolve().parents[2] / "data" / "embeddings" / "product_metadata.json"


class LootVisionPipeline:
    def __init__(self):
        self.detector = get_detector()
        self.embedder = get_embedder()
        self.condition_scorer = get_condition_scorer()
        self.pricing_service = get_pricing_service()
        self.index = self._load_index()

    def _load_index(self) -> ProductIndex | None:
        if INDEX_PATH.exists() and METADATA_PATH.exists():
            return ProductIndex.load(INDEX_PATH, METADATA_PATH)
        return None  # run scripts/build_index.py to create it

    def run(
        self,
        frame: np.ndarray,
        purchase_price: float = 0.0,
        confidence_threshold: float = 0.65,
        profit_config: ProfitConfig | None = None,
    ) -> ScanResponse:
        start = time.perf_counter()
        h, w = frame.shape[:2]
        detections = self.detector.detect(frame)

        items: list[ScanResultItem] = []
        for det in detections:
            x, y, bw, bh = det.bbox_xywh_norm
            x0, y0 = int(x * w), int(y * h)
            x1, y1 = int((x + bw) * w), int((y + bh) * h)
            crop = frame[max(0, y0):y1, max(0, x0):x1]
            if crop.size == 0:
                continue

            detected_object = DetectedObject(
                detection_id=det.detection_id,
                bbox=BoundingBox(x=x, y=y, width=bw, height=bh),
                category=det.category,
                detection_confidence=det.confidence,
            )

            best_match = None
            alternatives: list[ProductMatch] = []
            similarity = 0.0

            if self.index is not None:
                embedding = self.embedder.embed(crop)
                results = self.index.search(embedding, top_k=5)
                matches = [
                    ProductMatch(
                        product_id=r.product.product_id,
                        product_name=r.product.product_name,
                        brand=r.product.brand,
                        category=r.product.category,
                        image_url=r.product.image_path,
                        similarity=round(r.similarity, 4),
                        marketplace_price=r.product.marketplace_price,
                        source=r.product.source,
                    )
                    for r in results
                ]
                if matches:
                    best_match, alternatives = matches[0], matches[1:]
                    similarity = best_match.similarity

            if similarity >= confidence_threshold:
                level = "high" if similarity >= 0.85 else "medium"
            elif similarity > 0:
                level = "low"
            else:
                level = "none"
            confidence = MatchConfidence(level=level, threshold_used=confidence_threshold)

            condition = None
            pricing = None
            if best_match is not None and level != "none":
                cond_result = self.condition_scorer.assess(crop)
                condition = ConditionAssessment(
                    score=cond_result.score,
                    label=cond_result.label,  # type: ignore[arg-type]
                    visible_damage=cond_result.visible_damage,
                    method=cond_result.method,  # type: ignore[arg-type]
                )
                quote = self.pricing_service.get_price(
                    best_match.product_name, best_match.category
                )
                pricing = estimate_profit(
                    base_resale_price=quote.estimated_price,
                    condition_score=condition.score,
                    purchase_price=purchase_price,
                    price_source=quote.source,
                    config=profit_config,
                )

            items.append(
                ScanResultItem(
                    detection=detected_object,
                    best_match=best_match,
                    alternatives=alternatives,
                    condition=condition,
                    pricing=pricing,
                    confidence=confidence,
                )
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        return ScanResponse(
            scan_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            items=items,
            processing_time_ms=round(elapsed_ms, 2),
        )


@lru_cache(maxsize=1)
def get_pipeline() -> LootVisionPipeline:
    return LootVisionPipeline()
