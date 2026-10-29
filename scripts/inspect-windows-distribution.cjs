'use strict';
// Offline NSIS/7z/ASAR/PE inspection. Does not launch any generated executable.
const fs = require('node:fs'), path = require('node:path'), cp = require('node:child_process'), crypto = require('node:crypto'), zlib = require('node:zlib'), assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..'), app = path.join(root, 'apps/windows-ui');
if(process.argv.slice(2).some(v=>v!=='--openrgb')||process.argv.length>3)throw Error('reviewed_inspection_target_required');
const rgbBuild=process.argv.includes('--openrgb');
const output = path.resolve(app,require(path.join(app,rgbBuild?'electron-builder.rgb-development.cjs':'electron-builder.development.cjs')).directories.output);
const evidence = path.join(root, rgbBuild?'.cache/validation/openrgb-control-r2':'.cache/validation/windows-dev9');
const asar = require(path.join(app, 'node_modules/@electron/asar'));
const seven = path.join(root, '.cache/electron-builder/7zip@1.0.0/7zip-win-x64-a34pt/bin/7za.exe');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
let checks = 0;const check = (v, why) => {assert(v, why);checks++;};
function peInfo(raw) {
  const pe = raw.readUInt32LE(0x3c);check(raw.subarray(pe, pe + 4).equals(Buffer.from('PE\0\0')), 'PE signature');
  const count = raw.readUInt16LE(pe + 6), optional = pe + 24, table = optional + raw.readUInt16LE(pe + 20);
  const dirs = optional + (raw.readUInt16LE(optional) === 0x20b ? 112 : 96);
  function rvaOffset(rva) {
    for (let i = 0; i < count; i++) {const p = table + 40 * i, va = raw.readUInt32LE(p + 12), size = Math.max(raw.readUInt32LE(p + 8), raw.readUInt32LE(p + 16));if (rva >= va && rva < va + size) return raw.readUInt32LE(p + 20) + rva - va;}
    throw Error('Invalid resource address');
  }
  const base = rvaOffset(raw.readUInt32LE(dirs + 16));
  const entries = relative => {const p = base + relative, n = raw.readUInt16LE(p + 12) + raw.readUInt16LE(p + 14);return Array.from({length: n}, (_, i) => [raw.readUInt32LE(p + 16 + 8 * i), raw.readUInt32LE(p + 20 + 8 * i)]);};
  function leaves(relative) {return entries(relative).flatMap(([_key, value]) => {if (value & 0x80000000) return leaves(value & 0x7fffffff);const p = base + value, start = rvaOffset(raw.readUInt32LE(p));return [raw.subarray(start, start + raw.readUInt32LE(p + 4))];});}
  const resources = new Map(entries(0).map(([kind, target]) => [kind, leaves(target & 0x7fffffff)]));
  const ico = fs.readFileSync(path.join(app, 'assets/brand/windows-icon.ico'));
  let matched = 0;for (let i = 0; i < ico.readUInt16LE(4); i++) {const p = 6 + 16 * i, start = ico.readUInt32LE(p + 12), size = ico.readUInt32LE(p + 8);if ((resources.get(3) || []).some(b => b.equals(ico.subarray(start, start + size)))) matched++;}
  check(matched > 0 && (resources.get(14) || []).length > 0, 'Official icon resources present');
  const manifest = Buffer.concat(resources.get(24) || []).toString('utf8');
  check(/requestedExecutionLevel[^>]+level="asInvoker"/.test(manifest), 'As-invoker executable manifest');
  check(raw.readUInt32LE(dirs + 32) === 0 && raw.readUInt32LE(dirs + 36) === 0, 'Unsigned PE certificate table');
  return {machine: raw.readUInt16LE(pe + 4).toString(16), officialIconImages: matched, certificateTableEmpty: true};
}
function nsisBlocks(raw) {
  const magic = Buffer.from('efbeadde4e756c6c736f6674496e7374', 'hex');
  let start = -1, position = 0;
  while ((position = raw.indexOf(magic, position)) !== -1) {if (position >= 4 && position + 24 <= raw.length && raw.readUInt32LE(position + 20) === raw.length - position + 4) {start = position - 4;break;}position++;}
  check(start >= 0, 'Complete NSIS container found');
  position = start + 28;const blocks = [];
  while (position + 4 < raw.length) {
    const field = raw.readUInt32LE(position), size = field & 0x7fffffff;position += 4;
    if (size === 0 || position + size > raw.length) break;
    let data = raw.subarray(position, position + size);position += size;
    if (field & 0x80000000) data = zlib.inflateRawSync(data, {maxOutputLength: 700 * 1024 * 1024});
    blocks.push(data);
  }
  check(blocks.length > 1, 'NSIS data blocks decoded without execution');return blocks;
}
function inspectAsar(archive) {
  let fileCount = 0;
  for (const item of asar.listPackage(archive)) {
    const name = item.replace(/\\/g, '/').replace(/^\/+/, ''), stat = asar.statFile(archive, name.split('/').join(path.sep));
    if (stat.files) continue;
    check(!stat.link, 'No ASAR symlinks');
    check(!/(?:^|\/)(?:\.env(?:\..*)?|agent_config\.json|credentials\.json|secrets\.json|local\.properties)$|\.(?:pem|key|crt|cer|pfx|p12|jks|keystore|db|sqlite3?)$/i.test(name), 'No credentials, certificates or local databases');
    const data = asar.extractFile(archive, name.split('/').join(path.sep));fileCount++;
    if (name === 'package.json') {
      const pkg = JSON.parse(data);check(pkg.name === 'lone-smart-room' && pkg.productName === 'Lone Smart Room' && pkg.version === '2.0.0-dev.9', 'Packaged product/version');continue;
    }
    check(!name.startsWith('node_modules/') && !name.startsWith('build/') && !name.startsWith('electron-builder.'), 'No build-only tools in app');
    const source = path.join(app, name);check(fs.existsSync(source) && data.equals(fs.readFileSync(source)), 'Packaged resources equal source');
    if (/\.(?:cjs|js|html|css|json|svg)$/.test(name)) {
      check(!/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(data.toString('utf8')), 'No private keys in text resources');
      check(!/(?:secret_hex|api_key|password|access_token)\s*[:=]\s*["'][A-Za-z0-9_+/=.-]{24,}["']/i.test(data.toString('utf8')), 'No credential assignment patterns');
    }
  }
  const html = asar.extractFile(archive, 'index.html').toString('utf8');
  check(html.includes("connect-src 'none'") && !html.includes('src="agent-status.js"') && !html.includes('src="app-launch.js"'), 'Operational client remains absent');
  return fileCount;
}
fs.mkdirSync(evidence, {recursive: true});
const sharedAsar = fs.readFileSync(path.join(output, 'win-unpacked/resources/app.asar'));
const sharedExe = fs.readFileSync(path.join(output, 'win-unpacked/Lone Smart Room.exe'));
const application = peInfo(sharedExe);check(application.machine === '8664', 'Application payload is x64');
const appFileCount = inspectAsar(path.join(output, 'win-unpacked/resources/app.asar'));
const packages = [];
for (const kind of ['Setup', 'Portable']) {
  const name = rgbBuild?`Lone-Smart-Room-2.0.0-dev.9-x64-OpenRGB-Candidate-${kind}.exe`:`Lone-Smart-Room-2.0.0-dev.9-x64-${kind}-DEV.exe`, raw = fs.readFileSync(path.join(output, name));
  const pe = peInfo(raw), blocks = nsisBlocks(raw);
  const archives = blocks.filter(data => data.subarray(0, 6).equals(Buffer.from('377abcaf271c', 'hex')));
  check(archives.length === 1, 'Exactly one embedded 7z application archive');
  const inspection = path.join(evidence, kind.toLowerCase());fs.mkdirSync(inspection, {recursive: true});
  const payload = path.join(inspection, 'payload.7z');fs.writeFileSync(payload, archives[0]);
  const testOutput = cp.execFileSync(seven, ['t', payload], {encoding: 'utf8', windowsHide: true});
  check(testOutput.includes('Everything is Ok'), 'Embedded 7z integrity test');
  const listing = cp.execFileSync(seven, ['l', '-slt', payload], {encoding: 'utf8', windowsHide: true});fs.writeFileSync(path.join(inspection, 'payload-list.txt'), listing);
  const names = [...listing.matchAll(/^Path = (.+)$/gm)].slice(1).map(m => m[1].trim().replace(/\\/g, '/'));
  check(names.every(n => !n.startsWith('/') && !n.includes('../') && !/^[A-Za-z]:/.test(n)), 'Safe relative archive entries');
  check(names.every(n => !/(?:^|\/)(?:\.runtime|agent|recovery|\.git|node_modules)(?:\/|$)|\.(?:pem|key|crt|cer|pfx|p12|jks|keystore|db|sqlite3?)$/i.test(n)), 'No runtime secrets, agent, source control or build tools in outer payload');
  cp.execFileSync(seven, ['x', '-y', '-o'+inspection, payload, 'resources/app.asar', 'Lone Smart Room.exe', 'resources/monitoring/*', 'resources/app.asar.unpacked/*'], {encoding: 'utf8', windowsHide: true});
  check(fs.readFileSync(path.join(inspection, 'resources/app.asar')).equals(sharedAsar), 'Embedded ASAR equals inspected unpacked app');
  check(fs.readFileSync(path.join(inspection, 'Lone Smart Room.exe')).equals(sharedExe), 'Embedded executable equals inspected x64 application');
  check(fs.readFileSync(path.join(inspection,'resources/app.asar.unpacked/windows-inventory.ps1')).equals(fs.readFileSync(path.join(app,'windows-inventory.ps1'))),'Unpacked fixed read-only inventory helper matches source');
  const monitoring=path.join(inspection,'resources/monitoring');
  const manifest=JSON.parse(fs.readFileSync(path.join(monitoring,'manifest.json')));
  for(const [name,digest]of Object.entries(manifest.files))check(sha(fs.readFileSync(path.join(monitoring,name)))===digest,'Embedded sidecar matches verified manifest');
  require(path.join(app,'monitoring-runtime.cjs')).bundledLayout(path.join(inspection,'resources'),'2.0.0-dev.9');
  check(!names.some(n=>n.toLowerCase().endsWith('amdadlx64.dll')||n.endsWith('.h')),'No AMD driver DLL or SDK headers redistributed');
  if (kind === 'Setup') {
    check(blocks.some(b=>b.includes(fs.readFileSync(path.join(app,'build/preserve-runtime.ps1')))), 'Fixed runtime preservation helper embedded byte-for-byte');
    check(blocks.some(b=>b.includes(Buffer.from('Installation stopped before removing the previous version.', 'utf16le'))), 'Preservation failure stops before old uninstall');
    check(blocks.some(b => b.includes(Buffer.from('Replace its application files now?', 'utf16le'))), 'Explicit update consent compiled into installer');
    check(blocks.some(b => b.includes(Buffer.from('machine-wide installation exists', 'utf16le'))), 'Machine-wide migration stop compiled into installer');
    const uninstallers = blocks.filter(b => b.subarray(0, 2).toString() === 'MZ' && b.includes(Buffer.from('efbeadde4e756c6c736f6674496e7374', 'hex')));
    check(uninstallers.length === 1, 'Statically generated uninstaller included');
    const uninstallerInfo = peInfo(uninstallers[0]);check(uninstallerInfo.certificateTableEmpty, 'Uninstaller unsigned');
  }
  packages.push({kind, name, bytes: raw.length, sha256: sha(raw), pe, archiveBytes: archives[0].length, archiveSha256: sha(archives[0]), archiveEntries: names.length});
}
const execution = JSON.parse(fs.readFileSync(path.join(evidence, 'build-execution.json')));
check(execution.ok && execution.staticUninstallerExtractions === 1 && !execution.generatedExecutablesRun, 'Non-executing build receipt');
const result = {ok: true, checks, version: '2.0.0-dev.9', appId: 'com.lone.smartroom', application, appFileCount, applicationSha256: sha(sharedExe), asarSha256: sha(sharedAsar), packages,
  credentialsFound: false, operationalClient: false, packagedApplicationRun: false, installerRun: false};
fs.writeFileSync(path.join(evidence, 'artifact-inspection.json'), JSON.stringify(result, null, 2)+'\n');
console.log(`PASS: ${checks} offline checks; NSIS/portable payloads, x64 app, icons, metadata, credential scan; no generated executables run.`);
