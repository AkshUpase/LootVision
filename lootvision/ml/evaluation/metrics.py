"""
Evaluation metrics for each pipeline stage. All functions operate on
plain Python/numpy data so they can be unit-tested without any model
loaded, and are used by scripts/evaluate.py against whatever real data
is present.

No function in this file invents numbers - every metric here requires
the caller to supply real predictions/ground truth. If you don't have
data yet, don't call these; scripts/evaluate.py checks for that and says
so explicitly rather than printing placeholder metrics.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ---------------------------------------------------------------------------
# Retrieval metrics
# ---------------------------------------------------------------------------

def top_k_accuracy(ranked_predictions: list[list[str]], ground_truth: list[str], k: int) -> float:
    """
    ranked_predictions[i] = list of predicted product_ids for query i,
                             ordered best-first (only the top `k` are used).
    ground_truth[i]       = the correct product_id for query i.
    """
    if not ranked_predictions:
        return 0.0
    hits = sum(
        1 for preds, gt in zip(ranked_predictions, ground_truth) if gt in preds[:k]
    )
    return hits / len(ranked_predictions)


def recall_at_k(ranked_predictions: list[list[str]], ground_truth: list[list[str]], k: int) -> float:
    """
    Generalized recall@K when a query can have multiple acceptable matches
    (ground_truth[i] is a list of acceptable product_ids for query i).
    """
    if not ranked_predictions:
        return 0.0
    scores = []
    for preds, gts in zip(ranked_predictions, ground_truth):
        if not gts:
            continue
        hit = len(set(preds[:k]) & set(gts))
        scores.append(hit / len(gts))
    return float(np.mean(scores)) if scores else 0.0


def mean_cosine_similarity(similarities: list[float]) -> float:
    return float(np.mean(similarities)) if similarities else 0.0


# ---------------------------------------------------------------------------
# Detection metrics
# ---------------------------------------------------------------------------

def iou(box_a: tuple[float, float, float, float], box_b: tuple[float, float, float, float]) -> float:
    """boxes as (x, y, w, h) normalized or pixel, same units for both."""
    ax0, ay0, aw, ah = box_a
    bx0, by0, bw, bh = box_b
    ax1, ay1 = ax0 + aw, ay0 + ah
    bx1, by1 = bx0 + bw, by0 + bh

    inter_x0, inter_y0 = max(ax0, bx0), max(ay0, by0)
    inter_x1, inter_y1 = min(ax1, bx1), min(ay1, by1)
    inter_area = max(0.0, inter_x1 - inter_x0) * max(0.0, inter_y1 - inter_y0)

    union_area = aw * ah + bw * bh - inter_area
    return inter_area / union_area if union_area > 0 else 0.0


@dataclass
class DetectionPRResult:
    precision: float
    recall: float
    n_pred: int
    n_gt: int
    n_matched: int


def precision_recall(
    predicted_boxes: list[tuple[float, float, float, float]],
    ground_truth_boxes: list[tuple[float, float, float, float]],
    iou_threshold: float = 0.5,
) -> DetectionPRResult:
    """Greedy one-to-one matching by descending IoU for a single image."""
    matched_gt = set()
    n_matched = 0
    for pb in predicted_boxes:
        best_iou, best_idx = 0.0, -1
        for i, gb in enumerate(ground_truth_boxes):
            if i in matched_gt:
                continue
            cur_iou = iou(pb, gb)
            if cur_iou > best_iou:
                best_iou, best_idx = cur_iou, i
        if best_iou >= iou_threshold and best_idx != -1:
            matched_gt.add(best_idx)
            n_matched += 1

    precision = n_matched / len(predicted_boxes) if predicted_boxes else 0.0
    recall = n_matched / len(ground_truth_boxes) if ground_truth_boxes else 0.0
    return DetectionPRResult(
        precision=precision,
        recall=recall,
        n_pred=len(predicted_boxes),
        n_gt=len(ground_truth_boxes),
        n_matched=n_matched,
    )


# ---------------------------------------------------------------------------
# Condition classification metrics
# ---------------------------------------------------------------------------

def condition_classification_report(y_true: list[str], y_pred: list[str]) -> dict:
    """
    y_true / y_pred: lists of labels from {"Poor","Fair","Good","Excellent"}.
    Returns accuracy plus per-class precision/recall/F1.
    """
    labels = sorted(set(y_true) | set(y_pred))
    report = {}
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    report["accuracy"] = correct / len(y_true) if y_true else 0.0

    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        report[label] = {"precision": precision, "recall": recall, "f1": f1}

    return report
