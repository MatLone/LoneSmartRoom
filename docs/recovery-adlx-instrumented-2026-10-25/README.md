# Recuperação HTTPS e sessão física ADLX instrumentada

Data local: 25/10/2026, America/Sao_Paulo. Os recibos usam UTC de 26/10.
Base preservada: `76711ff`. Branch: `feature/ui-migration-preview`.
Runner e testes isolados: `6cdb395`. Nenhuma integração ao aplicativo instalado.

## 1. Recuperação HTTPS

Uma única partida manual de `agent/windows/agent_launcher.py`, versão já validada
fisicamente, SHA-256 `8f137269555ad33b744c4b19b65ac5726785f6d1482ff3182f5f3a495ee32a08`.
O launcher novo com encerramento gracioso não foi utilizado. HKCU Run não mudou.

Pré-verificação: agente/supervisor/mutex ausentes, porta 8776 livre, zero grants,
zero comandos pendentes, sete arquivos da implementação iguais ao manifesto,
banco íntegro e identidades/segredos cifrados/schema/revogações iguais à referência.
Certificado vigente, pin correspondente, chave cifrada carregável, configuração
LAN aprovada e rede Privada. Não houve elevação nem alteração de configuração.

O primeiro inventário encontrou o Electron instalado aberto e o perfil bloqueado.
Nenhuma partida havia ocorrido. O usuário encerrou manualmente por **Sair**,
autorizou repetir a pré-verificação e o perfil então foi conferido estável.
Instalação/perfil/backups corresponderam inclusive à referência anterior.

Processos confirmados por imagem, argumentos, árvore, criação e token:

| Papel | PID | Pai |
|---|---:|---:|
| Redirecionador Python da venv do supervisor | 19996 | processo de preparação |
| Supervisor Python efetivo | 5024 | 19996 |
| Redirecionador Python da venv do worker | 20352 | 5024 |
| Worker efetivo e dono do listener | 18304 | 20352 |

São um supervisor e um worker, com os redirecionadores normais da venv;
não quatro instâncias operacionais. Ambos os tokens foram conferidos na mesma
conta autorizada, sem elevação. Mutex existente com DACL verificada e retido;
nenhuma segunda execução foi utilizada para testar duplicação.

**Ocorrência de prontidão, preservada:** o inventário inicial após uma espera fixa
de três segundos ainda não encontrou listener e a asserção do helper falhou.
Essa asserção não iniciou nem reiniciou nada. A investigação de leitura encontrou
depois o mesmo worker com listener e sem erro nos logs. O evento `bootstrap_ready`
antecede `runner(layout)` e não comprova bind HTTPS. Não há marcação precisa do
instante de bind para atribuir a latência à rede ou a uma causa específica.
O inventário inicial está preservado em `system-started-early.json`, no cache local.
As verificações de prontidão posteriores passaram antes da etapa GPU.

Resultado de comunicação: listener único em 8776, vinculado à LAN aprovada,
sem wildcard; TLS **1.3**, cadeia do certificado local, hostname e pin validados
antes de enviar HMAC. GET autenticado `/v2/status` = **200**, agente online;
GET `/v2/apps` = **200**, lista permitida vazia. Nenhuma identidade foi criada;
a credencial existente foi usada somente em memória pelo verificador local.
O Samsung foi confirmado pelo usuário como **Conectado, sem novo pareamento**.

Observação contínua de **68,48 s**, 13 inventários saudáveis, mesmos processos e
listener. Cinco novos eventos sanitizados de bootstrap, sem evento de erro;
logs existentes com ACL exclusiva da conta e esquema/tamanho/retensão verificados.
O agente foi deixado ativo e continuou autenticado antes e depois da sessão GPU.

## 2. Preparação e testes da sessão GPU

Os recibos dos **258 testes Python, 319 verificações Node e 31 asserts C++** foram
revalidados contra **120 entradas de hash dos fontes**. Não foram apresentados
como uma nova execução integral dessas suítes. Nenhum fonte operacional coberto
mudou. O binário real e o mock conferiram com fontes e recibos de compilação.

Foram adicionados e executados **14 testes simulados**, sem falhas ou skips, com
audit hook recusando processos, DLLs, sockets e Registro. Cobrem primeira rejeição
seguida de recuperação na mesma ponte; todas as leituras rejeitadas; regra desconhecida;
timeout/falha fatal; frescor de 1,5 s; timestamp repetido; cadência/recursos; bootstrap;
falha de encerramento; memória; duração; exportação limitada e primeira rejeição retida.

O novo `scripts/adlx-instrumented-session.py` é apenas um runner de diagnóstico
opt-in, não importado pelo agente, Electron ou worker operacional. Ele permite
observar frames seguintes **na mesma instância** após uma rejeição de validação
identificada, mantendo o valor rejeitado nulo. Falhas de transporte, inicialização,
permissão, regra desconhecida e memória excessiva encerram a sessão normalmente.
Não altera o comportamento do runner operacional anterior nem dos validadores.

Foi recompilado somente o verificador estático, com MSVC/SDK já disponíveis;
os arquivos anteriores desse verificador foram preservados e comparados em cache.
O verificador executado checa caminho, hash, PE x64 e assinatura/catálogo sem
carregar ADLX. Nenhuma dependência, driver ou ferramenta foi instalada.

DLL: `C:\Windows\System32\amdadlx64.dll`, versão **1.4.0.121**, assinatura/catálogo
aceitos pelo WinVerifyTrust e SHA-256
`992f6db497a3c8af8d26e578c7b7fce90ed67e506d7790cc3221e4a01b67852a`.
Ponte real SHA-256
`8b26f91e834465d1cec11e8fe6ddab25f0804c9923be10fec26b494daaef5a4d`.
SDK V1.4, fontes fixados em `66557d410ce4c463f5f7106597d94f53dd84bc82`.

## 3. Resultado físico ADLX

Uma única sessão: **23:47:55–23:49:05**, duração total **70,097 s**, sem Electron,
benchmark, jogo, carga artificial ou configuração da GPU. Um carregamento/initialize;
ponte PID **376**, coletor Python efetivo PID **5316**. Transporte stdio herdado
privado, sem endpoint de rede ou Named Pipe operacional novo.

GPU identificada pelo ADLX: **AMD Radeon RX 6750 XT**, discreta, vendor AMD.
Driver informado em leitura por `Win32_VideoController`: **32.0.21045.16010**,
data **16/10/2026**; isso não identifica por si só o nome comercial do pacote Adrenalin.
O SDK informou intervalo interno de 1.000 ms. Todas as sete capacidades dinâmicas
foram consultadas com `ok=true, supported=true`; capacidade VRAM retornou sucesso.

**35 tentativas: 1 frame rejeitado (primeiro) e 34 válidos (97,14%).**
Não houve rejeição subsequente, erro fatal de transporte, falha de recurso ou restart.

| Métrica real | Unidade do contrato/ADLX | Mínimo | Média válida | Máximo | Amostras válidas |
|---|---|---:|---:|---:|---:|
| Utilização GPU | % | 0 | 0,324 | 10 | 34 |
| Temperatura GPU | °C | 55 | 55,647 | 57 | 34 |
| Hotspot | °C | 58 | 59,471 | 62 | 34 |
| VRAM utilizada | MB | 809 | 969,794 | 1.283 | 34 |
| Clock GPU | MHz | 0 | 840,118 | 2.497 | 34 |
| Potência GPU | W | 33 | 40,588 | 54 | 34 |
| Ventoinha GPU | RPM | 488 | 493 | 496 | 34 |
| VRAM total | MB | 12.272 | 12.272 | 12.272 | 2 |

MB permanece a unidade fornecida pela API/contrato; não foi renomeada para MiB.
Zeros de utilização/clock foram valores disponíveis retornados pela API, não
substituições de ausência. O primeiro frame rejeitado manteve as sete métricas
dinâmicas nulas e inválidas; a capacidade estática não foi contada como frame dinâmico válido.
Valores desta sessão de atividade normal não representam comportamento em jogos.

Intervalo efetivo entre ciclos com frames válidos: **média 2,0084 s**, mínimo
**1,9845 s**, máximo **2,0243 s** (33 intervalos, medidos por relógio monotônico).
O resumo de timestamps de todas as tentativas, incluindo a rejeitada, tem média
2,0079 s; são bases de cálculo distintas. Capacidade foi reamostrada em 60,24 s.
Não se deve equiparar frequência de consulta a uma nova amostra nativa garantida;
a progressão do timestamp e o frescor são verificados pelo provedor.

## 4. Regra exata e evidência sanitizada

Rejeição observada nesta sessão: `invalid_frame`, estágio **time**, regra
**age_null**, campo `age_seconds`. Ela ocorre antes da validação dos valores dos
sensores e da idade adicional da fila de transporte Python.

Primeiro frame: `timestamp_ms` era inteiro **6237127**; `age_seconds` era **null**;
`clock_source=unverified`. O diagnóstico nativo informou **clock_unmatched**:

| Referência comparada ao timestamp ADLX | Delta em ms |
|---|---:|
| Uptime/GetTickCount64 | **−2** |
| Unix/UTC | 1.792.976.639.236 |
| Windows/FILETIME | 13.437.450.239.236 |

A ponte só reconhece uma referência quando `0 <= referência - timestamp <= 5000 ms`.
Nenhuma correspondeu nesse frame. `age_at()` devolveu sentinela negativa;
`frame_json()` a serializou como null; o adaptador Python recusou corretamente esse
null. Isso demonstra a cadeia de rejeição, sem inferir conversão inválida de segundos
ou timezone. Os campos indicaram explicitamente timestamp em ms e idade em s.

Nos frames seguintes foi reconhecido `uptime_ms`, com idade válida e timestamp
avançando. Último registro retido: timestamp **6304745**, delta uptime **661 ms**,
idade **0,661 s** e `clock_matched`. Os 34 frames passaram também pelo limite do
provedor de **1,5 s**, sem tolerância extra, clamp ou alteração do contrato v1.

**Hipótese, não causa comprovada:** diferença de resolução entre o relógio usado
pelo SDK e `GetTickCount64` pode produzir um pequeno avanço aparente no primeiro
frame. A Microsoft documenta resolução típica de 10–16 ms para GetTickCount64.
Isso é compatível com o delta −2 ms observado, mas não comprova qual relógio interno
o driver usa ou exclui outras diferenças de sincronização. A AMD documenta o
timestamp como duração em ms desde o epoch do sistema, sem garantir nessa página
a equivalência exata com GetTickCount64.

Fontes oficiais consultadas:
[Microsoft GetTickCount64](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-gettickcount64),
[AMD IADLXGPUMetrics::TimeStamp](https://gpuopen.com/manuals/adlx/adlx-sdk-references/adlx-interfaces/performance-monitoring/iadlxgpumetrics/timestamp/).

A causa primitiva do frame da **sessão antiga** não pode ser provada retroativamente:
o frame original não foi retido. Esta sessão reproduziu a rejeição inicial com regra
e dados temporais agora identificados; é evidência nova, não recuperação do payload antigo.

Instrumentação: **16 registros**, **23.376 bytes** no arquivo compacto local,
19 registros antigos descartados; primeira rejeição preservada. Limites respeitados:
16 registros/32 KiB, sem payload bruto, exceções livres, caminhos pessoais ou segredos.
Os estados dos sensores nesse log são de pré-validação; a confirmação final de validade
está no contrato das métricas. Instrumentação opt-in terminou com o processo da ponte;
o padrão do código e a configuração operacional continuam desligados.

Nenhuma correção temporal foi aplicada. Não foi aumentado frescor, aceita leitura
futura ou convertida ausência em zero. Para integração futura, propõe-se manter o
primeiro frame inválido indisponível e permitir nova leitura na cadência normal da
mesma ponte, com prazo inicial limitado e erro persistente visível. Essa mudança
operacional ainda precisa de aprovação e testes; o runner desta entrega é diagnóstico.

## 5. Desempenho observado

CPU medida por deltas de tempo kernel+usuário via GetProcessTimes, divididos pelo
tempo monotônico observado e pelos **12 processadores lógicos**. Memória por
WorkingSetSize/PrivateUsage via K32GetProcessMemoryInfo. Nenhuma carga artificial.
Python exclui importações anteriores à linha de base; a ponte inclui seu bootstrap.

| Componente | CPU média (% da máquina) | RSS média MiB | RSS pico MiB |
|---|---:|---:|---:|
| Coletor Python | 0,00372 | 24,669 | 24,742 |
| Ponte nativa ADLX | 0,06316 | 24,620 | 24,645 |
| Soma observada | **0,06687** | **49,289** | **49,387** |

Sem Electron/intermediário de dashboard nesta sessão. RSS somada pode contar páginas
compartilhadas mais de uma vez; não representa memória física exclusiva. Resultado
abaixo de 0,5% nesta sessão curta, sem promessa para outros drivers/cargas ou versão
empacotada. Não comparar diretamente com consumo conjunto da dev.5 com Electron.

## 6. Encerramento, preservação e limitações

Parada normal, `StopPerformanceMetricsTracking`, liberação das interfaces,
`ADLXTerminate`/FreeLibrary, retorno da ponte **0**, fechamento do transporte e do
coletor. Nenhum force, restart ou segunda sessão.

Um inventário posterior que procurou apenas os números de PID encontrou `conhost.exe`
no número 376 e sinalizou residual. A imagem não era a ponte e o handle Popen da ponte
já confirmava saída 0. A inspeção subsequente por imagem/argumentos não encontrou
ponte/coletor e nenhum desses PIDs ainda existia. A primeira sinalização foi mantida
como limitação do inventário por PID, não relatada como processo GPU sobrevivente.
Não foi encerrado ou sinalizado nenhum processo. O identificador numérico isolado
nunca foi usado para uma ação de processo.

Estado final: supervisor **5024**, worker **18304**, mesmo instante de criação,
listener único **8776**, TLS 1.3/status autenticado 200, **zero grants** e **zero
comandos pendentes**. Samsung confirmado antes da GPU; não houve nova confirmação
humana após a GPU, embora o HTTPS continuasse autenticado. Agente deixado ativo.

Preservação por SHA-256: instalação **109 arquivos**, perfil **77**, backups dev.3
**341**, dev.4 **75**, dev.5 **156**, **86 arquivos operacionais protegidos**, todos
sem diferenças. Banco íntegro e hashes lógicos das identidades, segredos cifrados,
schema e revogações iguais. HKCU Run/firewall iguais; DLL, evidências antigas e
12 arquivos do build antigo preservados. Dados operacionais normais de nonce/status
podem mudar por consultas HMAC; não se afirma igualdade byte a byte do SQLite ativo.

Nenhum Android/Electron instalado alterado ou iniciado; nenhum jogo, WoL ou energia.
Sem instalação de dependências, serviços, tarefas, drivers ou novo autostart.
TLS, Crashpad, inicialização automática e encerramento gracioso continuam pendências
separadas. Não foi validado o comportamento em jogos, reconexão física do driver,
suspensão ou estabilidade longa; nenhuma dessas ações foi realizada.

## 7. Evidências, commits e reversão

`evidence/` contém apenas recibos e resumos sanitizados. Cache privado local ignorado:
`.cache/validation/recovery-adlx-instrumented-2026-10-25/`, com marcador exclusivo de
partida do agente, marcador exclusivo da sessão GPU, métricas v1, diagnóstico limitado
e inventários privados de hashes. Nada foi publicado.

Código desta etapa: `6cdb395`, três novos arquivos do runner/testes; nenhum fonte
do agente, contrato, provider, ponte real, Android ou Electron modificado.
O commit documental acompanha esta pasta. Checkpoints anteriores permanecem ancestrais.

Reversão proposta, **não executada**: árvore limpa, revisar `git show 6cdb395` e
`git revert 6cdb395` para retirar somente o runner e seus testes. Preservar as
evidências/documentação. Não usar reset destrutivo, restaurar banco/perfil ou parar
o agente; o runner não foi conectado a qualquer autostart. Artefatos anteriores
continuam preservados. A instalação dev.5 não exige rollback desta etapa.

Próximo passo depende de autorização: integrar os sensores GPU ao dashboard e widget
**somente em desenvolvimento isolado**, com tratamento explícito da primeira leitura
indisponível, sem enfraquecer os validadores e sem atualizar a instalação existente.
