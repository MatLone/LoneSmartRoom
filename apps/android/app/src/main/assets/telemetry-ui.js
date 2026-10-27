'use strict';
// Fixed native read only; no fetch, URLs, command parameters or persistent credentials.
(()=>{
 const model=window.loneTelemetry;let timer=null,expiry=null,pending=null,serial=0,view=null,at=0,visible=false,failures=0;
 let watermark=new Map(),reconnecting=false,generation=null,sequence=-1;
 const label=document.getElementById('telemetryState'),last=document.getElementById('telemetryLast');
 function paint(){
  const current=model.age(view,(performance.now()-at)/1000),metrics=new Map(current?.snapshot?.metrics.map(m=>[m.id,m])||[]);
  for(const node of document.querySelectorAll('[data-telemetry]')){
   let m=metrics.get(node.dataset.telemetry);
   if(m?.valid&&generation===current?.generation&&m.collected_at<= (watermark.get(m.id)||''))m={...m,valid:false,state:'warming_up'};
   node.textContent=model.format(m);node.dataset.state=m?.state||'unavailable';
   const age=m?.age_seconds===null||m?.age_seconds===undefined?'não coletado':m.age_seconds.toFixed(1)+' s';
   node.title=m?`${m.source} · ${m.collected_at||'sem amostra'} · idade ${age}`:'Sem medição';
   if(node.parentElement.matches('.sensor'))node.parentElement.querySelector('.sensor-value')?.setAttribute('aria-label',node.textContent);
  }
  for(const bar of document.querySelectorAll('[data-telemetry-bar]')){
   const m=metrics.get(bar.dataset.telemetryBar),valid=m?.valid&&m.unit==='percent'&&m.collected_at>(watermark.get(m.id)||'');bar.parentElement.hidden=!valid;bar.style.width=(valid?m.value:0)+'%';bar.parentElement.setAttribute('aria-label',valid?model.format(m):'Indisponível');
  }
 }
 function lose(message){
  if(view?.snapshot)for(const m of view.snapshot.metrics)if(m.collected_at)watermark.set(m.id,m.collected_at);
  reconnecting=true;view=null;label.textContent=message;paint();
 }
 function schedule(){if(visible)timer=setTimeout(query,Math.min(10000,2000*2**Math.min(failures,2)));}
 function query(){
  if(!visible||pending!==null)return;
  if(typeof window.LoneAgent?.refreshTelemetry!=='function'){label.textContent='Indisponível · transporte nativo ausente';return;}
  pending=++serial;label.textContent=reconnecting?'Reconectando · Atualizando':'Atualizando';
  const id=pending;expiry=setTimeout(()=>{if(pending===id){pending=null;failures++;lose('Sem comunicação · Indisponível');schedule();}},12000);
  window.LoneAgent.refreshTelemetry(id);
 }
 window.onLoneTelemetry=raw=>{
  if(!visible||raw?.request_id!==pending)return;
  clearTimeout(expiry);pending=null;
  try{
   const next=model.normalize(raw,{transportSeconds:raw.transport_seconds});
   if(generation===next.generation&&next.snapshot&&next.snapshot.sequence<sequence)throw Error();
   if(generation!==next.generation){watermark.clear();reconnecting=false;}
   view=next;at=performance.now();generation=next.generation;sequence=next.snapshot?.sequence??-1;failures=0;
   for(const m of next.snapshot?.metrics||[])if(m.valid&&m.collected_at>(watermark.get(m.id)||''))watermark.delete(m.id);
   reconnecting=watermark.size>0;
   label.textContent=next.snapshot?'HTTPS autenticado · '+(reconnecting?'Atualizando':'Medições recebidas'):'Coletor indisponível';
   last.textContent=next.snapshot?'Última atualização: '+new Date(next.snapshot.generated_at).toLocaleTimeString('pt-BR'):'Última atualização: nenhuma medição';
   paint();
  }catch{failures++;lose('Telemetria indisponível · consulte o agente');}
  schedule();
 };
 function update(){
  const active=!document.hidden&&!document.getElementById('panel-monitor').hidden;
  if(active===visible)return;visible=active;clearTimeout(timer);clearTimeout(expiry);pending=null;serial++;
  if(visible){lose('Atualizando');query();}else{lose('Consulta pausada');}
 }
 document.addEventListener('visibilitychange',update);
 new MutationObserver(update).observe(document.getElementById('panel-monitor'),{attributes:true,attributeFilter:['hidden']});
 // A single display timer ages values without issuing requests while hidden.
 setInterval(()=>{if(visible)paint();},1000);update();
})();
