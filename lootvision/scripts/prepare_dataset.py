#!/usr/bin/env python3
"""
Dataset preparation and validation script for LootVision product catalog.

Scans data/products/ directory structure, validates images and metadata,
checks for duplicates, and generates a manifest of all products.

Directory structure expected:
    data/products/<category>/<product_id>/
        metadata.json
        front.jpg
        back.jpg
        side.jpg (optional)
        angled.jpg (optional)

Usage:
    python scripts/prepare_dataset.py
    python scripts/prepare_dataset.py --validate
    python scripts/prepare_dataset.py --manifest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_DIR = ROOT / "data" / "products"
VALID_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VALID_CATEGORIES = {
    "tshirts", "shirts", "hoodies", "jeans", "jackets", "shoes", "bags"
}
REQUIRED_METADATA_FIELDS = {
    "product_id", "name", "brand", "category", "model_sku",
    "original_price_usd", "estimated_resale_price_inr", "condition",
    "demo", "images", "source", "attribution"
}
VALID_CONDITIONS = {"New", "Like New", "Good", "Fair", "Poor"}
VALID_IMAGE_VIEWS = {"front", "back", "side", "angled", "detail", "tag"}


def validate_image(path: Path) -> tuple[bool, str]:
    """Validate that image file is readable and has reasonable dimensions."""
    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            w, h = img.size
            if w < 64 or h < 64:
                return False, f"Image too small: {w}x{h} (min 64x64)"
            if w > 4096 or h > 4096:
                return False, f"Image too large: {w}x{h} (max 4096x4096)"
        return True, "OK"
    except Exception as e:
        return False, f"Invalid image: {e}"


def validate_metadata(meta: dict[str, Any], product_dir: Path) -> list[str]:
    """Validate metadata.json against schema. Returns list of errors."""
    errors = []
    
    # Check required fields
    missing = REQUIRED_METADATA_FIELDS - set(meta.keys())
    if missing:
        errors.append(f"Missing required fields: {missing}")
    
    # Check category
    if "category" in meta and meta["category"] not in VALID_CATEGORIES:
        errors.append(f"Invalid category: {meta["category"]} (valid: {VALID_CATEGORIES})")
    
    # Check condition
    if "condition" in meta and meta["condition"] not in VALID_CONDITIONS:
        errors.append(f"Invalid condition: {meta["condition"]} (valid: {VALID_CONDITIONS})")
    
    # Check demo flag
    if "demo" in meta and not isinstance(meta["demo"], bool):
        errors.append("demo must be boolean")
    
    # Check images dict
    if "images" in meta:
        if not isinstance(meta["images"], dict):
            errors.append("images must be a dict mapping view -> filename")
        else:
            for view, filename in meta["images"].items():
                if view not in VALID_IMAGE_VIEWS:
                    errors.append(f"Unknown image view: {view} (valid: {VALID_IMAGE_VIEWS})")
                img_path = product_dir / filename
                if not img_path.exists():
                    errors.append(f"Referenced image not found: {filename}")
                else:
                    ok, msg = validate_image(img_path)
                    if not ok:
                        errors.append(f"Image {filename}: {msg}")
    
    # Check product_id matches directory name
    if "product_id" in meta and meta["product_id"] != product_dir.name:
        errors.append(f"product_id {meta["product_id"]} != directory name {product_dir.name}")
    
    # Check numeric fields
    for field in ["original_price_usd", "estimated_resale_price_inr"]:
        if field in meta and not isinstance(meta[field], (int, float)):
            errors.append(f"{field} must be numeric")
    
    return errors


def compute_image_hash(path: Path) -> str:
    """Compute SHA256 hash of image file for duplicate detection."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_products() -> dict[str, Any]:
    """Scan all products and return validation results."""
    results = {
        "categories": {},
        "total_products": 0,
        "total_images": 0,
        "errors": [],
        "warnings": [],
        "duplicates": [],
        "products": []
    }
    
    if not PRODUCTS_DIR.exists():
        results["errors"].append(f"Products directory not found: {PRODUCTS_DIR}")
        return results
    
    # Track hashes for duplicate detection
    hash_to_products: dict[str, list[str]] = {}
    
    for category_dir in sorted(PRODUCTS_DIR.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        
        category = category_dir.name
        results["categories"][category] = {"products": 0, "images": 0}
        
        for product_dir in sorted(category_dir.iterdir()):
            if not product_dir.is_dir() or product_dir.name.startswith("."):
                continue
            
            product_id = product_dir.name
            meta_path = product_dir / "metadata.json"
            
            # Check metadata.json exists
            if not meta_path.exists():
                results["errors"].append(f"{category}/{product_id}: metadata.json not found")
                continue
            
            # Load metadata
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                results["errors"].append(f"{category}/{product_id}: Invalid JSON in metadata.json: {e}")
                continue
            
            # Validate metadata
            errors = validate_metadata(meta, product_dir)
            if errors:
                for err in errors:
                    results["errors"].append(f"{category}/{product_id}: {err}")
                continue
            
            # Count images
            image_files = [p for p in product_dir.iterdir() if p.suffix.lower() in VALID_EXT]
            results["total_images"] += len(image_files)
            results["categories"][category]["images"] += len(image_files)
            
            # Check for duplicate images (by hash)
            for img_path in image_files:
                img_hash = compute_image_hash(img_path)
                key = f"{category}/{product_id}/{img_path.name}"
                if img_hash in hash_to_products:
                    hash_to_products[img_hash].append(key)
                else:
                    hash_to_products[img_hash] = [key]
            
            # Add to results
            results["products"].append({
                "category": category,
                "product_id": product_id,
                "name": meta.get("name"),
                "brand": meta.get("brand"),
                "demo": meta.get("demo", False),
                "image_count": len(image_files),
                "views": list(meta.get("images", {}).keys())
            })
            
            results["categories"][category]["products"] += 1
            results["total_products"] += 1
    
    # Report duplicates
    for img_hash, locations in hash_to_products.items():
        if len(locations) > 1:
            results["duplicates"].append({
                "hash": img_hash[:16] + "...",
                "locations": locations
            })
            results["warnings"].append(f"Duplicate image hash found: {locations}")
    
    return results


def print_results(results: dict[str, Any], verbose: bool = False) -> None:
    """Print validation results in a readable format."""
    print("\n=== LootVision Dataset Validation ===\n")
    
    print(f"Total Products: {results["total_products"]}")
    print(f"Total Images:   {results["total_images"]}")
    
    print("\nBy Category:")
    for cat, info in results["categories"].items():
        print(f"  {cat}: {info["products"]} products, {info["images"]} images")
    
    if results["duplicates"]:
        print(f"\nDuplicate Images: {len(results["duplicates"])} groups")
        for dup in results["duplicates"]:
            print(f"  Hash: {dup["hash"]}")
            for loc in dup["locations"]:
                print(f"    - {loc}")
    
    if results["errors"]:
        print(f"\nErrors ({len(results["errors"])}):")
        for err in results["errors"]:
            print(f"  - {err}")
    else:
        print("\nNo validation errors")
    
    if results["warnings"]:
        print(f"\nWarnings ({len(results["warnings"])}):")
        for warn in results["warnings"]:
            print(f"  - {warn}")
    
    if verbose and results["products"]:
        print("\nProduct Details:")
        for p in results["products"]:
            demo_str = " [DEMO]" if p["demo"] else ""
            print(f"  {p["category"]}/{p["product_id"]}: {p["name"]} ({p["brand"]}){demo_str}")
            print(f"    Images: {p["image_count"]} ({", ".join(p["views"])})")


def generate_manifest(results: dict[str, Any], output_path: Path) -> None:
    """Generate a manifest JSON file for the dataset."""
    manifest = {
        "version": 1,
        "total_products": results["total_products"],
        "total_images": results["total_images"],
        "categories": {
            cat: {"products": info["products"], "images": info["images"]}
            for cat, info in results["categories"].items()
        },
        "products": results["products"]
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Validate and prepare LootVision product dataset")
    parser.add_argument("--validate", action="store_true", help="Run validation only")
    parser.add_argument("--manifest", type=str, help="Output manifest JSON path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix common issues (placeholder)")
    args = parser.parse_args()
    
    results = scan_products()
    print_results(results, verbose=args.verbose)
    
    if args.manifest:
        generate_manifest(results, Path(args.manifest))
    
    if results["errors"]:
        print("\nValidation FAILED")
        sys.exit(1)
    else:
        print("\nValidation PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
