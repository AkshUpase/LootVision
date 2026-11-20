# LootVision Backend

FastAPI service implementing the detection -> embedding -> retrieval ->
condition -> pricing -> profit pipeline.

## Install

```bash
cd lootvision
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Minimal install (heuristic detector + hash embedder, no GPU/model downloads):
pip install fastapi "uvicorn[standard]" python-multipart pydantic sqlalchemy \
            pillow numpy opencv-python-headless faiss-cpu

# Full install (real YOLOv8n + CLIP retrieval - larger download, needs internet):
pip install -r backend/requirements.txt
```

The pipeline auto-detects what's installed: `get_detector()` and
`get_embedder()` (in `ml/detection` and `ml/embeddings`) fall back to
dependency-free implementations if `ultralytics` / `open_clip_torch` aren't
present, so the API is runnable end-to-end either way. Retrieval quality is
real only with the full install — see the docstrings in those files.

## Build the product index (required before /api/v1/scan returns matches)

```bash
python scripts/generate_embeddings.py   # embeds data/products/* into vectors
python scripts/build_index.py           # builds data/embeddings/product_index.faiss
```

Until you run these, `/api/v1/scan` will still return detections but with no
product matches (`best_match: null`) — this is intentional, not a bug: there's
no catalog to retrieve against yet.

## Run

```bash
uvicorn backend.main:app --reload --port 8000
```

Then visit `http://localhost:8000/docs` for the interactive API explorer.

## Test

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -F "file=@data/products/sneakers/sample.jpg" \
  -F "purchase_price=800" \
  -F "confidence_threshold=0.65"
```

## Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy DSN, defaults to local SQLite |
| `EBAY_APP_ID` | If set, pricing switches from mock catalog to the eBay Browse API adapter (still needs OAuth wiring — see `backend/services/pricing.py`) |
