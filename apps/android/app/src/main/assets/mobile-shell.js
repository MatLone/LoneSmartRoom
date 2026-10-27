'use strict';
// Android presentation only. Native actions remain in the existing narrow bridge clients.
(() => {
  // Shared machined eight-tooth outline; beveled corners stay clear at 17–22 px.
  const settingsGear = '<path stroke-linejoin="bevel" d="M9.836 4.923 L10.514 2.617 L13.486 2.617 L14.164 4.923 L15.474 5.466 L17.584 4.314 L19.686 6.416 L18.534 8.526 L19.077 9.836 L21.383 10.514 L21.383 13.486 L19.077 14.164 L18.534 15.474 L19.686 17.584 L17.584 19.686 L15.474 18.534 L14.164 19.077 L13.486 21.383 L10.514 21.383 L9.836 19.077 L8.526 18.534 L6.416 19.686 L4.314 17.584 L5.466 15.474 L4.923 14.164 L2.617 13.486 L2.617 10.514 L4.923 9.836 L5.466 8.526 L4.314 6.416 L6.416 4.314 L8.526 5.466 Z"/><circle cx="12" cy="12" r="3.1"/>';
  const icons = {
    settings:settingsGear,
    sliders:'<path d="M4 7h6m4 0h6M4 17h10m4 0h2"/><circle cx="12" cy="7" r="2"/><circle cx="16" cy="17" r="2"/>',
    monitor:'<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8m-4-4v4"/>',
    activity:'<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    gamepad:'<path d="M8 6h8c2 0 3 1 4 4l1 6c.4 3-2 4-4 1l-1-1H8l-1 1c-2 3-4.4 2-4-1l1-6c1-3 2-4 4-4Z"/><path d="M6 11h4m-2-2v4m7-2h.01m3 2h.01"/>',
    shield:'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
    power:'<path d="M12 2v10m-6-7a9 9 0 1 0 12 0"/>',
    lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
    lamp:'<path d="M8 17h8m-7 4h6m-3-18a6 6 0 0 1 4 10c-1 1-1 2-1 3H9c0-1 0-2-1-3a6 6 0 0 1 4-10Z"/>',
    led:'<rect x="3" y="7" width="18" height="10" rx="2"/><path d="M7 11v2m5-2v2m5-2v2M7 3v1m10-1v1m-10 16v1m10-1v1"/>',
    fan:'<circle cx="12" cy="12" r="2"/><path d="M10 10C4 4 13 0 14 6v4m0 2c8-3 9 7 3 6l-4-3m-3-1c-2 8-10 2-5-2l4-1"/>',
    tv:'<rect x="3" y="5" width="18" height="13" rx="2"/><path d="M8 22h8m-4-4v4"/>',
    cpu:'<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4m6-4v4m-6 12v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4"/>',
    temperature:'<path d="M9 14V5a3 3 0 0 1 6 0v9a5 5 0 1 1-6 0Z"/><path d="M12 8v9"/>',
    gpu:'<rect x="2" y="6" width="19" height="12" rx="2"/><circle cx="10" cy="12" r="3"/><path d="M16 10h2m-2 4h2M6 18v3m3-3v3m3-3v3"/>',
    ram:'<rect x="2" y="7" width="20" height="10" rx="2"/><path d="M6 10v4m4-4v4m4-4v4m4-4v4M6 17v3m4-3v3m4-3v3m4-3v3"/>',
    chart:'<path d="M3 3v18h18M7 14l4-5 4 3 5-7"/>',
    arrow:'<path d="m9 5 7 7-7 7"/>',
    close:'<path d="m6 6 12 12M18 6 6 18"/>',
    refresh:'<path d="M20 7V3l-3 3a8 8 0 1 0 3 9M20 3h-5"/>',
    globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a18 18 0 0 1 0 18 18 18 0 0 1 0-18Z"/>',
    gear:settingsGear,
  };
  const svg = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.gear}</svg>`;
  const badge = (label, locked = false) => `<span class="status-badge${locked ? ' locked' : ''}">${locked ? svg('lock') : '<i></i>'}${label}</span>`;
  const heading = (kicker, name, description, n) => `<div class="page-heading"><div><span class="eyebrow">${kicker}</span><h1>${name}</h1><p>${description}</p></div><span class="page-number" aria-hidden="true">${n}</span></div>`;
  const nex = (mobile = false) => `<section class="nex-card ${mobile ? 'mobile-nex' : ''}" aria-label="NEX planejado"><div class="nex-type">NEX</div><div class="nex-copy"><h2>Um novo nível de conexão.</h2><p>Neural Environment eXecutive.<br>Espaço reservado ao futuro assistente.</p></div>${badge('Planejado')}</section>`;
  const pcCard = () => `<section class="pc-card" aria-label="Computador e conexão"><div class="pc-head"><div class="icon-tile">${svg('monitor')}</div><div><span class="small-label">PC PRINCIPAL</span><h2>Meu computador</h2></div><span id="agentState" class="status-badge" data-state="unknown" role="status">Desconhecido</span></div><div class="status-lines"><div class="status-line"><span>Estado de energia</span><b>Não verificado</b></div><div class="status-line"><span>Origem do status</span><b>${svg('lock')}Agente HTTPS</b></div></div><p id="agentLast" class="fine-print">Última comunicação: nenhuma registrada</p><p id="agentDetail" class="feedback" aria-live="polite">Aguardando consulta autenticada.</p><div class="action-row"><button id="pcWakeBtn" class="button primary" disabled>${svg('power')}Enviar Wake-on-LAN</button><button class="button" data-open="connection">${svg('settings')}Configurar</button></div><p id="wolFeedback" class="feedback" role="status">Carregando configuração Wake-on-LAN.</p><div class="secondary-actions"><button id="agentRefresh" class="inline-button">${svg('refresh')}Atualizar status</button><button class="inline-button" data-go="gamer">Gamer Launcher ${svg('arrow')}</button></div><p class="fine-print">Ausência de resposta não confirma que o PC está desligado. Enviar WoL não confirma o despertar.</p></section>`;
  const device = (id, icon, name, type) => `<button class="device-card" data-open="${id}" aria-label="Ver configuração de ${name}"><span class="device-top">${svg(icon)}<span class="switch-shape" aria-hidden="true"></span></span><strong>${name}</strong><small>${type}</small><span class="device-state">${svg('lock')}Integração indisponível</span></button>`;
  // Presentation follows the approved Windows family. Metrics use the fixed authenticated read contract.
  const unavailableRow = (label, id) => `<div class="metric-row"><span>${label}</span><strong${id ? ` data-telemetry="${id}"` : ""}>Indisponível</strong></div>`;
  const unavailableSensor = (icon, name, id) => `<section class="sensor" aria-label="${name}: indisponível"><div class="sensor-title">${svg(icon)}${name}</div><div class="sensor-value" data-telemetry="${id}">Indisponível</div><small>Consulta autenticada · somente leitura</small><div class="unavailable-track" aria-hidden="true"><span data-telemetry-bar="${id === "ram.used" ? "ram.utilization" : id}"></span></div></section>`;
  const controls = `${heading('LONE SMART ROOM / CONTROLES','Seu espaço,<br>sob controle<span class="accent">.</span>','Seu quarto e seu computador, em um só lugar.','01')}${pcCard()}<div class="security-line">${svg('shield')}Você mantém o controle. WoL independente e permissões individuais por aplicativo.</div><section class="surface room-surface"><div class="section-line"><h2>Dispositivos do quarto</h2><span>INTEGRAÇÕES FUTURAS</span></div><div class="device-grid">${device('lamp','lamp','Lâmpada','Iluminação ambiente')}${device('led','led','Fita LED','Iluminação de destaque')}${device('fan','fan','Ventilador','Climatização')}${device('tv','tv','Smart TV','Entretenimento')}</div></section>${nex(true)}<p class="brand-pending-note">LONE SMART ROOM · Seu ambiente, sob controle.</p>`;
  const monitor = `${heading('LONE SMART ROOM / MONITORAMENTO','Seu PC, em foco<span class="accent">.</span>','A mesma visão do hardware. Somente medições reais.','02')}<div class="monitor-top">${svg('shield')}<span id="telemetryState" role="status">Aguardando consulta autenticada</span></div><p class="fine-print" id="telemetryLast">Última atualização: nenhuma medição</p><div class="sensor-grid">${unavailableSensor('cpu','CPU · Intel i5-12400','cpu.utilization')}${unavailableSensor('gpu','GPU · Radeon RX 6750 XT','gpu.adlx.utilization')}${unavailableSensor('ram','RAM utilizada','ram.used')}${unavailableSensor('temperature','Temperatura GPU','gpu.adlx.temperature')}</div><section class="surface metric-details"><h2>AMD Radeon RX 6750 XT</h2><p>ADLX · disponibilidade conforme suporte do dispositivo.</p>${[['Hotspot','gpu.adlx.hotspot_temperature'],['VRAM utilizada','gpu.adlx.vram_used_mb'],['VRAM total','gpu.adlx.vram_total_mb'],['Clock do núcleo','gpu.adlx.core_clock'],['Potência','gpu.adlx.power'],['Ventoinhas','gpu.adlx.fan_rpm'],['RAM total','ram.total'],['RAM disponível','ram.available'],['RAM utilizada (%)','ram.utilization']].map(([label,id])=>unavailableRow(label,id)).join('')}</section><section class="surface metric-details" aria-label="Armazenamento remoto indisponível"><h2>Armazenamento</h2><p>Ocupação, taxas de I/O e atividade são medições distintas.</p>${['c','d'].map(v=>`<h3>Volume ${v.toUpperCase()}:</h3>${[['Capacidade','total'],['Disponível','available'],['Ocupação do disco','occupation'],['Leitura','read_rate'],['Gravação','write_rate'],['Atividade PDH','activity']].map(([label,k])=>unavailableRow(label,'storage.'+v+'.'+k)).join('')}`).join('')}</section><div class="section-line"><h2>Uso de recursos</h2><span>Indisponível</span></div><section class="empty-chart">${svg('chart')}<h3>Histórico ainda não integrado</h3><p>Sem amostras remotas. Nenhum valor demonstrativo é apresentado como medição.</p></section><div class="disabled-row"><div><strong>Perfis e ventoinhas</strong><small>Controle indisponível</small></div>${svg('lock')}</div><div class="disabled-row"><div><strong>Otimizações do sistema</strong><small>Nenhuma ação disponível</small></div>${svg('lock')}</div>${nex(true)}`;
  const gamer = `${heading('LONE SMART ROOM / GAMER LAUNCHER','Hora do jogo<span class="accent">.</span>','Seus atalhos. Suas permissões.','03')}<div class="game-layout"><section class="game-hero"><div class="game-kicker"><span>STEAM · APP 730</span><span class="status-badge locked" data-permission="cs2">Bloqueado</span></div><div class="game-title">COUNTER<br>STRIKE<span>2</span></div><p>Abertura pelo cliente Steam validado.<br>Sem alterar opções do jogo ou o VAC.</p><button class="button primary full" id="launchCs2" disabled>${svg('lock')}Abrir CS2</button></section><div class="game-aside"><section class="steam-row"><div class="icon-tile">${svg('globe')}</div><div><h2>Steam</h2><p>Cliente Windows</p></div><span class="status-badge locked" data-permission="steam">Bloqueado</span></section><button class="button full" id="launchSteam" disabled>${svg('lock')}Abrir Steam</button><div class="security-line">${svg('shield')}Você mantém o controle. A autorização do agente e a confirmação nativa continuam obrigatórias.</div><button id="launchPermissions" class="inline-button">${svg('refresh')}Atualizar permissões</button><button class="inline-button" data-open="permissions">Entender as permissões ${svg('arrow')}</button></div></div><section class="command-panel"><h2>Última solicitação: <span id="launchState">Desconhecido</span></h2><p id="launchDetail" aria-live="polite">Nenhuma solicitação confirmada nesta tela.</p><div class="command-steps"><span data-command="requested">Solicitado</span><span data-command="accepted">Aceito</span><span data-command="executed">Executado</span><span data-command="failed">Falha</span></div><p class="fine-print">“Executado” confirma o despacho ao Windows. Não confirma que a janela ou o jogo já carregou.</p><button class="inline-button" id="launchQuery" disabled>${svg('refresh')}Consultar resultado</button></section><div class="section-line"><h2>Outros recursos</h2><span>Indisponíveis</span></div><div class="disabled-row"><div><strong>FPS, overlays e perfis</strong><small>Sem telemetria ou automação nesta etapa</small></div>${svg('lock')}</div>`;
  const main = document.getElementById('workspace');
  main.innerHTML = `<section id="panel-controls" role="tabpanel" aria-labelledby="tab-controls">${controls}</section><section id="panel-monitor" role="tabpanel" aria-labelledby="tab-monitor" hidden>${monitor}</section><section id="panel-gamer" role="tabpanel" aria-labelledby="tab-gamer" hidden>${gamer}</section>`;
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  function selectTab(tab) {
    for (const button of tabs) {
      const selected = button === tab;
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
      document.getElementById(button.getAttribute('aria-controls')).hidden = !selected;
    }
    main.scrollTop = 0;
  }
  tabs.forEach((tab,index) => {
    tab.tabIndex = index === 0 ? 0 : -1;
    tab.addEventListener('click', () => selectTab(tab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); selectTab(tabs[next]); tabs[next].focus(); }
    });
  });
  const connection = document.getElementById('connectionDialog');
  const dialog = document.getElementById('settingsDialog');
  const brandDialog = document.getElementById('brandDialog');
  const labels = {lamp:['Lâmpada','Iluminação ambiente'], led:['Fita LED','Iluminação de destaque'], fan:['Ventilador','Climatização'], tv:['Smart TV','Entretenimento']};
  let returnFocus;
  function openSettings(kind, trigger) {
    returnFocus = trigger;
    if (kind === 'brand') { brandDialog.showModal(); brandDialog.scrollTop = 0; return; }
    if (kind === 'connection') { window.loneWolUI?.syncFields(); connection.showModal(); return; }
    const values = labels[kind];
    const title = kind === 'permissions' ? 'Você autoriza. O agente valida.' : values?.[0];
    if (!title) return;
    document.getElementById('settingsTitle').textContent = title;
    document.getElementById('settingsSubtitle').textContent = kind === 'permissions' ? 'PERMISSÕES' : values[1];
    document.getElementById('deviceContent').hidden = kind === 'permissions';
    document.getElementById('permissionContent').hidden = kind !== 'permissions';
    dialog.showModal();
  }
  document.addEventListener('click', event => {
    const open = event.target.closest('[data-open]');
    if (open) openSettings(open.dataset.open, open);
    const go = event.target.closest('[data-go]');
    if (go) selectTab(document.getElementById('tab-' + go.dataset.go));
    if (event.target.closest('[data-close]')) event.target.closest('dialog')?.close();
  });
  [connection, dialog, brandDialog].forEach(panel => panel.addEventListener('close', () => {
    if (panel === connection) window.loneWolUI?.syncFields();
    returnFocus?.focus();
  }));
  document.querySelectorAll('[data-icon]').forEach(node => { node.innerHTML=svg(node.dataset.icon); });
})();
