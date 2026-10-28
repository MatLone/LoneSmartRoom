'use strict';
// Fake clocks, process objects and DOM only. No Electron, pipe or native DLL runs.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const model=require('../apps/windows-ui/monitoring-model.js');
const {fixture,snapshot}=require('./electron-monitoring.cjs');
const {rendererFixture}=require('./helpers/monitoring-dom.cjs');
let checks=0;const check=(v,label)=>{assert(v,label);checks++;};
function sample(age=0,interval=2){
  const s=snapshot(),values=[.01,53,56,1024,12272,100,35,0];
  s.metrics.push(...model.gpuIds.map((id,i)=>({id,source:'amd.adlx',unit:['percent','celsius','celsius','megabytes','megabytes','megahertz','watts','rpm'][i],
    value:values[i],state:'available',valid:true,stale:false,data_kind:'real',collected_at:s.generated_at,age_seconds:age,
    interval_seconds:id.endsWith('total_mb')?60:interval,...(id.endsWith('total_mb')?{}:{ingress_age_seconds:.5,information_age_seconds:age+.5})})));
  return s;
}
function gpu(s){return s.metrics.find(m=>m.id==='gpu.adlx.utilization');}
function freshness(){
  for(const [interval,limit]of [[2,3],[10,11]]){
    const m=gpu(model.normalize(sample(2.69,interval),{gpu:true}));
    check(m.valid&&m.age_seconds===2.69&&m.information_age_seconds===3.19,'Admission and cache information ages explicitly distinct');
    check(m.display_limit_seconds===limit,'Display limit = cadence + one foreground UI tick');
    check(gpu(model.normalize(sample(limit-.001,interval),{gpu:true})).valid,'Immediately before display deadline');
    const expired=gpu(model.normalize(sample(limit,interval),{gpu:true}));
    check(!expired.valid&&expired.stale&&expired.value===null,'At deadline becomes stale, never old current number');
  }
  const original=model.normalize(sample(),{gpu:true}),aged=model.age(original,3);
  check(gpu(aged).state==='stale'&&gpu(aged).information_age_seconds===3.5,'Both host and renderer apply display expiry');
  check(gpu(aged).collected_at===gpu(original).collected_at,'Aging never renews timestamps');
  for(const bad of [null,-.1,1.50001,Infinity,NaN]){
    const s=sample();gpu(s).ingress_age_seconds=bad;assert.throws(()=>model.normalize(s,{gpu:true}));checks++;
  }
  const inconsistent=sample();gpu(inconsistent).information_age_seconds=123;assert.throws(()=>model.normalize(inconsistent,{gpu:true}));checks++;
  const legacy=sample();for(const m of legacy.metrics){delete m.ingress_age_seconds;delete m.information_age_seconds;}
  check(gpu(model.normalize(legacy,{gpu:true})).ingress_age_seconds===undefined,'Additive v1 metadata remains backward compatible');
  check(!gpu(model.age(original,NaN)).valid,'Invalid elapsed time fails closed');
}
async function lifecycle(){
  const root=path.resolve(__dirname,'..');
  const f=fixture({gpu:true,packaged:true,version:'2.0.0-dev.6',resolveLayout:()=>({python:path.join(root,'fixture.exe'),script:path.join(root,'fixture.py'),cwd:root})});
  f.host.start();
  const args=f.args()[1];
  check(args.includes('--application')&&args.includes('--gpu-development')&&!args.includes('--duration'),'Fixed owned packaged GPU launch, no development TTL');
  f.emit({v:1,event:'ready',bridge_pid:123,collector_pid:124,transport:'windows_named_pipe_v1',simulated:false});
  const emit=s=>f.emit({v:1,event:'response',body:{ok:true,snapshot:s}});
  emit(sample());f.host.setActive(false);check([...f.periods.values()].join()==='10000','One inactive polling timer');
  f.advance(30000);emit(sample(9,10));f.host.setActive(true);
  check(f.host.view().refreshing&&gpu(f.host.view().snapshot).value===null,'Restore holds old inactive reading as updating, not current');
  emit(sample(8,10));check(f.host.view().refreshing,'Inactive sample cannot satisfy foreground refresh');
  f.advance(2000);emit(sample(.1));
  check(!f.host.view().refreshing&&gpu(f.host.view().snapshot).valid,'New post-restore active frame clears updating');
  for(let i=0;i<500;i++){f.advance(1000);const s=sample(.1);s.sequence=i+2;emit(s);}
  check(f.host.view().connection==='connected'&&f.host.diagnostics().responses===504,'Long mocked lifecycle exceeds 82 seconds / 45 requests');
  f.emit({v:1,event:'disconnected'});check(f.host.view().connection==='disconnected','Pipe loss visible');
  const recovered=sample();recovered.sequence=999;emit(recovered);
  check(f.host.diagnostics().reconnections===1,'Reconnect same owned worker');
  const invalid=sample();invalid.sequence=1000;gpu(invalid).value=NaN;emit(invalid);
  check(f.host.view().connection==='disconnected','Malformed metrics never shown as connected');
  const fail=sample();fail.sequence=1001;for(const m of fail.metrics.filter(m=>m.id.startsWith('gpu.')))Object.assign(m,{value:null,valid:false,state:'error',ingress_age_seconds:undefined,information_age_seconds:undefined});
  emit(fail);check(f.host.view().snapshot.metrics[0].valid&&gpu(f.host.view().snapshot).value===null,'GPU failure does not poison basic metrics');
  assert.throws(()=>f.host.start());checks++;
  check(await f.host.stop(),'Cooperative EOF with actual mocked completion');
  check(f.child.exitCode===0&&f.timers.size===0,'No timers or mocked residual processes');
  check(f.child.requests.every(r=>r==='{"v":1,"op":"snapshot"}\n'),'Only fixed read request, no renderer-selected controls');
}
function renderer(){
  const f=rendererFixture(),s=model.normalize(sample(2.69),{gpu:true});
  f.send({v:1,connection:'connected',gpu_enabled:true,snapshot:s,last_valid_at:{}});
  check(f.cards[1].querySelector('.value').textContent==='<0,1%','Tiny real positive stays distinguishable from zero');
  const meta=f.cards[1].querySelector('.metric-meta p').textContent;
  check(meta.includes('cache')&&meta.includes('idade no ingresso')&&meta.includes('idade da informação')&&meta.includes('cadência'),'Visible provenance explains timing');
  f.send({v:1,connection:'connected',gpu_enabled:true,refreshing:true,snapshot:s,last_valid_at:{}});
  check(f.gpu.querySelector('.gpu-caption').textContent.includes('Atualizando'),'Explicit foreground updating message');
  f.document.hidden=true;f.reset();f.tick();check(f.writes()===0,'No hidden DOM polling work');
}
(async()=>{freshness();await lifecycle();renderer();const report={ok:true,checks,realSensors:false,realElectron:false,generatedExecutablesRun:false};
  const out=(process.env.LONE_TEST_REPORT_ROOT?process.env.LONE_TEST_REPORT_ROOT:path.resolve(__dirname,'../.cache/validation/windows-dev6'));fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,'dev6-node-tests.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
