# 03 - Drawing and read-only live canvas

Status: **demo version built; not yet checked on real devices**
Dependencies: [02](02-rooms-and-rounds.md)

## Demo version

The Drawer draws with a finger; each stroke goes over the room socket and appears on the Speaker's read-only canvas. Built:

- Strokes use 0-1 coordinates of a shared 760 x 680 space, capped at 512 points each (`apps/web/src/features/game/strokes.ts`).
- Server accepts add, undo, and clear only from the Drawer during collaboration, keeps the last 256 strokes, and pushes the update to the pair (`edit_drawing` in `services/api/app/game/store.py`).
- Reconnecting gets the current strokes from the snapshot.

## Demo checks (part of D3)

- [ ] Drawing, undo, and clear work by finger on the real iPad and iPhone, in both roles.
- [ ] Speaker sees strokes appear live and cannot draw.
- [ ] Rotating the device does not break or distort the drawing.

## Later (deferred)

Revision numbers with duplicate/out-of-order handling and resync, a frozen PNG export of the submitted drawing (needed only for AI feedback in [07](07-feedback.md)), local draft recovery, payload hardening beyond current validation.
