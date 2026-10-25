'use strict';
// Development-only fixed Python adapter; renderer cannot select a path, pipe or request.
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process');
const model=require('./monitoring-model.js');
const MAX_LINE=132096;
function createMonitoringHost({root,runId,simulated=false,publish=()=>{},spawnChild=spawn,now=()=>performance.now(),
  interval=setInterval,clear=clearInterval,timeout=setTimeout,cancel=clearTimeout}) {
  if(!/^[a-f0-9]{32}$/.test(runId))throw Error('invalid_development_session');
  let child=null,buffer=Buffer.alloc(0),timer=null,deadline=null,pending=false,closing=false,last=null,lastAt=0,requestAt=0;
  let status='connecting',error=null,stopPromise=null,stopResolve=null;
  const lastValid=new Map(),diagnostics={bridgePid:null,collectorPid:null,childPid:null,responses:0,reconnections:0,cleanStop:false};
  function view(){return {v:1,connection:status,simulated,error,snapshot:last?model.age(last,(now()-lastAt)/1000):null,
    last_valid_at:Object.fromEntries(lastValid)};}
  function send(){publish(view());}
  function fail(code){status='disconnected';error=code;pending=false;send();}
  function poll(){
    if(closing||!child||child.exitCode!==null)return;
    if(pending){if(now()-requestAt>1800)fail('read_timeout');return;}
    pending=true;requestAt=now();
    if(!child.stdin.write('{"v":1,"op":"snapshot"}\n'))fail('backpressure');
  }
  function onLine(line){
    let value;try{value=JSON.parse(line.toString('utf8'));}catch{return fail('invalid_transport');}
    if(value.v!==1)return fail('invalid_transport');
    if(value.event==='ready'){
      if(diagnostics.bridgePid||!Number.isSafeInteger(value.bridge_pid)||!Number.isSafeInteger(value.collector_pid)||
        value.transport!=='windows_named_pipe_v1'||value.simulated!==simulated)return fail('invalid_transport');
      diagnostics.bridgePid=value.bridge_pid;diagnostics.collectorPid=value.collector_pid;poll();return;
    }
    if(value.event==='response'){
      pending=false;
      if(!value.body?.ok)return fail(value.body?.error==='rate_limited'?'rate_limited':'read_unavailable');
      try{
        const snapshot=model.normalize(value.body.snapshot,{simulated});
        if(last&&snapshot.sequence<last.sequence)throw Error('sequence_regression');
        if(status==='disconnected')diagnostics.reconnections++;
        last=snapshot;lastAt=now();status='connected';error=null;diagnostics.responses++;
        for(const m of snapshot.metrics)if(m.valid)lastValid.set(m.id,m.collected_at);
        send();
      }catch{fail('invalid_metrics');}
    }else if(value.event==='stopped'){
      diagnostics.cleanStop=value.clean===true;status='stopped';error=value.clean?null:'stop_failed';
      diagnostics.workerResult=value.worker;send();
    }else if(value.event==='disconnected'||value.event==='error')fail('local_read_unavailable');
  }
  function start(){
    if(child||closing)throw Error('monitoring_already_started');
    const config=fs.readFileSync(path.join(root,'.venv','pyvenv.cfg'),'utf8');
    const home=/^home\s*=\s*(.+)$/m.exec(config)?.[1]?.trim();
    if(!home||!path.isAbsolute(home))throw Error('python_environment_unavailable');
    const python=fs.realpathSync(path.join(home,'python.exe'));
    if(!fs.statSync(python).isFile())throw Error('python_environment_unavailable');
    const args=['-I','-B',path.join(root,'scripts','monitoring-pipe-client.py'),'--session',runId,'--duration','70'];
    if(simulated)args.push('--simulated');
    const env={};for(const key of ['SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PATH'])if(process.env[key])env[key]=process.env[key];
    child=spawnChild(python,args,{cwd:root,shell:false,windowsHide:true,env,stdio:['pipe','pipe','ignore']});
    diagnostics.childPid=child.pid;
    child.stdin.on('error',()=>{if(!closing)fail('local_read_unavailable');});
    child.stdout.on('data',chunk=>{
      if(buffer.length+chunk.length>MAX_LINE){fail('response_too_large');void stop();return;}
      buffer=Buffer.concat([buffer,chunk]);
      let end;while((end=buffer.indexOf(10))>=0){const line=buffer.subarray(0,end);buffer=buffer.subarray(end+1);onLine(line);}
    });
    child.on('error',()=>{fail('launch_failed');void stop();});
    child.on('exit',code=>{
      if(timer!==null)clear(timer);if(deadline!==null)cancel(deadline);timer=null;deadline=null;
      status='stopped';if(code!==0)error='stop_failed';send();stopResolve?.(diagnostics.cleanStop&&code===0);
    });
    timer=interval(poll,1000);deadline=timeout(()=>{void stop();},72000);send();return view();
  }
  function stop(){
    if(stopPromise)return stopPromise;
    closing=true;if(timer!==null)clear(timer);if(deadline!==null)cancel(deadline);timer=null;deadline=null;
    stopPromise=new Promise(resolve=>{stopResolve=resolve;
      if(!child||child.exitCode!==null){resolve(!child||diagnostics.cleanStop);return;}
      child.stdin.end(); // Lifetime EOF only, no pipe/agent shutdown command.
      const limit=timeout(()=>{error='stop_timeout';send();resolve(false);},6500);limit?.unref?.();
      child.once('exit',()=>cancel(limit));
    });return stopPromise;
  }
  return {start,stop,view,diagnostics:()=>structuredClone(diagnostics)};
}
module.exports={createMonitoringHost,MAX_LINE};
