'use strict';
// Pure summaries of the already-owned cache. No sensor, network, command or AI API.
const metrics=require('./monitoring-model.js');
function summarize(view,{now=Date.now(),topic='all'}={}){
 const unavailable='Sem amostras reais atuais no cache local. Não iniciei coletores nem consultei o agente HTTPS.';
 try{
  if(!view||view.v!==1||view.connection!=='connected'||view.error!==null||view.simulated!==false||
     typeof view.gpu_enabled!=='boolean'||typeof view.refreshing!=='boolean'||!Number.isFinite(now)||
     JSON.stringify(view).length>65536||!view.snapshot||Date.parse(view.snapshot.generated_at)>now)return unavailable;
  const input={...view.snapshot,metrics:view.snapshot.metrics.map(m=>{
   if(m?.information_age_seconds===null&&m.ingress_age_seconds===undefined){const {information_age_seconds,...wire}=m;return wire;}
   return m;
  })};
  const snapshot=metrics.normalize(input,{gpu:view.gpu_enabled,simulated:false,now});
  const rows=new Map(snapshot.metrics.map(m=>{
   const wallAge=m.collected_at?Math.max(0,(now-Date.parse(m.collected_at))/1000):0;
   const delta=m.age_seconds===null?0:Math.max(0,wallAge-m.age_seconds);
   return [m.id,metrics.age({...snapshot,metrics:[m]},delta).metrics[0]];
  }));
  const gpuPending=view.refreshing||['updating','unavailable'].includes(view.gpu_resume_state);
  const display=id=>{
   if(id.startsWith('gpu.')&&gpuPending)return view.gpu_resume_state==='unavailable'?'Indisponível':'Atualizando';
   const m=rows.get(id);return m?.valid&&!m.stale&&m.data_kind==='real'?metrics.format(m):'Indisponível';
  };
  const parts=[];
  if(['all','cpu'].includes(topic))parts.push('CPU: '+display('cpu.utilization')+'. Temperatura da CPU: Indisponível (sensor não integrado).');
  if(['all','ram'].includes(topic))parts.push('RAM: '+display('ram.used')+' utilizados de '+display('ram.total')+'; disponíveis '+display('ram.available')+'; uso '+display('ram.utilization')+'.');
  if(['all','gpu'].includes(topic))parts.push('GPU: '+display('gpu.adlx.utilization')+'; '+display('gpu.adlx.temperature')+'; hotspot '+display('gpu.adlx.hotspot_temperature')+'; VRAM '+display('gpu.adlx.vram_used_mb')+' / '+display('gpu.adlx.vram_total_mb')+'; clock '+display('gpu.adlx.core_clock')+'; potência '+display('gpu.adlx.power')+'; ventoinhas '+display('gpu.adlx.fan_rpm')+'.');
  if(['all','storage'].includes(topic))for(const volume of ['c','d'])parts.push(volume.toUpperCase()+': ocupação '+display('storage.'+volume+'.occupation')+'; livres '+display('storage.'+volume+'.free')+'; leitura '+display('storage.'+volume+'.read_rate')+'; gravação '+display('storage.'+volume+'.write_rate')+'; atividade '+display('storage.'+volume+'.activity')+'.');
  parts.push('Fonte: cache local validado; snapshot '+snapshot.generated_at+'. Isso não confirma autenticação HTTPS.');
  return parts.join('\n').slice(0,1800);
 }catch{return unavailable;}
}
module.exports={summarize};
