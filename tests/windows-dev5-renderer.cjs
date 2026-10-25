'use strict';
// Minimal DOM substitutes exercise the actual renderer; no Chromium or sensors run.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {snapshot}=require('./electron-monitoring.cjs'),model=require('../apps/windows-ui/monitoring-model.js');
class Node {
  constructor(tag='div',cls=''){this.tag=tag;this.className=cls;this.children=[];this.dataset={};this.textContent='';this.attrs={};}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
  setAttribute(k,v){this.attrs[k]=v;}
  addEventListener(){}
  matches(s){
    if(s.startsWith('.'))return this.className.split(' ').includes(s.slice(1));
    if(s.startsWith('[')){const m=/^\[data-([\w-]+)(?:="([^"]+)")?\]$/.exec(s);if(!m)return false;
      const k=m[1].replace(/-([a-z])/g,(_,x)=>x.toUpperCase());return k in this.dataset&&(m[2]===undefined||this.dataset[k]===m[2]);}
    return this.tag===s;
  }
  querySelectorAll(s){const parts=s.split(' '),first=parts.shift(),found=[];
    const visit=n=>{for(const child of n.children){if(child.matches(first))found.push(child);visit(child);}};visit(this);
    return parts.length?found.flatMap(n=>n.querySelectorAll(parts.join(' '))):found;
  }
  querySelector(s){return this.querySelectorAll(s)[0]||null;}
}
const make=(tag,cls)=>new Node(tag,cls),cards=Array.from({length:4},()=>{const c=make('article','sensor');c.append(make('div','value'),make('small'));return c;});
const minis=Array.from({length:4},()=>{const c=make('div','mini-sensor');c.append(make('strong'),make('small'));return c;});
const storage=make('section'),notice=make('div'),body=make('div');let receive,tick,clock=0,checks=0;
const check=(v,n)=>{assert(v,n);checks++;};
const doc={createElement:make,getElementById:id=>({monitoringNotice:notice,storageMetrics:storage,dialogBody:body}[id]||null),
  querySelector:()=>null,querySelectorAll:s=>s==='#sensorGrid .sensor'?cards:s==='#miniSensors .mini-sensor'?minis:[]};
const native={onMetrics:fn=>receive=fn,getMetrics:()=>new Promise(()=>{})};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../apps/windows-ui/monitoring-renderer.js'),'utf8'),{
  window:{loneMetricModel:model,loneDesktop:native,addEventListener(){}},document:doc,performance:{now:()=>clock},
  setInterval:fn=>{tick=fn;return 1;},clearInterval(){},queueMicrotask:fn=>fn()});
const send=(connection,data,error=null)=>receive({v:1,connection,error,simulated:false,snapshot:data,last_valid_at:{}});
const sample=snapshot();sample.metrics.find(m=>m.id==='cpu.utilization').value=0.0043;
sample.metrics.find(m=>m.id==='storage.c.activity').value=0.0000496;
Object.assign(sample.metrics.find(m=>m.id==='storage.d.activity'),{valid:false,state:'unavailable',value:null});
send('connected',model.normalize(sample));
const volume=v=>storage.querySelector(`[data-volume="${v}"]`),value=id=>storage.querySelector(`[data-metric-id="${id}"]`).querySelector('strong').textContent;
check(cards[0].querySelector('.value').textContent==='<0,1%','Tiny CPU positive visible');
check(minis[0].querySelector('strong').textContent==='<0,1%','Widget receives exactly the same formatted value');
check(value('storage.c.activity')==='<0,1%','Tiny activity positive visible');
check(value('storage.d.activity')==='Indisponível','Null activity explicitly unavailable');
check(value('storage.c.read_rate')==='0 bytes/s','Valid I/O zero remains numeric');
for(const v of ['c','d']){
  check(volume(v).querySelector('.capacity-bar-label').textContent==='Ocupação do disco','Visible occupation label');
  check(volume(v).querySelector('progress').value===25,'Bar uses occupation, never activity');
  check(volume(v).querySelector('.badge').textContent==='Capacidade válida','Optional activity cannot invalidate capacity badge');
}
check(cards[2].querySelector('.ram-detail').textContent.includes('Disponível 8,0 GiB'),'RAM total/available/unit preserved');
clock=4000;tick();
check(cards[0].querySelector('.value').textContent==='—'&&cards[0].querySelector('small').textContent==='Desatualizada','Old CPU not refreshed into valid data');
check(value('storage.c.activity')==='Indisponível','Old activity unavailable');
check(volume('c').querySelector('progress').value===25,'Capacity retains its separate 60-second cadence');
send('disconnected',model.normalize(sample),'read_timeout');
check(notice.children[0].textContent.includes('Coletor desconectado'),'Disconnect shown explicitly');
check(cards[0].querySelector('.value').textContent==='—'&&value('storage.c.read_rate')==='—','Disconnect hides numeric readings');
check(volume('c').querySelector('progress').hidden,'No capacity bar suggesting a live read while disconnected');
send('connected',model.normalize(sample));check(cards[0].querySelector('.value').textContent==='<0,1%','Reconnection restores validated readings');
console.log(`PASS: ${checks} actual-renderer assertions with DOM substitutes; no GUI, sensors or packaged execution.`);
