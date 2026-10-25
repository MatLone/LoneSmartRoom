# Observações dev.5 — auditoria offline separada — 25/10/2026

Aprovação funcional da primeira sessão física mantida. Base: evidências já registradas
em `docs/windows-first-run-dev5-2026-10-25/evidence/`. Não houve nova execução do
Electron, reprodução de Crashpad ou medição física nesta auditoria.

## CPU: fatos e alcance

Na sessão anterior de 179,119 s, médias normalizadas pela CPU total da máquina:

| Componente | CPU média | RSS média |
|---|---:|---:|
| Coletor | 0,06397% | 29,85 MiB |
| Intermediário IPC | 0,04434% | 23,40 MiB |
| Grupo Electron | 2,04270% | 383,95 MiB |
| Soma | 2,15101% | 437,20 MiB |

Electron representa **94,9645% da soma de CPU desses componentes**. Não significa
95% de utilização do PC. Quatro processos Electron foram agrupados; não há perfil
por função main/renderer/GPU/utility para atribuir esse consumo a um deles.
RSS somada pode contar páginas compartilhadas mais de uma vez.

`scripts/audit-windows-dev5-observations.py` reanalisa os registros sem acessar sensores.
Usa apenas intervalos de amostras inteiramente contidos entre marcadores de interface:

| Janela aproximada desde início | CPU média do grupo Electron | Limitação |
|---|---:|---|
| 0–11,469 s: início/widget inicial | 1,9642% | Inclui inicialização |
| 11,469–105,077 s: dashboard observado | 2,1180% | Inclui navegação e capturas |
| 105,077–156,085 s: widget observado | 2,1711% | Inclui interação/capturas |
| 156,085–179,119 s: após ocultar | 1,3845% | Inclui restauração manual e saída |

Essas janelas **não são um trace de visibilidade**, fases de repouso controladas ou
amostras equivalentes para comparação. Não foi medida inatividade isolada. Não há
base para afirmar regressão contra dev.4 ou atribuir diferenças somente ao modo.

## Achados estáticos e testes de renderização

1. `monitoring-host.cjs` consulta o bridge em intervalo de 1 s e publica estado.
2. `monitoring-renderer.js` chama `refresh()` ao receber atualização e também por
   timer independente de 1 s, para atualizar idade/validade mesmo sem nova resposta.
3. `refresh()` reatribui textos, metadados e barras de CPU/RAM/discos e aviso de
   histórico. Faz trabalho inclusive para os cartões de outras abas/modos presentes
   no DOM. Não foi encontrado controle próprio de visibilidade nesse renderer.
4. O teste com DOM substituto observou **28 chamadas aos setters instrumentados**
   por push e mais 28 por timer sem amostra nova. Não conta todas as propriedades,
   layouts, paints ou milissegundos de CPU. A repetição é evidência de trabalho de
   atualização, não demonstra a causa dominante dos 2,04% do grupo Electron.
5. O mock também não suprime esse trabalho quando marcado hidden/widget. Ele não
   modela agendamento/throttling do Chromium. O comportamento real pode diferir.
6. O ciclo atual não comunica visibilidade ao `set_active` do coletor. O polling Node
   não é controlado automaticamente pelo throttle do timer renderer.

A documentação distingue ocultação/minimização de simples oclusão por outra janela;
`backgroundThrottling` é habilitado por padrão. Essas regras não fornecem, sozinhas,
uma medição de consumo em bandeja. Ver [BrowserWindow/Page Visibility, Electron](https://www.electronjs.org/docs/latest/api/browser-window#page-visibility).

Hipótese preliminar: combinação de múltiplos processos Chromium, atualização do
mesmo estado por dois caminhos e escrita recorrente do DOM pode contribuir. A parcela
de cada fator permanece desconhecida. Não se atribui ao ADLX, que não foi carregado.

Proposta futura de menor risco: instrumentar por processo/fase em uma sessão aprovada,
separando dashboard, widget e bandeja sem interações. Depois avaliar coalescência de
refresh, atualização somente de propriedades alteradas e propagação explícita de
atividade. Preservar envelhecimento/stale e recuperação mesmo quando oculto; não
eliminar indiscriminadamente o timer de validade. **Nenhuma otimização foi aplicada.**

## Crashpad: duas falhas reais de comunicação, crash não demonstrado

Os logs existentes contêm `TransactNamedPipe` em
`crashpad/util/win/registration_protocol_win.cc:136`, código `0xE9`, indicando que
não havia processo na outra extremidade do pipe na transação.

| Horário local (UTC−3), 25/10/2026 | Desde abertura | Até fim da sessão |
|---|---:|---:|
| 08:06:53,489 | 1,125 s | 177,993 s |
| 08:08:53,484 | 121,120 s | 57,998 s |

Primeira mensagem correlacionada temporalmente com startup. Segunda ocorreu durante
a sessão, cerca de 58 s antes do fim; **não é evidência de erro provocado pela saída**.
Distância entre mensagens: 119,995 s. Esse intervalo isolado não comprova timer/retry
de 120 s nem identifica o processo/handler causador.

No código oficial atual, falha nessa transação faz `SendToCrashHandlerServer` retornar
false. Isso indica falha de comunicação de registro com o handler; não demonstra uma
exceção fatal da aplicação. A revisão `main` consultada não foi comprovada idêntica
ao Chromium embarcado nesta build. Ver [fonte Crashpad](https://chromium.googlesource.com/crashpad/crashpad/+/refs/heads/main/util/win/registration_protocol_win.cc).

A sessão permaneceu funcional e encerrou normalmente, e o relatório existente não
encontrou eventos correlatos de Application Error/WER/hang 1000/1001/1002 do app.
Não há evidência de crash do Electron nesses registros. Tampouco é correto declarar
o erro inofensivo ou o crash reporting saudável: registro/captura futura pode ter
sido afetado, e faltam identidade/lifetime do handler e detalhe de sua inicialização.

O pipe citado pertence ao Crashpad; não há evidência que o associe ao Named Pipe
de métricas, ao agente HTTPS, à AMD ou a perda do IPC de sensores. Nenhuma captura
de memória, upload, dump novo, repetição física ou desativação do reporter ocorreu.

Próxima investigação proposta: mapear a revisão exata de Electron/Chromium e seu
bootstrap de reporter; se autorizado posteriormente, registrar somente metadados de
processos/horários numa sessão isolada. Não induzir crash, habilitar uploads ou
desativar segurança. Não há correção comprovada a aplicar nesta fase.

## Testes simulados adicionais — 23 verificações

`tests/monitoring-maintenance.cjs` reutiliza os fixtures de host/janela e um DOM
substituto, sem chamar Electron, sensores ou Named Pipe real:

- timeout/perda de IPC → desconectado; falha não mata worker;
- resposta nova válida → reconexão; valores expirados → null/stale;
- preservação do último horário válido; mensagens inválidas/rate limit;
- outra recuperação sem reinício; encerramento normal dos substitutos;
- redimensionamento widget e persistência; coordenadas fora da tela limitadas;
- minimizar normal continua minimização de barra de tarefas;
- restauração da mesma janela, sem ativar preferência automática de bandeja;
- fechamento do substituto e formatação de ausência versus zero;
- detecção da repetição de setters DOM descrita acima.

Rejeitar origem ADLX no antigo slot CPU reforça a allowlist; não se amplia o preload.
Testes de janela são de lógica com substitutos, **não** nova aprovação visual ou
prova de comportamento do compositor Windows. Demais suítes estão documentadas no
[relatório ADLX](../adlx-preparation-2026-10-25/README.md).

## Preservação

Nenhum arquivo de produção Electron/Android/agente foi alterado. Agente e HTTPS
verificados somente em leitura; zero grants. Perfis, instalação e backups comparados
por SHA-256. Não houve build, instalação, nova sessão física, jogo, WoL, energia,
alteração de driver, HKCU Run ou firewall. Pendências TLS e encerramento gracioso
permanecem separadas. Evidências finais sanitizadas no relatório ADLX.
