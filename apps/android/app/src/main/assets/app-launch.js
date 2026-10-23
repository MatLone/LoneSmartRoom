'use strict';
(() => {
  const native = window.LoneAgent;
  const state = document.getElementById('launchState');
  const detail = document.getElementById('launchDetail');
  const buttons = {steam: document.getElementById('launchSteam'), cs2: document.getElementById('launchCs2')};
  const query = document.getElementById('launchQuery');
  let allowed = new Set(), busy = false;
  const render = () => Object.entries(buttons).forEach(([app, button]) => { button.disabled = !native || busy || !allowed.has(app); });
  window.onLoneAppLaunch = result => {
    if (result.kind === 'permissions') {
      allowed = new Set(Array.isArray(result.allowed_apps) ? result.allowed_apps.filter(app => app in buttons) : []);
      detail.textContent = result.message || (allowed.size ? 'Confirme cada abertura no diálogo do aplicativo.' : 'Autorize Steam e/ou CS2 para este dispositivo no Windows.');
    } else {
      const labels = {requested: 'Solicitado', accepted: 'Aceito', executed: 'Executado', failed: 'Falha'};
      state.textContent = labels[result.state] || 'Desconhecido';
      busy = ['requested', 'accepted'].includes(result.state);
      const messages = {
        requested: 'Solicitação enviada; aguardando confirmação do agente.',
        accepted: 'O agente aceitou a solicitação. Consulte o resultado se necessário.',
        executed: 'O executor entregou a abertura ao Windows. Isso não confirma que a janela ou o jogo já carregou.',
        failed: 'A abertura falhou ou não foi confirmada. Consulte a solicitação antes de tentar novamente.'
      };
      detail.textContent = result.message || messages[result.state] || 'Consulte a solicitação.';
      query.disabled = !native;
    }
    render();
  };
  Object.entries(buttons).forEach(([app, button]) => button.addEventListener('click', () => native?.requestAppLaunch(app)));
  document.getElementById('launchPermissions').addEventListener('click', () => native?.refreshAppPermissions());
  query.addEventListener('click', () => native?.refreshLaunchResult());
  document.getElementById('launchPermissions').disabled = !native;
  query.disabled = !native;
  render();
  if (native) { native.refreshAppPermissions(); native.refreshLaunchResult(); }
  else detail.textContent = 'Abertura remota disponível no Android pareado, após autorização no Windows.';
})();
