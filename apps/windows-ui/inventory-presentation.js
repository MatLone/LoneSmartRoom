'use strict';
// Presentation only. Receives existing validated results; no reader or timer.
((root,factory)=>{const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.loneInventoryView=api;})(globalThis,()=>{
 const labels={name:'Nome',physical_cores:'Núcleos físicos',logical_cores:'Núcleos lógicos',reported_clock_mhz:'Clock informado (MHz)',max_clock_mhz:'Clock máximo informado (MHz)',cpu_temperature_celsius:'Temperatura CPU (°C)',cpu_power_watts:'Potência CPU (W)',capacity_bytes:'Capacidade',free_bytes:'Livre',resident_bytes:'Memória residente',received_bytes:'Recebido acumulado',sent_bytes:'Enviado acumulado',download_bytes_per_second:'Recebimento',upload_bytes_per_second:'Envio',link_bits_per_second:'Velocidade do link',configured_clock_mhz:'Clock configurado (MHz)',reported_speed_mhz:'Velocidade informada (MHz)',manufacturer:'Fabricante',version:'Versão',publisher:'Fornecedor',display_name:'Descrição',start_mode:'Inicialização',state:'Estado',signed:'Assinado',source:'Origem',steam_app_id:'AppID Steam'};
 const states={available:'Disponível',unavailable:'Indisponível',preview:'Prévia',plan_only:'Preparado; execução não habilitada'};
 const percent=n=>n>0&&n<.1?'<0,1%':n.toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
 function bytes(n){if(!Number.isFinite(n)||n<0)return 'Indisponível';const power=n===0?0:Math.min(3,Math.max(0,Math.floor(Math.log(n)/Math.log(1024))));const scaled=n/(1024**power);return (scaled>0&&scaled<.01?'<0,01':scaled.toLocaleString('pt-BR',{maximumFractionDigits:2}))+' '+['B','KiB','MiB','GiB'][power];}
 function cell(key,v){
  if(v===null||v===undefined||typeof v==='number'&&!Number.isFinite(v))return 'Indisponível';
  if(key.endsWith('_bytes_per_second'))return bytes(v)+'/s';
  if(key.endsWith('_bytes'))return bytes(v);
  if(key==='link_bits_per_second')return Number.isFinite(v)&&v>=0?(v/1e6).toLocaleString('pt-BR',{maximumFractionDigits:1})+' Mb/s':'Indisponível';
  return typeof v==='object'?JSON.stringify(v).slice(0,160):String(v).slice(0,180);
 }
 function render(document,value,target){
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const note=text=>el('p',text,'tool-note');target.replaceChildren();if(!value)return;
  target.append(el('p',value.state?'Estado: '+(value.extra?.partial?'Parcialmente disponível':states[value.state]||value.state)+(value.simulation?' · SIMULAÇÃO':''):'Resultado local'));
  if(value.source)target.append(note('Fonte: '+value.source));
  if(value.observed_at)target.append(note('Consulta da fonte: '+(Number.isFinite(Date.parse(value.observed_at))?new Date(value.observed_at).toLocaleString('pt-BR'):'horário indisponível')));
  const items=value.items||value.entries||value.streams||value.actions;
  if(Array.isArray(items)&&items.length){
   const all=items.slice(0,300),keys=[...new Set(all.flatMap(x=>Object.keys(x||{})))].slice(0,14);
   const table=el('table'),thead=el('thead'),head=el('tr'),tbody=el('tbody');let page=0;
   for(const key of keys)head.append(el('th',labels[key]||key.replaceAll('_',' ')));thead.append(head);table.append(thead,tbody);target.append(table);
   const navigation=el('div',undefined,'tool-pagination'),previous=el('button','Anterior','button'),next=el('button','Próxima','button'),status=note('');
   previous.type=next.type='button';
   function fill(){tbody.replaceChildren();const start=page*50;
    for(const item of all.slice(start,start+50)){const row=el('tr');for(const key of keys)row.append(el('td',cell(key,item?.[key])));tbody.append(row);}
    previous.disabled=page===0;next.disabled=start+50>=all.length;
    status.textContent=(start+1)+'–'+Math.min(start+50,all.length)+' de '+all.length+' itens retornados. A fonte pode aplicar limites.';
   }
   previous.addEventListener('click',()=>{if(page>0){page--;fill();}});next.addEventListener('click',()=>{if((page+1)*50<all.length){page++;fill();}});
   navigation.append(previous,status,next);if(all.length>50)target.append(navigation);fill();
  }else if(Array.isArray(items))target.append(note('Nenhum item disponível neste escopo.'));
  if(Array.isArray(value.extra?.cores)){
   target.append(el('h3','Uso por núcleo lógico · consulta pontual'));
   const grid=el('div',undefined,'core-readings');
   for(const core of value.extra.cores.slice(0,128)){
    const n=core?.utilization_percent,valid=Number.isFinite(n)&&n>=0&&n<=100;
    const card=el('div',undefined,'core-reading'),track=el('div',undefined,'core-track'),fill=el('span');
    if(valid)fill.style.width=n+'%';track.append(fill);card.append(el('span','Núcleo lógico '+String(core?.id??'não identificado').slice(0,20)),el('b',valid?percent(n):'Indisponível'),track);grid.append(card);
   }
   if(!value.extra.cores.length)grid.append(note('Contadores por núcleo indisponíveis nesta consulta. As demais fontes continuam independentes.'));
   target.append(grid,note('Valores informados pelo Windows, sem atualização automática nesta tela. Clock informado não é uma medição calibrada.'));
  }
  const technical=el('details',undefined,'metric-meta');technical.append(el('summary','Detalhes da consulta'));
  for(const [key,v]of Object.entries(value)){
   if(['items','entries','streams','actions','v','state','source','simulation','observed_at','settings'].includes(key))continue;
   if(key==='extra'&&v&&typeof v==='object'){const {cores,...rest}=v;if(Object.keys(rest).length)technical.append(note('Evidências: '+JSON.stringify(rest).slice(0,4000)));}
   else technical.append(note(key.replaceAll('_',' ')+': '+(typeof v==='object'?JSON.stringify(v):String(v)).slice(0,4000)));
  }
  if(technical.children.length>1)target.append(technical);
 }
 return Object.freeze({render,cell});
});
