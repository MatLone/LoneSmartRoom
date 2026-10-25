# Provedores básicos e diagnóstico do agente offline — 25/10/2026

Branch `feature/ui-migration-preview`; preservados `16530d1` e `a956004`.
**Implementação e 133 testes simulados aprovados. Sessão física não iniciada.**
Código/testes no commit `33765ab`; documentação e evidências em commit subsequente.

Antes da coleta, a verificação encontrou o agente já sem processo/listener. O
usuário decidiu explicitamente: **“Adiar a coleta e diagnosticar o agente somente
em leitura”**. Nenhuma instância real do coletor ou do agente foi iniciada. Não há
valores reais de CPU, RAM, discos ou overhead a apresentar nesta entrega.

## Provedores implementados

| Módulo | Comportamento |
|---|---|
| `monitoring/windows_basic.py` | Algoritmos puros com backend injetado, catálogo básico, CPU/RAM/volumes/I/O |
| `monitoring/windows_native.py` | APIs Win32 x64 somente leitura; DLLs de sistema com busca restrita a System32, sem carga ao importar o módulo |
| `monitoring/basic_session.py` | Uma sessão de duração limitada, amostras, estatísticas, recursos do próprio processo e encerramento cooperativo |
| `monitoring/basic_validation.py` | SHA-256 dos fontes/testes para conferir que a versão executada passou pelos mocks |
| `scripts/test-monitoring-basic-isolated.py` | Suíte offline que bloqueia operação real de DLLs, Registro, rede e processos |
| `scripts/monitoring-basic-session.py` | Runner físico opt-in, flag explícita e marcador exclusivo; NÃO executado |

CPU usa deltas de `GetSystemTimes`, descontando idle do total kernel + user;
kernel já inclui idle. A primeira amostra, um contador reiniciado ou intervalo
sem variação ficam em aquecimento, com valor nulo. Erro invalida a base anterior;
recuperação exige novamente duas leituras.
[Microsoft: GetSystemTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes).

RAM usa uma chamada `GlobalMemoryStatusEx` por lote: utilizada = total físico
utilizável − disponível. Percentual deriva do mesmo lote, sem presumir 16 GB exatos.
[Microsoft: GlobalMemoryStatusEx](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex).

Volumes: enumera apenas letras montadas do tipo `DRIVE_FIXED`. Não varre arquivos,
não busca rótulos, seriais ou conteúdo, nem consulta volumes de rede/removíveis.
Volumes sem letra/pontos de montagem exclusivos não são cobertos nesta versão.
O catálogo admite até sete volumes fixos e 61 métricas; excesso interrompe a
preparação, sem omissão silenciosa.

Espaço usa `GetDiskSpaceInformationW`: total e livre físicos independentes de quota,
disponível à conta e unidades efetivamente utilizadas. A ocupação percentual usa
alocação utilizada / total físico; espaço reservado/pool e quota não são convertidos
automaticamente em ocupação. Bytes = unidades de alocação × setores/unidade ×
bytes/setor. Sem API suportada, retorna indisponibilidade; não presume total físico
a partir de informação limitada por quota.
[Função](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getdiskspaceinformationw),
[campos e semântica](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-disk_space_information).

I/O usa apenas três contadores English PDH fechados por volume: `Disk Read Bytes/sec`,
`Disk Write Bytes/sec`, `% Idle Time`, em `LogicalDisk`. Taxas continuam bytes/s.
Atividade é o complemento do idle validado, rotulado como **tempo ativo do volume**,
não medição física de cada SSD/controlador. Não usa `% Disk Time` como substituto.
Há validação de retorno da API, CStatus, valor finito/faixa e evolução dos dois
campos brutos. Primeira amostra e regressão/reinício do contador aquecem novamente;
sem contador ou leitura confiável, o valor fica nulo. Nenhuma ativação/reparação de
contadores é tentada.
[PDH raw](https://learn.microsoft.com/en-us/windows/win32/api/pdh/nf-pdh-pdhgetrawcountervalue),
[PDH formatado](https://learn.microsoft.com/en-us/windows/win32/api/pdh/nf-pdh-pdhgetformattedcountervalue).

O processo consulta somente seus próprios tempos CPU e working set/commit privado.
CPU é normalizada pela quantidade total de processadores lógicos. Commit privado
não é apresentado como RAM residente privada. O custo da coleta real permanece
não medido; a meta <0,5% não foi avaliada fisicamente.
[Microsoft: memória do processo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex).

Cadências preservadas: CPU/RAM/I/O 1 s, espaço 60 s; o runner básico não cria slots
de GPU, VRAM, temperaturas ou ventoinhas. Cache e tratamento de idade da fundação
permanecem. Não há IPC, integração Electron/Android, serviço ou autostart ativado.

## Testes e gate físico

```powershell
.venv/Scripts/python.exe -B scripts/test-monitoring-basic-isolated.py
```

**133 testes, zero falhas, zero erros, zero skips**. Incluem os 91 anteriores e
42 adicionais de provedores/ABI/sessão. Não foi necessário instalar dependências.
Os testes nativos usam substitutos de DLL/funções, com proibição de carregamentos
reais. A construção do backend, chamadas de token, geometria, PDH e descoberta de
volumes foram exercitadas somente com mocks; isso não comprova suporte físico.
Recibo sanitizado em [tests.json](tests.json).

São cobertos: unidades/conversões, memória coerente, quota versus ocupação,
estados iniciais CPU/I/O, reset e indisponibilidade de contadores, falha de leitura,
recuperação, idade/cache, cadências, estatísticas sem duplicar snapshots de espaço,
normalização do custo próprio, encerramento e allowlist explícita dos exports Win32.
Não foram executadas novas suítes de servidores HTTPS ou consultas à API real.

O runner físico confere hashes da versão aprovada pelos mocks, exige a flag
`--authorized-single-session`, rejeita token elevado e cria um marcador com modo
exclusivo antes de instanciar o backend. A coleta planejada é 80 s, com margem para
cleanup, sem repetição e sem sobrescrita. Timeout não é sucesso; não há parada forçada.
Uma API nativa bloqueada exige interromper e avaliar, não matar processos.

O marcador `physical-session-started.json` e o recibo `physical-session.json`
**não existem** nesta entrega: a sessão não começou. Não executar o runner com
base na autorização anterior, pois o usuário adiou expressamente o teste.

## Diagnóstico somente leitura do agente

Horários abaixo em America/Sao_Paulo (UTC−3). Os recibos preservam UTC/offset.

| Evidência | Resultado |
|---|---|
| Processos históricos 6396 e 17992 | Ambos ausentes na consulta direta |
| Processos Python do launcher/agente deste repositório | Nenhum encontrado |
| Listener 8776 | Nenhum; consulta CIM fora do sandbox retornou ausência de instância, não um erro de acesso |
| Último boot | **25/10/2026 00:03:58,500** (`03:03:58.500Z`) |
| Sessão manual anterior do agente | Iniciada 24/10 às 20:25:48 local; os cinco recibos de bootstrap antigos continuam no log |
| HKCU Run `LoneSmartRoomSecureAgent` | Presente e SHA-256 idêntico ao histórico; ainda usa `secure_agent.py` diretamente, não `agent_launcher.py` |
| Pythonw da venv | Arquivo presente; não executado |
| StartupApproved\Run, valor específico | Não encontrado nessa chave; isso não prova que a entrada foi desativada ou bloqueada |
| Logs novos de launcher | Nenhum após o bootstrap antigo; como Run não usa o launcher, essa ausência não prova falta de despacho do Run |
| Application 1000/1001/1002/1026 correlacionado a Python | Nenhum na consulta delimitada, máximo 100 eventos a partir de 24/10 20:20 local |
| Arquivos protegidos | `config.dpapi`, `server.crt`, `server.key`, `tls.dpapi` correspondem aos hashes históricos, sem exposição/descriptografia |
| Certificado público | Vigente; expira 23/10/2027 11:13:46 UTC |
| Banco | `quick_check=ok`, conexão SQLite somente leitura |
| Grants | **0**, contagem somente leitura |

O primeiro acesso CIM dentro do sandbox foi negado. A verificação foi repetida com
autorização de leitura fora do sandbox; o resultado offline foi confirmado. Essa
limitação inicial da ferramenta não é evidência de falha de permissões do agente.

O System contém eventos de boot/encerramento (12/13, 6005/6006), um 1074 às
00:03:18 com iniciador registrado `winlogon.exe` e reason code `0x500ff`, além de
41/6008 em boots anteriores dessa noite. Esses IDs, isoladamente, não identificam
a causa dos desligamentos anteriores nem quem os solicitou. Nenhuma ação de energia
foi executada nesta tarefa. Não se atribui a reinicialização ao agente ou coletor.

**Conclusão com alta confiança:** houve nova sessão Windows depois da execução
manual conhecida; não se pode esperar que os PIDs daquela sessão permaneçam.
O agente não está operacional atualmente e o teste físico do monitoramento não
foi iniciado. A entrada automática permaneceu na implementação direta antiga;
o launcher observável que foi validado manualmente nunca foi registrado em Run.

**Ainda inconclusivo:** se o Windows despachou a entrada Run neste login e o
`secure_agent.py` saiu no bootstrap, ou se a entrada não foi despachada. Não há log
persistente do bootstrap direto para distinguir as duas situações. A ausência de
evento Application não exclui exceção Python/encerramento sem crash nativo.
Não há evidência nova relacionando o problema a HMAC, certificados ou ao tratamento
TLS excessivo/ambíguo. Integridade de arquivos não substitui validação operacional.

Evidências reduzidas, sem valores de credenciais nem conteúdo de memória:
[agent-offline.json](agent-offline.json).

## Preservação e próximo procedimento

Sem alterações em agente, supervisor/worker, Run, firewall, serviços, tarefas,
certificados, pareamento, permissões, APK dev.7, Electron dev.4 ou backups. Nenhum
Steam/CS2, WoL, operação de energia ou correção TLS/encerramento executada.
O banco foi apenas consultado. Nenhum dashboard foi aberto ou novo perfil criado.

Estado final: **agente offline, porta 8776 sem listener; zero grants**. O Samsung
não foi consultado novamente; o antigo relato Conectado é histórico, não confirmação
atual. Um PC sem agente disponível não deve ser apresentado como PC desligado.

Recomendação para aprovação posterior: preparar uma recuperação manual única com
verificação de caminhos, conta, porta e versão explícita do launcher, e só então
iniciar o processo autorizado e validar HTTPS/Samsung. Não alterar Run junto com
essa prova. A migração futura do Run deve ser uma etapa própria e não é solução
comprovada para um Windows que não despache a entrada. Não iniciar nada nesta tarefa.

Retomar a sessão única de métricas básicas somente após decisão/autorização nova,
com agente em estado conhecido e verificação novamente recente. Não houve tentativa
real consumida, mas o adiamento explícito impede o início automático posterior.

Reversão de código: reverter o commit documental e depois `33765ab`, após revisar
alterações posteriores; não usar reset --hard ou apagar perfis/recibos. Não há
instalação, dependência ou configuração operacional a restaurar. Preservar recibos
em `.cache/validation/monitoring-basic-2026-10-25/` e os checkpoints anteriores.
