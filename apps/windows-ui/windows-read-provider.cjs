'use strict';
// Fixed read-only helper and enum only. No shell, renderer script or arbitrary executable.
const path=require('node:path'),fs=require('node:fs'),os=require('node:os'),{execFile}=require('node:child_process');
const {INVENTORIES}=require('./workbench-service.cjs'),model=require('./workbench-model.js');
function createProvider({script=path.join(__dirname,'windows-inventory.ps1'),execute=execFile,now=Date.now,platform=process.platform}={}){
 let cache=new Map(),pending=null,lastNetwork=null;
 async function read(kind,target=''){
  if(![...INVENTORIES,'ping','dns'].includes(kind))throw Error('fixed_inventory_required');
  if(kind==='ping'||kind==='dns'){if(typeof target!=='string'||target.length>253||!/^[a-zA-Z0-9][a-zA-Z0-9.:-]*$/.test(target)||target.includes('..'))throw Error('invalid_target');}
  if(platform!=='win32')return {v:1,state:'unavailable',source:'unsupported_platform',items:[],simulation:false};
  const t=now(),key=kind+'|'+target;
  if(cache.has(key)&&t-cache.get(key).at<(['network'].includes(kind)?3000:15000))return structuredClone(cache.get(key).value);
  if(pending)return {v:1,state:'unavailable',source:'busy_readonly_provider',items:[],simulation:false};
  if(!path.isAbsolute(script)||!fs.existsSync(script)||fs.lstatSync(script).isSymbolicLink())throw Error('trusted_inventory_script_required');
  const system=process.env.SystemRoot||'C:\\Windows',program=path.join(system,'System32','WindowsPowerShell','v1.0','powershell.exe');
  const args=['-NoLogo','-NoProfile','-NonInteractive','-File',script,'-Kind',kind];if(target)args.push('-Target',target);
  pending=new Promise(resolve=>execute(program,args,{shell:false,windowsHide:true,encoding:'utf8',timeout:10000,maxBuffer:262144},(error,stdout)=>{
   // Timeout applies only to this helper we created, never a caller-supplied PID.
   if(error)return resolve({v:1,state:'unavailable',source:'windows.readonly.'+kind,items:[],error:
     error.killed===true||error.code==='ETIMEDOUT'?'readonly_timeout':error.code==='ERR_CHILD_PROCESS_STDIO_MAXBUFFER'?'readonly_response_limit':error.code==='ENOENT'?'readonly_helper_missing':'readonly_execution_failed',simulation:false});
   try{
    const v=JSON.parse(stdout.replace(/^\uFEFF/,''));if(v.v!==1||!['available','unavailable'].includes(v.state)||v.simulation!==false||v.source!=='windows.readonly.'+kind||!Array.isArray(v.items)||v.items.length>300||Buffer.byteLength(JSON.stringify(v))>262144)throw Error();
    if(Object.keys(v).some(k=>!['v','state','source','observed_at','items','extra','error','simulation'].includes(k)))throw Error();
    const clean=(value,depth=0)=>{if(depth>4)throw Error();if(value===null||typeof value==='boolean')return;if(typeof value==='number'){if(!Number.isFinite(value)||Math.abs(value)>Number.MAX_SAFE_INTEGER)throw Error();return;}if(typeof value==='string'){if(value.length>300||/[\x00-\x08\x0b-\x1f]/.test(value))throw Error();return;}if(Array.isArray(value)){if(value.length>300)throw Error();value.forEach(v=>clean(v,depth+1));return;}if(!value||typeof value!=='object'||Object.keys(value).length>30||Object.keys(value).some(k=>/password|secret|token|credential|command|private_key|certificate|^path$|^user$/i.test(k)))throw Error();Object.values(value).forEach(v=>clean(v,depth+1));};
    clean(v.items);if(v.extra)clean(v.extra);resolve(v);
   }catch{resolve({v:1,state:'unavailable',source:'invalid_readonly_response',items:[],simulation:false});}
  }));
  let value;try{value=await pending;}finally{pending=null;}
  if(kind==='network'&&value.state==='available'){
   const dt=lastNetwork?(t-lastNetwork.at)/1000:0;
   for(const item of value.items){const before=lastNetwork?.items.find(n=>n.name===item.name);
    item.download_bytes_per_second=before&&dt>0&&item.received_bytes>=before.received_bytes?(item.received_bytes-before.received_bytes)/dt:null;
    item.upload_bytes_per_second=before&&dt>0&&item.sent_bytes>=before.sent_bytes?(item.sent_bytes-before.sent_bytes)/dt:null;
   }lastNetwork={at:t,items:structuredClone(value.items)};
  }
  if(kind==='ping'&&value.state==='available')value.statistics=model.latency(value.items.filter(i=>i.status==='Success'&&Number.isFinite(i.rtt_ms)).map(i=>i.rtt_ms),4);
  cache.set(key,{at:t,value});if(cache.size>32)cache.delete(cache.keys().next().value);return structuredClone(value);
 }
 return Object.freeze({inventory:kind=>read(kind),network:(kind,target)=>read(kind,target),basic:()=>({v:1,state:'available',source:'node.os',observed_at:new Date(now()).toISOString(),simulation:false,platform:os.platform(),logical_cores:os.cpus().length,cpu_model:os.cpus()[0]?.model||null,total_ram_bytes:os.totalmem()})});
}
module.exports={createProvider};
