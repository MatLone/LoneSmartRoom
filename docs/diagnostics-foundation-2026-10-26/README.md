# Fundação de autodiagnóstico — desenvolvimento isolado

Implementação independente da interface Android e dos aplicativos instalados. Commits `2055a40` e `4ce62b8`; checkpoint anterior `29d12a6` preservado. **Há somente provedores simulados, sem sondas reais, reparos ou integração operacional.** O [exemplo](SIMULATED-example.json) é uma fixture com relógio fixo, não um diagnóstico deste computador.

## Arquitetura implementada

`SimulatedProvider → Probe v1 → DiagnosticEngine → cache limitado → relatório sanitizado v1`

- `diagnostics/contracts.py`: componentes e resultados enumerados, timestamps UTC/monotônicos, fatos tipados e allowlist de campos. Rejeita texto livre, portas diferentes de 8776, números usados como booleanos, clocks não finitos e versões incompatíveis.
- `diagnostics/engine.py`: redutor puro e cache de última evidência por componente. Nenhum socket, subprocesso, arquivo, serviço, Registro ou temporizador de polling. `collect()` consulta somente os provedores injetados; `snapshot()` apenas calcula a visão atual.
- `diagnostics/simulated.py`: filas substitutas limitadas a 64 frames; no máximo oito provedores distintos. Iteradores são limitados antes de materializar para impedir consumo ilimitado. Os relatórios têm no máximo oito verificações e 16 KiB; não existe histórico crescente.
- `diagnostics/demo.py`: exemplo reproduzível que imprime JSON explicitamente marcado `simulation:true`. Não inspeciona o computador.

O contrato diagnóstico v1 é separado do contrato de métricas v1 existente; nenhum campo do monitoramento operacional foi alterado. Não houve mudança de Named Pipe, renderer, preload, agente ou executores.

## Evidências e conclusões permitidas

| Componente | Conclusão preparada |
|---|---|
| HTTPS | Só fica saudável com resposta, autenticação e identidade TLS confirmadas; sem resposta é serviço offline, sem inferir energia do PC |
| Listener | Presença em 8776 exige identidade esperada; listener presente não prova HTTPS autenticado |
| IPC | Conexão, identidade do peer e versão do contrato precisam estar válidas |
| CPU/GPU/RAM | Processo ativo não basta: amostra deve estar válida e não desatualizada |
| Ponte ADLX | Execução, verificação da biblioteca e validade da amostra são evidências distintas |
| Inicialização | Separa configuração, login observado, despacho e sucesso do bootstrap; falta de despacho é hipótese inconclusiva, não causa comprovada |

Estados possíveis: `healthy`, `offline`, `unknown`, `unavailable`, `unsupported`, `error`, `stale`. O relatório mantém origem simulada, horário, idade, validade, código fixo e última comunicação HTTPS confirmada **pela fixture**. Não há valores numéricos de hardware neste contrato nem substituição de ausência por zero.

Exceções são convertidas em códigos como `provider_failure` e `provider_timeout`; seus textos, caminhos e payloads não são publicados. A última comunicação conhecida não é renovada por erro, nova consulta do cache ou ausência de frame. High-water marks impedem que um frame anterior a uma falha recupere artificialmente a saúde. Timestamps futuros e regressão monotônica são rejeitados; regressão UTC não fica mascarada por uma idade monotônica positiva.

As observações diagnósticas GPU/ADLX usam 3 s em atividade e 11 s em inatividade. Isso **não altera nem reimplementa a admissão nativa de frames ADLX de 1,5 s**, ou o fluxo visual Atualizando/timeout de 10 s já existente. Um futuro adaptador deverá receber a validade do monitoramento aprovado, sem tornar uma amostra antiga válida ao consultar seu estado.

## Testes

- **44 testes isolados aprovados**, com audit hook que proíbe rede, Registro, carregamento de DLLs e execução de processos externos.
- **206 testes Python aprovados na suíte final completa**, incluindo os 44 acima, preservação Android e regressões existentes. A suíte completa usa fixtures TLS em loopback e processos substitutos; não executa comandos reais.
- **133 regressões de monitoramento com mocks** aprovadas; sobrepõem parte da suíte geral e não devem ser somadas como casos únicos.
- Regressões Windows apenas com substitutos: **65** verificações da retomada GPU, **23** de manutenção/reconexão, **100** de bandeja/ciclo de vida e **54** de política de janela/preload. Nenhum Electron de produção ou sensor real foi iniciado.

Cobertura inclui credibilidade de HTTPS/listener/IPC, amostras indisponíveis e antigas, erro/recuperação, limite de idade, UTC/monotônico, exceções sanitizadas, último sucesso, rejeição de versão/tipos/campos, filas e cache limitados, relatório imutável em relação ao cache e distinção entre despacho e bootstrap.

Uma invocação inicial usou nome de arquivo de teste inexistente (`MODULE_NOT_FOUND`); nenhuma suíte foi executada por essa chamada. Os testes efetivos `electron-tray.cjs` e `electron-window-policy.cjs` passaram em seguida. Nenhuma falha de produto foi ocultada ou corrigida modificando produção.

## Limitações explícitas

- Não há leitura real de processos, portas, HKCU Run, logs, TLS, pipe ou sensores **pelos provedores desta fundação**. Todas as evidências deles são simuladas. As verificações de preservação abaixo são ferramentas privadas de auditoria existentes, não novos adaptadores operacionais.
- Não existe interface de autodiagnóstico no Android ou Electron instalado; não foi criado endpoint de rede, pipe ou canal de comandos.
- O reducer não autentica uma conexão por conta própria: um futuro adaptador autorizado deverá validar TLS/pin/HMAC ou peer/ACL antes de projetar evidências. Um processo Python arbitrário sob a mesma conta compartilha a autoridade do processo; a interface de provider não é sandbox de código malicioso.
- `provider_timeout` classifica um TimeoutError recebido do substituto. Não há watchdog capaz de interromper um provider bloqueado: adaptadores reais precisarão de limites de leitura e isolamento próprios, revisados antes de uso.
- Último sucesso é somente cache em memória. Não foi implementada persistência, leitura de credenciais, logging operacional ou coleta permanente.
- Despacho de HKCU Run continua inconclusivo sem evidências independentes de login/despacho/bootstrap; nenhum mecanismo de inicialização foi alterado ou testado fisicamente.

## Preservação verificada

[Recibo de preservação](preservation.json): **1.338 arquivos protegidos** idênticos, incluindo Windows instalado, perfil, recursos/bridges Android, recuperação e backups; quatro arquivos de runtime protegidos mantiveram hashes. Banco íntegro, identidades/segredos cifrados/schema/permissões preservados e zero grants.

[Agente original](agent-after.json): supervisor **5024**, worker **18304**, redirectors **19996/20352**, imagens/argumentos/parentesco/horários de criação preservados; listener único 8776 do worker esperado. Hash da entrada Run e das regras relevantes de firewall permaneceu igual ao início. Não houve reinício ou sinalização desses processos.

[Consulta de preservação](authenticated-final.json): TLS 1.3, certificado/hostname/pin verificados antes de usar a identidade existente em memória; somente GET `/v2/status` e `/v2/apps`, ambos HTTP 200, lista de permissões vazia. Nenhuma identidade ou permissão criada.

[Processos residuais](residuals.json): zero Electron do projeto/instalação ou componentes de monitoramento identificados na conferência. O Samsung esteve ausente: nenhuma ADB, tentativa remota, instalação ou verificação física do aparelho foi feita. Preservação do aplicativo instalado significa ausência de acesso/modificação, não uma nova auditoria física de seu armazenamento.

Não foram executados Steam, CS2, WoL, energia, nova sessão física Windows ou coleta de hardware. Android atual e Windows dev.7 instalado não foram atualizados. Não foram instalados drivers/dependências/serviços/tarefas, nem alterados HKCU Run, firewall, credenciais ou certificados. Pendências TLS, Crashpad e encerramento gracioso continuam separadas.

## Próximas etapas, mediante aprovação

1. Aprovação visual do [Android dev.8](../design/android-windows-family-dev8-2026-10-26/README.md); atualização física somente quando o usuário retornar e autorizar, com assinatura conferida e `adb install -r`, sem apagar dados.
2. Projetar adaptadores diagnósticos somente leitura, inicialmente a partir de snapshots já validados e logs sanitizados, sem nova sondagem de hardware. Realizar revisão de privacidade e timeout antes de qualquer execução real. Não compartilhar a identidade do Samsung com o desktop.
3. Uma futura apresentação deverá passar pelo processo principal Electron e API preload estreita, com mensagens limitadas e sem comandos de reparo. Não expor credenciais, caminhos genéricos, acesso ao pipe ou execução de shell ao renderer.
4. Retomar homologação física Windows dev.7 separadamente: confirmar previamente um caminho operável para Sair; verificações essenciais em 0–30 s, solicitação de saída até 45 s e reserva até 120 s para processos/pipes/HTTPS. Priorizar widget, bandeja e Atualizando até amostra nova. Não induzir falha de driver para provocar timeout. Se o caminho de saída não estiver disponível, adiar antes de abrir. Nenhuma sessão foi realizada enquanto o usuário estava ausente.

## Reversão

Reverter os commits do autodiagnóstico separadamente dos commits Android, preferindo `git revert` em ordem inversa após revisão. Não há processo, serviço, perfil ou instalação de diagnóstico para remover. A documentação pode ser revertida independentemente; preservar evidências antes de fazê-lo. Nenhum rollback de produção é necessário ou foi executado.
