# Research archive and background

These reports preserve earlier primary-source research and review, checked on 2026-10-10. They are not current implementation specifications and do not prove measured latency, educational effectiveness, child-data eligibility, or exhaustive originality.

- [Market research](market-research.md): comparison landscape and cautious positioning.
- [Technical research](technical-research.md): live voice/AI/privacy research with earlier game mechanics and stack candidates.
- [iPad/iPhone research](ios-platform-research.md): Safari and future native-platform considerations, not hardware validation.
- [Independent architecture review](architecture-review.md): one read-only agent review, before guest-session and live-collaboration revisions; not an independent live-source/device test.

## Superseded proposals

Current behavior is owned by [product.md](../product.md), and component recommendations by [architecture.md](../architecture.md). In particular:

- Both roles now independently hold to talk during live drawing; no strict alternating floor or one-question cap.
- Speaker keeps the private 3D reference and sees the live Drawer canvas.
- Drawer remains secret-blind until Reveal.
- AI supplies separate role feedback after the Round, not mandatory mid-turn coaching.
- Nickname + guest session replaces the earlier Supabase Auth proposal for the demo.
- Live drawing synchronization is required, not deferred.

The [historical HTML explainer](../../.lavish/technical-research.html) preserves the older report snapshot. Its body should not override current docs. Use the [current documentation index](../README.md) and [implementation plan](../implementation-plan.md) for the organized build plan.
