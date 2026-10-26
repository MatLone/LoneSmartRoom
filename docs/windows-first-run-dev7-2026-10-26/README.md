# Windows dev.7 — sessão física única, 26/10/2026

**Conclusão: parcialmente homologada.** O aplicativo instalado exibiu medições reais e encerrou cooperativamente, sem componentes ou pipes residuais. A retomada GPU, o Modo Widget e o fluxo da bandeja não foram homologados nesta sessão. Não houve repetição, reinstalação, recompilação ou correção funcional.

## Tempo e desvios do procedimento

| Marco | Tempo desde o lançamento |
|---|---:|
| Lançamento, 13:42:35,335447 BRT / 16:42:35,335447 UTC | 0 s |
| Meta de solicitar Sair | 45 s |
| Solicitação efetiva de fechamento normal pelo X | 76,584 s |
| Electron, coletor, IPC e ADLX encerrados; pipes liberados | 77,213 s |
| Conferências operacionais finais de HTTPS autenticado concluídas | 102,812 s |
| Limite absoluto autorizado | 120 s |

**Não cumpri o marco de saída aos 45 segundos.** O fluxo de observação/captura e o atraso na minha emissão da ação de fechamento consumiram a reserva planejada. A ferramenta não expôs a bandeja como superfície controlável. Usei o X normal da janela, que chama o encerramento cooperativo existente; não selecionei Sair na bandeja. Essa diferença impede considerar o procedimento integralmente aprovado. Não houve encerramento forçado.

Os componentes próprios e a conferência operacional do agente terminaram dentro dos 120 segundos. Auditorias posteriores de arquivos, backup, eventos e documentação ocorreram com o aplicativo já fechado; não são apresentadas como verificações concluídas dentro desse prazo. Nenhuma segunda sessão foi iniciada para preencher as lacunas.

## Evidência real e limites

- [Controles, captura inicial real](01-controls-real.jpg).
- [Controles imediatamente antes da transição de aba](02-controls-before-tab-transition-real.jpg). A captura ainda mostra Controles; não é uma captura de Monitoramento.
- [Monitoramento: árvore de acessibilidade real, sanitizada](03-monitor-accessibility-sanitized.txt). Confirma a aba e suas leituras, mas não substitui uma captura visual.
- [Medições de recursos e processos](resources.json), [resultado estruturado](result.json), [eventos consultados](windows-events.json).

Não há captura do widget, da bandeja, de Atualizando após restauração ou de Indisponível após 10 segundos. Não foram completadas verificações das três abas, painéis, rolagem, redimensionamento ou minimização/restauração. Nenhum cenário foi simulado nesta sessão física.

## Leituras observadas

Valores abaixo são fotografias da interface, não mínimos, médias ou máximos de toda a coleta. A árvore de Monitoramento indicou coletor local conectado e origem Windows + AMD ADLX.

| Indicador | Valor observado |
|---|---:|
| CPU Intel Core i5-12400, utilização | 15,5% na aba Monitoramento; capturas Controles 12,7% e 18,8% |
| RAM utilizada / total / disponível | 9,8 / 15,8 / 6,0 GiB |
| RAM utilizada | 62,2% |
| Radeon RX 6750 XT, utilização | 0% válido |
| GPU / hotspot | 40 / 45 °C |
| VRAM utilizada / total | 984 / 12.272 MB, conforme unidade exibida pelo provedor |
| Clock GPU | 2.483 MHz |
| Potência / ventoinha GPU | 16 W / 0 RPM válidos |
| C: capacidade / disponível / ocupação | 475,6 / 234,2 GiB / 50,8% |
| C: leitura / gravação / atividade PDH | 236,19 / 759,73 KiB/s / 0,2% |
| D: capacidade / disponível / ocupação | 447,1 / 242,1 GiB / 45,9% |
| D: leitura / gravação / atividade PDH | 0 / 0 bytes/s válidos / <0,1% |

A separação entre ocupação, taxas e atividade estava presente. O pequeno percentual positivo de D: não foi apresentado como zero. Temperaturas de CPU/placa-mãe permaneceram sem leitura, sem zero fictício. Não houve jogo, benchmark ou carga artificial.

O timestamp GPU visível foi `2026-10-26T16:43:14.478Z`. As capturas indicam atualização de valores; não foi registrado um fluxo de amostras suficiente para calcular cadências reais dos sensores, idades completas ou quantidades exatas de frames válidos/rejeitados. Não se pode inferir tais contagens a partir do número de amostras do observador de processos.

## Frescor GPU

A inspeção estática do código efetivamente instalado confirmou ingresso ADLX de 1,5 s, expiração ativa de 3 s, inativa de 11 s e indicação persistente após retomada de 10 s. Confirmou também exigência de amostra nova e válida e distinção null/zero/desatualizado.

**A correção Atualizando após restauração não foi validada fisicamente nesta sessão.** Não houve restauração, observação do timeout de 10 s nem indução de falhas. A inspeção estática não é prova de homologação física. Ver [inspeção anterior à abertura](prelaunch-monitoring-static.json); seus campos `applicationExecuted:false` descrevem somente aquela inspeção, não o teste posterior.

## Consumo observado

| Componente | CPU média da máquina | Pico por intervalo (~1 s) | RSS médio | Pico RSS |
|---|---:|---:|---:|---:|
| Electron, quatro processos | 1,6121% | 13,4064% | 385,38 MiB | 410,18 MiB |
| Coletor Python | 0,1332% | 7,0292% | 30,29 MiB | 31,34 MiB |
| Intermediário IPC | 0,0759% | 4,8159% | 23,34 MiB | 24,01 MiB |
| Ponte ADLX | 0,0523% | 2,4728% | 23,53 MiB | 24,62 MiB |
| Total | **1,8735%** | **19,0032%** | **462,54 MiB** | **489,93 MiB** |

CPU calculada por GetProcessTimes, tempos kernel+usuário divididos pelo tempo observado e pelos 12 processadores lógicos. Os picos são intervalares, não instantâneos; a primeira observação de um filho recém-descoberto inclui seu tempo desde a criação. RSS soma working sets e pode contar páginas compartilhadas mais de uma vez. O observador não integra esses totais.

Foram 78 observações de processos; os intervalos posteriores à primeira foram 1,000030–1,000528 s, média 1,000270 s. Isso mede a regularidade do observador, não a frequência de atualização dos sensores. Não há comparação equivalente entre dashboard, widget e bandeja. A referência de desenvolvimento de 0,529% e 454,22 MiB ocorreu em condições diferentes; os números atuais não provam regressão isoladamente.

## Processos e encerramento

- Electron principal PID 3984; filhos 20760, 21080 e 17104.
- IPC 14932; coletor 21884; ADLX 20764.
- Imagem, parentesco, conta/sessão e ausência de elevação conferidos. Um coletor, um intermediário e uma ponte; os filhos Electron são os subprocessos normais, não dashboards duplicados.
- Saída principal 0. Nenhum PID próprio residual. Duas instâncias de pipe observadas durante a operação; zero ao final. O observador foi somente leitura, sem abrir cliente IPC ou controlar processos.

## Erros

O aplicativo criou `debug.log` com 166 bytes e uma mensagem Crashpad `TransactNamedPipe ... (0xE9)`, às 13:42:36,513 BRT, cerca de 1,178 s após abrir. SHA-256: `575113466055a06eb511db8b6613ab2469754ab430c3d1c33bd8d9cbf8eed5f0`.

Não foram encontrados eventos Application 1000/1001 nem System 4101 correspondentes na janela consultada. Não foi observado crash do aplicativo, e a saída foi 0. Isso não resolve a origem do erro Crashpad nem exclui todos os tipos de falha. O arquivo original foi preservado e nenhum mecanismo de crash reporting foi desativado.

## Preservação e estado final

- Windows dev.7 continua instalada e fechada. Os 116 arquivos originais de instalação mantiveram os hashes; apenas o log normal de execução foi acrescentado.
- Perfil: 77 → 78 arquivos; nenhum removido. Um cache de preload acrescentado e 17 arquivos Chromium/cache/LevelDB atualizados normalmente. Preferências de janela permaneceram idênticas. Isso é preservação dos dados com gravações normais de execução, não identidade binária de todo o perfil.
- Backup `Windows-before-dev7-20261026T152048Z`, fora do Git: 194 arquivos, 402.160.249 bytes, hashes íntegros. Manifesto SHA-256 `3edc66d1c8fcdc55efa31ef06ea6697f19e6866bb4406a3f13b40b6c3ea70043`. Pré-verificação de ACL: 238 entradas restritas à conta. Quatro backups anteriores preservados.
- 98 arquivos-fonte, 80 artefatos anteriores e 86 arquivos operacionais protegidos intactos. Banco íntegro; identidades, segredos cifrados, revogações, schema e permissões preservados, sem exposição de conteúdo.
- Supervisor HTTPS 5024, worker 18304 e redirectors 19996/20352 mantiveram imagens, argumentos, parentesco e horários de criação esperados. Listener único 8776 pertence ao worker original.
- TLS 1.3, certificado/hostname/pin validados antes do uso de credenciais; GET autenticados `/v2/status` e `/v2/apps` HTTP 200. **Zero grants e zero comandos pendentes.** Não houve nova confirmação física do Samsung nesta sessão.
- HKCU Run, pasta Inicializar, serviços, tarefas e firewall sem diferenças nas comparações realizadas. Nenhuma alteração à tarefa OneSettings; a observação histórica inconclusiva continua separada.
- Android, certificados, credenciais, agente, executores, backups e DLL ADLX oficial preservados. Nenhuma ação Steam, CS2, WoL ou energia. Pendências TLS, Crashpad e encerramento gracioso não foram corrigidas.

## Próximo teste e reversão

É necessária nova autorização para uma sessão complementar. Preparar antes da abertura um caminho GUI efetivamente operável para Sair na bandeja; se isso não for possível, não iniciar prometendo validá-lo. Usar plano de ações curtas, cessar novas observações em T+30 s e solicitar saída até T+45 s, reservando até T+120 s somente para confirmar encerramento e agente. Priorizar widget, minimizar/restaurar, Atualizando até amostra nova, bandeja e Sair; registrar o que não ocorrer naturalmente, sem forçar falhas.

Não há mudança funcional a reverter nesta entrega. O commit é documental e pode ser revertido separadamente, preservando checkpoint e evidências. Nenhuma restauração de produção foi executada. A reversão da instalação permanece condicionada a autorização própria e ao backup dev.6 existente; não presumir restauração destrutiva ou downgrade automático.

O estado final operacional é aplicativo fechado, componentes próprios encerrados, agente HTTPS original ativo e zero grants. A árvore Git deve conter somente este registro documental após o commit; nenhuma nova build foi produzida.
