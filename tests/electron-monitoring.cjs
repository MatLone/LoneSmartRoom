'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{EventEmitter}=require('node:events');
const root=path.resolve(__dirname,'..'),model=require('../apps/windows-ui/monitoring-model.js');
const {createMonitoringHost,MAX_LINE}=require('../apps/windows-ui/monitoring-host.cjs');
let checks=0;const check=(v,label)=>{assert(v,label);checks++;};
function snapshot(simulated=false){
  const stamp=new Date().toISOString();return {schema_version:1,sequence:1,generated_at:stamp,contains_simulated:simulated,
    metrics:model.ids.map(id=>{
      const ram=id.startsWith('ram.'),field=id.split('.').at(-1),v=id.split('.')[1];
      let unit,value,source;
      if(id==='cpu.utilization'){unit='percent';value=0;source='win32.systemtimes';}
      else if(ram){unit=field==='utilization'?'percent':'bytes';value={total:16*1024**3,used:8*1024**3,available:8*1024**3,utilization:50}[field];source='win32.memory';}
      else{unit=['occupation','activity'].includes(field)?'percent':field.endsWith('_rate')?'bytes_per_second':'bytes';
        value={total:256*1024**3,used:64*1024**3,free:192*1024**3,available:192*1024**3,occupation:25,read_rate:0,write_rate:2048,activity:0}[field];
        source=['read_rate','write_rate','activity'].includes(field)?'win32.pdh.logicaldisk':'win32.volume.'+v;}
      return {id,source:simulated?'fixture.metrics':source,unit,value,state:'available',valid:true,stale:false,
        collected_at:stamp,age_seconds:0.1,interval_seconds:['total','free','available','used','occupation'].includes(field)&&!ram?60:1,data_kind:simulated?'simulated':'real'};
    })};
}
function contract(){
  const s=snapshot();const copy=()=>structuredClone(s);
  check(model.format(model.normalize(s).metrics[0])==='0%','Valid CPU zero preserved');
  check(model.format(model.normalize(s).metrics.find(m=>m.id==='ram.total'))==='16,0 GiB','Bytes converted to GiB explicitly');
  check(model.format(model.normalize(s).metrics.find(m=>m.id==='storage.c.write_rate'))==='2 KiB/s','Small nonzero rate remains distinguishable from zero');
  for(const changed of [m=>m.value=NaN,m=>m.value=-1,m=>m.value=101,m=>m.value=true,m=>m.unit='Celsius',m=>m.id='gpu.utilization',m=>m.source='<img onerror=bad>',m=>m.collected_at='yesterday',m=>m.valid=false,m=>m.data_kind='simulated']){
    const input=copy();changed(input.metrics[0]);assert.throws(()=>model.normalize(input));checks++;
  }
  const bad=copy();bad.metrics.push(bad.metrics[0]);assert.throws(()=>model.normalize(bad));checks++;
  const invalid=copy();Object.assign(invalid.metrics[0],{state:'unavailable',valid:false,value:null});
  check(model.format(model.normalize(invalid).metrics[0])==='—','Unavailable never zero');
  const stale=model.age(model.normalize(s),3);check(!stale.metrics[0].valid&&stale.metrics[0].value===null&&stale.metrics[0].state==='stale','Client age invalidates stale data without refreshing timestamp');
  const old=copy();old.metrics[0].age_seconds=4;check(model.normalize(old).metrics[0].value===null,'Old data rejected on arrival');
  assert.throws(()=>model.normalize(snapshot(true)));checks++;
  check(model.normalize(snapshot(true),{simulated:true}).contains_simulated,'Fixtures explicitly identified');
  const ram=copy();const stamp=new Date().toISOString();ram.metrics.filter(m=>m.id.startsWith('ram.')).forEach(m=>m.collected_at=stamp);ram.metrics.find(m=>m.id==='ram.used').value=7*1024**3;
  assert.throws(()=>model.normalize(ram));checks++;
}
function fixture(){
  const child=new EventEmitter();child.pid=123;child.exitCode=null;child.stdout=new EventEmitter();child.stdin=new EventEmitter();child.requests=[];
  child.stdin.write=value=>{child.requests.push(value);return true;};
  child.stdin.end=()=>{emit({v:1,event:'stopped',clean:true,worker:{ok:true}});child.exitCode=0;child.emit('exit',0);};
  const events=[],timers=new Map();let clock=0,next=0,spawnArgs;
  const host=createMonitoringHost({root,runId:'a'.repeat(32),publish:v=>events.push(v),now:()=>clock,
    spawnChild:(...args)=>{spawnArgs=args;return child;},interval:fn=>{timers.set(++next,fn);return next;},clear:id=>timers.delete(id),
    timeout:fn=>{timers.set(++next,fn);return next;},cancel:id=>timers.delete(id)});
  function emit(v){child.stdout.emit('data',Buffer.from(JSON.stringify(v)+'\n'));}
  return {host,child,events,timers,emit,advance:n=>clock+=n,args:()=>spawnArgs};
}
async function lifecycle(){
  const f=fixture();f.host.start();const args=f.args();
  check(path.isAbsolute(args[0])&&args[1].includes('-I')&&args[2].shell===false&&args[2].windowsHide,'Fixed absolute isolated interpreter, no shell');
  check(!args[1].some(x=>x.includes('steam')||x.includes('secure_agent')),'No operational agent or launcher');
  f.emit({v:1,event:'ready',bridge_pid:123,collector_pid:124,transport:'windows_named_pipe_v1',simulated:false});
  check(f.child.requests.length===1&&f.child.requests[0]==='{"v":1,"op":"snapshot"}\n','Main sends only fixed cache request');
  f.emit({v:1,event:'response',body:{ok:true,snapshot:snapshot()}});check(f.host.view().connection==='connected','Validated response connected');
  const previous=f.host.view().snapshot.metrics[0].collected_at;f.advance(3100);
  check(f.host.view().snapshot.metrics[0].value===null&&f.host.view().last_valid_at['cpu.utilization']===previous,'Last valid timestamp retained without keeping stale number');
  f.emit({v:1,event:'disconnected',error:'do not echo me'});check(f.host.view().connection==='disconnected'&&!JSON.stringify(f.host.view()).includes('do not echo me'),'Disconnect sanitized');
  f.emit({v:1,event:'response',body:{ok:true,snapshot:snapshot()}});check(f.host.view().connection==='connected'&&f.host.diagnostics().reconnections===1,'Reconnect validates new sample');
  const bad=snapshot();bad.metrics[0].value=102;f.emit({v:1,event:'response',body:{ok:true,snapshot:bad}});check(f.host.view().error==='invalid_metrics','Bad values never exposed as connected');
  const clean=await f.host.stop();check(clean&&f.host.diagnostics().cleanStop&&f.child.exitCode===0,'EOF waits for normal child shutdown, no kill API');
  check(f.host.stop()===f.host.stop(),'Stop idempotent');
  const large=fixture();large.host.start();large.child.stdout.emit('data',Buffer.alloc(MAX_LINE+1));check(large.host.view().connection!=='connected','Oversized stdout fails closed');await large.host.stop();
  const timeout=fixture();timeout.host.start();timeout.emit({v:1,event:'ready',bridge_pid:1,collector_pid:2,transport:'windows_named_pipe_v1',simulated:false});timeout.advance(2000);
  [...timeout.timers.values()][0]();check(timeout.host.view().error==='read_timeout','Pending read timeout visible');await timeout.host.stop();
  const source=fs.readFileSync(path.join(root,'apps/windows-ui/monitoring-renderer.js'),'utf8');
  check(!/\.innerHTML\s*=|\bfetch\(|XMLHttpRequest|WebSocket|child_process|localStorage/.test(source),'Sensor values rendered as text, no network, shell or production storage');
  const main=fs.readFileSync(path.join(root,'apps/windows-ui/desktop-main.cjs'),'utf8');
  check(main.includes("developmentReview && process.argv.includes('--lone-monitoring-development')")&&main.includes("!app.isPackaged"),'Collector requires unpackaged explicit development opt-in');
  check(main.includes("../../.cache/windows-monitoring-development")&&main.includes('process.env.LONE_MONITORING_RUN_ID'),'Unique isolated profile path');
}
if(require.main===module)(async()=>{contract();await lifecycle();console.log(JSON.stringify({ok:true,checks,simulated:true,realSensors:false,nativeProcesses:false}));})().catch(e=>{console.error(e.stack);process.exitCode=1;});
module.exports={snapshot};
