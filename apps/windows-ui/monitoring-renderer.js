'use strict';
(() => {
  const model=window.loneMetricModel,native=window.loneDesktop;
  const validStates={available:'Válida',warming_up:'Aquecendo',unsupported:'Não suportada',unavailable:'Indisponível',
    permission_denied:'Leitura não permitida',error:'Erro de leitura',stale:'Desatualizada'};
  let lastView=null,lastReceipt=0;
  // Update text only when it changes; no innerHTML or sensor-provided markup.
  const text=(node,value)=>{if(node&&node.textContent!==value)node.textContent=value;};
  const notice=document.getElementById('monitoringNotice');
  const status=document.createElement('span');status.className='monitoring-status';status.setAttribute('role','status');
  status.textContent='Coletor local desativado';notice.replaceChildren(status);
  const labels=[['cpu.utilization','CPU'],['gpu.adlx.utilization','GPU'],['ram.used','RAM'],['gpu.adlx.temperature','Temperatura GPU']];
  const cards=[...document.querySelectorAll('#sensorGrid .sensor')];
  const minis=[...document.querySelectorAll('#miniSensors .mini-sensor')];
  labels.forEach(([id,label],i)=>{if(id){cards[i].dataset.metricId=id;minis[i].dataset.metricId=id;
    if(i===3)text(cards[i].querySelector('.sensor-top span'),label);
    const progress=document.createElement('progress');progress.max=100;progress.value=0;progress.hidden=true;
    progress.setAttribute('aria-label','Utilização');cards[i].append(progress);
    const meta=document.createElement('details');meta.className='metric-meta';
    const summary=document.createElement('summary');summary.textContent='Origem e atualização';
    const detail=document.createElement('p');meta.append(summary,detail);cards[i].append(meta);
  }else{cards[i].querySelector('small').textContent='Sem provedor · indisponível';minis[i].querySelector('small').textContent='Sem provedor';}});
  const ramDetail=document.createElement('p');ramDetail.className='ram-detail';cards[2].append(ramDetail);
  const gpu=document.getElementById('gpuMetrics');
  const gpuTitle=document.createElement('h2');gpuTitle.textContent='AMD Radeon RX 6750 XT';gpu.append(gpuTitle);
  const gpuCaption=document.createElement('p');gpuCaption.className='gpu-caption';gpu.append(gpuCaption);
  for(const [key,label] of [['hotspot_temperature','Hotspot'],['vram_used_mb','VRAM utilizada'],['vram_total_mb','VRAM total'],['core_clock','Clock'],['power','Potência'],['fan_rpm','Ventoinha']]){
    const row=document.createElement('div');row.className='metric-row';row.dataset.metricId='gpu.adlx.'+key;
    const name=document.createElement('span');name.textContent=label;
    const value=document.createElement('strong');value.textContent='Indisponível';row.append(name,value);gpu.append(row);
  }
  const gpuMeta=document.createElement('details');gpuMeta.className='metric-meta';
  const gpuSummary=document.createElement('summary');gpuSummary.textContent='Origem, horários e validade';
  const gpuMetaText=document.createElement('p');gpuMeta.append(gpuSummary,gpuMetaText);gpu.append(gpuMeta);
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
      'Em desenvolvimento isolado, GPU, hotspot, VRAM, clock, potência e RPM usam somente consultas ADLX. Sensores não suportados permanecem indisponíveis.',
      'GPU atualiza a cada 2 segundos, com cadência reduzida em inatividade. MB são as unidades nativas ADLX, sem reinterpretar como GiB.',
      'Temperatura da CPU, controle de ventoinhas e FPS não estão integrados. Atividade PDH pode ficar indisponível.',
      'ACL e verificações de processo não isolam completamente outros programas sob a mesma conta.']){
      const p=document.createElement('p');p.textContent=text;body.append(p);
    }
  }));
  function historyNotice(connected){
    const title=document.getElementById('chartTitle'),selected=document.querySelector('[data-metric][aria-pressed=true]');
    text(title,'Histórico de '+(selected?.dataset.metric||'CPU')+' indisponível');
    text(document.querySelector('.chart-card .section-heading p'),'Série histórica ainda não integrada');
    text(document.querySelector('.empty-chart p'),'Os cartões exibem as leituras disponíveis. O gráfico histórico será integrado em outra etapa.');
    text(document.querySelector('.chart-caption span'),connected?'Coleta local ativa · gráfico indisponível':'Coletor sem conexão · gráfico indisponível');
    text(document.querySelector('.chart-caption span:last-child'),'Sem série histórica');
  }
  document.querySelectorAll('[data-metric]').forEach(button=>button.addEventListener('click',()=>historyNotice(lastView?.connection==='connected')));
  function metadata(m){return m?`${m.source} · ${m.unit} · ${validStates[m.state]||'Indisponível'} · ${m.collected_at||'sem leitura'}`:'Sem leitura disponível';}
  function refresh(){
    if(document.hidden)return; // Receive state, but defer DOM work while hidden.
    const view=lastView,connected=view?.connection==='connected';
    const snapshot=connected&&view.snapshot?model.age(view.snapshot,(performance.now()-lastReceipt)/1000):null;
    const byId=new Map((snapshot?.metrics||[]).map(m=>[m.id,m]));
    const prefix=view?.simulated?'DEMONSTRAÇÃO · ':'';
    let statusText=prefix+(connected?'Coletor local conectado · '+(view.simulated?'provedor simulado':view.gpu_enabled?'Windows + AMD ADLX':'leitura do Windows'):view?.connection==='connecting'?'Conectando ao coletor local…':
      view?.connection==='disabled'?'Coletor local desativado':view?.connection==='stopped'?'Sessão de coleta encerrada':'Coletor desconectado · dados indisponíveis');
    notice.dataset.connection=view?.connection||'disabled';
    if(connected&&snapshot.metrics.some(m=>m.stale))statusText+=' · há dados desatualizados';
    if(view?.error)statusText+=' · falha na leitura local';
    text(status,statusText);
    labels.forEach(([id],i)=>{
      if(!id)return;const m=byId.get(id),card=cards[i],mini=minis[i];
      const formatted=model.format(m);text(card.querySelector('.value'),formatted);text(mini.querySelector('strong'),formatted);
      const detail=m?.valid?'Leitura válida':m?validStates[m.state]:'Indisponível';
      let miniDetail=detail;
      const temp=byId.get('gpu.adlx.temperature'),utilization=byId.get('gpu.adlx.utilization');
      if(i===1&&temp?.valid)miniDetail='GPU · '+model.format(temp);
      if(i===3&&(utilization?.valid||temp?.valid))miniDetail=`VRAM ${model.format(byId.get('gpu.adlx.vram_used_mb'))} / ${model.format(byId.get('gpu.adlx.vram_total_mb'))}`;
      text(card.querySelector('small'),detail);text(mini.querySelector('small'),miniDetail);
      const last=view?.last_valid_at?.[id];text(card.querySelector('.metric-meta p'),metadata(m)+(last?' · última válida: '+last:''));
      const percent=byId.get(id==='ram.used'?'ram.utilization':id),progress=card.querySelector('progress');
      progress.hidden=!percent?.valid||id==='gpu.adlx.temperature';progress.value=percent?.valid?percent.value:0;
      card.dataset.availability=m?.state||'unavailable';
    });
    const ram=k=>model.format(byId.get('ram.'+k));text(ramDetail,`Total ${ram('total')} · Disponível ${ram('available')} · Uso ${ram('utilization')}`);
    const gpuValues=[];
    gpu.querySelectorAll('[data-metric-id]').forEach(row=>{
      const m=byId.get(row.dataset.metricId);
      text(row.querySelector('strong'),m?.valid?model.format(m):m?.stale?'Desatualizado':'Indisponível');
      row.title=metadata(m);row.dataset.availability=m?.state||'unavailable';gpuValues.push(metadata(m));
    });
    text(gpuMetaText,gpuValues.join('\n'));
    const gpuMetric=byId.get('gpu.adlx.utilization'),gpuTemp=byId.get('gpu.adlx.temperature');
    text(gpuCaption,!view?.gpu_enabled?'Provedor GPU desativado · disponível apenas em desenvolvimento isolado':
      !connected?'Coletor desconectado · dados indisponíveis':gpuMetric?.stale?'Dados GPU desatualizados':
      gpuMetric?.valid?'Somente leitura · ADLX · atualização '+gpuMetric.collected_at:'Aguardando leitura GPU válida · frames inválidos são descartados');
    const thermal=document.querySelectorAll('.thermal-values b');
    text(thermal[1],model.format(gpuTemp));
    text(document.querySelector('.thermal-card .badge'),gpuTemp?.valid?'GPU · ADLX':'Sem leitura GPU válida');
    for(const volume of ['c','d']){
      const card=storage.querySelector(`[data-volume="${volume}"]`),all=[];
      card.querySelectorAll('[data-metric-id]').forEach(row=>{
        const m=byId.get(row.dataset.metricId);text(row.querySelector('strong'),row.dataset.metricId.endsWith('.activity')&&!m?.valid?'Indisponível':model.format(m));
        row.title=metadata(m);row.dataset.availability=m?.state||'unavailable';all.push(metadata(m));
      });
      const occupation=byId.get('storage.'+volume+'.occupation'),progress=card.querySelector('progress');
      progress.hidden=!occupation?.valid;progress.value=occupation?.valid?occupation.value:0;
      text(card.querySelector('.badge'),occupation?.valid?'Capacidade válida':'Capacidade indisponível');
      text(card.querySelector('.metric-meta p'),all.join('\n'));
    }
    text(providerRows[0],connected?'APIs Windows':'Coletor desconectado');
    text(providerRows[1],!view?.gpu_enabled?'Desativado':gpuMetric?.valid?'ADLX · somente leitura':'Sem leitura válida');
    text(providerCaption,view?.simulated?'Provedor simulado · demonstração':connected?'Somente leitura · coleta local':'Monitoramento local · sem conexão');
    historyNotice(connected);
  }
  function receive(value){if(!value||value.v!==1)return;lastView=value;lastReceipt=performance.now();refresh();}
  native?.onMetrics(receive);native?.getMetrics().then(receive).catch(()=>receive({v:1,connection:'disconnected',error:'read_unavailable'}));
  const timer=setInterval(refresh,1000);window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});refresh();
  document.addEventListener('visibilitychange',refresh);
})();
