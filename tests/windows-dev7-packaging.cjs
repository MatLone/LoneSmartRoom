'use strict';
// Read-only package fixtures. No Electron, sensor, pipe or generated EXE execution.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),app=path.join(root,'apps/windows-ui');
const {bundledLayout}=require('../apps/windows-ui/monitoring-runtime.cjs');
const payload=path.join(root,'.cache/windows-monitoring-runtime/dev7'),base=path.dirname(payload);
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const original=JSON.parse(fs.readFileSync(path.join(payload,'manifest.json')));
const originalPolicy=JSON.parse(fs.readFileSync(path.join(payload,'code/BUNDLED-MONITORING.json')));
let checks=0;const check=(v,why)=>{assert(v,why);checks++;};
function layout(version,change=()=>{},omit=null){
  const manifest=structuredClone(original),policy=structuredClone(originalPolicy);
  manifest.version=policy.version=version;change(policy);
  const policyBytes=Buffer.from(JSON.stringify(policy));manifest.files['code/BUNDLED-MONITORING.json']=hash(policyBytes);
  if(omit)delete manifest.files[omit];
  const bytes=Buffer.from(JSON.stringify(manifest)),pin={schema:1,version,pythonVersion:'3.13.3',manifestSha256:hash(bytes)};
  const io=Object.create(fs);
  io.readFileSync=(file,encoding)=>{
    const relative=path.relative(payload,file).split(path.sep).join('/');
    const value=relative==='manifest.json'?bytes:relative==='code/BUNDLED-MONITORING.json'?policyBytes:null;
    return value?(encoding?value.toString(encoding):value):fs.readFileSync(file,encoding);
  };
  io.readdirSync=(dir,options)=>fs.readdirSync(dir,options).filter(e=>!omit||path.relative(payload,path.join(dir,e.name)).split(path.sep).join('/')!==omit);
  // Main normally resolves <resources>/monitoring; map that tree to the staged fixture.
  const map=file=>file===path.join(base,'monitoring')||file.startsWith(path.join(base,'monitoring')+path.sep)?payload+file.slice(path.join(base,'monitoring').length):file;
  const mapped={readFileSync:(f,e)=>io.readFileSync(map(f),e),statSync:f=>fs.statSync(map(f)),
    lstatSync:f=>fs.lstatSync(map(f)),realpathSync:f=>path.resolve(f),readdirSync:(f,o)=>io.readdirSync(map(f),o)};
  return bundledLayout(base,version,pin,mapped);
}
for(const version of ['2.0.0-dev.6','2.0.0-dev.7','2.0.0-dev.8','2.0.0-dev.9']){
  check(path.isAbsolute(layout(version).python),'Approved version validates protected GPU payload '+version);
  for(const change of [p=>p.gpuReadOnly=false,p=>delete p.gpuReadOnly,p=>p.nativeSha256='0'.repeat(64)]){
    assert.throws(()=>layout(version,change),/runtime_gpu_incomplete/);checks++;
  }
  for(const omit of ['code/native/adlx/bridge.exe','code/native/adlx/bridge-build.json','licenses/AMD-ADLX-SDK-License.pdf']){
    assert.throws(()=>layout(version,()=>{},omit),/runtime_gpu_incomplete/);checks++;
  }
}
const pkg=require('../apps/windows-ui/package.json'),lock=require('../apps/windows-ui/package-lock.json'),config=require('../apps/windows-ui/electron-builder.development.cjs');
check(pkg.version==='2.0.0-dev.9'&&lock.version===pkg.version&&lock.packages[''].version===pkg.version,'Version and lock roots match');
check(config.appId==='com.lone.smartroom'&&pkg.name==='lone-smart-room','Stable application identity');
check(config.directories.output.includes('desktop-dev9-consolidated-candidate-r12')&&config.extraResources[0].from.endsWith('/dev9-r1'),'Fresh distribution and runtime outputs');
check(config.nsis.runAfterFinish===false&&!config.nsis.allowElevation&&!config.nsis.deleteAppDataOnUninstall,'No autorun, elevation or profile deletion');
const approved=require('../docs/gpu-resume-fix-2026-10-26/evidence/source-hashes.json');
for(const file of ['apps/windows-ui/monitoring-model.js',
  'native/adlx/bridge.cpp','monitoring/adlx_provider.py'])check(hash(fs.readFileSync(path.join(root,file)))===approved[file],'Validated implementation retained '+file);
const result={ok:true,checks,failures:0,skipped:0,realSensors:false,packagedExecutablesRun:false,securityGuardVersions:['2.0.0-dev.6','2.0.0-dev.7','2.0.0-dev.8','2.0.0-dev.9']};
const out=path.join(root,'.cache/validation/windows-dev9');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'dev7-security-tests.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
