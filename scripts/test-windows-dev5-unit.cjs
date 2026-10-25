'use strict';
// Release gate: existing Node and substitute-only tests, never Electron or sensors.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.cache/validation/windows-dev5');
const files=['tests/electron-window-policy.cjs','tests/electron-tray.cjs','tests/electron-monitoring.cjs',
  'tests/windows-dev5-monitoring.cjs','tests/windows-dev5-renderer.cjs','tests/windows-distribution-policy.cjs'];
const results=[];let total=0;
fs.mkdirSync(out,{recursive:true});
for(const file of files){
  const r=cp.spawnSync(process.execPath,[path.join(root,file)],{cwd:root,encoding:'utf8',windowsHide:true});
  const output=(r.stdout||'')+(r.stderr||'');fs.writeFileSync(path.join(out,path.basename(file)+'.log'),output);
  if(r.status!==0)throw Error('Substitute suite failed: '+file);
  const count=Number(/PASS: (\d+)/.exec(output)?.[1]||/"checks":(\d+)/.exec(output)?.[1]);
  if(!Number.isSafeInteger(count)||count<=0)throw Error('Invalid suite receipt');
  results.push({file,checks:count,status:r.status});total+=count;
}
const sources=[...fs.readdirSync(path.join(root,'apps/windows-ui')).filter(n=>/\.(cjs|js|css|html|json)$/.test(n)).map(n=>'apps/windows-ui/'+n),...files];
const hashes=Object.fromEntries(sources.map(name=>[name,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,name))).digest('hex')]));
const receipt={ok:true,totalChecks:total,suites:results,sourceHashes:hashes,realSensors:false,nativeApplicationsRun:false,packagedExecutablesRun:false};
fs.writeFileSync(path.join(out,'node-unit-tests.json'),JSON.stringify(receipt,null,2)+'\n');console.log(`PASS: ${total} assertions across ${results.length} substitute/static suites; no GUI or real collection.`);
