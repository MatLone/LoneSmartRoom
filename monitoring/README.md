# Monitoramento independente — fundação, etapa 1

Fundação autorizada a partir de `65340970bba7435cd2606900317a584d20ee9a9f`,
na branch `feature/ui-migration-preview`. **Sem implantação.**
Em 25/10 foram adicionados provedores básicos Win32 opt-in e testes com mocks;
a sessão física foi adiada pelo usuário após encontrar o agente já offline.
Detalhes e novo gate: [provedores básicos e diagnóstico](../docs/monitoring-basic-2026-10-25/README.md).
Não há CLI de coleta, autostart, serviço, endpoint TCP, named pipe aberto ou ligação
com o Electron/Android. Importar o pacote não inicia threads nem coleta dados.

## Componentes implementados

| Arquivo | Responsabilidade |
|---|---|
| `contracts.py` | Esquema v1, tipos imutáveis, unidades, proveniência, disponibilidade e validação numérica |
| `catalog.py` | 22 slots declarados para CPU/GPU/RAM/armazenamento/ventoinhas; não faz inventário |
| `collector.py` | Provedores injetados, agendamento, modo inativo, prazo de leitura, cancelamento e encerramento |
| `cache.py` | Última leitura e histórico circular por métrica; snapshots independentes e envelhecimento monotônico |
| `ipc.py` | Contrato de requisição/resposta, política de acesso e limites de leitura; transporte nativo ausente |

Arquitetura preparada:

```text
Provedores explícitos → Collector → MetricCache → LocalReadService
                                                   │
                                 adaptador Win32 futuro com ACL/autenticação
                                                   │
                                        Electron main futuro
```

Os provedores substitutos existem somente em `tests/monitoring/monitoring_fakes.py`.
São `data_kind=simulated`; snapshots que os contêm incluem `contains_simulated=true`.
Os números da fixture não representam este PC e não são enviados a interfaces.
Não existe descoberta/importação dinâmica de plugins ou carregamento por caminho.

`windows_basic.py` contém os algoritmos de CPU/RAM/volumes/I/O com backend injetado;
`windows_native.py` contém exclusivamente APIs de leitura e gestão de seus próprios
handles. Nenhuma DLL de sensor é carregada; as DLLs nativas só são resolvidas ao
construir explicitamente o backend. `basic_session.py` organiza a sessão limitada,
e o runner físico exige autorização explícita, prova dos mocks e marcador exclusivo.
Ele não foi executado nesta entrega.

## Contrato de leitura

Cada métrica informa ID, componente, rótulo, origem, unidade, proveniência,
valor, estado, validade, horário UTC da tentativa/leitura, idade monotônica e
intervalo programado. `generated_at` é o horário do snapshot, não renova
`collected_at`; `sequence` muda apenas ao publicar um lote no cache.

Disponibilidades: `available`, `warming_up`, `unsupported`, `unavailable`,
`permission_denied`, `error` e `stale`. Todas as condições sem valor válido retornam
**`value=null`**. Zero continua válido, inclusive fan em Zero RPM. Para erro antigo,
o motivo `error` é preservado e `stale=true` indica também a idade excessiva.

Unidades: percentual 0–100, Celsius, bytes inteiros, bytes/s e RPM inteiro.
Booleanos, strings, NaN, infinito, contagens negativas, IDs duplicados/desconhecidos,
horários sem UTC e valores fora dos limites do contrato são rejeitados. As faixas
numéricas são limites de validação, não limites térmicos de alerta do hardware.

O provedor recebe a lista fechada de métricas devidas e um `ReadContext` com início,
deadline e evento de cancelamento. Deve devolver um lote completo de observações
frescas, sem trocar IDs/unidades/origem. O coletor usa o início da leitura como
timestamp conservador, sem rejuvenescimento após uma chamada lenta. Um futuro SDK
que só entregue amostra já antiga deverá declará-la indisponível ou ganhar suporte
explícito ao timestamp de origem antes de ser integrado; não carimbar cache do SDK
como leitura nova. Não há média ou interpolação de valores ausentes.

Um lote malformado, incompleto, duplicado ou excessivo gera erro nas métricas
solicitadas, sem publicar parcialmente valores não validados. Exceções de permissão
recebem motivo próprio. Um gerador é consumido no máximo até `n + 1` observações,
onde `n` é o número solicitado; chamadas bloqueadas ainda exigem cooperação do provedor.

Os IDs `storage.system` e `fan.*` são slots a resolver, não confirmação de disco,
volume, placa-mãe ou ventoinha detectados. Rótulos i5-12400/RX 6750 XT/DDR4 vêm das
informações do usuário. Nenhuma capacidade RAM/VRAM é preenchida com valor presumido.
Novos discos/sensores poderão compor um catálogo validado em etapa autorizada.
Relações como usada + disponível = total pertencem ao futuro provedor de memória;
esta fundação valida os campos, não inventa medições derivadas entre lotes diferentes.

## Agendamento e limites

| Cadência | Ativo | Inativo |
|---|---:|---:|
| CPU, RAM, GPU/VRAM em uso e atividade/throughput de disco | 1 s | 5 s |
| Temperaturas e RPM | 2 s | 10 s |
| Capacidade/espaço e total VRAM | 60 s | 60 s |

`Schedule` é uma configuração local imutável fornecida na construção. Intervalos
aceitam 0,1–3600 s; o modo inativo não pode acelerar a coleta. A interface futura
chamará `set_active()` por um host confiável; o IPC atual não permite alterar estado
ou configuração. Não há conexão com a janela instalada para detectar atividade agora.

Por padrão, uma amostra disponível expira em três intervalos registrados na sua
coleta. Mudar para modo inativo não prolonga silenciosamente a validade da leitura
anterior. A primeira passagem é imediata, sem repetir uma fila de coletas perdidas
após pausas. Alteração do relógio civil não muda idade/cadência; regressão monotônica
é erro e não produz valores artificialmente recentes.

Catálogo: máximo 64 métricas. Histórico: até 120 amostras por métrica (configurável
para menos), máximo teórico 7.680 entradas; catálogo atual limita a 2.640. Não há
histórico em arquivo, banco, logs operacionais ou transporte. Diagnósticos em memória
têm 64 eventos máximos e códigos fixos/origem validada, sem texto de exceções,
caminhos, payloads ou credenciais.

## Encerramento e limitações

`request_stop()` solicita cancelamento; `stop(timeout)` espera a conclusão do lote
em andamento e chama `close()` de cada provedor uma vez. Novos lotes não começam
após a solicitação. Chamadas simultâneas de stop são idempotentes. Não há sockets,
processos filhos ou mutex do agente para liberar nesta fundação.

`StopResult` separa `stopped`, `clean` e `timed_out`. Um read/close que não coopere
retorna timeout: não é declarado sucesso e não há kill de thread/processo. Falha
de close termina a execução com `clean=false`. A thread da biblioteca é daemon como
última proteção do processo hospedeiro; um futuro host não deverá sair abruptamente
para contornar timeout. Provedores nativos potencialmente bloqueantes precisarão de
worker em processo próprio e política autorizada de recuperação; ainda não incluídos.

O encerramento deste coletor é independente do encerramento gracioso do agente.
Não importa launcher, não usa porta 8776 e não sinaliza processos operacionais.

## Testes reproduzíveis, exclusivamente simulados

Da raiz do repositório, usando o Python já existente, sem instalar nada:

```powershell
.venv/Scripts/python.exe -B scripts/test-monitoring-isolated.py
```

O runner bloqueia por audit hook sockets, operações de Registro, criação de
processos, shell/startfile e novos carregamentos ctypes. O bootstrap da biblioteca
padrão ctypes é feito antes do guard exclusivamente porque testes de preservação
antigos importam seus tipos; isso resolve os helpers Kernel32 do próprio Python,
sem consultar sensores ou chamar DPAPI. Não são usados certificados ou banco reais.

Resultado e metodologia: [relatório da etapa](../docs/monitoring-foundation/README.md).
Política de transporte futuro: [IPC-PLAN.md](IPC-PLAN.md).
