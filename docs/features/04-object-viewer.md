# 04 - Secret object

Status: **demo version built (3D food objects); checked in WebGL browsers, not yet on a real iPad/iPhone**
Dependencies: [02](02-rooms-and-rounds.md)

## Demo version

Each round the server picks an object the pair has not seen yet from a server-only catalog of 8 low-poly foods (`services/api/app/game/objects.py`): apple, banana, carrot, strawberry, watermelon, cupcake, pizza, ice cream. Each has a checklist of visual features for the AI feedback ([07](07-feedback.md)).

- **Assets:** Kenney's Food Kit 2.0 (CC0, https://kenney.nl/assets/food-kit). Each model is one self-contained GLB (textures embedded, 20-115 KB) beside a 512 px transparent PNG rendered from it, in `services/api/app/game/assets/`. They are never in the web bundle.
- **Access:** `/api/v1/rounds/{round_id}/model` (GLB) and `/picture` (PNG) serve the round's object only to its Speaker, and to both players from Reveal on. The snapshot's `object_access` carries both URLs only when allowed.
- **Speaker view:** `<model-viewer>` shows the model in the Photo card: drag to spin (all directions), pinch to zoom, a slow auto-spin until touched. The picture shows while the 3D library and model load, and stays if WebGL or the model fails. The 3D library (~300 KB gzipped) is a lazy chunk loaded only on the play and result screens.
- **Reveal:** both players get the same 3D model beside the drawing (spin and zoom, picture while loading). The Drawer never downloads the model or picture before Reveal.

## Demo checks (part of D3)

- [x] Speaker sees and can spin the model; Drawer receives no object data before Reveal (headless Chromium with WebGL, iPhone-sized, 2026-10-11).
- [x] Reveal shows the 3D model next to the drawing on both devices (same run).
- [ ] The model loads and spins smoothly with touch on a real iPad and iPhone.

## Later (deferred)

A larger curated catalog beyond food, private cloud storage for assets, and a reset-view control.
