"""
Domain-gap experiment: the main research component of LootVision.

Compares retrieval accuracy of:
    Clean query      -> Clean catalog     (Domain A -> Domain A)
    Cluttered query  -> Clean catalog     (Domain B -> Domain A)

against the SAME catalog, using paired items (same physical product,
photographed clean vs. in a cluttered thrift-store-like setting).

Expects the layout described in data/products/README.md:
    data/domain_gap/domain_a_clean/<category>/<product_id>.jpg
    data/domain_gap/domain_b_cluttered/<category>/<product_id>_thrift.jpg

`<product_id>` must match between the two so pairing is unambiguous, and
must also exist in the retrieval catalog (data/products/) so we have
something to retrieve against.

Run via scripts/evaluate.py. This module raises rather than fabricating
numbers if the paired dataset isn't present.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from ml.embeddings.embedder import VisualEmbedder
from ml.evaluation.metrics import top_k_accuracy, mean_cosine_similarity
from ml.retrieval.vector_index import ProductIndex

VALID_EXT = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class DomainGapReport:
    n_pairs: int
    clean_top1: float
    clean_top5: float
    clean_mean_sim: float
    cluttered_top1: float
    cluttered_top5: float
    cluttered_mean_sim: float

    def summary(self) -> str:
        return (
            f"Domain-gap experiment over {self.n_pairs} paired products\n"
            f"{'':<10}{'Top-1':>10}{'Top-5':>10}{'MeanSim':>12}\n"
            f"{'Clean':<10}{self.clean_top1:>10.1%}{self.clean_top5:>10.1%}{self.clean_mean_sim:>12.3f}\n"
            f"{'Cluttered':<10}{self.cluttered_top1:>10.1%}{self.cluttered_top5:>10.1%}{self.cluttered_mean_sim:>12.3f}\n"
            f"Top-1 accuracy drop from domain gap: "
            f"{(self.clean_top1 - self.cluttered_top1):.1%}"
        )


def _find_images(root: Path) -> dict[str, Path]:
    """Maps product_id (filename stem, minus known suffixes) -> image path."""
    out = {}
    for p in root.rglob("*"):
        if p.suffix.lower() in VALID_EXT:
            stem = p.stem.replace("_thrift", "").replace("_cluttered", "")
            out[stem] = p
    return out


def run_domain_gap_experiment(
    embedder: VisualEmbedder,
    catalog_index: ProductIndex,
    domain_gap_root: Path,
    top_k: int = 5,
) -> DomainGapReport:
    clean_dir = domain_gap_root / "domain_a_clean"
    cluttered_dir = domain_gap_root / "domain_b_cluttered"
    if not clean_dir.exists() or not cluttered_dir.exists():
        raise FileNotFoundError(
            f"Expected {clean_dir} and {cluttered_dir} to exist. "
            "See data/products/README.md for the required layout. "
            "This experiment needs real paired photos - none are fabricated."
        )

    clean_images = _find_images(clean_dir)
    cluttered_images = _find_images(cluttered_dir)
    shared_ids = sorted(set(clean_images) & set(cluttered_images))
    if not shared_ids:
        raise ValueError(
            "No matching product_id pairs found between domain_a_clean and "
            "domain_b_cluttered. Filenames must share a stem, e.g. "
            "'nike_air_max_97.jpg' and 'nike_air_max_97_thrift.jpg'."
        )

    def evaluate(image_map: dict[str, Path]) -> tuple[float, float, float]:
        preds, sims, gts = [], [], []
        for pid in shared_ids:
            img = np.array(Image.open(image_map[pid]).convert("RGB"))
            emb = embedder.embed(img)
            results = catalog_index.search(emb, top_k=top_k)
            preds.append([r.product.product_id for r in results])
            sims.append(results[0].similarity if results else 0.0)
            gts.append(pid)
        return (
            top_k_accuracy(preds, gts, k=1),
            top_k_accuracy(preds, gts, k=5),
            mean_cosine_similarity(sims),
        )

    clean_top1, clean_top5, clean_sim = evaluate(clean_images)
    clutter_top1, clutter_top5, clutter_sim = evaluate(cluttered_images)

    return DomainGapReport(
        n_pairs=len(shared_ids),
        clean_top1=clean_top1,
        clean_top5=clean_top5,
        clean_mean_sim=clean_sim,
        cluttered_top1=clutter_top1,
        cluttered_top5=clutter_top5,
        cluttered_mean_sim=clutter_sim,
    )
