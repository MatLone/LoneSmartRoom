'use strict';
// Owned local adapter; renderer cannot select a path, pipe, lifetime or request.
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process');
const model=require('./monitoring-model.js');
const runtime=require('./monitoring-runtime.cjs');
const MAX_LINE=132096;
// UI retry budget only; does not change ADLX admission or metric expiry.
const GPU_RESUME_WAIT_MS=10000;
function createMonitoringHost({root,runId,simulated=false,packaged=false,gpu=false,resourcesPath,version,resolveLayout,
  publish=()=>{},spawnChild=spawn,now=()=>performance.now(),
  interval=setInterval,clear=clearInterval,timeout=setTimeout,cancel=clearTimeout}) {
  if(!/^[a-f0-9]{32}$/.test(runId))throw Error('invalid_development_session');
  if(packaged&&simulated)throw Error('simulated_packaged_monitoring_forbidden');
  if(typeof gpu!=='boolean'||(gpu&&simulated))throw Error('gpu_real_owned_only');
  let active=true,quiet=false;
  let resumeAt=null,refreshing=false;
  let child=null,buffer=Buffer.alloc(0),timer=null,deadline=null,pending=false,closing=false,last=null,lastAt=0,requestAt=0;
  let status='connecting',error=null,stopPromise=null,stopResolve=null,startedAt=0,attempted=false,stopTimedOut=false;
  const lastValid=new Map(),diagnostics={bridgePid:null,collectorPid:null,childPid:null,responses:0,reconnections:0,cleanStop:false,workerExited:false};
  const dynamicGpu=m=>m.id.startsWith('gpu.adlx.')&&!m.id.endsWith('total_mb');
  const resumedSample=m=>dynamicGpu(m)&&m.valid&&!m.stale&&m.state==='available'&&
    m.interval_seconds===2&&m.age_seconds!==null&&now()-m.age_seconds*1000>=resumeAt;
  function view(){
    let snapshot=last?model.age(last,(now()-lastAt)/1000):null;
    const waiting=refreshing&&now()-resumeAt<GPU_RESUME_WAIT_MS;
    const gpuResumeState=!gpu?'disabled':refreshing?(waiting?'updating':'unavailable'):resumeAt===null?'idle':'ready';
    if(snapshot&&(refreshing||(gpu&&active&&resumeAt!==null)))snapshot={...snapshot,metrics:snapshot.metrics.map(m=>dynamicGpu(m)&&
      (refreshing||(active&&resumeAt!==null&&m.valid&&!resumedSample(m)))?
      {...m,value:null,valid:false,stale:false,state:refreshing&&!waiting?'unavailable':'warming_up'}:m)};
    return {v:1,connection:status,simulated,gpu_enabled:gpu,refreshing:waiting,gpu_resume_state:gpuResumeState,error,snapshot,last_valid_at:Object.fromEntries(lastValid)};
  }
  function send(){publish(view());}
  function fail(code){status='disconnected';error=code;pending=false;
    if(gpu&&active&&!refreshing){resumeAt=now();refreshing=true;}
    send();}
  function poll(){
    if(closing||!child||child.exitCode!==null)return;
    if(!diagnostics.bridgePid){if(now()-startedAt>10000){fail('launch_timeout');void stop();}return;}
    if(pending){if(now()-requestAt>1800)fail('read_timeout');return;}
    pending=true;requestAt=now();
    if(!child.stdin.write('{"v":1,"op":"snapshot"}\n'))fail('backpressure');
  }
  function onLine(line){
    let value;try{value=JSON.parse(line.toString('utf8'));}catch{return fail('invalid_transport');}
    if(!value||typeof value!=='object'||Array.isArray(value)||value.v!==1)return fail('invalid_transport');
    if(closing&&!['stopped','shutdown_pending'].includes(value.event))return;
    if(value.event==='ready'){
      if(diagnostics.bridgePid||!Number.isSafeInteger(value.bridge_pid)||value.bridge_pid<=0||!Number.isSafeInteger(value.collector_pid)||value.collector_pid<=0||
        value.transport!=='windows_named_pipe_v1'||value.simulated!==simulated)return fail('invalid_transport');
      diagnostics.bridgePid=value.bridge_pid;diagnostics.collectorPid=value.collector_pid;poll();return;
    }
    if(value.event==='response'){
      pending=false;
      if(!value.body?.ok)return fail(value.body?.error==='rate_limited'?'rate_limited':'read_unavailable');
      try{
        const snapshot=model.normalize(value.body.snapshot,{simulated,gpu});
        if(last&&snapshot.sequence<last.sequence)throw Error('sequence_regression');
        if(status==='disconnected')diagnostics.reconnections++;
        last=snapshot;lastAt=now();status='connected';error=null;diagnostics.responses++;
        if(refreshing&&snapshot.metrics.some(resumedSample))refreshing=false;
        for(const m of snapshot.metrics)if(m.valid)lastValid.set(m.id,m.collected_at);
        send();
      }catch{fail('invalid_metrics');}
    }else if(value.event==='stopped'){
      diagnostics.cleanStop=value.clean===true;status='stopped';error=value.clean?null:'stop_failed';
      diagnostics.workerExited=value.workerExited===true||value.worker?.stop?.stopped===true||value.clean===true;
      diagnostics.workerResult=value.worker;send();
    }else if(value.event==='shutdown_pending'){error='stop_pending';send();}
    else if(value.event==='disconnected'||value.event==='error')fail('local_read_unavailable');
  }
  function launch(){
    if(child||closing)throw Error('monitoring_already_started');
    const layout=resolveLayout?resolveLayout():packaged?runtime.bundledLayout(resourcesPath,version):runtime.sourceLayout(root);
    const {python,script,cwd}=layout;
    if(![python,script,cwd].every(p=>typeof p==='string'&&path.isAbsolute(p)))throw Error('invalid_runtime_layout');
    const args=['-I','-S','-B',script,'--session',runId,...(packaged?['--application','--owner-pid',String(process.pid)]:['--duration','70'])];
    if(simulated)args.push('--simulated');
    if(gpu)args.push('--gpu-development');
    const env={};for(const key of ['SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PATH'])if(process.env[key])env[key]=process.env[key];
    startedAt=now();
    child=spawnChild(python,args,{cwd,shell:false,windowsHide:true,env,stdio:['pipe','pipe','ignore']});
    diagnostics.childPid=child.pid;
    child.stdin.on('error',()=>{if(!closing)fail('local_read_unavailable');});
    child.stdout.on('data',chunk=>{
      if(buffer.length+chunk.length>MAX_LINE){fail('response_too_large');void stop();return;}
      buffer=Buffer.concat([buffer,chunk]);
      let end;while((end=buffer.indexOf(10))>=0){const line=buffer.subarray(0,end);buffer=buffer.subarray(end+1);onLine(line);}
    });
    child.on('error',()=>{fail('launch_failed');if(!child.pid){diagnostics.workerExited=true;diagnostics.cleanStop=true;}void stop();});
    child.on('exit',code=>{
      if(timer!==null)clear(timer);if(deadline!==null)cancel(deadline);timer=null;deadline=null;
      status='stopped';if(code!==0)error='stop_failed';send();stopResolve?.(diagnostics.workerExited);
    });
    timer=interval(poll,1000);if(!packaged)deadline=timeout(()=>{void stop();},72000);send();return view();
  }
  function start(){
    if(attempted||closing)throw Error('monitoring_already_started');
    attempted=true;
    try{return launch();}
    catch{diagnostics.workerExited=!child?.pid;fail('launch_failed');return view();}
  }
  function stop(){
    if(child?.exitCode!==null&&diagnostics.workerExited){
      if(!stopPromise||stopTimedOut){stopPromise=Promise.resolve(true);stopTimedOut=false;}
      return stopPromise;
    }
    if(stopPromise)return stopPromise;
    closing=true;if(timer!==null)clear(timer);if(deadline!==null)cancel(deadline);timer=null;deadline=null;
    stopPromise=new Promise(resolve=>{stopResolve=resolve;
      if(!child||!child.pid||child.exitCode!==null){resolve(!child||!child.pid||diagnostics.workerExited);return;}
      const limit=timeout(()=>{stopTimedOut=true;error='stop_timeout';send();resolve(false);},6500);limit?.unref?.();
      child.once('exit',()=>cancel(limit));
      child.stdin.end(); // Lifetime EOF only, no pipe/agent shutdown command.
    });return stopPromise;
  }
  function setActive(value){
    if(typeof value!=='boolean')throw Error('boolean_required');
    if(!gpu||active===value||closing)return;
    active=value;
    if(active){resumeAt=now();refreshing=true;send();}
    if(timer!==null){clear(timer);timer=interval(poll,active?(quiet?2000:1000):10000);}
    if(active)poll();
  }
  function setQuiet(value){if(typeof value!=='boolean')throw Error('boolean_required');quiet=value;if(timer!==null){clear(timer);timer=interval(poll,active?(quiet?2000:1000):10000);}}
  function resume(){
    if(!gpu||closing)return;
    resumeAt=now();refreshing=true;send();
    if(active)poll();else setActive(true);
  }
  return {start,stop,view,setActive,setQuiet,resume,diagnostics:()=>structuredClone(diagnostics)};
}
module.exports={createMonitoringHost,MAX_LINE};
