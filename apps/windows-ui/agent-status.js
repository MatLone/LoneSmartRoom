'use strict';
(() => {
  const label = document.getElementById('agentState');
  const detail = document.getElementById('agentDetail');
  const last = document.getElementById('agentLast');
  const native = window.LoneAgent;
  const labels = {unknown: 'Desconhecido', connected: 'Conectado', disconnected: 'Desconectado'};
  window.onLoneAgentStatus = result => {
    label.textContent = labels[result.state] || labels.unknown;
    detail.textContent = String(result.message || 'Sem confirmação do agente.');
    last.textContent = result.last_success > 0
      ? `Última comunicação: ${new Date(result.last_success).toLocaleString('pt-BR')}`
      : 'Última comunicação: nenhuma registrada';
  };
  document.getElementById('agentPair').addEventListener('click', () => native?.showPairing());
  document.getElementById('agentRefresh').addEventListener('click', () => {
    if (native) { detail.textContent = 'Consultando identidade e status…'; native.refreshStatus(); }
  });
  if (native) native.refreshStatus();
  else {
    detail.textContent = 'O pareamento e a consulta HTTPS estão disponíveis no aplicativo Android.';
    document.getElementById('agentPair').disabled = true;
    document.getElementById('agentRefresh').disabled = true;
  }
})();
