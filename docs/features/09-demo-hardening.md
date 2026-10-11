# 09 - Demo setup

Status: **D1 built (`npm run demo`); D4 not started** - steps in the [implementation plan](../implementation-plan.md)
Dependencies: [08](08-round-integration.md)

## Demo version

The demo runs from a laptop on the same Wi-Fi as the iPad and iPhone. No hosting.

- **D1:** one command starts the API and serves the web app over HTTPS on the LAN (a self-signed or locally trusted certificate is fine), allows that origin on the room socket, and prints the URL and Room passcode. It reads `DEEPSEEK_API_KEY` from the shell for AI feedback; without it rounds use the neutral result.
  Built as `npm run demo` (`scripts/demo.mjs`): a self-signed certificate via `@vitejs/plugin-basic-ssl`, `ALLOWED_ORIGINS` set to `https://<each LAN IPv4>:5173`, and `DEMO_HOST` to add an address the machine cannot see itself. On Windows WSL in NAT mode that is the Windows Wi-Fi address, which also needs a Windows port forward to WSL (or WSL mirrored networking).
- **D4:** a short README section: start command, how to open the URL on each device (including accepting the certificate if needed), passcode entry, what to tap, and known limits.

## Demo checks

- [ ] From a fresh clone, the README steps get both devices into a round.
- [ ] The microphone prompt appears on both devices (proves the page is a secure context).

## Later (deferred)

Hosted HTTPS deployment, TURN, protected grown-up access instead of a CLI passcode, retention/cleanup for real use, and broader device and network testing. Real-child use stays blocked by [privacy-and-safety.md](../privacy-and-safety.md).
