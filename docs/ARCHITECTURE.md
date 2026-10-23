# Development boundary

Historical stage-0/1 design below. Implemented stage-2 architecture, activation
gates and remaining risks are documented in STAGE2.md and the v2 wire contract.

Current modules: `apps/android` (Kotlin/WebView), `apps/windows-ui` (Electron),
`agent/windows` (Python stdlib agent 1.5). Existing runtime sources are preserved.

Future agent boundaries: transport/API, security/pairing, capability dispatch,
Windows actions, telemetry providers, and integration adapters. Extract the existing
executors with regression tests before replacing transport. SignalRGB, Home Assistant
and NEX remain future adapters. No implementation is included in this baseline.

Keep the black/graphite/red interface and the three existing tabs: Controles,
Monitoramento PC, Gamer Launcher. Never report simulated readings as real telemetry.

WoL remains an independent Kotlin LAN emitter. Keep application ID, WebView origin,
storage keys, native bridge and callback unchanged. An Android update must use a
compatible signing identity and preserve data; no device install is part of setup.

Known agent limitations: HTTP without transport encryption or signed responses,
shared file-based secret, in-memory replay cache, no per-device revocation,
hardcoded network defaults/firewall script, and no explicit request timeout/rate limit.
Do not run installation, firewall, key-display, autostart or energy scripts in setup.

Next: define TLS/server identity and device pairing; keep credentials out of the
renderer; add a native Kotlin client; integrate authenticated presence first; then
test existing allowlisted actions in a separately authorized live session.
