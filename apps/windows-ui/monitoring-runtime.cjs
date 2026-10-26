'use strict';
// Only trusted main uses these fixed paths. No renderer/environment-selected interpreter.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function bundledLayout(resourcesPath,version,pin=require('./monitoring-package.json'),io=fs){
  const base=path.resolve(resourcesPath,'monitoring');
  if(pin.schema!==1||pin.version!==version||!/^[a-f0-9]{64}$/.test(pin.manifestSha256||''))throw Error('runtime_metadata_invalid');
  const checked=name=>{
    if(typeof name!=='string'||!name||name.includes('\\')||name.split('/').some(p=>!p||p==='.'||p==='..')||path.isAbsolute(name)||name.includes(':'))throw Error('runtime_path_invalid');
    const target=path.resolve(base,...name.split('/'));
    let current=base;
    for(const part of ['',...name.split('/')]){
      if(part)current=path.join(current,part);
      const stat=io.lstatSync(current);if(stat.isSymbolicLink())throw Error('runtime_link_invalid');
    }
    if(io.realpathSync(target).toLowerCase()!==target.toLowerCase())throw Error('runtime_path_redirected');
    return target;
  };
  const manifestFile=checked('manifest.json'),stat=io.statSync(manifestFile);
  if(stat.size>128*1024)throw Error('runtime_manifest_excessive');
  const bytes=io.readFileSync(manifestFile);if(hash(bytes)!==pin.manifestSha256)throw Error('runtime_manifest_mismatch');
  const manifest=JSON.parse(bytes);
  if(manifest.schema!==1||manifest.version!==version||manifest.pythonVersion!=='3.13.3'||!manifest.files||Array.isArray(manifest.files)||Object.keys(manifest.files).length>128)throw Error('runtime_manifest_invalid');
  for(const required of ['runtime/python.exe','runtime/python313.dll','runtime/python313.zip','runtime/python313._pth',
    'code/BUNDLED-MONITORING.json','code/scripts/monitoring-pipe-client.py','code/scripts/monitoring-pipe-server.py'])if(!manifest.files[required])throw Error('runtime_incomplete');
  for(const [name,digest]of Object.entries(manifest.files)){
    if(!/^[a-f0-9]{64}$/.test(digest)||hash(io.readFileSync(checked(name)))!==digest)throw Error('runtime_file_mismatch');
  }
  const expected=new Set(['manifest.json',...Object.keys(manifest.files)]);let entries=0;
  function walk(directory,depth=0){
    if(depth>6)throw Error('runtime_tree_excessive');
    for(const entry of io.readdirSync(directory,{withFileTypes:true})){
      if(++entries>256||entry.isSymbolicLink())throw Error('runtime_tree_invalid');
      const file=path.join(directory,entry.name);
      if(entry.isDirectory())walk(file,depth+1);
      else if(!entry.isFile()||!expected.delete(path.relative(base,file).split(path.sep).join('/')))throw Error('runtime_extra_file');
    }
  }
  walk(base);if(expected.size)throw Error('runtime_incomplete');
  const policy=JSON.parse(io.readFileSync(checked('code/BUNDLED-MONITORING.json'),'utf8'));
  if(policy.schema!==1||policy.realOnly!==true||policy.version!==version)throw Error('runtime_policy_invalid');
  if(['2.0.0-dev.6','2.0.0-dev.7'].includes(version)&&(policy.gpuReadOnly!==true||
    policy.nativeSha256!==manifest.files['code/native/adlx/bridge.exe']||!manifest.files['code/native/adlx/bridge-build.json']||
    !manifest.files['licenses/AMD-ADLX-SDK-License.pdf']))throw Error('runtime_gpu_incomplete');
  return {python:checked('runtime/python.exe'),script:checked('code/scripts/monitoring-pipe-client.py'),cwd:path.join(base,'code')};
}
function sourceLayout(root){
  const config=fs.readFileSync(path.join(root,'.venv','pyvenv.cfg'),'utf8'),home=/^home\s*=\s*(.+)$/m.exec(config)?.[1]?.trim();
  if(!home||!path.isAbsolute(home))throw Error('python_environment_unavailable');
  return {python:fs.realpathSync(path.join(home,'python.exe')),script:path.join(root,'scripts','monitoring-pipe-client.py'),cwd:root};
}
module.exports={bundledLayout,sourceLayout};
