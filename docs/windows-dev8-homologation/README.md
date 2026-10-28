# Homologação consolidada Windows dev.8 — 28/10/2026

**Conclusão: parcialmente homologada.** A dev.8 foi instalada uma única vez sobre
a dev.7. Monitoramento real, histórico, CSV e parte das ferramentas locais
funcionaram. A retomada GPU, a saída exclusivamente pela bandeja e diversas áreas
novas ainda não têm evidência física suficiente. A segunda sessão excedeu o prazo
planejado e não está aprovada no critério temporal. Não houve nova abertura após
seu encerramento.

Base: `64f3ec8`, branch `feature/windows-control-center`. Android congelado.
Os relatórios antigos descrevem a candidata antes desta instalação; este documento
registra o resultado instalado e não substitui as evidências anteriores.

## Instalação e recuperação

- NSIS executado **uma vez**, assistido, sem executar o portátil ou contornar
  proteções. Versão instalada: **2.0.0-dev.8**, identificador preservado.
- Destino: `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room`.
- Setup: 105.781.195 bytes; SHA-256
  `91262cbd9fb11835cb2db6f9b6cb3df37455847d83482f3bc91e27851cc03b7a`.
- Portátil preservado, não executado: 105.495.092 bytes; SHA-256
  `a285ed7ae0824573881ecac3deb81ea703113a52007efc9e2bd18ccd1d8d63fb`.
- Pacotes continuam **NotSigned**. Aplicação x64; stub do instalador x86.
- **115 arquivos** da candidata correspondem aos instalados por SHA-256.
- Backup novo, fora do Git e protegido por ACL somente da conta autorizada:
  `<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev8-20261028T035246Z`.
  Contém **195 arquivos / 402.164.658 bytes**, instalação dev.7 e perfil; todos
  novamente conferidos. SHA-256 do manifest:
  `781721b0931fb49256b0db481e9e004917cea98f7fd127d0dfdf9201d31f93bd`.
- A inspeção prévia confirmou que o backup anterior chamado before-dev7 contém
  dev.6. Por isso o novo backup efetivamente da dev.7 foi criado antes de instalar.

**Ocorrência real do instalador:** o NSIS removeu o `debug.log` adicional da pasta
anterior. Antes de abrir o app, somente esse arquivo ausente foi recuperado do
backup verificado, sem sobrescrever outro arquivo. Hash recuperado:
`3c07a1353428a6ee9239f0e7b0576d95a84dca4dd40d07281499ba062dd73c9c`.
O funcionamento posterior acrescentou quatro linhas Crashpad. O instalador futuro
precisa preservar explicitamente logs adicionais ou migrá-los com backup; isso
**não foi corrigido no NSIS atual** nem motivou outra instalação.

## Matriz do que foi efetivamente validado

| Área / funcionalidade | Resultado real nesta homologação | Situação |
|---|---|---|
| Dashboard, marca oficial, Controles e Monitoramento PC | Abertura e navegação observadas, sem falha visual relevante nas capturas | Operacionais no escopo observado |
| Terceira aba Gamer Launcher | Preservada no pacote e regressões; não foi percorrida fisicamente nesta sessão | Preparada; teste instalado pendente |
| CPU, RAM, C: e D: | Leituras reais e origem identificada; capacidade separada de I/O/atividade | Operacionais |
| GPU ADLX | Uso, temperatura, hotspot, VRAM, clock, potência e RPM reais | Operacional com limitação de retomada abaixo |
| Widget e bandeja | Widget real; ocultação e restauração da mesma sessão confirmadas, inclusive pelo usuário | Operacionais com limitações de evidência |
| Retomada GPU | Não capturamos Atualizando; primeira árvore acessível continha timestamp antigo, depois veio leitura nova | Não homologada |
| Saída normal | X normal encerrou Electron, coletor, IPC e ADLX; zero pipes depois | Operacional; Sair da bandeja não isolado de X |
| Central Windows / visão geral | Catálogo de 12 áreas e contratos aprovados em testes isolados | Percurso físico completo pendente |
| Hardware e rede | Inventário CPU falhou na UI; cópia diagnóstica de leitura retornou CPU/núcleos depois | Operacional com falha intermitente não explicada |
| Histórico / gráficos / CSV | Gráficos de dados reais; exportação pelo diálogo instalado e CSV conferido | Operacionais |
| Central de Diagnóstico | Cache de monitoramento/pipe/ADLX/sensores exibido; agente e inicialização Não verificado | Operacional com fontes limitadas; sem novas sondas |
| Manutenção | Prévia de metadados de temporários; nenhuma exclusão. Dois defeitos corrigidos só no desenvolvimento | Operacional com limitações na instalação |
| Perfis e otimização | Perfil Padrão salvo e auditado somente no próprio app | Persistência operacional; ajustes Windows bloqueados |
| Aplicativos | Inventário real do Registro exibido | Leitura operacional; atualização/instalação não implementadas |
| Periféricos | Tela e início do teste em foco abertos; contador capturado permaneceu zero | Captura de entrada não homologada; microfone não acionado |
| GPU e tela | Provedores e padrões preparados/testados com substitutos | Teste físico de padrões pendente |
| Rede e internet | Validação de alvos e cálculos testados com mocks | Ping/DNS pela UI instalada não executados |
| Biblioteca e FPS | Importação PresentMon, separação de streams e arquivo aprovados em mocks | Importação instalada pendente; FPS ao vivo não implementado |
| Quarto / RGB | Contratos, preferências e prévia de cenas preparados | Sem conectores físicos operacionais |
| NEX | Regras locais e navegação preparadas | Não é IA operacional; teste instalado pendente |
| Backup e auditoria | Arquivo local contém historyPolicy e profile/saved | Exportação/importação pela UI instalada pendentes |
| Touch Panel / overlay | Contratos, segurança e janelas testados anteriormente em desenvolvimento | Não abertos nesta homologação instalada |

### Dados reais e frescor

CSV exportado pela aplicação: **1.404 linhas, 108 snapshots, 13 métricas, seis
origens**, todos `simulation=false`, entre 04:00:07.781Z e 04:05:21.323Z.
**66 valores nulos e 291 zeros válidos** permaneceram distintos. Arquivo bruto
mantido localmente em `.cache/validation/windows-dev8-homologation/real-history.csv`.
O recibo reduzido está em `measurements.json`.

| Métrica exportada | Mínimo | Média | Máximo |
|---|---:|---:|---:|
| CPU do computador | 3,14% | 6,79% | 17,41% |
| GPU | 0% | 3,21% | 6% |
| Temperatura GPU | 53 °C | 53,03 °C | 54 °C |
| RAM utilizada | 10,76 GiB | 11,00 GiB | 11,28 GiB |
| Ocupação C: | 52,207% | 52,208% | 52,208% |
| Ocupação D: | 45,851% | 45,851% | 45,851% |

Leitura/gravação C: médias 232.237 / 398.404 bytes/s; D: zero válido em todas as
108 leituras/gravações exportadas. Atividade PDH válida em **103/108** registros
C: e **57/108** D:. Indisponibilidades não foram preenchidas com zero.
Os números são do período observado, sem benchmark ou carga artificial.

Capturas também registraram hotspot 56 °C, VRAM usada em torno de 850 MB / total
12.272 MB reportados pela API, clock 182 MHz, potência 37 W e ventoinha 494 RPM.
São exemplos visuais, não mínimos/médias/máximos dessas métricas.

O CSV amostra o histórico com intervalo médio **2,93 s** (máximo 11,886 s);
isso não mede toda a cadência interna dos sensores. Não obtivemos contagem completa
de frames ADLX aceitos/rejeitados na sessão instalada.

Na retomada, a primeira árvore acessível às 04:04:12.899Z continha amostra GPU
04:03:13.106Z e texto de validade antigo. Às 04:04:20.505Z havia leitura
04:04:17.883Z. A captura inicial com janela ocluída foi preservada em cache privado,
excluída da galeria. Não é possível atribuir com certeza o primeiro estado ao
renderer, pintura ou atraso da ferramenta de acessibilidade. Portanto **não
atestamos a correção de retomada**. Testes simulados mantêm ingresso 1,5 s,
frescor ativo 3 s/inativo 11 s e indisponibilidade após 10 s, sem flexibilização.

## Tempo, desempenho e encerramento

- Sessão 1: lançamento 03:58:53.896Z, pedido de fechar por X 04:10:34.991Z
  (**701,095 s**), primeira amostragem sem processos 04:10:35.896Z (~702 s),
  dentro dos 720 s planejados. O usuário também confirmou Sair, porém nossa ação
  X impede atribuir o encerramento exclusivamente ao menu da bandeja.
- Sessão 2: lançamento 04:13:19.760Z, pedido de fechar 09:32:59.222Z
  (**19.179,462 s / 5h19m39s**), sem processos às 09:33:04.356Z. O app ficou
  aberto durante a pausa da conversa, ultrapassando os 480 s planejados.
  **Falha no controle temporal da sessão**, não um sucesso de homologação.
  O observador parou no limite; não existe medição contínua das cinco horas.
- Nas duas saídas foi utilizado fechamento normal; nenhum taskkill, término
  forçado ou reinicialização. Não reabrimos depois da retomada da conversa.

O primeiro observador arredondava CPU por selecionar a sobrecarga inteira de
`Math.Max`. Seus números de CPU foram **invalidados**, não tratados como zero real.
O script foi corrigido para doubles e CPU acumulada antes da segunda sessão.
RSS da primeira sessão: média **481,69 MiB**, pico **514,28 MiB**.

Segunda sessão, **somente a janela amostrada de oito minutos**:

| Componente | CPU média do total lógico | Maior intervalo CPU | RSS médio | Pico RSS |
|---|---:|---:|---:|---:|
| Electron (quatro processos) | 0,5884% | 5,1469% | 392,07 MiB | 420,12 MiB |
| Coletor | 0,0362% | 0,1916% | 30,73 MiB | 31,19 MiB |
| Intermediário IPC | 0,0275% | 0,1905% | 23,36 MiB | 23,60 MiB |
| Ponte ADLX | 0,0173% | 0,1276% | 23,91 MiB | 24,34 MiB |
| Total | **0,6693%** | **5,1469%** | **470,06 MiB** | **498,49 MiB** |

CPU calculada por deltas de tempo kernel+usuário / tempo decorrido / 12 processadores
lógicos; médias ponderadas no mesmo conjunto de amostras completas. RSS inclui a
fase de criação e pode contar páginas compartilhadas mais de uma vez. Picos por
componente não precisam coincidir. Observação a cada ~2,045 s. Electron representa
~87,9% da CPU média dos componentes nesse recorte, sem prova de regressão em relação
a cenários diferentes. Não é um teste de vazamento de longa duração nem de impacto
em jogos; nenhuma carga artificial foi criada.

Quatro novas linhas Crashpad 0xE9: 00:58:55.231 / 01:00:55.230 e
01:13:20.859 / 01:15:20.855 locais, próximas à abertura e dois minutos depois.
Nenhum evento Application 1000/1001 correlacionado ou novo dump foi encontrado
na consulta realizada. Isso não identifica a causa do Crashpad nem o torna resolvido.

## Correções de desenvolvimento e testes

1. Inspetor: ENOENT da raiz significa prévia vazia `root_absent`, não acesso negado.
   EACCES continua indisponível. A travessia passa a respeitar 2.000 entradas
   globalmente, inclusive ao voltar da recursão. Observação real anterior: 2.002.
   Nenhuma função de exclusão foi adicionada.
2. Observador de desempenho: sobrecarga double e CPU acumulada para auditoria.
3. Novo `agent/development/supervision.py`: política pura, desativada por padrão,
   sem spawn, rede, Registro, segredos ou importação do agente operacional.
   Distingue pré-verificação, início, prontidão HTTPS comprovada, degradação,
   recuperação limitada opt-in, drenagem cooperativa e timeout sem força.

**Reexecutados:** nove suítes Node, **2.267 verificações**, aprovadas; 45 testes
Python (15 novos da política + 30 do launcher existente), aprovados, com processo
real/rede bloqueados. Recibos: `focused-node-tests.json` e `isolated-agent-tests.json`.
O primeiro teste adicional do inspetor falhou por contar chamadas lstat de
revalidação de diretórios como novas entradas; a asserção foi corrigida para medir
o limite contratado, mantendo os 2.000 itens e um limite separado de metadados.

A candidata instalada já tinha 19 suítes Node/3.242 verificações, Python 268 e
C++ mock 35 aprovados na preparação. Esses totais anteriores não são novas
execuções desta rodada. Não recompilamos/reempacotamos depois das correções acima;
**a instalação dev.8 continua correspondendo à candidata original**.

Inventário CPU: a UI retornou `readonly_provider_unavailable`; uma cópia isolada
do helper com diagnóstico sanitizado retornou dados depois. Isso limita as
hipóteses a ambiente/tempo de resposta/inicialização do provedor, mas não prova
timeout, encoding ou causa específica. Não aplicamos uma correção especulativa.

## Agente HTTPS: estado e proposta isolada

O agente **já estava offline e permaneceu offline**: zero supervisor/worker e
zero listener 8776. Não houve tentativa de recuperação ou autenticação ao serviço
ausente. Banco `quick_check` OK, **zero grants e zero comandos pendentes**;
hashes de configuração, certificado, chave protegida e DPAPI preservados.

Último boot observado: 27/10/2026 23:23:24,5 local. O HKCU Run continua apontando
diretamente para `pythonw.exe ... secure_agent.py serve`, em vez do launcher
validado. Isso ignora os recibos e a supervisão desse launcher. Os últimos registros
dele são anteriores ao boot. Não há evidência suficiente para decidir se o Windows
não despachou Run ou se o processo direto falhou antes de registrar algo.
**Confiança alta na divergência do caminho; baixa/inconclusiva na causa da falha
recorrente.** O hash do comando Run permaneceu igual.

A política nova reutiliza conceitualmente o launcher de caminhos fixos, mutex por
SID e a fundação cooperativa existentes. Um host futuro deverá adaptar ações
tipadas às implementações existentes e fornecer evidências frescas de identidade,
listener, TLS e autenticação. Um processo vivo não basta. Recuperação padrão tem
uma tentativa; orçamento maior, limitado a três, depende de aprovação/configuração
específica e exige confirmação de worker encerrado, mutex liberado e porta livre.
Falhas de segurança, duplicação, limpeza inconclusiva e timeout nunca causam kill
ou uma nova tentativa automática. Eventos são códigos fixos, limitados a 64.

**Preparada e testada com mocks; não é uma correção operacional definitiva.**
Faltam o adaptador host aprovado, integração dos recibos de despacho/bootstrap e
uma validação controlada de login/encerramento. Alterar Run, ligar o agente ou
substituir seu código requer autorização posterior. Nenhuma garantia de despacho
após login pode ser demonstrada somente por uma política de supervisão.

## Estado final e reversão

- **Dev.8 instalada e fechada**; zero Electron/coletores/IPC/ADLX da instalação e
  zero Named Pipes de monitoramento na verificação final.
- Perfil: **nenhum dos 78 arquivos anteriores ausente**, 83 atuais; 20 arquivos
  alterados durante a execução autorizada (estado de janela/caches normais).
  Histórico foi ativado pela UI com retenção de uma hora; arquivo de histórico
  observado ~924 kB. Perfil local Padrão salvo, sem aplicar ajustes ao Windows.
  Preferência de bandeja automática continua desligada.
- Backup dev.7: 195 arquivos íntegros. Backups anteriores não foram modificados.
- Agente offline preservado; autenticação não pôde ser verificada sem iniciá-lo.
  Android não acessado nem modificado; nenhuma instalação APK ou nova coleta no celular.
- Nenhuma alteração feita por nós em firewall/serviços/tarefas/HKCU Run. Apenas o
  comando Run foi comparado por hash; não se declara auditoria diferencial integral
  de todos os objetos do Windows nesta verificação final.
- Não executamos Steam, CS2, WoL, energia, reparos, debloat ou atuadores.

Reversão **não executada**: fechar normalmente o app; criar backup do perfil dev.8
atual; conferir o manifest acima; atualizar de volta com o NSIS dev.7 preservado
(SHA-256 `0033ee706adfd9edcd29d2f87b5bddc5751bcbd2a6337125e09adb84d49d7870`)
somente após autorização. Preservar o perfil atual e restaurar somente preferências
necessárias da cópia dev.7 caso haja incompatibilidade; não limpar dados, apagar
perfis ou tocar no banco do agente. Verificar arquivos antes de reabrir.
O plano é estático; não foi realizado ensaio de restauração/rollback instalado.
Reversão do código: reverter os commits desta rodada sem reset destrutivo; isso
não reverte a instalação nem altera o agente.

## Próximos trabalhos necessários

1. Resolver a evidência de retomada GPU com instrumentação de desenvolvimento;
   não homologar valores antigos como atuais.
2. Diagnosticar o inventário CPU com códigos de etapa/timeout sanitizados antes
   de alterar prazos ou encoding sem comprovação.
3. Incluir as correções do inspetor e preservação de logs em uma futura candidata,
   sem reinstalação automática agora.
4. Após autorização, testar as áreas ainda pendentes e Sair da bandeja com sessão
   curta e encerramento independente da continuidade da conversa.
5. Autorizar separadamente a implantação/validação do caminho de inicialização do
   agente. TLS 10054, encerramento gracioso, Crashpad e demais pendências seguem abertos.

## Evidências visuais reais

![Monitoramento instalado](captures/04-monitoramento-real-0.png)

![Widget instalado](captures/07-widget-sensores-0.png)

![Diagnóstico baseado no cache local](captures/12-diagnostico-real-0.png)

![Prévia de temporários sem exclusão](captures/22-temporarios-metadata-0.png)

Recibos temporais e acessibilidade ficam junto das capturas. Dados brutos de
processos, CSV e a imagem ocluída continuam no cache local ignorado pelo Git.

## Checkpoints desta rodada

- `39d8957`: correções do inspetor e scripts de medição/verificação.
- `1223a5c`: política isolada e desativada de supervisão do agente, com mocks.
- O commit documental que contém este relatório sucede os dois anteriores.
  Não houve merge, reinstalação adicional ou alteração no agente operacional.
