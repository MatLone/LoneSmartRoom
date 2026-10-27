'use strict';
// On-demand receipt from existing cache-only IPC. No polling or new collector.
(() => {
  const model=window.loneHardwareDiagnostics,panel=document.getElementById('hardwareDiagnostics');
  if(!model||!panel)return;
  const button=document.getElementById('hardwareDiagnosticRefresh'),origin=document.getElementById('hardwareDiagnosticOrigin');
  const container=document.getElementById('hardwareDiagnosticRows'),nodes=[];
  let generation=0,disposed=false;
  for(const row of model.project(null).rows){
    const section=document.createElement('section'),title=document.createElement('h3'),state=document.createElement('p'),detail=document.createElement('p');
    section.dataset.component=row.id;title.textContent=row.title;detail.className='metric-meta';
    section.append(title,state,detail);container.append(section);nodes.push({section,state,detail});
  }
  function render(result,queriedAt){
    origin.textContent=(result.origin==='simulated'?'SIMULAÇÃO · não descreve o PC':result.origin==='real'?'Cache local · origem real':'Sem evidência validada')+
      (queriedAt?' · consulta pontual '+queriedAt:'')+(result.generatedAt?' · snapshot '+result.generatedAt+' · sequência '+result.sequence:'');
    result.rows.forEach((row,i)=>{
      const n=nodes[i];n.section.dataset.state=row.state;
      n.state.textContent=row.label+' na consulta · '+row.valid+'/'+row.expected+' leituras válidas';
      n.detail.textContent=row.evidence.map(m=>m.id+' · '+m.source+' · '+m.state+(m.stale?' · expirada':'')+
        ' · coleta '+(m.collectedAt||'não disponível')+' · idade na consulta '+(m.ageSeconds===null?'não disponível':m.ageSeconds.toFixed(1)+' s')+
        ' · limite '+m.limitSeconds+' s').join('\n')||'Nenhuma evidência disponível nesta consulta.';
    });
  }
  async function query(){
    if(disposed||!panel.open||document.hidden)return;
    const id=++generation;render(model.project(null),null);button.disabled=true;
    try{
      // No sensor read: main returns its already-owned, aged in-memory snapshot.
      const value=await window.loneDesktop?.getMetrics();
      if(id===generation&&!disposed&&panel.open&&!document.hidden)render(model.project(value),new Date().toISOString());
    }catch{if(id===generation&&!disposed&&panel.open)render(model.project(null),null);}
    finally{if(id===generation&&!disposed)button.disabled=false;}
  }
  render(model.project(null),null);
  panel.addEventListener('toggle',()=>{
    if(panel.open)void query();else{generation++;button.disabled=false;render(model.project(null),null);}
  });
  button.addEventListener('click',()=>void query());
  document.addEventListener('visibilitychange',()=>{
    generation++;button.disabled=false;
    if(panel.open){render(model.project(null),null);if(!document.hidden)void query();}
  });
  window.addEventListener('pagehide',()=>{generation++;disposed=true;});
})();
