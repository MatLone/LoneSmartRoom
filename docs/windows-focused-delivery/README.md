# Windows focado — candidata dev.9 r11

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

Testes: 28 suítes Node / 3542 verificações; 24 testes Python dos executores;
regressões temporais de ingresso 1,5 s e frescor 3/11/10 s preservadas. Electron
isolado em 100% e 125% passou 17 verificações por sessão, sem coletor físico.
Modo gamer ativo/restauração foram testados com substitutos identificados; não
representam jogo real. Pacotes passaram 536 inspeções estáticas e comparação dos
três fontes do executor local. NotSigned; nenhum bloqueio do Windows foi contornado.

NSIS r11: 105806423 bytes, SHA-256
4104a54d672d0ab6a02cecd089df690967471b5611356c09bb0ddc897368aef3.
Portátil: 105515476 bytes, SHA-256
b8a976310965baa2890f2623260c30f27e6c157db796e26d33316380591e9985.
Pasta: .cache/artifacts/windows/desktop-dev9-consolidated-candidate-r11/.

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
