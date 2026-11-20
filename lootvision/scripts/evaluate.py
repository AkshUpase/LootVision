#!/usr/bin/env python3
"""
Runs whichever evaluations have the data available for them and clearly
reports which ones were SKIPPED due to missing data, rather than printing
fabricated numbers.

Usage:
    python scripts/evaluate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.embeddings.embedder import get_embedder  # noqa: E402
from ml.evaluation.domain_gap import run_domain_gap_experiment  # noqa: E402
from ml.retrieval.vector_index import ProductIndex  # noqa: E402

INDEX_PATH = ROOT / "data" / "embeddings" / "product_index.faiss"
METADATA_PATH = ROOT / "data" / "embeddings" / "product_metadata.json"
DOMAIN_GAP_ROOT = ROOT / "data" / "domain_gap"


def main() -> None:
    print("=== LootVision Evaluation ===\n")

    if not INDEX_PATH.exists():
        print(
            "[SKIP] Domain-gap / retrieval evaluation: no product index found.\n"
            "       Run scripts/generate_embeddings.py then scripts/build_index.py first.\n"
        )
        return

    index = ProductIndex.load(INDEX_PATH, METADATA_PATH)
    embedder = get_embedder()
    print(f"Loaded catalog index: {index.index.ntotal} products, dim={index.dim}")
    print(f"Using embedder: {type(embedder).__name__}\n")

    try:
        report = run_domain_gap_experiment(embedder, index, DOMAIN_GAP_ROOT)
        print(report.summary())
    except (FileNotFoundError, ValueError) as e:
        print(f"[SKIP] Domain-gap experiment: {e}")

    print(
        "\nFor detection-quality and condition-classification metrics, see "
        "ml/evaluation/metrics.py — call precision_recall() / "
        "condition_classification_report() with your own labeled evaluation "
        "set once you have one; this script does not fabricate those either."
    )


if __name__ == "__main__":
    main()
