'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.cache/validation/diagnostic-evidence-adapters-2026-10-26');fs.mkdirSync(out,{recursive:true});
const suites=['diagnostic-center','diagnostic-evidence','electron-window-policy','electron-tray','electron-monitoring','windows-dev5-monitoring',
  'windows-dev5-renderer','windows-distribution-policy','windows-dev6-monitoring','windows-dev7-packaging','version-launch-ui','android-wol-ui'];
let total=0;const results=[];
for(const name of suites){
  const r=cp.spawnSync(process.execPath,[path.join(root,'tests',name+'.cjs')],{cwd:root,encoding:'utf8',windowsHide:true,shell:false});
  const output=(r.stdout||'')+(r.stderr||'');fs.writeFileSync(path.join(out,name+'.log'),output);
  if(r.status!==0)throw Error('Mock regression failed: '+name);
  const match=/PASS: (\d+)/.exec(output)||/"checks":(\d+)/.exec(output),count=match?Number(match[1]):null;
  if(count!==null)total+=count;results.push({suite:name,ok:true,assertions:count});
}
const files=[...fs.readdirSync(path.join(root,'apps/windows-ui')).filter(n=>/\.(?:cjs|js|css|html|json)$/.test(n)).map(n=>'apps/windows-ui/'+n),
  ...suites.map(n=>'tests/'+n+'.cjs'),'tests/fixtures/diagnostic-evidence.json','scripts/test-diagnostic-evidence.cjs'];
const result={ok:true,totalCountedAssertions:total,suites:results,uncountedPassingSuites:results.filter(r=>r.assertions===null).length,
  nativeElectronRun:false,physicalSessions:0,operationalQueries:0,sourceHashes:Object.fromEntries(files.map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,n))).digest('hex')]))};
fs.writeFileSync(path.join(out,'node-tests.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({ok:true,suites:suites.length,totalCountedAssertions:total,physicalSessions:0}));
