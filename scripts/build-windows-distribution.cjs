'use strict';
// Deliberately never installs/runs a generated EXE. Existing toolchain only.
const fs = require('node:fs'), path = require('node:path'), cp = require('node:child_process');
const {staticUninstaller} = require('./nsis-static-uninstaller.cjs');
const root = path.resolve(__dirname, '..'), project = path.join(root, 'apps/windows-ui');
const modules = path.join(project, 'node_modules');
const config = require(path.join(project, 'electron-builder.development.cjs'));
const output = path.resolve(project, config.directories.output);
const evidence = path.join(root, '.cache/validation/windows-dev5');
const inside = (file, directory) => {const relative = path.relative(directory, file);return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));};
async function main() {
  if (!inside(output, path.join(root, '.cache/artifacts/windows'))) throw Error('Output outside artifact workspace');
  if (fs.existsSync(output)) throw Error('Output exists: preserve earlier artifacts; choose a new reviewed output directory');
  const versions = ['electron-builder', 'app-builder-lib'].map(name => require(path.join(modules, name, 'package.json')).version);
  if (versions.some(v => v !== '26.15.3')) throw Error('Static NSIS adapter requires reviewed electron-builder 26.15.3');
  const environmentNames = ['ELECTRON_BUILDER_CACHE', 'CSC_IDENTITY_AUTO_DISCOVERY', 'CSC_LINK', 'WIN_CSC_LINK', 'CSC_KEY_PASSWORD', 'WIN_CSC_KEY_PASSWORD'];
  const old = new Map(environmentNames.map(name => [name, process.env[name]]));
  const launches = [], originals = new Map();
  for (const name of ['spawn', 'spawnSync', 'execFile', 'execFileSync']) {
    const original = cp[name];originals.set(name, original);
    cp[name] = function(file, ...args) {
      const absolute = path.resolve(String(file));
      if (inside(absolute, output) || inside(absolute, path.join(root, '.cache/artifacts/windows')) || inside(absolute, path.join(project, 'dist')) || inside(absolute, path.join(root, '.cache/windows-monitoring-runtime'))) {
        throw Error('Forbidden execution of a generated distribution artifact');
      }
      launches.push({method: name, executable: absolute});
      return original.call(this, file, ...args);
    };
  }
  // This build has no reason to execute shell command strings.
  for (const name of ['exec', 'execSync']) {originals.set(name, cp[name]);cp[name] = () => {throw Error('Shell execution is forbidden in this distribution build');};}
  let extractionCount = 0, originalUninstaller, Target;
  try {
    for (const name of environmentNames) delete process.env[name];
    process.env.CSC_IDENTITY_AUTO_DISCOVERY = 'false';
    process.env.ELECTRON_BUILDER_CACHE = path.join(root, '.cache/electron-builder');
    const builder = require(path.join(modules, 'electron-builder'));
    Target = require(path.join(modules, 'app-builder-lib/out/targets/nsis/NsisTarget')).NsisTarget;
    const util = require(path.join(modules, 'app-builder-lib/out/targets/nsis/nsisUtil'));
    originalUninstaller = Target.prototype.computeScriptAndSignUninstaller;
    Target.prototype.computeScriptAndSignUninstaller = function(...args) {
      return staticUninstaller(this, ...args, {
        templates: util.nsisTemplatesDir, readFile: fs.promises.readFile,
        extract: async (input, destination) => {
          if (!inside(input, output) || !inside(destination, output)) throw Error('Static extraction outside new build');
          await util.UninstallerReader.exec(input, destination);extractionCount++;
        }
      });
    };
    const files = await builder.build({projectDir: project, targets: builder.Platform.WINDOWS.createTarget(['nsis', 'portable'], builder.Arch.x64), config, publish: 'never'});
    if (extractionCount !== 1) throw Error('Expected exactly one statically extracted NSIS uninstaller');
    fs.mkdirSync(evidence, {recursive: true});
    fs.writeFileSync(path.join(evidence, 'build-execution.json'), JSON.stringify({ok: true, files, staticUninstallerExtractions: extractionCount,
      generatedExecutablesRun: false, installerRun: false, packagedApplicationRun: false, execStringApisUsed: false, processLaunches: launches}, null, 2) + '\n');
    console.log('PASS: NSIS + portable built; uninstaller extracted statically; no generated executables launched.');
  } finally {
    if (Target && originalUninstaller) Target.prototype.computeScriptAndSignUninstaller = originalUninstaller;
    for (const [name, value] of originals) cp[name] = value;
    for (const [name, value] of old) {if (value === undefined) delete process.env[name];else process.env[name] = value;}
  }
}
if (require.main === module) main().catch(error => {console.error(error.stack);process.exitCode = 1;});
module.exports = {inside};
