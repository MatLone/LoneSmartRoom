'use strict';
// Documented SignalRGB v1 routes only. No redirects, proxy, arbitrary URL or install route.
const http=require('node:http');
const text=s=>typeof s==='string'&&s.length>0&&s.length<=160&&!/[\x00-\x1f\x7f<>\\/]/.test(s);
function effect(e){if(!e||!text(e.id)||!text(e.attributes?.name))throw Error('rgb_signal_contract');return {id:e.id,name:e.attributes.name,source:'signalrgb.api'};}
function current(v){const e=effect(v),a=v.attributes;if(typeof a.enabled!=='boolean'||!Number.isFinite(a.global_brightness)||a.global_brightness<0||a.global_brightness>100)throw Error('rgb_signal_contract');return {...e,enabled:a.enabled,brightness:a.global_brightness};}
function effectUrl(name){if(!text(name))throw Error('rgb_signal_effect_name');return 'signalrgb://effect/apply/'+encodeURIComponent(name);}
function createClient({request=http.request,timeout=3000,maxBytes=2097152}={}){
 async function call(method,route,body){return new Promise((resolve,reject)=>{
  let done=false,size=0,chunks=[],req,timer;const end=(error,value)=>{if(done)return;done=true;clearTimeout(timer);error?reject(Error(error)):resolve(value);};
  const data=body===undefined?null:JSON.stringify(body);
  try{req=request({hostname:'127.0.0.1',port:16038,path:'/api/v1/'+route,method,agent:false,headers:{Accept:'application/json',...(data?{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}:{})}},res=>{
   res.on('error',()=>end('rgb_signal_transport'));res.on('aborted',()=>end('rgb_signal_transport'));
   res.on('data',chunk=>{size+=chunk.length;if(size>maxBytes){end('rgb_signal_response_limit');req.destroy();}else chunks.push(chunk);});
   res.on('end',()=>{if(done)return;if(res.statusCode===403)return end('rgb_signal_permission_403');if(res.statusCode<200||res.statusCode>=300)return end('rgb_signal_http_error');
    try{const v=JSON.parse(Buffer.concat(chunks).toString('utf8'));if((v.apiVersion??v.api_version)!=='1.0'||v.status!=='ok')throw Error();end(null,v.data??null);}catch{end('rgb_signal_contract');}});
  });req.on('error',()=>end('rgb_signal_transport'));timer=setTimeout(()=>{end('rgb_signal_timeout');req.destroy();},timeout);if(data)req.write(data);req.end();}catch{end('rgb_signal_transport');}
 });}
 const id=x=>{if(!text(x))throw Error('rgb_signal_effect_id');return encodeURIComponent(x);};
 return Object.freeze({async current(){return current(await call('GET','lighting'));},async effects(){const d=await call('GET','lighting/effects');if(!Array.isArray(d?.items)||d.items.length>512)throw Error('rgb_signal_contract');const list=d.items.map(effect);if(new Set(list.map(e=>e.id)).size!==list.length)throw Error('rgb_signal_contract');return list;},
  async parameterless(key){const d=await call('GET','lighting/effects/'+id(key));effect(d);return !!d.attributes.parameters&&typeof d.attributes.parameters==='object'&&!Array.isArray(d.attributes.parameters)&&Object.keys(d.attributes.parameters).length===0;},
  apply:key=>call('POST','lighting/effects/'+id(key)+'/apply'),brightness:value=>{if(!Number.isInteger(value)||value<0||value>100)throw Error('rgb_signal_brightness');return call('PATCH','lighting/global_brightness',{global_brightness:value});},
  enabled:value=>{if(typeof value!=='boolean')throw Error('rgb_signal_enabled');return call('PATCH','lighting/enabled',{enabled:value});}});
}
module.exports={createClient,effectUrl,current,effect,text};
