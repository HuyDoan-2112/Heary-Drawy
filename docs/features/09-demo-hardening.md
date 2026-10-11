# 09 - Device hardening and controlled demo release

Status: **not started**  
Dependencies: [08](08-round-integration.md), reviewed demo host/retention/deployment policy  
References: [testing](../testing.md), [privacy](../privacy-and-safety.md), [architecture](../architecture.md)

## Deliverable

A documented, stable adult-only two-device demo with reproducible setup, recovery/fallback checks, protected host access, and explicit known limits.

## Scope and ownership

Own cross-feature E2E/device acceptance and deployment configuration/run instructions. Coordinate shared dependency/configuration changes; do not replace feature modules casually.

- Configure HTTPS, correct browser/backend origins, persistent non-sleeping runtime, secrets, private Storage, and provider accounts only with deployment authorization.
- Resolve host access and demo retention/cleanup. Keep real-child/public launch gates separate.
- Exercise mic/playback unlock, Safari foreground/background, orientation, multitouch, canvas/3D memory, poor connectivity, TURN, restart, and expiry.
- Confirm clean fallback/retry paths and no secret/credential/raw-media logging.
- Record actual devices/OS, SDK/model versions, test scenarios, measured behavior, and honest limitations.

## Out of scope

Automatic public launch, native distribution, legal certification, clinical/learning-effect claims, or solving every future scaling concern.

## Acceptance

- [ ] Both devices pass applicable actual-device cases in the test strategy, both role directions.
- [ ] Disconnect/restart/provider-failure paths fail safely without stuck mics, duplicated results, or lost secret barriers.
- [ ] Host/detail access is protected; controlled participant-only assumptions are documented.
- [ ] Room/session/draft/transcript/result cleanup follows the reviewed policy, including deployment logs/backups.
- [ ] Setup, start/stop, recovery, and demonstration instructions work and contain no committed secrets.
- [ ] Unresolved malicious-client backend-crash cutoff is disclosed; broader child deployment remains gated.
- [ ] README and feature/plan status reflect evidence, not aspirations.

Deployment is not implied by documentation or code completion. Ask before provisioning or publishing.

Evidence: none yet.
