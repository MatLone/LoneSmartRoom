'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createHistory,FIELDS}=require('../apps/windows-ui/performance-history.cjs');
const raw=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../.cache/telemetry-tests/https-frame.json')));
let t=Date.parse(raw.snapshot.generated_at),checks=0;const check=x=>{assert(x);checks++;};
function frame(){return {connection:'connected',simulated:true,snapshot:{...structuredClone(raw.snapshot),sequence:Math.floor((t-Date.parse(raw.snapshot.generated_at))/2000)+1,metrics:raw.snapshot.metrics.map(m=>({...m,collected_at:new Date(t).toISOString()}))}};}
const disabled=createHistory();check(!disabled.record(frame()));check(disabled.query(5).state==='disabled');
const h=createHistory({enabled:true,now:()=>t,maxPoints:1800});
for(let i=0;i<1900;i++){check(h.record(frame()));t+=2000;}
check(h.stats().points<=1800);check(h.query(5).rows.length<=120);check(h.query(60).rows.length<=120);check(h.query(5).simulation);
const q=h.query(5);q.rows[0][2][0]=999;check(h.query(5).rows[0][2][0]!==999);
assert.throws(()=>h.query(10));checks++;
const before=h.stats().points;check(!h.record(frame())===false||h.stats().points<=1800); // Any new point still stays bounded.
const old=frame();old.snapshot.sequence=0;t+=2000;check(!h.record(old));
const bad=frame();bad.snapshot.metrics[0].value=NaN;check(!h.record(bad));
const unavailable=frame();unavailable.snapshot.metrics[0].value=null;unavailable.snapshot.metrics[0].valid=false;unavailable.snapshot.metrics[0].state='unsupported';check(h.record(unavailable));
check(h.query(5).rows.at(-1)[2][0]===null);check(h.query(5).rows.at(-1)[2][1]==='unsupported');
h.close();check(h.query(5).state==='disabled');
const root=path.resolve(__dirname,'../.cache/history-unit-tests');fs.mkdirSync(root,{recursive:true});
const dir=fs.mkdtempSync(path.join(root,'own-')),store=createHistory({enabled:true,directory:dir,now:()=>t,maxPoints:20,maxBytes:4096});
for(let i=0;i<21;i++){t+=2000;store.record(frame());}store.close();
const file=path.join(dir,'performance-history-v1.json');check(fs.statSync(file).size<=4096);
const loaded=createHistory({enabled:true,directory:dir,now:()=>t,maxPoints:20,maxBytes:4096});check(loaded.query(60).rows.length>0);loaded.close();
fs.writeFileSync(file,'{"v":2,"secret":"must never reach UI"}');const corrupt=createHistory({enabled:true,directory:dir,now:()=>t,maxPoints:20,maxBytes:4096});check(corrupt.query(5).rows.length===0);check(corrupt.stats().error==='history_file_rejected');
assert.throws(()=>createHistory({enabled:true,directory:'C:\\production\\profile'}));checks++;
let api,calls=[];vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,'../apps/windows-ui/preload.cjs'),'utf8'),{require:()=>({contextBridge:{exposeInMainWorld:(_n,a)=>api=a},ipcRenderer:{invoke:(...a)=>{calls.push(a);return Promise.resolve();}}})});
(async()=>{await api.getPerformanceHistory(5);check(calls[0][0]==='history:read');for(const v of [0,10,{},'5',null,Infinity]){await assert.rejects(api.getPerformanceHistory(v));checks++;}check(calls.length===1);console.log(`PASS: ${checks} bounded history, retention, persistence, null, invalid-file and restricted preload assertions`);})();
