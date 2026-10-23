'use strict';
/* Lone Smart Room v1.4: interface demonstrativa.
   No app Android instalado, SOMENTE a ação Wake-on-LAN envia UDP real por ponte nativa.
   Sem integração de sensores, microfone ou comandos Windows remotos nesta etapa. */
const icons = {
  house:'<path d="m3.8 11 8.2-7 8.2 7v8.6a1.2 1.2 0 0 1-1.2 1.2H5a1.2 1.2 0 0 1-1.2-1.2V11Z"/><path d="M9.6 20.8v-7.2h4.8v7.2"/>',
  lamp:'<path d="M9 18h6m-5 3h4M8.5 14c-.9-1.3-2.5-2.7-2.5-5a6 6 0 0 1 12 0c0 2.3-1.6 3.7-2.5 5l-.5 2H9l-.5-2Z"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  monitor:'<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8m-4-4v4"/>',
  fan:'<circle cx="12" cy="12" r="2"/><path d="M12 10c-3.5-1-3.5-7-1-7 3 0 3.2 3 2.5 7m.1 3.2c2.5-2.7 7.5.6 6.2 2.9-1.7 2.8-4.7 1.1-6.7-.8M10.3 13.7c1 3.6-4.5 6.3-5.9 4.2-1.7-2.7 1-4.4 5.2-5.4"/>',
  settings:'<path d="M4 5h16M4 12h16M4 19h16"/><circle cx="9" cy="5" r="2" fill="#262b36"/><circle cx="15" cy="12" r="2" fill="#262b36"/><circle cx="9" cy="19" r="2" fill="#262b36"/>',
  gamepad:'<path d="M6.5 8h11a4 4 0 0 1 3.9 3l1.1 6c.4 2.3-2.1 3.6-3.7 2.1l-2.5-2.3H7.7l-2.5 2.3c-1.6 1.5-4.1.2-3.7-2.1l1.1-6a4 4 0 0 1 3.9-3Z"/><path d="M6.5 12h5m-2.5-2.5v5M16.5 11h.01M19 13h.01"/>',
  moon:'<path d="M20.3 15.5A8.7 8.7 0 0 1 8.5 3.7a9 9 0 1 0 11.8 11.8Z"/>',
  palette:'<path d="M12 3a9 9 0 1 0 0 18h1.7a2.2 2.2 0 0 0 1.5-3.8 1.2 1.2 0 0 1 .7-2.1h1.8A4.3 4.3 0 0 0 22 11c0-4.4-4.7-8-10-8Z"/><circle cx="7" cy="11" r="1"/><circle cx="11" cy="7.5" r="1"/><circle cx="16" cy="8.5" r="1"/><circle cx="7.9" cy="15.4" r="1"/>',
  chevron:'<path d="m9 5 7 7-7 7"/>',
  info:'<circle cx="12" cy="12" r="10"/><path d="M12 11v5m0-8h.01"/>',
  bot:'<rect x="4" y="7" width="16" height="13" rx="4"/><path d="M12 3v4"/><circle cx="9" cy="13" r="1"/><circle cx="15" cy="13" r="1"/><path d="M9 17h6"/>',
  mic:'<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3m-4 0h8"/>',
  stop:'<rect x="5" y="5" width="14" height="14" rx="3"/>',
  x:'<path d="M5 5 19 19M19 5 5 19"/>',
  cpu:'<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3"/>',
  memory:'<rect x="2" y="7" width="20" height="10" rx="2"/><path d="M6 10h2m2 0h2m2 0h2m2 0h1M5 17v3m4-3v3m6-3v3m4-3v3"/>',
  drive:'<rect x="3" y="6" width="18" height="12" rx="3"/><path d="M3 14h18M7 16h.01M11 16h.01"/>',
  shield:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
  rocket:'<path d="M4 20c1-4 3-6 7-7l5-8 4-1-1 4-8 5c-1 4-3 6-7 7Z"/><path d="m11 13 3 3M3 12l5-1m4 10 1-5M5 17l-2 4"/>',
  chart:'<path d="M3 20V4M3 20h18M7 14l4-4 4 3 5-7"/>',
  smartphone:'<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/>',
  power:'<path d="M12 3v9M6.5 5.5a8.5 8.5 0 1 0 11 0"/>',
  refresh:'<path d="M3 12a9 9 0 0 1 15.4-6.4L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.4 6.4L3 16M3 21v-5h5"/>',
  sliders:'<path d="M4 5h16M4 12h16M4 19h16"/><circle cx="9" cy="5" r="2" fill="#262b36"/><circle cx="15" cy="12" r="2" fill="#262b36"/><circle cx="9" cy="19" r="2" fill="#262b36"/>',
  gear:'<circle cx="12" cy="12" r="3"/><path d="M19 13.5a1.6 1.6 0 0 0 .3 1.8l.1.1-1.8 3.1-.2-.1a1.6 1.6 0 0 0-1.7.6l-.1.2h-3.6l-.1-.2a1.6 1.6 0 0 0-1.7-.6l-.2.1-1.8-3.1.1-.1a1.6 1.6 0 0 0 .3-1.8V12a1.6 1.6 0 0 0-.3-1.8l-.1-.1L11 7l.2.1a1.6 1.6 0 0 0 1.7-.6l.1-.2h3.6l.1.2a1.6 1.6 0 0 0 1.7.6l.2-.1 1.8 3.1-.1.1a1.6 1.6 0 0 0-.3 1.8Z"/>'
};
const svg=(name)=>`<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name]||icons.info}</svg>`;
const catalog=[
  {id:'lamp',name:'Lâmpada',subtitle:'Iluminação principal',icon:'lamp',rgb:true},
  {id:'led',name:'Fita LED',subtitle:'Iluminação RGB',icon:'sun',rgb:true},
  {id:'pc',name:'RGB do PC',subtitle:'Ventoinhas e gabinete',icon:'monitor',rgb:true},
  {id:'fan',name:'Ventilador',subtitle:'Velocidades 1, 2 e 3',icon:'fan',rgb:false}
];
const palette=[{name:'Vermelho',hex:'#f04759'},{name:'Amarelo',hex:'#fac93e'},{name:'Azul',hex:'#397bfa'},{name:'Verde',hex:'#2ac573'},{name:'Roxo',hex:'#ae6aea'},{name:'Branco',hex:'#f5e9d4'}];
const defaults={devices:{lamp:{on:true,color:'#f5e9d4',brightness:80},led:{on:true,color:'#f04759',brightness:65},pc:{on:true,color:'#f04759',brightness:90},fan:{on:false,speed:2}},activeTab:'controls',fanControl:{profile:'auto',cpu:65,case:50}};
const $=(selector)=>document.querySelector(selector);
const els={frame:$('#appFrame'),grid:$('#deviceGrid'),modal:$('#modalLayer'),modalPower:$('#modalPower'),range:$('#brightnessRange'),brightnessValue:$('#brightnessValue'),swatches:$('#swatches'),voiceStatus:$('#voiceStatus'),voicePanel:$('#voicePanel'),speakBtn:$('#speakBtn'),speakText:$('#speakText'),toast:$('#toast')};
let initial;try{initial=JSON.parse(localStorage.getItem('lone-smart-room-demo-v1'))}catch{};
const state={devices:structuredClone(defaults.devices),activeTab:'controls',modal:null,voice:'idle',fanControl:structuredClone(defaults.fanControl),toolModal:null,gameId:'cs2',gameProfiles:{cs2:'competitive',valorant:'competitive',fortnite:'balanced'},gameOptions:{background:true,cooling:true,lighting:true,gameMode:true,overlay:false},gameSession:false,gameTick:0,gameHistory:[]};
if(initial && initial.devices){for(const item of catalog){const old=initial.devices[item.id];if(old&&typeof old.on==='boolean'){Object.assign(state.devices[item.id],old)}}}
if(initial&&['controls','monitor','gamer'].includes(initial.activeTab))state.activeTab=initial.activeTab;
if(initial&&initial.fanControl){const f=initial.fanControl;if(['auto','quiet','balanced','performance','manual'].includes(f.profile))state.fanControl.profile=f.profile;for(const id of ['cpu','case'])if(Number.isFinite(f[id]))state.fanControl[id]=Math.max(id==='cpu'?40:35,Math.min(100,Math.round(f[id]))) }
if(initial&&['cs2','valorant','fortnite'].includes(initial.gameId))state.gameId=initial.gameId;
if(initial&&initial.gameProfiles)for(const id of ['cs2','valorant','fortnite'])if(['competitive','balanced','quality'].includes(initial.gameProfiles[id]))state.gameProfiles[id]=initial.gameProfiles[id];
if(initial&&initial.gameOptions)for(const id of ['background','cooling','lighting','gameMode','overlay'])if(typeof initial.gameOptions[id]==='boolean')state.gameOptions[id]=initial.gameOptions[id];
const save=()=>{try{localStorage.setItem('lone-smart-room-demo-v1',JSON.stringify({devices:state.devices,activeTab:state.activeTab,fanControl:state.fanControl,gameId:state.gameId,gameProfiles:state.gameProfiles,gameOptions:state.gameOptions}))}catch{}};
let toastTimer;
function toast(message){clearTimeout(toastTimer);els.toast.textContent=message;els.toast.classList.add('shown');toastTimer=setTimeout(()=>els.toast.classList.remove('shown'),2300)}
function powerButton(id){const v=state.devices[id];return `<button class="toggle ${v.on?'on':''}" role="switch" aria-label="${v.on?'Desligar':'Ligar'} ${catalog.find(d=>d.id===id).name}" aria-checked="${v.on}" data-switch="${id}"><i></i></button>`}
function renderCards(){els.grid.innerHTML=catalog.map(d=>{const v=state.devices[d.id];return `<article class="device-card ${v.on?'':'off'}" tabindex="0" data-device="${d.id}" title="Pressione e segure para abrir ajustes"><div class="device-top"><span class="device-icon">${svg(d.icon)}</span><button type="button" class="settings-btn" aria-label="Ajustar ${d.name}" data-settings="${d.id}">${svg('settings')}</button></div><div class="device-details"><strong>${d.name}</strong><span>${v.on?(d.id==='fan'?`Velocidade ${v.speed}`:'Ligado'):'Desligado'}</span></div><div class="device-bottom"><span class="mini-label">${d.rgb&&v.on?`${v.brightness}% de brilho`:d.id==='fan'?'3 velocidades':'Toque na chave'}</span>${powerButton(d.id)}</div></article>`}).join('')}
function togglePower(id){const s=state.devices[id];s.on=!s.on;save();renderCards();if(state.modal===id)renderModal();toast(`${catalog.find(d=>d.id===id).name} ${s.on?'ligado':'desligado'} (demo)`)}
const isInsideControl=(el)=>!!el.closest('button,input');
let pressTimer,pressStart;
function clearPress(){clearTimeout(pressTimer);pressTimer=null;pressStart=null}
els.grid.addEventListener('pointerdown',e=>{const card=e.target.closest('[data-device]');if(!card||isInsideControl(e.target))return;clearPress();pressStart={x:e.clientX,y:e.clientY};const id=card.dataset.device;pressTimer=setTimeout(()=>{pressTimer=null;openModal(id)},520)});
els.grid.addEventListener('pointermove',e=>{if(pressStart&&Math.hypot(e.clientX-pressStart.x,e.clientY-pressStart.y)>11)clearPress()});
['pointerup','pointercancel','pointerleave'].forEach(type=>els.grid.addEventListener(type,clearPress));
els.grid.addEventListener('contextmenu',e=>{const card=e.target.closest('[data-device]');if(card){e.preventDefault();clearPress();openModal(card.dataset.device)}});
els.grid.addEventListener('click',e=>{const sw=e.target.closest('[data-switch]');if(sw){togglePower(sw.dataset.switch);return}const settings=e.target.closest('[data-settings]');if(settings)openModal(settings.dataset.settings)});
els.grid.addEventListener('keydown',e=>{const card=e.target.closest('[data-device]');if(card&&e.target===card&&(e.key==='Enter'||e.key===' ')){e.preventDefault();openModal(card.dataset.device)}});
function renderModal(){const d=catalog.find(x=>x.id===state.modal);if(!d)return;const v=state.devices[d.id];$('#modalTitle').textContent=d.name;$('#modalSub').textContent=d.subtitle;$('#modalIcon').innerHTML=svg(d.icon);els.modalPower.classList.toggle('on',v.on);els.modalPower.setAttribute('aria-checked',String(v.on));$('#modalRgb').hidden=!d.rgb;$('#modalFan').hidden=d.rgb;
  if(d.rgb){els.swatches.innerHTML=palette.map(c=>`<button class="swatch ${v.color===c.hex?'selected':''}" style="background:${c.hex}" aria-label="Cor ${c.name}" aria-pressed="${v.color===c.hex}" title="${c.name}" data-color="${c.hex}"></button>`).join('');els.range.value=v.brightness;els.brightnessValue.textContent=`${v.brightness}%`;paintRange(v)}
  else document.querySelectorAll('[data-speed]').forEach(btn=>{btn.classList.toggle('active',Number(btn.dataset.speed)===v.speed);btn.setAttribute('aria-pressed',String(Number(btn.dataset.speed)===v.speed))})
}
function openModal(id){if(!state.devices[id])return;state.modal=id;renderModal();els.modal.hidden=false;$('#modalClose').focus()}
function closeModal(){state.modal=null;els.modal.hidden=true}
function paintRange(v){els.range.style.background=`linear-gradient(to right,${v.color} 0%,${v.color} ${v.brightness}%,#424855 ${v.brightness}%,#424855 100%)`}
$('#modalClose').addEventListener('click',closeModal);$('#modalShade').addEventListener('click',closeModal);
els.modalPower.addEventListener('click',()=>{if(state.modal)togglePower(state.modal)});
els.swatches.addEventListener('click',e=>{const btn=e.target.closest('[data-color]');if(!btn||!state.modal)return;const s=state.devices[state.modal];s.color=btn.dataset.color;s.on=true;save();renderCards();renderModal()});
els.range.addEventListener('input',e=>{if(!state.modal)return;const s=state.devices[state.modal];s.brightness=Number(e.target.value);s.on=s.brightness>0;els.brightnessValue.textContent=`${s.brightness}%`;paintRange(s);save();renderCards()});
$('#speedGrid').addEventListener('click',e=>{const btn=e.target.closest('[data-speed]');if(!btn)return;state.devices.fan.speed=Number(btn.dataset.speed);state.devices.fan.on=true;save();renderCards();renderModal();toast(`Velocidade ${btn.dataset.speed} selecionada (demo)`)});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(!els.modal.hidden)closeModal();if(!$('#toolModalLayer').hidden)closeToolModal()}});
function applyScene(name){if(name==='gamer'){state.devices.lamp.on=false;for(const k of ['led','pc']){state.devices[k].on=true;state.devices[k].color='#f04759';state.devices[k].brightness=70}}else if(name==='dormir'){for(const d of catalog)state.devices[d.id].on=false}else if(name==='acordar'){for(const k of ['lamp','led','pc']){state.devices[k].on=true;state.devices[k].color='#f5e9d4';state.devices[k].brightness=100}}save();renderCards();toast(`Cena ${name.charAt(0).toUpperCase()+name.slice(1)} ativada (demo)`)}
document.querySelectorAll('[data-scene]').forEach(btn=>btn.addEventListener('click',()=>applyScene(btn.dataset.scene)));
$('#syncRgb').addEventListener('click',()=>{const source=state.devices.led.color;for(const id of ['lamp','pc']){state.devices[id].color=source;state.devices[id].on=true}save();renderCards();toast('Iluminação RGB sincronizada (demo)')});
function renderTabs(){document.querySelectorAll('[data-tab]').forEach(btn=>{const active=btn.dataset.tab===state.activeTab;btn.classList.toggle('active',active);btn.setAttribute('aria-selected',String(active))});for(const pane of document.querySelectorAll('[role="tabpanel"]')){const isActive=pane.id===`panel-${state.activeTab}`;pane.hidden=!isActive;pane.classList.toggle('active',isActive)}$('#viewScroll').scrollTop=0}
document.querySelectorAll('[data-tab]').forEach(btn=>btn.addEventListener('click',()=>{state.activeTab=btn.dataset.tab;save();renderTabs()}));
const fakeMetrics={cpu:{base:47,spread:5},gpu:{base:44,spread:6},ram:{base:39,spread:3},ssd:{base:38,spread:3}};
let step=0;
function metricsNow(){step++;return {cpu:Math.round(47+5*Math.sin(step*.45)),gpu:Math.round(44+6*Math.cos(step*.33)),ram:Math.round(39+3*Math.sin(step*.16)),ssd:Math.round(38+2*Math.sin(step*.11)),cpuUsage:Math.round(21+10*Math.sin(step*.4)),gpuUsage:Math.round(17+8*Math.cos(step*.42)),ramUsage:Math.round(43+2*Math.sin(step*.17)),rpm:Math.round(1080+130*Math.sin(step*.39))}}
function renderMetrics(){const m=metricsNow();const cardData=[{icon:'cpu',label:'Processador',value:`${m.cpu}°C`,desc:'Temperatura CPU',progress:m.cpu},{icon:'monitor',label:'Placa de vídeo',value:`${m.gpu}°C`,desc:'Temperatura GPU',progress:m.gpu},{icon:'memory',label:'Memória RAM',value:`${(16*m.ramUsage/100).toFixed(1).replace('.',',')} GB`,desc:'De 16 GB (simulados)',progress:m.ramUsage},{icon:'drive',label:'SSD',value:`${m.ssd}°C`,desc:'Temperatura do disco',progress:m.ssd}];$('#sensorGrid').innerHTML=cardData.map(x=>`<div class="sensor-card"><div class="sensor-title"><span>${svg(x.icon)}</span><b>${x.label}</b></div><div class="sensor-number">${x.value}</div><div class="sensor-desc">${x.desc}</div><div class="mini-bar"><i style="width:${x.progress}%"></i></div></div>`).join('');const bars=[['Uso do processador',m.cpuUsage,'%'],['Uso da GPU',m.gpuUsage,'%'],['Uso da RAM',m.ramUsage,'%']];$('#usageBars').innerHTML=bars.map(([name,value,suffix])=>`<div class="resource-row"><div class="resource-line"><span>${name}</span><b>${value}${suffix}</b></div><div class="mini-bar"><i style="width:${value}%"></i></div></div>`).join('');$('#monitorExtras').innerHTML=`<div class="extra-stat"><div><span>${svg('fan')}</span> Ventoinhas</div><strong>${m.rpm.toLocaleString('pt-BR')} RPM</strong></div><div class="extra-stat"><div><span>${svg('monitor')}</span> Estado do PC</div><strong>Modo demo</strong></div>`}
// Perfis e velocidades nesta Etapa 1.1 são exclusivamente estados visuais, nunca comandos reais.
const coolingProfiles={auto:{name:'Auto',cpu:65,case:50},quiet:{name:'Silencioso',cpu:50,case:40},balanced:{name:'Equilibrado',cpu:65,case:55},performance:{name:'Desempenho',cpu:90,case:85},manual:{name:'Manual'}};
const fanChannels=[{id:'cpu',name:'Radiador / CPU',desc:'Ventoinhas do water cooler',minimum:40,maxRpm:2200},{id:'case',name:'Gabinete',desc:'Ventoinhas do gabinete',minimum:35,maxRpm:1700}];
function coolingPercent(id){const p=state.fanControl.profile;return p==='manual'?state.fanControl[id]:coolingProfiles[p][id]}
function renderFanControls(){
  document.querySelectorAll('[data-fan-profile]').forEach(btn=>{const selected=btn.dataset.fanProfile===state.fanControl.profile;btn.classList.toggle('selected',selected);btn.setAttribute('aria-pressed',String(selected))});
  const manual=state.fanControl.profile==='manual';
  $('#fanChannels').innerHTML=fanChannels.map(ch=>{const percent=coolingPercent(ch.id);const rpm=Math.round(percent/100*ch.maxRpm/10)*10;return `<div class="fan-channel"><div class="fan-channel-header"><div><b>${ch.name}</b><small>${ch.desc}</small></div><div class="fan-values"><strong>${rpm.toLocaleString('pt-BR')} RPM</strong><span>estimado · ${percent}%</span></div></div><input aria-label="Potência ${ch.name}" data-fan-range="${ch.id}" class="fan-range" type="range" min="${ch.minimum}" max="100" step="5" value="${percent}" ${manual?'':'disabled'} style="--range-progress:${percent}%"><div class="fan-channel-hint">${manual?'Ajuste demonstrativo; nunca abaixo do mínimo calibrado.':'Para alterar manualmente, selecione o perfil Manual.'}</div></div>`}).join('');
}
$('#fanProfiles').addEventListener('click',e=>{const btn=e.target.closest('[data-fan-profile]');if(!btn)return;state.fanControl.profile=btn.dataset.fanProfile;save();renderFanControls();toast(`Perfil ${coolingProfiles[state.fanControl.profile].name} selecionado (demo)`) });
$('#fanChannels').addEventListener('input',e=>{const range=e.target.closest('[data-fan-range]');if(!range||state.fanControl.profile!=='manual')return;state.fanControl[range.dataset.fanRange]=Number(range.value);save();renderFanControls()});

const ramProcesses=[{label:'Navegador',detail:'Revisar abas que não está usando'},{label:'Launchers de jogos',detail:'Revisar se estão abertos sem necessidade'},{label:'Aplicativos em segundo plano',detail:'Identificar os dispensáveis'}];
const safeTasks=[{id:'startup',label:'Revisar aplicativos de inicialização',desc:'Evitar que programas desnecessários iniciem com o Windows'},{id:'temp',label:'Analisar arquivos temporários',desc:'Mostrar itens seguros para limpeza, após revisão'},{id:'storage',label:'Verificar espaço livre no SSD',desc:'Identificar armazenamento quase cheio'},{id:'game',label:'Verificar Modo de Jogo',desc:'Conferir as configurações de jogos do Windows'}];
function openToolModal(kind){state.toolModal=kind;const isRam=kind==='ram';$('#toolModalTitle').textContent=isRam?'Gerenciar memória RAM':'Otimizar Windows';$('#toolModalSub').textContent='Ferramenta em demonstração';$('#toolModalIcon').innerHTML=svg(isRam?'memory':'settings');
$('#toolModalBody').innerHTML=isRam?`<p class="tool-intro">A memória usada como cache pode ser liberada automaticamente pelo Windows quando necessário. O ideal é identificar consumo excessivo e revisar aplicativos antes de fechá-los.</p><div class="tool-subtitle">Exemplos do que revisar</div>${ramProcesses.map((p,i)=>`<label class="task-option"><input type="checkbox" data-ram-task="${i}"><span><b>${p.label}</b><small>${p.detail}</small></span></label>`).join('')}<button class="tool-confirm" id="toolAnalyzeBtn">Simular análise da RAM</button><div class="tool-result" id="toolResult" aria-live="polite"></div>`:
`<p class="tool-intro">Selecione as verificações desejadas. O sistema só recomendará mudanças após análise e confirmação; nenhuma modificação será feita nesta prévia.</p><div class="tool-subtitle">Verificações disponíveis</div>${safeTasks.map(t=>`<label class="task-option"><input type="checkbox" data-safe-task="${t.id}" checked><span><b>${t.label}</b><small>${t.desc}</small></span></label>`).join('')}<button class="tool-confirm" id="toolAnalyzeBtn">Simular diagnóstico</button><div class="tool-result" id="toolResult" aria-live="polite"></div>`;
$('#toolModalLayer').hidden=false;$('#toolModalClose').focus();}
function closeToolModal(){state.toolModal=null;$('#toolModalLayer').hidden=true}
$('#ramToolsBtn').addEventListener('click',()=>openToolModal('ram'));
$('#windowsToolsBtn').addEventListener('click',()=>openToolModal('windows'));
$('#toolModalClose').addEventListener('click',closeToolModal);
$('#toolModalShade').addEventListener('click',closeToolModal);
$('#toolModalBody').addEventListener('click',e=>{if(e.target.id!=='toolAnalyzeBtn')return;const isRam=state.toolModal==='ram';const selected=[...$('#toolModalBody').querySelectorAll('input:checked')];const result=$('#toolResult');if(!selected.length){result.textContent='Selecione pelo menos um item para revisar.';return;}result.textContent=isRam?`Prévia: ${selected.length} categoria(s) para revisar. Nenhum processo foi encerrado e nenhuma memória foi liberada.`:`Prévia: ${selected.length} verificação(ões) selecionada(s). Nenhum arquivo foi apagado e nenhuma configuração foi alterada.`;result.classList.add('visible')});
renderFanControls();
renderMetrics();setInterval(renderMetrics,2500);
let finishTimer;
function setVoice(status){state.voice=status;els.frame.dataset.voice=status;const active=status==='listening',processing=status==='processing';els.speakBtn.classList.toggle('active',active);els.speakBtn.innerHTML=`<span>${svg(active?'stop':'mic')}</span><span id="speakText">${active?'Parar':'Falar'}</span>`;els.speakBtn.disabled=processing;els.voicePanel.hidden=!active;els.voiceStatus.textContent=active?'Ouvindo... (simulação)':processing?'Processando comando...':'Microfone desligado';if(active){$('#demoCommand').focus()}}
function runCommand(str){if(state.voice!=='listening')return;const t=str.trim().toLowerCase();if(!t){toast('Digite um comando para testar');return}clearTimeout(finishTimer);setVoice('processing');finishTimer=setTimeout(()=>{let msg='Comando demonstrativo recebido';if(t.includes('gamer')){applyScene('gamer');msg='Modo Gamer ativado'}else if(t.includes('dormir')){applyScene('dormir');msg='Cena Dormir ativada'}else if(t.includes('acordar')){applyScene('acordar');msg='Cena Acordar ativada'}else{const id=t.includes('ventilador')?'fan':t.includes('pc')?'pc':t.includes('led')||t.includes('fita')?'led':t.includes('lâmpada')||t.includes('lampada')||t.includes('luz')?'lamp':null;if(id){const v=state.devices[id];if(t.includes('desliga')||t.includes('apaga'))v.on=false;else if(t.includes('liga')||t.includes('acende'))v.on=true;else v.on=true;if(id==='fan'){const speedMatch=t.match(/\b([123])\b/);if(speedMatch)v.speed=Number(speedMatch[1])}if(t.includes('azul')&&id!=='fan')v.color='#397bfa';if(t.includes('vermelh')&&id!=='fan')v.color='#f04759';msg=`${catalog.find(x=>x.id===id).name} ajustado (demo)`;save();renderCards()}}setVoice('idle');toast(msg);$('#demoCommand').value=''},800)}
els.speakBtn.addEventListener('click',()=>{if(state.voice==='idle'){setVoice('listening')}else if(state.voice==='listening'){setVoice('idle');toast('Escuta encerrada')}});
$('#executeCommand').addEventListener('click',()=>runCommand($('#demoCommand').value));$('#demoCommand').addEventListener('keydown',e=>{if(e.key==='Enter')runCommand(e.target.value)});document.querySelectorAll('[data-command]').forEach(btn=>btn.addEventListener('click',()=>runCommand(btn.dataset.command)));
for(const el of document.querySelectorAll('[data-icon]'))el.innerHTML=svg(el.dataset.icon);
$('#minimizeBtn').addEventListener('click',()=>{if(window.loneDesktop)window.loneDesktop.minimize();else toast('O recurso de minimizar funciona na versão Windows')});
$('#closeBtn').addEventListener('click',()=>{if(window.loneDesktop)window.loneDesktop.close();else toast('Feche a aba do navegador para sair')});
if(window.loneDesktop){document.body.classList.add('electron')}
renderCards();renderTabs();


// Gamer Launcher — tudo demonstrativo. Nenhuma detecção, leitura de FPS ou alteração do Windows.
const games={
 cs2:{title:'Counter-Strike 2',short:'CS2',store:'Steam',note:'Competitivo · FPS e estabilidade',desc:'Priorizar consistência dos quadros, baixa latência e evitar processos dispensáveis; não alterar a configuração gráfica automaticamente.',baseFps:322},
 valorant:{title:'VALORANT',short:'VALORANT',store:'Riot Client',note:'Tático · Baixa latência',desc:'Conferir aplicativos em segundo plano, temperatura e consistência de frametime.',baseFps:290},
 fortnite:{title:'Fortnite',short:'FORTNITE',store:'Epic Games',note:'Battle Royale · Equilíbrio',desc:'Escolher conscientemente entre fluidez e qualidade; revisar o uso de VRAM e os processos em segundo plano.',baseFps:168}
};
const gameProfileCopy={
 competitive:{title:'Competitivo',desc:'Foco em consistência de FPS e latência. Não promete ganho automático nem altera arquivos do jogo.'},
 balanced:{title:'Equilibrado',desc:'Balanceia estabilidade, ruído e qualidade visual, sem forçar configurações de hardware.'},
 quality:{title:'Qualidade',desc:'Preserva qualidade gráfica e mantém monitoramento de temperaturas, utilização e frametime.'}
};
const gameTasks=[
 {id:'background',label:'Revisar apps em segundo plano',desc:'Sugerir fechamento apenas dos processos escolhidos por você.'},
 {id:'cooling',label:'Perfil térmico de jogo',desc:'Preparar curva compatível e validada; preservar a bomba do water cooler.'},
 {id:'lighting',label:'Cena RGB via SignalRGB',desc:'Usar um efeito configurado previamente, se a integração estiver disponível.'},
 {id:'gameMode',label:'Verificar Modo de Jogo',desc:'Conferir a configuração do Windows sem alterar serviços ou registro.'}
];
let gamerTimer=null;
function currentGame(){return games[state.gameId]}
function renderGameLibrary(){
 $('#gameLibrary').innerHTML=Object.entries(games).map(([id,g])=>`<button type="button" class="game-tile ${state.gameId===id?'active':''}" data-select-game="${id}" aria-pressed="${state.gameId===id}"><span class="game-tile-icon">${svg('gamepad')}</span><strong>${g.short}</strong><small>${g.store}</small></button>`).join('');
 const g=currentGame();$('#gameSelected').innerHTML=`<span><b>${g.title}</b><br>${g.note}</span><span class="game-store">${g.store}</span>`;
}
function renderGameOptimizer(){
 const g=currentGame(),profile=state.gameProfiles[state.gameId],detail=gameProfileCopy[profile];
 $('#optimizerHint').textContent=g.desc;
 document.querySelectorAll('[data-game-profile]').forEach(btn=>{const active=btn.dataset.gameProfile===profile;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active))});
 $('#gameProfileDetail').innerHTML=`<b>${detail.title}</b> — ${detail.desc}`;
 $('#gameChecks').innerHTML=gameTasks.map(t=>`<label class="game-check"><input type="checkbox" data-game-task="${t.id}" ${state.gameOptions[t.id]?'checked':''}><span><b>${t.label}</b><small>${t.desc}</small></span></label>`).join('');
 $('#overlayPreference').checked=state.gameOptions.overlay;
}
function syntheticGameTelemetry(){
 if(!state.gameSession)return null;
 const t=state.gameTick,base=currentGame().baseFps,offset=Math.round(22*Math.sin(t*.61)+9*Math.sin(t*1.67));
 const fps=Math.max(42,base+offset);
 return {fps,low:Math.max(28,Math.round(base*.66+13*Math.sin(t*.13))),frametime:(1000/fps+0.23*Math.abs(Math.cos(t*1.4))).toFixed(2),cpu:Math.round(60+8*Math.sin(t*.25)),gpu:Math.round(68+7*Math.sin(t*.33)),cpuUsage:Math.round(57+12*Math.sin(t*.4)),gpuUsage:Math.round(78+14*Math.cos(t*.42))};
}
function renderGameTelemetry(){
 const d=syntheticGameTelemetry(),g=currentGame();
 $('#gameSessionLabel').textContent=state.gameSession?`${g.short} · sessão simulada ativa`:'Nenhum jogo em execução';
 $('.session-state').classList.toggle('playing',state.gameSession);
 const minutes=Math.floor(state.gameTick/60),seconds=state.gameTick%60;
 $('#gameTime').textContent=state.gameSession?`${String(minutes).padStart(2,'0')}:${String(seconds).padStart(2,'0')}`:'00:00';
 const metricData=[['FPS atual',d?String(d.fps):'—'],['FPS 1% Low',d?String(d.low):'—'],['Frametime',d?`${d.frametime}`:'—']];
 $('#gameMetrics').innerHTML=metricData.map(([label,v])=>`<div class="game-metric"><b>${v}</b><span>${label}${label==='Frametime'?' (ms)':''}</span></div>`).join('');
 $('#gameResources').innerHTML=[['CPU',d?`${d.cpu}°C · ${d.cpuUsage}%`:'—'],['GPU',d?`${d.gpu}°C · ${d.gpuUsage}%`:'—']].map(([name,value])=>`<div class="game-resource"><span>${name}</span><b>${value}</b></div>`).join('');
 const hist=state.gameHistory, points=hist.map((v,i)=>`${(i/Math.max(hist.length-1,1))*300},${Math.max(8,Math.min(95,100-((v-40)/450)*90)).toFixed(1)}`).join(' ');
 $('#fpsLine').setAttribute('points',points);
 $('#gameChartLabel').textContent=state.gameSession?'Amostras ilustrativas · não medidas':'Aguardando sessão demonstrativa';
 $('#gameSessionButton').innerHTML=`<span>${svg(state.gameSession?'stop':'gamepad')}</span>${state.gameSession?'Encerrar sessão simulada':'Simular sessão de jogo'}`;
}
function stopGameSession(){state.gameSession=false;state.gameTick=0;state.gameHistory=[];clearInterval(gamerTimer);gamerTimer=null;renderGameTelemetry()}
$('#gameLibrary').addEventListener('click',e=>{const target=e.target.closest('[data-select-game]');if(!target)return;stopGameSession();state.gameId=target.dataset.selectGame;save();renderGameLibrary();renderGameOptimizer();$('#gameLog').textContent=`${currentGame().title} selecionado. Perfil salvo localmente, sem alterações no Windows.`;toast(`${currentGame().title} selecionado (demo)`) });
$('#gameProfiles').addEventListener('click',e=>{const btn=e.target.closest('[data-game-profile]');if(!btn)return;state.gameProfiles[state.gameId]=btn.dataset.gameProfile;save();renderGameOptimizer()});
$('#gameChecks').addEventListener('change',e=>{const inp=e.target.closest('[data-game-task]');if(!inp)return;state.gameOptions[inp.dataset.gameTask]=inp.checked;save()});
$('#overlayPreference').addEventListener('change',e=>{state.gameOptions.overlay=e.target.checked;save();toast(`Preferência de overlay ${e.target.checked?'ativada':'desativada'} (demo)`) });
$('#applyGameProfile').addEventListener('click',()=>{
 const tasks=gameTasks.filter(t=>state.gameOptions[t.id]).map(t=>t.label.toLowerCase());
 $('#gameLog').textContent=`Perfil ${gameProfileCopy[state.gameProfiles[state.gameId]].title} preparado em demonstração para ${currentGame().title}. ${tasks.length?`Etapas previstas: ${tasks.join('; ')}.`:'Nenhuma ação adicional selecionada.'} Nada foi alterado no Windows.`;
 toast('Perfil simulado preparado; nenhuma configuração alterada');
});
$('#gameSessionButton').addEventListener('click',()=>{
 if(state.gameSession){stopGameSession();toast('Sessão simulada encerrada');return}
 state.gameSession=true;state.gameTick=0;state.gameHistory=[];renderGameTelemetry();toast('Sessão demonstrativa iniciada — FPS fictício');
 clearInterval(gamerTimer);gamerTimer=setInterval(()=>{if(!state.gameSession)return;state.gameTick++;const d=syntheticGameTelemetry();state.gameHistory.push(d.fps);if(state.gameHistory.length>45)state.gameHistory.shift();renderGameTelemetry()},1000);
});
renderGameLibrary();renderGameOptimizer();renderGameTelemetry();



// Etapa 1.4 — envio WoL real somente no app Android; demais comandos são simulações.
const nativeWake=!!(window.LoneAndroid && typeof window.LoneAndroid.sendWake==='function');
const remote={status:'offline',pending:null,timeout:null,mobile:false,lastWake:''};
const remoteNames={offline:'Estado do PC não verificado',starting:'Iniciando PC... (demo)',online:'PC ligado (demo)',sleeping:'PC suspenso (demo)',restarting:'Reiniciando PC... (demo)',sent:'Pacote WoL enviado'};
const wolDefaults={mac:'02:00:00:C7:AC:53',broadcast:'172.31.250.255',port:9};
let wol=Object.assign({},wolDefaults);
try {const stored=JSON.parse(localStorage.getItem('lone-wol-settings-v1')); if(stored && typeof stored==='object') wol=Object.assign(wol,stored)} catch {}
function saveWol(){try{localStorage.setItem('lone-wol-settings-v1',JSON.stringify(wol))}catch{}}
function syncWolFields(){ $('#wolMac').value=wol.mac; $('#wolBroadcast').value=wol.broadcast; $('#wolPort').value=wol.port; }
function readWolFields(){
  wol.mac=$('#wolMac').value.trim().toUpperCase().replace(/-/g,':');
  wol.broadcast=$('#wolBroadcast').value.trim();wol.port=Number($('#wolPort').value);
  if(!/^([0-9A-F]{2}:){5}[0-9A-F]{2}$/.test(wol.mac))throw Error('MAC inválido. Use AA:BB:CC:DD:EE:FF');
  const octets=wol.broadcast.split('.');
  if(octets.length!==4||octets.some(o=>!/^(0|[1-9]\d{0,2})$/.test(o)||Number(o)>255))throw Error('Endereço de broadcast inválido');
  if(![7,9].includes(wol.port)) throw Error('Selecione porta UDP 7 ou 9');
  saveWol(); return wol;
}
function setWolFeedback(message,success=false){const el=$('#wolFeedback');el.textContent=message;el.dataset.success=success?'true':'false';}
function remoteOnline(){return remote.status==='online'}
function renderRemote(){
  const label=remoteNames[remote.status]||'Estado desconhecido';
  const desc=nativeWake ? {offline:'Estado real ainda não verificado',sent:'Comando transmitido pela rede; aguardando verificação',starting:'Aguardando confirmação',online:'Estado simulado, não verificado',sleeping:'Repouso simulado',restarting:'Reiniciando simulado'}[remote.status] : {offline:'Sem conexão • simulação',sent:'Comando simulado',starting:'Aguardando inicialização simulada',online:'Disponível para comandos simulados',sleeping:'Repouso • simulação',restarting:'Aguardando retorno simulado'}[remote.status];
  const dot=$('#remoteStatusDot').closest('.remote-status');dot.dataset.status=remote.status;
  $('#remoteStatusText').textContent=label;$('#remoteStatusDetails').textContent=desc;
  $('#pcWakeBtn').disabled=!nativeWake && !['offline','sleeping'].includes(remote.status);
  $('#pcWakeText').textContent=nativeWake?'Enviar Wake-on-LAN':remote.status==='sleeping'?'Simular despertar':remote.status==='online'?'PC ligado':['starting','restarting'].includes(remote.status)?'Aguarde...':'Simular ligar PC';
  const modalStatus=$('#remoteModalStatus');modalStatus.className='remote-dialog-status '+remote.status;
  modalStatus.innerHTML=`<i></i><span>${label} • ${nativeWake?'WoL real / estado não confirmado':'demonstração'}</span>`;
  for(const b of document.querySelectorAll('[data-remote-action]')){
    const action=b.dataset.remoteAction;
    b.disabled=action==='wake' ? (!nativeWake && !['offline','sleeping'].includes(remote.status)) : !remoteOnline();
  }
}
function remoteTransition(status,after,delay=1900){
  clearTimeout(remote.timeout);remote.status=status;renderRemote();
  if(after){remote.timeout=setTimeout(()=>{remote.status=after;renderRemote();toast(`PC ${after==='online'?'ligado':after==='offline'?'desligado':after==='sleeping'?'suspenso':'atualizado'} — simulação`)},delay)}
}
function simulateRemoteAction(action){
 if(action==='wake'){
   if(nativeWake){
     try{const cfg=readWolFields();setWolFeedback('Transmitindo pacote WoL...');window.LoneAndroid.sendWake(cfg.mac,cfg.broadcast,cfg.port);toast('Enviando Wake-on-LAN pela rede local...')}
     catch(err){setWolFeedback(err.message);toast(err.message)}
     return;
   }
   if(!['offline','sleeping'].includes(remote.status))return;
   remoteTransition('starting','online',1700);toast('Pacote Wake-on-LAN simulado (não enviado)');return;
 }
 if(!remoteOnline())return;
 if(action==='sleep'){remoteTransition('sleeping');toast('Suspensão simulada, nenhuma ação real');return}
 if(action==='restart'){remoteTransition('restarting','online',2000);toast('Reinicialização simulada, nenhuma ação real');return}
 if(action==='shutdown'){remoteTransition('offline');toast('Desligamento simulado, nenhuma ação real');return}
 if(action==='steam'||action==='cs2'){toast(`${action==='steam'?'Steam':'Counter-Strike 2'} — abertura simulada`);return}
}
window.onLoneWakeResult=function(result){
  if(!nativeWake)return;
  if(result&&result.ok){
    remote.status='sent';remote.lastWake=new Date().toLocaleTimeString('pt-BR');
    renderRemote();setWolFeedback(`Pacote enviado às ${remote.lastWake}. O PC ainda não foi verificado como online.`,true);
    toast('Wake-on-LAN enviado! Confira se o PC despertou.');
  }else{const reason=result&&result.message?String(result.message):'Falha ao enviar Wake-on-LAN';setWolFeedback(reason);toast(reason)}
};
function initNativeWol(){
  syncWolFields();
  $('#wolModeBadge').textContent=nativeWake?'ENVIO REAL NO ANDROID':'DEMONSTRAÇÃO';
  $('#remoteModeTag').textContent=nativeWake?'WoL REAL':'DEMO';
  $('#remoteActionNote').textContent=nativeWake?'O botão Ligar envia um pacote real por Wi-Fi. As outras funções ainda NÃO controlam o Windows.':'No navegador e no Windows todas as ações são simuladas.';
  if(nativeWake){document.body.classList.add('lone-android-native');$('#mobilePreviewBtn').hidden=true;window.loneVersion.render('Android');$('#remoteHelper').textContent='Envio real de Wake-on-LAN no Android. Estado online, desligamento e jogos ainda não estão integrados.'}
  for(const id of ['wolMac','wolBroadcast','wolPort'])$('#'+id).addEventListener('change',()=>{try{readWolFields();setWolFeedback('Configurações salvas neste dispositivo.')}catch(err){setWolFeedback(err.message)}});
  renderRemote();
}
function showRemoteModal(){
 $('#pcRemoteModal').hidden=false;$('#remoteActionPanel').hidden=false;$('#remoteConfirm').hidden=true;remote.pending=null;
 renderRemote();
}
function hideRemoteModal(){remote.pending=null;$('#pcRemoteModal').hidden=true}
function promptRemoteAction(action){
 if(action==='wake'){simulateRemoteAction(action);return}
 if(!remoteOnline())return;
 if(['sleep','restart','shutdown'].includes(action)){
   remote.pending=action;
   const options={sleep:['Suspender computador?','Na próxima etapa, o PC entraria em suspensão e a sessão seria interrompida.'],restart:['Reiniciar computador?','Na próxima etapa, trabalhos não salvos podem ser perdidos ao reiniciar.'],shutdown:['Desligar computador?','Na próxima etapa, aplicativos serão encerrados; salve seu trabalho antes de desligar.']};
   $('#remoteConfirmHeading').textContent=options[action][0];$('#remoteConfirmDescription').textContent=options[action][1]+' Nesta prévia, nada acontece de verdade.';
   $('#remoteActionPanel').hidden=true;$('#remoteConfirm').hidden=false;
 }else simulateRemoteAction(action);
}
$('#pcWakeBtn').addEventListener('click',()=>simulateRemoteAction('wake'));
$('#pcRemoteBtn').addEventListener('click',showRemoteModal);
$('#pcRemoteFromMonitor').addEventListener('click',()=>{state.activeTab='controls';save();renderTabs();$('#pcRemoteSection').scrollIntoView({block:'start',behavior:'smooth'});showRemoteModal()});
$('#pcRemoteShade').addEventListener('click',hideRemoteModal);
$('#remoteModalClose').addEventListener('click',hideRemoteModal);
$('#remoteActionGrid').addEventListener('click',e=>{const btn=e.target.closest('[data-remote-action]');if(btn&&!btn.disabled)promptRemoteAction(btn.dataset.remoteAction)});
$('.remote-app-actions').addEventListener('click',e=>{const btn=e.target.closest('[data-remote-action]');if(btn&&!btn.disabled)promptRemoteAction(btn.dataset.remoteAction)});
$('#remoteCancel').addEventListener('click',()=>{remote.pending=null;$('#remoteActionPanel').hidden=false;$('#remoteConfirm').hidden=true});
$('#remoteConfirmYes').addEventListener('click',()=>{const action=remote.pending;remote.pending=null;$('#remoteActionPanel').hidden=false;$('#remoteConfirm').hidden=true;if(action)simulateRemoteAction(action)});
$('#remoteHowBtn').addEventListener('click',()=>{$('#remoteSetupInfo').hidden=!$('#remoteSetupInfo').hidden});
$('#mobilePreviewBtn').addEventListener('click',()=>{remote.mobile=!remote.mobile;document.body.classList.toggle('mobile-preview',remote.mobile);$('#mobilePreviewBtn').setAttribute('aria-pressed',String(remote.mobile));$('#mobilePreviewText').textContent=remote.mobile?'Ver Windows':'Ver Android';window.loneVersion.render(remote.mobile?'Prévia Android':'Widget Windows 11');toast(remote.mobile?'Layout Android simulado; não é um APK':'Layout Windows restaurado')});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('#pcRemoteModal').hidden)hideRemoteModal()});
initNativeWol();
