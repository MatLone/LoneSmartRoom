'use strict';
// VM/DOM/event/process substitutes only; never starts Electron, Python or ADLX.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const model=require('../apps/windows-ui/monitoring-model.js');
const {createMonitoringHost}=require('../apps/windows-ui/monitoring-host.cjs');
const {snapshot,fixture}=require('./electron-monitoring.cjs');
const {rendererFixture}=require('./helpers/monitoring-dom.cjs');
let checks=0;const check=(value,label)=>{assert(value,label);checks++;};
function gpuSnapshot(){
  const s=snapshot(),units=['percent','celsius','celsius','megabytes','megabytes','megahertz','watts','rpm'];
  const values=[.01,55.5,62,1000,12272,2497,42,0];
  s.metrics.push(...model.gpuIds.map((id,i)=>({id,source:'amd.adlx',unit:units[i],value:values[i],state:'available',
    valid:true,stale:false,collected_at:s.generated_at,age_seconds:.1,interval_seconds:id.endsWith('total_mb')?60:2,data_kind:'real'})));
  return s;
}
function normalized(s=gpuSnapshot()){return model.normalize(s,{gpu:true});}
function mutateGpu(id,fn){const s=gpuSnapshot();fn(s.metrics.find(m=>m.id==='gpu.adlx.'+id));return s;}
function formatContract(){
  const s=normalized();check(s.schema_version===1&&s.metrics.length===29,'Additive v1, 21 basic + 8 GPU metrics');
  check(model.ids.length===21&&model.gpuIds.length===8,'Legacy IDs preserved separately');
  assert.throws(()=>model.normalize(gpuSnapshot()));checks++;
  const expected=['<0,1%','55,5 °C','62 °C','1.000 MB','12.272 MB','2.497 MHz','42 W','0 RPM'];
  model.gpuIds.forEach((id,i)=>check(model.format(s.metrics.find(m=>m.id===id))===expected[i],'Native GPU unit '+id));
  for(const [id,fn] of [
    ['utilization',m=>m.value=101],['temperature',m=>m.value=NaN],['power',m=>m.value=Infinity],
    ['temperature',m=>m.value=-274],['temperature',m=>m.value=301],['vram_used_mb',m=>m.value=1.5],
    ['core_clock',m=>m.value=1.5],['fan_rpm',m=>m.value=1000001],['power',m=>m.value=5001],
    ['utilization',m=>m.source='win32.systemtimes'],['utilization',m=>m.interval_seconds=1],
    ['utilization',m=>m.collected_at='2099-01-01T00:00:00Z'],['temperature',m=>m.value=null],
    ['utilization',m=>m.id='gpu.set_clock']]){
    assert.throws(()=>normalized(mutateGpu(id,fn)));checks++;
  }
  assert.throws(()=>normalized(mutateGpu('vram_used_mb',m=>m.value=12273)));checks++;
  assert.throws(()=>normalized(mutateGpu('vram_total_mb',m=>m.value=0)));checks++;
  const missing=normalized(mutateGpu('fan_rpm',m=>Object.assign(m,{value:null,valid:false,state:'unsupported'})));
  check(model.format(missing.metrics.find(m=>m.id==='gpu.adlx.fan_rpm'))==='—','Unavailable never becomes zero RPM');
  const aged=model.age(s,6).metrics.find(m=>m.id==='gpu.adlx.temperature');
  check(aged.state==='stale'&&!aged.valid&&aged.value===null,'UI cache ages without refreshing original timestamp');
  const inactive=gpuSnapshot();inactive.metrics.filter(m=>m.id.startsWith('gpu.')&&!m.id.endsWith('total_mb')).forEach(m=>m.interval_seconds=10);
  check(normalized(inactive).metrics.length===29,'Inactive GPU cadence explicitly permitted');
}
async function hostIntegration(){
  check(!!createMonitoringHost({runId:'a'.repeat(32),packaged:true,gpu:true}),'Packaged owned GPU host can be constructed without native operations');
  assert.throws(()=>createMonitoringHost({runId:'a'.repeat(32),gpu:true,simulated:true}));checks++;
  const f=fixture({gpu:true});f.host.start();
  check(f.args()[1].includes('--gpu-development')&&f.args()[1].includes('--duration')&&!f.args()[1].includes('--application'),'Fixed development GPU flag only');
  f.emit({v:1,event:'ready',bridge_pid:123,collector_pid:124,transport:'windows_named_pipe_v1',simulated:false});
  const first=gpuSnapshot();first.metrics.filter(m=>m.id.startsWith('gpu.')&&!m.id.endsWith('total_mb')).forEach(m=>Object.assign(m,{value:null,valid:false,state:'error'}));
  f.emit({v:1,event:'response',body:{ok:true,snapshot:first}});
  check(f.host.view().connection==='connected'&&f.host.view().snapshot.metrics[0].valid,'First rejected GPU frame does not disconnect CPU or IPC');
  check(f.host.view().snapshot.metrics.find(m=>m.id==='gpu.adlx.temperature').value===null,'First invalid GPU reading stays null');
  const next=gpuSnapshot();next.sequence=2;f.emit({v:1,event:'response',body:{ok:true,snapshot:next}});
  check(f.host.view().gpu_enabled&&f.host.view().snapshot.metrics.find(m=>m.id==='gpu.adlx.temperature').value===55.5,'Next valid frame reaches main');
  f.emit({v:1,event:'disconnected'});check(f.host.view().connection==='disconnected','IPC disconnect reported');
  const recovered=gpuSnapshot();recovered.sequence=3;f.emit({v:1,event:'response',body:{ok:true,snapshot:recovered}});
  check(f.host.diagnostics().reconnections===1,'Reconnect same owned process');
  const timers=f.timers.size;f.host.setActive(false);check(f.timers.size===timers,'Inactivity replaces timer, does not add polling');
  check([...f.periods.values()].join()==='10000','Hidden/unfocused GPU session polls cache at 10 seconds');
  f.host.setActive(true);check([...f.periods.values()].join()==='1000','Foreground cache polling restored to one second');
  check(f.child.requests.every(x=>x==='{"v":1,"op":"snapshot"}\n'),'No new wire commands or arbitrary arguments');
  assert.throws(()=>f.host.start());checks++;
  check(await f.host.stop(),'Normal EOF still waits for owned worker exit');
  check(f.child.exitCode===0&&f.timers.size===0,'No mocked processes/timers remain');
}
function rendererIntegration(){
  const f=rendererFixture();
  const send=(connection,s)=>f.send({v:1,connection,gpu_enabled:true,simulated:false,snapshot:s,last_valid_at:{}});
  const sample=normalized();send('connected',sample);
  check(f.cards[0].querySelector('.value').textContent==='0%','CPU unchanged');
  check(f.cards[2].querySelector('.value').textContent==='8,0 GiB','RAM unchanged');
  check(f.cards[1].querySelector('.value').textContent==='<0,1%','Small GPU positive percent remains nonzero');
  check(f.cards[3].querySelector('.value').textContent==='55,5 °C','GPU temperature prominent');
  const row=id=>f.gpu.querySelector(`[data-metric-id="gpu.adlx.${id}"]`).querySelector('strong').textContent;
  check(row('vram_total_mb')==='12.272 MB'&&row('fan_rpm')==='0 RPM','Native MB and valid zero RPM visible');
  f.window.innerWidth=390;send('connected',sample);
  check(f.minis[0].querySelector('strong').textContent==='0%'&&f.minis[2].querySelector('strong').textContent==='8,0 GiB','Widget CPU/RAM remain visible');
  check(f.minis[1].querySelector('strong').textContent==='<0,1%'&&f.minis[1].querySelector('small').textContent.includes('55,5 °C'),'Widget GPU utilization + temperature');
  check(f.minis[3].querySelector('small').textContent.includes('1.000 MB / 12.272 MB'),'Compact widget VRAM');
  f.reset();f.tick();check(f.writes()===0,'No duplicate text writes without new data');
  f.document.hidden=true;f.reset();send('connected',sample);f.tick();check(f.writes()===0,'Hidden interface defers DOM changes');
  f.clock(7000);f.document.hidden=false;f.listeners.get('visibilitychange')();
  check(f.cards[3].querySelector('small').textContent==='Desatualizada'&&row('core_clock')==='Desatualizado','Foreground restoration ages readings');
  send('disconnected',sample);check(f.cards[1].querySelector('.value').textContent==='—'&&row('power')==='Indisponível','Disconnect never shows old GPU numbers');
  send('connected',normalized(mutateGpu('power',m=>Object.assign(m,{value:null,valid:false,state:'unsupported'}))));
  check(row('power')==='Indisponível'&&f.cards[3].querySelector('.value').textContent==='55,5 °C','Partially unavailable sensors independent');
  check(f.storage.querySelector('[data-volume="c"]').querySelector('[data-metric-id="storage.c.read_rate"]').querySelector('strong').textContent==='0 bytes/s','Disk valid zero unchanged');
}
(async()=>{formatContract();await hostIntegration();rendererIntegration();
  const main=fs.readFileSync(path.resolve(__dirname,'../apps/windows-ui/desktop-main.cjs'),'utf8');
  check(main.includes("const gpuDevelopment=monitoringDevelopment&&process.argv.includes('--lone-gpu-development')"),'GPU gated behind existing isolated development profile');
  const result={ok:true,checks,realSensors:false,realProcesses:false,electronRun:false};
  const out=path.resolve(__dirname,'../.cache/validation/gpu-dashboard-integration-2026-10-26');fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,'gpu-node-tests.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
