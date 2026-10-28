'use strict';
// Production host/renderer with fake clocks, DOM and process streams only.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {fixture,snapshot}=require('./electron-monitoring.cjs');
const {rendererFixture}=require('./helpers/monitoring-dom.cjs');
const {fixture:windowFixture}=require('./electron-tray.cjs');
const model=require('../apps/windows-ui/monitoring-model.js');
let checks=0;const check=(v,label)=>{assert(v,label);checks++;};
const dynamic=m=>m.id.startsWith('gpu.adlx.')&&!m.id.endsWith('total_mb');
function sample({state='available',age=0,interval=2}={}){
  const s=snapshot();s.metrics.push(...model.gpuIds.map((id,i)=>({id,source:'amd.adlx',
    unit:['percent','celsius','celsius','megabytes','megabytes','megahertz','watts','rpm'][i],
    value:state==='available'||id.endsWith('total_mb')?[0,53,56,1024,12272,100,35,0][i]:null,
    state:id.endsWith('total_mb')?'available':state,valid:id.endsWith('total_mb')||state==='available',stale:false,
    collected_at:s.generated_at,age_seconds:age,interval_seconds:id.endsWith('total_mb')?60:interval,data_kind:'real'})));
  return s;
}
function setup(){
  const f=fixture({gpu:true});f.host.start();
  f.emit({v:1,event:'ready',bridge_pid:1,collector_pid:2,transport:'windows_named_pipe_v1',simulated:false});
  f.send=s=>f.emit({v:1,event:'response',body:{ok:true,snapshot:s}});
  f.send(sample());f.host.setActive(false);f.advance(12000);f.host.setActive(true);return f;
}
const metric=(v,id='gpu.adlx.utilization')=>v.snapshot.metrics.find(m=>m.id===id);
const noGpuNumbers=v=>v.snapshot.metrics.filter(dynamic).every(m=>m.value===null&&!m.valid);
async function restore(){
  const f=setup();check(f.host.view().refreshing&&noGpuNumbers(f.host.view()),'Restore masks old readings');
  f.advance(2000);f.send(sample());
  check(!f.host.view().refreshing&&f.host.view().gpu_resume_state==='ready','New valid frame completes restore');
  check(metric(f.host.view()).valid&&metric(f.host.view()).value===0,'Valid GPU zero is not unavailable');
  f.host.setActive(false);f.advance(12000);f.host.setActive(true);
  for(let i=0;i<4;i++){
    f.advance(2000);f.send(sample({state:'error'}));
    check(f.host.view().refreshing&&noGpuNumbers(f.host.view()),'Repeated rejected readings keep updating before retry deadline');
    check(f.host.view().snapshot.metrics.filter(m=>!m.id.startsWith('gpu.')).every(m=>m.valid),'GPU error preserves current CPU, RAM and disks');
  }
  f.advance(2000);f.send(sample({state:'error'}));
  check(!f.host.view().refreshing&&f.host.view().gpu_resume_state==='unavailable','Persistent failure is explicit at 10 seconds, not successful refresh');
  check(noGpuNumbers(f.host.view()),'Persistent errors never convert null to zero');
  f.advance(2000);f.send(sample({state:'error'}));
  check(f.host.view().gpu_resume_state==='unavailable','Repeated errors do not restart retry deadline');
  f.advance(2000);f.send(sample());
  check(f.host.view().gpu_resume_state==='ready'&&metric(f.host.view()).valid,'Recovery after terminal unavailable needs fresh valid sample');
  check(f.host.diagnostics().childPid===123,'Recovery does not respawn owned child');
  await f.host.stop();check(f.child.exitCode===0&&f.timers.size===0,'Normal mocked cleanup');
}
async function unavailable(){
  for(const state of ['unsupported','unavailable','permission_denied','warming_up']){
    const f=setup();f.advance(2000);f.send(sample({state}));
    check(f.host.view().refreshing&&noGpuNumbers(f.host.view()),'No valid sample for '+state);
    f.advance(8000);f.send(sample({state}));
    check(f.host.view().gpu_resume_state==='unavailable'&&noGpuNumbers(f.host.view()),'Bounded wait for '+state);
    check(metric(f.host.view(),'gpu.adlx.vram_total_mb').valid,'Static capacity is not a dynamic recovery sample');
    await f.host.stop();
  }
  const first=setup(),ageNull=sample({state:'error',age:null});first.advance(2000);first.send(ageNull);
  check(first.host.view().refreshing&&noGpuNumbers(first.host.view()),'First age_null rejection represented as missing GPU reading');
  first.advance(2000);first.send(sample());check(!first.host.view().refreshing,'Next admitted frame recovers');await first.host.stop();
}
async function invalidAndPartial(){
  const f=setup();f.advance(2000);f.send(sample({age:2.1}));
  check(f.host.view().refreshing,'Pre-restore active sample cannot complete restore');
  f.send(sample({interval:10}));check(f.host.view().refreshing,'Inactive cached sample cannot complete active resume');
  f.send(sample({age:3}));check(f.host.view().refreshing,'Expired sample cannot complete restore');
  const partial=sample();for(const m of partial.metrics.filter(dynamic))if(m.id!=='gpu.adlx.temperature')m.age_seconds=2.1;
  f.send(partial);check(!f.host.view().refreshing&&metric(f.host.view(),'gpu.adlx.temperature').valid,'Partial new supported reading can complete GPU resume');
  check(metric(f.host.view()).value===null&&!metric(f.host.view()).valid,'Partial completion never exposes another pre-restore reading');
  f.advance(2000);f.send(sample());check(metric(f.host.view()).valid,'Individual old sensor replaced by new read');await f.host.stop();
  for(const change of [s=>s.generated_at='2099-01-01T00:00:00Z',s=>s.metrics.find(dynamic).value=NaN,
    s=>s.metrics.find(dynamic).age_seconds=Infinity,s=>s.metrics.find(dynamic).age_seconds=-1,
    s=>s.metrics.find(dynamic).ingress_age_seconds=1.500001]){
    const bad=setup();bad.advance(2000);const s=sample();change(s);bad.send(s);
    check(bad.host.view().connection==='disconnected'&&bad.host.view().refreshing,'Invalid temporal/value input fails closed, never completes resume');
    bad.advance(2000);bad.send(sample());check(bad.host.view().connection==='connected'&&!bad.host.view().refreshing,'Validated sample reconnects after invalid input');
    await bad.host.stop();
  }
}
async function ipc(){
  const f=setup();f.advance(2000);f.send(sample());
  f.emit({v:1,event:'disconnected'});const at=f.host.view();
  check(at.connection==='disconnected'&&at.refreshing,'Pipe loss starts a new bounded recovery');
  f.advance(1000);f.send(sample({age:2}));check(f.host.view().refreshing&&noGpuNumbers(f.host.view()),'Old cache on reconnect is not new data');
  f.advance(1000);f.send(sample({state:'error'}));check(f.host.view().refreshing,'IPC restored does not imply GPU restored');
  f.advance(2000);f.send(sample());check(!f.host.view().refreshing&&metric(f.host.view()).valid,'Fresh sample recovers same IPC child');
  check(f.host.diagnostics().childPid===123&&f.host.diagnostics().reconnections===1,'One child and one recovery');
  await f.host.stop();
  const timeout=setup();timeout.advance(10000);
  check(timeout.host.view().gpu_resume_state==='unavailable','Missing responses cannot leave updating forever');
  await timeout.host.stop();
}
async function modesAndRenderer(){
  const w=windowFixture(),first=w.win;w.controller.hideToTray();w.trays[0].emit('click');
  check(w.win===first&&w.win.visible,'Same window restored from tray');
  w.controller.setMode('widget');w.win.setBounds({x:90,y:50,width:390,height:720});w.pending();
  w.controller.setMode('dashboard');w.controller.setMode('widget');
  check(w.win.getBounds().width===390&&w.windows===1,'Widget resize and mode roundtrip preserve window');
  const f=setup(),r=rendererFixture();r.send(f.host.view());
  check(r.gpu.querySelector('.gpu-caption').textContent.includes('Atualizando'),'Renderer displays updating');
  check(r.minis[1].querySelector('strong').textContent==='—','Widget never shows old GPU zero');
  f.advance(2000);f.send(sample({state:'error'}));r.send(f.host.view());
  check(r.gpu.querySelector('.gpu-caption').textContent.includes('Atualizando'),'One error does not end renderer updating');
  f.advance(8000);f.send(sample({state:'error'}));r.send(f.host.view());
  check(r.gpu.querySelector('.gpu-caption').textContent.includes('GPU indisponível após retomada'),'Renderer explicitly reports persistent failure');
  check(r.cards[1].querySelector('small').textContent==='Indisponível'&&r.minis[1].querySelector('small').textContent==='Indisponível','Dashboard and widget agree on unavailable');
  check(r.cards[0].querySelector('.value').textContent==='0%'&&r.cards[2].querySelector('.value').textContent==='8,0 GiB','CPU and RAM remain real-contract values in fixtures');
  check(r.storage.querySelector('[data-volume="c"]').querySelector('[data-metric-id="storage.c.read_rate"]').querySelector('strong').textContent==='0 bytes/s','Storage valid zero unchanged');
  r.document.hidden=true;r.reset();f.advance(2000);f.send(sample());r.send(f.host.view());
  check(r.writes()===0,'No hidden DOM work');r.document.hidden=false;r.listeners.get('visibilitychange')();
  check(r.minis[1].querySelector('strong').textContent==='0%'&&r.gpu.querySelector('.gpu-caption').textContent.includes('Somente leitura'),'Visible dashboard/widget recover on valid sample');
  await f.host.stop();w.trays[0].menu[3].click();await new Promise(setImmediate);
  check(w.win.destroyed&&w.trays[0].destroyed,'Normal mock Sair still works');
}
(async()=>{await restore();await unavailable();await invalidAndPartial();await ipc();await modesAndRenderer();
  const report={ok:true,checks,failures:0,skipped:0,realSensors:false,realElectron:false,realProcesses:false,
    recoveryBudgetMs:10000,adlxIngressSeconds:1.5,displayActiveSeconds:3,displayInactiveSeconds:11};
  const out=(process.env.LONE_TEST_REPORT_ROOT?process.env.LONE_TEST_REPORT_ROOT:path.resolve(__dirname,'../.cache/validation/gpu-resume-fix-2026-10-26'));fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,'resume-tests.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
