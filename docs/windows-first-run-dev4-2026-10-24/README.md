# Teste físico Windows dev.4 — bandeja, dashboard e widget

**Uma única sessão da instalação dev.4 foi executada e encerrada por Sair da bandeja. Nenhum processo Electron permaneceu ativo.** As ações de bandeja foram validadas com assistência manual do usuário e conferência técnica de processos, janela, geometria e preferências. Há limitações de captura e uma diferença de inventário de tarefas sem atribuição confirmada, descritas abaixo.

Data: **24/10/2026**, America/Sao_Paulo (UTC−03:00). Branch `feature/ui-migration-preview`, preservando o checkpoint `4cf5f2cbedc5b6513bbac04ee9a20f6f82c3aa4a` e todos os anteriores. Este registro não contém correções de código, nova instalação ou execução de outro pacote Lone.

## Preparação e sessão

Executável autorizado e aberto uma única vez:

`<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe`

- Antes da abertura: versão do arquivo/registro **2.0.0-dev.4**, 74 arquivos do payload correspondentes à distribuição revisada, zero Electron, zero agente e zero listener 8776.
- Zero grants, verificados em SQLite somente leitura, sem expor dispositivos ou credenciais.
- Backup `Windows-before-dev4-20261024T174801Z` validado antes e depois: **72 arquivos, 27 diretórios, 8.589.376 bytes**, SHA-256 e ACLs privados corretos. Nenhuma restauração.
- Processo principal PID **14860**, criado às **17:04:37,517**; janela observada de identificador **2623538**. Os mesmos quatro PIDs permaneceram nas amostras da sessão; isso corresponde à arquitetura multiprocesso do Electron, não a quatro dashboards.
- Última captura visual antes do encerramento: **17:19:03,733**, perfazendo **866,216 segundos** desde a criação do processo principal. Esse é o período mínimo observado, superior aos 60 segundos solicitados. Não representa um teste de carga ou monitoramento contínuo de todos os frames.
- Consulta às **17:19:53,800** confirmou zero processos do Lone; consulta final do sistema às **17:19:57** confirmou zero Electron, zero agente e zero listener 8776. Não houve reabertura.

## Resultados por requisito

| Teste | Observação / resultado |
|---|---|
| Marca, versão e dashboard | Logo oficial, identidade preto/grafite/vermelho, versão dev.4 e título “Seu espaço, sob controle.” confirmados |
| Controles / Monitoramento PC / Gamer Launcher | Três abas navegadas no dashboard e na navegação inferior do widget |
| Painéis flutuantes | Painel Meu computador abriu e fechou no dashboard e no widget; campos de conexão permaneceram bloqueados |
| Segurança visual | Comunicação não integrada, sensores sem medições fictícias, Steam/CS2 desabilitados e sem ações operacionais |
| Minimizar normal | Botão normal acionado; ícone permaneceu na barra de tarefas, processo e janela mantidos; restauração normal sem nova abertura |
| Minimizar para bandeja | Ação explícita no dashboard e no widget ocultou a janela; PID principal permaneceu ativo e respondendo, sem janela principal visível na amostra de Get-Process |
| Ícone na área de notificação | Ícone LONE observado no painel real de ícones ocultos, com captura nativa do painel |
| Clique no Tray | Usuário confirmou clique no LONE dos ícones ocultos; restaurados o mesmo PID e identificador de janela |
| Menu contextual | Usuário confirmou “Abrir dashboard”, “Modo Widget” e “Sair”, com menu permanecendo aberto; a imagem específica do menu não foi obtida pela ferramenta |
| Abrir dashboard pelo menu | Usuário selecionou a opção; geometria completa **1360 × 960 em (280, 36)** confirmada, com mesmo processo e janela |
| Modo Widget pelo menu | Usuário selecionou a opção; após verificação posterior, modo `widget` e geometria **429 × 820 em (1462, 106)** confirmados |
| Redimensionar | Widget inicial 440 × 820 reduzido para 429 × 820 pelo menu nativo Tamanho; layout continuou legível, com navegação inferior e painel acessíveis |
| Rolagem | Conteúdo do Gamer Launcher rolado no widget, mantendo navegação e controles bloqueados |
| Posição / dimensões | Bounds separados de dashboard/widget preservados no arquivo de preferências e reaplicados durante alternância na mesma sessão |
| Preferência automática | `minimizeToTray:false` durante toda a verificação; não foi alterada |
| Estabilidade | Pelo menos 866,216 s de sessão observada, sem Error, crash ou travamento identificado; amostras dos processos responderam |
| Sair | Usuário selecionou exclusivamente Sair no menu da bandeja; ferramentas confirmaram zero processos e nenhuma janela Lone remanescente |

Não foi realizado teste de segunda invocação nem nova sessão para verificar restauração após reinício do aplicativo: a autorização limitava a execução a uma sessão. O X não foi usado, pois o encerramento solicitado era exclusivamente pelo Tray.

## Evidências reais

As imagens são capturas da aplicação **instalada**, não prévias HTML ou montagem. JPEGs nativos foram preservados sem edição. Algumas capturas da barra de tarefas/área final incluem o desktop e o chat ao fundo; não contêm credenciais do agente.

- [Dashboard Controles](screenshots/01-dashboard.jpg)
- [Monitoramento PC](screenshots/02-monitoramento.jpg)
- [Gamer Launcher](screenshots/03-gamer-launcher.jpg)
- [Painel flutuante no dashboard](screenshots/04-painel-dashboard.jpg)
- [Minimização normal: barra de tarefas](screenshots/05-minimizado-normal.jpg)
- [Dashboard restaurado](screenshots/08-restaurado-pela-bandeja.jpg)
- [Widget inicial](screenshots/09-widget.jpg)
- [Widget redimensionado](screenshots/10-widget-redimensionado.jpg)
- [Painel no widget](screenshots/11-painel-widget.jpg)
- [Monitoramento no widget](screenshots/12-widget-monitoramento.jpg)
- [Gamer Launcher no widget](screenshots/13-widget-gamer.jpg)
- [Rolagem no widget](screenshots/14-widget-rolagem.jpg)
- [Painel nativo com ícone LONE](screenshots/icone-bandeja-painel-real.jpg)
- [Dashboard após opção do menu](screenshots/18-dashboard-menu-bandeja.jpg)
- [Widget após opção do menu, confirmado](screenshots/19-widget-menu-confirmado.jpg)
- [Área de trabalho após Sair](screenshots/20-area-trabalho-apos-sair.jpg)

O estado final dos processos está comprovado por **consultas reais CIM/Get-Process**, em [after-exit-processes.json](evidence/after-exit-processes.json) e [system-after.json](evidence/system-after.json). Não foi aberto o Gerenciador de Tarefas e não foi criada uma imagem sintética que o imite. A captura final do desktop complementa esses recibos; não é uma captura de uma lista gráfica de processos.

### Limitações de observação e interação

O painel do shell não foi exposto como janela controlável pela API. O usuário abriu a área de ícones e operou o menu; as ferramentas capturaram os resultados e verificaram processos, janela e preferências. O painel real dos ícones foi capturado, mas **a captura do menu contextual com os três itens permanece pendente**. Não apresentar capturas do widget como se fossem esse menu.

Uma primeira captura após a confirmação de Modo Widget ainda mostrou dashboard. Os testes foram pausados para esclarecer; o usuário confirmou posteriormente o widget e a leitura seguinte comprovou `mode:widget`, tamanho e posição esperados. Preservam-se ambos os recibos de modo, sem classificar a diferença de momento como defeito comprovado.

A tentativa inicial de arrastar a borda selecionou texto sem mudar o tamanho. A verificação de redimensionamento foi concluída pelo menu nativo da janela (Alt+Espaço → Tamanho), sem configurar o Windows. Nenhuma correção foi aplicada.

As capturas do início de algumas transições receberam árvore de acessibilidade ainda referente à aba anterior, embora a imagem mostrasse a nova aba. Observações posteriores atualizaram a árvore antes de selecionar novos controles. Esses textos transitórios não foram usados para alegar uma falha visual.

## Preservação dos dados e do sistema

**1.185 arquivos protegidos fora do perfil Electron permaneceram idênticos**, incluindo os arquivos instalados dev.4, pacotes, código funcional, originais de recuperação, backup anterior e material privado do agente. O verificador dos originais/cópias de recuperação aprovou **86 registros**.

O perfil de produção teve gravações normais da sessão: de 72 para 76 arquivos, **18 arquivos alterados, 4 adicionados e nenhum original removido**. Isso inclui o novo `desktop-window-state.json` e caches/journals de runtime; o perfil não é descrito como byte a byte idêntico após uma sessão real. Nenhuma operação de limpeza, importação, redefinição ou restauração foi feita, e não foram usados controles que salvem configurações operacionais. Conteúdo do perfil e seus mapas privados de hashes não foram incluídos no Git.

Preferências finais verificadas:

```json
{
  "schema": 1,
  "mode": "widget",
  "bounds": {
    "dashboard": {"x": 280, "y": 36, "width": 1360, "height": 960},
    "widget": {"x": 1462, "y": 106, "width": 429, "height": 820}
  },
  "dashboardMaximized": false,
  "minimizeToTray": false
}
```

Entradas Run/RunOnce e arquivos das pastas de inicialização permaneceram iguais, comparados por valores/hashes sem depender da ordem das propriedades JSON. Configurações de serviços e retratos das regras persistentes de firewall também permaneceram iguais. Não foi habilitado autostart Electron.

### Diferença no retrato de tarefas agendadas — inconclusiva

O hash agregado dos XMLs exportados das tarefas diferiu entre o início e o fim da sessão, embora a contagem permanecesse **204**, com **zero tarefas Lone Smart Room**. Não foram guardados XMLs individuais anteriores nessa coleta; não foi possível identificar qual definição originou a diferença. Não atribuir a diferença ao Electron ou a uma tarefa específica sem evidência adicional.

A consulta limitada encontrou `OneSettings\RefreshCache` existente, com último resultado 0 e execução registrada às **17:05:51**, durante a janela de teste. Isso é uma observação de leitura, **não comprova que essa tarefa causou a diferença**. O canal TaskScheduler/Operational estava desabilitado; não foi habilitado e não há histórico desse canal para atribuir a alteração. Nenhuma tarefa foi iniciada, modificada, registrada ou desabilitada pelo procedimento. Não houve interferência em OneSettings\RefreshCache.

Essa divergência fica registrada como pendência de inventário, separada dos resultados visuais. Não declarar que todas as definições de tarefas foram comprovadamente inalteradas.

## Erros, segurança e estado final

Nenhum evento Application 1000/1001/1002/1026 correlacionado aos componentes consultados foi encontrado no intervalo. Não houve janela Error observada nas capturas desta sessão. Isso não elimina a investigação anterior de Error nem comprova ausência de todo erro não registrado. Uma primeira tentativa do coletor de eventos falhou ao reinterpretar uma data já convertida pelo PowerShell; o coletor foi ajustado e a leitura concluída, sem alterar o aplicativo.

- Agente HTTPS **continua offline**; nenhum processo e nenhum listener 8776. Não foi iniciado/reiniciado.
- Configurações privadas, certificados, HMAC, pareamento, entrada de inicialização do agente e código permanecem preservados. Nenhuma credencial foi descriptografada ou copiada para o Electron.
- **Zero grants** ao final. Não foram executados Steam, CS2, WoL, ações de energia, correções TLS ou ações sobre Android/AMD/rede.
- O desktop continua sem cliente operacional autenticado; a pendência TLS permanece aberta e separada.
- Backup preservado e revalidado: `<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev4-20261024T174801Z`. SHA-256 do manifesto privado: `13c12ff4d0e896dda9915b4d8d9b337aa480565059e844ac6bc41a9932444dcc`.
- **Aplicativo encerrado**, sem processo oculto após Sair. Nenhuma reabertura ou correção será realizada sem nova autorização.

Resultado: os comportamentos de bandeja testados funcionaram na sessão assistida, com restauração da mesma janela, alternância de modo e encerramento completo. Preservam-se como ressalvas a captura ausente do menu contextual e a diferença de inventário de tarefas sem causa determinada. Uma eventual próxima etapa deve tratar essas pendências em escopo próprio, sem presumir autorização para nova execução ou mudança de código.
