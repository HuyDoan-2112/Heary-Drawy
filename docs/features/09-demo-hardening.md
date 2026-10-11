# 09 - Demo setup

Status: **not started - steps D1 and D4 in the [implementation plan](../implementation-plan.md)**
Dependencies: [08](08-round-integration.md)

## Demo version

The demo runs from a laptop on the same Wi-Fi as the iPad and iPhone. No hosting.

- **D1:** one command starts the API and serves the web app over HTTPS on the LAN (a self-signed or locally trusted certificate is fine), allows that origin on the room socket, and prints the URL and Room passcode. It reads `DEEPSEEK_API_KEY` from the shell for AI feedback; without it rounds use the neutral result.
- **D4:** a short README section: start command, how to open the URL on each device (including accepting the certificate if needed), passcode entry, what to tap, and known limits.

## Demo checks

- [ ] From a fresh clone, the README steps get both devices into a round.
- [ ] The microphone prompt appears on both devices (proves the page is a secure context).

## Later (deferred)

Hosted HTTPS deployment, TURN, protected grown-up access instead of a CLI passcode, retention/cleanup for real use, and broader device and network testing. Real-child use stays blocked by [privacy-and-safety.md](../privacy-and-safety.md).
