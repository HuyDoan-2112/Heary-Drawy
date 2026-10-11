# Round lifecycle

Status: draft state contract supporting the [agreed mechanism](product.md). No state machine has been implemented. Round timer, match length, and Play again disconnect timeout remain provisional.

## States

Room admission and Pair waiting happen before a Round exists. Within a Round:

```text
role_intro -> collaborating -> finalizing -> feedback -> exploring -> finished
                                                                    |
                                              next Round, roles swapped
```

| State | Speaker | Drawer | Server responsibility |
| --- | --- | --- | --- |
| `role_intro` | Brief role orientation; object may be assigned for Speaker access | Brief role orientation; no object | Record roles, object assignment, intro timing |
| `collaborating` | Keep reference; read-only live canvas; hold to talk | Edit canvas; hold to ask/clarify | Validate live strokes, independent microphone grants, pair isolation |
| `finalizing` | No microphone grant; waiting | Frozen acknowledged drawing revision; waiting | Stop both grants, finalize permitted audio, process bounded evidence jobs |
| `feedback` | Speaker panel and shared team result | Drawer panel and shared team result | Publish one finalized result; allow object Reveal to both |
| `exploring` | Authorized 3D exploration | Authorized 3D exploration | Track Play again intent and make viewer fallback usable |
| `finished` | No live editing/talking for this Round | Same | Close round; create next Round with swapped roles or finish Match |

Object visibility is role/phase-dependent. Speaker receives object access for collaboration and keeps it through the Round. Drawer receives object data only in `feedback`, `exploring`, or `finished`, never during role intro or collaboration.

## Transition rules

- Randomize initial roles once per Match; persist them. A reconnect does not reroll roles or choose another secret.
- Role intro is a short child-facing orientation before collaboration. The demo has no separate private preparation period.
- Both microphone holds are independently permitted only during collaboration. There is no single-speaker floor and no one-question cap.
- Drawer submission references the last acknowledged drawing revision. Reject or resynchronize if it differs from authoritative state; do not analyze a canvas that the Speaker/server never received.
- Entering finalization freezes editing, cancels outstanding holds, and invalidates delayed grants. Let already permitted tails finalize under a bounded tested policy.
- Analysis has a deadline. Missing evidence gives neutral/incomplete feedback, not a fabricated low score. Persist result and feedback state together once.
- Open exploration through an explicit acknowledgement of feedback presentation. Its exact UI may be one combined screen, but permissions must remain equivalent.
- Play again uses both-ready acknowledgement before creating the next Round and swapping roles. If one child is ready first, show friendly waiting copy. Do not require a vanished teammate indefinitely; record the reviewed disconnect/timeout behavior.
- A new Round has a new ID/epoch; old holds, strokes, jobs, and Play again messages cannot mutate it. Do not reveal/preload the next object's secret to its Drawer.

## Pausing and recovery

Connection/media trouble can pause a Round without changing its underlying stage. Stop local audio and new editing as appropriate; show a clear reconnect state rather than silently continuing.

- Reconnect authenticates the same guest session and retrieves a role-filtered current snapshot plus the permitted canvas revision.
- In-memory voice grants are not inferred from persisted intent. Revoke stale provider permissions before resuming; the user must press again.
- A backend restart reconstructs game state from Postgres, retries eligible analysis jobs, and marks unrecoverable ephemeral speech incomplete.
- Never automatically replay audio, reopen microphones, or replay queued presses after reconnect.
- Room expiry closes sessions and cancels media/jobs according to the approved cleanup policy.
- One child leaving requires an explicit retry/end/adult-help path. Automatic bot substitution mid-round is not part of the initial demo.

See [API](api.md) for message identities, [data model](data-model.md) for idempotency, and [testing](testing.md) for transition/recovery acceptance.
