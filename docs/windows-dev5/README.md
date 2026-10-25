# Windows 2.0.0-dev.5 — preparação da distribuição

Preparação autorizada em **25/10/2026**, na branch `feature/ui-migration-preview`,
a partir de `216dcba`, preservando `3abd308` e os checkpoints anteriores.
**Esta entrega não instala nem executa o aplicativo empacotado.** A instalação
Windows permanece dev.4; não houve sessão física de sensores, Electron, NSIS ou portátil.

## Alterações

- Percentuais positivos inferiores a 0,1% aparecem como **`<0,1%`**. Zero real
  permanece `0%`. A formatação não altera o valor original do contrato.
- Taxas positivas inferiores à resolução decimal também não aparecem como zero;
  uma taxa válida zero continua **`0 bytes/s`**.
- A barra dos volumes é identificada como **Ocupação do disco**. Capacidade,
  disponibilidade, leitura, gravação e **Atividade PDH** aparecem separadamente.
  Atividade nula/inválida/desatualizada aparece como **Indisponível**. A validade
  da capacidade não implica validade da atividade opcional.
- Dashboard e indicadores compactos usam o mesmo modelo validado. Leitura antiga
  perde seu valor numérico; não é atualizada artificialmente por uma nova renderização.
- A versão empacotada prepara coleta durante a vida do aplicativo, em lugar do
  limite de 70 segundos das sessões de desenvolvimento. Nada inicia com o Windows.
- Identidade visual, abas, painéis, navegação, Tray, posições/dimensões por modo,
  instância única e esquema 1 das preferências foram preservados. O X continua
  solicitando saída normal; minimizar automaticamente para bandeja não foi habilitado.

## Arquitetura e ciclo de vida

```text
APIs Windows somente leitura → provedores/cache do coletor Python
                ↕ Named Pipe local protegido v1
intermediário Python próprio ↔ stdio privado ↔ Electron main
                → preload restrito → dashboard / widget
```

O processo principal utiliza caminhos fixos em `resources/monitoring`, executável
absoluto, argumentos internos fixos e `shell=false`. Um identificador aleatório
interno distingue a sessão do pipe. O renderer não seleciona caminhos, argumentos,
pipe, PID, duração, provedor nem comandos. `contextIsolation`, sandbox,
`nodeIntegration=false`, CSP sem conexões e validação de remetente permanecem ativos.

A aplicação empacotada verifica versão, hash do manifesto e todos os arquivos do
payload antes do lançamento; rejeita arquivos extras e links/redirecionamentos.
O hash esperado fica no ASAR. O intermediário verifica o processo Electron pai por
handle retido, PID, imagem, SID, sessão, ausência de elevação e liveness. Coletor e
intermediário verificam suas respectivas identidades. O bloqueio de instância do
Electron precede a criação do monitoramento. Não há fallback para Python do agente,
PowerShell, CMD, URI, processo genérico ou cliente HTTPS operacional.

Foi mantido o Named Pipe nativo validado: DACL explícita da conta, rejeição remota,
primeira instância, handles de processos esperados, SID/sessão/imagem/elevação,
protocolo v1, requisição de 256 bytes, resposta de 128 KiB, timeout transacional
de 1,5 segundo e limite de duas requisições/s com burst de quatro. O namespace
interno histórico `Dev.v1` foi conservado para preservar o transporte validado;
ele não publica serviço de rede. Não existe endpoint TCP/HTTP novo.

O main solicita apenas snapshots fixos a cada segundo, com uma requisição pendente
por vez. CPU, RAM, I/O e atividade conservam a cadência básica de 1 s; capacidade
dos volumes, 60 s. Validade é independente por métrica; o modelo invalida leituras
com idade igual ou superior a três intervalos. A primeira leitura de CPU/I/O exige
aquecimento. Não foram adicionados sensores de GPU, temperaturas, VRAM, RPM ou FPS.

Falha de integridade/inicialização do coletor deixa o dashboard aberto e indica
indisponibilidade. Desconexão transitória pode reconectar ao mesmo worker, sem
criar processos redundantes. Não há respawn automático se um componente morrer;
recuperação depois desse caso requer futura reabertura autorizada da aplicação.

Ao sair pelo X ou pela bandeja, o main encerra o stdio que possui; o intermediário
fecha o canal de vida do seu worker. O coletor interrompe o agendamento, aguarda
suas operações, fecha consulta PDH/pipe e informa a saída. O intermediário aguarda
o worker efetivamente terminar. O Electron só completa a saída após essa confirmação.
Solicitações simultâneas de saída são agregadas. Não se usa encerramento forçado.
Se o prazo de 6,5 s expirar, o aplicativo **não informa sucesso nem desaparece**:
restaura a janela e preserva a bandeja para decisão do usuário. Uma conclusão real
posterior permite solicitar saída novamente. Monitoramento e agente HTTPS possuem
ciclos de vida separados.

**Limites:** ACL e checagem de processo não isolam malware sob a mesma conta;
os hashes locais também não substituem assinatura Authenticode nem protegem contra
alguém que possa modificar simultaneamente ASAR e payload. Uma chamada de kernel
que não finalize pode prolongar o encerramento; não há garantia de saída forçada
em prazo fixo. Esses casos foram exercitados com substitutos; a versão empacotada
ainda precisa de validação física autorizada. Não se declara comprovada a ausência
de órfãos em todos os cenários de crash/queda de energia.

## Runtime e empacotamento

- Electron **45.0.0**, electron-builder/app-builder-lib **26.15.3**, Node **22.16.0**
  já disponíveis. Nenhum `npm install`, `npm ci`, `pip`, download ou driver novo.
- Snapshot local do CPython **3.13.3**, já usado nas validações anteriores: 31 arquivos
  de payload, incluindo 527 fontes da biblioteca padrão num ZIP, módulos básicos
  de monitoramento, scripts fixos, DLLs necessárias e licença do Python.
- Este é um snapshot controlado da instalação local validada, **não** o pacote
  embeddable oficial baixado. Os binários são comparados byte a byte com a origem.
- Busca isolada por `python313._pth`, sem `import site`, dependências de usuário,
  `site-packages`, Registry/PYTHONPATH ou venv externa. ZIP sem compressão interna
  evita depender de zlib no bootstrap; NSIS/portátil comprimem o payload externo.
  A resolução por `._pth` segue a [documentação oficial do Python](https://docs.python.org/3.13/using/windows.html#pth-files).
- O payload não inclui testes/provedores fictícios, agente HTTPS, identidades,
  certificados, banco de pareamento, perfis, dumps ou arquivos operacionais.
  Modo simulado é recusado no payload de produção.
- Metadados preservados: **Lone Smart Room**, `name=lone-smart-room`,
  **`appId=com.lone.smartroom`**, x64 e recursos oficiais de marca. Os wrappers
  NSIS seguem o bootstrap padrão; a arquitetura do payload é verificada separadamente.
- Instalador assistido por usuário, sem elevação, sem execução ao concluir,
  sem criação de serviços, tarefas, firewall ou inicialização automática.
  Instalação anterior exige confirmação explícita; modo silencioso é recusado.
- **Sem assinatura Authenticode do aplicativo/instalador.** Mensagens genéricas
  “signing with signtool” do builder não comprovam assinatura. Não contornar
  SmartScreen, Defender ou política de execução.

O procedimento de compilação usa `scripts/prepare-monitoring-payload.py` e
`scripts/build-windows-distribution.cjs`, com a toolchain local. O segundo bloqueia
execução de EXEs gerados e usa extração estática do uninstaller NSIS, sem executar
o gerador intermediário. Não usar o comando genérico de distribuição no lugar
dessa rotina auditada. Entradas existentes não são sobrescritas: futuras builds
devem utilizar outro diretório revisado e manter seus manifestos.

O manifesto do payload é fixado em `apps/windows-ui/monitoring-package.json`.
Fontes, dependências e hashes permitem conferir/reconstituir a entrada da build;
não foi demonstrada reprodução bit a bit do NSIS, que também possui metadados de
empacotamento. A revisão de atualizações de manutenção do Python é uma tarefa
futura separada; esta entrega não atualiza o runtime validado silenciosamente.

## Verificações desta entrega

- **133 testes Python básicos**, cobrindo contratos, cache, CPU/RAM/discos,
  API nativa simulada e regressões WoL/Steam/CS2.
- **28 testes Python** de IPC/ciclo de vida, incluindo os sete novos testes de
  execução contextual e encerramento. Sem skip, falha ou chamada nativa de sensores.
- **296 verificações Node**, em seis suítes: janela/preload, Tray/persistência/
  instância única, contrato/host, integridade/ciclo de vida, renderer real com DOM
  substituto e política de distribuição. Não houve Chromium/GUI de teste nesta etapa.
- **2.278 verificações offline** do runtime: hashes, origem, PE x64, biblioteca
  padrão, sintaxe e importação de módulos pelo interpretador existente. O executável
  Python incluído no pacote não foi executado. Importação não constrói provedores reais.
- A inspeção final dos pacotes e os resultados de preservação estão em `evidence/`.
  A guarda do índice Git verifica padrões de segredos e a bridge WoL preservada.

**408 verificações offline dos dois pacotes** e inspeção adicional de 15 recursos
ASAR/sete imagens do ícone PE passaram. Os 30 arquivos do ASAR correspondem às fontes;
o payload de monitoramento dos dois pacotes corresponde ao manifesto revisado.
Authenticode confirmou `NotSigned` para NSIS, portátil e aplicativo. Os wrappers
são PE x86, contendo o aplicativo/runtime **x64**, como no fluxo NSIS anterior.
O ASAR e o campo FileVersion identificam dev.5; o ProductVersion numérico do
executável Electron permanece `2.0.0.0`, como compatibilidade do formato PE.

A primeira tentativa produziu arquivos intermediários, mas falhou ao iniciar o
compilador NSIS: `spawn UNKNOWN`. Eles e seu log foram preservados. A consulta de
versão ao mesmo compilador existente funcionou com permissão apropriada de execução;
a segunda tentativa usa diretório distinto. Não se alterou proteção do Windows.
Essa falha de compilação não é um crash do aplicativo nem evidência de falha TLS.

## Artefatos prontos — NÃO EXECUTAR sem autorização

Diretório absoluto:
`<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\windows\desktop-dev5-monitoring-distribution-attempt2`

| Pacote | Tamanho exato | SHA-256 |
|---|---:|---|
| `Lone-Smart-Room-2.0.0-dev.5-x64-Setup-DEV.exe` | 105.525.755 bytes | `fe616c66c71f30f7d6c220b49864b60b6aba5cbd4c6ee0a14a76763ddf776c49` |
| `Lone-Smart-Room-2.0.0-dev.5-x64-Portable-DEV.exe` | 105.239.630 bytes | `7645daefb687e3f69af58971583258b333160a8e2f9524b406c3fb098b29b8aa` |

Hashes também em `SHA256SUMS.txt`. Manifesto do runtime:
`ed179b40d0adeae54a33fdf293a2f64117ebab0e2abadf15bdf114537da78f52`.
O diretório da primeira tentativa foi preservado separadamente; ele **não** é a
distribuição aprovada. A segunda tentativa completou NSIS e portátil, com exatamente
uma extração estática de uninstaller e zero execuções de artefatos gerados.

## Estado preservado

Leitura final em **25/10/2026, 10:30 UTC**:

- Supervisor **400** e agente **8680** conservam imagem, proprietário, parentesco
  e horários de criação esperados desde a recuperação anterior. Listener único
  **8776 → 8680**, sem processo de monitoramento residual.
- Dois GETs fixos autenticados (`/v2/status`, `/v2/apps`): **200**, **TLS 1.3**,
  hostname/cadeia e pin do certificado validados antes de enviar autenticação.
  Identidade existente usada apenas em memória; nenhuma identidade foi criada.
- **Zero grants, zero comandos pendentes**, banco íntegro, identidades cifradas,
  esquema e revogações preservados. Nenhum comando operacional foi enviado.
- **239 arquivos protegidos fora da UI** sem divergências. Fontes do agente e
  Android não diferem do checkpoint. A bridge Kotlin WoL mantém a implementação
  preservada; não houve teste físico WoL nem alteração do Samsung nesta etapa.
- Instalação dev.4: **77 arquivos**; perfil de produção: **76 arquivos**;
  backups pré-dev.3: **341 arquivos**, pré-dev.4: **75 arquivos**, contando seus
  metadados. Comparação SHA-256 antes/depois sem diferenças.
- Hashes da entrada Run e das regras de firewall relevantes inalterados.
  Não houve instalação, criação de serviços/tarefas, mudanças de rede ou drivers.
- Não houve nova confirmação física no Samsung; confirmou-se a disponibilidade
  do agente para a identidade já pareada, sem alterar o aplicativo Android.

Inventários privados e dados operacionais ficam fora do Git. As evidências públicas
contêm resultados, hashes de fontes/artefatos e identidades de processos, sem
senhas, chaves privadas, segredo HMAC, tokens ou conteúdo do banco.

## Desempenho e limites conhecidos

Não houve medição física da dev.5. A sessão aprovada anterior é somente referência:
CPU conjunta média **0,4613%**, RSS somada média **441,25 MiB**, pico **463,43 MiB**.
Páginas compartilhadas podem ser contadas mais de uma vez na soma. Não há garantia
de consumo idêntico na versão empacotada ou em sessões prolongadas.

PDH permanece opcional. Na sessão anterior, leitura/gravação tiveram 100% de
validade após aquecimento; atividade C: **95,24%**, D: **52,38%**. Não foi adicionado
fallback e os motivos exatos de cada indisponibilidade continuam sem comprovação.
Preservam-se nulos, erros e aquecimento; nenhuma métrica substitui outra.

A pendência TLS sobre corpos excessivos/ambíguos e a validação física do
encerramento gracioso do agente continuam separadas e não foram corrigidas aqui.
O Electron continua sem cliente autenticado operacional para o agente. Nenhum grant
desktop ou do Samsung é criado pela instalação ou pelo monitoramento.

## Atualização proposta dev.4 → dev.5 — NÃO EXECUTADA

1. Obter autorização específica para a instalação. Inventariar a dev.4 e confirmar
   que ela foi encerrada normalmente pela bandeja, sem processos residuais.
2. Fazer **novo backup protegido** do perfil de produção em
   `%APPDATA%\Lone Smart Room` e dos arquivos instalados, fora do Git e do destino
   de instalação. Calcular SHA-256, verificar integridade/ACL e registrar arquivos
   eventualmente bloqueados sem forçar cópia inconsistente. Conservar todos os
   backups e pacotes anteriores, inclusive `Windows-before-dev4-20261024T174801Z`.
3. Conferir os hashes da dev.5, condição de assinatura e destino
   `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room`.
   Manter `appId` e perfil existentes. Não importar perfil de desenvolvimento.
4. Executar somente o NSIS assistido autorizado, confirmar substituição de arquivos
   e **não abrir o aplicativo ao concluir**. Se houver bloqueio de segurança, parar.
   Não usar o portátil como substituto do instalador.
5. Inspecionar versão/recursos/hash dos arquivos sem abrir o app. Comparar o perfil
   com o backup, verificar ausência de autostart/serviço/firewall e preservar o agente.
6. Solicitar autorização separada para a primeira execução da dev.5: uma sessão
   limitada com sensores básicos, Tray, widget, reconexão, encerramento normal e
   medição por componente. O monitoramento inicia nessa abertura, não na instalação.

## Reversão proposta — NÃO EXECUTADA

- O sistema instalado não exige reversão agora: dev.4 e perfil não foram alterados.
- Código: em árvore limpa, reverter os commits de implementação em ordem inversa
  com `git revert`, após decisão do usuário. Não usar reset destrutivo nem apagar
  os pacotes, evidências e checkpoints. Conservar a documentação histórica.
- Se uma futura instalação apresentar problemas, encerrar normalmente a dev.5 e
  conferir que seus próprios componentes saíram; não tocar no agente HTTPS.
- Preservar primeiro o perfil corrente e comparar com o backup anterior. A dev.5
  mantém o esquema 1 de preferências da dev.4 e não migra banco de credenciais;
  isso não garante automaticamente qualquer downgrade de dados futuro.
- Retorno ao NSIS dev.4 preservado depende de autorização e de revisão da aceitação
  de versão anterior pelo instalador. Não executar silenciosamente, desinstalar para
  contornar erro nem apagar userData. Restaurar perfil/arquivos somente quando
  necessário, autorizado e com o aplicativo encerrado, verificando os hashes.
- A versão portátil preserva a mesma identidade/perfil por padrão. Não foi testada
  fisicamente nem é recomendada para execução paralela com a instalação normal.

**Parada:** instalação e primeira execução física dependem de novas autorizações.

## Commits e recuperação do código

- `c368c4e`: precisão visual e distinção entre ocupação e atividade, com teste do renderer.
- `74d942e`: contexto de execução, integridade e encerramento dos componentes próprios.
- `0a73b70`: versão dev.5, runtime privado fixado e empacotamento/inspeções isoladas.
- A documentação e as evidências são registradas em commit posterior separado.

`216dcba` e `3abd308` continuam ancestrais da branch. Para retornar o código ao
checkpoint, uma proposta não destrutiva é reverter `0a73b70`, `74d942e`, `c368c4e`,
nessa ordem, em árvore limpa e após autorização. Essa operação não altera a instalação
dev.4, não apaga os artefatos gerados e não deve tocar no agente. A reversão não foi
executada. Fontes e evidências aprovadas anteriores permanecem disponíveis.
