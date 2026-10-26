'use strict';
// Pure mocks/fake clocks only. Never starts Electron, Python, sensors or a pipe.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {SessionPolicy}=require('./helpers/complementary-session-policy.cjs');
const {fixture:windowFixture}=require('./electron-tray.cjs');
const {fixture:hostFixture,snapshot}=require('./electron-monitoring.cjs');
const model=require('../apps/windows-ui/monitoring-model.js');
let checks=0;const check=(v,label)=>{assert(v,label);checks++;};
function sample(age=0,interval=2,state='available'){
  const s=snapshot();s.metrics.push(...model.gpuIds.map((id,i)=>({id,source:'amd.adlx',unit:['percent','celsius','celsius','megabytes','megabytes','megahertz','watts','rpm'][i],
    state,valid:state==='available',stale:false,value:state==='available'?[0,53,56,1000,12272,100,35,0][i]:null,
    collected_at:s.generated_at,age_seconds:age,interval_seconds:id.endsWith('total_mb')?60:interval,data_kind:'real'})));return s;
}
const gpu=s=>s.metrics.find(m=>m.id==='gpu.adlx.utilization');
function clockPolicy(){
  const p=new SessionPolicy(1000);
  check(p.decide(1000,5).newChecks,'Clock anchored at launch, not completion of tool call');
  check(!p.decide(1040,10).newChecks,'Operation that would consume exit reserve cannot start');
  check(p.decide(1045).requestNormalExit,'Normal exit is prioritized at 45 seconds');
  check(p.requestExit()&&!p.requestExit(),'One exit request, no launch retry');
  check(!p.decide(1060).newChecks,'No more checks after exit requested');
  check(p.finish({confirmedMonotonicSeconds:1090,ownedProcesses:0,ownedPipes:0,normalExit:true,checksComplete:true}),'Confirmed normal completion before cap can pass');
  for(const confirmed of [1120,1185,1324])check(!p.finish({confirmedMonotonicSeconds:confirmed,ownedProcesses:0,ownedPipes:0,normalExit:true,checksComplete:true}),'Late exit never passes');
  for(const bad of [{ownedProcesses:1,ownedPipes:0},{ownedProcesses:0,ownedPipes:1},{normalExit:false},{checksComplete:false}])
    check(!p.finish({confirmedMonotonicSeconds:1090,ownedProcesses:0,ownedPipes:0,normalExit:true,checksComplete:true,...bad}),'Partial cleanup or missing evidence fails');
  const blocked=new SessionPolicy(0);check(blocked.decide(80).phase==='exit_only','Delayed UI return cannot restart clock');
  blocked.requestExit();check(blocked.decide(121).phase==='expired'&&!blocked.decide(121).force,'Blocked normal exit expires without force');
  for(const now of [NaN,Infinity,-1])assert.throws(()=>new SessionPolicy(0).decide(now));checks+=3;
  const reversed=new SessionPolicy(0);reversed.decide(20);assert.throws(()=>reversed.decide(19));checks++;
}
function expiration(){
  for(const [interval,boundary]of [[2,3],[10,11]])for(const delta of [-.00001,0,.00001]){
    const m=gpu(model.normalize(sample(boundary+delta,interval),{gpu:true}));
    check(delta<0?m.valid&&!m.stale:!m.valid&&m.stale&&m.value===null,'Exact display boundary '+boundary+' '+delta);
  }
  const s=model.normalize(sample(),{gpu:true}),stamp=gpu(s).collected_at;
  check(gpu(model.age(s,3)).collected_at===stamp&&gpu(model.age(s,3)).value===null,'Old numeric data is not renewed by rendering');
  for(const state of ['unsupported','unavailable','error','warming_up']){
    const m=gpu(model.normalize(sample(0,2,state),{gpu:true}));check(m.value===null&&!m.valid&&model.format(m)==='—','Unavailable '+state+' is never zero');
  }
  check(model.format(gpu(s))==='0%','Real zero remains valid zero');
}
async function lifecycle(){
  let stopped=false,worker=true,pipe=true,lease=true,resolve,requests=0;
  const f=windowFixture({beforeExit:()=>{requests++;return new Promise(r=>resolve=r);}});
  const first=f.win;f.controller.hideToTray();check(!f.win.visible&&f.windows===1,'Tray hides one live window');
  f.trays[0].emit('click');check(f.win===first&&f.win.visible,'Tray restores same window');
  f.controller.setMode('widget');f.win.setBounds({x:90,y:50,width:390,height:720});f.pending();f.controller.setMode('dashboard');f.controller.setMode('widget');
  check(f.win.getBounds().width===390&&f.win.getBounds().height===720,'Widget resized bounds survive mode roundtrip');
  f.trays[0].menu[3].click();await Promise.resolve();f.trays[0].menu[3].click();
  check(requests===1&&!f.win.destroyed&&worker&&pipe&&lease,'Concurrent Sair waits for one owned cleanup');
  worker=false;pipe=false;lease=false;stopped=true;resolve(true);await new Promise(setImmediate);
  check(stopped&&!worker&&!pipe&&!lease&&f.quits===1&&f.win.destroyed&&f.trays[0].destroyed,'Only verified cooperative mock cleanup completes exit');
  const h=hostFixture({gpu:true});h.host.start();
  h.emit({v:1,event:'ready',bridge_pid:1,collector_pid:2,transport:'windows_named_pipe_v1',simulated:false});
  h.emit({v:1,event:'response',body:{ok:true,snapshot:sample()}});h.host.setActive(false);
  check([...h.periods.values()].join()==='10000','One inactive timer');h.advance(12000);h.host.setActive(true);
  check([...h.periods.values()].join()==='1000'&&h.host.view().refreshing,'One foreground timer and updating state');
  h.emit({v:1,event:'response',body:{ok:true,snapshot:sample(2,10)}});check(h.host.view().refreshing,'Pre-restore inactive data cannot clear updating');
  h.advance(2000);h.emit({v:1,event:'response',body:{ok:true,snapshot:sample(0)}});
  check(!h.host.view().refreshing&&gpu(h.host.view().snapshot).valid,'New active reading replaces old data');
  assert.throws(()=>h.host.start());checks++;check(await h.host.stop(),'Host finishes cooperative EOF');check(h.timers.size===0,'No mock timers remain');
}
(async()=>{clockPolicy();expiration();await lifecycle();const report={ok:true,checks,realProcesses:false,realSensors:false,realElectron:false,
  policyScope:'test_only_executable_spec_not_installed_or_operational',pipeReleaseScope:'fake_handles_and_existing_mock_pipe_regressions'};
  const out=path.resolve(__dirname,'../.cache/validation/dev6-complementary-plan-2026-10-26');fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,'plan-node-tests.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
