# Baseline validation — 2026-10-23

## Preservation

- 86 copy records verified using SHA-256; all recorded originals remain unchanged.
- Runtime Kotlin, JavaScript, HTML, CSS, XML, Electron bridges and Python files
  match the audited source bytes. Android Gradle/build/signing configuration is
  the only Android preparation change. Electron manifest pins dependencies.
- Recovery contains the Electron 1.4 sources, Android 1.4 sources, working Android
  sources, agent 1.5 sources, five original distribution ZIPs, and the existing
  Android debug APK. The two agent ZIPs are byte-identical and both retained.
- Runtime `agent_config.json`, keys, local.properties, IDE state, caches and user
  device data were not imported. No Samsung install/uninstall/data-clear was run.

## Build results

| Check | Result |
| --- | --- |
| Android assembleDebug | PASS; com.lonesmartroom.app, versionCode 14, versionName 1.4.0, minSdk 26, targetSdk 35 |
| Android artifact signing | Both recovered and generated APK signatures verify; signers DIFFER |
| Android lintDebug | FAIL: 1 inherited error, 4 warnings; not disabled or suppressed |
| Windows NSIS x64 | PASS; generated installer, not executed |
| Windows portable x64 | PASS; generated portable executable, not executed |
| Windows Authenticode | Unsigned development artifacts |
| Existing Python agent tests | PASS; loopback HTTP + injected executor, no actual OS actions |
| Baseline regression suite | PASS: 4 tests |
| Production Kotlin WoL JVM tests | PASS: packet layout, normalization, invalid input rejection; no UDP sent |
| JavaScript/CommonJS syntax | PASS: app.js, main.cjs, preload.cjs |
| Preservation verification | PASS: originals and recovery copies unchanged |
| Git exclusions | PASS: recovery, caches, tool binaries, keys, .env, local.properties, runtime config, dependencies and outputs ignored |

The new APK is an isolated build artifact, NOT an authorized update for the
Samsung. Its debug signer differs from the recovered APK. Establish the actual
installed app's signing identity and compatible original key before any update.
Do not uninstall the installed app to bypass a signing mismatch.

Reproducibility means pinned tool/dependency inputs and repeatable build commands;
bit-for-bit identical packages are not claimed. Gradle wrapper/distribution and
artifact SHA-256 metadata, exact npm direct versions and package-lock are recorded.
Gradle dependency checksums are a recorded first-use baseline from the resolved
artifacts, not an independent security endorsement of every dependency.

## Open issues (not silently fixed)

1. Android lint: `android:windowLightNavigationBar` in values/styles.xml requires
   API 27 while minSdk is 26. A future fix should scope the item to values-v27;
   no style/runtime source was changed in this preservation task.
2. Other lint warnings concern Gradle age, activity orientation, enabled WebView
   JavaScript, and Android data-extraction rules. See android-lint-baseline.txt.
3. npm audit reports 14 vulnerable dependency entries: 13 high and 1 critical.
   This is not a count of independent CVEs. The critical entry is transitive tar;
   Electron and electron-builder also have high-severity advisories. Complete
   report: dependency-audit.json. Do not treat this baseline as release-ready.
4. npm reports a transitive Git dependency (@electron/node-gyp) pinned by commit
   but without the usual registry integrity field. Preserve that limitation in
   supply-chain review. No automatic audit fix or unreviewed upgrade was run.
5. Agent 1.5 security limitations remain as documented in ARCHITECTURE.md. The
   API was not started on the LAN; firewall, registry and autostart were not changed.
6. No physical WoL, live energy-action, UI interaction, device update, performance,
   or hardware-sensor validation was performed. User-reported existing WoL after
   suspension and shutdown remains the operational reference.
7. Recovery is local to the same disk; an external trusted backup is still needed
   for disk-loss recovery. No repository remote or publishing was configured.

## Environment repairs made only in the development copy

- Added complete Gradle 8.11.1 wrapper, official checksum pins and artifact
  verification metadata; retained AGP 8.10.1 / Kotlin 2.0.21 from working Android.
- Fixed Android build tools to 35.0.0 and isolated debug signing and preferences.
- Installed portable MinGit locally, with official archive SHA-256 validation.
- Resolved npm lock with Electron 38.0.0 / electron-builder 26.0.0, the exact
  baseline versions selected from the original ranges, not a version upgrade.
- Extracted only Windows tools from the checksum-pinned winCodeSign bundle to
  avoid macOS symbolic-link privilege requirements. No Windows policy was changed.
- Kept dependency caches and build outputs under the 2.0 workspace.

## Next implementation gate

Review lint and dependency remediation before release. Then implement an explicit
authenticated transport/pairing contract, preserve HMAC v1 behavior during migration,
and connect a native Kotlin client for presence first. Prove credential rejection,
revocation, server identity, replay protection across agent restarts and preservation
of WoL settings before adding any real remote action to the UI.
