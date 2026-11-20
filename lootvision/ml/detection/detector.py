"""
Object detection stage of the LootVision pipeline.

Design contract
----------------
`ObjectDetector.detect(image) -> list[Detection]` is the ONLY thing the rest of
the pipeline depends on. This lets us swap the underlying model (YOLOv8n today,
YOLO11 or a distilled edge model tomorrow) without touching any other stage.

Two implementations are provided:

1. `YoloV8Detector`   — real detector using Ultralytics YOLOv8n. Requires
                         `pip install ultralytics` and downloads pretrained
                         COCO weights on first use (needs internet).
2. `HeuristicDetector` — a dependency-free fallback used when `ultralytics`
                         isn't installed. It finds visually distinct regions
                         via classical CV (contour detection on edges), so the
                         rest of the pipeline is runnable and testable without
                         any model download. This is NOT a substitute for a
                         trained detector and is clearly labeled as such in
                         its output.

Swap which one is active via `get_detector()` at the bottom of this file.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np


@dataclass
class Detection:
    detection_id: str
    bbox_xywh_norm: tuple[float, float, float, float]  # normalized x,y,w,h
    category: str
    confidence: float
    source: str = field(default="unknown")  # "yolov8n" | "heuristic_cv"


class ObjectDetector(Protocol):
    def detect(self, image: np.ndarray) -> list[Detection]: ...


class HeuristicDetector:
    """
    Dependency-free fallback detector.

    Uses Canny edge detection + contour finding to propose bounding boxes
    around visually distinct objects. This gives the pipeline something real
    to run end-to-end on before a trained detector is wired in, but it is a
    classical-CV baseline, not a learned model — box quality and category
    labels are much weaker than YOLO. Category is always "item" since this
    method has no notion of object class.
    """

    MIN_AREA_FRACTION = 0.01  # ignore specks smaller than 1% of frame area
    MAX_AREA_FRACTION = 0.85  # ignore boxes that basically cover the whole frame

    def detect(self, image: np.ndarray) -> list[Detection]:
        import cv2

        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 120)
        edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=1)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections: list[Detection] = []
        frame_area = h * w
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            area_fraction = (cw * ch) / frame_area
            if not (self.MIN_AREA_FRACTION <= area_fraction <= self.MAX_AREA_FRACTION):
                continue
            detections.append(
                Detection(
                    detection_id=str(uuid.uuid4()),
                    bbox_xywh_norm=(x / w, y / h, cw / w, ch / h),
                    category="item",
                    # confidence here is a coverage-based heuristic, not a
                    # learned probability - kept deliberately conservative.
                    confidence=0.5,
                    source="heuristic_cv",
                )
            )
        # keep the largest N boxes so results stay usable in a cluttered frame
        detections.sort(key=lambda d: d.bbox_xywh_norm[2] * d.bbox_xywh_norm[3], reverse=True)
        return detections[:8]


class YoloV8Detector:
    """
    Real detector using Ultralytics YOLOv8n, pretrained on COCO.

    COCO's 80 classes don't cover most thrift-store items (no "vintage
    t-shirt" class), which is precisely why detection here only needs to
    find "an object worth inspecting" — fine-grained identity comes from the
    embedding + retrieval stage (ml/embeddings, ml/retrieval), not from this
    detector's class label.
    """

    def __init__(self, weights: str = "yolov8n.pt", conf_threshold: float = 0.35):
        from ultralytics import YOLO  # local import: optional heavy dependency

        self.model = YOLO(weights)
        self.conf_threshold = conf_threshold

    def detect(self, image: np.ndarray) -> list[Detection]:
        h, w = image.shape[:2]
        results = self.model.predict(image, conf=self.conf_threshold, verbose=False)[0]
        detections: list[Detection] = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0].item())
            category = self.model.names.get(cls_id, "item")
            detections.append(
                Detection(
                    detection_id=str(uuid.uuid4()),
                    bbox_xywh_norm=(x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h),
                    category=category,
                    confidence=float(box.conf[0].item()),
                    source="yolov8n",
                )
            )
        return detections


def get_detector() -> ObjectDetector:
    """Factory: prefers YOLOv8n, falls back to the dependency-free heuristic."""
    try:
        return YoloV8Detector()
    except Exception:
        return HeuristicDetector()
