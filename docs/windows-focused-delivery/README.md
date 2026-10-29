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

## Preparação da manutenção do agente (não executada)

O agente permaneceu offline. Backup protegido independente:
Agent-before-reliable-20261029T022318Z, 31 arquivos, manifesto
1cce3e7b5a7b83a20e524db5f4fb3c44659695ca727aaef8e7854d2bc3b3a860.
Contém estado criptografado, fontes e a entrada Run anterior para reversão;
nenhuma credencial foi decriptada e nenhum conteúdo privado foi versionado.
Preparação: scripts/prepare-agent-maintenance.py; somente leitura nos originais.

Manutenção proposta, mediante UMA autorização consolidada própria:
1. Renovar identidade/ausência de processos, listener livre e zero grants.
2. Validar o supervisor candidato contra o checkpoint e backup protegido.
3. Uma inicialização manual da candidata, status autenticado e observação de 60 s.
4. Encerrar somente pelo canal cooperativo local. Se houver timeout, parar sem
   forçar processos ou alterar Run. Verificar porta e mutex liberados.
5. Uma segunda inicialização controlada, somente após sucesso do passo anterior,
   para deixar o agente ativo; validar novamente TLS/certificado/pin/status/grants.
6. Substituir apenas a entrada Run específica pelo comando absoluto preparado,
   com comparação prévia do hash do valor original. Não tocar StartupApproved,
   firewall, serviços ou tarefas. Guardar valor anterior no backup protegido.
7. Validar despacho real no próximo login autorizado; sucesso manual não comprova
   inicialização automática. Nenhum reboot/logoff está incluído nesta proposta.

Reversão do agente: com sessão candidata encerrada cooperativamente, restaurar
apenas o valor Run anterior a partir do backup privado. Não sobrescrever banco
ou certificados automaticamente. Recuperar launcher legado apenas sob autorização
separada quando necessário. Relay permanece desativado sem publisher registrado
e permissão de leitura específica; não conceder grants de execução.

Essa manutenção não foi executada nesta entrega; o recibo de preparação registra
registry_written=false, agent_started=false e credentials_decrypted=false.

## Estado de entrega antes da confirmação do instalador

Checkpoint funcional 9ecf48d; integração RGB b832c67; preparação do agente
14a63ee. Árvore limpa antes deste recibo documental. Gates renovados: instalação
e perfil iguais ao baseline, zero grants, zero comandos pendentes, zero listener
8776 e nenhum Electron/Python/ADLX do LSR. Nenhuma nova instalação executada.
A confirmação em tempo de ação foi solicitada para o hash r12 e ainda não foi
respondida neste ponto. Não considerar a instalação/homologação concluídas.

| Funcionalidade | Funciona instalada? | Testada com dados reais? | O que falta? |
|---|---|---|---|
| Organização nas três áreas e NEX | Candidata ainda não instalada | Electron isolado real | Instalar/homologar r12 |
| CPU/GPU/RAM/discos, widget/histórico | Não revalidados nesta fase instalada | Validado anteriormente; regressões nesta fase | Sessão instalada e retomada GPU |
| Biblioteca Steam e inspeção CS2 | Novo fluxo ainda não instalado | Manifestos, assinatura e instalação reais | Teste da interface instalada; abertura requer autorização específica |
| Modo Gamer e restauração do perfil | Ainda não instalado | Substitutos, não jogo real | Homologação com jogo autorizado |
| Inventário OpenRGB | Ainda não instalado | SDK real, 2 controladores, zero escritas | Homologar UI; ações físicas continuam bloqueadas |
| Cenas/lâmpadas/ventilador | Apenas cadastro local | Sem provedor físico validado | Configurar hardware/credenciais e autorizar ações |
| FPS/overlay | CSV implementado; não FPS real homologado | CSV sintético; inspeção de software instalada | RTSS 7.3.7 e Afterburner 4.6.6 encontrados; memória compartilhada/captura não ativada. PresentMon não está no PATH |
| Touch Panel | Novo fluxo ainda não instalado | Janela real em resolução simulada | Homologação de uso por toque |
| Agente HTTPS | Offline, preservado | Leitura de estado; sem nova autenticação | Manutenção própria aprovada e validação cooperativa |

Não há alegação de aplicativo 100% concluído ou de FPS real funcional. Android
permanece intocado, sem ADB ou mudanças no APK. Nenhuma ação de energia, jogo,
LED, firewall ou inicialização automática foi executada nesta fase.
