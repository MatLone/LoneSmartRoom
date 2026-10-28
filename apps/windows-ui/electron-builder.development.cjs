'use strict';
// Build-time configuration only. No runtime, identity or userData changes.
const path = require('node:path');
const existing = require('./package.json').build;
module.exports = {
  ...existing,
  directories: {...existing.directories, output: '../../.cache/artifacts/windows/desktop-dev9-consolidated-candidate-r6'},
  electronDist: 'node_modules/electron/dist',
  npmRebuild: false,
  afterPack: require('./build/preservation.cjs').afterPack,
  extraResources: [{from: '../../.cache/windows-monitoring-runtime/dev9-r1', to: 'monitoring', filter: ['**/*']}],
  publish: null,
  win: {...existing.win, target: [{target: 'nsis', arch: ['x64']}, {target: 'portable', arch: ['x64']}], requestedExecutionLevel: 'asInvoker'},
  nsis: {
    ...existing.nsis,
    oneClick: false, perMachine: false, selectPerMachineByDefault: false,
    allowElevation: false, packElevateHelper: false,
    runAfterFinish: false, deleteAppDataOnUninstall: false,
    differentialPackage: false,
    createDesktopShortcut: false,
    include: path.join(__dirname, 'build/development-installer.nsh'),
    installerIcon: 'assets/brand/windows-icon.ico',
    uninstallerIcon: 'assets/brand/windows-icon.ico',
    artifactName: 'Lone-Smart-Room-${version}-x64-Setup-DEV.${ext}'
  },
  portable: {
    requestExecutionLevel: 'user', unpackDirName: false,
    artifactName: 'Lone-Smart-Room-${version}-x64-Portable-DEV.${ext}'
  }
};
