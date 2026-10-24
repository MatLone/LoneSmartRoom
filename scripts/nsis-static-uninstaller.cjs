'use strict';
// Build-only adapter: official electron-builder parser replaces execution of
// the intermediate uninstaller generator. No fallback to process execution.
const path = require('node:path');
async function staticUninstaller(target, defines, commands, installerPath, sharedHeader, archs, deps) {
  if (target.options.script) throw new Error('Custom NSIS scripts require separate review');
  const script = await deps.readFile(path.join(deps.templates, 'installer.nsi'), 'utf8');
  const uninstallerPath = path.join(target.outDir, `${path.basename(installerPath, 'exe')}__uninstaller.exe`);
  defines.BUILD_UNINSTALLER = null;
  defines.UNINSTALLER_OUT_FILE = uninstallerPath;
  await target.executeMakensis(defines, commands, sharedHeader + await target.computeFinalScript(script, false, archs));
  await deps.extract(installerPath, uninstallerPath);
  delete defines.BUILD_UNINSTALLER;
  defines.UNINSTALLER_OUT_FILE = uninstallerPath;
  return {script, isCustomScript: false};
}
module.exports = {staticUninstaller};
