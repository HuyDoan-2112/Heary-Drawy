# Data model and persistence rules

Status: draft logical model. No tables or migrations exist. The foundation/rooms features will turn this into reviewed SQL migrations.

## Records

| Record | Essential fields / ownership |
| --- | --- |
| Room | ID, active shape code, host owner reference, admission status, expiry |
| Player | Opaque ID, Room ID, nickname, normalized nickname, avatar, membership status |
| Guest session | Player/Room binding, hash of securely random bearer token, expiry/revocation |
| Pair / Match | Room ID, exactly two teammate identities, initial roles, current Round |
| Round | Match ID, round index, roles, phase/version, recovery epoch, private object assignment, submission/result reference |
| Speaking hold | Round/Player/hold ID, connection epoch, requested/granted/ending/canceled/ended status, provider outcome, deadline |
| Drawing | Round ID, current revision, retained strokes/snapshot, immutable submitted revision and private PNG reference |
| Transcript/evidence | Round/Player/hold IDs, provider item ID, final/incomplete status, allowed evidence; protected by retention policy |
| Analysis job | Kind, Round/input revision, status, attempts, deadline, claim lease, bounded error code |
| Result | Round ID, analyzed input revision, rubric/model configuration versions, separate role recaps/tips, shared stars or neutral status |
| Play again intent | Round/Player ID, both-ready acknowledgement under the reviewed advance policy |

Secret object assignment/catalog/rubrics are server-private data. The shared snapshot is a deliberately constructed projection, never a serialization of all these records.

## Constraints and transactions

- Unique normalized nickname per Room. Define consistent Unicode normalization/case folding before migration; trimming/case-insensitivity are product requirements. Do not rely on a pre-check alone.
- Active shape codes cannot collide. Retired-code reuse and session cleanup need an explicit Room lifecycle policy.
- A Player has at most one active Pair in a Room; pair creation/admission is transactional.
- Unique Round index per Match; persist the initial random roles.
- Unique command ID scoped to authenticated Player/session. Retrying the same ID/payload replays its outcome; reusing it with changed content is an error.
- Unique speaking hold identity per Round/Player. Concurrent holds for different players are legal.
- Only Drawer mutates drawing revision; operations compare the expected drawing revision. Revisions increase monotonically, including undo and clear. Stroke order is independent of round phase version.
- Submission atomically freezes one revision. A retry cannot create another submission or silently substitute a new image.
- One finalized Result per Round. Jobs carry input revisions; stale/duplicate completions cannot overwrite it or award more stars.
- Result publication and transition into feedback are one database mutation/transaction.
- Round transitions use locks or optimistic version checks. Do not make every stroke/mic hold increment a global phase version that falsely serializes both children.

A provider permission update cannot be committed atomically with SQL. Store the hold's intent/status, confirm grants, cancel stale intent, and revoke/compensate late grants. Recovery must reconcile provider permissions before allowing resume.

## Drawing and assets

Retained stroke points use normalized coordinates and finite bounded numeric values, with allowed colors/widths and maximum payload/point counts. Validate PNG type, decoded dimensions, and association with the frozen revision before analysis. A client-supplied hash/filename alone does not prove which drawing it represents.

Prefer reconstructing the submitted PNG from the authoritative retained drawing when implementing the final submit path. If using client export, independently verify the correspondence; choose/document that implementation in the drawing feature.

Private asset keys are opaque. Return server-authorized access references, never arbitrary Storage keys/paths chosen by a child. The catalog stays server-side; model rubrics and bot inputs use different contracts.

## Retention and observability

Do not permanently store raw voice in this baseline. Guest tokens are hashed at rest, never logged; their returned bearer value is a one-time possession credential, not a nickname. Transcripts, drawings, evidence, and local drafts are potentially personal data even without real names.

Room/session/draft/result TTLs and backup/deletion behavior are unresolved. Define the adult-demo policy before deploying and satisfy [child-use gates](privacy-and-safety.md) before real children. Logs should contain opaque IDs, stages, timings, and bounded error codes, not raw speech, drawings, names, secrets, model prompts, or signed URLs.

Analysis jobs use bounded retries and transactional claims in the existing Postgres deployment. Expired claim leases allow restart recovery; no external queue is required for this slice.
