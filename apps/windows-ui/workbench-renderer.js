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
 function show(value,target){window.loneInventoryView.render(document,value,target);}
 function afterSave(result){message.textContent=result?.saved?'Configuração local salva. Nenhuma alteração aplicada ao Windows.':'Ação concluída.';return reload();}
 function showFps(value,target){
  target.replaceChildren();const states={inactive:'Fonte desativada',awaiting_frames:'Aguardando novos frames',available:'Leitura do arquivo atualizada',stale:'Dados desatualizados',unavailable:'Fonte indisponível'};
  target.append(el('p',states[value?.state]||'Sem leitura'),note('Origem: CSV externo PresentMon · captura pelo LSR desativada'));
  if(value?.observed_at)target.append(note('Última atualização do arquivo: '+new Date(value.observed_at).toLocaleTimeString('pt-BR')));
  if(value?.archived)target.append(note('Resumo arquivado no histórico de sessões.'));
  for(const stream of value?.report?.streams||[]){
   const c=el('article',undefined,'history-chart');c.append(el('h3',stream.name));
   const table=el('table'),heading=el('tr'),row=el('tr');
   for(const [key,title,unit]of [['average_fps','FPS médio',' FPS'],['mean_frametime_ms','Frametime médio',' ms'],['one_percent_low_fps','1% Low',' FPS']]){heading.append(el('th',title));row.append(el('td',Number.isFinite(stream[key])?stream[key].toLocaleString('pt-BR',{maximumFractionDigits:2})+unit:'Indisponível'));}
   table.append(heading,row);c.append(table,note(stream.samples+' frames apresentados · não equivale a FPS exibidos'));
   if(stream.points?.length){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg'),line=document.createElementNS(svg.namespaceURI,'polyline'),max=Math.max(1,...stream.points);svg.setAttribute('viewBox','0 0 300 80');svg.setAttribute('role','img');svg.setAttribute('aria-label','Frametimes em milissegundos, amostragem limitada a 120 pontos');line.setAttribute('points',stream.points.map((ms,i)=>`${5+290*i/Math.max(1,stream.points.length-1)},${75-65*ms/max}`).join(' '));svg.append(line);c.append(svg);}
   target.append(c);
  }
 }
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
   const history=card('Histórico local limitado','Reutiliza as amostras do coletor existente. Limite de 4 MiB e 20 mil pontos; períodos maiores dependem dos dados retidos. Sem coletor não há novas amostras.');
   const enabled=input('','checkbox'),hours=choose(['1','6','24','168']);enabled.checked=data.settings.history.enabled;hours.value=String(data.settings.history.retentionHours);
   history.append(label('Registrar histórico enquanto o aplicativo estiver ativo',enabled),label('Retenção máxima em horas',hours),button('Salvar política do histórico',async()=>afterSave(await api.configureHistory(enabled.checked,Number(hours.value)))),button('Exportar última hora em CSV',()=>api.exportHistory(60),true));
  }
  if(id==='maintenance'){
   const c=card('Prévia de limpeza','Inspeciona apenas o cache próprio do módulo. Dados pessoais, credenciais, caches ativos e arquivos Windows são excluídos.');const out=output(c);c.prepend(button('Inspecionar cache elegível',async()=>show(await api.cleanupPreview(),out)));
   const meta=card('Temporários: inspeção sem exclusão','Somente metadados, arquivos tmp/log/bak antigos e raízes fixas. Varredura limitada; arquivos pessoais, dump e debug.log ficam excluídos. Nenhum botão de limpeza é habilitado.');const scope=choose([{id:'own',title:'Cache próprio LSR'},{id:'user_temp',title:'Temporários do usuário'},{id:'windows_temp',title:'Temporários Windows: acesso pode ser negado'}]),metaOut=output(meta);meta.prepend(label('Escopo da prévia',scope),button('Calcular prévia limitada',async()=>show(await api.inspectTemp(scope.value),metaOut),true));
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
  if(id==='peripherals'){
   const mic=card('Microfone: nível local por toque','Ativa somente após consentimento explícito na janela nativa. Limite de 10 segundos, sem gravação ou rede. Não mede SPL, bateria ou qualidade do headset.');const status=el('p','Inativo'),meter=el('meter');meter.min=0;meter.max=1;meter.value=0;const audio=window.loneAudioTest.createAudioTest({onLevel:v=>{meter.value=v.rms;status.textContent='Nível digital RMS: '+v.rms.toFixed(3)+' · pico '+v.peak.toFixed(3);},onState:s=>status.textContent=s==='stopped'?'Microfone inativo':s==='permission_required'?'Aguardando permissão local':'Leitura local: até 10 segundos'});const previous=dispose;dispose=()=>{previous();void audio.stop();};mic.append(button('Testar microfone por 10 s',()=>audio.start()),button('Parar microfone',()=>audio.stop(),true),meter,status);
  }
  if(id==='display'){
   const panels=card('Touch Panel e overlay local','Janelas convencionais compartilham o mesmo coletor. Sem injeção; overlay pode não aparecer em tela cheia exclusiva. Posição recuperada se o monitor for desconectado.');
   const displays=choose([]);panels.append(label('Monitor de destino',displays));api.displays().then(items=>{for(const d of items){const o=el('option',(d.label||'Monitor')+' · '+d.width+' × '+d.height);o.value=d.id;displays.append(o);}});
   panels.append(button('Abrir Touch Panel',()=>api.openPanel('touch',Number(displays.value))),button('Abrir overlay de telemetria',()=>api.openPanel('overlay',Number(displays.value)),true));
   const c=card('Monitores e GPU','Consulta o Electron e o inventário; não altera resolução, frequência ou drivers.');const info=output(c);c.prepend(button('Identificar monitores',async()=>show({items:await api.displays()},info)),button('Versões de drivers',async()=>show(await api.inventory('drivers'),info),true));
   const t=card('Padrões visuais','Observação visual de pixels, cores, gradientes, contraste e movimento. Não é um instrumento calibrado nem mede ghosting ou tempo de resposta.');const pattern=choose(['Preto','Branco','Vermelho','Verde','Azul','Gradiente','Contraste','Movimento']),stage=el('div',undefined,'display-pattern');stage.dataset.pattern='Preto';stage.setAttribute('role','img');stage.setAttribute('aria-label','Padrão visual de tela');const moving=el('span');stage.append(moving);pattern.addEventListener('change',()=>stage.dataset.pattern=pattern.value);t.append(label('Padrão',pattern),stage,note('O teste ocupa apenas a janela do aplicativo. Nenhum modo de monitor é aplicado.'));
  }
  if(id==='network'){
   const c=card('Rede e internet sob demanda','Ping envia quatro sondas apenas ao pressionar Executar. DNS resolve o destino informado. Sem teste de velocidade ou tráfego intenso automático.');const target=input('Destino: IP ou hostname'),kind=choose([{id:'ping',title:'RTT, jitter e perda'},{id:'dns',title:'Resolução DNS'}]),out=output(c);c.prepend(label('Destino configurado pelo usuário',target),label('Teste',kind),button('Executar teste de leitura',async()=>show(await api.networkTest(kind.value,target.value.trim()),out)));
   const a=card('Tráfego e velocidade da interface','São necessárias duas leituras para calcular bytes/s. Velocidade do link não é throughput de internet.');const view=output(a);a.prepend(button('Atualizar adaptadores',async()=>show(await api.inventory('network'),view),true));
  }
  if(id==='games'){
   const external=card('Acompanhar CSV externo PresentMon','Escolha um CSV que uma captura externa já autorizada esteja atualizando. O LSR não inicia PresentMon, ETW, Steam ou jogos. Somente linhas acrescentadas depois da seleção contam; sem linhas novas por 3 segundos os valores expiram.');const liveOut=output(external);
   external.append(button('Selecionar CSV externo',async()=>showFps(await api.attachFpsSource(),liveOut)),button('Encerrar e arquivar leitura',async()=>showFps(await api.stopFpsSource(),liveOut),true),note('Limite de 2 MiB por arquivo acompanhado. FPS apresentados, não FPS exibidos. Nenhum jogo ao vivo homologado nesta etapa. Overlay compartilha a mesma fonte e o mesmo coletor CPU/GPU.'));
   let fpsPending=false;const updateFps=async()=>{if(fpsPending||document.hidden)return;fpsPending=true;try{showFps(await api.fpsSnapshot(),liveOut);}catch{liveOut.textContent='Fonte FPS indisponível';}finally{fpsPending=false;}};
   void updateFps();const fpsTimer=setInterval(()=>void updateFps(),2000);dispose=()=>clearInterval(fpsTimer);
   const library=card('Biblioteca local','Catálogo manual e manifestos Steam sob demanda. Não executa atalhos, jogos ou Steam.');const libraryOut=output(library),gameName=input('Nome do jogo'),appId=input('AppID Steam opcional');library.prepend(button('Detectar manifestos Steam',async()=>show(await api.inventory('games'),libraryOut)),label('Nome',gameName),label('AppID: apenas identificação',appId),button('Adicionar ao catálogo',async()=>{await afterSave(await api.saveGame({name:gameName.value,steamAppId:appId.value?Number(appId.value):null}));await open(id);},true));show({items:data.settings.games},libraryOut);
   const archive=card('Histórico de sessões importadas','Horário de importação não é o início da sessão. Não existe captura FPS ao vivo ativa.');archive.append(button('Consultar sessões locais',async()=>{const r=await api.gameSessions();show({items:r.entries.flatMap(e=>e.report.streams.map(s=>({...s,imported_at:e.imported_at,points:undefined})))},output(archive));},true));
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
   const c=card('NEX · Next Environment Executive','Modo local por regras e cache validado. Histórico local limitado a 40 mensagens. Nenhuma IA externa, transmissão de dados ou escuta contínua.');const chat=el('div',undefined,'nex-messages'),entry=input('Pergunte sobre estado, hardware, rede ou ferramentas');entry.maxLength=1000;
   for(const r of data.conversation||[])chat.append(el('p',r.text,r.role==='user'?'nex-user':'nex-reply'));
   c.append(chat,label('Mensagem',entry),button('Enviar ao NEX local',async()=>{const text=entry.value;const r=await api.askNex(text);chat.append(el('p',text,'nex-user'),el('p',r.reply,'nex-reply'));if(r.history_error)chat.append(note('Histórico indisponível; arquivo anterior preservado.'));entry.value='';if(r.section)chat.append(button('Abrir ferramenta recomendada',()=>open(r.section),true));}),note('Voz: microfone por toque e motor configurável ainda não habilitados. Nenhuma ação sensível é executada por texto.'));
  }
  if(id==='audit'){
   const c=card('Backup e importação de configurações','Exporta apenas dados deste módulo, sem credenciais, certificados ou bancos operacionais. Importação validada; não aplica configurações Windows.');c.append(button('Exportar configurações',()=>api.exportSettings()),button('Importar configurações validadas',async()=>{await api.importSettings();await open(id);},true));
   const a=card('Auditoria de ações locais','Histórico limitado a 120 registros de códigos e resultados; não registra texto de conversas ou segredos.');show(await api.readAudit(),output(a));
   a.append(note('Pontos de restauração e rollback de ações Windows exigem futura execução especificamente autorizada. Desinstalações e reparos não possuem reversão completa garantida.'));
  }
 }
 document.querySelectorAll('[data-tool]').forEach(b=>b.addEventListener('click',()=>void open(b.dataset.tool).catch(()=>message.textContent='Central indisponível neste contexto.')));
 if(api){const link=button('Biblioteca, perfis e sessões FPS',()=>open('games'),true);link.dataset.openTool='games';document.getElementById('panel-gamer')?.prepend(link);}
 document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{dispose();dispose=()=>{};panel.hidden=true;}));
 select.addEventListener('change',()=>void open(select.value));
 if(api)api.onNavigate(section=>void open(section));
 if(api)api.snapshot('overview').then(value=>{data=value;for(const s of value.catalog.SECTIONS){const o=el('option',s.title);o.value=s.id;select.append(o);}}).catch(()=>{});
 window.addEventListener('pagehide',()=>dispose());
})();
