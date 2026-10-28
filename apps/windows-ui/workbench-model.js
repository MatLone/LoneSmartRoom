'use strict';
((root,factory)=>{const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.loneWorkbenchModel=api;})(globalThis,()=>{
 const finite=n=>typeof n==='number'&&Number.isFinite(n);
 function latency(values,attempts){
  if(!Array.isArray(values)||values.length>32||!Number.isInteger(attempts)||attempts<1||attempts>32||values.length>attempts||values.some(n=>!finite(n)||n<0||n>60000))throw Error('invalid_latency');
  const diffs=values.slice(1).map((n,i)=>Math.abs(n-values[i]));
  return {v:1,received:values.length,sent:attempts,loss_percent:100*(attempts-values.length)/attempts,min_ms:values.length?Math.min(...values):null,mean_ms:values.length?values.reduce((a,b)=>a+b,0)/values.length:null,max_ms:values.length?Math.max(...values):null,jitter_ms:diffs.length?diffs.reduce((a,b)=>a+b,0)/diffs.length:null,method:'mean_absolute_successive_rtt_difference'};
 }
 function createInputSession({maxEvents=2000,doubleClickMs=250}={}){
  if(!Number.isInteger(maxEvents)||maxEvents<10||maxEvents>5000||!finite(doubleClickMs)||doubleClickMs<50||doubleClickMs>1000)throw Error('invalid_input_policy');
  let events=[],pressed=new Set(),keys=new Set(),lastClick=null,doubles=0,moves=0,intervals=[],lastMove=null;
  return Object.freeze({record(e){
   if(!e||!['down','up','move','click'].includes(e.type)||!finite(e.at)||e.at<0||events.length>=maxEvents||events.length&&e.at<events.at(-1).at)return false;
   if(e.type==='down'||e.type==='up'){if(typeof e.code!=='string'||!/^\w{1,32}$/.test(e.code))return false;keys.add(e.code);if(e.type==='down')pressed.add(e.code);else pressed.delete(e.code);}
   if(e.type==='click'){if(lastClick!==null&&e.at-lastClick<=doubleClickMs)doubles++;lastClick=e.at;}
   if(e.type==='move'){moves++;if(lastMove!==null&&e.at>lastMove)intervals.push(e.at-lastMove);lastMove=e.at;}
   events.push({type:e.type,at:e.at,code:e.code||null});return true;
  },view(){return {v:1,events:events.length,pressed:[...pressed],keys:[...keys],possible_double_clicks:doubles,moves,mean_browser_event_interval_ms:intervals.length?intervals.reduce((a,b)=>a+b,0)/intervals.length:null,hardware_polling_rate_hz:null,hardware_latency_ms:null,method:'browser_events_only_not_hardware_measurement'};}});
 }
 function csvRows(text){
  if(typeof text!=='string'||text.length>8388608)throw Error('csv_limit');
  let rows=[],row=[],field='',quoted=false;
  for(let i=0;i<text.length;i++){
   const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++;}else if(!field||quoted)quoted=!quoted;else throw Error('csv_quote');}
   else if(!quoted&&(c===','||c==='\n'||c==='\r')){row.push(field);field='';if(c!==','){if(c==='\r'&&text[i+1]==='\n')i++;if(row.some(Boolean))rows.push(row);row=[];if(rows.length>120001)throw Error('csv_rows');}}
   else field+=c;
  }
  if(quoted)throw Error('csv_quote');if(field||row.length){row.push(field);rows.push(row);}return rows;
 }
 function presentmon(text){
  const rows=csvRows(text);if(rows.length<2)throw Error('csv_empty');const header=rows.shift().map(s=>s.trim().replace(/^\uFEFF/,''));
  const index=header.indexOf('MsBetweenPresents')>=0?header.indexOf('MsBetweenPresents'):header.indexOf('msBetweenPresents');
  if(index<0)throw Error('presentmon_frametime_column_required');
  const app=header.indexOf('Application'),pid=header.indexOf('ProcessID'),swap=header.indexOf('SwapChainAddress');
  let groups=new Map(),rejected=0;
  for(const row of rows){
   const raw=row[index],ms=raw?.trim()===''?NaN:Number(raw);
   if(!finite(ms)||ms<=0||ms>60000){rejected++;continue;}
   const name=app>=0?row[app]||'Desconhecido':'Desconhecido';if(name.length>120)throw Error('application_limit');
   const key=[name,pid>=0?row[pid]:'',swap>=0?row[swap]:''].join('|');if(!groups.has(key)){if(groups.size>=32)throw Error('csv_stream_limit');groups.set(key,{name,frames:[]});}groups.get(key).frames.push(ms);
  }
  return {v:1,source:'presentmon_csv_import',live:false,simulation:false,semantic:'presented_frames_not_displayed_fps',rejected,
   method:'fps=count*1000/sum_ms;1pct_low=1000/mean_slowest_ceil_1pct;at_least_100_frames',streams:[...groups.values()].map(({name,frames})=>{
    const total=frames.reduce((a,b)=>a+b,0),slow=[...frames].sort((a,b)=>b-a).slice(0,Math.ceil(frames.length*.01)),stride=Math.max(1,Math.ceil(frames.length/120));
    return {name,samples:frames.length,average_fps:1000*frames.length/total,mean_frametime_ms:total/frames.length,one_percent_low_fps:frames.length>=100?1000/(slow.reduce((a,b)=>a+b,0)/slow.length):null,points:frames.filter((_v,i)=>i%stride===0).slice(0,120)};
   })};
 }
 function csvCell(value){const s=String(value??'');return '"'+(/^[\s]*[=+@-]/.test(s)?"'"+s:s).replaceAll('"','""')+'"';}
 return Object.freeze({latency,createInputSession,presentmon,csvRows,csvCell});
});
