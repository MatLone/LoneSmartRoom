'use strict';
// Offline verification of the ONE newly authorized run; starts no network/sensors.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const model=require('../apps/android/app/src/main/assets/telemetry-model.js');
const folder=path.resolve(__dirname,'../.cache/telemetry-loopback-authorized-2026-10-27');
const result=JSON.parse(fs.readFileSync(path.join(folder,'real-transport-result.json')));
const started=Date.parse(result.receipt.started_at),origins=new Map();
for(const r of result.ipc_records||[])if(r.ok)origins.set(r.snapshot.sequence,r.snapshot);
const frames=[],failures=[],unique=new Map();let unavailable=0,zero=0,nulls=0;
for(const receipt of result.records||[]){
 let view;try{view=model.normalize(receipt.body,{transportSeconds:receipt.transport_seconds});}
 catch{failures.push('android_contract_rejected');continue;}
 if(!view.snapshot){unavailable++;continue;}
 const s=view.snapshot,origin=origins.get(s.sequence);
 if(!origin||origin.generated_at!==s.generated_at){failures.push('ipc_sequence_not_proven');continue;}
 const by=new Map(origin.metrics.map(m=>[m.id,m]));let proven=0;
 for(const m of s.metrics){
  if(m.value===null){nulls++;continue;}
  if(!m.valid||m.stale||m.data_kind!=='real'||Date.parse(m.collected_at)<started){failures.push('not_new_real_valid_sample');continue;}
  const o=by.get(m.id);
  if(!o||!o.valid||o.collected_at!==m.collected_at||o.unit!==m.unit||o.source!==m.source||o.value!==m.value){failures.push('metric_changed_between_ipc_and_android');continue;}
  if(!(m.age_seconds<m.expires_after_seconds)){failures.push('expired_at_client');continue;}
  proven++;if(m.value===0)zero++;
  unique.set(m.id+'|'+m.collected_at,{id:m.id,value:m.value,unit:m.unit,source:m.source,collected_at:m.collected_at,age_seconds:m.age_seconds,valid:m.valid,stale:m.stale});
 }
 frames.push({sequence:s.sequence,generated_at:s.generated_at,received_at:receipt.received_at,proven_metrics:proven});
}
const ids=new Set([...unique.values()].map(m=>m.id));
const required=['cpu.utilization','ram.total','ram.used','ram.available','storage.c.total','storage.d.total','gpu.adlx.utilization','gpu.adlx.temperature'];
// Actual Android card renderer, with only DOM/native I/O substituted. Playback
// retains the live-run timestamps/ages; it is NOT a new or currently live capture.
const nodes=new Map(model.ids.map(id=>[id,{dataset:{telemetry:id},textContent:'',title:'',parentElement:{matches:()=>false}}]));
let hidden=true,observer,timerId=0;const calls=[],timers=new Map(),label={},last={};
const document={hidden:false,getElementById:id=>id==='panel-monitor'?{hidden}:id==='telemetryState'?label:last,
 querySelectorAll:s=>s==='[data-telemetry]'?[...nodes.values()]:[],addEventListener:()=>{}};
const window={loneTelemetry:model,LoneAgent:{refreshTelemetry:id=>calls.push(id)}};
vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,'../apps/android/app/src/main/assets/telemetry-ui.js'),'utf8'),
 {window,document,performance:{now:()=>0},MutationObserver:class{constructor(cb){observer=cb;}observe(){}},
 setTimeout:(cb,ms)=>{const id=++timerId;timers.set(id,{cb,ms});return id;},clearTimeout:id=>timers.delete(id),setInterval:()=>0,Map,Date,Number,Math});
const frame=(result.records||[]).find(r=>r.body?.snapshot);
let cards=null;
if(frame){
 hidden=false;observer();window.onLoneTelemetry({...structuredClone(frame.body),request_id:calls.at(-1),transport_seconds:frame.transport_seconds});
 const expected=model.normalize(frame.body,{transportSeconds:frame.transport_seconds});
 for(const m of expected.snapshot.metrics)if(nodes.get(m.id).textContent!==model.format(m))failures.push('card_render_mismatch');
 cards={evidence_kind:'offline_render_of_same_live_session_response',currently_live:false,generated_at:frame.body.snapshot.generated_at,
  status:label.textContent,labels:Object.fromEntries([...nodes].map(([id,n])=>[id,n.textContent]))};
 hidden=true;observer();if(label.textContent!=='Consulta pausada')failures.push('polling_pause_failed');
}
const summary={v:1,live:true,simulated:false,client:'actual_Android_telemetry_model_in_Node_no_physical_Samsung',
 ok:failures.length===0&&required.every(id=>ids.has(id))&&frames.some(f=>f.proven_metrics>0),
 received_snapshots:frames.length,unavailable_responses:unavailable,unique_real_sensor_samples:unique.size,
 valid_zero_values:zero,null_values:nulls,failures:[...new Set(failures)],frames,metrics:[...unique.values()],cards};
fs.writeFileSync(path.join(folder,'android-client-proof.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({...summary,metrics:undefined,frames:undefined,cards:undefined}));
process.exitCode=summary.ok?0:1;
