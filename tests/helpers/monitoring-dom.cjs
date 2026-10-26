'use strict';
// Deliberately small DOM substitutes; counts setter calls, not CPU/GPU time.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
function rendererFixture(){
  let writes=0,receive,tick,clock=0;const timers=[];
  class Node{
    constructor(tag='div',cls=''){this.tag=tag;this.className=cls;this.children=[];this.dataset={};this._text='';this.attrs={};}
    set textContent(value){writes++;this._text=value;}get textContent(){return this._text;}
    append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){writes++;this.children=nodes;}
    setAttribute(k,v){writes++;this.attrs[k]=v;}addEventListener(){}
    matches(s){if(s.startsWith('.'))return this.className.split(' ').includes(s.slice(1));
      if(s.startsWith('[')){const m=/^\[data-([\w-]+)(?:="([^"]+)")?\]$/.exec(s);if(!m)return false;const k=m[1].replace(/-([a-z])/g,(_,x)=>x.toUpperCase());return k in this.dataset&&(m[2]===undefined||this.dataset[k]===m[2]);}
      return this.tag===s;}
    querySelectorAll(s){const parts=s.split(' '),first=parts.shift(),found=[];const visit=n=>{for(const c of n.children){if(c.matches(first))found.push(c);visit(c);}};visit(this);return parts.length?found.flatMap(n=>n.querySelectorAll(parts.join(' '))):found;}
    querySelector(s){return this.querySelectorAll(s)[0]||null;}
  }
  const make=(tag,cls)=>new Node(tag,cls),cards=Array.from({length:4},()=>{const n=make('article','sensor');n.append(make('div','value'),make('small'));return n;});
  const minis=Array.from({length:4},()=>{const n=make('div','mini-sensor');n.append(make('strong'),make('small'));return n;});
  const storage=make('section'),gpu=make('section'),notice=make('div'),body=make('div'),listeners=new Map();
  const document={hidden:false,visibilityState:'visible',createElement:make,addEventListener:(name,fn)=>listeners.set(name,fn),getElementById:id=>({monitoringNotice:notice,storageMetrics:storage,gpuMetrics:gpu,dialogBody:body}[id]||null),
    querySelector:()=>null,querySelectorAll:s=>s==='#sensorGrid .sensor'?cards:s==='#miniSensors .mini-sensor'?minis:[]};
  const window={innerWidth:1360,loneMetricModel:require('../../apps/windows-ui/monitoring-model.js'),
    loneDesktop:{onMetrics:fn=>receive=fn,getMetrics:()=>new Promise(()=>{})},addEventListener:(name,fn)=>listeners.set(name,fn)};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../apps/windows-ui/monitoring-renderer.js'),'utf8'),{
    window,document,performance:{now:()=>clock},setInterval:(fn,ms)=>{tick=fn;timers.push(ms);return 1;},clearInterval(){},queueMicrotask:fn=>fn()});
  return {cards,minis,storage,gpu,notice,document,window,timers,listeners,send:receive,tick:()=>tick(),clock:n=>clock=n,
    writes:()=>writes,reset:()=>writes=0};
}
module.exports={rendererFixture};
