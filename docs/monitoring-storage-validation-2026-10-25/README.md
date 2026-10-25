# Validação física adicional de armazenamento — 25/10/2026

**A correção de inicialização PDH foi validada fisicamente.** Leitura e gravação
de C:/D: tiveram **100% de amostras válidas após o aquecimento**. A atividade
permanece parcialmente indisponível: C: 95,24%, D: 52,38% após o aquecimento.
Nenhum fallback foi implementado, nenhum valor ausente virou zero e não houve
segunda tentativa nesta autorização.

Uma sessão de **67,1737 s**, incluindo bootstrap e encerramento, foi executada em
Electron de desenvolvimento. Não foi instalada ou atualizada uma versão Windows.
Agente legado, perfil de produção, backups e fontes funcionais permanecem intactos.

## Pré-verificação e escopo

- Branch `feature/ui-migration-preview`; preservados `a5e6538`, `2d17287`, `eb5f835`,
  `d79724e` e ancestrais. O código funcional medido continua o de `eb5f835`.
- Recibos dos **154 testes Python aprovados** (133 básicos + 21 transporte/montagem)
  comparados por SHA-256 aos arquivos atuais: idênticos, sem necessidade de nova
  execução. Foram executados quatro testes puros adicionais da contabilização de
  recursos por componente e verificações de sintaxe do novo bootstrap de teste.
- A composição atual chama `open_disk_query(volumes)` antes do start do coletor;
  propriedade e fechamento da consulta já cobertos nas três regressões da correção.
- Identidade do agente conferida por usuário, imagem, argumentos, parentesco e
  horário de criação; supervisor 400/worker 8680, não só comparação de números.
  Listener único 8776, zero grants, zero comandos pendentes e GET autenticado OK.
- Sem Electron instalado/de desenvolvimento ou monitoramento residual antes do
  teste. Instalação, perfil e dois backups inventariados novamente por hash.
- Instrumentação separada: `3abd308` adiciona somente observador/contabilização e
  bootstrap de validação. Não modifica main/preload, coletor, transporte ou sensores.
- Novo ledger `.cache/validation/monitoring-storage-2026-10-25/physical-attempt.json`,
  aberto exclusivamente antes do lançamento. O marker da sessão anterior foi mantido.

Uma falha de importação no verificador de preparação (`-I` com stdin sem raiz no
`sys.path`) foi corrigida antes de lançar o Electron. Nenhuma coleta havia começado;
fontes aprovados e configuração do sistema não foram alterados.

## Sessão, fonte e inicialização

Início **09:21:32.370 UTC / 06:21:32.370 em São Paulo**. Worker observado por
64,985 s, Electron por 65,459 s, tentativa completa por **67,174 s**, abaixo de 90 s.
Fim do worker: 09:22:38.996 UTC. Não houve benchmark, escrita intensiva ou carga
artificial. Capturas, perfil de teste e arquivos de evidência produzem I/O normal
do próprio ensaio e estão incluídos no contexto das leituras, sem atribuição por arquivo.

PID coletor **9872**, intermediário **15272**, Electron principal **17588**, com
três processos Electron auxiliares. Todos pertencem à conta/sessão esperada, com
imagem exata e token sem elevação. Nenhum processo operacional foi controlado.

Fonte de I/O e atividade: `win32.pdh.logicaldisk`. A implementação associa cada
root autorizado aos caminhos fechados `\LogicalDisk(C:)\...` e
`\LogicalDisk(D:)\...`, com `Disk Read Bytes/sec`, `Disk Write Bytes/sec` e
`% Idle Time`. Chaves e mapeamento foram revisados no código íntegro; identificadores
`storage.c.*`/`storage.d.*` e unidades foram conservados até as linhas da interface.
Nenhum número de disco físico foi presumido a partir da letra do volume.

Houve exatamente **uma amostra inicial `warming_up` por contador de I/O/atividade**,
com valor nulo. A existência de taxas válidas posteriores, com o setup revisado e
fonte intacta, comprova o funcionamento da consulta que faltou no ensaio anterior.
Não houve inspeção extra de handles PDH nem segunda consulta de sensores.
Contadores de taxa dependem de duas amostras e intervalo adequado, conforme a
[documentação Microsoft de coleta PDH](https://learn.microsoft.com/en-us/windows/win32/perfctrs/collecting-performance-data).

## Disponibilidade e valores reais

Foram **64 tentativas únicas por contador**. Percentuais incluem e excluem o
aquecimento explicitamente; snapshots repetidos do cache não contam como nova leitura.

| Volume / métrica | Válidas | Aquecimento | Indisponíveis | Válidas / todas | Válidas após aquecimento |
|---|---:|---:|---:|---:|---:|
| C: leitura | 63 | 1 | 0 | 98,44% | 100% |
| C: gravação | 63 | 1 | 0 | 98,44% | 100% |
| C: atividade | 60 | 1 | 3 | 93,75% | 95,24% |
| D: leitura | 63 | 1 | 0 | 98,44% | 100% |
| D: gravação | 63 | 1 | 0 | 98,44% | 100% |
| D: atividade | 33 | 1 | 30 | 51,56% | 52,38% |

| Métrica | Mínimo válido | Média válida | Máximo válido |
|---|---:|---:|---:|
| C: leitura, bytes/s | 0 | 58.727,59 | 1.637.072,91 |
| C: gravação, bytes/s | 16.239,11 | 528.827,97 | 3.518.485,06 |
| C: atividade do volume | 0,004302% | 0,102838% | 0,878129% |
| D: leitura, bytes/s | 0 | 0 | 0 |
| D: gravação, bytes/s | 0 | 0 | 0 |
| D: atividade do volume | 0,0000496% | 0,022327% | 0,073916% |

Médias de atividade descrevem **somente o subconjunto válido**, não toda a janela.
No C: leitura houve 32 zeros válidos; no D: leitura e gravação tiveram cada uma
63 zeros válidos. São **158 zeros reais** nessas taxas, separados dos 33 resultados
indisponíveis de atividade e do aquecimento. Não houve tráfego não zero de D:
exercitado; não foi gerada carga para forçá-lo.

Intervalo de atualização de origem das tentativas I/O: mínimo **1,001 s**, média
**1,00946 s**, máximo **1,016 s**, aproximadamente 0,991 Hz. CPU/RAM seguiram a
cadência básica e permaneceram válidas nas quatro conferências visuais; capacidade
de C:/D: foi recebida com a cadência de 60 s. Valores completos de todas as métricas
e intervalos em [metrics-summary.json](metrics-summary.json).

O transporte retornou 65 respostas, sem timeout, rejeição ou reconexão; foram
preservados 67 eventos de estado, incluindo conexão/stop. Há **724 tentativas únicas**:
684 válidas, 7 de aquecimento e 33 indisponíveis. **Nenhuma stale observada**.
Cache final 745 entradas; limite não saturado. Não houve exceção de provedor ou
erro de transporte nos diagnósticos. A indisponibilidade de uma leitura não foi
rotulada como exceção nem a ausência de exceção foi tratada como disponibilidade total.

## O que foi e não foi comprovado sobre precisão

**Comprovado neste ensaio:** consulta inicializada, aquecimento, identificação de
fonte/volume, unidades, cadência, integração cache→IPC→UI, valores exatos no contrato,
zeros válidos e nulos distintos. Dashboard e widget corresponderam ao mesmo contrato
de leitura, com amostras de instantes diferentes quando a tela mudou de modo.

**Não comprovado:** calibração absoluta contra instrumento independente, precisão
sob carga sustentada, I/O não zero do D: e correspondência com utilização física
de cada SSD. Não se executou contador/benchmark externo para comparar números.
Atividade vem de `100 − % Idle Time` do volume lógico; não é ocupação de espaço,
bytes/s nem `% Disk Time`. Não se converte uma métrica na outra.

### Indisponibilidade residual da atividade

Leitura/gravação permaneceram válidas após aquecimento enquanto somente atividade
falhou. Não há evidência de repetição da falta de inicialização ou falha global
da consulta. O C: recuperou as três indisponibilidades sem novo aquecimento; o D:
também teve várias recuperações desse tipo. **Inferência:** o padrão é compatível
com rejeição do valor formatado/da faixa após atualizar a base, em vez de perda da
consulta inteira. Isso não identifica o retorno exato ou uma causa no Windows.

Valores brutos de idle, CStatus e retorno formatado individuais não foram retidos.
Pelo código, retorno ausente/não finito ou complemento fora de 0–100 é rejeitado.
Idle ligeiramente acima de 100 é hipótese, **não causa comprovada**. Não há evidência
para atribuir o problema a SSD, driver AMD, agente HTTPS ou falta de permissão.
Não houve reparo/ativação de contadores, clamp, troca de fonte ou fallback.

## Dashboard, widget e limites de apresentação

**28 verificações reais**: perfil separado, main/preload reais, sandbox e isolamento,
CPU/RAM/capacidade funcionando, quatro fases de comparação das linhas do DOM com
o snapshot IPC, unidades/origens/validade, zeros numéricos, nulos como `—`, ausência
de overflow horizontal, ações operacionais bloqueadas e ausência de crash/erro.
Nenhuma navegação, bandeja ou identidade visual funcional foi modificada.

Capturas reais, sem retoque, da janela visível Electron de desenvolvimento:

- [Dashboard e indicadores](captures/dashboard-monitor.png)
- [Volumes no dashboard](captures/dashboard-storage.png)
- [Origem e horários](captures/dashboard-storage-origin.png)
- [Widget](captures/widget-monitor.png)
- [Volumes no widget — C:](captures/widget-storage-c.png)
- [Volumes no widget — D:](captures/widget-storage-d.png)
- [Widget estreito](captures/widget-narrow.png)
- [Dashboard ao fim](captures/dashboard-storage-final.png)

Dashboard 1360×960, widget 440×820 e estreito 350×680, escala de aplicação 100%.
As imagens de volumes são capturas de posições de rolagem; conteúdo acima/abaixo
do viewport permanece acessível. Não houve medição de latência/FPS ou teste de jogos.
O indicador HTTPS superior continua não integrado, separado do coletor conectado.

**Risco de precisão visual identificado:** percentuais têm uma casa decimal.
23 das 60 atividades válidas C: e 29 das 33 D: eram positivas, mas o formatador
mostrou `0%` por arredondamento. No contrato e CSV continuaram positivas — não são
os zeros reais de I/O. Isso limita a distinção visual de zero exato em atividade.
Recomenda-se futuramente `<0,1%` para pequenos positivos, mantendo `0%` para zero
exato, com teste próprio. **Nenhuma alteração de formatação foi feita nesta tarefa.**

A barra vermelha do cartão representa **ocupação do volume**, não atividade; seu
`aria-label` e código fazem essa distinção. Como ela fica abaixo da linha de
atividade, recomenda-se um rótulo visível para evitar associação visual indevida.
O badge do cartão reflete a ocupação, não a disponibilidade de todos os contadores.
Esses ajustes de apresentação devem ser aprovados na preparação da candidata.

## Consumo por componente

CPU normalizada pela capacidade total: tempos kernel+user de cada processo desde
a criação / 67,173663 s / 12 processadores lógicos × 100. Memória por working set,
64 observações com os seis processos presentes; soma pode repetir páginas compartilhadas.

| Componente | CPU média total | RAM residente mínima | Média | Máxima |
|---|---:|---:|---:|---:|
| Coletor Python | 0,07172% | 28,02 MiB | 28,17 MiB | 28,26 MiB |
| Intermediário IPC | 0,02520% | 20,91 MiB | 20,99 MiB | 21,02 MiB |
| Electron, 4 processos | 0,36442% | 352,70 MiB | 392,09 MiB | 414,25 MiB |
| Total | **0,46134%** | **401,64 MiB** | **441,25 MiB** | **463,43 MiB** |

Máximos individuais podem ocorrer em instantes diferentes; não somar picos para
substituir o pico total medido. CPU cumulativa: coletor 0,578125 s, intermediário
0,203125 s, Electron 2,9375 s; total 3,71875 s. Custo do observador externo e do
observador do agente não incluído. Bootstrap, instrumentação e capturas internas
do Electron estão incluídos. Processos muito breves antes da enumeração podem escapar.

| Comparação com a sessão anterior | Anterior | Atual |
|---|---:|---:|
| Duração completa | 68,100 s | 67,174 s |
| CPU média conjunta | 0,41491% | 0,46134% |
| Soma média de working sets | 425,19 MiB | 441,25 MiB |
| Pico da soma de working sets | 449,99 MiB | 463,43 MiB |

Diferença média de CPU: **+0,04643 ponto percentual**; memória média **+16,06 MiB**.
O ensaio anterior não separou componentes. As sessões têm diferentes instantes,
carga de fundo, capturas, sequência de navegação e instrumentação; **não é um A/B
controlado e não prova causalidade da correção PDH**. A referência de planejamento
<0,5% do coletor foi atendida em média neste teste curto; não é garantia de uso
contínuo, impacto nulo, picos ou jogos. Não se observou travamento/degradação visual
relevante, mas o ensaio não mede todos os efeitos sobre o sistema.

## Estado final e preservação

- Electron saiu com código 0; coletor, intermediário e quatro processos Electron
  encerrados normalmente. Nenhum resíduo. Stop `clean=true`, `stopped=true`,
  `timed_out=false`; sem kill, segunda abertura ou repetição automática.
- Mesmos supervisor **400**, worker **8680**, redirecionadores 17772/10996, criação,
  usuário, argumentos e imagem. Listener único **8776**. Observador: 15 amostras
  saudáveis em 77,367 s, sem operação de controle do agente.
- Pós-verificação às 09:23:36–09:23:39 UTC: identidades intactas, GETs de status/apps
  HTTP 200/TLS 1.3 com certificado/hostname/pin e autenticação preservados; permissões
  vazias. Zero grants e pendentes; SQLite quick_check e identidade lógica OK.
- Instalação dev.4 **77 arquivos**, perfil **76**, backups dev.3/dev.4 **341/75**
  incluindo metadados: hashes/árvores idênticos antes/depois. Os 263 arquivos
  operacionais protegidos fora do banco mantiveram seus hashes. Sem descriptografia
  de perfis ou cópia de segredos para Git. Nenhum arquivo de fonte funcional mudou.
- HKCU Run e regras relevantes de firewall com os mesmos hashes; não foram feitas
  alterações em serviços, tarefas, drivers, configuração Windows, credenciais,
  certificados ou permissões.
  Android dev.7 e Electron instalado não foram abertos/atualizados. Não houve Steam,
  CS2, WoL, energia, GPU, temperaturas, FPS ou carga artificial.
- O helper autenticado foi separado do Electron; nenhuma identidade desktop nova,
  pareamento ou cliente Electron–HTTPS foi criado. Não houve nova conferência
  física da tela Samsung. Agente foi deixado ativo deliberadamente.

TLS e encerramento gracioso continuam tarefas separadas, sem alterações.
A conferência final às **09:38:29–09:38:32 UTC** repetiu as verificações de
identidade/listener, zero grants, integridade e GETs autenticados com sucesso,
sem iniciar novamente o monitoramento; recibos `*-final.json`.

## Alternativas para atividade, sem implementar fallback

**Recomendação de menor risco:** manter leitura/gravação e ocupação reais, preservar
`null` onde a atividade falhar e tratar atividade como opcional; se necessário,
ocultar temporariamente só esse indicador com explicação explícita. Não derivar
tempo ativo de bytes/s, preencher com último valor, limitar resultados ou mostrar zero.

Alternativa para avaliação futura: expor atividade do **disco físico** como uma
métrica distinta e qualificada, após mapear volume→partição→disco e validar a
topologia. As associações nativas são documentadas por
[Win32_LogicalDiskToPartition](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-logicaldisktopartition)
e [Win32_DiskDriveToDiskPartition](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-diskdrivetodiskpartition).
Há um contador físico de idle documentado em
[Win32_PerfRawData_PerfDisk_PhysicalDisk](https://learn.microsoft.com/en-us/previous-versions/aa394308%28v%3Dvs.85%29).
Isso não é atividade exclusiva de C: ou D:; volumes podem compartilhar discos.
WMI/PDH podem compartilhar a infraestrutura de contadores: não há garantia de
corrigir a causa atual. Permissões, custo, compatibilidade e topologia precisam
de validação própria, sem elevação presumida. Nada disso foi consultado neste PC
ou implementado como fallback nesta tarefa.

## Evidências, commits e próximos passos

[metrics-summary.json](metrics-summary.json), [readings.csv](readings.csv),
[resources-summary.json](resources-summary.json), [resources.csv](resources.csv),
[ui-verification.json](ui-verification.json) e [assessment.json](assessment.json)
separam sucesso de transporte, disponibilidade e limitações de precisão.
Manifesto em [artifact-sha256.json](artifact-sha256.json); originais locais em
`.cache/validation/monitoring-storage-2026-10-25/`, com hashes em
[raw-sha256.json](raw-sha256.json). Inventários privados permanecem fora do Git.

Commit de instrumentação: `3abd308` (somente testes/observador). Relatório em commit
documental subsequente. Reversão, se necessária, consiste em revisar o commit
inverso da instrumentação; nada a restaurar na instalação, perfil ou banco. Não
apagar markers de tentativa, backups ou evidências, nem encerrar o agente.

Antes da implantação: aprovar política da atividade opcional e ajustes de precisão
visual/barra; preparar lifecycle e empacotamento do coletor para uso instalado,
pois o host atual é explicitamente de desenvolvimento e tem TTL de teste. Não
declarar coleta permanente pronta. Nenhum novo NSIS foi preparado/executado.

Solicitar autorização específica para **preparar a próxima versão instalável**,
com essas limitações explícitas, testes e plano de atualização/reversão. Preparação
não autoriza instalar, ativar autostart, novos grants ou cliente HTTPS desktop.
