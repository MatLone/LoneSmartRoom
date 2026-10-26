'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, '..'), app = path.join(root, 'apps/windows-ui');
const config = require(path.join(app, 'electron-builder.development.cjs'));
const pkg = require(path.join(app, 'package.json'));
const {staticUninstaller} = require('../scripts/nsis-static-uninstaller.cjs');
const {inside} = require('../scripts/build-windows-distribution.cjs');
let checks = 0;const check = (value, message) => {assert(value, message);checks++;};
async function main() {
  check(pkg.name === 'lone-smart-room' && pkg.productName === 'Lone Smart Room', 'Existing package identity');
  check(pkg.version === '2.0.0-dev.6' && config.appId === 'com.lone.smartroom', 'Existing version and appId');
  check(config.files === pkg.build.files, 'Existing explicit packaged-file list retained');
  check(config.publish === null && config.npmRebuild === false, 'No publication/dependency rebuild');
  check(config.win.target.every(t => t.arch.length === 1 && t.arch[0] === 'x64'), 'x64 artifacts only');
  check(config.win.requestedExecutionLevel === 'asInvoker', 'Application not elevated');
  for (const key of ['oneClick', 'perMachine', 'selectPerMachineByDefault', 'allowElevation', 'packElevateHelper', 'runAfterFinish', 'deleteAppDataOnUninstall', 'differentialPackage', 'createDesktopShortcut']) {
    check(config.nsis[key] === false, 'Conservative NSIS '+key);
  }
  check(config.nsis.allowToChangeInstallationDirectory === true, 'Assisted destination selection retained');
  check(config.portable.requestExecutionLevel === 'user' && config.portable.unpackDirName === false, 'Portable current user and temporary extraction');
  check(config.win.icon === pkg.build.win.icon && config.nsis.installerIcon === pkg.build.win.icon && config.nsis.uninstallerIcon === pkg.build.win.icon, 'Official icon for all wrappers');
  check(!config.files.includes('electron-builder.development.cjs') && !config.files.includes('build/**/*'), 'Build-only code excluded');
  const nsi = fs.readFileSync(config.nsis.include, 'utf8');
  check(/IfSilent loneSilentRejected loneInteractive/.test(nsi), 'Silent installation rejected');
  check(/StrCpy \$isForceCurrentInstall "1"/.test(nsi), 'Only current user install');
  check(/MB_DEFBUTTON2/.test(nsi) && /IDYES loneUpdateApproved/.test(nsi), 'Explicit update consent, default No');
  for (const hive of ['HKCU', 'HKLM']) for (const view of [32, 64]) check(nsi.includes(`loneCheckPrevious ${hive} ${view}`), 'Both registry views checked');
  check(!/\b(?:Exec|ExecWait|WriteRegStr|WriteRegDWORD|RMDir|Delete)\b/.test(nsi), 'Custom installer policy has no execution, registry writes or removals');
  check(inside(path.join(root, '.cache/artifacts/windows/test'), path.join(root, '.cache/artifacts/windows')), 'Output child accepted');
  check(!inside(path.join(root, 'apps/windows-ui/dist'), path.join(root, '.cache/artifacts/windows')), 'Legacy output rejected');
  const calls = [], defines = {}, target = {
    options: {}, outDir: path.join(root, '.cache/test-not-created'),
    computeFinalScript: async (script, installer, archs) => {calls.push(['script', installer, archs]);return script;},
    executeMakensis: async (d, c, script) => {check('BUILD_UNINSTALLER' in d, 'Generator compiled only');calls.push(['compile', script]);}
  };
  const deps = {templates: 'templates', readFile: async () => 'NSIS template', extract: async (input, output) => {calls.push(['static-extract', input, output]);}};
  const result = await staticUninstaller(target, defines, {}, path.join(target.outDir, 'Setup.exe'), 'header', ['x64'], deps);
  check(result.isCustomScript === false && result.script === 'NSIS template', 'Original installer template retained');
  check(!('BUILD_UNINSTALLER' in defines) && defines.UNINSTALLER_OUT_FILE.endsWith('__uninstaller.exe'), 'Final installer uses extracted uninstaller');
  check(calls.map(x => x[0]).join(',') === 'script,compile,static-extract', 'No process launch or signing fallback');
  await assert.rejects(staticUninstaller({...target, options: {script: 'other'}}, {}, {}, 'Setup.exe', '', [], deps));checks++;
  await assert.rejects(staticUninstaller(target, {}, {}, 'Setup.exe', '', [], {...deps, extract: async () => {throw Error('Invalid NSIS stream');}}));checks++;
  const source = fs.readFileSync(path.join(root, 'scripts/build-windows-distribution.cjs'), 'utf8');
  check(source.includes("versions.some(v => v !== '26.15.3')"), 'Builder version pinned');
  check(source.includes('Forbidden execution of a generated distribution artifact') && source.includes('Shell execution is forbidden'), 'Generated EXE/shell execution blocked');
  check(source.includes('if (fs.existsSync(output)) throw'), 'Previous artifacts never overwritten');
  check(source.includes('for (const name of environmentNames) delete process.env[name]'), 'Signing credentials removed only from child build environment');
  const main = fs.readFileSync(path.join(app, 'desktop-main.cjs'), 'utf8'), html = fs.readFileSync(path.join(app, 'index.html'), 'utf8');
  check(main.includes('contextIsolation: true') && main.includes('nodeIntegration: false') && main.includes('sandbox: true'), 'Runtime hardening retained');
  check(html.includes("connect-src 'none'") && !html.includes('src="agent-status.js"') && !html.includes('src="app-launch.js"'), 'No operational client');
  check(!/\b(?:setLoginItemSettings|setOpenAtLogin)\s*\(/.test(main), 'No autostart behavior added');
  check(main.includes('requestSingleInstanceLock') && pkg.build.files.includes('desktop-window.cjs'), 'Scoped Tray lifecycle packaged');
  console.log(`PASS: ${checks} distribution policy/static-uninstaller assertions; no applications or installers executed.`);
}
main().catch(error => {console.error(error.stack);process.exitCode = 1;});
