'use strict';
// All fixtures, including Python process objects, are substitutes. No packaged executable or sensors run.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),{EventEmitter}=require('node:events');
const root=path.resolve(__dirname,'..'),model=require('../apps/windows-ui/monitoring-model.js'),{snapshot}=require('./electron-monitoring.cjs');
const {createMonitoringHost}=require('../apps/windows-ui/monitoring-host.cjs');
const {bundledLayout}=require('../apps/windows-ui/monitoring-runtime.cjs');
let checks=0;const check=(v,n)=>{assert(v,n);checks++;};const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function precision(){
  for(const n of [Number.MIN_VALUE,0.0000496,0.0043,0.049,0.099999]){
    const metric={unit:'percent',value:n,valid:true,stale:false};const before=JSON.stringify(metric);
    check(model.format(metric)==='<0,1%','Small positive percent never zero');check(JSON.stringify(metric)===before,'Formatting preserves the original value');
  }
  check(model.format({unit:'percent',value:0,valid:true,stale:false})==='0%','Exact zero stays zero');
  check(model.format({unit:'percent',value:0.1,valid:true,stale:false})==='0,1%','Boundary 0.1 percent');
  check(model.format({unit:'bytes_per_second',value:0,valid:true,stale:false})==='0 bytes/s','Valid zero I/O retained');
  check(model.format({unit:'bytes_per_second',value:0.000001,valid:true,stale:false})==='<0,01 bytes/s','Tiny positive rate not zero');
  check(model.format({unit:'percent',value:null,valid:false,stale:false})==='—','Null never formatted as zero');
  check(model.age(model.normalize(snapshot()),4).metrics[0].value===null,'Stale nulls number');
  const renderer=fs.readFileSync(path.join(root,'apps/windows-ui/monitoring-renderer.js'),'utf8');
  check(renderer.includes("textContent='Ocupação do disco'")&&renderer.includes("'Capacidade válida'"),'Occupation bar and capacity badge labeled independently');
  check(renderer.includes("endsWith('.activity')&&!m?.valid?'Indisponível'"),'Activity null explicitly unavailable');
  const preload=fs.readFileSync(path.join(root,'apps/windows-ui/preload.cjs'),'utf8');
  check(!/\b(?:spawn|exec|readFile|net\.connect|setLoginItemSettings)\b/.test(preload),'No privileged generic preload');
}
function runtimeProof(){
  const cache=path.join(root,'.cache/tests');fs.mkdirSync(cache,{recursive:true});
  const temp=fs.mkdtempSync(path.join(cache,'dev5 runtime with spaces-')),base=path.join(temp,'monitoring');
  const names=['runtime/python.exe','runtime/python313.dll','runtime/python313.zip','runtime/python313._pth','code/BUNDLED-MONITORING.json',
    'code/scripts/monitoring-pipe-client.py','code/scripts/monitoring-pipe-server.py','code/monitoring/winpipe.py'];
  for(const name of names){const f=path.join(base,name);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,name==='code/BUNDLED-MONITORING.json'?JSON.stringify({schema:1,version:'2.0.0-dev.5',realOnly:true}):'fixture '+name);}
  const manifest={schema:1,version:'2.0.0-dev.5',pythonVersion:'3.13.3',files:Object.fromEntries(names.map(n=>[n,hash(fs.readFileSync(path.join(base,n)))]))};
  const bytes=Buffer.from(JSON.stringify(manifest)),mf=path.join(base,'manifest.json');fs.writeFileSync(mf,bytes);
  const pin={schema:1,version:manifest.version,manifestSha256:hash(bytes)};
  try{
    const layout=bundledLayout(temp,manifest.version,pin);check(layout.python===path.join(base,'runtime/python.exe')&&layout.cwd===path.join(base,'code'),'Fixed bundled interpreter/script and cwd');
    assert.throws(()=>bundledLayout(temp,'wrong',pin));checks++;
    assert.throws(()=>bundledLayout(temp,manifest.version,{...pin,manifestSha256:'0'.repeat(64)}));checks++;
    const changed=path.join(base,'code/monitoring/winpipe.py'),old=fs.readFileSync(changed);fs.writeFileSync(changed,'tampered');
    assert.throws(()=>bundledLayout(temp,manifest.version,pin));checks++;fs.writeFileSync(changed,old);
    const extra=path.join(base,'code/json.py');fs.writeFileSync(extra,'unexpected');assert.throws(()=>bundledLayout(temp,manifest.version,pin));checks++;fs.unlinkSync(extra);
    const invalid=Buffer.from(JSON.stringify({...manifest,files:{...manifest.files,'../escape.py':'0'.repeat(64)}}));fs.writeFileSync(mf,invalid);
    assert.throws(()=>bundledLayout(temp,manifest.version,{...pin,manifestSha256:hash(invalid)}));checks++;fs.writeFileSync(mf,bytes);
    const linked=new Proxy(fs,{get(target,key){if(key==='lstatSync')return f=>f===changed?{isSymbolicLink:()=>true}:target.lstatSync(f);return target[key];}});
    assert.throws(()=>bundledLayout(temp,manifest.version,pin,linked));checks++;
  }finally{const resolved=fs.realpathSync(temp);assert(resolved.startsWith(fs.realpathSync(cache)+path.sep));fs.rmSync(resolved,{recursive:true});}
}
function hostFixture({layoutFailure=false,automaticExit=true}={}){
  const child=new EventEmitter();child.pid=17;child.exitCode=null;child.stdout=new EventEmitter();child.stdin=new EventEmitter();
  const requests=[],scheduled=new Map(),views=[];let next=0,args,calls=0,clock=0;
  const emit=value=>child.stdout.emit('data',Buffer.from(JSON.stringify(value)+'\n'));
  const exit=()=>{emit({v:1,event:'stopped',clean:true,workerExited:true,worker:{stop:{stopped:true}}});child.exitCode=0;child.emit('exit',0);};
  child.stdin.write=data=>{requests.push(data);return true;};child.stdin.end=()=>{if(automaticExit)exit();};
  const host=createMonitoringHost({root,runId:'a'.repeat(32),packaged:true,version:'2.0.0-dev.5',now:()=>clock,
    resolveLayout:()=>{if(layoutFailure)throw Error('fixture broken');return {python:path.join(root,'.cache/fixture-python.exe'),script:path.join(root,'.cache/fixture-client.py'),cwd:root};},
    publish:value=>views.push(value),spawnChild:(...value)=>{args=value;calls++;return child;},
    interval:(fn,ms)=>{scheduled.set(++next,{fn,ms,type:'interval'});return next;},clear:id=>scheduled.delete(id),
    timeout:(fn,ms)=>{scheduled.set(++next,{fn,ms,type:'timeout'});return next;},cancel:id=>scheduled.delete(id)});
  return {host,child,emit,exit,requests,scheduled,views,args:()=>args,calls:()=>calls,advance:n=>clock+=n};
}
async function ownedLifecycle(){
  assert.throws(()=>createMonitoringHost({root,runId:'a'.repeat(32),packaged:true,simulated:true}));checks++;
  const f=hostFixture();f.host.start();const [exe,args,options]=f.args();
  check(path.isAbsolute(exe)&&options.shell===false&&options.windowsHide,'No elevation, shell or relative executable');
  check(args.includes('--application')&&args.includes('--owner-pid')&&!args.includes('--duration')&&!args.includes('--simulated'),'Permanent lifetime owned by the packaged application only');
  check(f.scheduled.size===1&&[...f.scheduled.values()][0].ms===1000,'One polling timer, no 70-second production TTL');
  f.emit({v:1,event:'ready',bridge_pid:17,collector_pid:18,transport:'windows_named_pipe_v1',simulated:false});
  check(f.requests[0]==='{"v":1,"op":"snapshot"}\n','Only fixed readonly request');
  f.emit({v:1,event:'response',body:{ok:true,snapshot:snapshot()}});check(f.host.view().connection==='connected','Validated data accepted');
  f.emit({v:1,event:'disconnected'});check(f.host.view().connection==='disconnected','IPC unavailable distinct');
  f.emit({v:1,event:'response',body:{ok:true,snapshot:snapshot()}});check(f.host.diagnostics().reconnections===1,'Reconnect same worker');
  check(f.calls()===1,'Reconnection does not duplicate process');
  f.advance(4000);check(f.host.view().snapshot.metrics[0].value===null,'Stale data null');
  assert.throws(()=>f.host.start());checks++;
  check(await f.host.stop(),'Normal EOF waits for actual worker exit');
  check(f.child.exitCode===0&&f.scheduled.size===0,'All timers and mocked child gone');
  const missing=hostFixture({layoutFailure:true});missing.host.start();check(missing.host.view().connection==='disconnected'&&missing.calls()===0,'Invalid runtime fails closed without exiting dashboard');check(await missing.host.stop(),'Missing runtime leaves no children');
  const slow=hostFixture({automaticExit:false});slow.host.start();const pending=slow.host.stop();
  [...slow.scheduled.values()].find(t=>t.type==='timeout'&&t.ms===6500).fn();check(await pending===false&&slow.child.exitCode===null,'Stop timeout never declares success or kills');
  slow.exit();check(await slow.host.stop(),'Later actual worker completion permits safe exit');
  const malformed=hostFixture();malformed.host.start();malformed.emit(null);check(malformed.host.view().error==='invalid_transport','Null transport frame cannot crash Electron');await malformed.host.stop();
}
(async()=>{precision();runtimeProof();await ownedLifecycle();const result={ok:true,checks,realSensors:false,realNativeProcesses:false,packagedExecutablesRun:false};
  fs.mkdirSync(path.join(root,'.cache/validation/windows-dev5'),{recursive:true});fs.writeFileSync((process.env.LONE_TEST_REPORT_ROOT?path.join(process.env.LONE_TEST_REPORT_ROOT,'monitoring-node-tests.json'):path.join(root,'.cache/validation/windows-dev5/monitoring-node-tests.json')),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
