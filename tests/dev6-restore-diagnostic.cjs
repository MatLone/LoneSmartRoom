'use strict';
// Regression originally exposed by exploratory acceptance; no expected-failure masking.
const fs=require('node:fs'),path=require('node:path');
const {fixture,snapshot}=require('./electron-monitoring.cjs');
const model=require('../apps/windows-ui/monitoring-model.js');
function sample(state='available'){
  const s=snapshot();s.metrics.push(...model.gpuIds.map((id,i)=>({id,source:'amd.adlx',unit:['percent','celsius','celsius','megabytes','megabytes','megahertz','watts','rpm'][i],
    value:state==='available'?[0,53,56,1024,12272,100,35,0][i]:null,state,valid:state==='available',stale:false,
    collected_at:s.generated_at,age_seconds:0,interval_seconds:id.endsWith('total_mb')?60:2,data_kind:'real'})));return s;
}
(async()=>{
  const f=fixture({gpu:true});f.host.start();f.emit({v:1,event:'ready',bridge_pid:1,collector_pid:2,transport:'windows_named_pipe_v1',simulated:false});
  f.emit({v:1,event:'response',body:{ok:true,snapshot:sample()}});f.host.setActive(false);f.advance(12000);f.host.setActive(true);
  f.advance(2000);f.emit({v:1,event:'response',body:{ok:true,snapshot:sample('error')}});
  const v=f.host.view(),gpu=v.snapshot.metrics.filter(m=>m.id.startsWith('gpu.')&&!m.id.endsWith('total_mb'));
  const cases=[{id:'restore_keeps_updating_after_invalid_new_read',expected:true,actual:v.refreshing},
    {id:'invalid_new_read_never_leaks_numeric_gpu_values',expected:true,actual:gpu.every(m=>m.value===null&&!m.valid)}];
  f.advance(2000);f.emit({v:1,event:'response',body:{ok:true,snapshot:sample()}});
  cases.push({id:'next_valid_frame_restores_values_without_respawn',expected:true,actual:!f.host.view().refreshing&&f.host.view().snapshot.metrics.some(m=>m.id==='gpu.adlx.utilization'&&m.valid)});
  await f.host.stop();const failures=cases.filter(c=>c.actual!==c.expected);
  const result={ok:failures.length===0,checks:cases.length,failures:failures.length,cases,realProcesses:false,realSensors:false,
    classification:'strict_restore_state_acceptance_not_a_numeric_data_leak',installedApplicationModified:false,developmentHostUnderTest:true};
  const out=path.resolve(__dirname,'../.cache/validation/dev6-complementary-plan-2026-10-26');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'restore-diagnostic.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));process.exitCode=failures.length?1:0;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
