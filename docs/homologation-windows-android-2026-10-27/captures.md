# Capturas físicas desta sessão

Nenhuma imagem abaixo é simulação. A proveniência e os hashes estão em
[`evidence/capture-provenance.json`](evidence/capture-provenance.json).

## Samsung — Controles e HTTPS preservado

![Android dev.9 — Controles e Conectado](captures/android-controls.png)

## Samsung — Monitoramento, sem métricas remotas fictícias

![Android Monitoramento PC](captures/android-monitor.png)

[Área inferior após rolagem](captures/android-monitor-scrolled.png).

## Samsung — Gamer Launcher, zero grants

![Android Gamer Launcher bloqueado](captures/android-gamer.png)

## Samsung — Painel de dispositivo

![Painel de Lâmpada indisponível](captures/android-device-panel.png)

[Painel da identidade visual](captures/android-brand-panel.png).

A captura do ícone real na tela inicial está no cache local
`.cache/validation/samsung-v23-physical/screens/home-official-icon.png`.
Não foi versionada porque inclui conteúdo da tela inicial fora do aplicativo.
A gravação da abertura não comprovou visualmente a splash nativa; não se inclui
um asset estático como se fosse uma captura física dela.

## Windows instalado — espera por nova amostra ao reativar

![Windows aguardando nova amostra GPU](captures/windows-updating.png)

Essa evidência é da reativação inicial da janela. Não corresponde ao instante
posterior à restauração específica pela bandeja, que não foi capturado.

## Windows instalado — Monitoramento com dados reais

![Windows dev.7 Monitoramento PC](captures/windows-monitor.png)

## Windows instalado — Modo Widget

![Widget da dev.7 instalada](captures/windows-widget.png)

Restauração pela bandeja e seleção de Sair foram confirmadas pelo usuário;
encerramento e liberação dos pipes foram comprovados pelo observador, conforme
[`evidence/windows-resources.json`](evidence/windows-resources.json).
