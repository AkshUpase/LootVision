"""
Fine-grained visual embedding stage — the ML core of LootVision.

We deliberately do NOT train a classifier over product classes. Product
inventory in a thrift store is open-set (new items constantly) and long-tail
(most products appear once). Instead we embed each object crop into a shared
vector space and retrieve nearest neighbors (see ml/retrieval/). Adding a new
product to the catalog is then just: embed one photo, insert the vector —
no retraining required. This is the design requirement from the project brief.

Two implementations:

1. `ClipEmbedder`       — real embedding via OpenCLIP (ViT-B/32, laion2b
                           weights). Requires `pip install open_clip_torch
                           torch pillow` and downloads pretrained weights.
2. `HashEmbedder`        — dependency-free fallback producing a deterministic
                           pseudo-embedding from low-level image statistics
                           (color histogram + HOG-like gradient orientation
                           histogram). This is explicitly NOT a semantic
                           embedding and will not produce good retrieval —
                           it exists purely so the rest of the pipeline
                           (indexing, similarity search, API wiring) is
                           testable without a multi-GB model download.
"""
from __future__ import annotations

from typing import Protocol

import numpy as np


EMBED_DIM_CLIP = 512
EMBED_DIM_FALLBACK = 256


class VisualEmbedder(Protocol):
    dim: int

    def embed(self, image: np.ndarray) -> np.ndarray: ...


class ClipEmbedder:
    """Real embedder: OpenCLIP ViT-B/32 image tower."""

    dim = EMBED_DIM_CLIP

    def __init__(self, model_name: str = "ViT-B-32", pretrained: str = "laion2b_s34b_b79k"):
        import open_clip
        import torch

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained
        )
        self.model.to(self.device).eval()

    def embed(self, image: np.ndarray) -> np.ndarray:
        from PIL import Image

        pil_img = Image.fromarray(image)
        tensor = self.preprocess(pil_img).unsqueeze(0).to(self.device)
        with self.torch.no_grad():
            features = self.model.encode_image(tensor)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze(0).cpu().numpy().astype(np.float32)


class HashEmbedder:
    """
    Dependency-free fallback: color histogram + gradient-orientation
    histogram, L2-normalized. Deterministic, fast, zero downloads.

    NOT a semantic embedding — two visually similar-but-not-identical products
    (e.g. two different red hoodies) will not necessarily land close together.
    Swap to ClipEmbedder for real fine-grained retrieval.
    """

    dim = EMBED_DIM_FALLBACK

    def embed(self, image: np.ndarray) -> np.ndarray:
        import cv2

        resized = cv2.resize(image, (128, 128))
        if resized.ndim == 2:
            resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)

        # color histogram (64 bins per channel -> 192 total, downsampled to 128)
        hist_r = cv2.calcHist([resized], [0], None, [48], [0, 256]).flatten()
        hist_g = cv2.calcHist([resized], [1], None, [48], [0, 256]).flatten()
        hist_b = cv2.calcHist([resized], [2], None, [48], [0, 256]).flatten()
        color_feat = np.concatenate([hist_r, hist_g, hist_b])  # 144

        # gradient orientation histogram (coarse HOG-like signal)
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
        mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
        grad_hist, _ = np.histogram(ang, bins=112, range=(0, 360), weights=mag)

        feat = np.concatenate([color_feat, grad_hist]).astype(np.float32)  # 256
        norm = np.linalg.norm(feat)
        return feat / norm if norm > 0 else feat


def get_embedder() -> VisualEmbedder:
    """Factory: prefers CLIP, falls back to the dependency-free hash embedder."""
    try:
        return ClipEmbedder()
    except Exception:
        return HashEmbedder()
