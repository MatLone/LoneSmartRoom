# Monitoramento no Electron — desenvolvimento isolado, 25/10/2026

**Atualização posterior, com autorização própria:** a validação física adicional
confirmou a correção da inicialização e 100% de throughput válido após aquecimento
nos dois volumes. A atividade continua parcialmente indisponível e há ressalvas
de precisão visual. [Novo relatório e evidências](../monitoring-storage-validation-2026-10-25/README.md).
O restante deste documento preserva o resultado histórico da primeira sessão.

**CPU, RAM e capacidade/espaço dos volumes foram recebidos pelo dashboard e widget
em uma única sessão real de 68,100 s.** Electron e coletor encerraram normalmente,
sem resíduos; agente original, perfil instalado e backups preservados.

**Limitação material:** todos os contadores PDH ficaram indisponíveis nessa sessão.
A montagem nova deixou de abrir a consulta PDH. A falha foi corrigida depois, com
três regressões simuladas adicionais, **sem repetir a coleta física**. I/O real e
atividade não estão aprovados para implantação. Não considerar o `ok` dos testes
de janela/transporte uma aprovação de todas as fontes de sensores.

Branch `feature/ui-migration-preview`, preservando `8b5ef78` e ancestrais.
Nenhum instalador, pacote portátil ou aplicativo instalado foi executado/atualizado.

## Arquitetura efetivamente implementada

```text
Provedores básicos Win32 → Collector.start() → MetricCache
                                              ↓ somente leitura
                              Named Pipe Windows de desenvolvimento v1
                                              ↓
                    adaptador Python de leitura (filho do Electron main)
                                              ↓ stdio privado
                           Electron main → preload restrito → renderer
```

O adaptador lança somente seu worker coletor, com Python absoluto resolvido da venv
existente, scripts fixos, `-I -B`, cwd explícito, `shell=False` e sem elevação.
O executável base já disponível é usado diretamente, sem instalar dependências.
O intermediário Python permite atestar ambas as pontas nativamente sem addon FFI
no Electron. Não importa módulos do agente nem recebe identidade do Samsung.

Componentes:

| Fonte | Responsabilidade |
|---|---|
| `monitoring/pipe_protocol.py` | Namespace local fechado, framing e pedido v1 estrito |
| `monitoring/winpipe.py` | ACL, identidade Windows, handles e I/O overlapped cancelável |
| `monitoring/pipe_server.py` | Uma conexão por vez, admissão e leitura apenas do cache |
| `monitoring/development_collector.py` | Composição CPU/RAM/C:/D: e propriedade da consulta PDH; corrigida após a sessão |
| `scripts/monitoring-pipe-{client,server}.py` | Hosts explícitos, lifecycle local limitado e logs sanitizados |
| `apps/windows-ui/monitoring-host.cjs` | Intermediário principal, polling, validação, cache e encerramento do filho |
| `monitoring-model.js` / `monitoring-renderer.js` / `monitoring.css` | Contrato validado, validade temporal e apresentação responsiva |

O host exige aplicativo não empacotado, `--lone-development-review`, flag explícita
de monitoramento e identificador de sessão. Perfil, sessionData, logs e crashDumps
ficam em `.cache/windows-monitoring-development/<id>/`, sem importar dados normais.
O perfil real usado termina em `3b6eac4c4d9dc4dedd5db3dfe516a67e/profile`.
Não há autostart, serviço, tarefa, coleta permanente ou comunicação Electron–agente.

## Segurança do IPC

- Nome `\\.\pipe\LoneSmartRoom.Monitoring.Dev.v1.<id-aleatório>`, local e versionado.
  O sufixo é separação de sessão, **não segredo de autenticação**.
- `FILE_FLAG_FIRST_PIPE_INSTANCE` e um handle retido até o fim impedem ocupar
  novamente o nome entre pedidos. Endpoint ocupado falha fechado.
- `PIPE_REJECT_REMOTE_CLIENTS`, máximo de uma instância/conexão, DACL protegida
  com uma ACE explícita para o SID da conta. Máscara `0x00120183`, sem o direito
  append/criar instância na ACE do cliente. DACL efetivamente lida e conferida.
- Ambas as pontas verificam PID obtido do pipe contra processo cujo handle foi
  mantido desde a criação: horário de criação, imagem, SID, sessão e token sem
  elevação. O servidor também valida o token de impersonação, revertendo antes
  de acessar o serviço. Falha de reversão é fatal para o worker.
- Contrato v1: uint32 big-endian com tamanho + JSON UTF-8; somente `snapshot` e
  `capabilities`, sem parâmetros livres. Requisição até 256 bytes, resposta até
  128 KiB, prazo total de transação 1,5 s, 2 pedidos/s com burst 4.
- ACK fixo de um byte confirma consumo da resposta antes de desconectar, evitando
  descartar bytes ainda no buffer. Não há flush bloqueante sem prazo.
- I/O pendente é cancelado e sua conclusão aguardada antes de liberar memória.
  Reconexão só ao mesmo worker atestado, sem respawn automático.
- EOF do pipe anônimo herdado controla a vida exclusivamente do filho criado por
  esta sessão. Named Pipe não oferece stop, configuração, execução, grant ou energia.
- Renderer com `contextIsolation=true`, `sandbox=true`, `nodeIntegration=false`,
  CSP `connect-src 'none'` e bloqueio de navegação/recursos externos preservados.
  Preload adiciona somente `getMetrics()` e `onMetrics(callback)`, sem expor evento
  Electron, PID, SID, nome de pipe, caminhos ou operação escolhida pelo renderer.
  Origem/frame e número de argumentos são conferidos no processo principal.
- Dados passam por lista fechada de IDs, fontes, unidades, cadências e valores;
  DOM usa texto, sem interpolar valores de sensores em HTML. Leituras inválidas ou
  antigas ficam nulas; último horário válido pode permanecer, sem conservar número
  antigo como se estivesse atualizado. Consulta da UI não dispara amostragem.

O prazo de transação limita o trabalho solicitado; o escoamento de uma operação
cancelada ainda depende de o kernel concluir o cancelamento. Não há garantia de
latência rígida contra travamento do sistema/driver. Os supervisores reportam
timeout/resíduo em vez de matar processos ou declarar sucesso. O ensaio nativo
foi curto e não equivale a auditoria formal ou fuzzing prolongado do transporte.

**Fronteira efetiva:** ACL da conta e relação de processos não isolam malware sob
a mesma conta, injeção, alteração dos fontes ou controle de administrador. O dono
pode modificar DACLs e atacar seus próprios processos. Não há autenticação HMAC/TLS
ou identidade por instalação neste canal. Outra conta real não foi usada nos testes:
há inspeção nativa da ACL, políticas sintéticas e rejeição real de PID inesperado
da mesma conta. Não prometer proteção maior que essa.

Fundamentação: [segurança de Named Pipes](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights),
[identificação do cliente](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid),
[identificação do servidor](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeserverprocessid),
[cancelamento e vida dos buffers](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex).
Plano detalhado: [IPC-PLAN.md](../../monitoring/IPC-PLAN.md).

## Testes e problemas encontrados durante o desenvolvimento

| Grupo final | Resultado |
|---|---:|
| Regressões básicas: contrato, cache, provedores, preservação, WoL, Steam/CS2 com substitutos | 133 testes, zero falhas/erros/skips |
| Segurança/transporte/montagem, sem DLL/processo/rede real | 21 testes, zero falhas/erros/skips |
| Modelo e host Node, subprocessos substitutos | 35 verificações |
| Bandeja, lifecycle, instância única e persistência, mocks | 85 verificações |
| Política, preload e recursos de empacotamento, mocks | 54 verificações |
| Pipe nativo com provedor simulado | 15 verificações |
| Electron real com provedor explicitamente simulado, fontes finais | 19 verificações |
| Única sessão com sensores reais, revisão anterior à correção PDH | 17 verificações de interface/transporte, com limitação I/O registrada |

Contagens de verificações/assertions não são somadas como se fossem casos unittest.
Os 133 testes incluem admissão concorrente de múltiplos clientes, estado antigo,
limites do histórico e mensagens inválidas. Testes novos cobrem direitos nativos,
endpoint ocupado, rejeição de PID/identidade, cancelamento, EOF e reconexões. Não
houve teste de carga, benchmark ou abertura de jogo.

Problemas registrados, sem omitir falhas:

1. O sandbox impediu o cliente nativo com acesso negado. O mesmo teste passou sob
   a conta normal, sem elevação, fora do sandbox. **A ACL não foi ampliada.**
2. Os guards antigos recusaram o preload com dois novos métodos. A revisão fixa
   agora permite exatamente esses métodos de cache e seu hash; nenhuma exceção
   Android/legada foi ampliada. Houve também ajuste do contexto VM dos testes.
3. O bootstrap do teste simulado falhou ao interpretar barras do caminho com
   espaços em `NODE_OPTIONS`; passou após usar caminho com `/`. Não iniciou coleta.
4. A fixture gerava timestamps após seu próprio `generated_at` em uma virada de
   milissegundo; foi corrigida sem afrouxar a validação do contrato.
5. Na sessão física, a montagem não chamou `open_disk_query(volumes)`. Por código,
   `disk_counters()` devolve mapa vazio se a consulta não foi aberta e o provedor
   publica indisponibilidade, exatamente como observado. A composição foi
   centralizada e corrigida em `eb5f835`, com testes de abertura anterior ao start,
   ausência de volumes e liberação na falha de construção. **Não há segunda prova
   real dessa correção.** Ela também não resolve por si só a instabilidade anterior
   de `% Idle Time`, que permanece separada de erros de inicialização.
6. As legendas antigas do gráfico diziam “coleta não iniciada” apesar dos cartões
   ativos. Após a sessão foram ajustadas para “histórico indisponível”; o gráfico
   permanece vazio, sem curva inventada. Regresso visual foi somente com fixtures.

## Única sessão real e frequência observada

Início **05:22:20.040 UTC (02:22:20 em São Paulo)**. Tentativa completa **68,100 s**;
Electron observou 66,519 s, worker 66,162 s, encerrados normalmente. Revisão medida:
`2d172871eb1e7012112871ad4cf9ed73435d4bc0`, antes do ajuste PDH.

Foram 66 respostas, sem timeout/rejeição/reconexão nessa sessão; 65 snapshots da UI
preservados, com **735 tentativas únicas**: 344 válidas, 390 indisponíveis e uma de
aquecimento. Nenhuma leitura stale observada. Não confundir repetição do cache ou
resposta de IPC com nova coleta. Cache final 767 entradas de até 2.520; não houve
teste físico de saturação ou estabilidade prolongada.

| Grupo | Intervalo médio observado | Mínimo / máximo |
|---|---:|---:|
| CPU, RAM e tentativas I/O | 1,0095 s (~0,991 Hz) | 1,003 / 1,016 s |
| Espaço por volume | 60,003 s | duas leituras por volume |
| Polling IPC e atualização da UI | programados a cada 1 s | 66 respostas; idade preservada do coletor |

Intervalos de origem calculados por timestamps das amostras únicas recebidas,
com precisão de milissegundo. O scheduler autônomo foi usado nesta sessão; não foi
reutilizado o runner manual da primeira coleta. Fase de polling/renderer e caches
podem repetir uma leitura; não há garantia de sincronismo exato de 1 Hz.

| Métrica válida | Mínimo | Média | Máximo |
|---|---:|---:|---:|
| CPU total (64 válidas, inicial descartada) | 3,771% | 7,963% | 21,521% |
| RAM utilizada | 11,178 GiB | 11,265 GiB | 11,384 GiB |
| RAM disponível | 4,379 GiB | 4,498 GiB | 4,585 GiB |
| RAM utilizada (%) | 70,913% | 71,468% | 72,218% |

Total RAM utilizável: **15,762783 GiB**. GiB = 2³⁰ bytes, sem pressupor 16 GB exatos.

| Volume | Capacidade | Disponível médio | Ocupação média |
|---|---:|---:|---:|
| C: | 475,605465 GiB | 238,234791 GiB | 49,903028% |
| D: | 447,128902 GiB | 348,684055 GiB | 22,014274% |

Leitura, gravação e atividade de C:/D: tiveram cada uma **65 tentativas
indisponíveis**, sempre nulas. Não há taxa real em bytes/s aprovada nesta sessão.
Ocupação de volume não substitui atividade, bytes/s ou utilização física do SSD.
GPU, VRAM, temperaturas, RPM e FPS não foram coletados. Sem leitura de documentos,
nomes de arquivos pessoais, rótulos ou seriais dos volumes.

## Consumo conjunto e limites da medição

Árvore observada: quatro processos Electron + adaptador Python PID 17024 + coletor
PID 18304; main Electron PID 1296. Consultados por handles somente de leitura e
imagens exatas da sessão; sem controle ou inspeção de memória de processos alheios.

- **CPU média conjunta: 0,414906% da capacidade total.** Soma de 3,390625 s de CPU
  kernel+user de seis processos observados desde a criação / 68,100339 s de parede
  / 12 processadores lógicos × 100. Inclui bootstrap e capturas/renderização de
  testes; processos muito breves anteriores à primeira enumeração podem escapar.
- Pico entre intervalos observados com os seis processos: **4,034%**, não o pico
  instantâneo absoluto. A média integral não implica uso sempre abaixo de 0,5%.
- Soma dos working sets com os seis presentes: mínimo **395,711 MiB**, média
  **425,188 MiB**, máximo **449,988 MiB**. Páginas compartilhadas podem ser contadas
  em mais de um processo: não é memória física exclusiva atribuída ao conjunto.
- Soma de commit privado: média **245,838 MiB**, máximo **285,145 MiB**; não é RAM
  residente privada. Observações de bootstrap com menos processos não entram na
  estatística de memória acima.
- Observador externo de recursos e observador do agente não estão incluídos nesse
  custo. A captura PNG e o harness dentro do Electron estão incluídos.

A referência de 0,5% originalmente era para o coletor isolado. Este resultado do
conjunto ficou abaixo dela em média nesta sessão curta, mas não aprova consumo
contínuo, bateria, jogos, FPS ou comportamento em horas de execução. Não foi gerada
carga artificial e nenhuma configuração Windows/AMD foi alterada.

## Capturas reais e diferença para a revisão final

Arquivos em [captures/](captures/) são PNGs de `BrowserWindow.capturePage()` da
janela Electron **visível e efetivamente executada**, com main/preload reais, não
HTML isolado nem montagem de números. Dashboard 1360×960, widget 440×820 e estreito
350×680, escala de aplicação 100%; sem alterar escala global do Windows.

- [Dashboard — monitoramento](captures/dashboard-monitor.png)
- [Dashboard — origem e timestamp](captures/dashboard-origin.png)
- [Dashboard — volumes](captures/dashboard-storage.png)
- [Widget — monitoramento](captures/widget-monitor.png)
- [Widget — volumes](captures/widget-storage.png)
- [Widget estreito](captures/widget-narrow-storage.png)
- [Controles](captures/dashboard-controls.png)
- [Painel de permissões](captures/permissions-panel.png)

Essas capturas preservam a sessão original e, portanto, mostram I/O ausente e a
legenda de gráfico anterior à correção textual. Não foram retocadas. A revisão
final com legendas corrigidas foi capturada só com fixtures marcadas DEMONSTRAÇÃO,
no cache `simulated/`; não apresentá-la como uma segunda coleta real.
Histórico gráfico, sensores futuros e autorização operacional permanecem ausentes.
O indicador superior de comunicação HTTPS permanece “não integrada”, separado do
coletor local. As três abas, bandeja, X normal e restauração do widget são mantidos.

## Estado final e preservação

- Electron de desenvolvimento saiu com código 0; EOF encerrou seu adaptador e o
  worker. Stop `clean=true`, `stopped=true`, `timed_out=false`. Sem kill/terminate,
  sem reabertura automática e sem processos residuais observados.
- Agente original: supervisor **400**, worker **8680**, redirecionadores **17772** e
  **10996**, mesmos horários, usuário, imagem e argumentos; listener único **8776**.
  Observação periódica: 15 amostras saudáveis em 77,425 s, sem sinais aos processos.
- Helper separado, após a sessão, fez somente GETs `/v2/status` e `/v2/apps`:
  HTTP 200/TLS 1.3, cadeia/hostname/pin validados antes de credenciais; agente online,
  permissões vazias. **Zero grants e zero comandos pendentes**, SQLite quick_check
  OK, identidades/segredos cifrados/revogações/esquema preservados. Não houve nova
  interação física no Samsung; não atribuir a ele esta evidência local.
- Instalação Electron: **77 arquivos**, perfil de produção **76**, ambos iguais
  antes/depois. Backups dev.3/dev.4: **341/75 arquivos incluindo metadados**,
  árvores idênticas. Backup dev.4 também validado contra manifesto conhecido:
  72 arquivos de payload, 27 diretórios, 8.589.376 bytes, ACL privada preservada.
- 263 arquivos operacionais protegidos fora do banco permanecem iguais. Cinco
  fontes Electron no repositório foram alterados com autorização e comparados à
  referência `8b5ef78`; não foram classificados como instalação modificada.
- Android dev.7, WoL, certificados, pareamento, HMAC, executores, HKCU Run, rede,
  firewall, drivers, serviços, tarefas e proteções Windows não foram modificados.
  Não se executou Steam, CS2, energia ou WoL.

Pendências separadas: [TLS](../design/brand/compact-review-2026-10-24/TLS.md),
[encerramento gracioso do agente](../graceful-shutdown-2026-10-24/README.md) e
[diagnóstico de autostart](../agent-recovery-2026-10-25/AUTOSTART-DIAGNOSTIC-PLAN.md).

Na retomada, **09:07–09:08 UTC (06:07–06:08 local)**, foram reconferidos os mesmos
processos/horários, listener único, zero grants, ausência de Electron/monitoramento
e hashes de perfis/backups. GETs autenticados novamente HTTP 200/TLS 1.3.
Leitura estática do ASAR instalado confirmou **2.0.0-dev.4**, nome e ícone oficial;
o ProductVersion numérico do PE é `2.0.0.0`, sem substituir a versão do package.
Uma tentativa anterior dessa inspeção final foi impedida por cota da revisão
automática de permissões e não foi executada; retomou-se após o usuário pedir
continuidade. Nenhuma coleta real foi repetida por causa dessa interrupção.
Recibos adicionais: [agent-final.json](agent-final.json),
[preservation-final.json](preservation-final.json),
[installed-package-final.json](installed-package-final.json),
[authenticated-resumed-final.json](authenticated-resumed-final.json).

## Commits, evidências e reversão

1. `a5e65386f58084c9c171f8311265105538b5c7ab` — transporte nativo e testes.
2. `2d172871eb1e7012112871ad4cf9ed73435d4bc0` — integração Electron; revisão física medida.
3. `eb5f8354d1a5c68434c68ba88af7839904ba6265` — montagem PDH e legendas, testes simulados finais.
4. Relatório e evidências em commit documental posterior.

[metrics-summary.json](metrics-summary.json), [readings.csv](readings.csv),
[resources-summary.json](resources-summary.json), [resources.csv](resources.csv)
contêm valores completos. Os recibos JSON distinguem gate anterior, revisão real e
fontes finais testadas com fixtures. [raw-sha256.json](raw-sha256.json) registra os
originais locais; [artifact-sha256.json](artifact-sha256.json) cobre as evidências
exportadas. Inventários privados, perfis, logs e credenciais não foram para Git.

A sessão real fica preservada em
`.cache/validation/monitoring-electron-2026-10-25/physical/`; seu marcador exclusivo
`physical-attempt.json` não foi apagado. O gate prévio não autoriza executar a
revisão corrigida: fontes mudaram e a tentativa única já foi consumida.

Reversão: como nenhuma instalação ou configuração operacional foi alterada, não há
rollback de perfil/banco a executar. Se necessário, revisar commits inversos na ordem
`eb5f835`, `2d17287`, `a5e6538` em uma branch; conservar relatórios, marker e backups.
Não usar reset destrutivo, apagar caches ou encerrar o agente como reversão.

## Próxima autorização proposta

Antes de implantar: nova sessão física **especificamente autorizada** para a revisão
com abertura PDH, identidade do agente e preservação conferidas novamente, um novo
recibo de tentativa sem apagar o anterior, até 90 s e encerramento normal. Esperado:
CPU/RAM/espaço continuam válidos; throughput aquece e fornece taxas quando suportado;
atividade continua nula onde inválida; sem bypass de validações ou mudanças Windows.

Depois dessa aprovação, preparar uma versão candidata de desenvolvimento para a
futura implantação: pacote novo, versão própria, hashes, backup do perfil e plano
assistido. É preciso projetar lifecycle do coletor implantado e cadência por
visibilidade; o TTL de teste não é uma implementação de coleta permanente.
Não gerar/instalar silenciosamente uma atualização ou conectar o cliente desktop
ao HTTPS do agente. A instalação existente só muda mediante autorização específica.
