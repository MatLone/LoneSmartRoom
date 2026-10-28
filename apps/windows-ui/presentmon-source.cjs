'use strict';
// Read an explicitly selected external CSV. No ETW session, process, DLL or hook.
const fs=require('node:fs'),path=require('node:path'),model=require('./workbench-model.js');
function createSource({io=fs,now=Date.now,interval=setInterval,clear=clearInterval,publish=()=>{}}={}){
 let file=null,timer=null,baseline=0,stamp=null,report=null,state='inactive',fingerprint=null,lastSize=0;
 function read(){
  let current=path.parse(file).root;
  for(const part of path.relative(current,file).split(path.sep)){current=path.join(current,part);if(io.lstatSync(current).isSymbolicLink())throw Error('source_path');}
  const fd=io.openSync(file,'r');
  try{const s=io.fstatSync(fd);if(!s.isFile()||s.nlink!==1||s.size>2097152)throw Error('source_limit');
   const bytes=Buffer.alloc(s.size);let offset=0;while(offset<bytes.length){const n=io.readSync(fd,bytes,offset,bytes.length-offset,offset);if(!n)throw Error('source_changed');offset+=n;}
   const after=io.fstatSync(fd);if(after.size!==s.size||after.mtimeMs!==s.mtimeMs)throw Error('source_changed');
   const text=bytes.toString('utf8'),end=text.lastIndexOf('\n');
   const rows=model.csvRows(end>=0?text.slice(0,end+1):'');
   if(!rows.length||!rows[0].some(v=>/^[Mm]sBetweenPresents$/.test(v)))throw Error('unsupported_csv');
   return {rows,size:s.size};
  }finally{io.closeSync(fd);}
 }
 const csv=rows=>rows.map(r=>r.map(v=>'"'+v.replaceAll('"','""')+'"').join(',')).join('\n')+'\n';
 function view(){const age=stamp===null?null:Math.max(0,(now()-stamp)/1000),fresh=state==='available'&&age<=3;
  return {v:1,source:'presentmon_external_csv',capture_started_by_lsr:false,live_game_verified:false,
   state:state==='available'&&!fresh?'stale':state,observed_at:stamp===null?null:new Date(stamp).toISOString(),age_seconds:age,
   report:fresh?structuredClone(report):null,method:'Only complete rows appended after attachment; presented FPS, not displayed FPS.'};}
 function poll(){if(!file)return;
  try{const input=read();if(input.size<lastSize||input.rows.length-1<baseline){baseline=input.rows.length-1;stamp=null;report=null;fingerprint=null;state='awaiting_frames';}
   lastSize=input.size;const fresh=input.rows.slice(baseline+1);
   if(fresh.length){const next=model.presentmon(csv([input.rows[0],...fresh]));
    const id=JSON.stringify(next.streams);if(next.streams.length&&id!==fingerprint){report=next;stamp=now();fingerprint=id;state='available';}}
  }catch{state='unavailable';report=null;}
  publish(view());
 }
 function stop(){if(timer!==null)clear(timer);timer=null;file=null;state='inactive';stamp=null;report=null;publish(view());}
 function attach(selected){if(typeof selected!=='string'||!path.isAbsolute(selected)||path.extname(selected).toLowerCase()!=='.csv')throw Error('source_path');
  stop();file=selected;
  try{const input=read();baseline=input.rows.length-1;lastSize=input.size;fingerprint=null;state='awaiting_frames';timer=interval(poll,1000);timer?.unref?.();publish(view());return view();}
  catch{stop();throw Error('presentmon_source_rejected');}
 }
 return Object.freeze({attach,stop,view,poll,finish(){const final=report;stop();return final;}});
}
module.exports={createSource};
