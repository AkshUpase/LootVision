# 🔍 LootVision — AI-Powered Visual Reselling Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PyTorch-2.4-EE4C2C?style=for-the-badge&logo=pytorch" alt="PyTorch">
  <img src="https://img.shields.io/badge/OpenCLIP-ViT--B%2F32-792EE5?style=for-the-badge" alt="OpenCLIP">
  <img src="https://img.shields.io/badge/FAISS-CPU%201.8-00599C?style=for-the-badge" alt="FAISS">
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge" alt="YOLOv8">
  <img src="https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react" alt="React 18">
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css" alt="Tailwind CSS">
</p>

---

> **Creator & Developer:** **Aksh Upase**  
> **Contact:** [Akshupase06@gmail.com](mailto:Akshupase06@gmail.com)  
> **Project Repository:** LootVision  

---

## 📌 Project Overview

**LootVision** is an AI-powered visual retrieval system and reselling assistant built for thrift-store shoppers, vintage collectors, and arbitrage resellers. Unlike standard barcode scanners or traditional product classifiers with fixed categories, LootVision uses **fine-grained visual embedding and zero-shot vector retrieval** to bridge the domain gap between real-world cluttered images and clean e-commerce catalog items.

### 🎯 Key Research Question
*Can a lightweight visual representation model reliably identify valuable products from cluttered, poorly lit, real-world thrift-store scenes by retrieving their nearest matches from a clean catalog without requiring model retraining?*

---

## 🌟 Key Features

- **📱 Mobile-First AR HUD Experience**:
  - Live WebRTC camera scanner with touch-optimized controls.
  - Edge-aware AR bounding box overlays that flip and shift to remain visible on screen.
  - Camera flip (front/back), torch/flashlight toggle, and frame freeze/scan buttons.
  - **Swipe-to-dismiss** interactive bottom sheet with slide-up animations.
  - Built-in **Gallery Image Upload** fallback for scanning photos without camera access.

- **🧠 OpenCLIP Visual & Text Embeddings (ViT-B/32)**:
  - Produces L2-normalized 512-dimensional embeddings directly from detected object crops.
  - Uses shared vision-language representation space, enabling catalog population from detailed text prompts or clean images.

- **⚡ Zero-Retraining Vector Retrieval (FAISS)**:
  - High-performance `IndexFlatIP` inner-product search over cosine-normalized vectors.
  - Products can be added to the catalog instantly without gradient descent or model fine-tuning.

- **🔍 Smart Object Detection & Centered Crop Fallback (YOLOv8n)**:
  - Real-time YOLOv8n object detection isolating candidate items in the frame.
  - Smart center-frame fallback for unclassified categories (e.g. vintage t-shirts, clothing) ensuring seamless scanning.

- **📊 Computer Vision Condition Assessment**:
  - Classical CV wear-and-tear estimation analyzing surface texture irregularities (Laplacian variance), contrast fading, and symmetry deviations.
  - Returns a calibrated 0–100 condition score with descriptive damage tags.

- **💰 Intelligent Resale & Profit Engine (INR / ₹)**:
  - Real-time resale valuation based on market catalog benchmarks.
  - Condition-adjusted pricing, marketplace fee deductions, and estimated shipping costs.
  - Computes Net Estimated Profit, ROI %, and visual "Profitable" / "Unprofitable" badges.

- **🌐 Cross-Device Accessibility**:
  - Full local support on desktop and laptop browsers (`localhost:5173`).
  - Seamless tunnel integration via **ngrok** for mobile access with full HTTPS camera permissions (`getUserMedia`).

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             CLIENT (Browser)                             │
│                                                                          │
│   Phone / Laptop Camera ──▶ WebRTC Stream ──▶ Canvas Frame Sampler      │
│            │                                         │                   │
│            ▼                                         ▼                   │
│      Live <video>                      POST /api/v1/scan (multipart)     │
│   (object-contain AR HUD)                            │                   │
└──────────────────────────────────────────────────────┼───────────────────┘
                                                       │
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI / Python)                        │
│                                                                          │
│  /api/v1/scan                                                            │
│    ├── 1. Object Detector   (YOLOv8n + Center Fallback) ──▶ BBoxes[]     │
│    ├── 2. Crop & Normalizer (Pillow / OpenCV)                            │
│    ├── 3. Visual Embedder   (OpenCLIP ViT-B/32)         ──▶ 512-d Vector │
│    ├── 4. Vector Retriever  (FAISS IndexFlatIP)         ──▶ Top Matches  │
│    ├── 5. Condition Scorer  (Laplacian/Contrast/CV)     ──▶ Score 0-100  │
│    ├── 6. Pricing Service   (Mock Catalog / eBay API)   ──▶ Base Resale  │
│    └── 7. Profit Engine     (Fee, Shipping, ROI)        ──▶ Net Profit   │
│                                                                          │
│  Persistent Stores:                                                      │
│    ├── SQLite (lootvision.db)   ── Product metadata, history, settings   │
│    └── FAISS (product_index)    ── 512-d normalized catalog embeddings   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Product Catalog Categories

The retrieval database includes **64+ catalog items** embedded across 11 key resale categories, with realistic Indian Rupee (**₹**) valuations:

| Category | Sample Products in Catalog | Typical Price Range |
|---|---|---|
| **Laptops & Tech** | MacBook Air, MacBook Pro, Dell XPS 13, ThinkPad, Gaming Laptop | ₹15,000 – ₹75,000 |
| **T-Shirts & Tops** | Vintage Band Tees, Sports Jerseys, Graphic Tees, Polo Shirts | ₹400 – ₹1,500 |
| **Shirts** | Flannel Shirts, Denim Shirts, Formal Dress Shirts, Hawaiian Shirts | ₹500 – ₹2,500 |
| **Sneakers & Shoes** | Nike Running Shoes, Converse High Tops, Adidas Retro, Loafers | ₹2,000 – ₹9,000 |
| **Jackets & Outerwear** | Denim Jackets, Leather Biker Jackets, Bomber Jackets, Hoodies | ₹900 – ₹5,000 |
| **Cameras** | Canon DSLR, Sony Mirrorless, Vintage 35mm Film, Fujifilm Instax | ₹4,000 – ₹25,000 |
| **Gaming Gear** | PlayStation DualShock, Xbox Wireless, Nintendo Switch Joy-Con | ₹800 – ₹4,500 |
| **Watches** | Casio Analog, Digital Sport, Smartwatches, Vintage Mechanical | ₹1,200 – ₹12,000 |
| **Bags** | Canvas Backpacks, Leather Totes, Messenger Bags, Fanny Packs | ₹700 – ₹6,500 |
| **Audio** | Sony Over-Ear Headphones, Bluetooth Earbuds, Foldable Headphones | ₹700 – ₹6,000 |
| **Pants & Bottoms** | Levi's Blue Jeans, Cargo Shorts, Chino Trousers, Denim Skirts | ₹600 – ₹2,500 |

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind CSS | High-performance reactive mobile interface |
| **Icons & Design** | Custom Lucide-style SVGs, CSS animations | Lightweight, zero extra runtime dependencies |
| **Backend API** | FastAPI, Uvicorn, Python 3.10+ | Asynchronous REST API with auto OpenAPI docs |
| **Object Detection** | Ultralytics YOLOv8n (COCO weights) | Rapid single-pass edge object proposal |
| **Embedding Model** | OpenCLIP (ViT-B/32, LAION-2B weights) | Fine-grained visual representation & text encoder |
| **Vector Index** | FAISS CPU (`IndexFlatIP`) | Real-time cosine similarity search (exact inner product) |
| **Condition Analysis** | OpenCV, NumPy, SciPy | Surface texture, contrast degradation, and symmetry metrics |
| **Database** | SQLite + SQLAlchemy | Scan history and user configuration persistence |
| **Tunneling** | ngrok v3 | Secure HTTPS tunneling for mobile camera support |

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Git**
- (Optional) **ngrok** account for mobile testing

---

### 2. Backend Setup

```powershell
# Navigate to project directory
cd lootvision/lootvision

# Install Python backend dependencies
pip install -r backend/requirements.txt

# Populate catalog and generate FAISS vector index
python scripts/populate_catalog.py

# Start FastAPI backend server
python -m uvicorn backend.main:app --reload --port 8000
```
Backend will be live at: `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)

---

### 3. Frontend Setup

Open a new terminal:
```powershell
# Navigate to frontend folder
cd lootvision/lootvision/frontend

# Install node dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend will be live at: `http://localhost:5173`

---

### 4. Mobile Access via ngrok (Recommended)

Browsers restrict camera access (`getUserMedia`) to `localhost` or verified `HTTPS` origins. To test on a mobile phone:

```powershell
# Start ngrok tunnel pointing to Vite dev server
ngrok http 5173
```
Open the generated `https://<your-subdomain>.ngrok-free.dev` on your smartphone browser.

---

## 📡 API Reference

### `POST /api/v1/scan`
Uploads a captured camera frame or image file for end-to-end detection, embedding, matching, condition scoring, and profit calculation.

**Request:** `multipart/form-data`
- `file`: Image file (JPEG/PNG)
- `purchase_price`: Float (default `500.0`)
- `confidence_threshold`: Float (default `0.70`)
- `fee_percent`: Float (default `0.12`)
- `shipping_estimate`: Float (default `100.0`)

**Response:**
```json
{
  "scan_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "timestamp": "2026-11-20T08:00:00Z",
  "processing_time_ms": 142.5,
  "items": [
    {
      "detection": {
        "detection_id": "a82f...",
        "bbox": {"x": 0.15, "y": 0.20, "width": 0.70, "height": 0.65},
        "category": "laptop",
        "detection_confidence": 0.85
      },
      "best_match": {
        "product_id": "laptop_macbook_air",
        "product_name": "Apple MacBook Air",
        "brand": "Apple",
        "category": "laptop",
        "similarity": 0.826,
        "marketplace_price": 55000.0
      },
      "condition": {
        "score": 92,
        "label": "Excellent",
        "visible_damage": ["No significant surface damage visually detected"]
      },
      "pricing": {
        "estimated_resale_price": 50600.0,
        "purchase_price": 500.0,
        "estimated_profit": 44028.0,
        "roi_percent": 8805.6,
        "is_profitable": true
      }
    }
  ]
}
```

### Other Endpoints
- `GET /api/v1/history?limit=50`: Returns logged past scans with thumbnail previews and profit details.
- `GET /api/v1/settings`: Fetches current user defaults (currency, purchase price, fee %, shipping).
- `PUT /api/v1/settings`: Updates user configuration.
- `GET /health`: Health check endpoint.

---

## 🔬 Research & Evaluation Framework

LootVision incorporates evaluation scripts in `scripts/`:
- `scripts/generate_embeddings.py`: Batch image embedder for external product image folders.
- `scripts/build_index.py`: Serializes embeddings into high-speed FAISS vector databases.
- `scripts/evaluate.py`: Calculates Top-1 / Top-5 retrieval accuracy and Recall@K.
- `scripts/benchmark.py`: Measures inference latency (FPS) across detection, embedding, and retrieval stages.

---

## 👨‍💻 Author

**Aksh Upase**  
- **Email**: [Akshupase06@gmail.com](mailto:Akshupase06@gmail.com)  
- **Role**: Lead Developer & System Architect  
- **Project**: LootVision — AI Visual Reselling Assistant  

---

## 📄 License

This project is licensed under the MIT License — feel free to use and adapt for academic, research, and non-commercial resale projects.
