'use strict';
(()=>{
 const api=window.lonePanel,model=window.loneMetricModel,grid=document.getElementById('panelMetrics');let latest=null,at=0,full=false;
 const specs=[['cpu.utilization','CPU','%'],['gpu.adlx.utilization','GPU','%'],['gpu.adlx.temperature','Temperatura GPU','°C'],['gpu.adlx.hotspot_temperature','Hotspot','°C'],['ram.used','RAM usada','GiB'],['gpu.adlx.vram_used_mb','VRAM','MB'],['gpu.adlx.core_clock','Clock GPU','MHz'],['gpu.adlx.power','Potência GPU','W'],['gpu.adlx.fan_rpm','Ventoinha GPU','RPM'],['gpu.adlx.vram_total_mb','VRAM total','MB'],['storage.c.occupation','Disco C:','%'],['storage.d.occupation','Disco D:','%']];
 const nodes=new Map();for(const [id,name,unit]of specs){const c=document.createElement('article'),h=document.createElement('h2'),v=document.createElement('strong'),info=document.createElement('small');h.textContent=name;v.textContent='Indisponível';c.append(h,v,info);grid.append(c);nodes.set(id,{v,info,unit});}
 function render(){const snapshot=latest?.connection==='connected'&&latest.snapshot?model.age(latest.snapshot,(performance.now()-at)/1000):null;
  const metrics=new Map(snapshot?.metrics.map(m=>[m.id,m])||[]);
  document.getElementById('panelState').textContent=latest?.simulated?'DEMONSTRAÇÃO · dados simulados':latest?.connection==='connected'?'Telemetria local · origem e horário por sensor':'Coletor desconectado · dados indisponíveis';
  for(const [id,node]of nodes){const m=metrics.get(id),gpu=id.startsWith('gpu.'),formatted=m?model.format(m):null;
   node.v.textContent=gpu&&latest?.refreshing?'Atualizando':gpu&&latest?.gpu_resume_state==='unavailable'?'Indisponível':formatted&&formatted!=='—'?formatted:m?.stale?'Desatualizado':'Indisponível';node.info.textContent=m?m.source+' · '+(m.collected_at?new Date(m.collected_at).toLocaleTimeString('pt-BR'):'sem leitura'):'';
  }
 }
 function update(value){latest=value;at=performance.now();render();}
 api.context().then(c=>{document.body.dataset.role=c.role;document.getElementById('panelRole').textContent=c.role==='touch'?'Touch Panel':'Overlay local';});
 api.onMetrics(update);api.snapshot().then(update);const timer=setInterval(()=>{if(!document.hidden)render();},1000);
 document.getElementById('exit').addEventListener('click',()=>api.close());document.getElementById('full').addEventListener('click',()=>{full=!full;api.fullscreen(full);});
 for(const b of document.querySelectorAll('[data-section]'))b.addEventListener('click',()=>api.showMain(b.dataset.section));
 window.addEventListener('pagehide',()=>clearInterval(timer));
})();
