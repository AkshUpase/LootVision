# LootVision Frontend

Camera-first AR scanner UI. React + TypeScript + Vite + Tailwind.

## Install & run

```bash
cd lootvision/frontend
npm install
npm run dev
```

Open the printed `http://localhost:5173` URL. To test on your phone (camera
access needs it), visit `http://<169.254.130.12>:5173` from your
phone on the same Wi-Fi — `vite.config.ts` already sets `host: true` for this.
Camera access over plain HTTP only works for `localhost`; for a real phone on
LAN you'll need either a self-signed HTTPS dev cert or a tunnel (e.g. `ngrok`).

By default the app calls the backend at `http://localhost:8000`. Override with
a `.env` file:

```
VITE_API_BASE=http://192.168.1.23:8000
```

## What's here (Phase 1 + 8 of the roadmap)

- `hooks/useCamera.ts` — WebRTC camera stream + frame capture to JPEG blob
- `hooks/useScanLoop.ts` — polls `/api/v1/scan` on an interval, skips
  overlapping requests
- `components/CameraFeed.tsx` — live video + scanline signature element
- `components/DetectionOverlay.tsx` — AR-style bounding boxes with floating
  price/profit HUD cards
- `components/ItemDetailSheet.tsx` — full breakdown when a detection is tapped
- `pages/Scanner.tsx` / `History.tsx` / `Settings.tsx` — the three main screens

## Design tokens

Dark HUD-scanner palette (see `tailwind.config.js`): `void` background,
`scan` (cyan-green) for detection/active state, `signal` (amber) for price,
`profit` (green) / `loss` (red) for the profitability verdict. Space Grotesk
for display type, JetBrains Mono for all numeric/data readouts — the
monospace numerals are the signature element, reinforcing that every number
on screen is a live measurement, not decoration.
