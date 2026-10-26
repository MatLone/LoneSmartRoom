# Autodiagnóstico — leitores passivos e primeira tentativa

**Resultado: validação física incompleta, interrompida com segurança.** Uma única
sessão de **0,756 s** foi executada, dentro do teto de 60 s. Não houve consulta
HTTPS autenticada, início de aplicativo/coletor/ADLX ou repetição da sessão.
O agente não foi declarado em falha nem reiniciado.

## Implementação

- `diagnostics/windows_readers.py`: inventário local por CIM, identidades nativas
  retidas por handles com direitos de consulta/sincronização, SID/sessão/elevação,
  criação, imagem, parentesco e argumentos fixos; listener 8776; namespace de
  pipes; banco SQLite `mode=ro`; leitor limitado dos logs existentes; GET fixo de
  status com certificado/hostname/pin antes do envio da identidade/HMAC.
- `diagnostics/windows-census.ps1`: script local fixo, sem alteração de Registro,
  firewall ou processos. Lê somente a entrada Run do agente. Linhas de comando e
  caminhos privados ficam transitoriamente na memória; não entram nos recibos.
- `diagnostics/passive.py`: sessão única explícita, duas consultas de status no
  máximo, sem retry. Reserva tempo para conferências finais e fechamento dos
  próprios handles. Não solicita controle ou encerramento de processos.
- Contrato/reducer/apresentação: origem `observed` explicitamente habilitada;
  simulação continua sendo o padrão. Não mistura recibos simulados com reais.
  A apresentação observada distingue **Saudável, Indisponível, Desatualizado,
  Falha e Não verificado**. Falha de verificação não comprova falha do serviço.
- `scripts/run-diagnostics-passive.py`: exige hashes dos fontes testados,
  recibo de preservação e `--once`; cria marcador exclusivo antes do acesso real.
  Não faz parte da inicialização do Electron nem do agente.

Não foi instalado nada e não há integração operacional com o dashboard.

## Evidências reais da única sessão

Horário do inventário: **2026-10-26 19:50:22 UTC (16:50:22 Brasília)**.
Ver [session.json](session.json) e [validation-summary.json](validation-summary.json).

| Componente | Observado | Interpretação permitida |
|---|---|---|
| Cadeia Python | PIDs 19996 → 5024 → 20352 → 18304 vivos, mesma conta/sessão, sem elevação; imagens e criação conferidas por handles | Argumentos não aprovados pelo leitor inicial; identidade completa **Não verificada** |
| TCP 8776 | Um listener, PID 18304, endereço privado específico | Presença confirmada; não comprova HTTPS autenticado |
| HTTPS | Nenhum GET executado; gate de identidade bloqueou o avanço | **Não verificado** nesta sessão, sem inferir offline ou PC desligado |
| Electron/monitoramento | Zero processos identificados do aplicativo e monitoramento | Coletores/ponte **Indisponíveis por inatividade normal**, sem falha comprovada |
| Named Pipe | Consulta do namespace sem resultado verificável (`null`) | **Não verificado**; não foi aberta conexão com o pipe |
| Últimas amostras | Sem interface passiva autorizada para acessar o cache em memória | Valor, idade e disponibilidade de sensores não foram inventados |
| Inicialização | Entrada Run presente; hash igual ao histórico preservado | Origem/despacho pelo Windows **Não verificados**; logs não foram alcançados nesta tentativa |

O inventário é uma fotografia desse horário, não uma prova de disponibilidade
atual permanente. Não houve verificação física nova do Samsung. O banco foi
conferido novamente na preservação posterior: íntegro, identidade/permissões
inalteradas e **zero grants**. A atividade da cadeia/listener foi observada no
início; autenticação final não foi executada, pois a tentativa foi interrompida.

## Defeito do leitor e correção exclusivamente isolada

O código testado na sessão era `86ab555`, com **146 testes** aprovados antes da
execução. O parser só reconhecia `pythonw.exe caminho-do-launcher [--worker]`.
O bootstrap validado e documentado usa **`-I -B` antes do script**, inclusive na
criação do worker em `agent/windows/agent_launcher.py`.

Essa omissão é um defeito determinístico do leitor, coerente com os quatro
processos rejeitados. A linha de comando bruta não foi persistida: não se pode
afirmar, a partir do recibo sanitizado sozinho, todos os tokens de cada processo.
Não há evidência de adulteração do agente ou de falha TLS nesta sessão.

O commit **`3ee871c`** reconhece estritamente esse formato documentado, além do
formato simples já previsto. Continua rejeitando `-c`, `-m`, opções extras,
outros scripts/interpretes e argumentos arbitrários. Também evita apresentar
identidade não confirmada como uma divergência comprovada/Falha.

**A correção passou em mocks, mas não foi validada novamente no ambiente real.**
O marcador da tentativa permanece preservado. Nenhum arquivo do agente foi
substituído. `observed-report.json` e `observed-view.json` são uma interpretação
offline do inventário capturado, usando seu horário original; não representam
uma segunda sessão nem a execução física do leitor corrigido.

## Testes e recursos

- **150 testes finais de diagnóstico aprovados**, sem falhas/erros/skips.
  Incluem os 96 testes anteriores e 54 cenários dos leitores/orquestração.
- **175 regressões adicionais aprovadas**, somente mocks: contrato/cache,
  provedores básicos, Named Pipe/ciclo de vida, ADLX instrumentado, preservação
  WoL e executores Steam/CS2 substituídos.
- Audit hook bloqueou novas operações de rede, Registro, carregamento/chamadas
  nativas e criação de processos durante os testes; o bootstrap padrão do Python
  (`ctypes`/SSL) ocorre antes do hook, sem inicializar leitores ou ADLX.
- O teste de SQLite revelou conexão de fixture não fechada: leitores agora usam
  `contextlib.closing`, com regressão de integridade/ausência de escrita.
- Nesta tentativa curta, RSS final do leitor Python: **26,438 MiB**. Delta do
  contador de CPU: **0 s na resolução observada**; isso não significa custo
  total nulo. PowerShell/CIM transitórios não foram contabilizados. Não houve
  tempo de observação adequado para estimar médias/picos ou consumo contínuo.
- Nenhum processo de inventário permaneceu ativo ao terminar; handles de
  consulta foram fechados. Nenhum processo de monitoramento foi criado.

Recibos: [tests-summary.json](tests-summary.json),
[regressions-summary.json](regressions-summary.json),
[evidence-sha256.json](evidence-sha256.json).

## Preservação

**1.338 arquivos protegidos e quatro arquivos de runtime permaneceram idênticos**
ao baseline anterior, abrangendo instalação Windows, perfil, backups, código
protegido, assets Android e arquivos de recuperação. SQLite `quick_check` OK;
identidades, credenciais cifradas e permissões preservadas por hashes lógicos.
Nenhum segredo ou linha de comando privada foi incluído neste relatório/Git.

O APK Android dev.9 permanece com SHA-256
`92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2`.
Não houve acesso ao Samsung, instalação, atualização, coleta física de sensores,
novo grant, comando operacional ou alteração do agente/Run/firewall.

## Limitações e próxima autorização

1. É necessária **nova autorização para uma nova sessão passiva**, com evidência
   independente, para validar o parser corrigido e alcançar os gates HTTPS.
   Não apagar/reutilizar o marcador desta tentativa para realizar retry oculto.
2. O pipe valida o intermediário originalmente criado pelo Electron. Outro
   cliente não deve ser aceito ampliando ACL/allowlist. Namespace presente não
   comprova peer, contrato, saúde do IPC ou validade de amostras.
3. O cache atual fica em memória. Sem aplicativo aberto/interface de leitura
   autorizada, sensores não podem ser homologados pelo autodiagnóstico.
   A consulta do namespace do pipe também ficou inconclusiva nesta tentativa.
4. Logs de bootstrap/Run não provam despacho após login. Não alterar o launcher
   ativo para fabricar essa evidência; origem e correlação de login ficam pendentes.
5. Deadlines são cooperativas: consultas locais podem bloquear no sistema.
   Em timeout não há kill automático; a sessão é incompleta e qualquer processo
   próprio ainda ativo deve ser registrado, nunca ocultado como sucesso.
6. ACL por usuário não isola contra código malicioso da mesma conta. Handles,
   argumentos permitidos e hashes não atestam o conteúdo da memória do agente.
7. **TLS 10054 continua pendente**. Ver [TLS-PLAN.md](TLS-PLAN.md). Não houve
   reprodução adversarial nem correção operacional nesta tarefa.

## Plano de integração visual futura (não implementado)

Após validar os leitores e receber autorização separada, o processo principal
do Electron poderá consumir somente um resumo versionado e limitado do módulo.
O preload deve expor exclusivamente leitura de estados/horários, sem caminhos,
credenciais, acesso genérico ao pipe, Registro ou execução de processos.
Renderer com `contextIsolation` e sem Node, cartões das cinco categorias,
inatividade normal explícita, última comunicação autenticada separada de
presença de listener e amostras antigas nunca renovadas pelo polling da UI.

Para monitoramento já aberto, preferir projetar o estado validado em memória do
host existente, em vez de conectar um novo cliente ao Named Pipe. Cadência
baixa/configurável, pausa com painel oculto e TTL original preservado. Sem
reparo automático, nova identidade desktop ou comandos de energia/aplicativos.
TLS pendente impede declarar pronto um novo cliente autenticado operacional.

## Commits e reversão

- `86ab555`: leitores e primeira bateria simulada.
- `3ee871c`: parser documentado e regressões pós-tentativa, sem retry físico.
- Commit documental posterior: resultados, preservação e plano TLS separados.

Não há implantação a reverter. Em uma branch de revisão, reverter os commits de
implementação na ordem inversa, preservando este relatório e a evidência da
tentativa. Não tocar na instalação, APK, perfil, banco, certificados ou backups;
não reiniciar o agente. Commits aprovados `a46ada6`, `c0bce81`, `b2b5e2c`,
`75d00eb` e `e6f2897` permanecem ancestrais.
