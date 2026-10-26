'use strict';
(() => {
  const model=window.loneDiagnosticModel,center=document.getElementById('diagnosticCenter');
  if(!model||!center)return;
  const grid=document.getElementById('diagnosticGrid'),select=document.getElementById('diagnosticScenario'),
    refresh=document.getElementById('diagnosticRefresh'),error=document.getElementById('diagnosticError');
  let generation=0,unlockTimer=null;
  const shapes={shield:'m12 3 8 4v5c0 5-8 9-8 9s-8-4-8-9V7Z',monitor:'M3 4h18v13H3ZM8 21h8m-4-4v4',
    link:'M9 15 15 9M8 16l-2 2a4 4 0 0 1-6-6l4-4m12 0 2-2a4 4 0 0 1 6 6l-4 4',
    chip:'M5 5h14v14H5ZM9 1v4m6-4v4M9 19v4m6-4v4M1 9h4m-4 6h4m14-6h4m-4 6h4',
    activity:'M2 12h5l3-8 4 16 3-8h5',clock:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4v5l3 2',lock:'M5 10h14v11H5ZM8 10V7a4 4 0 0 1 8 0v3m-4 4v3'};
  function node(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
  function icon(name){
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',shapes[name]||shapes.shield);svg.append(p);return svg;
  }
  const date=value=>value?value.slice(8,10)+'/'+value.slice(5,7)+' · '+value.slice(11,19)+' UTC':'Não verificada';
  function pair(list,title,text){const row=node('div','diagnostic-detail-row');row.append(node('dt','',title),node('dd','',text));list.append(row);}
  function render(view){
    center.dataset.simulation=String(view.simulation);
    document.getElementById('diagnosticDemo').hidden=!view.simulation;
    document.getElementById('diagnosticClock').textContent=view.clock?'Relógio simulado fixo: '+date(view.clock):'Sem consulta operacional';
    const fragments=[];
    for(const card of view.cards){
      const article=node('article','diagnostic-card');article.dataset.card=card.id;article.dataset.state=card.state;
      const top=node('div','diagnostic-card-top'),tile=node('span','diagnostic-icon');tile.append(icon(card.icon));
      top.append(tile,node('h3','',card.title),node('span','diagnostic-data-tag',card.simulated?'SIMULADO':'SEM EVIDÊNCIA'));
      const status=node('strong','diagnostic-status',card.label);status.dataset.state=card.state;
      const summary=node('p','diagnostic-summary',card.summary),last=node('div','diagnostic-last');
      last.append(node('span','',card.simulated?'Última verificação simulada':'Última verificação'),node('time','',date(card.checkedAt)));
      if(card.checkedAt)last.lastElementChild.dateTime=card.checkedAt;
      article.append(top,status,summary,last);
      const details=node('details','diagnostic-details');details.append(node('summary','','Detalhes técnicos'));
      if(!card.details.length)details.append(node('p','','Nenhuma evidência disponível. Não há leitura real neste painel.'));
      for(const r of card.details){
        const block=node('section','diagnostic-evidence');block.append(node('h4','',r.component),node('p','',r.message));
        const list=node('dl');pair(list,'Estado simulado',r.state);pair(list,'Regra',r.code);
        pair(list,'Horário da evidência',date(r.checkedAt));
        pair(list,'Idade da evidência simulada',r.age===null?'Indisponível':String(r.age)+' s');
        pair(list,'Validade do recibo',String(r.ttl)+' s');
        if(r.lastCommunication)pair(list,'Última comunicação simulada',date(r.lastCommunication));
        block.append(list);details.append(block);
      }
      article.append(details);fragments.push(article);
    }
    grid.replaceChildren(...fragments);
    const pending=document.getElementById('diagnosticPending');
    pending.replaceChildren(...view.pending.map(p=>{const li=node('li');li.append(node('strong','',p.title),node('span','',p.status));return li;}));
    const messages={disabled:'A demonstração está disponível somente na revisão isolada de desenvolvimento. Nenhuma sonda foi ativada.',
      rate_limited:'Aguarde antes de consultar novamente a demonstração.',busy:'Uma consulta simulada ainda está em andamento.',
      provider_timeout:'A demonstração excedeu o prazo. Nenhum estado antigo é apresentado como atual.',
      invalid_message:'Resposta inválida rejeitada. O estado dos componentes não foi confirmado.',
      invalid_report:'Relatório inválido rejeitado. Nenhuma evidência foi promovida a saudável.',
      invalid_request:'Consulta de demonstração inválida rejeitada.',provider_unavailable:'Demonstração indisponível. Não confirma falha do computador.'};
    error.hidden=!view.error;error.textContent=view.error?messages[view.error]||messages.invalid_message:'';
  }
  async function load(){
    const id=++generation;clearTimeout(unlockTimer);refresh.disabled=true;select.disabled=true;grid.setAttribute('aria-busy','true');
    let timeout;
    try{
      const result=await Promise.race([window.loneDesktop?.getDiagnostics(select.value)||Promise.resolve(null),
        new Promise(resolve=>{timeout=setTimeout(()=>resolve(null),2500);})]);
      if(id===generation&&!center.hidden)render(result?model.project(result):model.empty('provider_timeout'));
    }catch{if(id===generation&&!center.hidden)render(model.empty('provider_unavailable'));}
    finally{
      clearTimeout(timeout);
      if(id===generation){grid.setAttribute('aria-busy','false');unlockTimer=setTimeout(()=>{refresh.disabled=false;select.disabled=false;},550);}
    }
  }
  render(model.empty());
  document.getElementById('diagnosticOpen').addEventListener('click',()=>{center.hidden=false;center.focus();center.scrollIntoView({block:'start'});void load();});
  document.getElementById('diagnosticClose').addEventListener('click',()=>{
    center.hidden=true;generation++;clearTimeout(unlockTimer);grid.setAttribute('aria-busy','false');refresh.disabled=false;select.disabled=false;
    document.getElementById('diagnosticOpen').focus();
  });
  refresh.addEventListener('click',()=>void load());select.addEventListener('change',()=>void load());
  window.addEventListener('pagehide',()=>{generation++;clearTimeout(unlockTimer);});
})();
