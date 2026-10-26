# Autodiagnóstico — adaptadores preparados, somente mocks

**Resultado:** preparação de desenvolvimento concluída e validada offline. Nenhum leitor operacional, reparo, serviço ou integração nos aplicativos instalados foi ativado. Android dev.9 e seus assets aprovados ficaram intactos.

A [arquitetura](ARCHITECTURE.md) foi registrada em `a46ada6`, antes do commit funcional **`c0bce81`**. Ambos evoluem a fundação anterior; não substituem o agente HTTPS, o monitoramento ou as bridges existentes.

## Apresentação preparada

- [Prévia estática em HTML](review.html).
- [Captura da prévia simulada](SIMULATED-review.png).
- [Relatório de exemplo](SIMULATED-report.json) e [modelo de apresentação](SIMULATED-view.json).

Os oito cartões são explicitamente **SIMULADOS**, com relógio fixo de fixture. Não retratam a saúde atual do computador. O Chromium usado para capturar o documento tem perfil próprio, não carrega main/preload da instalação e não inicia sensores.

| Rótulo | Significado |
|---|---|
| Saudável | Evidência suficiente e válida, dentro do frescor exigido |
| Indisponível | Sem conexão/amostra/suporte; ausência de prova aparece como **Não verificado** |
| Desatualizado | A evidência/amostra excedeu a validade, preservando horário e idade anteriores |
| Falha | Falha explícita do recibo, contrato ou verificação; não significa automaticamente falha física do componente |

O estado bruto `unknown` é preservado no modelo, sem convertê-lo em prova de PC desligado. Última comunicação autenticada é apresentada apenas no cartão HTTPS. Consultar novamente o cache não renova os horários. Nenhum botão de correção, execução, reinício ou concessão de permissão foi adicionado.

## Componentes implementados

| Componente | O que foi preparado e testado |
|---|---|
| HTTPS | Recibo de **GET `/v2/status`**; exige 200, TLS, hostname, pin e uso de HMAC na requisição. Distingue timeout, TLS rejeitado, autenticação e erro HTTP |
| Listener 8776 | Presença separada da identidade: imagem, criação e parentesco precisam estar verificados no recibo; não usa apenas PID |
| Named Pipe | Recibo de conexão local, SID, sessão, identidade do servidor e contrato v1; trata desconexão, timeout, limites e reconexão |
| CPU/RAM/GPU | Validação de snapshots no contrato de métricas v1, com catálogos puros existentes; zero válido, null, aquecimento, erro, indisponibilidade e suporte parcial permanecem distintos |
| Ponte ADLX | Estado do processo/biblioteca e do último quadro; ingresso até 1,5 s; quadro rejeitado permanece indisponível, sem reinício |
| Inicialização | Configuração esperada, login, sessão, linhagem e eventos sanitizados correlacionados; distingue despacho não comprovado, falha de bootstrap e retorno do agente |
| Apresentação | Modelo PT-BR limitado, códigos enumerados, mensagens fixas e HTML escapado sem scripts ou rede |

Arquivos principais:

- `diagnostics/evidence.py`: frame de recibo UTC/monotônico e fila finita de fixtures. JSON UTF-8 limitado a **32 KiB**, sem chaves duplicadas, NaN ou infinito; sem URL, caminho de pipe ou arquivo como parâmetro de leitor.
- `diagnostics/adapters.py`: adaptadores de recibos de status, listener, pipe e ADLX; aceita apenas `FixtureReader` nesta fase.
- `diagnostics/metric_evidence.py`: valida snapshots simulados conhecidos, tipos, unidades, fontes, limites e consistência RAM/VRAM. Não constrói API nativa.
- `diagnostics/startup_evidence.py`: interpreta até 64 eventos por recibo, usando a allowlist de eventos do launcher existente; não abre logs ou Registro.
- `diagnostics/contracts.py` / `engine.py`: detalhe diagnóstico enumerado adicional, cache existente e expiração conservadora.
- `diagnostics/presentation.py` / `scenarios.py`: apresentação limitada e cenários de demonstração explicitamente simulados.

O contrato de métricas v1 e os endpoints/preloads operacionais não mudaram. O relatório diagnóstico v1 recebeu um campo opcional de detalhe; consumidores futuros que rejeitem campos adicionais precisarão de negociação explícita. Não há consumidores operacionais integrados hoje.

## Frescor e temporização

- ADLX: idade de ingresso **até 1,5 s**, sem flexibilização.
- GPU e ponte: expiração ao atingir **3 s ativa / 11 s inativa**.
- CPU/RAM: acompanha o contrato existente: intervalo 1 s → validade de 3 s; intervalo 5 s em inatividade → 15 s. Não usa o limite ativo de 3 s para acusar artificialmente falha de uma amostra na cadência inativa.
- Métricas incorporam a idade original e o atraso de entrega do snapshot; não recebem o horário da consulta como se fosse uma nova coleta.
- A verificação de expiração do reducer foi alinhada a `idade >= limite`, inclusive sem chegar novo frame. Não houve mudança de temporização no aplicativo instalado.
- Retomada GPU informada como pendente impede estado saudável até a amostra nova e válida. O mecanismo operacional de Atualizando/10 s não foi substituído ou alterado.

## Inicialização após login: limites de inferência

`attempt`, `child_created` e `bootstrap_ready` podem existir numa execução manual; **não provam que Windows despachou HKCU Run**. Sem prova independente de origem e correlação da sessão, o diagnóstico permanece inconclusivo. Logs anteriores ao login ou anteriores à última tentativa não são usados como sucesso da tentativa atual.

Falha de bootstrap só é atribuída à inicialização correlacionada quando há evidência de despacho e identidade/sessão verificadas. `bootstrap_ready` confirma apenas bootstrap, nunca HTTPS autenticado. Retorno/saída do processo é separado de falha do mecanismo de login. Eventos `duplicate`/`legacy_present` não geram reinício ou conclusão automática de falha.

O atual formato de log não contém prova suficiente da origem HKCU Run. Esta implementação **não resolveu a causa da inicialização automática nem adicionou instrumentação ao launcher ativo**. Nenhum Registro, tarefa, serviço ou arquivo do agente foi alterado.

## Testes e ocorrência TLS registrada

- **96 testes isolados** aprovados, com audit hook que bloqueia rede, Registro, DLLs e criação de processos. O recibo inclui hashes dos fontes e testes: [tests-summary.json](tests-summary.json).
- **266 testes** aprovados na última suíte completa contra os fontes finais; fixtures loopback e executores substitutos, sem usar o agente operacional.
- A primeira suíte completa, com 265 casos numa revisão intermediária, teve **um erro TLS `WinError 10054`** no teste existente `test_pair_rate_limit_and_request_limit`. Ocorreu ao ler o corpo da resposta de uma requisição de pareamento de 1.025 bytes, para a qual se esperava HTTP 400.
- Uma execução intermediária posterior de 265 casos também passou. Isso **não elimina a intermitência**. O caso é consistente com a pendência conhecida de fechamento/reset em corpos acima do limite; a causa não foi reanalisada nem corrigida nesta tarefa. Nenhum pacote excessivo foi enviado ao agente operacional.

Histórico estruturado: [validation-results.json](validation-results.json). Não apresentar o resultado como estabilidade TLS definitivamente homologada. A pendência continua sendo bloqueio para declarar pronto um novo cliente autenticado operacional.

Os testes também identificaram e corrigiram problemas exclusivos do desenvolvimento: marcador de fixture `None` tratado como erro em vez de “nenhum dado novo”; idade de evidência antiga exibida como idade do recibo; expiração exclusiva no instante limite. Nenhuma dessas correções foi aplicada a uma instalação.

## Limites de segurança e riscos restantes

1. **Não há sondas reais nesta entrega.** Recibos booleanos não verificam certificados, HMAC, processo ou ACL por conta própria. São projeções que um futuro leitor confiável deverá produzir após validar a fronteira real. Nenhum dado real pode ser apresentado como fixture ou vice-versa; os adaptadores atuais rejeitam origem `real`.
2. A ACL por usuário do Named Pipe não fornece isolamento contra processos maliciosos da mesma conta. Nenhum pipe foi criado ou aberto pelos novos módulos. Não houve ampliação de API preload.
3. Timeout de transporte é um resultado de fixture. Não existe watchdog nativo ou garantia de interrupção de um leitor real bloqueado; leitores operacionais precisarão de timeouts e isolamento próprios.
4. Os limites de 32 KiB/64 métricas/eventos são desta projeção, não alterações aos limites do servidor HTTPS/pipe existente. Payload maior é recusado; não truncado nem aceito por aumentar limites silenciosamente.
5. Não há reparo, polling permanente, inicialização automática, concessão de grants ou ações de energia. A interface de provider Python não é sandbox contra código arbitrário da mesma conta; o runner limita operações durante os testes.
6. Nenhum histórico pessoal, conteúdo de arquivos, credencial, certificado privado, payload bruto ou texto livre de exceção sai no relatório. Campos desconhecidos e códigos não enumerados são recusados.

## Preservação comprovada

[Auditoria](preservation.json): **1.338 arquivos protegidos** e quatro arquivos de runtime mantiveram hashes. Instalações, perfil Windows, recursos Android, fontes funcionais, backups e recuperação ficaram intactos. Banco íntegro; identidades, segredos cifrados, schema e permissões preservados. **Zero grants**.

[Release preservada](release-preservation.json): APK dev.9/código 23 continua com SHA-256 `92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2`; dez APKs anteriores e 28 assets aprovados também permaneceram intactos. Não houve mudanças em `apps/`, `agent/`, `monitoring/` ou `native/`.

[Estado do agente](agent-after.json): mesmas identidades do supervisor/worker e listener único 8776. Hashes de HKCU Run e regras relevantes de firewall iguais aos iniciais. A consulta de preservação é uma ferramenta privada somente leitura, não uma ativação dos novos adaptadores. Nenhum restart/sinalização ou requisição operacional ao agente foi feito por eles. [Sem resíduos](residuals.json): não foram encontrados aplicativos ou componentes de monitoramento de desenvolvimento em execução ao concluir.

Android/Samsung não foi acessado; nenhuma instalação, compilação de APK/NSIS, atualização Windows, coleta física ou execução Steam/CS2/WoL/energia ocorreu. As pendências Crashpad, TLS e encerramento gracioso continuam separadas.

## Próxima validação proposta — exige autorização específica

1. Revisar os leitores reais propostos, suas fontes, limites, autenticação e escopo de leitura antes de codificá-los/ativá-los. Não reutilizar a identidade do Samsung como identidade desktop. Um novo cliente autenticado depende da resolução/validação da pendência TLS e de identidade independente ou fonte local de recibos já autorizada.
2. Priorizar validação offline contra recibos reais previamente sanitizados, obtidos somente após aprovação de coleta. Nenhum dump de memória, segredo ou payload privado será necessário.
3. Autorizar separadamente uma sessão somente leitura de até **60 s** para leitores específicos. Não iniciar coletores/ADLX adicionais ou abrir o Windows instalado para fazer o pipe aparecer: se o endpoint estiver ausente, registrar indisponibilidade. Não reiniciar o agente nem conceder grants para “resolver” um teste.
4. Para HTTPS, conferir certificado/hostname/pin e somente GET status com identidade explicitamente autorizada. Se essa identidade não existir, manter a verificação inconclusiva e parar a etapa HTTP; não copiar credenciais do celular.
5. Para pipe/logon, validar identidade do peer/processo e correlação atual de login sem editar Registry/logs. Ausência de prova de despacho permanece hipótese.
6. Encerrar os leitores de teste cooperativamente, sem repetições automáticas ou força, e conferir agente, listener, zero grants, APK e perfis. A homologação física Windows dev.7 e a instalação Android continuam exigindo autorizações próprias.

## Reversão

Reverter separadamente o commit documental desta entrega, depois `c0bce81` e `a46ada6`, revisando conflitos. Nenhuma instalação, entrada de inicialização, serviço, processo ou credencial de diagnóstico precisa ser removida: nada operacional foi implantado. Não executar reset destrutivo, restauração de backup ou downgrade do Android. Os commits `75d00eb` e `e6f2897` e os checkpoints anteriores permanecem ancestrais preservados.
