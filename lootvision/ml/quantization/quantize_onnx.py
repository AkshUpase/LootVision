"""
Edge-AI optimization: export a model to ONNX, then apply INT8 dynamic
quantization, and benchmark FP32 vs INT8.

What quantization does
-----------------------
Neural network weights (and often activations) are normally stored as 32-bit
floats (FP32). Dynamic INT8 quantization maps weight tensors to 8-bit
integers using a per-tensor (or per-channel) scale/zero-point, computed from
the weight's value range - "dynamic" because activation ranges are computed
on-the-fly at inference time rather than requiring a calibration pass.

Why it helps
-------------
- **Model size**: INT8 weights are ~4x smaller than FP32 (1 byte vs 4 bytes
  per parameter) - critical for shipping a model to a phone browser.
- **Inference speed**: integer arithmetic is cheaper than float arithmetic on
  most CPUs (and has dedicated fast paths in ONNX Runtime / mobile NPUs),
  so latency typically drops meaningfully, especially on CPU-only devices.
- **Accuracy trade-off**: quantization introduces rounding error. For most
  CNN/ViT backbones used for embeddings/detection, INT8 dynamic quantization
  costs a small amount of accuracy (often <1-2% on classification-style
  metrics) in exchange for large speed/size wins - but this must be measured,
  not assumed, which is what `run_benchmark()` below does.

Usage
-----
This script does NOT fabricate benchmark numbers. It requires an actual
ONNX model file to run against. Export your embedding or detection model to
ONNX first (see the `export_clip_to_onnx` helper below for an example using
open_clip + torch.onnx.export), then run:

    python ml/quantization/quantize_onnx.py --model path/to/model.onnx

If no model is supplied, it prints instructions rather than pretending to
benchmark something that doesn't exist.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path


def export_clip_to_onnx(output_path: str, model_name: str = "ViT-B-32", pretrained: str = "laion2b_s34b_b79k") -> None:
    """Example export helper - requires torch + open_clip installed."""
    import open_clip
    import torch

    model, _, _ = open_clip.create_model_and_transforms(model_name, pretrained=pretrained)
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)

    class ImageEncoderWrapper(torch.nn.Module):
        def __init__(self, clip_model):
            super().__init__()
            self.clip_model = clip_model

        def forward(self, x):
            return self.clip_model.encode_image(x)

    wrapper = ImageEncoderWrapper(model)
    torch.onnx.export(
        wrapper,
        dummy_input,
        output_path,
        input_names=["image"],
        output_names=["embedding"],
        dynamic_axes={"image": {0: "batch"}, "embedding": {0: "batch"}},
        opset_version=17,
    )
    print(f"Exported ONNX model to {output_path}")


def quantize_dynamic_int8(fp32_model_path: str, int8_model_path: str) -> None:
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(
        model_input=fp32_model_path,
        model_output=int8_model_path,
        weight_type=QuantType.QInt8,
    )
    print(f"Quantized model written to {int8_model_path}")


def run_benchmark(fp32_path: str, int8_path: str, n_runs: int = 50) -> dict:
    import numpy as np
    import onnxruntime as ort

    def bench(path: str) -> dict:
        session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        input_name = session.get_inputs()[0].name
        input_shape = [d if isinstance(d, int) else 1 for d in session.get_inputs()[0].shape]
        dummy = np.random.randn(*input_shape).astype(np.float32)

        # warmup
        for _ in range(5):
            session.run(None, {input_name: dummy})

        start = time.perf_counter()
        for _ in range(n_runs):
            session.run(None, {input_name: dummy})
        elapsed = time.perf_counter() - start

        return {
            "avg_latency_ms": (elapsed / n_runs) * 1000,
            "fps": n_runs / elapsed,
            "model_size_mb": Path(path).stat().st_size / (1024 * 1024),
        }

    fp32_stats = bench(fp32_path)
    int8_stats = bench(int8_path)

    return {
        "fp32": fp32_stats,
        "int8": int8_stats,
        "speedup": fp32_stats["avg_latency_ms"] / int8_stats["avg_latency_ms"],
        "size_reduction_percent": (
            (1 - int8_stats["model_size_mb"] / fp32_stats["model_size_mb"]) * 100
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quantize and benchmark an ONNX model.")
    parser.add_argument("--model", type=str, help="Path to an FP32 .onnx model")
    parser.add_argument("--runs", type=int, default=50)
    args = parser.parse_args()

    if not args.model:
        print(
            "No --model provided.\n\n"
            "Steps to produce real benchmark numbers:\n"
            "  1. Export a model to ONNX, e.g.:\n"
            "       python -c \"from ml.quantization.quantize_onnx import export_clip_to_onnx; "
            "export_clip_to_onnx('data/embeddings/clip_fp32.onnx')\"\n"
            "  2. Run this script:\n"
            "       python ml/quantization/quantize_onnx.py --model data/embeddings/clip_fp32.onnx\n"
        )
        raise SystemExit(0)

    fp32_path = args.model
    int8_path = fp32_path.replace(".onnx", "_int8.onnx")
    quantize_dynamic_int8(fp32_path, int8_path)
    results = run_benchmark(fp32_path, int8_path, n_runs=args.runs)

    print("\n=== FP32 vs INT8 Benchmark ===")
    for precision in ("fp32", "int8"):
        s = results[precision]
        print(
            f"{precision.upper():>5}: {s['avg_latency_ms']:.2f} ms/run  "
            f"{s['fps']:.1f} FPS  {s['model_size_mb']:.2f} MB"
        )
    print(f"\nSpeedup: {results['speedup']:.2f}x")
    print(f"Size reduction: {results['size_reduction_percent']:.1f}%")
    print(
        "\nNote: accuracy change is NOT measured by this script - re-run your "
        "retrieval/detection evaluation (ml/evaluation/) against the INT8 "
        "model separately and compare to the FP32 numbers to report that delta."
    )
