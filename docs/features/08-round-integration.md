# 08 - Full round, Reveal, and role swap

Status: **demo version built; real-device walkthrough is step D3**
Dependencies: [02](02-rooms-and-rounds.md)-[07](07-feedback.md) demo versions

## Demo version

The web app runs the whole flow from server snapshots: grown-up passcode, character pick, pairing, role intro, live drawing and voice, Done, Reveal with the neutral result (AI feedback after D2), Play again with roles swapped, up to 3 rounds, and Done to leave.

## Demo checks (D3)

- [ ] Two adults complete 3 rounds on the real iPad and iPhone, each device playing both roles.
- [ ] Drawing and holding the talk button at the same time work (multitouch).
- [ ] Play again waits for both players, then swaps roles once.
- [ ] No screen has broken layout, clipped text, or horizontal scrolling on either device.

Record device models, iOS versions, and results in [testing.md](../testing.md).

## Later (deferred)

A round timer, a 60-second disconnect timeout with a grown-up help screen, and recovery from late events across rounds.
