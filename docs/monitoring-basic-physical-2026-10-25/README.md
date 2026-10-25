# Primeira sessão física de monitoramento básico — 25/10/2026

Uma única sessão autorizada foi concluída, sem repetição: **80,0009 s de coleta**,
**80,4144 s para a tentativa completa**, dentro do máximo de 90 s. O coletor PID
16708 encerrou normalmente, sem threads ou processos residuais. O agente HTTPS
permaneceu ativo; supervisor 400, worker 8680 e listener único 8776 preservados.

Branch `feature/ui-migration-preview`, partindo de `ed4c3a0`; preservados `33765ab`,
`d5eeeb6` e os checkpoints anteriores. Esta entrega altera somente documentação e
evidências. Não altera provedores, executores, agente, interfaces ou configurações.

## Autorização e pré-verificação

- Janela real: **04:36:33.531–04:37:53.532 UTC**, ou **01:36:33–01:37:53 em
  São Paulo (UTC−3)**, em 25/10/2026. Não houve coleta anterior nesta autorização.
- Identidade dos quatro processos da árvore validada por imagem, argumentos,
  proprietário, parentesco e horário de criação, comparada à recuperação aprovada.
  Nenhum processo foi sinalizado, atualizado, encerrado ou reiniciado.
- Porta 8776 com um listener pertencente ao worker esperado. Zero grants e zero
  comandos pendentes; banco consultado em modo somente leitura.
- Recibo de **133 testes aprovados, zero falhas e zero erros**, conferido contra
  SHA-256 dos fontes/testes atuais. Não foi necessário reexecutar a suíte: não houve
  mudança de código desde a execução aprovada. Isso não representa uma nova rodada
  dos 133 testes. A integridade das evidências físicas foi validada separadamente.
- Python 3.13.3 da venv existente, biblioteca padrão/Win32, token sem elevação.
  Nenhuma instalação de dependência, driver ou ferramenta.
- 268 arquivos protegidos fora do banco coincidiram com a referência; integridade
  lógica do banco, identidades, segredos cifrados, permissões e esquema preservados.

Evidência: [preflight.json](preflight.json), [agent-before.json](agent-before.json).

## Valores reais

Médias aritméticas calculadas somente com **leituras únicas válidas**, sem contar
repetições do cache. GiB = 2³⁰ bytes; MiB = 2²⁰ bytes. Valores completos, unidades,
fontes, contagens e timestamps estão em [metrics-summary.json](metrics-summary.json)
e [readings.csv](readings.csv).

| Métrica | Mínimo | Média | Máximo | Leituras válidas |
|---|---:|---:|---:|---:|
| CPU total | 2,344% | 6,863% | 25,065% | 79 |
| RAM utilizada | 10,972 GiB | 11,036 GiB | 11,154 GiB | 79 |
| RAM disponível | 4,609 GiB | 4,727 GiB | 4,791 GiB | 79 |
| RAM utilizada (%) | 69,605% | 70,014% | 70,759% | 79 |

RAM total utilizável informada pelo Windows: **16.925.159.424 bytes
(15,763 GiB)**, constante. Não foi preenchida a partir dos 16 GB nominais.
CPU utiliza deltas de `GetSystemTimes`, descontando idle; a primeira amostra foi
`warming_up`, valor nulo, excluída da estatística. RAM deriva de um único lote
`GlobalMemoryStatusEx`, com utilizada + disponível = total validado.

| Volume | Capacidade | Disponível mínimo / médio / máximo | Ocupação mínima / média / máxima |
|---|---:|---:|---:|
| C: | 475,605 GiB | 238,325256 / 238,325449 / 238,325642 GiB | 49,884531 / 49,884571 / 49,884612% |
| D: | 447,129 GiB | 348,684055 GiB, constante | 22,014274%, constante |

Foram **duas leituras de espaço por volume**, separadas por aproximadamente 60 s.
Capacidade usa `GetDiskSpaceInformationW`; ocupação é alocação utilizada/total
físico, distinta de espaço disponível à conta. Nesta sessão, disponível e livre
físico coincidiram. C: utilizado médio 237,253748 GiB; D: 98,432182 GiB.
Só foram enumeradas letras de volumes locais fixos C: e D:, sem varrer arquivos,
ler documentos, rótulos ou seriais. Volumes sem letra não estão cobertos.

| Contador PDH LogicalDisk | Mínimo (bytes/s) | Média (bytes/s) | Máximo (bytes/s) | Válidas |
|---|---:|---:|---:|---:|
| C: leitura | 0 | 20.996,33 | 376.791,01 | 78 |
| C: gravação | 0 | 397.194,34 | 2.133.139,71 | 78 |
| D: leitura | 0 | 0 | 0 | 78 |
| D: gravação | 0 | 0 | 0 | 78 |

Os zeros de throughput D: são **leituras válidas**, não preenchimento de ausência.
Cada contador teve uma amostra inicial de aquecimento. Taxa em bytes/s, ocupação
de espaço e atividade temporal são métricas separadas.

| Atividade do volume, 100 − % Idle Time | Mínimo | Média válida | Máximo | Válidas / aquecimento / indisponíveis |
|---|---:|---:|---:|---:|
| C: | 0% | 0,063596% | 0,466539% | 70 / 1 / 8 |
| D: | 0,000410% | 0,012883% | 0,074321% | 40 / 1 / 38 |

**A atividade PDH apresentou indisponibilidades relevantes, especialmente em D:.**
Essas médias descrevem somente o subconjunto válido e não toda a janela. A fonte
mede atividade do volume lógico, não utilização física do SSD/controlador. Não usa
`% Disk Time` nem throughput como substituto. Os 46 resultados indisponíveis
permaneceram nulos; não foram limitados artificialmente nem convertidos em zero.

## Cadência e qualidade

| Grupo | Intervalo mínimo | Intervalo médio | Intervalo máximo |
|---|---:|---:|---:|
| CPU | 1,000027 s | 1,000443 s | 1,002720 s |
| RAM | 1,000063 s | 1,013267 s | 2,000277 s |
| I/O e atividade | 1,000024 s | 1,013264 s | 2,000233 s |
| Espaço C: | 60,025673 s | 60,025673 s | 60,025673 s |
| Espaço D: | 60,025707 s | 60,025707 s | 60,025707 s |

Às 04:36:51.538 UTC, RAM e I/O reutilizaram uma leitura do segundo anterior,
respectivamente com idade 0,999941 s e 0,999848 s. O runner físico chama `step()`
aproximadamente a cada segundo, enquanto cada provedor exige intervalo próprio
integral. **Inferência fortemente sustentada:** o pequeno desfasamento entre esses
relógios adiou a próxima leitura até o tick seguinte, produzindo a lacuna de 2 s.
Não foi exercitado o agendamento autônomo `Collector.start()` com sensores reais;
não se pode atribuir a ele o mesmo comportamento sem teste específico. Nenhuma
correção ou repetição física foi feita. Revisar o acionamento por prazo individual
em desenvolvimento e testar com relógios simulados antes de nova validação física.

A causa exata das indisponibilidades PDH é **inconclusiva**: os dados brutos e
`CStatus` individuais não foram preservados. Pelo código, as causas possíveis são
status inválido, retorno ausente/não finito ou atividade fora de 0–100. Arredondamento
de idle acima de 100 é apenas hipótese. Throughput permaneceu válido após
aquecimento e não houve diagnóstico de exceção da consulta inteira, o que não
comprova qual ramo rejeitou a atividade. Não alterar contadores do Windows nem
relaxar validação para mascarar a falha. Manter atividade condicional/indisponível
na futura interface até qualificação da fonte.

Foram 80 snapshots de 21 métricas, 1.680 aparições e **890 tentativas únicas**:
837 disponíveis, 7 de aquecimento e 46 indisponíveis. Timestamps ordenados dentro
da sessão; nenhuma amostra desatualizada nos snapshots. Valores inválidos são
nulos, sem interpolação. Cache final **911 de 2.520 entradas permitidas**, incluindo
21 registros iniciais não coletados. A sessão não saturou o histórico; limites de
retenção foram cobertos pelos testes simulados, não por uma execução física longa.

## Custo do próprio coletor

- CPU de processo: **0,078125 s** durante **80,000951 s**, normalizada pelos
  **12 processadores lógicos**: `CPU_s / tempo_s / 12 × 100` = **0,008138% da
  capacidade total**, média. A referência de planejamento <0,5% foi atendida nesta
  sessão; não constitui garantia para todas as cargas ou execuções longas.
- RAM residente (`WorkingSetSize`, 80 observações): mínimo **28,734 MiB**,
  média **29,328 MiB**, máximo **29,891 MiB**. Commit privado é registrado
  separadamente no CSV; não equivale a memória residente privada.
- Processamento de um ciclo: mínimo **0,256 ms**, média **0,720 ms**, máximo
  **2,693 ms**, sem incluir a espera normal entre ciclos.
- Janela de recursos abrange amostragem, snapshots/cache e espera do próprio
  processo. Não inclui todo o bootstrap nem a serialização final do relatório.
  Não mede custo do observador externo, agente ou restante do Windows.

Não houve carga artificial, benchmark, jogo ou teste de FPS/latência. O consumo
medido não comprova ausência de impacto em jogos. Sem erro de leitura por exceção
ou timeout; único diagnóstico do coletor foi `collector_stopped`. As rejeições de
atividade PDH continuam sendo limitações e não são ocultadas por esse diagnóstico.

## Encerramento e preservação

O stop cooperativo retornou `stopped=true`, `clean=true`, `timed_out=false`;
nenhuma thread de monitoramento permaneceu. A inspeção posterior encontrou zero
processos do monitoramento. Nenhum agente foi parado para terminar o teste.

Supervisor PID **400** e worker **8680**, incluindo seus dois redirecionadores de
venv, mantiveram imagem, argumentos, usuário, parentesco e horário de criação.
O observador independente registrou 15 verificações saudáveis; inspeções anteriores
e posteriores também confirmaram o listener único 8776 no worker esperado. Essas
verificações periódicas não são prova contínua em resolução subsegundo.
Conferência final às **04:51:05 UTC** manteve as mesmas identidades, um listener
8776 e zero processos de monitoramento; banco íntegro e grants zerados também
foram reconferidos. Evidência de processos: [agent-final.json](agent-final.json).

Após o término do coletor, um **helper separado** fez somente GETs autenticados
`/v2/status` e `/v2/apps`: ambos HTTP 200 em **TLS 1.3**, hostname, cadeia e pin
verificados antes do envio de credencial. Agente online, lista de permissões vazia.
O coletor não acessou rede, agente ou IPC. Não houve nova checagem física da tela
do Samsung nesta sessão; a confirmação anterior de Conectado permanece histórica,
e a evidência atual é a consulta local autenticada sem novo pareamento.

Banco `quick_check` OK, **zero grants**, zero comandos pendentes; identidades,
segredos cifrados, revogações, permissões e esquema sem alteração lógica. Os 268
arquivos protegidos permaneceram iguais. Não se compara o hash bruto do SQLite
como se logs legítimos da consulta autenticada fossem corrupção do banco.
Hashes de HKCU Run e regras relevantes de firewall permaneceram iguais. Backups
e checkpoints anteriores preservados; nenhum procedimento de recuperação executado.

Android dev.7 e Electron dev.4 instalados não foram atualizados ou executados.
Não houve novos certificados, credenciais, grants, drivers, serviços, tarefas,
autostart, alterações de Registro/rede, Steam, CS2, WoL ou comandos de energia.
TLS excessivo/ambíguo e encerramento gracioso continuam pendências separadas;
o launcher legado permanece ativo e não foi sinalizado.

## Evidências e integridade

- [metrics-summary.json](metrics-summary.json): estatísticas completas, fontes,
  intervalos, estado final, custo e duração, sem duplicar snapshots de baixa cadência.
- [readings.csv](readings.csv): 890 tentativas únicas com UTC, origem, unidade,
  valor, estado e validade; campo vazio representa valor nulo, não zero.
- [collector-resources.csv](collector-resources.csv): 80 ciclos, CPU do processo,
  memória, tempos e cache.
- [validation.json](validation.json): coerência de valores, timestamps, cache,
  preservação e ausência de resíduos.
- [agent-observation.json](agent-observation.json), [agent-after.json](agent-after.json),
  [authenticated-status.json](authenticated-status.json): preservação e conexão.
- [artifact-sha256.json](artifact-sha256.json): hashes dos JSON/CSV exportados.
  Este README e o manifesto não se incluem no próprio manifesto.

Snapshots completos preservados no cache local ignorado pelo Git:
`.cache/validation/monitoring-basic-2026-10-25/physical-session.json`.
SHA-256: `cbc6644ca9ce4a70340988c026ce77a1850e8ba3163b92c4cba1c7395a128e71`.
O marcador exclusivo `physical-session-started.json` foi mantido para impedir
repetição acidental. Logs auxiliares e digests privados não foram adicionados ao Git;
os arquivos exportados não contêm tokens, chaves ou conteúdo de arquivos pessoais.

## Próxima fase proposta e reversão

Solicitar autorização para implementar **transporte IPC local protegido e primeiros
indicadores em Electron de desenvolvimento isolado**, sem substituir a instalação:
CPU, RAM e capacidade/espaço primeiro; taxas I/O separadas; atividade PDH conservando
indisponibilidade. Named pipe sem TCP, ACL restrita à conta/sessão, bloqueio remoto,
verificação de identidade das duas pontas pelo Windows, limites de mensagens e
requisições, parser estrito e acesso somente ao cache. Processo principal Electron
faz operações privilegiadas; preload oferece apenas leituras fechadas, com
`contextIsolation=true` e `nodeIntegration=false`. Falha fechada e dados antigos
explicitamente sinalizados; nenhuma API genérica de comandos.

Plano e fronteira existentes em [IPC-PLAN.md](../../monitoring/IPC-PLAN.md).
Essa proposta não conecta um novo cliente ao agente HTTPS nem reutiliza credenciais
do Samsung. A pendência TLS continua bloqueando integração HTTPS operacional de
novos clientes. Coleta contínua, nova sessão física ou atualização instalada exigem
escopo próprio; não estão automaticamente autorizadas por este resultado.

Reversão desta entrega é documental: retirar apenas os relatórios adicionados e
os links correspondentes, por commit inverso revisado. Não executar reset destrutivo,
rollback do agente ou apagar backups/cache/marcador de execução. O coletor já está
parado; o agente deve continuar ativo. Implementação básica permanece no commit
`33765ab`, sem alteração de código nesta sessão.
