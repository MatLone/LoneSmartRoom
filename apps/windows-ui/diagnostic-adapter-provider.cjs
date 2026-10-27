'use strict';
// Development-only fixed mock adapter process. No real reader paths or agent identity.
const path=require('node:path'),{spawn}=require('node:child_process'),model=require('./diagnostics-model.js');
function createAdapterProvider({root,enabled=false,spawnChild=spawn,timeout=setTimeout,cancel=clearTimeout}={}){
 if(typeof enabled!=='boolean'||typeof root!=='string'||!path.isAbsolute(root))throw Error('invalid_mock_provider');
 let child=null,buffer=Buffer.alloc(0),pending=null,closed=false,attempted=false;
 function finish(error,value){if(!pending)return;const current=pending;pending=null;cancel(current.timer);error?current.reject(Error(error)):current.resolve(value);}
 function start(){
  if(attempted)return;attempted=true;
  child=spawnChild(path.join(root,'.venv/Scripts/python.exe'),['-I','-B',path.join(root,'scripts/diagnostic-adapter-worker.py')],
   {cwd:root,shell:false,windowsHide:true,env:{SystemRoot:process.env.SystemRoot||process.env.WINDIR||'C:\\Windows'},stdio:['pipe','pipe','ignore']});
  child.stdin.on('error',()=>finish('mock_worker_unavailable'));
  child.on('error',()=>finish('mock_worker_unavailable'));
  child.on('exit',()=>{closed=true;finish('mock_worker_closed');});
  child.stdout.on('data',chunk=>{
   if(buffer.length+chunk.length>24577){finish('mock_response_limit');stop();return;}
   buffer=Buffer.concat([buffer,chunk]);const end=buffer.indexOf(10);if(end<0)return;
   const line=buffer.subarray(0,end);buffer=buffer.subarray(end+1);
   try{
    const v=JSON.parse(line.toString('utf8'));
    if(buffer.length||!pending||v.v!==1||v.scenario!==pending.scenario||!model.adapterBundle(v.bundle))throw Error();
    finish(null,v.bundle);
   }catch{finish('mock_response_invalid');stop();}
  });
 }
 function get(scenario){
  if(!enabled||closed||!model.scenarios.includes(scenario))return Promise.reject(Error('mock_provider_disabled'));
  if(pending)return Promise.reject(Error('mock_provider_busy'));
  start();
  return new Promise((resolve,reject)=>{
   pending={resolve,reject,scenario,timer:timeout(()=>{finish('mock_provider_timeout');stop();},900)};
   child.stdin.write(JSON.stringify({v:1,scenario})+'\n');
  });
 }
 function stop(){closed=true;finish('mock_provider_closed');child?.stdin.end();}
 return Object.freeze({get,stop,stats:()=>({enabled,simulation:true,operationalReaders:false,started:attempted,closed,pending:!!pending})});
}
module.exports={createAdapterProvider};
