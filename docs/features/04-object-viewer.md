# 04 - Private object reference and 3D viewer

Status: **not started**  
Dependencies: [01](01-foundation.md) for isolated viewer; [02](02-rooms-and-rounds.md) for private delivery  
References: [product](../product.md), [architecture](../architecture.md), [API](../api.md), [privacy](../privacy-and-safety.md)

## Deliverable

Speaker can explore the private 3D object before and during drawing. Drawer cannot receive it until Reveal, when both get the Discovery Reward.

## Scope and ownership

Own frontend objects module, backend asset/catalog access, object fixtures/licenses, and tests. Coordinate Storage setup and schema changes.

- Bundle model-viewer only; curated, licensed, self-contained private GLBs and matching reference images/rubrics.
- Authorized role/phase fetches; no client catalog or future-round preload.
- Rotation, zoom/reset controls, accessible labels, reduced motion, image/loading/error fallback.
- Preserve Speaker reference throughout collaboration; render it alongside a read-only canvas during integration.
- Release WebGL/viewer resources between rounds.

## Parallel boundary

An isolated viewer may use an explicitly synthetic development object after 01. Secret delivery/privacy tests require 02; never put real hidden assets in public frontend fixtures as an integration shortcut.

## Out of scope

AR/camera, procedural 3D generation, custom scene engine, Round timers, canvas ownership, and voice.

## Acceptance

- [ ] Speaker retains reference access throughout collaboration and can inspect it during questions.
- [ ] Drawer cannot obtain ID/rubric/URLs/bytes before Reveal via state, guessed requests, metadata, caches, or bundle.
- [ ] Both may explore after Reveal, including swapped roles in a later Round.
- [ ] Viewer behaves on actual iPad/iPhone; zoom/reset and fallback remain usable.
- [ ] Asset provenance/license and bounded size are recorded.
- [ ] Failed asset/WebGL loading does not block Play again.

Evidence: none yet.
