'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),model=require('../apps/android/app/src/main/assets/telemetry-model.js');
const raw=JSON.parse(fs.readFileSync(path.join(root,'.cache/telemetry-tests/https-frame.json'),'utf8'));
let checks=0;const ok=(x)=>{assert(x);checks++;},equal=(a,b)=>{assert.deepEqual(a,b);checks++;};
const view=model.normalize(raw,{simulation:true});equal(view.snapshot.metrics.length,29);
equal(model.format(view.snapshot.metrics.find(m=>m.id==='gpu.adlx.fan_rpm')),'0 RPM');
equal(model.format(view.snapshot.metrics.find(m=>m.id==='cpu.utilization')),'<0,1%');
equal(model.age(view,1000).snapshot.metrics.every(m=>m.value===null),true);
for(const edit of [r=>r.telemetry_version=2,r=>r.snapshot.metrics[0].value=NaN,r=>r.snapshot.metrics[0].source='private',r=>r.snapshot.metrics[0].unit='watts',r=>r.snapshot.metrics[0].age_seconds=-1,r=>r.snapshot.metrics.push(r.snapshot.metrics[0]),r=>r.snapshot.metrics[0].expires_after_seconds=100,r=>r.snapshot.contains_simulated=false]){
 const bad=structuredClone(raw);edit(bad);assert.throws(()=>model.normalize(bad,{simulation:true}));checks++;
}
assert.throws(()=>model.normalize(raw));checks++;
// Exercise actual polling/lifecycle renderer with a minimal DOM, deterministic clock and fixed native mock.
let now=0,hidden=true,observer,visibility,timerId=0;const timeouts=new Map(),calls=[];
const nodes=new Map(model.ids.map(id=>[id,{dataset:{telemetry:id},textContent:'',title:'',parentElement:{matches:()=>false}}]));
const status={textContent:''},last={textContent:''};
const document={hidden:false,getElementById:id=>id==='panel-monitor'?{hidden}:id==='telemetryState'?status:last,
 querySelectorAll:selector=>selector==='[data-telemetry]'?[...nodes.values()]:[],addEventListener:(n,cb)=>visibility=cb};
const simulationModel={...model,normalize:(r,o)=>model.normalize(r,{...o,simulation:true})};
const window={loneTelemetry:simulationModel,LoneAgent:{refreshTelemetry:id=>calls.push(id)}};
vm.runInNewContext(fs.readFileSync(path.join(root,'apps/android/app/src/main/assets/telemetry-ui.js'),'utf8'),{window,document,performance:{now:()=>now},MutationObserver:class{constructor(cb){observer=cb;}observe(){}},
 setTimeout:(cb,ms)=>{const id=++timerId;timeouts.set(id,{cb,ms});return id;},clearTimeout:id=>timeouts.delete(id),setInterval:()=>0,Map,Date,Math,Number});
equal(calls.length,0);hidden=false;observer();equal(calls.length,1);
const reply=()=>window.onLoneTelemetry({...structuredClone(raw),request_id:calls.at(-1),transport_seconds:0});reply();
equal(nodes.get('gpu.adlx.fan_rpm').textContent,'0 RPM');
hidden=true;observer();equal(status.textContent,'Consulta pausada');equal(nodes.get('gpu.adlx.fan_rpm').textContent,'Indisponível');
const oldcalls=calls.length;document.hidden=true;visibility();equal(calls.length,oldcalls);
hidden=false;document.hidden=false;visibility();reply();
equal(nodes.get('gpu.adlx.fan_rpm').textContent,'Indisponível'); // Same old timestamp is not current after resume.
const fresh=structuredClone(raw);fresh.snapshot.sequence++;fresh.snapshot.generated_at=new Date(Date.parse(fresh.snapshot.generated_at)+1000).toISOString();
for(const m of fresh.snapshot.metrics)m.collected_at=fresh.snapshot.generated_at;
const next=[...timeouts.values()].find(t=>t.ms===2000);ok(next);next.cb();window.onLoneTelemetry({...fresh,request_id:calls.at(-1),transport_seconds:0});
equal(nodes.get('gpu.adlx.fan_rpm').textContent,'0 RPM');
const {createTelemetryDevelopmentHost}=require('../apps/windows-ui/monitoring-telemetry-host.cjs');
assert.throws(()=>createTelemetryDevelopmentHost({root,runId:'a'.repeat(32),packaged:true}));checks++;
console.log(`PASS: ${checks} remote telemetry assertions; HTTPS fixture -> actual Android model/UI; no device or sensors`);
