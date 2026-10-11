# Heary Drawy: iPad and iPhone platform research

> Background platform research, not device validation or the current build plan. See [current architecture](../architecture.md), [product](../product.md), and [device acceptance](../testing.md). Older mechanics/stack candidates below may be superseded.

Research checked: 2026-10-10  
Status: web-first demo selected; native options retained for future reference; not device-tested  
Related report: [Technical research](technical-research.md)

## Executive finding

An iPad and an iPhone can be the two player devices. We do not need two computers, an App Store launch, or a camera inside the game. The current audio direction is live push-to-talk over WebRTC, replacing the earlier recording-and-upload delivery.

The important distinction is **an application experience** versus **a signed native application**:

- A Home Screen web app runs through the browser engine with an app icon and app-like presentation.
- A Capacitor app packages a web interface in a native app with access to native plugins.
- React Native with Expo uses native UI and device APIs; Expo Go can preview compatible projects before we build our own signed app.

**Confirmed decision:** build the initial demo as a responsive website over HTTPS, opened in Safari on the iPad and iPhone. Home Screen installation is optional, not required. Native iOS packaging, Expo, Capacitor, TestFlight, and App Store distribution are deferred. Device audio, drawing, and 3D still need actual hardware tests.

No app has been built or run on the user's devices. The earlier React / Next.js / Supabase stack remains a candidate, not an approved decision.

## 1. Confirmed scope

- Available hardware: one iPad and one iPhone; exact models and OS versions are not yet known.
- Current platform: responsive website in Safari over HTTPS. No Mac or Apple Developer Program membership is needed for this path.
- Two controlled player devices and one pair for the first demo.
- Custom application-level rate limiting remains deferred for this controlled demo.
- Role authorization, private media, hidden-information rules, and bounded turns remain necessary.
- Roles swap every round, so both devices must support live speaking/listening and drawing.
- The interactive 3D object reward appears after every round's feedback, before Continue and the role swap.
- Live audio only during bounded push-to-talk turns; no always-open call, webcam, video, public matchmaking, or free chat.

A larger tablet display is desirable for drawing, but the iPhone cannot be a permanently voice-only device without changing the role-swap requirement.

## 2. Platform options

| Option | What the user opens | Mac needed for the initial demo? | Paid Apple membership for initial demo? | Main tradeoff |
| --- | --- | --- | --- | --- |
| Web / PWA | Safari URL or Home Screen web app | No | No | Browser lifecycle and audio behavior must be tested |
| Capacitor | Our own signed native app containing a web UI | For the normal local iOS build/debug path; cloud builds are possible | Not for limited personal-device testing through Xcode; needed for normal TestFlight/App Store distribution | Reuses web drawing/3D, but adds signing and WebView/plugin integration |
| React Native + Expo Go | Project opened inside the Expo Go app | No for compatible physical-device preview | No for Expo Go preview | Good native prototype path, but not our own standalone app and limited to bundled native modules |
| React Native + own development/release build | Our own signed app | Local builds/debugging use Mac + Xcode; EAS can build in the cloud | Normally required for EAS-signed physical-device builds and TestFlight; free local Xcode testing is an alternative | Native app identity and custom modules, with provisioning/build setup |

A cloud build can remove the need to own the build machine. It does not remove Apple signing requirements or the value of native debugging tools.

Sources: [Apple developer account](https://developer.apple.com/help/account/basics/about-your-developer-account), [Capacitor environment](https://capacitorjs.com/docs/getting-started/environment-setup), [Expo development builds](https://docs.expo.dev/develop/development-builds/introduction/), [Expo EAS setup](https://docs.expo.dev/build/setup/).

## 3. Web app / PWA on iPad and iPhone

### What it means

Deploy a responsive application over HTTPS, open it in Safari, and add it to the Home Screen. Use a web app manifest, appropriate icons, and standalone presentation. A service worker may cache the app shell and selected non-secret assets, but does not make cloud AI or multiplayer work offline.

Apple documents opening websites as web apps and adding them to the Home Screen. Exact menu labels depend on the OS version.

Sources: [Apple iPhone guide](https://support.apple.com/guide/iphone/bookmark-a-website-iph42ab2f3a7/ios), [Apple iPad web-app guide](https://support.apple.com/guide/ipad/open-as-web-app-ipad8f1f7a29/ipados).

### Fit for Heary Drawy

- Live microphone: `getUserMedia` and WebRTC, with authorized push-to-talk transmission and original voice reaching the partner immediately.
- Drawing: browser canvas and Pointer Events for finger input; pencil input is optional, not required.
- Incoming audio: unlock playback through deliberate user interaction where Safari requires it. Replay is not required by the live design; adding it would require a separate buffering/retention decision.
- 3D reward: a reviewed GLB/glTF asset in a viewer such as model-viewer, without AR.
- Pair state: authenticated HTTPS requests plus the selected realtime mechanism.

WebRTC documents real-time audio transport, signaling, and ICE connectivity. Test the actual Safari versions, audio permissions, STUN/TURN route, and reconnection behavior. WebKit's MediaRecorder article is historical evidence of capture support, not a current compatibility matrix; recording formats matter only if we choose disclosed temporary buffering for AI or optional replay.

### Critical setup detail

A phone opening `http://192.168.x.x:3000` on the development computer is not the same as the computer opening localhost. Microphone access requires a secure context. Use an HTTPS deployment or a properly secured development tunnel with appropriate access controls.

The local Lavish address `127.0.0.1` is also not a remotely accessible game deployment. On an iPhone, it points to the iPhone itself, not this development environment.

### Limits

Test Safari and Home Screen mode separately. Do not assume uninterrupted live audio or sockets after screen lock, persistent permissions across installations, or offline multiplayer. Mute transmission and pause on backgrounding, cancellation, or connection loss. Recover from app suspension by reloading authoritative round state.

Sources: [WebKit MediaRecorder](https://webkit.org/blog/11353/mediarecorder-api/), [MDN microphone requirements](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia), [MDN Pointer Events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events), [model-viewer browser support](https://modelviewer.dev/).

## 4. Capacitor: web interface inside a native app

Capacitor uses WKWebView on iOS and supports native Swift/Objective-C integration. Its normal local iOS workflow uses macOS and Xcode. Current version requirements should be checked when selecting a Capacitor release; do not assume an old iPad supports every current toolchain target.

This is a plausible path if we first establish a strong web UI and later want a signed app without rewriting the canvas and 3D viewer.

Important qualifications:

- Next.js server routes do not execute inside the native bundle. Keep server functionality deployed separately; design the client so it can be packaged appropriately.
- Microphone permissions and WebView capture must be configured and tested. Browser behavior is not automatically identical inside a wrapper.
- Use a maintained native recording plugin if needed, after checking its support, privacy behavior, and audio export format.
- A wrapper is not a guarantee of App Store approval. Apple's minimum-functionality guideline expects more than an inadequately repackaged website.

Sources: [Capacitor iOS](https://capacitorjs.com/docs/ios), [Capacitor environment setup](https://capacitorjs.com/docs/getting-started/environment-setup), [Apple review guideline 4.2](https://developer.apple.com/app-store/review/guidelines/).

## 5. React Native + Expo: future native option, not demo scope

### Why it fits the application direction

React Native provides native views and interaction, while Expo supplies supported device modules and build workflows. The backend can still use Supabase or another service; changing the client does not require changing the game's server-side rules.

A candidate client stack:

- React Native + Expo + TypeScript for screens and navigation.
- `expo-audio` for recording and original-clip playback.
- React Native Skia plus an appropriate gesture layer for freehand drawing and image export.
- A small 3D viewer using `expo-gl` and compatible rendering libraries, or an isolated WebView containing a reviewed web viewer.

These are candidates, not a tested integration. Expo documents audio, Skia, GLView, and WebView as included in Expo Go for the documented SDK. Exact Expo Go / SDK compatibility must be checked before installing dependencies.

### Demo through Expo Go

1. Install a compatible Expo Go version on both devices.
2. Start the development server on the development computer.
3. Open the project on each device using the development URL / QR code.
4. Prefer a reachable local network; use Expo's tunnel option if routing prevents access.
5. Follow the current account sign-in requirements in Expo's physical-device instructions.
6. Give each device its own player session and join the same game room.

A QR used by an adult during development setup is distinct from the child's three-shape room join. The game itself still requests no camera access.

Expo Go is a preview container, not a branded standalone Heary Drawy installation. It cannot load arbitrary additional native modules. It should not be treated as the long-term classroom distribution mechanism.

### Native audio details

Set the microphone permission explanation, request permission explicitly, and configure the audio mode for recording and playback. Test silent mode, speaker volume, headphone/Bluetooth routing, interruptions, and denied permission.

Stop recording on backgrounding and cancellation. We do not need background microphone access for this turn-based game. Do not enable background recording merely because the library supports it.

Native recordings may initially live in the app's cache. Upload safely and keep only what is needed for the authorized round; do not rely on cache files surviving device storage pressure.

Sources: [Expo start developing](https://docs.expo.dev/get-started/start-developing/), [expo-audio](https://docs.expo.dev/versions/latest/sdk/audio/), [React Native Skia in Expo](https://docs.expo.dev/versions/latest/sdk/skia/), [GLView](https://docs.expo.dev/versions/latest/sdk/gl-view/), [WebView](https://docs.expo.dev/versions/latest/sdk/webview/).

## 6. Apple's build and installation rules, in plain language

### Do we need a Mac?

- HTTPS web app: no.
- Expo Go preview on actual devices: no local native compilation required.
- Normal local iOS native build, simulator, and native debugging: Mac + Xcode.
- Expo EAS cloud build: uses hosted build infrastructure, so we need not own a Mac for the build itself; signing and distribution still apply.

### Do we need to pay Apple?

Apple advertises its Developer Program at $99 annually; local currency, eligibility, and potential fee waivers can vary.

We do not need paid membership just to open a web app or preview a compatible project in Expo Go.

Apple also permits limited personal-device testing through Xcode with a free Personal Team. Its current documentation states that provisioning expires after seven days and restricts the number of registered devices/apps. This requires local Xcode access and periodic rebuilding/reinstallation; it is not TestFlight distribution.

Normal TestFlight / App Store distribution requires the relevant Developer Program membership and signing setup. EAS's free plan is separate from Apple's membership: a free cloud-build tier does not waive Apple's distribution requirements.

### Can we use TestFlight?

Yes, after preparing and signing a suitable build and setting up App Store Connect. External testing may require beta review. Do not assume a public App Store release is required for the two-device demo, or that TestFlight approval will be immediate.

Sources: [Apple Developer Program](https://developer.apple.com/programs/), [Apple Personal Team limits](https://developer.apple.com/help/account/basics/about-your-developer-account), [TestFlight](https://developer.apple.com/testflight/), [Expo EAS setup](https://docs.expo.dev/build/setup/), [Expo physical-device builds](https://docs.expo.dev/tutorial/eas/ios-development-build-for-devices/).

## 7. Tablet-first does not mean tablet-only

Design the game for touch first:

- Large, widely spaced controls and minimal reading.
- A large drawing area, undo, clear confirmation, and a simple color palette.
- Avoid accidental page scrolling while drawing; for web, scope touch handling to the canvas rather than disabling scrolling everywhere.
- Map input coordinates correctly after layout, orientation, and safe-area changes.
- Preserve the drawing across orientation changes and reconnects.
- Respect iPhone safe areas, iPad resizing/multitasking, and portrait/landscape layouts.
- Support finger drawing. Apple Pencil should be optional and device-compatible, not a prerequisite.
- Support both roles on both screens. The phone's smaller drawing area is a real demo constraint.

Do not claim pixel-perfect or accessible device behavior until the actual iPad and iPhone have been tested.

## 8. 3D reward on iOS

The timing is confirmed: **after every round's feedback**.

Use curated, licensed GLB/glTF models. For a web/Capacitor client, model-viewer is a candidate. It is a web component, not a React Native native view. For React Native, evaluate a compatible GL renderer or an isolated WebView; these require separate interaction, asset-loading, and performance tests.

Requirements remain:

- Rotate, zoom, reset, and a clear Continue action.
- No AR or camera permissions.
- Asset identity withheld from the Drawer until the authorized reveal.
- Static-image fallback when 3D loading/rendering fails.
- Dispose inactive rendering resources between rounds and use modest assets appropriate to the hardware.
- No automatic negative feedback for a viewer failure.
- The pretty 3D model must not be a drawing-quality standard.

No 3D viewer was run on the user's hardware during this research.

## 9. Additional App Store and child-data constraints

The privacy release gate in the technical report applies regardless of platform. A native app does not make recordings anonymous or change provider eligibility.

Apple's App Review Guidelines add relevant requirements:

- Section 1.3: Kids Category apps may not send personally identifiable information or device information to third parties; external links and purchases need a parental gate, and third-party analytics/advertising are restricted.
- Section 5.1.2: disclose sharing of personal data with third parties, including third-party AI, and obtain explicit permission.
- Section 2.5.14: obtain consent and clearly indicate recording activity.
- Section 4.2: provide adequate app functionality, not merely an inadequate website wrapper.

A cloud transcription pipeline handling identifiable child voice needs explicit review against the intended distribution category and data flow. Provider ZDR alone does not establish App Store compliance. Choosing another category is not a way to remove child privacy obligations.

For the prototype, use adults and synthetic examples. Do not assume that a parent approving the microphone prompt is the complete privacy/consent process.

Source: [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/).

## 10. Direct validation on the available devices

Before building the complete game, validate these on the actual iPad and iPhone:

1. Identify model names, OS versions, and whether a Mac is available.
2. Use the selected HTTPS website in Safari. Test Home Screen mode separately only if that optional feature is included.
3. Connect both devices to an authorized WebRTC session with adults testing. Hold to talk and verify that the partner hears speech immediately; release and verify transmission stops, in both directions.
4. Confirm permission denial, cancellation, screen lock, phone-call interruption, and reconnect behavior.
5. Draw with a finger on both devices; test undo and image export.
6. Display one licensed 3D model; test rotation, zoom, reset, and fallback.
7. Run a two-device round and swap roles, ensuring that each secret stays hidden until results.
8. Repeat in the intended installation mode; Safari success alone does not certify Home Screen or wrapped-native behavior.

Internet is still required for cloud AI and server-coordinated play unless a separate offline design is built. Network isolation at a demo venue can block local development servers; have a tested connection route, not an assumed one.

## 11. Work that can proceed independently

Two focused work tracks can proceed once their contract is agreed:

- **Device track:** live push-to-talk capture/playback, Safari audio unlock, drawing/export, 3D viewer, touch layout, and installation.
- **Backend/AI track:** authenticated game and media-room state, signaling/TURN or a managed transport, speaking permissions, bounded turns, completed-turn transcription, feature evidence, and deterministic feedback.

Agree on round states, media formats, authenticated endpoints, and feature-result schemas first. Neither track should fabricate a working integration. Finish with the actual end-to-end round on both devices.

This research used parallel source retrieval, not separately spawned research agents.

## 12. Remaining device checks and future scope

The platform decision is resolved for the demo: a responsive HTTPS website in Safari.

Still to check:

1. Exact iPad and iPhone models and OS versions.
2. Microphone permission, live voice delay, release/cancellation muting, audio routing/echo, drawing, and 3D performance on both devices.
3. Whether optional Home Screen installation adds value to the demo.
4. Whether later classroom support should include Android tablets and additional browsers.

Mac access and Apple signing become relevant only if native packaging is revisited. Keep this comparison for that future decision; do not build a native client alongside the web demo without a concrete need.

## Sources and verification limits

Primary sources checked on 2026-10-10:

- [Apple iPhone Home Screen website instructions](https://support.apple.com/guide/iphone/bookmark-a-website-iph42ab2f3a7/ios).
- [Apple iPad Open as Web App](https://support.apple.com/guide/ipad/open-as-web-app-ipad8f1f7a29/ipados).
- [Apple Developer Program](https://developer.apple.com/programs/).
- [Apple developer account / Personal Team](https://developer.apple.com/help/account/basics/about-your-developer-account).
- [Apple TestFlight](https://developer.apple.com/testflight/).
- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/).
- [WebKit MediaRecorder and WKWebView capture](https://webkit.org/blog/11353/mediarecorder-api/), published in 2020; historical, not a current compatibility matrix.
- [Capacitor iOS](https://capacitorjs.com/docs/ios) and [environment requirements](https://capacitorjs.com/docs/getting-started/environment-setup).
- [Expo development preview](https://docs.expo.dev/get-started/start-developing/) and [development builds](https://docs.expo.dev/develop/development-builds/introduction/).
- [Expo EAS setup](https://docs.expo.dev/build/setup/) and [physical-device iOS builds](https://docs.expo.dev/tutorial/eas/ios-development-build-for-devices/).
- [expo-audio](https://docs.expo.dev/versions/latest/sdk/audio/), [Skia](https://docs.expo.dev/versions/latest/sdk/skia/), [GLView](https://docs.expo.dev/versions/latest/sdk/gl-view/), and [WebView](https://docs.expo.dev/versions/latest/sdk/webview/).
- [MDN microphone secure-context requirements](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) and [Pointer Events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events).
- [MDN WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API) and [WebRTC peer connections, signaling, and ICE](https://webrtc.org/getting-started/peer-connections).
- [model-viewer](https://modelviewer.dev/).

This report verifies published capabilities and policy constraints. It does not certify compatibility with unknown hardware/OS versions, App Store approval, legal compliance, drawing performance, microphone quality, or a working native integration.
