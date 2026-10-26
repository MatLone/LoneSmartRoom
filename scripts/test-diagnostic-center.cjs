'use strict';
// Existing Node runtime; substitute/static suites only, no Electron or sensors.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.cache/validation/diagnostic-center-2026-10-26');
fs.mkdirSync(out,{recursive:true});
const suites=['diagnostic-center','electron-window-policy','electron-tray','electron-monitoring','windows-dev5-monitoring',
  'windows-dev5-renderer','windows-distribution-policy','windows-dev6-monitoring','windows-dev7-packaging','version-launch-ui','android-wol-ui'];
const results=[];let total=0;
for(const suite of suites){
  const run=cp.spawnSync(process.execPath,[path.join(root,'tests',suite+'.cjs')],{cwd:root,encoding:'utf8',windowsHide:true,shell:false});
  const output=(run.stdout||'')+(run.stderr||'');fs.writeFileSync(path.join(out,suite+'.log'),output);
  if(run.status!==0)throw Error('Substitute regression failed: '+suite);
  const match=/PASS: (\d+)/.exec(output)||/"checks":(\d+)/.exec(output),count=match?Number(match[1]):null;
  if(count!==null)total+=count;results.push({suite,ok:true,assertions:count});
}
const files=[...fs.readdirSync(path.join(root,'apps/windows-ui')).filter(n=>/\.(?:cjs|js|css|html|json)$/.test(n)).map(n=>'apps/windows-ui/'+n),
  ...suites.map(s=>'tests/'+s+'.cjs'),'scripts/test-diagnostic-center.cjs','tests/electron-diagnostic-bootstrap.cjs','tests/electron-diagnostic-native.cjs'];
const report={ok:true,suites:results,totalCountedAssertions:total,uncountedPassingSuites:results.filter(r=>r.assertions===null).length,
  realSensors:false,nativeApplicationsRun:false,operationalReaders:false,sourceHashes:Object.fromEntries(files.map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,n))).digest('hex')]))};
fs.writeFileSync(path.join(out,'node-tests.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({ok:true,suites:results.length,totalCountedAssertions:total,uncountedPassingSuites:report.uncountedPassingSuites,realSensors:false}));
