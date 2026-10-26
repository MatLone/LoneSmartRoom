# Retomada GPU — sessão física complementar em desenvolvimento

26/10/2026, checkpoint `f97f0bd`, correção funcional `3dc783c`.
**Uma sessão, 35,98 s, encerrada normalmente.** Retomada aprovada nos cenários
reais observados. Indisponibilidade persistente e rejeição ADLX não ocorreram;
continuam comprovadas por mocks, sem alegação de teste físico desses casos.

A instalação Windows dev.6 não foi aberta nem modificada. Não houve compilação,
NSIS, instalação, atualização de Android/agente ou repetição da sessão.

## Alvo, isolamento e relógio

- Electron de desenvolvimento existente, carregando `apps/windows-ui` da branch
  `feature/ui-migration-preview`, com a correção `3dc783c`.
- Conteúdo dessa pasta comparado ao commit funcional sem diferenças. Sete hashes
  da entrega da correção conferidos; 97 hashes de fontes e quatro do ensaio
  temporário conferidos antes/depois. [Recibo](evidence/source-receipt.json).
- Perfil novo e exclusivo em `.cache/windows-monitoring-development/<sessão>/`.
  Nenhuma importação do perfil de produção; isolamento, contextIsolation,
  sandbox e Node Integration desabilitado conferidos na execução.
- Ponte real com recibo/binário/fonte correspondentes. DLL oficial System32
  verificada por hash e Authenticode antes da abertura; carregamento real ADLX
  confirmado. Nenhuma instalação de SDK/driver/runtime ou elevação.
- O processo principal foi criado às **11:22:16,214739 BRT / 14:22:16,214739 UTC**.
  O observador de recursos ancorou o relógio monotônico em GetProcessTimes, não
  no término da chamada da ferramenta. Ausência de componentes confirmada aos
  **35,978 s**, antes do limite de 120 s.
- O ensaio reservava Sair até aproximadamente 45 s. Concluiu os itens essenciais
  mais cedo e o acionou aos **34,30 s**. Tempos internos de ações usam um marco
  monotônico conservador imediatamente anterior ao lançamento; não são contagens
  iniciadas depois da abertura. O tempo total acima usa a criação efetiva.

## Método e limite da interação

O ensaio temporário acompanhou os entrypoints reais, sem reescrever métricas.
Ocultação, restauração, modo widget e Sair passaram pelos controles reais da
aplicação. O **callback do item Sair do menu real da bandeja** foi acionado pelo
harness de desenvolvimento. Não foi um clique de mouse no menu, nem kill ou
encerramento direto do worker. Essa distinção permanece registrada: acessibilidade
do menu/contexto visual e clique humano na bandeja não foram novamente homologados.

O temporizador independente do ensaio estava preparado para priorizar o mesmo
Sair aos 45 s mesmo se a coleta de evidências demorasse. Não foi necessário
esperá-lo. Não havia recuperação forçada/reabertura automática. O único marcador
de tentativa impede um novo lançamento pelo mesmo procedimento.

As capturas abaixo vieram de `BrowserWindow.capturePage` da janela Electron real
com sensores reais; não são HTML isolado, mockup ou montagem. A ferramenta Windows
também encontrou a janela de desenvolvimento; não foi necessário enviar gestos
externos para concluir o fluxo dentro do prazo.

## Resultado da retomada

| Fluxo real | Atualizando | Nova leitura válida / ready | Espera |
| --- | --- | --- | --- |
| Minimização normal e restauração | 12,642 s | 14,669 s | **2,027 s** |
| Ocultação para bandeja e restauração | 28,021 s | 30,061 s | **2,041 s** |

Durante Atualizando, todos os valores GPU dinâmicos ficaram nulos/não válidos.
A telemetria do renderer registrou literalmente **“Atualizando GPU após restauração
· aguardando nova amostra”** enquanto a janela estava visível. A UI só voltou a
mostrar os valores após a nova amostra válida; a legenda passou a indicar a
atualização ADLX com seu timestamp. `ready` corresponde ao estado atualizado,
sem inventar um texto “Atualizado” que não consta na interface.

Na retomada pela bandeja, um snapshot subsequente ainda tinha cadência inativa
de 10 s. Não encerrou Atualizando, mesmo com idade de cache baixa. O snapshot
ativo seguinte, cadência de 2 s, foi aceito; o cache GPU estava com idade de
aproximadamente **0,031 s** e ingresso de **0,471 s**. As sete leituras dinâmicas
novas eram válidas, inclusive considerando a idade adicional da informação ADLX.
Não houve promoção de dados anteriores à restauração a valores atuais.

[Linha do tempo e textos observados](evidence/resume-timeline.json).

### O que foi e não foi observado

| Item | Evidência |
| --- | --- |
| Atualizando, espera e recuperação com leitura nova | **Real**, duas retomadas |
| Dashboard, widget, CPU/GPU/RAM/discos | **Real** |
| Mesmo objeto/janela após bandeja e widget | **Real**, uma janela; ID interno 1 |
| Zero GPU válido | **Real**, 0% nas 13 leituras admitidas |
| GPU persistentemente indisponível após 10 s | **Não ocorreu fisicamente**; mocks aprovados |
| Rejeição ADLX, age_null, NaN/infinito/futuro | **Não ocorreram nesta sessão**; mocks aprovados |
| Falha e recuperação de IPC | Não ocorreu; 23 respostas, zero timeouts/rejeições |
| Expiração exatamente em 3/11 s | Limites preservados; fronteiras exatas comprovadas por mocks, não forçadas no hardware |
| Clique de mouse no menu/contexto da bandeja | Não repetido; foram usados os callbacks reais |
| Todas as abas, painéis e rolagem completa | Não repetidos nesta sessão curta |

Nenhum erro foi injetado na sessão física. Não houve falha de hardware/driver
provocada, carga artificial, benchmark, jogo ou alteração de configurações GPU.

## Sensores e cadência

RX 6750 XT identificada pelo ADLX 1.4; as sete capacidades dinâmicas retornaram
suporte confirmado. Capacidade total de VRAM também disponível, **12.272 MB**
na unidade retornada pelo SDK, sem reinterpretá-la como GiB.

| Métrica GPU | Mínimo | Média | Máximo |
| --- | ---: | ---: | ---: |
| Utilização (%) | 0 | 0 | 0 |
| Temperatura (°C) | 55 | 55,92 | 57 |
| Hotspot (°C) | 59 | 59,62 | 61 |
| VRAM utilizada (MB) | 949 | 968,38 | 982 |
| Clock (MHz) | 0 | 791,15 | 2498 |
| Potência (W) | 33 | 39,85 | 51 |
| Ventoinha (RPM) | 491 | 493,92 | 498 |

**Uma inicialização nativa, 13 tentativas, 13 frames admitidos com leituras
dinâmicas válidas, zero rejeitados e zero aquecimentos ADLX contados.**
O cache inicialmente expôs `warming_up` antes da primeira leitura; isso não
representa um frame ADLX rejeitado. Uma leitura de capacidade estática não foi
contada como frame dinâmico. Instrumentação de diagnóstico de frames permaneceu
desativada; o observador registrou apenas resultados sanitizados.

Idade de ingresso observada: **0,006–0,585 s**, dentro de 1,5 s. Intervalos entre
leituras: **2,004–10,003 s**, média 2,675 s incluindo a inatividade. Houve redução
de cadência durante a ocultação e retorno à cadência ativa. Não se aumentou
nenhum limite temporal. [Dados GPU](evidence/gpu-summary.json).

Valores básicos únicos observados no cache/UI, sem contar novamente o mesmo
timestamp; não são todas as amostras internas do coletor:

- CPU: **3,60–24,11%**, média 8,55% (20 leituras válidas distintas).
- RAM: total 16.925.159.424 bytes; utilização **59,99–60,91%**.
- C: 510.677.479.424 bytes totais, 253.689.745.408 disponíveis, ocupação **50,31%**.
- D: 480.101.003.264 bytes totais, 259.957.473.280 disponíveis, ocupação **45,85%**.
- C: leitura **0–1.153.628 bytes/s**, gravação **0–1.876.332 bytes/s**.
- D: leitura e gravação **0 bytes/s válidos**, sem gerar carga para alterá-los.
- Atividade PDH válida: C **0,043–0,482%**, D **0,007–0,046%**; também houve
  indisponibilidade intermitente, preservada como `null`. Não foi substituída por
  zero nem confundida com ocupação/taxa de I/O. Causa não investigada neste escopo.

CPU/RAM e dados dinâmicos antigos ficaram desatualizados nas consultas do host
enquanto oculto; o renderer deliberadamente não atualiza o DOM oculto. Após a
restauração, o conteúdo visível foi renovado pelo fluxo normal. Não se apresenta
texto de uma janela oculta como se fosse uma medição atual exibida ao usuário.

[Métricas básicas](evidence/sensor-summary.json) e
[observações PDH opcionais](evidence/optional-pdh-observations.json).

## Capturas reais

Dashboard, janela de 1360 × 960:

![Dashboard real com dados Windows e AMD ADLX](evidence/01-dashboard-real.png)

Widget, janela redimensionada para 390 × 740:

![Widget real com CPU GPU RAM e temperatura](evidence/02-widget-real.png)

A navegação inferior permanece visível; o conteúdo inferior exige rolagem normal.
Não foi percorrida toda a página para conservar tempo. Não se declara aprovação
de cada posição de scroll ou painel com base em somente essas capturas.
“Comunicação não integrada” no topo continua descrevendo o cliente desktop do
agente HTTPS, ainda não implementado. É independente do **coletor local conectado**
e do agente HTTPS que permanece atendendo o Android.

## Desempenho observado

CPU média abaixo: tempo de kernel+usuário dos processos observados, dividido por
35,978 s e por 12 processadores lógicos, em percentual da máquina. Pico CPU é o
maior intervalo amostrado de aproximadamente 1 s, não um pico instantâneo garantido.

| Componente | CPU média | Pico CPU observado | RSS médio / pico (MiB) |
| --- | ---: | ---: | ---: |
| Electron, 4 processos | 1,386% | 3,469% | 367,61 / 410,24 |
| Intermediário IPC, PID 1276 | 0,0217% | 0,130% | 22,87 / 22,88 |
| Coletor, PID 15904 | 0,0977% | 0,130% | 31,22 / 31,30 |
| ADLX, PID 2296 | 0,0832% | 0,130% | 24,57 / 24,60 |
| **Conjunto** | **1,589%** | **3,469%** | **441,07 / 488,94** |

As médias RSS por componente usam suas janelas de existência; sua soma não é
idêntica à média conjunta que inclui o começo da inicialização. Working sets
somados podem contar páginas compartilhadas mais de uma vez. O observador Python
externo não está incluído; os observers executados dentro dos componentes e as
capturas estão incluídos.

O valor de CPU conjunta é superior à referência anterior de 0,529%. Esta sessão
durou apenas 36 s, incluindo startup, capturas, minimização e restauração. Não é
uma comparação equivalente nem demonstra regressão causada pela correção.
Não se comprovou uma meta de CPU conjunta inferior a 0,5%. Para avaliar consumo
estável será necessário outro protocolo autorizado, sem alongar esta sessão.
[Recibo de desempenho](evidence/performance.json).

## Encerramento, erros e preservação

Sair passou pelo callback real às 34,30 s. O evento `will-quit` ocorreu por volta
de 34,51 s no relógio conservador do ensaio. O observador confirmou todos os
processos próprios encerrados, exit code Electron **0**, aos **35,98 s**.

- Electron principal PID 18036 e seus três filhos terminaram.
- Intermediário 1276, coletor 15904 e ADLX 2296 terminaram cooperativamente.
- Limpeza de coletor/GPU retornou `clean=true`, sem timeout.
- Pipe de métricas e lease de exclusividade GPU ausentes, Win32 código 2; a
  inspeção não criou nem conectou endpoints. Nenhum processo órfão/duplicado.
- Zero erros de renderer registrados; stderr vazio, nenhuma mensagem Crashpad
  nesta sessão. Eventos 1000/1001/4101 relevantes: zero, sem falhas de consulta.
  Isso não resolve as mensagens Crashpad históricas nem prova saúde de todo
  componente interno. A consulta de eventos precisou corrigir uma conversão
  local de data; foi refeita em leitura, sem reabrir o aplicativo.
- Mesmos supervisor HTTPS **5024**, worker **18304** e redirectors, identidade
  completa conferida. Listener LAN único **8776**, TLS 1.3, hostname/certificado/pin
  e GETs status/apps autenticados HTTP 200. **Zero grants e comandos pendentes.**
- Instalação (117 arquivos), perfil de produção (77) e quatro backups anteriores
  byte a byte preservados; banco íntegro, identidades cifradas/esquema/revogações
  preservados. 86 arquivos operacionais protegidos inalterados.
- Run/RunOnce, Inicializar, serviços, tarefas e firewall sem diferenças nesta
  sessão. A observação histórica OneSettings continua inconclusiva; nenhuma
  tarefa foi alterada por este procedimento.
- Nenhum Android, Steam, CS2, WoL ou comando de energia foi acionado. Nenhuma
  correção TLS, Crashpad ou encerramento gracioso do agente foi aplicada.

[Sessão](evidence/session.json), [limpeza](evidence/cleanup.json),
[preservação final](evidence/preservation-final.json) e
[eventos Windows](evidence/windows-events.json).

## Próxima versão instalável — plano, não executado

1. Com autorização separada, preparar **Windows 2.0.0-dev.7**, se a numeração
   continuar disponível, incluindo somente a correção aprovada e regressões.
2. Atualizar metadados/manifestações de integridade do pacote, mantendo appId,
   diretório de instalação, perfil, identidade visual, sensores, bandeja e widget.
3. Reexecutar testes/inspeções de distribuição. Excluir todos os hooks temporários,
   perfis de ensaio, logs, credenciais e arquivos de pareamento do artefato.
   Não modificar runtime ADLX/driver nem agente para incluir esta correção visual.
4. Preparar NSIS e portátil pelo fluxo existente, sem executá-los; registrar
   hashes e ausência de Authenticode se continuar aplicável, sem contornar proteções.
5. Antes de futura instalação autorizada, criar novo backup protegido da dev.6 e
   perfil, conferir hashes e gates do agente/grants. Preservar todos os backups.
6. Instalação assistida e primeira execução exigirão autorizações próprias; não
   transformar a autorização desta sessão em autorização de atualização.

Reversão futura de instalação precisa de plano compatível com dados e backup,
sem limpeza automática. Nesta entrega **não há instalação a reverter**. Nenhum
código funcional mudou; apenas relatório/evidências foram acrescentados. Os
testes 65 de retomada e 43 de prazo foram repetidos antes da abertura e passaram;
a base completa 289 Python / 526 Node / 35 C++ permanece documentada no checkpoint
`f97f0bd`, com fontes correspondentes preservadas. Não se declara que toda essa
suíte foi novamente executada durante a sessão física.

O novo commit documental será informado na entrega. Árvore Git deve terminar
limpa. Reverter esse commit, se necessário, só afeta documentação; não desfaz um
teste já realizado nem requer rollback do Windows. Checkpoints e backups anteriores
permanecem preservados. **Nenhuma nova sessão ou implantação está em andamento.**
