# Lone Smart Room Windows 2.0.0-dev.7 — pacotes preparados

26/10/2026. Branch `feature/ui-migration-preview`. Base `af2c9c8`, correção
funcional `3dc783c` e checkpoints anteriores preservados. Commit de preparação:
**`d4f39a704089720659c87f0a2992aa2ac75afee8`**.

**NSIS x64 e portátil gerados e inspecionados, sem instalação ou execução.**
A produção continua Windows dev.6, fechada. Nenhum sensor real, Electron GUI,
Steam, CS2, WoL ou comando de energia foi executado nesta etapa.

## Escopo incremental

Inclui a correção de retomada GPU validada com mocks e na
[sessão física isolada anterior](../gpu-resume-physical-2026-10-26/README.md).
Os bytes de `monitoring-host.cjs`, `monitoring-renderer.js` e `monitoring-model.js`
continuam exatamente os aprovados em `3dc783c`; a inspeção confirmou sua inclusão
no ASAR dos dois pacotes. Não se usou a instalação dev.6 como alvo de build.

- Atualizando só conclui com leitura GPU dinâmica válida, fresca e posterior à
  retomada, em cadência ativa. Outra leitura antiga não vira atual numa recuperação
  parcial. Capacidade estática não comprova recuperação dinâmica.
- Erro persistente por 10 s vira estado explícito de indisponibilidade, não sucesso.
  Leituras válidas posteriores podem recuperar sem respawn. Esse orçamento da
  mensagem não torna uma amostra antiga válida.
- Ingresso ADLX continua **0–1,5 s**, rejeitando futuro, não finitos, `age_null` e
  timestamp sem avanço. GPU ativa expira em **3 s** e inativa em **11 s**.
- Contrato métrico v1, origem, unidade, timestamp e disponibilidade preservados;
  null, zero válido e desatualizado permanecem distintos. Primeiro frame inválido
  não é exibido como medição atual.
- CPU i5-12400, GPU RX 6750 XT, RAM, C:/D:, PDH opcional, dashboard, widget, três
  abas, bandeja, preferências, instância única e encerramento cooperativo mantidos.

Não inclui histórico, autodiagnóstico, FPS, redesign Android, sensores adicionais
ou cliente HTTPS operacional no Electron. Não altera executores/grants, TLS,
Crashpad ou encerramento gracioso do agente.

## Alterações de preparação

- `package.json` e as duas versões raiz do lockfile passaram a dev.7. Dependências
  e suas resoluções não mudaram; não houve npm install ou download de dependências.
- Novos diretórios de artefatos e sidecar; nenhum pacote/runtime anterior foi
  sobrescrito. Scripts de preparação/inspeção apontam para dev.7.
- A exigência `gpuReadOnly`/hash nativo/licença no carregador do runtime, antes
  condicionada à dev.6, foi estendida **também à dev.7**. A proteção da dev.6 não
  foi removida. Novos testes rejeitam políticas/manifestações incompletas das duas
  versões mesmo com hashes da fixture recalculados.
- Manifesto e pin do novo runtime gerados. Arquivos de agente, Android, preload,
  controle de janelas e provedores não mudaram.

## Artefatos — não executar sem autorização

Diretório:
`<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\windows\desktop-dev7-distribution`

| Pacote | Bytes | SHA-256 |
| --- | ---: | --- |
| `Lone-Smart-Room-2.0.0-dev.7-x64-Setup-DEV.exe` | 105740715 | `0033ee706adfd9edcd29d2f87b5bddc5751bcbd2a6337125e09adb84d49d7870` |
| `Lone-Smart-Room-2.0.0-dev.7-x64-Portable-DEV.exe` | 105454515 | `2f16abc3d34ba50ef4a7c1ed83b1ee47714531bfe271625da6ee731022a6a060` |

[SHA256SUMS.txt](SHA256SUMS.txt). Identidade `com.lone.smartroom`, nome Lone Smart
Room. ASAR/FileVersion **2.0.0-dev.7**; ProductVersion numérico **2.0.0.0**, como no
fluxo anterior. Os invólucros NSIS/portátil são PE x86 com **payload aplicativo
x64**, verificado como machine 8664, conforme o empacotamento existente.

Os dois pacotes, o aplicativo e a ponte estão **NotSigned**. Mensagens genéricas
de signing no builder não são assinatura; tabelas PE e Get-AuthenticodeSignature
confirmaram a condição. Nenhuma proteção foi contornada. Uso local de
desenvolvimento; publicação e assinatura futura são etapas separadas.

## Inventário e integridade

- Electron **45.0.0**, builder **26.15.3**, Node de build **22.16.0** existentes.
- CPython **3.13.3**, snapshot do runtime local autorizado; **527** fontes stdlib
  em ZIP, `_pth` isolado e somente extensões/DLLs permitidas.
- Sidecar: **39 arquivos + manifesto**, 17 módulos Python de monitoramento
  incluindo `__init__`, dois entrypoints, ponte própria, recibo nativo e licenças.
- ASAR: **30 arquivos**; árvore externa: **114 arquivos**. Ambas as cópias
  embutidas equivalem ao aplicativo/sidecar inspecionados.
- SDK ADLX **1.4**, revisão `66557d410ce4c463f5f7106597d94f53dd84bc82`.
  DLL do driver, headers, helper, samples, hooks de ensaio, perfis, credenciais,
  certificados privados e dados de pareamento não entram no pacote.
- Pin do manifesto: `5963dfb94967850396da8f3744bf2f544f12c8f4c4e483a2b85825eaa0cc1761`.
- Executável da aplicação SHA-256:
  `83230a8511efd2d0b6383826456cd95c59d3324ac5b169d3265bfb549d4c2559`.
- ASAR SHA-256:
  `9d947532e65e369b206bafc9d38d552dcabdb695182a31f9ff43f1e6d90362bd`.

[Inventário completo](evidence/component-inventory.json),
[manifesto do monitoramento](evidence/monitoring-manifest.json),
[inspeção dos artefatos](evidence/artifact-inspection.json) e
[versão/recursos](evidence/package-inspection.json).

O build usou o adaptador existente que extrai o desinstalador estaticamente.
A guarda Node rejeita lançamento direto de artefatos gerados e APIs exec/execSync;
ferramentas locais de compilação/arquivo foram utilizadas normalmente. O recibo
confirma uma extração estática, sem executar o gerador/desinstalador resultante,
NSIS, portátil, Python empacotado ou aplicativo. Nenhuma publicação foi solicitada.
[Recibo do build](evidence/build-execution.json).

## Testes e inspeções

| Grupo | Resultado |
| --- | --- |
| Python básico/preservação/launchers | 133 aprovados |
| Python IPC protegido | 28 aprovados |
| Python ADLX/provedor, sessão, composição e admissão | 69 aprovados |
| Python bridge/diagnóstico com processos nativos mock | 59 aprovados |
| **Python total** | **289; zero falhas/erros/skips** |
| Node regressões anteriores e retomada | 526 aprovadas |
| Node segurança de empacotamento dev.7 | 23 aprovadas |
| **Node total** | **549; zero falhas/skips** |
| C++ self-test da fixture mock | **35 aprovadas** |
| Runtime: arquivos, stdlib, imports e modo application | **2323 verificações aprovadas** |
| NSIS/portátil: arquivos, PE/ASAR, recursos, segredos e manifesto | **288 verificações aprovadas** |
| Conferência adicional de recursos | **21 arquivos ASAR e 7 imagens ICO aprovados** |

Mocks cobrem restauração válida/inválida, erros repetidos, indisponibilidade
persistente, recuperação parcial/IPC, age_null, dados futuros/antigos/não finitos,
fronteiras 1,5/3/11 s, orçamento visual de 10 s, zero/null, bandeja, widget e saída.
A asserção originalmente falha segue **3/3 aprovada**, sem inverter expectativa.

Os testes IPC cobrem SID/identidade, ACL, rejeição remota, limites, timeout,
reconexão e limpeza com substitutos. Renderer/preload conservam CSP sem rede,
contextIsolation, sandbox, Node Integration desligado e API fixa de métricas e
janela, sem execução genérica. Nenhuma coleta real ou endpoint TCP foi criado.

O C++ foi exercitado somente pela fixture compilada existente, cujo hash e fonte
correspondem ao recibo, nunca pela DLL ADLX. A inspeção Python utilizou o
interpretador existente com imports do sidecar e auditoria que nega APIs nativas,
rede, Registro e subprocessos. Não valida fisicamente o Python empacotado.
[Resultados/ comandos](evidence/test-results.json).

Reprodução no ambiente existente: preparar payload novo, verificar payload,
executar regressões, build e inspeções. Os scripts recusam sobrescrever o payload
e o diretório de artefatos existentes; um novo build requer outro destino revisado.
Não se promete SHA idêntico de uma recompilação futura, apenas os hashes dos
arquivos efetivamente gerados e inspecionados nesta entrega.

## Licença, atualização e limitações

Conferência documentada em [LICENSE-REVIEW.md](LICENSE-REVIEW.md). A licença ADLX
original e os avisos acompanham o runtime sem alteração de seus termos. Não foi
criada/aceita EULA em nome do usuário nem liberada distribuição pública.

[Plano de atualização, backup e reversão](UPDATE-AND-RECOVERY.md): não executado.
Mesmo appId, destino, perfil e esquema de preferências; compatibilidade esperada
por equivalência dos componentes de persistência, ainda sujeita à futura
instalação e execução autorizadas. `runAfterFinish=false`, instalação assistida
por usuário, sem elevação, novo serviço, driver, tarefa ou autostart.

O pacote dev.7 **não foi validado fisicamente**. A validação de 35,98 s anterior
comprovou a correção no desenvolvimento, não o bootstrap deste novo pacote.
PDH continua opcional/intermitente. GPU depende de suporte do driver; mudança
do hash oficial fixado provoca recusa segura, sem fallback de DLL. ACL por SID
não isola completamente processos da mesma conta. Hashes não substituem
Authenticode nem impedem adulteração por quem pode reescrever aplicação e pins.

Não há nova medição de desempenho. A sessão isolada anterior registrou CPU média
conjunta **1,589%**, RSS médio **441,07 MiB**, pico **488,94 MiB**, incluindo startup
e capturas em apenas 36 s. Não comparar diretamente com a referência mais longa
0,529% / 454,22 / 480,73 MiB nem garantir consumo do pacote. Shared pages podem
ser contadas repetidamente. Travamento nativo pode exceder prazos; não há kill
automático, garantia absoluta de limpeza após crash ou proteção contra queda de energia.
TLS, Crashpad e encerramento gracioso do agente continuam pendências separadas.

## Preservação final

Conferência às **12:04 BRT / 15:04 UTC**:

- Instalação dev.6 (117 arquivos), perfil (77) e quatro backups anteriores iguais
  byte a byte ao início. Mais **80 arquivos de artefatos/runtimes anteriores** e
  **86 arquivos operacionais protegidos** preservados.
- Mesmos supervisor 5024, worker 18304 e redirectors esperados, identificados
  por imagem/argumentos/criação/cadeia, não apenas PID. Listener LAN único 8776.
- TLS 1.3, hostname/certificado/pin e status/apps HTTP 200; **zero grants e comandos
  pendentes**. Banco íntegro, identidades cifradas, esquema e revogações preservados.
  Nonces e last-seen das consultas podem evoluir; banco ativo não é comparado byte a byte.
- Run/RunOnce, Inicializar, serviços e firewall sem diferenças; sem processos
  Electron, monitoramento ou instaladores. Nenhuma confirmação física no Samsung
  foi solicitada, nenhum app Android alterado.
- Hash OneSettings/RefreshCache mudou novamente, sem tarefas criadas/removidas
  nem ator identificado. Observação **inconclusiva**, sem atribuição ao projeto
  ou intervenção na tarefa.

[Recibo de preservação](evidence/preservation-final.json). Binários e logs privados
ficam fora do Git; recibos sanitizados, avisos e planos ficam versionados.
O commit documental seguinte registra esta entrega; seu hash consta na resposta.
Árvore Git deverá terminar limpa, sem reescrita de checkpoints.

**Parada nesta etapa: nenhum instalador ou aplicativo empacotado será executado.**
