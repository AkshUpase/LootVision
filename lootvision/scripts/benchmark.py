#!/usr/bin/env python3
"""
Convenience entrypoint for the FP32 vs INT8 benchmark. Real logic lives in
ml/quantization/quantize_onnx.py — see that file's docstring for the full
explanation of what quantization does and why.

Usage:
    python scripts/benchmark.py --model data/embeddings/clip_fp32.onnx
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(ROOT / "ml" / "quantization" / "quantize_onnx.py"), run_name="__main__")
