'use strict';
// Same persisted WoL contract and native packet sender; no dependency on HTTPS.
(() => {
  const key = 'lone-wol-settings-v1';
  const defaults = {mac:'02:00:00:C7:AC:53', broadcast:'172.31.250.255', port:9};
  const native = window.LoneAndroid;
  const button = document.getElementById('pcWakeBtn');
  const feedback = document.getElementById('wolFeedback');
  const settings = document.getElementById('wolSettingsFeedback');
  const fields = Object.fromEntries(['mac','broadcast','port'].map((name,i) => [name,document.getElementById(['wolMac','wolBroadcast','wolPort'][i])]));
  let saved = {...defaults}, readable = true, busy = false, timer;
  try {
    const raw = localStorage.getItem(key);
    if (raw !== null) {
      const value = JSON.parse(raw);
      if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error('Invalid settings');
      saved = {...defaults, ...value};
    }
  } catch (_) { readable = false; }
  const available = () => !!native && typeof native.sendWake === 'function';
  function validate(value) {
    const mac = String(value.mac).trim().replace(/-/g, ':').toUpperCase();
    if (!/^(?:[0-9A-F]{2}:){5}[0-9A-F]{2}$/.test(mac)) throw Error('Informe um MAC válido com seis pares hexadecimais.');
    const broadcast = String(value.broadcast).trim();
    const octets = broadcast.split('.');
    if (octets.length !== 4 || octets.some(x => !/^(0|[1-9][0-9]{0,2})$/.test(x) || Number(x) > 255)) throw Error('Informe um broadcast IPv4 válido.');
    const port = Number(value.port);
    if (![7,9].includes(port)) throw Error('Use somente a porta UDP 7 ou 9.');
    return {...value, mac, broadcast, port};
  }
  function validSaved() { try { return readable && !!validate(saved); } catch (_) { return false; } }
  function render() { button.disabled = !available() || !validSaved() || busy; }
  function syncFields() {
    fields.mac.value = String(saved.mac);
    fields.broadcast.value = String(saved.broadcast);
    fields.port.value = String(saved.port);
    settings.textContent = readable ? 'Abrir ou fechar este painel não altera os valores salvos.' : 'Não foi possível ler a configuração. O registro original foi preservado; revise os campos antes de salvar.';
  }
  document.getElementById('wolSave').addEventListener('click', () => {
    try {
      const next = validate({...saved, mac:fields.mac.value, broadcast:fields.broadcast.value, port:fields.port.value});
      localStorage.setItem(key, JSON.stringify(next));
      saved = next; readable = true;
      syncFields(); settings.textContent = 'Configuração Wake-on-LAN salva neste aplicativo.';
      feedback.textContent = 'Wake-on-LAN pronto. O envio é independente da conexão HTTPS.';
      render();
    } catch (error) { settings.textContent = error.name === 'QuotaExceededError' || error.name === 'SecurityError' ? 'Não foi possível salvar. A configuração anterior foi mantida.' : error.message; }
  });
  button.addEventListener('click', () => {
    if (busy || !available() || !validSaved()) return;
    const config = validate(saved);
    busy = true; render();
    feedback.removeAttribute('data-success');
    feedback.textContent = 'Enviando pacote Wake-on-LAN…';
    // A timeout never retries the UDP send and never marks the PC as powered on.
    timer = setTimeout(() => { busy = false; render(); feedback.textContent = 'Sem confirmação do envio. O estado do PC permanece não verificado.'; }, 15000);
    try { window.LoneAndroid.sendWake(config.mac, config.broadcast, config.port); }
    catch (_) { window.onLoneWakeResult({ok:false}); }
  });
  window.onLoneWakeResult = result => {
    clearTimeout(timer); busy = false; render();
    const ok = result?.ok === true;
    feedback.dataset.success = String(ok);
    feedback.textContent = ok ? 'Pacote Wake-on-LAN enviado. Consulte o status HTTPS para verificar o retorno do agente.' : 'O envio Wake-on-LAN não foi confirmado. Confira a configuração e a rede.';
  };
  window.loneWolUI = Object.freeze({syncFields});
  syncFields(); render();
  feedback.textContent = !readable || !validSaved() ? 'Revise a configuração Wake-on-LAN. Nenhum dado foi substituído.' : !available() ? 'O envio Wake-on-LAN está disponível no aplicativo Android instalado.' : 'Wake-on-LAN pronto. O envio é independente da conexão HTTPS.';
})();
