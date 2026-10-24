'use strict';
// Visual review only. No network, native bridge, IPC, storage or device commands.
(() => {
  const icons = {
    settings:'<path d="m9 3-1 3-3 1-2 3 2 2v3l2 3 3-1 3 1 3-2 1-3 3-2-1-3-3-1-2-3Z"/><circle cx="12" cy="12" r="3"/>',
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
    gpu:'<rect x="2" y="6" width="19" height="12" rx="2"/><circle cx="10" cy="12" r="3"/><path d="M16 10h2m-2 4h2M6 18v3m3-3v3m3-3v3"/>',
    ram:'<rect x="2" y="7" width="20" height="10" rx="2"/><path d="M6 10v4m4-4v4m4-4v4m4-4v4M6 17v3m4-3v3m4-3v3m4-3v3"/>',
    chart:'<path d="M3 3v18h18M7 14l4-5 4 3 5-7"/>',
    arrow:'<path d="m9 5 7 7-7 7"/>',
    close:'<path d="m6 6 12 12M18 6 6 18"/>',
    refresh:'<path d="M20 7V3l-3 3a8 8 0 1 0 3 9M20 3h-5"/>',
    globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a18 18 0 0 1 0 18 18 18 0 0 1 0-18Z"/>',
    gear:'<path d="M6 4h12v16H6zM9 8h6m-6 4h6m-6 4h3"/>',
  };
  const svg = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.gear}</svg>`;
  const badge = (label, locked = false) => `<span class="status-badge${locked ? ' locked' : ''}">${locked ? svg('lock') : '<i></i>'}${label}</span>`;
  const heading = (kicker, name, description, n) => `<div class="page-heading"><div><span class="eyebrow">${kicker}</span><h1>${name}</h1><p>${description}</p></div><span class="page-number" aria-hidden="true">${n}</span></div>`;
  const nex = (mobile = false) => `<section class="nex-card ${mobile ? 'mobile-nex' : ''}" aria-label="NEX planejado"><div class="nex-type">NEX</div><div class="nex-copy"><h2>Um novo nível de conexão.</h2><p>Neural Environment eXecutive.<br>Espaço reservado ao futuro assistente.</p></div>${badge('Planejado')}</section>`;
  const pcCard = () => `<section class="pc-card" aria-label="Computador e conexão"><div class="pc-head"><div class="icon-tile">${svg('monitor')}</div><div><span class="small-label">PC PRINCIPAL</span><h2>Meu computador</h2></div>${badge('Desconhecido')}</div><div class="status-lines"><div class="status-line"><span>Conexão HTTPS</span><b>${svg('lock')}Não consultada</b></div><div class="status-line"><span>Última comunicação</span><b>—</b></div></div><div class="action-row"><button class="button primary" data-action="wake" disabled>${svg('power')}Enviar Wake-on-LAN</button><button class="button" data-open="connection">${svg('settings')}Configurar</button></div><p class="fine-print">Sem leitura do agente nesta prévia. Ausência de resposta não confirma que o computador está desligado.</p></section>`;
  const device = (id, icon, name, type) => `<button class="device-card" data-open="${id}" aria-label="Ver configuração de ${name}"><span class="device-top">${svg(icon)}<span class="switch-shape" aria-hidden="true"></span></span><strong>${name}</strong><small>${type}</small><span class="device-state">${svg('lock')}Integração indisponível</span></button>`;
  const controls = `${heading('SEU ESPAÇO, CONECTADO','Meu quarto','O essencial, sempre por perto.','01')}${pcCard()}<div class="security-line">${svg('shield')}WoL independente do agente. Abrir aplicativos continua exigindo autorização específica.</div><div class="section-line"><h2>Dispositivos do quarto</h2><span>Configurar ${'↗'}</span></div><div class="device-grid">${device('lamp','lamp','Lâmpada','Iluminação ambiente')}${device('led','led','Fita LED','Luz de destaque')}${device('fan','fan','Ventilador','Climatização')}${device('tv','tv','Smart TV','Entretenimento')}</div>${nex(true)}<p class="brand-pending-note">Marca final pendente: Variante 3 — Contorno Luminoso. Nenhuma logo foi recriada nesta proposta.</p>`;
  const monitor = `${heading('MONITORAMENTO PC','Seu PC, em foco','Métricas apenas quando forem reais.','02')}<div class="monitor-top">${svg('shield')}Consulta de status e coleta de sensores são capacidades diferentes.</div><div class="sensor-grid">${[['cpu','CPU'],['gpu','GPU'],['ram','RAM']].map(([icon,name])=>`<section class="sensor"><div class="sensor-title">${svg(icon)}${name}</div><div class="sensor-value">—</div><small>Coleta não implementada</small></section>`).join('')}</div><div class="section-line"><h2>Uso de recursos</h2><span>Indisponível</span></div><section class="empty-chart">${svg('chart')}<h3>Aguardando integração de hardware</h3><p>Os gráficos aparecerão quando o agente fornecer medições reais. Não há valores demonstrativos.</p></section><div class="disabled-row"><div><strong>Perfis e ventoinhas</strong><small>Controle ainda não implementado</small></div>${svg('lock')}</div><div class="disabled-row"><div><strong>Otimizações do sistema</strong><small>Nenhuma ação disponível</small></div>${svg('lock')}</div>${nex(true)}`;
  const gamer = `${heading('GAMER LAUNCHER','Hora do jogo.','Seus atalhos. Suas permissões.','03')}<div class="game-layout"><section class="game-hero"><div class="game-kicker"><span>STEAM · APP 730</span>${badge('Bloqueado',true)}</div><div class="game-title">COUNTER<br>STRIKE<span>2</span></div><p>Abertura pelo cliente Steam validado.<br>Sem alterar opções do jogo ou o VAC.</p><button class="button primary full" data-action="cs2" disabled>${svg('lock')}Abrir CS2</button></section><div class="game-aside"><section class="steam-row"><div class="icon-tile">${svg('globe')}</div><div><h2>Steam</h2><p>Cliente Windows</p></div>${badge('Bloqueado',true)}</section><button class="button full" data-action="steam" disabled>${svg('lock')}Abrir Steam</button><div class="security-line">${svg('shield')}Permissão por aplicativo e por dispositivo. A confirmação nativa permanece obrigatória.</div><button class="inline-button" data-open="permissions">Entender as permissões ${svg('arrow')}</button></div></div><section class="command-panel"><h2>Última solicitação</h2><p>Nenhum pedido nesta prévia.</p><div class="command-steps"><span>Solicitado</span><span>Aceito</span><span>Executado</span><span>Falha</span></div><p class="fine-print">“Executado” confirma o despacho ao Windows. Não confirma que a janela ou o jogo já carregou.</p><button class="inline-button" disabled data-action="query">${svg('refresh')}Consultar resultado</button></section><div class="section-line"><h2>Outros recursos</h2><span>Indisponíveis</span></div><div class="disabled-row"><div><strong>FPS, overlays e perfis</strong><small>Sem telemetria ou automação nesta etapa</small></div>${svg('lock')}</div>`;
  const main = document.getElementById('workspace');
  main.innerHTML = `<section id="panel-controls" role="tabpanel" aria-labelledby="tab-controls">${controls}</section><section id="panel-monitor" role="tabpanel" aria-labelledby="tab-monitor" hidden>${monitor}</section><section id="panel-gamer" role="tabpanel" aria-labelledby="tab-gamer" hidden>${gamer}</section>`;
  const context = document.getElementById('desktopContext');
  context.innerHTML = `<h2>O próximo capítulo</h2>${nex()}<section class="context-section"><span class="eyebrow">CAPACIDADES</span><div class="context-item"><span>Agente HTTPS</span><b>Sem consulta</b></div><div class="context-item"><span>Steam / CS2</span><b>Com autorização</b></div><div class="context-item"><span>Sensores</span><b>Indisponíveis</b></div><div class="context-item"><span>Casa conectada</span><b>Indisponível</b></div><button class="inline-button" data-open="connection">Configurar conexão ${svg('arrow')}</button></section><section class="context-section"><p class="fine-print">Proposta visual do dashboard. O Electron atual ainda não possui cliente HTTPS nativo ou emissor WoL.</p><p class="brand-pending-note">Marca aprovada pendente.<br>Variante 3 · Contorno Luminoso.</p></section>`;
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  function selectTab(tab) {
    for (const button of tabs) {
      const selected = button === tab;
      button.setAttribute('aria-selected', String(selected));
      document.getElementById(button.getAttribute('aria-controls')).hidden = !selected;
    }
    main.scrollTop = 0;
  }
  tabs.forEach((tab,index) => {
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
  const dialog = document.getElementById('settingsDialog');
  const explanations = {
    lamp:['Lâmpada','Iluminação ambiente','Integração com a lâmpada ainda não implementada. Os controles serão habilitados quando houver suporte real ao dispositivo.'],
    led:['Fita LED','Iluminação de destaque','A integração de iluminação será tratada em uma etapa própria. Nenhuma cor ou intensidade é enviada nesta prévia.'],
    fan:['Ventilador','Climatização','Liga/desliga e velocidade aguardam uma integração compatível. Nenhum ventilador ou serviço do Windows é controlado por este painel.'],
    tv:['Smart TV','Entretenimento','A descoberta e o controle da TV ainda não foram implementados. O estado do aparelho permanece desconhecido.']
  };
  function openSettings(kind) {
    let title,subtitle,content;
    if (kind === 'connection') {
      title='Meu computador'; subtitle='CONEXÃO E WAKE-ON-LAN';
      content=`<p>Prévia de organização. Os dados salvos no aplicativo não são lidos, alterados ou substituídos aqui.</p><label class="field">Servidor pareado<input readonly placeholder="Preservar servidor existente"></label><label class="field">MAC Ethernet<input readonly placeholder="Preservar configuração existente"></label><label class="field">Broadcast<input readonly placeholder="Preservar configuração existente"></label><label class="field">Porta WoL<select disabled><option>Configuração UDP 7 ou 9</option></select></label><div class="dialog-note">Na migração, o WoL continuará usando o armazenamento atual e a ponte Kotlin. Enviar o pacote não comprova que o PC despertou.</div><button class="button full" data-action="pair" disabled>${svg('shield')}Parear com Windows</button><button class="button primary full" data-action="save" disabled>Salvar · indisponível na prévia</button>`;
    } else if (kind === 'permissions') {
      title='Você autoriza. O agente valida.'; subtitle='PERMISSÕES';
      content=`<p>Pareamento permite consultar status. Abrir Steam e CS2 exige uma autorização própria para cada aplicativo e dispositivo, concedida no Windows.</p><div class="dialog-note">O novo visual não concede permissões. HTTPS, identidade do servidor, HMAC, anti-replay e confirmação nativa continuam obrigatórios.</div><div class="disabled-row"><div><strong>Steam</strong><small>Sem autorização nesta prévia</small></div>${svg('lock')}</div><div class="disabled-row"><div><strong>Counter-Strike 2</strong><small>Sem autorização nesta prévia</small></div>${svg('lock')}</div>`;
    } else {
      const values=explanations[kind]; if (!values) return;
      [title,subtitle]=values;
      content=`<p>${values[2]}</p><div class="disabled-row"><div><strong>Alimentação</strong><small>Estado não lido · controle indisponível</small></div><input class="switch-input" type="checkbox" role="switch" disabled aria-label="Alimentação indisponível"></div>${kind==='lamp'||kind==='led'?'<div class="dialog-field-top"><span>Intensidade</span><span>Sem leitura</span></div><input class="disabled-range" type="range" disabled aria-label="Brilho indisponível">':''}<label class="field">Integração<select disabled><option>Ainda não disponível</option></select></label><div class="dialog-note">Este painel permite revisar o desenho. Nenhuma configuração é persistida e nenhum dispositivo recebe comandos.</div><button class="button full" disabled data-action="save-device">Salvar configuração</button>`;
    }
    document.getElementById('dialogContent').innerHTML=`<div class="dialog-header"><div><span class="eyebrow">${subtitle}</span><h2 id="settingsTitle">${title}</h2></div><button class="icon-button" data-close aria-label="Fechar configurações">${svg('close')}</button></div><div class="dialog-body">${content}</div>`;
    dialog.showModal();
  }
  document.addEventListener('click', event => {
    const open=event.target.closest('[data-open]');
    if (open) openSettings(open.dataset.open);
    if (event.target.closest('[data-close]')) dialog.close();
  });
  document.querySelectorAll('[data-icon]').forEach(node => { node.innerHTML=svg(node.dataset.icon); });
})();
