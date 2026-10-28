'use strict';
// Main only. Fixed passive metadata script, no HTTP/Samsung identity/commands.
const path=require('node:path'),{spawn}=require('node:child_process'),model=require('./diagnostics-model.js');
function createProvider({root,enabled=false,spawnChild=spawn,now=Date.now,schedule=setTimeout,cancel=clearTimeout}={}){
 if(typeof enabled!=='boolean'||typeof root!=='string'||!path.isAbsolute(root))throw Error('evidence_configuration');
 let child=null,pending=null,cache=null,closed=false,last=-Infinity;
 function get(){
  if(!enabled||closed)return Promise.resolve(null);
  if(pending)return pending;
  const t=now();if(t>=last&&t-last<10000)return Promise.resolve(cache);last=t;cache=null;
  let resolve;const promise=new Promise(r=>{resolve=r;});pending=promise;
  let bytes=Buffer.alloc(0),invalid=false,timer;
  const finish=value=>{resolve(value);};
  try{
   child=spawnChild(path.join(root,'.venv/Scripts/python.exe'),['-I','-B',path.join(root,'scripts/desktop-agent-evidence.py')],
    {cwd:root,shell:false,windowsHide:true,env:{SystemRoot:process.env.SystemRoot||'C:\\Windows'},stdio:['ignore','pipe','ignore']});
   child.stdout.on('data',part=>{if(bytes.length+part.length>16385){invalid=true;bytes=Buffer.alloc(0);return;}if(!invalid)bytes=Buffer.concat([bytes,part]);});
   child.on('error',()=>{invalid=true;finish(null);});
   child.once('close',code=>{
    cancel(timer);child=null;pending=null;
    try{const report=JSON.parse(bytes.toString('utf8'));if(closed||invalid||code!==0||!model.validate(report,true))throw Error();cache=report;finish(structuredClone(report));}
    catch{finish(null);}
   });
   timer=schedule(()=>{invalid=true;cache=null;finish(null);},15000);timer?.unref?.();
  }catch{child=null;pending=null;finish(null);}
  // No kill on timeout. Keep pending child tracked; never start a duplicate.
  return promise;
 }
 async function stop(){closed=true;cache=null;if(!child)return true;
  const owned=child;return new Promise(resolve=>{let timer=schedule(()=>resolve(false),6500);owned.once('close',()=>{cancel(timer);resolve(true);});});}
 return Object.freeze({get,peek:()=>cache?structuredClone(cache):null,stop,
  stats:()=>({enabled,closed,workerActive:!!child,authenticatedHttp:false,repairs:false})});
}
module.exports={createProvider};
