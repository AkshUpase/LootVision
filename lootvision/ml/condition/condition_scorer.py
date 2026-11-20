"""
Condition / wear-and-tear assessment.

Per the brief: implement a practical baseline first, and design the interface
so a stronger learned model (autoencoder / Siamese anomaly detector / trained
CNN regressor) can be swapped in later without touching the rest of the
pipeline.

`ConditionScorer.assess(crop) -> ConditionResult` is the stable interface.

Baseline implementation (`HeuristicConditionScorer`)
-----------------------------------------------------
Since we don't have a labeled "condition score" dataset for a student project,
the baseline uses classical CV signals that correlate loosely with visible
wear, and is explicit that this is a heuristic, not a calibrated model:

  - Edge/texture irregularity (Laplacian variance): high-frequency noise can
    indicate scratches, tears, or surface damage.
  - Local contrast anomalies: patches of unusually low contrast can indicate
    fading or staining.
  - Symmetry deviation (for roughly-symmetric object crops): asymmetric
    silhouettes can indicate missing parts or deformation.

This is deliberately conservative and explainable, not a trained model —
see `TrainedConditionScorer` for the extension point once labeled
before/after condition photos are available (Phase 6 in the roadmap).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class ConditionResult:
    score: int  # 0-100
    label: str  # "Poor" | "Fair" | "Good" | "Excellent"
    visible_damage: list[str]
    method: str  # "baseline_heuristic" | "trained_model"


class ConditionScorer(Protocol):
    def assess(self, crop: np.ndarray) -> ConditionResult: ...


def _score_to_label(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Poor"


class HeuristicConditionScorer:
    """Dependency: OpenCV only. No training data required."""

    def assess(self, crop: np.ndarray) -> ConditionResult:
        import cv2

        gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY) if crop.ndim == 3 else crop
        gray = cv2.resize(gray, (256, 256))

        damage: list[str] = []

        # 1. high-frequency irregularity -> possible scratches/cracks/tears
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # very high local variance beyond natural texture suggests damage;
        # thresholds are heuristic and should be calibrated against real
        # labeled data before being trusted quantitatively.
        scratch_penalty = 0
        if laplacian_var > 900:
            damage.append("Possible scratches or surface irregularity")
            scratch_penalty = min(25, (laplacian_var - 900) / 40)

        # 2. low local contrast patches -> possible fading/staining
        clahe_input = gray.astype(np.uint8)
        block = 32
        low_contrast_blocks = 0
        total_blocks = 0
        for y in range(0, 256, block):
            for x in range(0, 256, block):
                patch = clahe_input[y:y + block, x:x + block]
                total_blocks += 1
                if patch.std() < 8:
                    low_contrast_blocks += 1
        fade_ratio = low_contrast_blocks / max(total_blocks, 1)
        fade_penalty = 0
        if fade_ratio > 0.35:
            damage.append("Possible fading or staining in low-contrast regions")
            fade_penalty = min(20, fade_ratio * 40)

        # 3. left/right asymmetry -> possible missing parts / deformation
        h, w = gray.shape
        left, right = gray[:, : w // 2], np.fliplr(gray[:, w // 2:])
        min_w = min(left.shape[1], right.shape[1])
        asymmetry = np.mean(np.abs(left[:, :min_w].astype(int) - right[:, :min_w].astype(int)))
        asym_penalty = 0
        if asymmetry > 35:
            damage.append("Possible missing part or shape deformation")
            asym_penalty = min(15, (asymmetry - 35) / 3)

        score = int(max(0, 100 - scratch_penalty - fade_penalty - asym_penalty))
        if not damage:
            damage.append("No significant surface damage visually detected")

        return ConditionResult(
            score=score,
            label=_score_to_label(score),
            visible_damage=damage,
            method="baseline_heuristic",
        )


class TrainedConditionScorer:
    """
    Extension point for Phase 6: load a small CNN fine-tuned to regress a
    0-100 condition score from labeled (image, condition_score) pairs, or a
    feature-space anomaly detector (e.g. reconstruction error from an
    autoencoder trained only on "good condition" reference images).

    Left unimplemented here deliberately - it requires a labeled dataset this
    scaffold does not fabricate. Wire it up once you have:
        data/metadata/condition_labels.csv  (image_path, condition_score)
    """

    def __init__(self, weights_path: str):
        raise NotImplementedError(
            "TrainedConditionScorer requires labeled condition data and a "
            "training run. See ml/condition/README.md for the training plan."
        )

    def assess(self, crop: np.ndarray) -> ConditionResult:  # pragma: no cover
        raise NotImplementedError


def get_condition_scorer() -> ConditionScorer:
    return HeuristicConditionScorer()
