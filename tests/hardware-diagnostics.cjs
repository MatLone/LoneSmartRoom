'use strict';
// Synthetic snapshots only; the real collector is never started here.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const diagnostics=require('../apps/windows-ui/hardware-diagnostics.js');
const {snapshot,fixture}=require('./electron-monitoring.cjs');
const metricModel=require('../apps/windows-ui/monitoring-model.js');
let checks=0;const check=(value,label)=>{assert(value,label);checks++;};
const clone=x=>JSON.parse(JSON.stringify(x));
function view(simulated=false){return {v:1,connection:'connected',simulated,gpu_enabled:false,refreshing:false,
  gpu_resume_state:'disabled',error:null,snapshot:snapshot(simulated),last_valid_at:{}};}
const row=(v,id,options)=>diagnostics.project(v,options).rows.find(r=>r.id===id);
async function rendererTests(){
  class Element{
    constructor(){this.children=[];this.dataset={};this.events={};this.textContent='';this.open=false;}
    append(...children){this.children.push(...children);}
    addEventListener(name,fn){this.events[name]=fn;}
  }
  const ids=Object.fromEntries(['hardwareDiagnostics','hardwareDiagnosticRefresh','hardwareDiagnosticOrigin','hardwareDiagnosticRows'].map(id=>[id,new Element()]));
  let calls=0,reply=()=>Promise.resolve(view());
  const document={hidden:false,events:{},getElementById:id=>ids[id],createElement:()=>new Element(),
    addEventListener(name,fn){this.events[name]=fn;}};
  const window={events:{},loneHardwareDiagnostics:diagnostics,loneDesktop:{getMetrics:()=>{calls++;return reply();}},
    addEventListener(name,fn){this.events[name]=fn;}};
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,'../apps/windows-ui/hardware-diagnostics-renderer.js'),'utf8'),{window,document});
  const settle=async()=>{await Promise.resolve();await Promise.resolve();};
  const panel=ids.hardwareDiagnostics,button=ids.hardwareDiagnosticRefresh,origin=ids.hardwareDiagnosticOrigin,rows=ids.hardwareDiagnosticRows;
  check(calls===0&&rows.children.length===7,'Closed panel makes no IPC request and builds fixed groups');
  panel.open=true;panel.events.toggle();await settle();
  check(calls===1&&origin.textContent.includes('origem real'),'Open queries existing IPC once');
  check(origin.textContent.includes('consulta pontual')&&rows.children[0].children[1].textContent.includes('na consulta'),'Receipt identified as point-in-time, not live health');
  reply=()=>Promise.resolve(view(true));button.events.click();await settle();
  check(origin.textContent.includes('SIMULAÇÃO'),'Synthetic origins remain explicitly labelled');
  reply=()=>Promise.reject(Error('private message'));button.events.click();await settle();
  check(!origin.textContent.includes('private')&&rows.children[0].dataset.state==='unknown','Provider failure clears prior successful receipt without leaking errors');
  let finish;reply=()=>new Promise(resolve=>{finish=resolve;});button.events.click();
  check(button.disabled&&rows.children[0].dataset.state==='unknown','Pending query clears old evidence');
  panel.open=false;panel.events.toggle();finish(view());await settle();
  check(rows.children[0].dataset.state==='unknown'&&!button.disabled,'Closed panel ignores delayed response');
  document.hidden=true;panel.open=true;const before=calls;panel.events.toggle();
  check(calls===before,'Hidden document does not query');
  document.hidden=false;reply=()=>Promise.resolve(view());document.events.visibilitychange();await settle();
  check(rows.children[0].dataset.state==='available','Returning to visible open panel queries fresh view');
  document.hidden=true;document.events.visibilitychange();check(rows.children[0].dataset.state==='unknown','Hiding document clears evidence');
  document.hidden=false;reply=()=>new Promise(resolve=>{finish=resolve;});button.events.click();window.events.pagehide();finish(view());await settle();
  check(rows.children[0].dataset.state==='unknown','Page disposal ignores late response');
  // No timers, process, network or sensor APIs exist in this VM at all.
}
function withGpu(){
  const v=view();v.gpu_enabled=true;v.gpu_resume_state='idle';
  const stamp=v.snapshot.generated_at;
  const units=['percent','celsius','celsius','megabytes','megabytes','megahertz','watts','rpm'];
  v.snapshot.metrics.push(...metricModel.gpuIds.map((id,i)=>({id,source:'amd.adlx',unit:units[i],
    data_kind:'real',state:'available',valid:true,stale:false,value:id.endsWith('total_mb')?12000:0,
    collected_at:stamp,age_seconds:0,interval_seconds:id.endsWith('total_mb')?60:2})));
  return v;
}
async function main(){
  const v=view(),original=JSON.stringify(v),result=diagnostics.project(v);
  check(result.origin==='real'&&result.rows.length===7,'Seven groups from real-origin synthetic cache');
  check(row(v,'cpu').state==='available'&&row(v,'cpu').valid===1,'Zero CPU remains a valid sample');
  check(row(v,'ram').state==='available'&&row(v,'volume-c').state==='available','Full RAM and capacity groups');
  check(row(v,'gpu').state==='disabled','Disabled GPU does not certify hardware health');
  check(JSON.stringify(v)===original,'Projection never mutates shared cache');
  check(diagnostics.project(view(true)).origin==='simulated','Simulation provenance remains explicit');
  check(row(v,'cpu',{elapsedSeconds:3}).state==='stale','Exact CPU TTL expires');
  check(row(v,'volume-c',{elapsedSeconds:3}).state==='available','Capacity keeps its own TTL');
  check(row(v,'volume-c',{elapsedSeconds:180}).state==='stale','Capacity expires independently');
  check(diagnostics.project(v,{elapsedSeconds:2}).generatedAt===v.snapshot.generated_at,'Projection never renews timestamp');
  const partial=clone(v);partial.snapshot.metrics=partial.snapshot.metrics.filter(m=>m.id!=='ram.used');
  check(row(partial,'ram').state==='unknown','Missing group members cannot certify availability');
  for(const state of ['error','permission_denied','unsupported','unavailable','warming_up']){
    const x=clone(v);Object.assign(x.snapshot.metrics[0],{state,value:null,valid:false});
    check(row(x,'cpu').state===state,'Explicit nonavailable state: '+state);
  }
  const gpu=withGpu();check(row(gpu,'gpu').state==='available','Validated GPU zero RPM/utilization');
  check(row(gpu,'gpu',{elapsedSeconds:3}).state==='stale','GPU active TTL remains 3 seconds');
  gpu.refreshing=true;check(row(gpu,'gpu').state==='warming_up','Resume never displays available prematurely');
  check(row(gpu,'gpu').valid===0,'Resume does not count held GPU readings as currently usable');
  gpu.refreshing=false;gpu.gpu_resume_state='unavailable';
  check(row(gpu,'gpu').state==='unavailable','Resume timeout remains explicit');
  gpu.gpu_resume_state='ready';Object.assign(gpu.snapshot.metrics.at(-1),{state:'unsupported',valid:false,value:null});
  check(row(gpu,'gpu').state==='partial','Unsupported sensor kept separate from available');
  for(const m of gpu.snapshot.metrics.filter(m=>m.id.startsWith('gpu.')))Object.assign(m,{state:'unsupported',valid:false,value:null});
  check(row(gpu,'gpu').state==='unsupported','No supported GPU sensors is not success');
  for(const mutate of [x=>x.snapshot.metrics[0].source='private path',x=>x.snapshot.metrics[0].value=NaN,
    x=>x.snapshot.metrics.push(x.snapshot.metrics[0]),x=>x.snapshot.contains_simulated=true,
    x=>x.snapshot.metrics[0].data_kind='simulated',x=>x.snapshot.metrics[0].interval_seconds=.01,
    x=>x.snapshot.generated_at='2999-01-01T00:00:00Z',x=>x.snapshot.metrics[0].collected_at='2999-01-01T00:00:00Z',
    x=>x.extra='x'.repeat(65536),x=>x.gpu_enabled='yes',x=>x.refreshing=1,x=>x.error='arbitrary text']){
    const x=clone(v);mutate(x);check(diagnostics.project(x).rows.every(r=>r.state==='unknown'),'Malformed data rejected as a whole');
  }
  for(const elapsedSeconds of [-1,NaN,Infinity])check(diagnostics.project(v,{elapsedSeconds}).origin==='none','Invalid monotonic age rejected');
  const utf8=clone(v);utf8.extra='界'.repeat(22000);check(diagnostics.project(utf8).origin==='none','UTF-8 byte limit, not just character count');
  for(const connection of ['disabled','disconnected','connecting','stopped']){
    const x={...v,connection};check(diagnostics.project(x).rows.every(r=>r.valid===0),'Cached values unavailable after '+connection);
  }
  const host=fixture();host.host.start();
  host.emit({v:1,event:'ready',bridge_pid:1,collector_pid:2,transport:'windows_named_pipe_v1',simulated:false});
  host.emit({v:1,event:'response',body:{ok:true,snapshot:snapshot()}});
  check(row(host.host.view(),'cpu').state==='available','Existing host view accepted without another collector');
  host.advance(3000);check(row(host.host.view(),'cpu').state==='stale','Host ages measured cache');
  await host.host.stop();check(row(host.host.view(),'cpu').state==='unavailable','Stopped host cannot report valid current readings');
  const root=path.resolve(__dirname,'../apps/windows-ui'),pkg=JSON.parse(fs.readFileSync(path.join(root,'package.json')));
  check(pkg.build.files.includes('hardware-diagnostics.js'),'New projection packaged explicitly');
  const policy=require('../apps/windows-ui/desktop-policy.cjs'),{pathToFileURL}=require('node:url');
  check(policy.allowedResource(pathToFileURL(path.join(root,'hardware-diagnostics.js')).href),'Only fixed local module added to resource allowlist');
  await rendererTests();
  console.log(JSON.stringify({ok:true,checks,realSensors:false,operationalAgentAccess:false,newCollectors:0,newTimers:0}));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
