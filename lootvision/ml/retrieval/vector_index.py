"""
Vector similarity search over the product catalog.

Design requirement from the brief: new products must be addable WITHOUT
retraining any model. FAISS gives us that directly - inserting a product is
`index.add(embedding)` plus appending one row of metadata. No gradient step
involved.

Storage layout on disk (see scripts/build_index.py):
    data/embeddings/product_index.faiss   -- the FAISS index itself
    data/embeddings/product_metadata.json -- parallel array of ProductMeta,
                                              row i corresponds to vector i

We use IndexFlatIP (inner product) over L2-normalized vectors, which is
mathematically equivalent to cosine similarity and exact (no approximation
error) - appropriate for a catalog of thousands, not tens of millions, of
products.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


@dataclass
class ProductMeta:
    product_id: str
    product_name: str
    brand: str | None
    category: str
    image_path: str
    marketplace_price: float
    condition: str
    source: str


@dataclass
class RetrievalResult:
    product: ProductMeta
    similarity: float  # cosine similarity, [-1, 1] but expect [0, 1] in practice


class ProductIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self._faiss = self._import_faiss()
        self.index = self._faiss.IndexFlatIP(dim)
        self.metadata: list[ProductMeta] = []

    @staticmethod
    def _import_faiss():
        try:
            import faiss
            return faiss
        except ImportError as e:
            raise ImportError(
                "faiss is required for retrieval. Install with "
                "`pip install faiss-cpu` (see backend/requirements.txt)."
            ) from e

    def add(self, embedding: np.ndarray, meta: ProductMeta) -> None:
        vec = self._normalize(embedding).reshape(1, -1).astype(np.float32)
        self.index.add(vec)
        self.metadata.append(meta)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[RetrievalResult]:
        if self.index.ntotal == 0:
            return []
        vec = self._normalize(query_embedding).reshape(1, -1).astype(np.float32)
        sims, idxs = self.index.search(vec, min(top_k, self.index.ntotal))
        results = []
        for sim, idx in zip(sims[0], idxs[0]):
            if idx == -1:
                continue
            results.append(RetrievalResult(product=self.metadata[idx], similarity=float(sim)))
        return results

    @staticmethod
    def _normalize(vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    # --- persistence ---------------------------------------------------

    def save(self, index_path: str | Path, metadata_path: str | Path) -> None:
        self._faiss.write_index(self.index, str(index_path))
        Path(metadata_path).write_text(
            json.dumps([asdict(m) for m in self.metadata], indent=2)
        )

    @classmethod
    def load(cls, index_path: str | Path, metadata_path: str | Path) -> "ProductIndex":
        faiss = cls._import_faiss()
        index = faiss.read_index(str(index_path))
        obj = cls.__new__(cls)
        obj._faiss = faiss
        obj.index = index
        obj.dim = index.d
        raw = json.loads(Path(metadata_path).read_text())
        obj.metadata = [ProductMeta(**row) for row in raw]
        return obj
