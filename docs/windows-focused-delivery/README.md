# Windows dev.9 r12 — entrega instalada e manutenção do agente

Consolidação de 29/10/2026. Branch `feature/windows-control-center`.
Implementação: `9ecf48d` e `b832c67`; preparação e gates: `14a63ee` e
`3682823`. Checkpoints anteriores e worktree C1 preservados, sem merge global.
Android congelado: nenhum ADB, APK ou aplicativo Samsung acessado nesta entrega.

## Resultado atual

A atualização NSIS foi executada uma vez, com confirmação assistida, sem abertura
automática ao concluir. Windows **2.0.0-dev.9** instalado em
`<USERPROFILE>\AppData\Local\Programs\Lone Smart Room`.
Identificador `com.lone.smartroom`. Conferência final: **118 arquivos** iguais
à candidata; aplicativo fechado e zero processos Electron/coletor/IPC/ADLX do LSR.
Enumeração complementar do namespace de pipes: zero nomes LoneSmartRoom.
O leitor padrão não conseguiu enumerar o namespace; a confirmação veio da
consulta complementar, registrada separadamente. Não confundir ausência de
resultado no primeiro leitor com prova de ausência de pipe.

O agente está ativo: supervisor efetivo **18256**, worker HTTPS **6500**,
com redirecionadores da venv **6040 / 19612**. São duas cadeias legítimas de
redirecionador/runtime, verificadas por imagem, argumentos, identidade e parentesco;
não duas instâncias operacionais. Listener único 8776 pertencente ao worker.
Última consulta em **03:27:31 UTC**: HTTP 200, TLS 1.3, hostname e pin válidos,
banco íntegro, **zero grants e zero comandos pendentes**.

## Matriz objetiva

| Funcionalidade | Funciona instalada? | Testada com dados reais? | O que falta? |
|---|---|---|---|
| Controles, Monitoramento PC e Gamer Launcher | Sim | Interface instalada | Revisão continuada de uso; antigas 12 áreas arquivadas, fora da navegação padrão |
| CPU, GPU, RAM e discos | Sim | CPU/RAM/PDH/AMD ADLX reais | Temperatura CPU indisponível; nenhuma estimativa fictícia |
| Widget e navegação compacta | Sim | Leituras reais e mesma janela | Homologação completa do instante de retomada GPU pela bandeja |
| Bandeja, restauração e Sair | Sim | Usuário restaurou e selecionou Sair; processos encerrados | Captura confiável do estado GPU imediatamente após restaurar |
| Histórico e gráficos | Sim, dados locais limitados | Pontos reais observados | Exportação CSV preservada e testada automaticamente; não repetida fisicamente nesta fase |
| NEX | Sim, regras locais e cache | Resumo com sensores reais | Não é IA externa nem cliente HTTPS autenticado |
| Biblioteca e inspeção Steam/CS2 | Sim, leitura | Manifestos e executável verificado; nenhum jogo em execução | Abertura real exige autorização operacional específica |
| Modo Gamer | Código e interface instalados, desligado por padrão | Detecção sem jogo; ativação/restauração com mocks | Sessão real de jogo autorizada; não altera configurações do Windows |
| Touch Panel | Sim, janela alternativa | Janela instalada com dados reais | Entrada por toque/hardware específico não homologada |
| OpenRGB | Inventário somente leitura | Nollie 16_OS2_1 e B660M AORUS PRO DDR4 | Escrita física não habilitada nem testada |
| Cenas, lâmpadas e ventilador | Preferências/cadastro local | Sem atuação física | Provedor, hardware, credenciais próprias e autorização |
| FPS e overlay | Importação/tail CSV e overlay preparados | Fixtures; sem captura FPS ao vivo nesta fase | RTSS 7.3.7/Afterburner 4.6.6 encontrados; leitor ao vivo não ativado. PresentMon ausente do PATH |
| Central de Diagnóstico | Contratos/interface preparados | Mocks e leitores anteriormente validados | Integração operacional do dashboard ainda protegida; não chama novas sondas |
| HTTPS do agente | Sim | TLS 1.3, pinagem e status autenticado reais | TLS 10054 continua aberto |
| Supervisor e parada cooperativa | Sim | Início, estabilidade, parada normal, liberação de mutex/porta e novo início | Despacho real após login ainda não testado |
| Relay para Android | Código preparado, desativado sem publisher/escopo de leitura | Não ativado nesta entrega | Migração coordenada futura; nenhuma identidade Samsung copiada para Electron |

## Evidências físicas da instalação

[Capturas reais](installed-captures/) separadas das prévias de desenvolvimento em
`captures/`. Dashboard, monitoramento, Gamer, widget, NEX, biblioteca, Touch Panel
e OpenRGB são do executável instalado, não HTML isolado.

Amostras observadas: CPU 7–24%; RAM aproximadamente 7,7–8,1 GiB / 15,8 GiB;
GPU 0–5%, 53–54 °C, hotspot 55–60 °C; VRAM aproximadamente 662–732 MB / 12272 MB;
clock 270–302 MHz, potência 38 W e ventoinha 482–488 RPM. São exemplos das
capturas, não uma série estatística completa de sensores. C: 475,6 GiB com
216,7 GiB livres (54,4% ocupado); D: 447,1 GiB com 242,1 GiB livres (45,9%).
I/O zero válido e atividade positiva inferior a 0,1% permaneceram distintos de null.
Origem/timestamp/idade foram exibidos; exemplo GPU: coleta 02:53:42.413 UTC,
intervalo 2 s, ingresso 0,4 s e idade da informação 2 s, dentro do limite ativo 3 s.

A primeira observação de recursos teve **180,53 s**. O aplicativo ainda estava
ativo ao terminar essa medição; encerramento por Sair confirmado **258,61 s após
a abertura**, após interação manual e espera das ferramentas. Não declarar
encerramento dentro de 180 s. Duas sessões complementares distintas verificaram
NEX/biblioteca e Touch/OpenRGB, com pedidos de fechamento normal aos 105,58 s e
131,09 s, respectivamente. Nenhum processo foi encerrado à força.

A captura solicitada após restaurar pela bandeja atingiu a janela do chat e os
metadados UIA disponíveis estavam antigos. Esse arquivo foi preservado apenas no
cache privado e **não é evidência de GPU atualizada**. O comportamento permanece
parcialmente homologado, apesar das regressões temporais passarem. Nenhum limite
1,5 / 3 / 11 / 10 s foi relaxado.

### Desempenho observado

91 observações, aproximadamente 2,006 s entre amostras; primeira sessão somente.

| Componente | CPU média total | RSS médio | RSS pico |
|---|---:|---:|---:|
| Electron | 0,787% | 368,81 MiB | 397,96 MiB |
| Python coletor + IPC | 0,062% | 54,53 MiB | 55,42 MiB |
| Ponte ADLX | 0,018% | 23,54 MiB | 24,09 MiB |
| Conjunto | **0,867%** | **446,88 MiB** | **477,32 MiB** |

CPU por delta GetProcessTimes / tempo real / 12 processadores lógicos. O primeiro
delta de cada processo é indisponível e omitido; início de processos pode reduzir
ligeiramente a média calculada. RSS somado pode contar páginas compartilhadas
mais de uma vez. Pico conjunto calculado por instante, não soma de picos.
Coletor e intermediário Python foram agrupados; não atribuir consumo separado sem
medição. Referências anteriores tiveram outras condições; não comprovam regressão.
O observador passivo não inicia, sinaliza ou encerra o aplicativo.

Foram observadas novas mensagens Crashpad `0xE9` no debug.log. O prefixo original
do arquivo continua íntegro. Não há evidência suficiente para classificá-las como
crash do aplicativo; consulta limitada a eventos Application 1000/1001 na última
hora não retornou eventos correspondentes. Não foi aplicado remendo Crashpad.

## Manutenção consolidada do agente — executada com autorização própria

Backup protegido: **Agent-before-reliable-20261029T022318Z**, 31 arquivos.
Manifesto SHA-256:
`1cce3e7b5a7b83a20e524db5f4fb3c44659695ca727aaef8e7854d2bc3b3a860`.
Inclui estado cifrado e recuperação privada de Run; conteúdo sensível não foi
versionado. Fontes consolidados reutilizam `reliable_bootstrap.py`, hash
`f3c764247fcd34907c916e7e6ef8aea7dca056d03f05cf3a0aaa18ecca443ee6`.

1. Primeiro início 03:01:06 UTC, uma tentativa. Identidade, listener e HTTPS
   autenticado aprovados; estabilidade confirmada por 104,76 s.
2. Parada pelo evento local protegido às 03:03:19 UTC, código 0. Worker fechou
   listener, concluiu encerramento e liberou mutex; supervisor encerrou. Porta
   livre, mutexes readquiridos/liberados e banco íntegro. Nenhum taskkill/força.
3. Segundo início 03:04:43 UTC para deixar a comunicação ativa. Autenticação
   aprovada antes de qualquer alteração de inicialização automática.
4. Somente o valor Run existente foi substituído, comparando o original e
   conferindo a leitura após gravar. Hash anterior
   `3139f837ebc03ab77c5c16bc00fcb76031fb6a50ef8ccbcd4a014d6c4b509dc5`;
   novo `51c5c7be89b6f1e1ed134c2d4e5c398fe8cff088607fe203383383f12c1958dc`.
   Comando absoluto com Python da venv e `-I -B`; não houve serviço, tarefa,
   alteração de StartupApproved, firewall ou reboot/logoff.

Isso homologa a parada cooperativa da implementação consolidada, não demonstra
que o Windows já a despachou após login. O valor antigo apontava diretamente ao
agente; logs antigos sem tentativa após o boot sugerem configuração antiga, mas
não comprovam por si falha do Windows. Próximo login requer validação própria.
Samsung não foi acessado; as identidades cifradas e certificados foram comparados
ao backup e preservados. Não declarar confirmação física Android nesta sessão.

## Testes e integridade

- 29 suítes Node, **3557 verificações** aprovadas, incluindo UI, IPC, preload,
  ciclo de vida, histórico, modo gamer e OpenRGB.
- **24 testes Python** dos executores Steam/CS2 com processos substitutos.
- **137 testes isolados** de confiabilidade do agente na fonte consolidada.
- **542 inspeções** do pacote e comparação dos fontes locais autorizados.
- Electron de desenvolvimento: 17 verificações em 100%, 17 em 125% e 18 em 150%.
- Regressões GPU preservam 1,5 s de ingresso, 3/11 s de frescor e 10 s de falha
  persistente após restauração. Nenhuma execução física adicional para testes.
- Após instalação e uso: 118 arquivos iguais ao artefato, identidades do banco
  iguais ao backup, config/certificados iguais, workbench-v1 preservado e backups
  verificados. Geometria, cache, histórico e conversa NEX mudam normalmente pelo
  uso; não alegar perfil inteiro byte a byte idêntico após essas sessões.

Nenhum Steam/CS2, benchmark, WoL, energia ou escrita RGB executado. Nenhuma
credencial, certificado ou grant criado. Android permaneceu congelado.

## Pacotes e reversão

NSIS r12: **105807090 bytes**,
`7979f17fcfdb42b5d326d194b97e3ae3448ddcc29dc0d574abc63ce7bad9e543`.
Portátil: **105516140 bytes**,
`9a4a4e65e19349a60c3ab14584140d33c1b73730bb7837a9141e2271562a60df`.
Ambos NotSigned; nenhum controle Windows foi contornado. Portátil não executado.
Artefatos preservados em `.cache/artifacts/windows/desktop-dev9-consolidated-candidate-r12/`.

Backup Windows: **Windows-before-dev9-20261029T021121Z**, 201 arquivos,
403361107 bytes, ACL exclusiva. Manifesto:
`f6131c8f01068abde895404fb87d16f5b1904a990c6ba8c01c9e80420034c02a`.
Ele contém a dev.8 instalada antes desta atualização e 83 arquivos de perfil.
Backups anteriores continuam preservados. Reversão não foi executada.

Para reverter UI: fechar normalmente, verificar manifesto, guardar separadamente
os dados atuais e restaurar a instalação correspondente à dev.8 sem apagar perfil
ou arquivos externos. Usar journal de preservação do instalador; não remover
backups. Não restaurar o banco do agente como parte da reversão do Electron.
Para reverter o agente: autorização própria, parada cooperativa, restauração
somente do valor Run anterior a partir de `run-recovery.json` protegido; verificar
porta livre e identidade antes de qualquer início legado. Não sobrescrever
certificados, dispositivos ou banco automaticamente.

Pendências: retomada GPU com evidência confiável; login automático real;
TLS 10054; avisos Crashpad; FPS ao vivo; teste autorizado do Modo Gamer;
integração física de dispositivos e cliente desktop autenticado independente.
Ações correspondentes exigem homologação própria, não nova instalação rotineira.
