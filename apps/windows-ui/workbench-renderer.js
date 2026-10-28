'use strict';
(()=>{
 const panel=document.getElementById('panel-tools'),body=document.getElementById('toolBody'),message=document.getElementById('toolMessage'),select=document.getElementById('toolSelect');if(!panel)return;
 const api=window.loneTools,model=window.loneWorkbenchModel;let current='overview',data=null,dispose=()=>{};
 const el=(tag,text,className)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;};
 const note=text=>el('p',text,'tool-note');
 const label=(text,node)=>{const n=el('label',text,'field');n.append(node);return n;};
 const input=(placeholder='',type='text')=>{const n=el('input');n.type=type;n.placeholder=placeholder;n.maxLength=200;return n;};
 const choose=(values)=>{const n=el('select');for(const value of values){const o=el('option',typeof value==='string'?value:value.title);o.value=typeof value==='string'?value:value.id;n.append(o);}return n;};
 function button(text,action,secondary=false){const n=el('button',text,secondary?'button':'button primary');n.type='button';n.addEventListener('click',async()=>{n.disabled=true;message.textContent='';try{await action();}catch{message.textContent='Operação indisponível ou entrada inválida. Nenhuma alteração de sistema foi executada.';}finally{n.disabled=false;}});return n;}
 function card(title,description){const n=el('section',undefined,'surface tool-card');n.append(el('h2',title));if(description)n.append(note(description));body.append(n);return n;}
 function output(parent){const n=el('div',undefined,'tool-output');parent.append(n);return n;}
 function show(value,target){target.replaceChildren();if(!value)return;const state=el('p',value.state?`Estado: ${value.state} · Fonte: ${value.source||'LSR local'}${value.simulation?' · SIMULAÇÃO':''}`:'Resultado local');target.append(state);if(value.observed_at)target.append(note('Verificado: '+new Date(value.observed_at).toLocaleString('pt-BR')));
  const items=value.items||value.entries||value.streams||value.actions;
  if(Array.isArray(items)&&items.length){const table=el('table'),keys=Object.keys(items[0]).slice(0,8),head=el('tr');for(const k of keys)head.append(el('th',k.replaceAll('_',' ')));const thead=el('thead');thead.append(head);table.append(thead);const tbody=el('tbody');for(const item of items.slice(0,150)){const row=el('tr');for(const key of keys){const v=item[key];row.append(el('td',v===null||v===undefined?'Indisponível':typeof v==='object'?JSON.stringify(v).slice(0,160):String(v).slice(0,180)));}tbody.append(row);}table.append(tbody);target.append(table);}else if(Array.isArray(items))target.append(note('Nenhum item disponível neste escopo.'));
  for(const [k,v]of Object.entries(value)){if(['items','entries','streams','actions','v','state','source','simulation','observed_at','settings'].includes(k))continue;target.append(note(k.replaceAll('_',' ')+': '+(typeof v==='object'?JSON.stringify(v):String(v))));}
 }
 function afterSave(result){message.textContent=result?.saved?'Configuração local salva. Nenhuma alteração aplicada ao Windows.':'Ação concluída.';return reload();}
 async function reload(){data=await api.snapshot(current);return data;}
 async function open(id){
  if(!api){message.textContent='Bridge de desenvolvimento indisponível';return;}
  dispose();dispose=()=>{};current=id;await reload();const section=data.catalog.SECTIONS.find(s=>s.id===id);if(!section)return;
  for(const b of document.querySelectorAll('[data-tool]'))b.setAttribute('aria-current',String(b.dataset.tool===id));
  for(const n of ['controls','monitor','gamer'])document.getElementById('panel-'+n).hidden=true;
  panel.hidden=false;document.getElementById('toolTitle').textContent=section.title;document.getElementById('toolDescription').textContent=section.description;document.getElementById('breadcrumb').textContent=section.title;
  document.getElementById('toolSafety').textContent=data.enabled?'Ferramentas locais · consultas sob demanda · alterações no Windows e dispositivos bloqueadas':'Modo de revisão · abra com perfil de desenvolvimento isolado para habilitar ferramentas locais';
  select.value=id;body.replaceChildren();message.textContent='';document.getElementById('workspace').scrollTop=0;
  const C=data.catalog;
  if(id==='overview'){
   const grid=el('div',undefined,'tool-grid');body.append(grid);for(const s of C.SECTIONS.filter(s=>s.id!=='overview')){const c=el('article',undefined,'surface tool-card');c.append(el('h2',s.title),note(s.description),button('Abrir ferramenta',()=>open(s.id),true));grid.append(c);}
   const c=card('Estado real da implementação','Inventário e ferramentas locais são funcionais no código. Ações privilegiadas, conectores físicos, captura FPS ao vivo e IA exigem provedores ou homologação.');c.append(note('Android congelado. Agente HTTPS operacional e instalações permanecem fora deste módulo.'));
  }
  if(id==='hardware'){
   const c=card('Inventário do PC','Informações adicionais são obtidas somente ao atualizar. Sensores contínuos continuam usando o coletor existente.');
   const kind=choose([{id:'hardware',title:'CPU e núcleos'},{id:'memory',title:'Módulos RAM e frequência'},{id:'disks',title:'Volumes e capacidade'},{id:'network',title:'Adaptadores e tráfego'},{id:'drivers',title:'Drivers: somente leitura'},{id:'peripherals',title:'Periféricos PnP'}]);const out=output(c);
   c.prepend(button('Atualizar informações',async()=>show(await api.inventory(kind.value),out)),label('Fonte de inventário',kind));
   c.append(button('Abrir sensores contínuos',()=>{panel.hidden=true;document.getElementById('tab-monitor').click();},true));
   c.append(note('Temperatura/energia CPU, bateria e firmware ausentes são Indisponíveis. Clock informado pelo Windows não é medição calibrada.'));
  }
  if(id==='maintenance'){
   const c=card('Prévia de limpeza','Inspeciona apenas o cache próprio do módulo. Dados pessoais, credenciais, caches ativos e arquivos Windows são excluídos.');const out=output(c);c.prepend(button('Inspecionar cache elegível',async()=>show(await api.cleanupPreview(),out)));
   const r=card('Planos de diagnóstico e reparo','Exibe comandos fixos, privilégios, efeitos e limitações de reversão. Não inicia SFC, DISM, atualizações ou reparos.');const plan=choose(C.REPAIRS),target=output(r);r.prepend(label('Procedimento',plan),button('Revisar procedimento',async()=>show(await api.repairPlan(plan.value),target)));
   const i=card('Gerenciamento somente leitura');const category=choose([{id:'processes',title:'Processos: consumo acumulado e RAM'},{id:'services',title:'Serviços e estados'},{id:'startup',title:'Entradas de inicialização'},{id:'events',title:'Falhas recentes: metadados'}]),view=output(i);i.prepend(label('Categoria',category),button('Consultar inventário',async()=>show(await api.inventory(category.value),view)));
  }
  if(id==='optimization'){
   const c=card('Perfis reversíveis','O perfil organiza escolhas dentro do LSR. Salvar não altera Registro, serviços, energia, aplicativos ou segurança.');
   const name=choose(C.PROFILES);name.value=data.settings.profile.name;c.append(label('Perfil',name));const selected=new Map();
   for(const a of C.ADJUSTMENTS){const row=el('article',undefined,'tool-adjustment'),check=input('','checkbox');check.checked=data.settings.profile.adjustments.includes(a.id);selected.set(a.id,check);const h=el('label',a.title);h.prepend(check);row.append(h,note('Estado Windows: Não verificado'),note(a.benefit),note('Efeitos: '+a.sideEffect),note(`Admin: ${a.admin?'Sim':'Não'} · Reinício: ${a.restart}`),note('Reversão: '+a.rollback));c.append(row);}
   c.append(button('Salvar perfil no LSR',async()=>afterSave(await api.saveProfile(name.value,[...selected].filter(([,n])=>n.checked).map(([id])=>id)))));
   c.append(note('Não há limpeza agressiva de RAM ou promessa de aumento de FPS. Defender, SmartScreen, firewall e Windows Update não são desabilitados.'));
  }
  if(id==='applications'){
   const c=card('Aplicativos instalados','Sem instalação, atualização ou desinstalação automática. A disponibilidade de atualizações precisa de fonte verificável.');const out=output(c);c.prepend(button('Ler aplicativos instalados',async()=>show(await api.inventory('applications'),out)));
   const b=card('Conjunto pós-formatação','Lista local com IDs WinGet conhecidos. Manifesto e origem precisam ser conferidos antes da futura instalação.');const name=input('Nome do conjunto'),checks=new Map();b.append(label('Nome',name));for(const p of C.PACKAGES){const check=input('','checkbox'),row=el('label',p.name+' · '+p.id,'tool-check');row.prepend(check);b.append(row);checks.set(p.id,check);}b.append(button('Salvar conjunto',async()=>{await afterSave(await api.saveBundle(name.value,[...checks].filter(([,n])=>n.checked).map(([id])=>id)));show({items:data.settings.bundles},out);}));
   b.append(button('Exportar configurações e listas',()=>api.exportSettings(),true),button('Importar lista validada',async()=>{await api.importSettings();await open(id);},true));show({items:data.settings.bundles},output(b));
  }
  if(id==='peripherals'){
   const c=card('Mouse e teclado','Hardware informado: Zaopin Z2, GravaStar 60V Pro e Razer BlackShark V3 Pro. A identificação precisa ser conferida com o dispositivo.');const out=output(c);c.prepend(button('Ler dispositivos PnP',async()=>show(await api.inventory('peripherals'),out)));
   const t=card('Teste de entrada em foco','Não usa hooks globais. Intervalos do navegador não medem polling rate ou latência física. Teste só recebe eventos dentro da área ativa.');const area=el('div','Inicie e clique aqui. Mova o mouse ou pressione teclas.','input-test-area');area.tabIndex=0;const stats=el('pre');let active=false,session;
   const render=()=>{stats.textContent=JSON.stringify(session.view(),null,2);};
   t.append(button('Iniciar teste local',()=>{session=model.createInputSession();active=true;area.focus();render();}),button('Encerrar teste',()=>{active=false;area.textContent='Teste encerrado.';},true),area,stats);
   for(const type of ['pointermove','click','keydown','keyup'])area.addEventListener(type,e=>{if(!active)return;if(type==='keydown'||type==='keyup')e.preventDefault();session.record({type:type==='pointermove'?'move':type==='keydown'?'down':type==='keyup'?'up':'click',at:performance.now(),code:e.code});render();});dispose=()=>{active=false;};
   const audio=card('Áudio e headset','Enumeração local sob demanda. Microfone, bateria do receptor, DPI e firmware permanecem indisponíveis sem integração/permissão validada.');const devices=output(audio);audio.append(button('Listar entradas e saídas de áudio',async()=>{if(!navigator.mediaDevices?.enumerateDevices)throw Error();const list=await navigator.mediaDevices.enumerateDevices();show({items:list.map((d,i)=>({kind:d.kind,label:d.label||'Dispositivo '+(i+1),state:d.label?'identificado':'permissão limitada'}))},devices);},true));
  }
  if(id==='display'){
   const c=card('Monitores e GPU','Consulta o Electron e o inventário; não altera resolução, frequência ou drivers.');const info=output(c);c.prepend(button('Identificar monitores',async()=>show({items:await api.displays()},info)),button('Versões de drivers',async()=>show(await api.inventory('drivers'),info),true));
   const t=card('Padrões visuais','Observação visual de pixels, cores, gradientes, contraste e movimento. Não é um instrumento calibrado nem mede ghosting ou tempo de resposta.');const pattern=choose(['Preto','Branco','Vermelho','Verde','Azul','Gradiente','Contraste','Movimento']),stage=el('div',undefined,'display-pattern');stage.dataset.pattern='Preto';stage.setAttribute('role','img');stage.setAttribute('aria-label','Padrão visual de tela');const moving=el('span');stage.append(moving);pattern.addEventListener('change',()=>stage.dataset.pattern=pattern.value);t.append(label('Padrão',pattern),stage,note('O teste ocupa apenas a janela do aplicativo. Nenhum modo de monitor é aplicado.'));
  }
  if(id==='network'){
   const c=card('Rede e internet sob demanda','Ping envia quatro sondas apenas ao pressionar Executar. DNS resolve o destino informado. Sem teste de velocidade ou tráfego intenso automático.');const target=input('Destino: IP ou hostname'),kind=choose([{id:'ping',title:'RTT, jitter e perda'},{id:'dns',title:'Resolução DNS'}]),out=output(c);c.prepend(label('Destino configurado pelo usuário',target),label('Teste',kind),button('Executar teste de leitura',async()=>show(await api.networkTest(kind.value,target.value.trim()),out)));
   const a=card('Tráfego e velocidade da interface','São necessárias duas leituras para calcular bytes/s. Velocidade do link não é throughput de internet.');const view=output(a);a.prepend(button('Atualizar adaptadores',async()=>show(await api.inventory('network'),view),true));
  }
  if(id==='games'){
   const c=card('Sessões FPS / PresentMon','Importação de CSV com frames apresentados. Não inicia captura ao vivo, jogos, hooks, injeção ou acesso ao VAC.');const out=output(c);c.prepend(button('Importar CSV PresentMon',async()=>show(await api.importPresentmon(),out)));c.append(note('FPS médio = frames / soma dos frametimes; 1% Low = inverso da média do 1% mais lento, mínimo 100 frames. Streams de processo/swapchain ficam separados.'));
   const p=card('Perfis por jogo','Configuração local; não altera arquivos de jogos ou configurações Windows. Biblioteca e executores Steam/CS2 mantêm bloqueio.');const name=input('Nome do jogo'),monitoring=input('','checkbox'),overlay=input('','checkbox');p.append(label('Jogo',name),label('Desejar monitoramento',monitoring),label('Desejar overlay',overlay),button('Salvar perfil',async()=>afterSave(await api.saveGameProfile({name:name.value,monitoring:monitoring.checked,overlay:overlay.checked}))));show({items:data.settings.gameProfiles},output(p));
  }
  if(id==='environment'){
   const c=card('Dispositivos e conectores','Nenhum equipamento é acionado. Controladores precisam estar disponíveis, configurados e homologados.');show({items:C.CONNECTORS.map(c=>({name:c.title,state:c.state,support:c.support}))},output(c));
   const d=card('Configurar dispositivo no LSR');const name=input('Nome'),identifier=input('Identificador, ex.: lampada'),connector=choose(C.CONNECTORS),entity=input('Entidade opcional, ex.: light.quarto');d.append(label('Nome',name),label('ID local',identifier),label('Conector',connector),label('Entidade',entity),button('Salvar dispositivo',async()=>{await afterSave(await api.saveDevice({id:identifier.value,name:name.value,connector:connector.value,entity:entity.value}));await open(id);}));show({items:data.settings.devices},output(d));
   const s=card('Cenas com prévia');const scene=input('Gamer, Trabalho, Relaxar, Noturno…'),color=input('','color'),brightness=input('','range');color.value='#ff153f';brightness.min=0;brightness.max=100;brightness.value=50;const devices=new Map();s.append(label('Nome',scene),label('Cor',color),label('Brilho',brightness));for(const device of data.settings.devices){const check=input('','checkbox'),row=el('label',device.name,'tool-check');row.prepend(check);s.append(row);devices.set(device.id,check);}s.append(button('Salvar cena',async()=>{await afterSave(await api.saveScene({name:scene.value,deviceIds:[...devices].filter(([,n])=>n.checked).map(([id])=>id),color:color.value,brightness:Number(brightness.value)}));await open(id);}));
   for(const v of data.settings.scenes){const out=output(s);s.append(button('Prévia: '+v.name,async()=>show(await api.scenePreview(v.id),out),true));}
  }
  if(id==='nex'){
   const c=card('NEX · Next Environment Executive','Modo local por regras e evidências. Nenhuma IA externa, transmissão de dados ou escuta contínua. Conversa desta sessão somente em memória.');const chat=el('div',undefined,'nex-messages'),entry=input('Pergunte sobre estado, hardware, rede ou ferramentas');entry.maxLength=1000;
   c.append(chat,label('Mensagem',entry),button('Enviar ao NEX local',async()=>{const text=entry.value;const r=await api.askNex(text);chat.append(el('p',text,'nex-user'),el('p',r.reply,'nex-reply'));entry.value='';if(r.section)chat.append(button('Abrir ferramenta recomendada',()=>open(r.section),true));}),note('Voz: microfone por toque e motor configurável ainda não habilitados. Nenhuma ação sensível é executada por texto.'));
  }
  if(id==='audit'){
   const c=card('Backup e importação de configurações','Exporta apenas dados deste módulo, sem credenciais, certificados ou bancos operacionais. Importação validada; não aplica configurações Windows.');c.append(button('Exportar configurações',()=>api.exportSettings()),button('Importar configurações validadas',async()=>{await api.importSettings();await open(id);},true));
   const a=card('Auditoria de ações locais','Histórico limitado a 120 registros de códigos e resultados; não registra texto de conversas ou segredos.');show(await api.readAudit(),output(a));
   a.append(note('Pontos de restauração e rollback de ações Windows exigem futura execução especificamente autorizada. Desinstalações e reparos não possuem reversão completa garantida.'));
  }
 }
 document.querySelectorAll('[data-tool]').forEach(b=>b.addEventListener('click',()=>void open(b.dataset.tool).catch(()=>message.textContent='Central indisponível neste contexto.')));
 document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{dispose();dispose=()=>{};panel.hidden=true;}));
 select.addEventListener('change',()=>void open(select.value));
 if(api)api.snapshot('overview').then(value=>{data=value;for(const s of value.catalog.SECTIONS){const o=el('option',s.title);o.value=s.id;select.append(o);}}).catch(()=>{});
 window.addEventListener('pagehide',()=>dispose());
})();
