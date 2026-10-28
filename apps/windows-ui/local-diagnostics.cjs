'use strict';
// Consumes only the existing host cache. Does not probe agent, ports, Registry or sensors.
const model=require('./diagnostics-model.js'),contract=require('./diagnostics-contract.js');
function createLocalDiagnostics({metrics=()=>null,now=Date.now}={}){
 let last=-Infinity;
 function snapshot(query){
  const t=now(),generated=new Date(t).toISOString();
  const envelope=(error,report=null)=>({v:1,mode:'local',scenario:query?.scenario||'overview',error,report});
  if(!model.request(query)||query.scenario!=='overview')return envelope('disabled');
  if(t-last<500)return envelope('rate_limited');last=t;
  const unknown=(component,ttl)=>({component,state:'unknown',code:'not_observed',detail_code:null,evidence_kind:'local_cache',observed_at:null,age_seconds:null,valid:false,freshness_seconds:ttl,last_communication:null});
  let view;try{view=metrics();}catch{return envelope('provider_unavailable');}
  const gpuTtl=view?.snapshot?.metrics?.find(m=>m.id==='gpu.adlx.utilization')?.interval_seconds===10?11:3;
  const mode=gpuTtl===11?'inactive':'active';
  const checks=contract.components.map(id=>unknown(id,id==='agent_startup'?300:id==='monitoring_ipc'?5:id==='cpu_collector'||id==='ram_collector'?3:id==='gpu_collector'||id==='adlx_bridge'?gpuTtl:10));
  const byId=new Map(checks.map(c=>[c.component,c]));
  // Transport 'connected' is set only after the protected pipe client accepts v1.
  if(view&&!view.simulated){
   const pipe=byId.get('monitoring_ipc');
   if(view.connection==='connected'&&view.snapshot){Object.assign(pipe,{state:'healthy',code:'validated_ipc',observed_at:generated,age_seconds:0,valid:true});}
   else Object.assign(pipe,{state:'unavailable',code:'ipc_disconnected',detail_code:'pipe_disconnected',observed_at:generated,age_seconds:0});
   for(const [component,ids,detail]of [['cpu_collector',['cpu.utilization'],'metrics_valid'],['ram_collector',['ram.used','ram.total','ram.available','ram.utilization'],'metrics_valid'],['gpu_collector',['gpu.adlx.utilization'],'metrics_partial_support'],['adlx_bridge',['gpu.adlx.utilization'],'adlx_frame_valid']]){
    const row=byId.get(component),readings=ids.map(id=>view.snapshot?.metrics.find(m=>m.id===id));
    if(view.connection!=='connected'||readings.some(m=>!m)){Object.assign(row,{state:'unavailable',code:'component_not_running',detail_code:'metrics_missing'});continue;}
    const available=readings.every(m=>m.valid&&!m.stale&&m.value!==null&&m.data_kind==='real'&&Number.isFinite(m.age_seconds)&&m.age_seconds<row.freshness_seconds&&Number.isFinite(Date.parse(m.collected_at))&&Date.parse(m.collected_at)<=t);
    const stale=readings.some(m=>m.stale||m.state==='stale');
    if(available){const oldest=readings.map(m=>m.collected_at).sort()[0],age=(t-Date.parse(oldest))/1000;if(age<row.freshness_seconds)Object.assign(row,{state:'healthy',code:'valid_sample',detail_code:detail,observed_at:oldest,age_seconds:age,valid:true});else Object.assign(row,{state:'stale',code:'sample_stale',detail_code:'metrics_stale',observed_at:oldest,age_seconds:age});}
    else Object.assign(row,{state:stale?'stale':'unavailable',code:stale?'sample_stale':'provider_unavailable',detail_code:view.refreshing&&component.includes('gpu')?'awaiting_new_sample':stale?'metrics_stale':'metrics_missing'});
   }
  }
  const report={schema_version:1,generated_at:generated,mode,simulation:false,repair_capability:false,power_state:'unknown',checks};
  return model.validate(report,true)?envelope(null,report):envelope('invalid_report');
 }
 return Object.freeze({snapshot});
}
module.exports={createLocalDiagnostics};
