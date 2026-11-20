#!/usr/bin/env python3
"""
Reads data/metadata/embeddings_raw.json (produced by generate_embeddings.py)
and builds the FAISS index used by the backend at query time.

Run after generate_embeddings.py, and re-run any time you add new products —
this NEVER retrains a model, it just rebuilds the index, which is fast
(seconds, even for thousands of products) because IndexFlatIP has no training
step.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.retrieval.vector_index import ProductIndex, ProductMeta  # noqa: E402

EMBEDDINGS_RAW = ROOT / "data" / "metadata" / "embeddings_raw.json"
INDEX_OUT = ROOT / "data" / "embeddings" / "product_index.faiss"
METADATA_OUT = ROOT / "data" / "embeddings" / "product_metadata.json"


def main() -> None:
    if not EMBEDDINGS_RAW.exists():
        print(f"{EMBEDDINGS_RAW} not found. Run scripts/generate_embeddings.py first.")
        return

    rows = json.loads(EMBEDDINGS_RAW.read_text())
    if not rows:
        print("embeddings_raw.json is empty - nothing to index.")
        return

    dim = len(rows[0]["embedding"])
    index = ProductIndex(dim=dim)

    for row in rows:
        meta = ProductMeta(
            product_id=row["product_id"],
            product_name=row["product_name"],
            brand=row["brand"],
            category=row["category"],
            image_path=row["image_path"],
            marketplace_price=row["marketplace_price"],
            condition=row["condition"],
            source=row["source"],
        )
        index.add(np.array(row["embedding"], dtype=np.float32), meta)

    INDEX_OUT.parent.mkdir(parents=True, exist_ok=True)
    index.save(INDEX_OUT, METADATA_OUT)
    print(f"Built index with {len(rows)} products -> {INDEX_OUT}")


if __name__ == "__main__":
    main()
