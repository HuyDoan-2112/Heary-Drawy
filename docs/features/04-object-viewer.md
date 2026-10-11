# 04 - Secret picture

Status: **demo version built (2D pictures); 3D viewer deferred**
Dependencies: [02](02-rooms-and-rounds.md)

## Demo version

Each round the server picks a picture the pair has not seen yet from a small server-only catalog of 6 SVG pictures (`services/api/app/game/objects.py`). The Speaker sees it throughout the round; the Drawer gets it only at Reveal, when both see it beside the drawing. The picture is served from `/api/v1/rounds/{round_id}/picture` only to an authorized player, and is not in the web bundle.

## Demo checks (part of D3)

- [ ] Speaker sees the picture on both devices; Drawer does not until Reveal.
- [ ] Reveal shows the picture next to the drawing on both devices.

## Later (deferred)

Interactive 3D models (model-viewer + licensed GLB files in private storage) with rotate/zoom, an image fallback when 3D fails, and a larger curated catalog with a feature checklist per object for AI feedback.
