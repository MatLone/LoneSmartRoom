'use strict';
(() => {
  const model=window.loneMetricModel,native=window.loneDesktop;
  const validStates={available:'Válida',warming_up:'Aquecendo',unsupported:'Não suportada',unavailable:'Indisponível',
    permission_denied:'Leitura não permitida',error:'Erro de leitura',stale:'Desatualizada'};
  let lastView=null,lastReceipt=0;
  const notice=document.getElementById('monitoringNotice');
  const status=document.createElement('span');status.className='monitoring-status';status.setAttribute('role','status');
  status.textContent='Coletor local desativado';notice.replaceChildren(status);
  const labels=[['cpu.utilization','CPU'],[null,'GPU'],['ram.used','RAM'],[null,'Temperatura']];
  const cards=[...document.querySelectorAll('#sensorGrid .sensor')];
  const minis=[...document.querySelectorAll('#miniSensors .mini-sensor')];
  labels.forEach(([id],i)=>{if(id){cards[i].dataset.metricId=id;minis[i].dataset.metricId=id;
    const progress=document.createElement('progress');progress.max=100;progress.value=0;progress.hidden=true;
    progress.setAttribute('aria-label','Utilização');cards[i].append(progress);
    const meta=document.createElement('details');meta.className='metric-meta';
    const summary=document.createElement('summary');summary.textContent='Origem e atualização';
    const detail=document.createElement('p');meta.append(summary,detail);cards[i].append(meta);
  }else{cards[i].querySelector('small').textContent='Sem provedor · indisponível';minis[i].querySelector('small').textContent='Sem provedor';}});
  const ramDetail=document.createElement('p');ramDetail.className='ram-detail';cards[2].append(ramDetail);
  const storage=document.getElementById('storageMetrics');
  for(const volume of ['c','d']){
    const card=document.createElement('article');card.className='surface storage-metric';card.dataset.volume=volume;
    const heading=document.createElement('div');heading.className='section-heading';
    const title=document.createElement('h2');title.textContent='Volume '+volume.toUpperCase()+':';
    const state=document.createElement('span');state.className='badge';state.dataset.volumeState=volume;heading.append(title,state);card.append(heading);
    const entries=[['total','Capacidade'],['available','Disponível'],['occupation','Ocupado'],['read_rate','Leitura'],['write_rate','Gravação'],['activity','Atividade PDH']];
    for(const [key,label]of entries){const row=document.createElement('div');row.className='metric-row';row.dataset.metricId='storage.'+volume+'.'+key;
      const text=document.createElement('span');text.textContent=label;const value=document.createElement('strong');value.textContent='—';
      row.append(text,value);card.append(row);}
    const progressLabel=document.createElement('div');progressLabel.className='capacity-bar-label';progressLabel.textContent='Ocupação do disco';card.append(progressLabel);
    const progress=document.createElement('progress');progress.max=100;progress.value=0;progress.hidden=true;progress.setAttribute('aria-label','Ocupação do disco '+volume.toUpperCase()+':');card.append(progress);
    const meta=document.createElement('details');meta.className='metric-meta';const summary=document.createElement('summary');summary.textContent='Origem, horários e validade';
    const detail=document.createElement('p');meta.append(summary,detail);card.append(meta);storage.append(card);
  }
  const providerRows=document.querySelectorAll('.provider-card .provider-row .badge');
  const providerCaption=document.querySelector('.provider-card .section-heading p');
  const sensorButton=document.querySelector('[data-panel="sensors"]');
  // Keep the existing settings modal and navigation. Only its monitoring explanation changes.
  sensorButton?.addEventListener('click',()=>queueMicrotask(()=>{
    const body=document.getElementById('dialogBody');body.replaceChildren();
    for(const text of ['Coletor independente → cache → Named Pipe local → processo principal → interface.',
      'CPU, RAM e volumes C:/D: usam APIs de leitura do Windows. Cada indicador conserva origem, unidade, horário e validade.',
      'Coleta somente no contexto do aplicativo. Nenhuma conexão do Electron ao agente HTTPS.',
      'GPU, temperaturas, VRAM, RPM e FPS não estão integrados. Atividade PDH pode ficar indisponível.',
      'ACL e verificações de processo não isolam completamente outros programas sob a mesma conta.']){
      const p=document.createElement('p');p.textContent=text;body.append(p);
    }
  }));
  function historyNotice(connected){
    const title=document.getElementById('chartTitle'),selected=document.querySelector('[data-metric][aria-pressed=true]');
    if(title)title.textContent='Histórico de '+(selected?.dataset.metric||'CPU')+' indisponível';
    const caption=document.querySelector('.chart-card .section-heading p');if(caption)caption.textContent='Série histórica ainda não integrada';
    const text=document.querySelector('.empty-chart p');if(text)text.textContent='Os cartões exibem as leituras disponíveis. O gráfico histórico será integrado em outra etapa.';
    const status=document.querySelector('.chart-caption span');if(status)status.textContent=connected?'Coleta local ativa · gráfico indisponível':'Coletor sem conexão · gráfico indisponível';
    const last=document.querySelector('.chart-caption span:last-child');if(last)last.textContent='Sem série histórica';
  }
  document.querySelectorAll('[data-metric]').forEach(button=>button.addEventListener('click',()=>historyNotice(lastView?.connection==='connected')));
  function metadata(m){return m?`${m.source} · ${m.unit} · ${validStates[m.state]||'Indisponível'} · ${m.collected_at||'sem leitura'}`:'Sem leitura disponível';}
  function refresh(){
    const view=lastView,connected=view?.connection==='connected';
    const snapshot=connected&&view.snapshot?model.age(view.snapshot,(performance.now()-lastReceipt)/1000):null;
    const byId=new Map((snapshot?.metrics||[]).map(m=>[m.id,m]));
    const prefix=view?.simulated?'DEMONSTRAÇÃO · ':'';
    status.textContent=prefix+(connected?'Coletor local conectado · '+(view.simulated?'provedor simulado':'leitura do Windows'):view?.connection==='connecting'?'Conectando ao coletor local…':
      view?.connection==='disabled'?'Coletor local desativado':view?.connection==='stopped'?'Sessão de coleta encerrada':'Coletor desconectado · dados indisponíveis');
    notice.dataset.connection=view?.connection||'disabled';
    if(connected&&snapshot.metrics.some(m=>m.stale))status.textContent+=' · há dados desatualizados';
    if(view?.error)status.textContent+=' · falha na leitura local';
    labels.forEach(([id],i)=>{
      if(!id)return;const m=byId.get(id),card=cards[i],mini=minis[i];
      const text=model.format(m);card.querySelector('.value').textContent=text;mini.querySelector('strong').textContent=text;
      const detail=m?.valid?'Leitura válida':m?validStates[m.state]:'Indisponível';
      card.querySelector('small').textContent=detail;mini.querySelector('small').textContent=detail;
      card.querySelector('.metric-meta p').textContent=metadata(m);
      const last=view?.last_valid_at?.[id];if(last)card.querySelector('.metric-meta p').textContent+=' · última válida: '+last;
      const percent=byId.get(id==='ram.used'?'ram.utilization':id),progress=card.querySelector('progress');
      progress.hidden=!percent?.valid;progress.value=percent?.valid?percent.value:0;
      card.dataset.availability=m?.state||'unavailable';
    });
    const ram=k=>model.format(byId.get('ram.'+k));ramDetail.textContent=`Total ${ram('total')} · Disponível ${ram('available')} · Uso ${ram('utilization')}`;
    for(const volume of ['c','d']){
      const card=storage.querySelector(`[data-volume="${volume}"]`),all=[];
      card.querySelectorAll('[data-metric-id]').forEach(row=>{
        const m=byId.get(row.dataset.metricId);row.querySelector('strong').textContent=row.dataset.metricId.endsWith('.activity')&&!m?.valid?'Indisponível':model.format(m);
        row.title=metadata(m);row.dataset.availability=m?.state||'unavailable';all.push(metadata(m));
      });
      const occupation=byId.get('storage.'+volume+'.occupation'),progress=card.querySelector('progress');
      progress.hidden=!occupation?.valid;progress.value=occupation?.valid?occupation.value:0;
      card.querySelector('.badge').textContent=occupation?.valid?'Capacidade válida':'Capacidade indisponível';
      card.querySelector('.metric-meta p').textContent=all.join('\n');
    }
    if(providerRows[0])providerRows[0].textContent=connected?'APIs Windows':'Coletor desconectado';
    if(providerCaption)providerCaption.textContent=view?.simulated?'Provedor simulado · demonstração':connected?'Somente leitura · APIs Windows':'Monitoramento local · sem conexão';
    historyNotice(connected);
  }
  function receive(value){if(!value||value.v!==1)return;lastView=value;lastReceipt=performance.now();refresh();}
  native?.onMetrics(receive);native?.getMetrics().then(receive).catch(()=>receive({v:1,connection:'disconnected',error:'read_unavailable'}));
  const timer=setInterval(refresh,1000);window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});refresh();
})();
