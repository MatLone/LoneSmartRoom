'use strict';
// Three-area Windows shell. Fixed app-local capabilities; no generic tools UI.
(()=>{
 const api=window.loneTools;if(!api)return;
 const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const note=t=>el('p',t,'tool-note');
 const label=(text,n)=>{const l=el('label',text,'field');l.append(n);return l;};
 const input=(placeholder='',type='text')=>{const n=el('input');n.type=type;n.placeholder=placeholder;n.maxLength=100;n.autocomplete='off';return n;};
 const select=values=>{const n=el('select');for(const [id,title]of values){const o=el('option',title);o.value=id;n.append(o);}return n;};
 const status=el('p','','tool-note');status.setAttribute('role','status');
 function button(text,action,secondary=false){const b=el('button',text,secondary?'button':'button primary');b.type='button';b.addEventListener('click',async()=>{b.disabled=true;try{await action();}catch{status.textContent='Consulta ou configuração indisponível. Nenhum comando operacional executado.';}finally{b.disabled=false;}});return b;}
 const card=(parent,title,description)=>{const c=el('section',undefined,'surface tool-card');c.append(el('h2',title),note(description));parent.append(c);return c;};
 const out=c=>{const n=el('div',undefined,'tool-output');c.append(n);return n;};
 const show=(r,target)=>window.loneInventoryView.render(document,r,target);
 const dialog=el('dialog',undefined,'focus-dialog');dialog.id='focusDialog';const close=button('Fechar',()=>dialog.close(),true),content=el('div');dialog.append(close,content,status);document.body.append(dialog);
 let focusAt=null;dialog.addEventListener('close',()=>focusAt?.focus());
 const state=()=>api.snapshot('overview');
 async function open(id){focusAt=document.activeElement;content.replaceChildren();status.textContent='';
  if(id==='nex'){
   const c=card(content,'NEX · assistente local','Respostas por regras e cache validado. Sem IA externa, transmissão de conversas ou microfone permanente.');const history=el('div',undefined,'nex-messages'),field=input('Pergunte sobre CPU, GPU, RAM, discos, cenas ou seções');field.maxLength=1000;
   const draw=items=>{history.replaceChildren();for(const r of items){const p=el('p',r.text,r.role==='user'?'nex-user':'nex-reply');history.append(p);}history.scrollTop=history.scrollHeight;};
   draw((await state()).conversation);const send=async()=>{if(!field.value.trim())return;const value=field.value.trim(),r=await api.askNex(value);field.value='';draw((await state()).conversation);status.textContent=r.history_error?'Histórico local indisponível; arquivo anterior preservado.':'';if(r.rgbRequest)window.loneRGBProviders.offer(c,r.rgbRequest,api);if(r.section){const b=button('Abrir seção indicada',()=>{dialog.close();navigate(r.section);},true);c.append(b);}};
   c.append(history,label('Mensagem ao NEX',field),button('Enviar ao NEX local',send));field.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();void send();}});
   c.append(note('Voz por toque depende de um provedor configurado. Nenhuma credencial de IA é solicitada ou incluída nesta versão.'));
  }else if(id==='hardware'){
   const c=card(content,'Detalhes da CPU e RAM','Consulta pontual do Windows. Clock informado não é medição calibrada; temperatura CPU permanece indisponível.');const kind=select([['hardware','CPU e núcleos'],['memory','Módulos RAM'],['disks','Volumes locais']]),target=out(c);c.prepend(label('Fonte',kind),button('Consultar detalhes',async()=>show(await api.inventory(kind.value),target)));
  }else if(id==='history'){
   const s=await state(),c=card(content,'Configurar histórico','Registro somente enquanto o LSR estiver aberto. Limite de 4 MiB e 20 mil pontos. Não inicia com o Windows.');const enabled=input('','checkbox'),retention=select([['1','1 hora'],['6','6 horas'],['24','24 horas'],['168','7 dias']]);enabled.checked=s.settings.history.enabled;retention.value=String(s.settings.history.retentionHours);
   c.append(label('Registrar histórico local',enabled),label('Retenção máxima',retention),button('Salvar histórico',async()=>{await api.configureHistory(enabled.checked,Number(retention.value));status.textContent='Política local salva. Novas medições dependem do coletor.';}),button('Exportar última hora em CSV',()=>api.exportHistory(60),true));
  }else if(id==='panels'){
   const c=card(content,'Touch Panel e overlay','Modos do mesmo aplicativo, com os mesmos sensores. Não há hooks, injeção ou alteração da resolução dos monitores.');const screens=await api.displays(),target=select(screens.map(d=>[String(d.id),(d.label||'Monitor')+' · '+d.width+' × '+d.height]));c.append(label('Tela de destino',target),button('Abrir Touch Panel',()=>api.openPanel('touch',Number(target.value))),button('Abrir overlay',()=>api.openPanel('overlay',Number(target.value)),true),note('Overlay convencional pode não aparecer em tela cheia exclusiva. FPS exige CSV externo válido.'));
  }else if(id==='environment'){
   await window.loneRGBProviders.mount(content,api);
  }
  if(!dialog.open)dialog.showModal();
 }
 function navigate(id){if(['hardware','history'].includes(id)){document.getElementById('tab-monitor').click();}else if(id==='games'){document.getElementById('tab-gamer').click();}else if(id==='overview'){document.getElementById('tab-controls').click();}else if(['nex','environment'].includes(id))void open(id);}
 document.addEventListener('click',e=>{const b=e.target.closest('[data-focus]');if(b)void open(b.dataset.focus).catch(()=>{});});api.onNavigate(navigate);
 const top=document.querySelector('.top-actions'),nex=button('NEX',()=>open('nex'),true);nex.id='nexOpen';top.prepend(nex);
 const monitor=document.getElementById('panel-monitor'),actions=el('div',undefined,'focus-actions');actions.append(button('Detalhes CPU / RAM',()=>open('hardware'),true),button('Configurar histórico',()=>open('history'),true),button('Touch Panel / Overlay',()=>open('panels'),true));monitor.querySelector('.page-heading').after(actions);
 const pc=document.querySelector('.pc-message'),pcFacts=document.querySelectorAll('.pc-facts strong'),localBadge=document.querySelector('.pc-intro .badge');
 const local=button('Verificar estado local',async()=>{const r=await api.inventory('localstatus'),item=r.items?.[0];pc.textContent=r.state==='available'?(item?.listener_count===0?'Agente HTTPS offline: nenhum listener em 8776.':'Listener 8776 presente; identidade e autenticação não verificadas.'):'Estado do agente indisponível nesta consulta.';localBadge.textContent='PC local ativo';pcFacts[0].textContent=item?.listener_count===0?'Sem listener':'Não autenticado';pcFacts[1].textContent='Sessão local ativa';pcFacts[2].textContent=r.observed_at?new Date(r.observed_at).toLocaleTimeString('pt-BR'):'Indisponível';},true);document.querySelector('.pc-actions').append(local);
 document.querySelector('.pc-intro h2').textContent='DEV-PC';document.querySelector('.pc-content .muted').textContent='Estado local e autenticação HTTPS são evidências distintas. Nenhuma identidade do Samsung é usada pelo desktop.';
 const gamer=document.getElementById('panel-gamer'),lib=card(gamer,'Biblioteca de jogos','Manifestos Steam lidos sob demanda. Nenhum jogo ou Steam é aberto por esta consulta.'),library=out(lib);
 lib.prepend(button('Identificar jogos instalados',async()=>show(await api.inventory('games'),library)));
 const mode=card(gamer,'Modo Gamer Inteligente · CS2','Consentimento desligado por padrão. Detecta CS2 a cada 5 s quando habilitado e modifica somente atividades do próprio LSR. Nenhuma otimização do Windows ou promessa de ganho de FPS.');
 const enabled=input('','checkbox'),reduce=input('','checkbox'),quiet=input('','checkbox'),overlay=input('','checkbox'),modeState=out(mode);
 const drawMode=value=>{if(!value)return;document.getElementById('dashboard').classList.toggle('game-active',value.state==='active'&&value.policy.quietUi);enabled.checked=value.policy.enabled;reduce.checked=value.policy.reduceHistory;quiet.checked=value.policy.quietUi;overlay.checked=value.policy.overlay;modeState.replaceChildren(note('Estado: '+({active:'Perfil Gamer ativo',idle:'Nenhum jogo detectado',not_verified:'Ainda não verificado',unavailable:'Verificação indisponível'}[value.state]||value.state)),note('Última verificação: '+(value.last_checked_at?new Date(value.last_checked_at).toLocaleTimeString('pt-BR'):'Nenhuma')));if(value.detected_game)modeState.append(note('CS2 detectado por processo; isso não comprova renderização ou FPS.'));show({items:value.sessions.map(s=>({game:s.game,start:new Date(s.started).toLocaleString('pt-BR'),outcome:s.outcome,end:s.ended?new Date(s.ended).toLocaleString('pt-BR'):null}))},modeState.appendChild(el('div')));};
 mode.prepend(label('Habilitar com consentimento',enabled),label('Reduzir polling de leitura para 2 s e histórico para 5 s durante o jogo',reduce),label('Reduzir animações do LSR',quiet),label('Abrir overlay ao detectar o jogo',overlay),button('Salvar preferências do Modo Gamer',async()=>drawMode(await api.gamer('configure',{v:1,enabled:enabled.checked,reduceHistory:reduce.checked,quietUi:quiet.checked,overlay:overlay.checked}))),button('Verificar CS2 agora · somente leitura',async()=>drawMode(await api.gamer('poll')),true));api.onGamer(drawMode);void api.gamer().then(drawMode);
 for(const badge of document.querySelectorAll('.game-layout .badge.locked'))badge.textContent='Confirmação local';document.querySelector('.cs2-card p').textContent='Abertura local via Steam com confirmação individual. Sem grants remotos.';document.querySelector('.steam-card p').textContent='Executável local e assinatura Valve verificados antes do despacho. Sem argumentos livres.';
 for(const target of ['steam','cs2']){const old=document.querySelector('[data-action="'+target+'"]');if(old){old.textContent='Solicitar abertura local';old.title='Requer confirmação nativa individual; sem grants remotos';old.disabled=false;old.addEventListener('click',async()=>{old.disabled=true;try{const r=await api.requestLocalLaunch(target);modeState.append(note('Abertura local: '+r.state+(r.state==='dispatched'?' · despacho não confirma jogo aberto':'')));}finally{old.disabled=false;}});}}
 const fps=card(gamer,'FPS e histórico de sessões','Importação preservada. O acompanhamento ao vivo depende de uma captura externa compatível já autorizada; o LSR não inicia PresentMon ou jogos.'),fpsOut=out(fps);
 fps.prepend(button('Importar CSV PresentMon',async()=>show(await api.importPresentmon(),fpsOut)),button('Acompanhar CSV externo',async()=>show(await api.attachFpsSource(),fpsOut),true),button('Encerrar e arquivar fonte',async()=>show(await api.stopFpsSource(),fpsOut),true),button('Ver sessões',async()=>{const r=await api.gameSessions();show({items:r.entries.flatMap(e=>e.report.streams.map(s=>({...s,points:undefined,imported_at:e.imported_at})))},fpsOut);},true));
 const updateFps=async()=>{if(document.hidden||gamer.hidden)return;const r=await api.fpsSnapshot();if(r.state!=='inactive')show(r,fpsOut);};const fpsTimer=setInterval(()=>void updateFps().catch(()=>{}),2000);window.addEventListener('pagehide',()=>clearInterval(fpsTimer));
 const shortcut=button('Touch Panel',()=>open('panels'),true);document.getElementById('panel-controls').querySelector('.page-heading').append(shortcut);
 document.querySelectorAll('[data-tool]').forEach(n=>n.hidden=true);
 const obsolete=document.getElementById('panel-tools');if(obsolete)obsolete.hidden=true;
})();
