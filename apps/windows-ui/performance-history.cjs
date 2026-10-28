'use strict';
// Bounded, opt-in history owned by development main; no sensors or network.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const FIELDS=Object.freeze([
 ['cpu.utilization','percent','win32.systemtimes'],['gpu.adlx.utilization','percent','amd.adlx'],['gpu.adlx.temperature','celsius','amd.adlx'],
 ['ram.used','bytes','win32.memory'],['ram.utilization','percent','win32.memory'],
 ...['c','d'].flatMap(v=>[['occupation','percent'],['read_rate','bytes_per_second'],['write_rate','bytes_per_second'],['activity','percent']].map(([k,u])=>['storage.'+v+'.'+k,u,k==='occupation'?'win32.volume.'+v:'win32.pdh.logicaldisk']))]);
const STATES=['available','unavailable','stale','unsupported','error','warming_up','permission_denied'];
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const validValue=(v,u)=>finite(v)&&v>=(u==='celsius'?-273.15:0)&&v<=({percent:100,celsius:300,bytes:Number.MAX_SAFE_INTEGER,bytes_per_second:Number.MAX_SAFE_INTEGER}[u]);
function createHistory({enabled=false,directory=null,storageRoot=null,extended=false,now=Date.now,intervalMs=2000,retentionSeconds=3600,maxPoints=1800,maxBytes=2097152,flushMs=30000}={}){
 if(typeof enabled!=='boolean'||typeof extended!=='boolean'||!Number.isInteger(intervalMs)||intervalMs<1000||intervalMs>60000||!Number.isInteger(retentionSeconds)||retentionSeconds<300||retentionSeconds>(extended?604800:3600)||!Number.isInteger(maxPoints)||maxPoints<1||maxPoints>(extended?20000:3600)||!Number.isInteger(maxBytes)||maxBytes<4096||maxBytes>4194304||flushMs<30000)throw Error('invalid_history_policy');
 const owned=storageRoot!==null&&path.isAbsolute(storageRoot)&&directory!==null&&path.relative(storageRoot,directory)!==''&&!path.relative(storageRoot,directory).startsWith('..')&&!path.isAbsolute(path.relative(storageRoot,directory));
 if(directory!==null&&(!path.isAbsolute(directory)||!directory.includes(path.sep+'.cache'+path.sep)&&!owned))throw Error('development_history_directory');
 const windows=extended?[5,30,60,360,1440,10080]:[5,30,60];
 let rows=[],simulation=null,sequence=-1,generation=null,last=-Infinity,lastFlush=now(),dirty=false,closed=false,error=null,storageReadOnly=false;
 const filename=directory&&path.join(directory,'performance-history-v1.json');
 function safeDirectory(){
  if(!directory)return;
  let current=path.parse(directory).root;
  for(const part of path.relative(current,directory).split(path.sep)){
   current=path.join(current,part);
   if(fs.existsSync(current)){const s=fs.lstatSync(current);if(!s.isDirectory()||s.isSymbolicLink())throw Error('history_path_rejected');}
   else fs.mkdirSync(current);
  }
  if(fs.existsSync(filename)&&(!fs.lstatSync(filename).isFile()||fs.lstatSync(filename).isSymbolicLink()))throw Error('history_path_rejected');
 }
 const payload=()=>({v:1,simulation,fields:FIELDS,rows});
 function trim(t){rows=rows.filter(r=>r[0]<=t&&t-r[0]<=retentionSeconds*1000).slice(-maxPoints);}
 function flush(force=false){
  if(storageReadOnly||!enabled||closed||!filename||!dirty||!force&&now()-lastFlush<flushMs)return false;
  let temp,created=false;
  try{
   safeDirectory();trim(now());let bytes=JSON.stringify(payload());
   while(Buffer.byteLength(bytes)>maxBytes&&rows.length){rows.shift();bytes=JSON.stringify(payload());}
   if(Buffer.byteLength(bytes)>maxBytes)throw Error('history_size_limit');
   temp=path.join(directory,'.history-'+crypto.randomBytes(8).toString('hex')+'.tmp');
   fs.writeFileSync(temp,bytes,{flag:'wx',mode:0o600});created=true;fs.renameSync(temp,filename);created=false;
   dirty=false;lastFlush=now();error=null;return true;
  }catch{error='history_storage_unavailable';return false;}
  finally{if(created&&temp&&fs.existsSync(temp))fs.unlinkSync(temp);} // Only a file this operation successfully created.
 }
 function load(){
  if(!enabled||!filename)return;
  try{
   safeDirectory();if(!fs.existsSync(filename))return;
   if(fs.statSync(filename).size>maxBytes)throw Error();
   const p=JSON.parse(fs.readFileSync(filename,'utf8'));
   if(p.v!==1||typeof p.simulation!=='boolean'||JSON.stringify(p.fields)!==JSON.stringify(FIELDS)||!Array.isArray(p.rows)||p.rows.length>maxPoints)throw Error();
   let previous=-Infinity;
   for(const r of p.rows){
    if(!Array.isArray(r)||r.length!==FIELDS.length+2||!Number.isSafeInteger(r[0])||r[0]<=previous||!Number.isSafeInteger(r[1])||r[1]<0)throw Error();
    previous=r[0];
    for(let i=0;i<FIELDS.length;i++){
     const m=r[i+2];if(!Array.isArray(m)||m.length!==3||!STATES.includes(m[1])||m[2]!==null&&(!Number.isSafeInteger(m[2])||m[2]>r[0]))throw Error();
     if(m[1]==='available'?!validValue(m[0],FIELDS[i][1])||m[2]===null:m[0]!==null)throw Error();
    }
   }
   rows=p.rows;simulation=p.simulation;trim(now());
  }catch{rows=[];error='history_file_rejected';storageReadOnly=true;}
 }
 load();
 function record(view){
  if(!enabled||closed)return false;
  const s=view?.snapshot,t=now();
  if(view.connection!=='connected'||!s||s.schema_version!==1||typeof view.simulated!=='boolean'||s.contains_simulated!==view.simulated||!Number.isSafeInteger(s.sequence)||s.sequence<0||!Array.isArray(s.metrics)||s.metrics.length>29||!Number.isSafeInteger(t)||t-last<intervalMs)return false;
  if(simulation!==null&&simulation!==view.simulated){error='history_provenance_changed';return false;}
  const byId=new Map(s.metrics.map(m=>[m.id,m]));
  if(byId.size!==s.metrics.length)return false;
  const metricGeneration=view.history_generation??'owned-monitoring';
  if(generation===metricGeneration&&s.sequence<=sequence)return false;
  const row=[t,s.sequence];
  for(const [id,unit,source]of FIELDS){
   const m=byId.get(id),expected=view.simulated?(id.startsWith('gpu.')?'fixture.adlx':'fixture.metrics'):source;
   if(!m){row.push([null,'unavailable',null]);continue;}
   const timestamp=m.collected_at===null?null:Date.parse(m.collected_at);
   if(m.source!==expected||m.unit!==unit||!STATES.includes(m.state)||typeof m.valid!=='boolean'||typeof m.stale!=='boolean'||m.data_kind!==(view.simulated?'simulated':'real')||timestamp!==null&&(!Number.isSafeInteger(timestamp)||timestamp>t)||m.age_seconds!==null&&(!finite(m.age_seconds)||m.age_seconds<0))return false;
   const ttl=id.startsWith('gpu.')?m.interval_seconds+1:m.interval_seconds*3;
   const good=m.valid&&!m.stale&&m.state==='available'&&finite(m.age_seconds)&&m.age_seconds<ttl;
   if(good&&(!validValue(m.value,unit)||timestamp===null))return false;
   row.push([good?m.value:null,good?'available':m.state==='available'?'stale':m.state,timestamp]);
  }
  simulation=view.simulated;sequence=s.sequence;generation=metricGeneration;
  if(t<=last){error='history_clock_regression';return false;}
  rows.push(row);last=t;dirty=true;trim(t);flush();return true;
 }
 function query(minutes){
  if(!windows.includes(minutes))throw Error('invalid_history_window');
  if(!enabled||closed)return {v:1,state:'disabled',simulation:false,minutes,fields:FIELDS,rows:[]};
  const t=now();trim(t);const selected=rows.filter(r=>t-r[0]<=minutes*60000),stride=Math.max(1,Math.ceil(selected.length/120));
  // Keep the latest actual point of each bucket; no fabricated interpolation.
  const reduced=[];for(let i=0;i<selected.length;i+=stride)reduced.push(selected[Math.min(i+stride-1,selected.length-1)]);
  const value={v:1,state:rows.length?'available':'empty',simulation:simulation===true,minutes,fields:FIELDS,rows:reduced,error};
  if(Buffer.byteLength(JSON.stringify(value))>131072)throw Error('history_response_limit');
  return JSON.parse(JSON.stringify(value));
 }
 function exportCsv(minutes){
  if(!windows.includes(minutes))throw Error('invalid_history_window');
  const cell=require('./workbench-model.js').csvCell,t=now(),lines=[['timestamp_utc','sequence','simulation','metric','unit','source','value','state','collected_at'].map(cell).join(',')];let bytes=lines[0].length;
  if(enabled&&!closed)for(const row of rows.filter(r=>t-r[0]<=minutes*60000))for(let i=0;i<FIELDS.length;i++){
   const [id,unit,source]=FIELDS[i],m=row[i+2],line=[new Date(row[0]).toISOString(),row[1],simulation,id,unit,simulation?(id.startsWith('gpu.')?'fixture.adlx':'fixture.metrics'):source,m[0],m[1],m[2]===null?'':new Date(m[2]).toISOString()].map(cell).join(',');bytes+=Buffer.byteLength(line)+2;if(bytes>8388608)throw Error('history_csv_size_reduce_window');lines.push(line);
  }return lines.join('\r\n');
 }
 return Object.freeze({record,query,flush,exportCsv,close(){flush(true);closed=true;},stats:()=>({enabled,points:rows.length,maxPoints,maxBytes,retentionSeconds,error,dirty,closed,storageReadOnly})});
}
module.exports={createHistory,FIELDS};
