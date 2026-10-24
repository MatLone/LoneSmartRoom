'use strict';
(() => {
  // Integrated Electron renderer: window controls only; no operational client, storage or launch handler.
  const icons={
    sliders:'<path d="M4 7h4m4 0h8M4 17h8m4 0h4"/><circle cx="10" cy="7" r="2"/><circle cx="14" cy="17" r="2"/>',
    activity:'<path d="M2 12h5l3-8 4 16 3-8h5"/>',
    monitor:'<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8m-4-4v4"/>',
    gamepad:'<path d="M7 7h10c3 0 4 3 4 7s-1 5-3 3l-2-2H8l-2 2c-2 2-3 0-3-3s1-7 4-7Z"/><path d="M6 10v4m-2-2h4m8-1h.1m2 2h.1"/>',
    shield:'<path d="m12 3 8 4v5c0 5-8 9-8 9s-8-4-8-9V7Z"/><path d="m8 12 3 3 5-6"/>',
    lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v3"/>',
    chip:'<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 1v4m6-4v4M9 19v4m6-4v4M1 9h4m-4 6h4m14-6h4m-4 6h4"/>',
    gpu:'<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="9" cy="12" r="3"/><path d="M15 10h4m-4 4h4M6 18v3m4-3v3"/>',
    memory:'<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10v4m4-4v4m4-4v4m4-4v4M6 18v3m4-3v3m4-3v3m4-3v3"/>',
    temperature:'<path d="M9 14V5a3 3 0 0 1 6 0v9a5 5 0 1 1-6 0Z"/><path d="M12 8v9"/>',
    lamp:'<path d="M8 15c-4-4-4-11 4-12 8 1 8 8 4 12l-1 3H9Z"/><path d="M9 21h6m-6-3h6"/>',
    led:'<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10v4m5-4v4m5-4v4M7 2v1m10-1v1M7 21v1m10-1v1"/>',
    fan:'<circle cx="12" cy="12" r="2"/><path d="M11 10C4 2 14 0 15 6c.3 2-1 3-2 4m1 1c8-7 10 3 4 4-2 .3-3-1-4-2m-1 1c7 8-3 10-4 4-.3-2 1-3 2-4m-1-1c-8 7-10-3-4-4 2-.3 3 1 4 2"/>',
    tv:'<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M8 22h8m-4-3v3"/>',
    smartphone:'<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 5h4m-3 14h2"/>',
    globe:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
    chart:'<path d="M3 3v18h18M6 15l4-5 4 3 5-7"/>',
    tray:'<path d="M4 14v6h16v-6M8 14l4 4 4-4M12 3v14"/>',
    widget:'<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M14 3v18m0-11h7"/>',
    chevron:'<path d="m9 6 6 6-6 6"/>',arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>',minus:'<path d="M5 12h14"/>',maximize:'<rect x="5" y="5" width="14" height="14" rx="1"/>',close:'<path d="m6 6 12 12M18 6 6 18"/>',
    gear:'<path stroke-linejoin="bevel" d="M9.836 4.923 L10.514 2.617 L13.486 2.617 L14.164 4.923 L15.474 5.466 L17.584 4.314 L19.686 6.416 L18.534 8.526 L19.077 9.836 L21.383 10.514 L21.383 13.486 L19.077 14.164 L18.534 15.474 L19.686 17.584 L17.584 19.686 L15.474 18.534 L14.164 19.077 L13.486 21.383 L10.514 21.383 L9.836 19.077 L8.526 18.534 L6.416 19.686 L4.314 17.584 L5.466 15.474 L4.923 14.164 L2.617 13.486 L2.617 10.514 L4.923 9.836 L5.466 8.526 L4.314 6.416 L6.416 4.314 L8.526 5.466 Z"/><circle cx="12" cy="12" r="3.1"/>'
  };
  const svg=name=>`<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name]||icons.lock}</svg>`;
  const devices=[['lamp','Lâmpada','Iluminação ambiente'],['led','Fita LED','Iluminação de destaque'],['fan','Ventilador','Climatização'],['tv','Smart TV','Entretenimento']];
  document.getElementById('deviceGrid').innerHTML=devices.map(([id,name,caption])=>`<article class="device"><div class="device-top">${svg(id)}<button class="switch" disabled aria-label="${name}: integração indisponível"></button></div><h3>${name}</h3><p>${caption}</p><div class="device-foot"><span>Integração indisponível</span><button class="icon-button" data-panel="${id}" aria-label="Ver configuração de ${name}">${svg('gear')}</button></div></article>`).join('');
  const sensors=[['chip','CPU','%'],['gpu','GPU','%'],['memory','RAM','GB'],['temperature','Temperatura','°C']];
  document.getElementById('miniSensors').innerHTML=sensors.map(([icon,label])=>`<div class="mini-sensor"><div>${svg(icon)}${label}</div><strong>—</strong><small>Coleta não implementada</small></div>`).join('');
  document.getElementById('sensorGrid').innerHTML=sensors.map(([icon,label,unit])=>`<article class="sensor"><div class="sensor-top"><span>${label}</span>${svg(icon)}</div><div class="value">—<span>${unit}</span></div><small>Sem medição disponível</small></article>`).join('');
  document.querySelectorAll('[data-icon]').forEach(n=>n.innerHTML=svg(n.dataset.icon));
  const tabs=[...document.querySelectorAll('[role=tab]')],main=document.getElementById('workspace');
  const names={controls:'Controles',monitor:'Monitoramento PC',gamer:'Gamer Launcher'};
  function select(tab){if(!(tab in names))return;tabs.forEach(b=>{const active=b.dataset.tab===tab;b.setAttribute('aria-selected',String(active));document.getElementById('panel-'+b.dataset.tab).hidden=!active;});document.getElementById('breadcrumb').textContent=names[tab];main.scrollTop=0;}
  tabs.forEach((b,i)=>{b.addEventListener('click',()=>select(b.dataset.tab));b.addEventListener('keydown',e=>{let next;if(e.key==='ArrowRight'||e.key==='ArrowDown')next=(i+1)%tabs.length;if(e.key==='ArrowLeft'||e.key==='ArrowUp')next=(i+tabs.length-1)%tabs.length;if(e.key==='Home')next=0;if(e.key==='End')next=tabs.length-1;if(next!==undefined){e.preventDefault();select(tabs[next].dataset.tab);tabs[next].focus();}});});
  document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.go)));
  document.getElementById('grantsCount').textContent='—';
  document.getElementById('auditTime').textContent='Identidade desktop e consulta de permissões ainda não implementadas.';
  const dialog=document.getElementById('settingsDialog');let returnFocus;
  const row=(title,status)=>`<div class="provider-row"><span>${title}</span><span class="badge">${status}</span></div>`;
  const note=text=>`<div class="dialog-note">${text}</div>`;
  const panels={
    connection:['CONEXÃO E SEGURANÇA','Meu computador','<p>O dashboard ainda não possui um cliente autenticado. A integração futura reutilizará a identidade TLS, a autenticação por dispositivo e as autorizações do agente existente.</p>'+row('Conexão HTTPS desktop','Não integrada')+row('Última consulta','Nenhuma')+'<label class="field">Servidor HTTPS<input disabled placeholder="Disponível após integração aprovada"></label><button class="button" disabled>'+svg('lock')+'Vincular dashboard</button>'+note('A conexão autenticada permanece bloqueada até corrigir e validar a pendência TLS. Nenhuma credencial é solicitada ou copiada nesta etapa.')],
    permissions:['AUTORIZAÇÕES','Você autoriza. O agente valida.','<p>Cada dispositivo precisa de autorização individual por aplicativo. A interface não concede grants automaticamente.</p>'+row('Steam','Bloqueado na interface')+row('Counter-Strike 2','Bloqueado na interface')+'<p class="muted">Nenhum registro do Samsung é usado como identidade desktop. Sem cliente autenticado, as permissões não são consultadas.</p>'+note('Solicitado → Aceito → Executado ou Falha. “Executado” confirma o despacho, não a abertura real. A confirmação do usuário e as verificações do agente continuarão obrigatórias.')],
    sensors:['ARQUITETURA EM AVALIAÇÃO','Sensores reais, quando disponíveis.','<p>Um provedor local separado irá fornecer valor, unidade, origem e horário de cada amostra. Dados ausentes ou antigos terão indicação própria.</p>'+row('CPU e RAM','APIs Windows em avaliação')+row('GPU','Provedor a validar')+row('Temperaturas','Sem provedor')+note('Nenhum coletor foi iniciado. Não são instalados drivers, serviços ou componentes de monitoramento nesta etapa.')],
    wol:['ANDROID PRESERVADO','Wake-on-LAN','<p>O envio real permanece no aplicativo Android validado. Ele funciona de forma independente da disponibilidade do agente Windows.</p>'+row('Emissor Android','Preservado')+row('Emissor desktop','Não integrado')+note('Não há envio de pacote nesta versão. “Pacote enviado” não confirma que o computador despertou.')],
    about:['IDENTIDADE OFICIAL','Lone Smart Room','<div class="dialog-identity"><img src="assets/brand/windows-icon.svg" width="76" height="76" alt="Ícone oficial Windows"><span>Ícone oficial Windows<br>Símbolo angular · vermelho neon</span></div><p>Dashboard Windows 2.0 integrado ao Electron existente e baseado na interface Android dev.7 validada.</p>'+row('NEX','Planejado')+row('SignalRGB e Home Assistant','Integrações futuras')+note('Navegação, painéis e janela widget estão integrados. Steam, CS2, energia e coleta de sensores permanecem indisponíveis neste cliente.')]
  };
  for(const [id,title,caption]of devices)panels[id]=[caption.toUpperCase(),title,'<p>Integração ainda não implementada. Nenhum comando é enviado ao equipamento.</p>'+row('Estado do dispositivo','Desconhecido')+'<div class="provider-row"><span>Alimentação</span><button class="switch" disabled aria-label="Alimentação indisponível"></button></div><label class="field">Integração<select disabled><option>Ainda não disponível</option></select></label><button class="button" disabled>Salvar configuração</button>'];
  document.addEventListener('click',e=>{const b=e.target.closest('[data-panel]');if(!b)return;const data=panels[b.dataset.panel];if(!data)return;returnFocus=b;document.getElementById('dialogEyebrow').textContent=data[0];document.getElementById('dialogTitle').textContent=data[1];document.getElementById('dialogBody').innerHTML=data[2];dialog.showModal();});
  document.getElementById('dialogClose').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>returnFocus?.focus());
  document.querySelectorAll('[data-metric]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-metric]').forEach(n=>n.setAttribute('aria-pressed',String(n===b)));document.getElementById('chartTitle').textContent='Aguardando medições de '+b.dataset.metric;}));
  const root=document.getElementById('dashboard'),toggle=document.getElementById('widgetToggle');
  const native=window.loneDesktop;let windowState=null;
  function renderWindow(value){
    if(!value)return;windowState=value;
    const compact=value.mode==='widget'||innerWidth<=640;
    root.dataset.mode=compact?'widget':'dashboard';
    toggle.setAttribute('aria-pressed',String(value.mode==='widget'));
    document.getElementById('maximizeBtn').disabled=value.mode==='widget';
    document.getElementById('trayMinimizeBtn').disabled=!value.trayAvailable;
    document.getElementById('runtimeLabel').textContent=value.reviewProfile?'Electron · desenvolvimento isolado':value.development?'Electron · desenvolvimento':'Electron · integração visual';
    document.getElementById('communicationState').title='Cliente autenticado ainda não implementado. Nenhuma consulta ao agente.';
  }
  window.addEventListener('resize',()=>renderWindow(windowState));
  toggle.addEventListener('click',async()=>{
    if(!native||!windowState)return;
    toggle.disabled=true;
    try{renderWindow(await native.setWindowMode(windowState.mode==='widget'?'dashboard':'widget'));}
    finally{toggle.disabled=false;}
  });
  document.getElementById('trayMinimizeBtn').addEventListener('click',async()=>{
    if(!native||!windowState?.trayAvailable)return;
    const result=await native.minimizeToTray();renderWindow(result.state);
  });
  document.getElementById('minimizeBtn').addEventListener('click',()=>native?.minimize());
  document.getElementById('closeBtn').addEventListener('click',()=>native?.close());
  document.getElementById('maximizeBtn').addEventListener('click',async()=>renderWindow(await native?.toggleMaximize()));
  native?.onWindowState(renderWindow);
  native?.getWindowState().then(renderWindow);
  window.loneVersion?.render('Windows');
})();
