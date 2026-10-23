# Lone Smart Room 2.0 — development baseline

This is an isolated development copy. Product/runtime versions remain Android and
Electron 1.4.0 and Python agent 1.5.0. No new control, telemetry, AI, or network
integration is implemented. Existing functional source files are byte-preserved.

## Layout

- `apps/android`: functional Kotlin/WebView Android source, working build toolchain.
- `apps/windows-ui`: Electron 1.4 interface; exact direct dependency versions + npm lock.
- `agent/windows`: unchanged real Windows agent 1.5 and its mocked-executor tests.
- `contracts`: future protocol boundary; no implementation.
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
.\scripts\test-safe.ps1
.\scripts\android-build.ps1
.\scripts\test-android-packet.ps1
.\scripts\android-build.ps1 -Tasks @('lintDebug')
.\scripts\windows-build.ps1
python -B scripts/verify-preservation.py
```

Android script accepts `-JavaHome`, `-SdkRoot`, and `-Tasks`. Gradle 8.11.1 wrapper
is committed; AGP is 8.10.1, Kotlin 2.0.21. Dependency downloads require network.
The default task assembles the APK; lint is a separate check that currently fails
on an inherited API-26 style issue, documented in `docs/VALIDATION.md`. It is not
disabled or suppressed. Gradle artifact checksums are committed in
`apps/android/gradle/verification-metadata.xml`.
The Windows build uses `npm ci` and does not install or launch the generated app.
Application dependencies are unchanged; exact baseline versions were selected
from the original ranges, without an upgrade/security-remediation campaign.
The Windows helper verifies the vendor bundle checksum and extracts Windows tools
only, avoiding macOS symlinks without requiring Developer Mode or admin privileges.
The npm lock also pins a transitive Git dependency to its commit; npm warns that
this dependency does not carry the usual registry integrity field.

Outputs: Android `apps/android/app/build/outputs/apk/debug/`; Windows
`apps/windows-ui/dist/`. Recovery files and generated binaries stay outside Git.

Builds are repeatable from pinned inputs, not claimed byte-for-byte deterministic:
timestamps, packaging tools, caches and local debug signing may affect outputs.
The new debug signing key is isolated in `.cache/android/`. Do NOT install its APK
over the Samsung app until signing compatibility is verified. Do NOT uninstall,
clear data, alter application ID, WebView origin, or WoL storage keys.

## Safety and recovery

Do not run the agent, firewall/autostart installers, key-display script, or real
energy actions during automated verification. The existing agent test binds only
to loopback on an ephemeral port and injects an executor that records actions.
No firewall, registry, existing app, or device is changed by that test.

Existing defaults in the agent and its deployment scripts remain historical LAN
configuration; they are not applied here. Security limitations are documented in
`docs/ARCHITECTURE.md`. Android cleartext traffic remains disabled.

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
