'use strict';
// Session math only. No process access, capture library, injection, hooks or I/O.
((root,factory)=>{const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.loneGameSessions=api;})(globalThis,()=>{
 const finite=x=>typeof x==='number'&&Number.isFinite(x),stamp=x=>typeof x==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString().replace('.000Z','Z')===x.replace('.000Z','Z');
 const unavailable=()=>({v:1,session_id:null,game:'cs2',state:'not_started',source:'not_connected',simulation:false,started_at:null,ended_at:null,samples:0,rejected:0,
  fps:null,frametime_ms:null,average_fps:null,one_percent_low_fps:null,low_state:'unavailable',method:'frames_per_elapsed_time_and_mean_slowest_ceil_1_percent',semantic:'presented_frames',history:[]});
 function createSession({game='cs2',startedAt,simulation=false,maxFrames=60000,sessionId=globalThis.crypto.randomUUID().replaceAll('-','')}={}){
  if(game!=='cs2'||!stamp(startedAt)||typeof simulation!=='boolean'||!Number.isInteger(maxFrames)||maxFrames<100||maxFrames>120000||typeof sessionId!=='string'||!/^[a-f0-9]{32}$/.test(sessionId))throw Error('invalid_session');
  let frames=[],count=0,total=0,lastSequence=-1,lastMono=-Infinity,rejected=0,endedAt=null,limited=false;
  function record(frame){
   if(!simulation||endedAt||limited)return false; // Real source is intentionally NOT implemented/authorized.
   if(!frame||Object.keys(frame).sort().join(',')!=='frametime_ms,monotonic_seconds,sequence,v'||frame.v!==1||!Number.isSafeInteger(frame.sequence)||frame.sequence<=lastSequence||!finite(frame.monotonic_seconds)||frame.monotonic_seconds<0||frame.monotonic_seconds<=lastMono||!finite(frame.frametime_ms)||frame.frametime_ms<=0||frame.frametime_ms>60000){rejected++;return false;}
   if(count>=maxFrames){limited=true;return false;}
   frames.push([frame.monotonic_seconds,frame.frametime_ms]);count++;total+=frame.frametime_ms;lastSequence=frame.sequence;lastMono=frame.monotonic_seconds;return true;
  }
  function view(){
   if(!simulation)return {...unavailable(),session_id:sessionId,state:'source_unavailable',started_at:startedAt};
   const slowest=[...frames].map(f=>f[1]).sort((a,b)=>b-a).slice(0,Math.ceil(count*.01));
   const stride=Math.max(1,Math.ceil(count/120)),history=[];for(let i=0;i<count;i+=stride)history.push([...frames[Math.min(count-1,i+stride-1)]]);
   return {...unavailable(),session_id:sessionId,state:limited?'capacity_reached':endedAt?'finished':count?'capturing':'warming_up',source:'fixture.frames',simulation:true,started_at:startedAt,ended_at:endedAt,
    samples:count,rejected,frametime_ms:count?frames.at(-1)[1]:null,fps:count?1000/frames.at(-1)[1]:null,average_fps:count?1000*count/total:null,
    one_percent_low_fps:count>=100?1000/(slowest.reduce((a,b)=>a+b,0)/slowest.length):null,low_state:count>=100?'available':'warming_up',history};
  }
  function finish(when){if(!stamp(when)||Date.parse(when)<Date.parse(startedAt))throw Error('invalid_session_end');if(!endedAt)endedAt=when;return view();}
  return Object.freeze({record,view,finish});
 }
 function createArchive(limit=20){
  if(!Number.isInteger(limit)||limit<1||limit>20)throw Error('session_history_limit');let items=[];
  return Object.freeze({append(view){
   if(!view||view.v!==1||view.game!=='cs2'||view.simulation!==true||!['finished','capacity_reached'].includes(view.state)||!stamp(view.ended_at)||!Number.isInteger(view.samples)||view.samples<0||view.samples>120000||view.source!=='fixture.frames')throw Error('invalid_session_summary');
   if(typeof view.session_id!=='string'||!/^[a-f0-9]{32}$/.test(view.session_id)||!stamp(view.started_at)||Date.parse(view.started_at)>Date.parse(view.ended_at)||view.method!==unavailable().method||view.semantic!=='presented_frames'||!Number.isInteger(view.rejected)||view.rejected<0)throw Error('invalid_session_summary');
   for(const key of ['average_fps','one_percent_low_fps'])if(view[key]!==null&&(!finite(view[key])||view[key]<0))throw Error('invalid_session_summary');
   const allowed=['v','session_id','game','state','source','simulation','started_at','ended_at','samples','rejected','average_fps','one_percent_low_fps','method','semantic'];
   const summary=Object.fromEntries(allowed.map(k=>[k,view[k]]));
   if(JSON.stringify(summary).length>2048)throw Error('session_summary_limit');items=items.filter(s=>s.session_id!==view.session_id);items.push(summary);items=items.slice(-limit);
  },list:()=>JSON.parse(JSON.stringify({v:1,simulation:items.length>0,sessions:items}))});
 }
 return Object.freeze({createSession,createArchive,unavailable});
});
