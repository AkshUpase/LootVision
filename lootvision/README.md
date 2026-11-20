# LootVision — AI-Powered Visual Reselling Assistant

> "LootVision is not a barcode scanner or traditional product classifier. It is a
> fine-grained visual retrieval system designed to bridge the domain gap between
> cluttered real-world thrift-store imagery and clean e-commerce product imagery."

**Research question:** Can a lightweight visual representation model reliably
identify valuable products from cluttered, poorly lit, real-world thrift-store
images by retrieving their nearest matches from a clean e-commerce image database?

---

## 1. System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (Browser)                            │
│                                                                            │
│   Phone Camera ──▶ WebRTC video stream ──▶ Canvas frame sampler          │
│         │                                          │                     │
│         │                                          ▼                     │
│         │                          ┌───────────────────────────┐         │
│         │                          │  Local ONNX/WASM inference │        │
│         │                          │  (YOLO-nano detector, opt.)│        │
│         │                          └──────────────┬─────────────┘        │
│         │                                         │ crops                │
│         ▼                                         ▼                      │
│   Live <video>                         POST /api/v1/scan (multipart)     │
└──────────────────────────────────────────┼───────────────────────────────┘
                                            │
                                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI, Python)                        │
│                                                                            │
│  /api/v1/scan                                                            │
│     1. Detection service   (YOLOv8n)        → boxes[]                    │
│     2. Crop + preprocess                                                 │
│     3. Embedding service   (CLIP/SigLIP)    → vector[512]                │
│     4. Retrieval service   (FAISS/Chroma)   → top-K matches + cos-sim    │
│     5. Condition service   (CNN / anomaly)  → condition score            │
│     6. Pricing service     (mock/eBay API)  → resale price               │
│     7. Profit engine       (config-driven)  → profit, ROI                │
│                                                                            │
│  Persistent stores:                                                      │
│     SQLite/Postgres  — product metadata, scan history, settings          │
│     FAISS/Chroma     — product embeddings (swap-in, no retraining)       │
└──────────────────────────────────────────────────────────────────────────┘
```

## 2. Data Flow (per detected object)

```
Camera Frame
   → Object Detection (YOLOv8n)               [bbox, class, det_conf]
   → Crop + Resize + Normalize
   → Visual Embedding (CLIP ViT-B/32 or SigLIP)[512-d / 768-d vector]
   → Vector Similarity Search (FAISS, cosine)  [top-K product matches]
   → Condition / Anomaly Model                 [condition score 0-100]
   → Marketplace Price Lookup (mock/eBay)      [resale price estimate]
   → Profit Engine (config formula)            [profit, ROI, confidence]
   → AR Overlay Render                         [box + label + price + profit]
```

## 3. Technology Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite + Tailwind | fast iteration, typed, mobile-friendly |
| Camera | `getUserMedia` WebRTC + `<canvas>` sampling | native browser API, no plugin |
| Edge inference (optional) | ONNX Runtime Web (WASM/WebGPU) | run detector/embedder client-side |
| Backend | FastAPI (Python 3.11) | async, typed, easy ML integration |
| Detection | YOLOv8n (Ultralytics) | small, real-time, well documented |
| Embedding | CLIP ViT-B/32 (open_clip) or SigLIP | zero-shot, no retraining needed |
| Vector DB | FAISS (local) — ChromaDB as drop-in alt | add products without retraining |
| Metadata DB | SQLite (dev) → Postgres (prod) | relational product/history data |
| Quantization | ONNX Runtime INT8 dynamic quant | mobile-viable latency |
| Pricing | Mock pricing service (clearly labeled) + eBay Browse API adapter | no fabricated live prices |

## 4. Folder Structure

```
lootvision/
├── frontend/        React/TS/Vite scanner UI
├── backend/          FastAPI app: api routes, services, db models
├── ml/                detection / embeddings / retrieval / condition / quantization / evaluation
├── data/              products (images), embeddings (built index), metadata (csv/json)
├── scripts/           generate_embeddings.py, build_index.py, benchmark.py, evaluate.py
└── README.md
```

## 5. Model Selection Reasoning

- **Detection — YOLOv8n over two-stage detectors (Faster R-CNN):** we need
  real-time performance on commodity hardware / browser edge; YOLO's single-pass
  design trades a little accuracy for large speed gains, acceptable since detection
  here only needs to isolate "an object worth inspecting," not classify it.
- **Embedding — CLIP/SigLIP over a trained classifier:** a classifier requires a
  fixed, retrained label set. Thrift inventory is open-set and constantly changing.
  Embedding + nearest-neighbor retrieval lets us **add new products by inserting a
  vector**, with zero retraining — this is the core design requirement in §5/§6 of
  the brief, and the reason this is a retrieval problem, not a classification problem.
- **Condition — lightweight CNN / anomaly detector, not damage-segmentation:** a
  full damage-segmentation model needs pixel-level labels we don't have. A
  practical baseline (fine-tuned small CNN regressing a 0-100 score, or a
  feature-space anomaly detector comparing against "clean" reference embeddings)
  is realistic for a student project and is explicitly designed to be swapped for
  a stronger model later (see `ml/condition/`).

## 6. Evaluation Methodology

| Component | Metrics |
|---|---|
| Detection | Precision, Recall, mAP@0.5, FPS |
| Retrieval | Top-1 / Top-5 accuracy, Recall@K, mean cosine similarity |
| Condition | Accuracy, Precision, Recall, F1 |
| Edge optimization | FP32 vs INT8: model size, latency, FPS, memory, accuracy delta |
| **Domain gap** (headline experiment) | Top-1/Top-5 accuracy for Clean→Clean vs Cluttered→Clean retrieval |

All numbers are produced by `scripts/evaluate.py` and `scripts/benchmark.py` against
whatever data/model is actually present — **nothing here is a fabricated result**.
Until real data/models are loaded, these scripts will report "no data" rather than
invented numbers.

## 7. Research Novelty

The core contribution is not the app — it's the **domain-gap retrieval experiment**:
measuring how much retrieval accuracy degrades when the query image comes from a
cluttered, poorly-lit thrift-store photo instead of a clean product photo, and then
testing concrete mitigations (background removal, augmentation, hard-negative
contrastive fine-tuning). See `ml/evaluation/domain_gap.py` (Phase 10).

## 8. Risks & Limitations

- Retrieval accuracy is fundamentally bounded by product-database coverage — an
  item with no visually similar entry in the DB cannot be correctly matched.
  The UI must communicate "no reliable match" rather than guessing (see `MatchConfidence`).
- Condition scoring from a single 2D image cannot detect internal/functional
  defects (e.g., a camera's shutter failure) — only visible surface damage.
- Marketplace pricing without a live API key is **mocked and clearly labeled**;
  do not present mock prices as real listings.
- Real-time in-browser inference (ONNX/WASM) has real hardware limits on older
  phones; the architecture falls back to server-side inference over the network.

## 9. Demonstrating to a Professor

1. Lead with the domain-gap experiment plot (clean-vs-cluttered Top-1 accuracy) —
   this is the thesis, not the camera UI.
2. Show the live scanner second, as the applied demonstration of the retrieval system.
3. Walk through FP32→INT8 quantization numbers from `scripts/benchmark.py` to show
   the edge-AI angle is real, not aspirational.
4. Be explicit about what's mocked (pricing API) vs measured (all ML metrics).

## 10. Development Roadmap (Phases)

- [x] **Phase 1** — Project scaffold + camera scanner UI shell *(this delivery)*
- [x] **Phase 2** — Object detection service (stubbed interface + YOLOv8n integration point)
- [x] **Phase 3** — CLIP/SigLIP embedding service
- [x] **Phase 4** — FAISS vector index + build script
- [x] **Phase 5** — Detection → embedding → retrieval wiring (`/api/v1/scan`)
- [ ] **Phase 6** — Condition assessment model (baseline scaffolded, needs labeled data to train)
- [x] **Phase 7** — Mock pricing + profit engine
- [x] **Phase 8** — AR-style overlay UI
- [ ] **Phase 9** — ONNX export + INT8 quantization + benchmark run
- [ ] **Phase 10** — Domain-gap experiment with real Domain A / Domain B image sets
- [ ] **Phase 11** — Polish + demo script

Phases marked `[ ]` need either real image data, a GPU for fine-tuning, or a
marketplace API key that only you can supply — the code scaffolding and scripts
for them are included and ready to run once that's in place.

## 11. Setup

See `frontend/README.md` and `backend/README.md` for install/run instructions.
