# Lone Smart Room 2.0 — secure pairing and status

This is an isolated development copy. Stage 2 adds status-only HTTPS pairing in
Python/Kotlin. Product package versions remain 1.4.0 pending the signing/update
plan; the legacy agent 1.5 remains intact. Electron runtime is now 45.0.0 and
electron-builder 26.15.3 after security remediation. WoL, its bridge/storage contract
and legacy action implementations are preserved. No new power/AI/telemetry command
is enabled. Current report: `docs/STAGE2.md`; stage-0/1 reports are historical.

## Layout

- `apps/android`: functional Kotlin/WebView Android source, working build toolchain.
- `apps/windows-ui`: Electron 1.4 interface; exact direct dependency versions + npm lock.
- `agent/windows`: unchanged real Windows agent 1.5 and its mocked-executor tests.
- `agent/windows/secure_*.py`: HTTPS status service, DPAPI, pairing and local management.
- `contracts`: implemented v2 status/pairing contract and legacy boundary.
- `scripts`: repeatable build and safe-test commands.
- `tests`: source-integrity, interface, identity, security, and storage regression guards.
- `docs`: baseline inventory, toolchain checksums, architecture and validation results.
- `recovery` (ignored): source snapshots, original ZIPs, existing Android APK, manifest.
- `.tools` / `.cache` (ignored): portable Git, dependencies, local build/signing state.

## Build and test (PowerShell, from this directory)

Prerequisites: Node 22.16.x / npm 10.9.x, Python 3.13.3, JDK 21 (Java/Kotlin bytecode
target remains 17), Android SDK platform 35 and build tools 35.0.0. Tested versions
and Gradle checksum pins are in `docs/toolchain.json`. No global tool installation
or PATH mutation is required by these scripts.

```powershell
.\scripts\prepare-agent.ps1
.\scripts\android-build.ps1
.\scripts\test-safe.ps1
.\scripts\test-android-packet.ps1
.\scripts\android-build.ps1 -Tasks @('lintDebug')
.\scripts\windows-build.ps1
.\scripts\test-electron.ps1
python -B scripts/verify-preservation.py
```

Android script accepts `-JavaHome`, `-SdkRoot`, and `-Tasks`. Gradle 8.11.1 wrapper
is committed; AGP is 8.10.1, Kotlin 2.0.21. Dependency downloads require network.
The default task assembles the APK; lint is a separate check. The inherited API-26
style error was fixed in values-v27 without changing the WoL emitter or disabling
lint. Gradle artifact checksums are committed in
`apps/android/gradle/verification-metadata.xml`.
The Windows build uses `npm ci` and does not install or launch the generated app.
Current exact npm versions remediate the recorded advisories; see the stage-2 audit.
The Windows helper verifies the vendor bundle checksum and extracts Windows tools
only, avoiding macOS symlinks without requiring Developer Mode or admin privileges.

Outputs: Android `apps/android/app/build/outputs/apk/debug/`; Windows
`apps/windows-ui/dist/`. Recovery files and generated binaries stay outside Git.

Builds are repeatable from pinned inputs, not claimed byte-for-byte deterministic:
timestamps, packaging tools, caches and local debug signing may affect outputs.
The new debug signing key is isolated in `.cache/android/`. Do NOT install its APK
over the Samsung app until signing compatibility is verified. Do NOT uninstall,
clear data, alter application ID, WebView origin, or WoL storage keys.

An opt-in original-signed 2.0 candidate (versionCode 15) was prepared and verified.
See `docs/ANDROID-COMPATIBLE-APK.md` for its exact path/hash, offline preparation
command, tests and recovery plan. Ordinary builds still use the isolated key.
After explicit authorization, version 2.0.0-dev.1 / 15 is installed on Samsung;
WoL settings survived, and real Wi-Fi HTTPS pairing/status and credential reload
passed. See `docs/SAMSUNG-INSTALLATION.md`. A subsequent single authorized sleep
test also passed: the user confirmed wake via the Android app, and fresh Android
HTTPS status passed after resume. Windows reported an Unknown wake source; see
`docs/SUSPEND-WOL-TEST.md`. Additional power actions and new APK installations
require their own authorization. The inherited visual header saying 1.4 is pending.

## Safety and recovery

App-control cycle 1 is implemented and tested with injected executors only.
Steam/CS2 require separate local per-device grants and native Android confirmation.
See `docs/APP-CONTROL-CYCLE1.md` and `contracts/app-launch-v2.md` for the v16 build,
security limits and proposed physical test. No new Samsung install, real app launch
or production permission grant was performed. Power commands remain blocked.

Do not run the legacy agent, legacy firewall/autostart installers, key-display
script, or real energy actions during automated verification. Agent tests bind only
to loopback on an ephemeral port and injects an executor that records actions.
No firewall, registry, existing app, or device is changed by that test.

Existing legacy deployment scripts remain historical LAN configuration and were
not applied. The secure agent has a separate per-user startup entry, independently
of Electron, and refuses to listen before the configured interface is Private.
The subsequent authorized LAN activation added a narrowly scoped Private-profile
firewall rule; current activation evidence is in `docs/LAN-ACTIVATION.md`.
Android cleartext traffic remains disabled.
See `docs/STAGE2.md` for activation, revocation, signing and remaining physical tests.

`recovery/manifest.json` identifies originals and copied files with SHA-256 hashes.
`docs/baseline-inventory.json` is its shareable, path-independent inventory.
`recovery/lone-smart-room-baseline.bundle` preserves the initial Git history;
`recovery/baseline-commit.txt` identifies that commit. Verify a bundle with
`git bundle verify`, and restore it into a new directory with `git clone`.
The originals and recovery snapshots are not development targets. The local
recovery folder is not an off-device backup: copy it to trusted backup storage
before relying on it for disaster recovery. Do not publish recovery archives.

Use local Git branches/commits for all changes; no remote is configured. Secrets,
local.properties, runtime agent configuration, keys, outputs and caches are ignored.
Before any remote publishing, review both tracked files and Git history.
