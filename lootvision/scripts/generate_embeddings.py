#!/usr/bin/env python3
"""
Embed every product image under data/products/<category>/<file> and write
one row per image to data/metadata/embeddings_raw.json.

Directory convention:
    data/products/sneakers/nike_air_max_97.jpg
    data/products/cameras/sony_a6000.jpg
    ...
    -> category is inferred from the immediate parent folder name.

This does NOT build the FAISS index itself (see build_index.py) - it just
does the (potentially slow) embedding pass so re-indexing is fast afterwards.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.embeddings.embedder import get_embedder  # noqa: E402

PRODUCTS_DIR = ROOT / "data" / "products"
OUT_PATH = ROOT / "data" / "metadata" / "embeddings_raw.json"

VALID_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def main() -> None:
    if not PRODUCTS_DIR.exists() or not any(PRODUCTS_DIR.iterdir()):
        print(
            f"No product images found under {PRODUCTS_DIR}.\n"
            "Add images like data/products/<category>/<name>.jpg first.\n"
            "See data/products/README.md for the expected layout."
        )
        return

    embedder = get_embedder()
    print(f"Using embedder: {type(embedder).__name__} (dim={embedder.dim})")

    rows = []
    image_paths = [p for p in PRODUCTS_DIR.rglob("*") if p.suffix.lower() in VALID_EXT]
    if not image_paths:
        print(f"No images with extensions {VALID_EXT} found under {PRODUCTS_DIR}.")
        return

    for path in image_paths:
        category = path.parent.name
        product_name = path.stem.replace("_", " ").title()
        try:
            image = np.array(Image.open(path).convert("RGB"))
        except Exception as e:
            print(f"  skip {path}: {e}")
            continue
        embedding = embedder.embed(image)
        rows.append(
            {
                "product_id": path.stem,
                "product_name": product_name,
                "brand": None,
                "category": category,
                "image_path": str(path.relative_to(ROOT)),
                "marketplace_price": 0.0,  # filled in / overridden at index-build or pricing time
                "condition": "Unknown",
                "source": "product_catalog",
                "embedding": embedding.tolist(),
            }
        )
        print(f"  embedded {path.relative_to(ROOT)}  -> {category}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(rows, indent=2))
    print(f"\nWrote {len(rows)} embeddings to {OUT_PATH}")


if __name__ == "__main__":
    main()
