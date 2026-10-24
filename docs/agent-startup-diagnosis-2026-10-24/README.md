# Diagnóstico somente leitura — inicialização do agente HTTPS

**24/10/2026. Agente não iniciado, reiniciado ou modificado.** Electron e Android não foram abertos ou modificados nesta tarefa. Checkpoint preservado: `e108bfe3a4867563dc396c67527a073241f4db24`, branch `feature/ui-migration-preview`.

**Conclusão:** o agente está cadastrado em HKCU Run, mas não foi encontrado um lançamento correspondente nos registros de processamento das listas Run do último login. A hipótese mais consistente é falha/omissão no despacho de logon, com **confiança moderada**. A causa técnica exata continua **inconclusiva**: não há log persistente do bootstrap e a auditoria completa de criação/encerramento de processos não estava acessível. Não foi comprovado um crash, erro TLS ou erro de diretório de trabalho.

## 1. Mecanismo atual

Uma entrada lógica por usuário, observada nas duas visões do Registro:

```text
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
Nome: LoneSmartRoomSecureAgent
Tipo: REG_SZ
```

Comando registrado, sem segredos:

```text
"<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.venv\Scripts\pythonw.exe" "<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\agent\windows\secure_agent.py" serve
```

SHA-256 do texto: `3139f837ebc03ab77c5c16bc00fcb76031fb6a50ef8ccbcd4a014d6c4b509dc5`, igual ao registro anterior funcional. Os 221 caracteres estão abaixo do limite documentado de 260. Caminhos com espaços estão entre aspas; interpretador, script, venv e Python base existem nos caminhos atuais. Não há referência v1.4/v1.5 ou caminho antigo nesse comando.

HKCU Run é disparado **no login da conta**, não como serviço antes do login; ordem e prontidão de execução não são garantidas pelo Windows. Fonte: [Microsoft — Run and RunOnce Registry Keys](https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys).

| Aspecto | Verificação |
|---|---|
| Conta | Conta atual corresponde à conta interativa e ao proprietário do Explorer, sessão 1; perfil `<USERPROFILE>` |
| Privilégios | Consulta não elevada; mecanismo por usuário, sem elevação programada |
| Pasta Inicializar | Nenhum atalho correspondente encontrado nas pastas do usuário ou comuns; alvos dos `.lnk` foram lidos sem salvar |
| Tarefas agendadas | Nenhum nome/caminho/ação correspondente a Lone Smart Room ou `secure_agent.py` |
| Serviços | Nenhum serviço com nome/caminho correspondente ao agente |
| Script de login por Environment | Nenhuma referência ao agente em UserInitMprLogonScript |
| StartupApproved | Nenhuma entrada específica encontrada nas áreas consultadas; ausência não comprova execução nem habilitação efetiva |
| Políticas Run | Valores DisableCurrentUserRun/DisableLocalMachineRun e variantes RunOnce ausentes nas áreas HKCU/HKLM consultadas |
| Condições de rede | Certificado público referencia endereço presente em adaptador local; perfil correspondente atualmente Privado, sem publicar endereço ou SSID |
| Diretório de trabalho no Run | Não especificado; diretório efetivo do processo automático extinto não pôde ser recuperado |

As políticas consultadas e sua relação com listas de logon estão documentadas em [Microsoft — ADMX Logon](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-admx-logon). Não houve alteração de política, aprovação ou permissão.

O inventário cobre esses mecanismos usuais e correspondências de nomes/ações; não é uma busca irrestrita por toda forma possível de persistência do Windows.

## 2. Evidência nova: processamento do login

Horários locais America/Sao_Paulo (UTC−03:00); recibos conservam UTC.

| Momento | Evidência |
|---|---|
| 13:32:08 | Snapshot anterior mostrava agente ativo, listener 8776, PID 13012; não é um teste repetido hoje |
| 14:09:07–14:09:13 | System 1074, 6006 e Kernel-General 13 contextualizam encerramento/reinicialização |
| 14:09:40 | LastBootUpTime e Kernel-General 12 confirmam o último boot |
| 14:10:05–14:11:20 | Shell-Core 9705/9706 registram processamento das listas Run/RunOnce; 12 eventos 9707 e 12 eventos 9708 com PID, sem Python ou agente nos comandos correspondentes |
| Janela 14:09:35–14:39:40 | Foram lidos 223 eventos Shell-Core e 14 eventos Windows PowerShell 400/403; nenhum correspondeu ao agente ou à consulta de rede usada por `private_profile()` |
| 19:04:17 | Estado final: zero processos do agente, zero Electron e nenhum listener 8776 |

Os comandos e mensagens de outros programas não foram publicados. A ausência do agente nessas fontes é evidência contra um despacho normal de Run nessa janela, **não prova absoluta de que nenhum processo transitório existiu**. Não há auditoria completa disponível para concluir se ele nasceu e terminou antes do primeiro registro próprio.

### Divergência entre consultas do Registro

- Leitura direta .NET de HKCU e HKEY_USERS e `reg.exe query` de **32 e 64 bits** encontram a entrada correta.
- `Win32_StartupCommand` retorna 19 itens, nenhum correspondente ao agente.
- Provedor `StdRegProv`, consultando explicitamente HKEY_USERS da mesma conta, enumera 13 valores na lista Run, enquanto a leitura direta enumera 14. O único nome adicional na visão direta é `LoneSmartRoomSecureAgent`. A enumeração retornou sucesso; GetStringValue específico retornou 1, sem conteúdo utilizável.
- A identidade da conta é a mesma do usuário conectado e do Explorer; não se trata de uma entrada comprovadamente instalada em outra conta.
- O processo Python de diagnóstico consultado não apresentou identidade de pacote MSIX (`GetCurrentPackageFullName` retornou 15700).

**A divergência foi observada, mas sua origem não foi determinada.** Não chamar a visão WMI de prova definitiva da visão usada pelo Explorer, nem afirmar virtualização, corrupção do Registro, MSIX ou bloqueio de segurança. O resultado positivo de reg.exe é um contraponto importante. Não reescrever ou duplicar a entrada apenas para fazê-la aparecer no WMI.

## 3. Ambiente, dependências e certificados

Verificações realizadas sem importar `secure_agent`, sem inicializar Store/DPAPI e sem abrir servidor:

- Venv ativa, **CPython 3.13.3 x64**, base `C:\Python313`, `include-system-site-packages=false`.
- Imports de dependências aprovados: **cryptography 50.0.2, cffi 2.1.1, pycparser 3.12**, versões correspondentes ao lock existente. Nenhum pip/install foi executado.
- Biblioteca SSL disponível: OpenSSL 3.0.16. Sintaxe do script válida por AST, sem executá-lo.
- Dependências também importaram com sucesso a partir de `C:\Windows\System32` em um subprocesso Python CLI **somente de diagnóstico**. Módulos locais resolvem pelo diretório absoluto do script, verificados por PathFinder, sem executar os módulos do projeto. Não foi lançado `pythonw.exe` nesta investigação.
- `config.dpapi`, `devices.db`, `server.crt`, `server.key` e `tls.dpapi` presentes. Certificado público vigente, até **23/10/2027 11:13:46 UTC**; chave continua com cabeçalho de chave privada criptografada.
- Leitura/importação atual funcionou nessa conta. Proprietário de arquivo diferente do usuário, isoladamente, não foi tratado como falta de acesso. Não foi realizada prova de execução de pythonw no login nem auditoria histórica de todas as permissões.

Os hashes do estado protegido foram preservados. **Não foram descriptografados configuração, credenciais ou passphrase; a chave privada não foi carregada em um SSLContext.** Portanto não foi repetida a validação funcional DPAPI/certificado-chave/bind; a validação anterior bem-sucedida é histórica, não um resultado novo.

## 4. Manual versus automático

| Aspecto | Manual anteriormente validado | Automático atual |
|---|---|---|
| Entrada | `scripts/manage-agent.ps1 -Action serve` | HKCU Run |
| Executável/argumentos | Venv pythonw, script absoluto e `serve` | Os mesmos destinos e argumento |
| CWD | Wrapper define explicitamente a raiz 2.0 | Não é especificado na entrada Run; valor histórico desconhecido |
| Conta/contexto | Sessão interativa 1, sem elevação, conforme recibos anteriores | HKCU da mesma conta interativa; execução automática não foi observada |
| Dependência do Electron | Nenhuma | Nenhuma |
| Resultado | PID wrapper + processo Python base, HTTPS autenticado validado na ocasião | Sem processo/listener após o último reboot; sem evidência de despacho no log Run consultado |
| Erros persistentes | Recibos pontuais da execução anterior | O script não mantém log persistente do bootstrap; exceções comuns não têm captura externa permanente |

`secure_agent.py` calcula ROOT/STATE a partir de `__file__`, não de CWD; imports do script usam seu diretório e o teste de dependências em CWD neutro passou. Assim, o diretório de trabalho é uma **diferença real**, mas não uma causa comprovada ou a explicação mais forte isoladamente.

O guardião de rede retorna falso em perfil não confiável, falha de consulta ou timeout e o laço aguarda 10 segundos sem abrir listener. Uma indisponibilidade de rede inicial, **sozinha**, deveria deixar o processo aguardando; não explica integralmente a ausência de processo. Exceções anteriores ao laço ou em bind/TLS não são recuperadas por ele, além de KeyboardInterrupt; continuam possibilidades sem registro específico.

## 5. Logs, bloqueios e pontos não verificáveis

- Nenhum `.log` de diagnóstico persistente encontrado em `.runtime/secure-agent`.
- Nenhum evento Application 1000/1001/1002/1026 relacionado ao Python/agente após o boot; nenhum Report.wer Python correspondente encontrado nas pastas existentes consultadas. Dumps não foram abertos, gerados ou enviados.
- Nenhum bloqueio correspondente encontrado nos IDs de CodeIntegrity, AppLocker e Defender consultados. Ausência de registros não elimina todo bloqueio possível.
- Security e Diagnostics-Performance retornaram `LogInfoUnavailable` nesta conta; Sysmon/Operational não foi encontrado. **Não foi possível usar 4688/4689 para provar criação/saída do processo.** Não houve elevação adicional, habilitação de auditoria ou instalação de coletor.
- Foram corrigidos somente dois problemas no coletor local ignorado pelo Git: conflito de nome com alias PowerShell e conversão de data. As leituras foram repetidas; isso não é erro do agente nem correção aplicada a ele.
- Não foram executados comandos de gerenciamento do agente, nem mesmo devices/app-permissions: o código desses comandos carrega configuração e inicializa Store. Contagens foram obtidas diretamente por SQLite `mode=ro`.

## 6. Hipóteses e confiança

| Hipótese/conclusão | Grau e fundamento |
|---|---|
| Agente atualmente offline; Run registrado | **Alta confiança**, por processos/porta e leituras independentes positivas do registro |
| Ausência/falha no despacho da entrada durante o login observado | **Moderada; hipótese principal**, pois o Shell registrou outros comandos Run e nenhum do agente/Python |
| Origem dessa falha: filtragem, visibilidade ou persistência da entrada em contexto de login | **Baixa a moderada**, sugerida pela divergência WMI, sem comprovação do mecanismo; reg.exe encontra a entrada |
| Processo iniciou e encerrou cedo por exceção não registrada | **Possível, confiança baixa**, devido à ausência de bootstrap log e auditoria completa; nenhum erro específico foi encontrado |
| CWD causou falha de dependência | **Pouco sustentada atualmente**: caminhos absolutos, imports e resolução em CWD neutro passaram; o ambiente histórico completo é desconhecido |
| Caminho antigo, comando maior que 260, dependência ausente ou certificado expirado | **Não encontrados nas verificações atuais**; não afirmar que essas condições foram testadas funcionalmente no instante do login |
| Outra conta, dependência de Electron ou necessidade de novos grants | **Sem sustentação nos dados atuais**; conta/Explorer coincidem, Run é independente e zero grants não impede servir status |
| Pendência TLS causou a ausência no login | **Nenhuma evidência nova**; não houve despacho registrado nem evento TLS correlacionado. Mantida como investigação separada |

Não há base técnica para prometer uma correção definitiva sem uma observação controlada futura do bootstrap/logon.

## 7. Correção mínima recomendada — proposta, não aplicada

**Primeiro tornar o início observável, mantendo HKCU Run por usuário e o agente seguro existente.** Não trocar imediatamente para serviço/tarefa, não regravar registro às cegas e não alterar autenticação/rede.

Proposta concreta para uma próxima implementação autorizada:

1. Criar um bootstrap local específico, por exemplo `scripts/start-secure-agent.py`, executado pelo mesmo pythonw da venv. Fixar raiz/CWD e diretório de módulos; aceitar somente o fluxo fixo `secure_agent.py serve`, sem argumentos externos de comandos.
2. Registrar antes dos imports do agente apenas hora UTC, PID, fase e resultado; em falha, somente classe da exceção e códigos numéricos permitidos. **Sem raw stdout/stderr, cabeçalhos HTTP, mensagens de exceção sem filtro, locais de memória, tokens, IDs de dispositivos, endereços de LAN ou código de pareamento.** Rotação limitada e pasta própria privada, fora do Git, sem alterar ACLs dos arquivos existentes.
3. Fazer apenas uma chamada do agente por execução, sem supervisor, relançamento ou retentativa automática. Preservar integralmente o laço de rede privada, TLS/HMAC, replay, certificados, permissões e executores existentes.
4. Após revisão do código e testes com executor substituto, propor atualização **somente do valor já existente** `LoneSmartRoomSecureAgent` para apontar ao bootstrap. Preservar nome, HKCU, conta e tipo; conferir tamanho/aspas. Não criar outra entrada, task ou serviço. Essa gravação exige autorização específica e verificação por reg.exe e por contexto independente; WMI isoladamente não será critério suficiente.
5. Se uma leitura independente demonstrar que o registro precisa de reparo, corrigir somente o valor individual autorizado, mantendo cópia verificável do original. Se ele já estiver correto, não o regravar como suposta solução de uma divergência de provedor.

Isso elimina a falta de observabilidade e a ambiguidade de CWD, **mas não é apresentado como causa raiz já provada ou garantia de autostart recuperado**. Não foi criado o bootstrap, modificado secure_agent.py, gravado Registro ou iniciado processo do agente nesta etapa.

### Riscos e reversão planejada

- Logs podem vazar dados se houver captura indiscriminada: usar whitelist e ACLs privadas; testar com sentinelas falsas antes do uso real.
- Um caminho novo inválido pode impedir o início: validar arquivos, venv, sintaxe e comando com executor substituto antes de qualquer gravação.
- Duplicar Run/tarefa/manual pode abrir instâncias concorrentes: manter um único mecanismo e abortar se já houver processo/listener; não adicionar watchdog ou grants.
- Para reverter futura alteração, restaurar apenas o valor REG_SZ original de 221 caracteres já identificado, via procedimento autorizado; reverter o commit específico do bootstrap sem reset destrutivo. Não apagar chaves inteiras nem tocar Android/Electron, certificados ou banco de dispositivos. Preservar logs e backups.
- Se o agente já estiver em execução numa reversão futura, não encerrá-lo automaticamente: isso exige autorização própria. Nenhuma reversão foi realizada hoje.

## 8. Plano de um único teste futuro

**Não executado e sem autorização nesta tarefa.** Para comprovar o autostart, uma execução manual isolada não basta.

1. Revisar e aprovar o bootstrap/registro e o plano de recuperação; manter zero grants, certificados e pareamento. Confirmar inexistência de processo/listener duplicado e integridade dos backups.
2. Obter autorização **separada e expressa** para um único ciclo controlado de reinicialização e login, salvando antes o trabalho do usuário. Nenhum comando de energia está autorizado agora.
3. No login, deixar exclusivamente a entrada Run iniciar o agente. Não abrir Electron, não chamar serve manualmente e não repetir o ciclo. Registrar bootstrap e Shell desde o início.
4. Observar por até 180 segundos: um agente lógico (wrapper/base Python podem produzir dois PIDs), perfil Privado correto e listener HTTPS 8776. Se a rede estiver Pública, o serviço deve continuar bloqueado. Run pode sofrer atraso pelo Windows; timeout será registrado como ausência de sucesso nessa janela, não como prova de falha permanente.
5. Consultar somente status autenticado pelo Samsung com o pareamento e pinagem existentes; confirmar Conectado e última comunicação real. Não criar identidade desktop, pareamento, grants ou executar aplicativos/energia/WoL.
6. Se houver falha, preservar os logs sanitizados e parar, sem relançamento manual ou nova reinicialização. Se funcionar, registrar o resultado e manter o agente conforme a autorização; um eventual encerramento posterior também deve estar previsto no protocolo aprovado.

## 9. Preservação comprovada

Comparação antes/depois: **269 arquivos protegidos sem divergências**, incluindo código do agente, estado cifrado, Android, Electron instalado e perfil. Os imports de dependências usaram `-B`, sem gravação de bytecode; módulos do agente não foram executados. **86 registros** de originais e cópias de recuperação aprovados.

Backup `<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev4-20261024T174801Z` revalidado por hashes e ACLs, preservando todos os backups anteriores. Nenhuma funcionalidade de WoL, HTTPS, HMAC, pinagem, replay, identidades ou executores foi alterada. Não houve novo teste funcional desses recursos nesta análise somente leitura.

Zero grants, quatro comandos históricos inalterados, nenhum agente iniciado, nenhum Electron aberto e nenhum listener 8776 no encerramento. Nenhuma modificação em firewall, roteador, serviços, Registro, drivers, rede privada ou Android. A diferença agregada anterior de tarefas continua inconclusiva e **não foi atribuída ao agente**; somente correspondências relevantes ao seu início foram investigadas.

**Parada após o diagnóstico.** Próxima autorização sugerida: preparar e testar o bootstrap sanitizado com substitutos, mantendo agente parado e deixando a gravação Run e o teste de logon para autorizações posteriores.
