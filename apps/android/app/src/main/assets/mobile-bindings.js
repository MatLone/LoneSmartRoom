'use strict';
// Compose the existing clients; never expose credentials or create a native API.
(() => {
  const agentCallback = window.onLoneAgentStatus;
  const launchCallback = window.onLoneAppLaunch;
  let connected = false, permissionsFresh = false, allowed = new Set();
  const buttons = {steam:document.getElementById('launchSteam'), cs2:document.getElementById('launchCs2')};
  function permitted(app) { return connected && permissionsFresh && allowed.has(app); }
  function renderPermissions() {
    Object.entries(buttons).forEach(([app, button]) => {
      if (!permitted(app)) button.disabled = true;
      document.querySelectorAll('[data-permission="' + app + '"]').forEach(node => {
        node.textContent = permitted(app) ? 'Autorizado pelo agente' : 'Bloqueado';
        node.classList.toggle('locked', !permitted(app));
      });
    });
  }
  // Also reject synthetic click events on disabled controls before legacy listeners.
  document.addEventListener('click', event => {
    const button = event.target.closest('#launchSteam, #launchCs2');
    if (!button) return;
    const app = button.id === 'launchSteam' ? 'steam' : 'cs2';
    if (button.disabled || !permitted(app)) { event.preventDefault(); event.stopImmediatePropagation(); }
  }, true);
  window.onLoneAgentStatus = result => {
    agentCallback(result);
    const previous = connected;
    connected = result.state === 'connected';
    const state = connected ? 'connected' : result.state === 'disconnected' ? 'disconnected' : 'unknown';
    document.getElementById('agentState').dataset.state = state;
    document.getElementById('connectionState').textContent = document.getElementById('agentState').textContent;
    document.getElementById('connectionLast').textContent = document.getElementById('agentLast').textContent;
    document.getElementById('pairingInfo').textContent = connected ? 'O agente confirmou a identidade TLS e a autenticação deste dispositivo.' : 'Sem confirmação atual do agente. O pareamento salvo não foi removido. Falha de conexão não confirma PC desligado.';
    if (!connected || !previous) { permissionsFresh = false; allowed.clear(); }
    renderPermissions();
    if (connected && !previous) window.LoneAgent?.refreshAppPermissions();
  };
  window.onLoneAppLaunch = result => {
    launchCallback(result);
    if (result.kind === 'permissions') {
      permissionsFresh = connected;
      allowed = new Set(connected && Array.isArray(result.allowed_apps) ? result.allowed_apps.filter(app => app === 'steam' || app === 'cs2') : []);
    } else {
      document.querySelectorAll('[data-command]').forEach(node => {
        node.classList.toggle('active', node.dataset.command === result.state);
      });
    }
    renderPermissions();
  };
  renderPermissions();
})();
