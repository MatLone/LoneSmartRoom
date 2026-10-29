# Windows focado — candidata dev.9 r12

Base preservada: eb53a82; branch feature/windows-control-center; Android congelado.
O worktree C1 não foi alterado. A interface padrão tem somente Controles,
Monitoramento PC e Gamer Launcher. NEX é um diálogo integrado e Touch Panel
permanece uma janela alternativa do mesmo processo principal. Código das antigas
12 áreas preservado; operações genéricas recusadas no serviço em modo focado.

Implementados: modo gamer CS2 desligado por padrão, detecção de processo com
caminho esperado, polling 5 s mediante consentimento, leitura do cache a 2 s e
histórico a 5 s durante jogo, redução de animações, overlay opcional e restauração
das políticas do próprio LSR. Sessões interrompidas são identificadas ao reabrir.
Não altera Windows, arquivos/configurações de jogos ou segurança; não promete FPS.

Abertura local de Steam/CS2 reutiliza os executores originais byte a byte e seu
WinVerifyTrust com cache local, organização Valve Corp., caminhos e manifestos.
Renderer recebe apenas duas ações enumeradas. Main exige confirmação nativa
individual, recibo durável e cooldown de 60 s; não cria grants remotos.
Inspeção real de prontidão CS2 passou, sem executar Steam ou jogo. A abertura real
continua não homologada e exige confirmação operacional específica.

Testes: 29 suítes Node / 3557 verificações; 24 testes Python dos executores;
regressões temporais de ingresso 1,5 s e frescor 3/11/10 s preservadas. Electron
isolado em 100% e 125% passou 17 verificações por sessão, sem coletor físico.
Modo gamer ativo/restauração foram testados com substitutos identificados; não
representam jogo real. Pacotes passaram 542 inspeções estáticas e comparação dos
três fontes do executor local. NotSigned; nenhum bloqueio do Windows foi contornado.

NSIS r12: 105807090 bytes, SHA-256
7979f17fcfdb42b5d326d194b97e3ae3448ddcc29dc0d574abc63ce7bad9e543.
Portátil: 105516140 bytes, SHA-256
9a4a4e65e19349a60c3ab14584140d33c1b73730bb7837a9141e2271562a60df.
Pasta: .cache/artifacts/windows/desktop-dev9-consolidated-candidate-r12/.

Novo backup fora do Git: Windows-before-dev9-20261029T021121Z (UTC; 28/10 no
horário do usuário), 201 arquivos / 403361107 bytes, ACL exclusiva verificada;
manifesto f6131c8f01068abde895404fb87d16f5b1904a990c6ba8c01c9e80420034c02a.
A instalação original dev.8 e seus 83 arquivos de perfil continuam iguais ao
baseline antes da implantação; backup anterior não substituído. Banco íntegro,
zero grants; nenhum processo de agente ou listener 8776 observado.

A entrada Run ainda referencia o agente direto, não o supervisor validado. Logs
do launcher não têm tentativa correspondente ao boot mais recente. Isso é uma
evidência de configuração antiga, não prova de falha no despacho do Windows.
Migração do agente e alteração de Run não serão feitas junto do instalador.
Requerem confirmação consolidada separada, backup protegido de estado e Run,
validação de um início/encerramento cooperativo, autenticação e decisão explícita
sobre o estado final. Não reiniciar, não forçar processos ou alterar TLS 10054.

Instalação autorizada pelo usuário condicionada aos gates, aguardando a
confirmação em tempo de ação exigida pelo skill de Computer Use. Uma tentativa
NSIS, sem execução automática final; conferir estática e perfil antes da sessão
física. Não executar o portátil. Se bloqueado por segurança, parar.

Rollback: manter backup e journal de preservação. Com app encerrado normalmente,
verificar manifesto e restaurar a instalação dev.8 correspondente, preservando
arquivos externos e qualquer perfil novo para revisão. Não usar reset/pm clear,
não remover backups e não restaurar dados do agente como parte de rollback UI.

Resultados físicos serão registrados após execução; não estão presumidos aqui.

## Integração RGB disponível

O SDK OpenRGB já estava em 127.0.0.1:6742, pertencendo ao processo OpenRGB.
Implementado cliente próprio de inventário usando somente as consultas 0 e 1
do [protocolo oficial](https://gitlab.com/CalcProgrammer1/OpenRGB/-/raw/master/NetworkProtocol.h).
Limites de mensagem, timeout, resposta e número de controladores; nenhum comando
de cores, modos ou redetecção. O endpoint não aceita host/porta do renderer.
A verificação de proprietário é metadado local, sem alegar autenticação forte
ou isolamento contra o mesmo usuário. Leitura real identificou Nollie 16_OS2_1
e B660M AORUS PRO DDR4; zero ações físicas. SignalRGB está presente, mas suas
portas não são usadas como API presumida. Nenhum serviço foi alterado.

As cenas continuam preferências locais sem aplicação física; lâmpada, fita e
ventilador não ganham compatibilidade por inferência. Home Assistant requer
configuração/credencial própria e permanece não configurado.

A interface final passou em 150% com leitura real OpenRGB e inspeção CS2 sem
execução. [Capturas](captures/) e [recibo](focused-electron.json).
