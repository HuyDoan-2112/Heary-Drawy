# Heary Drawy - approved UI design (draft v1, 2026-10-10)

Kenny approved these screens as the current UI direction. They are a visual reference for building the real app, not production code. Build the screens in the app's own stack (React + TypeScript per `docs/architecture.md`) and match the look; do not add extra details.

## Folders

| Folder | What it is |
| --- | --- |
| `screens/` | PNG screenshot of every screen. **Start here.** |
| `assets/drawy/` | Mascot Drawy (a lory parrot) as SVG, 7 poses. Ready to use in the app. |
| `assets/avatars/` | The 10 pickable characters as SVG. Ready to use. |
| `design/` | Source files from the Claude Design canvas (`*.dc.html` + `canvas.json`). They need the Claude Design runtime (`support.js`), so they will not open as normal web pages. Read them for exact sizes, colors and copy. |

## Screen flow

| # | Screenshot | Design file | Purpose |
| --- | --- | --- | --- |
| 1 | `01-pick-character.png` | `Main.dc.html` | Pick 1 of 10 characters (an avatar already picked by someone else shows a Picked badge). Optional real "My name" input. Grown-ups button. |
| 2 | `02-turn-on-mic.png` | `02b-Mic.dc.html` | Ask for microphone permission; a grown-up taps Allow. |
| 3 | `03-pick-mode.png` | `02c-Mode.dc.html` | Normal (default). Advanced button is visible but unavailable for now; advanced content is designed later. |
| 4 | `04-meet-teammate.png` | `02-Team.dc.html` | "You and Kiwi are a team!" then Let's play. |
| 5 | `05a`-`05e` | `P1`-`P4` | One round. A role intro ("You talk!" / "You draw!") shows for about 3 s, then fades into the play screen. No separate preparation step. |
| 6 | `06-drawy-checking.png` | `06b-Checking.dc.html` | Drawy looks at the drawing while the AI scores. |
| 7 | `07-result.png` | `07-Result.dc.html` | Team result: 1-3 stars when scoring succeeds, or friendly neutral result when scoring is unavailable; Photo vs drawing, Drawy says 2 sentences, sticker earned, Play again (both children ready, then roles swap) or Done. |
| - | `08-parents-phone.png` | `08-Grownups-Gate.dc.html`, then `08-Grownups.dc.html` | Parents-only area on a phone behind a grown-up gate (no teacher features). Sample data. |
| - | `00-drawy-mascot.png` | `00-Drawy.dc.html` | Mascot sheet. |

Play screens are portrait. iPad frame 820 x 1180, iPhone frame 390 x 844.

### Speaker (describer) play screen
- Top bar: music on/off button, role chip ("You talk"), time-left bar.
- "Photo" card with the secret object; the child can rotate it. In the design the 3D apple is a flat stand-in; the real app should use a 3D model (e.g. model-viewer + GLB).
- "Kiwi" panel: the drawer's canvas, live and read-only, in a dark frame with a red live dot so it looks like a shared screen. Green bars show when Kiwi is talking.
- Big "Hold to talk" button. Push-to-talk, live audio, both children may talk at the same time.

### Drawer play screen
- Same top bar ("You draw").
- Strip showing when the speaker is talking (no replay button: replay is not in the plan).
- Canvas, 6 colors, undo, clear (iPad only, must ask before clearing).
- "Hold to talk" and "Done!".

## Feedback rules (decided)
- Children see only 1-3 stars (minimum 1) and 2 sentences from Drawy: one specific praise, one guiding question that points at the weakest area without giving the answer. Use a pre-written sentence bank, not free AI text.
- Detailed category scores (details given, did not say the name, partner asked, answers helped, drawing matched) are for parents only. Speech clarity is never scored.

## Design tokens

| Token | Value |
| --- | --- |
| Background | `#D9F0FF`, hills `#C6EED8` / `#A6E0C0`, white clouds |
| Ink (text, outlines) | `#1B2B4B`, outlines 4-6 px, "sticker" shadow `0 8px 0 #1B2B4B` |
| Coral (talk, mic) | `#FF6F59` |
| Sun (selected, stars) | `#FFC83D` |
| Mint (go / done) | `#2EC4A0` |
| Grape (draw, music) | `#6C4DF6` |
| Fonts | Fredoka (children's screens), Nunito (parents' text) |
| Touch targets | 72 px+ on iPad, 46 px+ on iPhone |

## Mascot: Drawy the Lory
A small lory parrot (parrots copy words = talking and listening) holding a crayon (drawing). Pose per screen: curious (pick character), listen (mic), talk (role intro, mode), cheer (team, result), search with magnifier (checking), proud (drawer intro). Drawy is not shown on the play screens so children can focus. Drawy should never look sad or pressure the child.

## Still to design
Reconnecting / partner left, 3D load failure fallback and reset/zoom, Play again disconnect timeout/help, time-up behaviour, Advanced mode content.
