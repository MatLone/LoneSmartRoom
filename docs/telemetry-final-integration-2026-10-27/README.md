# Entrega Android — bloqueio operacional confirmado

**Funciona no Samsung: NÃO, a implantação não foi iniciada.**
O Android permanece dev.9/v23; o agente original permanece ativo. Não se tentou
substituí-lo sem uma forma segura de parada, conforme a condição expressa do pedido.

## O que foi implementado

Marco `a6c1add`, branch `feature/telemetry-android-development`:

- `telemetry/relay.py`: canal Named Pipe específico de leitura de cache, distinto
  do pipe exclusivo coletor/intermediário já existente. Não inicia coletor.
- Publisher e reader verificam handles nativos retidos, PID/criação/imagem,
  SID/sessão e ausência de elevação. DACL por conta, primeira instância e rejeição
  de clientes remotos reutilizam as primitivas Windows existentes.
- Somente snapshot v1; pedidos adicionais/comandos são recusados. Limites de
  128 bytes por pedido, 32 KiB por resposta, 2 leituras/s, I/O de até 1,5 s.
- Revalidação do contrato, UTC/idade e tempo de transporte. Desconexão, morte
  ou troca de identidade do publisher e mensagens inválidas retornam Indisponível,
  sem fallback de valores antigos. Geração conservada na perda de conexão evita
  apagar a barreira contra amostras antigas da interface Android.
- `agent/windows/telemetry_runtime.py`: composição opt-in da rota autenticada
  `/v2/telemetry` com o relay registrado. Leitura explicitamente separada dos
  grants de aplicativos; recurso desativado por padrão.

São APIs internas: o bootstrap confiável precisa registrar os peers após conferir
imagem/argumentos e controlar seus handles. Não existe registro de PID ou comando
via Android/renderer/HTTP. Essa integração ao bootstrap operacional **não foi
ativada nem homologada**. ACL por conta não isola código malicioso da mesma conta.

## Testes novos, proporcionais à mudança

**16 testes focados aprovados:** identidade/PID reutilizado, ACL, tokens de outra
conta/remotos, limites, rate limit, versão/framing/dados inválidos, frescor,
ausência de coletor, perda/recuperação, null/zero, autenticação, escopo de leitura
e status existente. Nenhum sensor ou agente operacional foi usado nesses testes.

**9 verificações nativas aprovadas:** cache publisher e HTTPS em processos
separados, Named Pipe real, identidade e DACL nativas, HTTP 401 sem autenticação,
HTTP 200 autenticado, 29 métricas, zero válido, zero grants de comandos e saída
cooperativa do publisher. Duração 0,7861 s. Dados **explicitamente simulados**;
isso não é uma nova coleta física nem homologação no telefone.

A coleta real Windows → HTTPS → modelo/cartões Android já foi comprovada no marco
`af40096`/`9f80ab9`, em 30 snapshots e 15 respostas HTTPS. O novo relay entre
processos foi testado nesta entrega com fixtures; ainda requer validação com
métricas atuais e bootstrap integrado antes de qualquer implantação.

## Bloqueio concreto do agente legado

Supervisor efetivo **2096**, worker **14908**, com os redirecionadores venv 16828 e
8592, mesmas imagens, argumentos e horários de criação. O worker usa
`agent_launcher.py --worker`; não executa `graceful_launcher.py`.

Inspeção atual, somente leitura:

| Processo | Console | Janelas top-level | Canal de parada |
|---|---|---:|---|
| Supervisor 2096 | Ausente, AttachConsole erro 6 | 0 | Launcher aguarda o worker |
| Worker 14908 | Ausente, AttachConsole erro 6 | 0 | Loop legado sem stop local/API |

O código legado usa DEVNULL e não lê stdin como sinal de saída. O canal novo de
encerramento não está carregado nessa sessão. A sondagem de console afetou
somente o helper de inspeção: nenhum Ctrl+C/Break, WM_CLOSE, evento de stop,
escrita de memória ou término de processo foi enviado.

Portanto **não existe procedimento de substituição controlada validado para a
sessão ativa dentro destas restrições**. Adicionar um arquivo novo não atualiza
o código já carregado. Não se improvisou parada forçada, logoff, reinício,
alteração de rede ou atualização de arquivos carregados.

## Samsung e APK

ADB inicialmente offline/ausente; depois o aparelho foi reconhecido e o usuário
confirmou conexão e desbloqueio. Modelo verificado **SM-S731B**.

- Instalado: `com.lonesmartroom.app`, **2.0.0-dev.9, código 23**.
- APK instalado lido via ADB sem alteração: SHA-256
  `92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2`.
- Candidato: **2.0.0-dev.10, código 24**, mesmo package, SHA-256
  `06f1dfe8693e8489a7d3b82e51c730ca5333b5435f826e94b1be3457109d4078`.
- Ambos passaram apksigner e possuem certificado SHA-256
  `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.

Compatibilidade de atualização confirmada; **nenhum `adb install`, `pm clear`,
desinstalação, pareamento ou abertura do app foi executado**. Não há captura real
de métricas novas no Samsung a apresentar. WoL, cofre e preferências não foram
modificados; não houve teste funcional WoL ou nova inspeção/descriptografia do cofre.

## Estado final e recuperação

Verificação em 27/10/2026 **11:24:04 −03:00**: agente original autenticado HTTP 200,
TLS 1.3, hostname/pinagem válidos, listener privado único 8776 no PID 14908.
Banco íntegro, zero grants, mesmas identidades/credenciais/permissões, arquivos
protegidos e hash de HKCU Run. Consultas normais podem registrar nonces normalmente;
não houve escrita direta no banco operacional.

Instalação Windows: mesmos 117 arquivos (116 originais mais debug.log);
perfil: 78 arquivos idênticos; backup dev.7: 194 hashes conferidos. PID 11724 e
debug.log preservados. Sem processos temporários de relay ou pipes LSR restantes.
Sem alterações de firewall, serviços, tarefas, drivers ou instalações.

**Rollback operacional não foi necessário nem aplicado:** não houve atualização.
Os backups/artefatos anteriores permanecem conservados. Não foi criado backup
novo de substituição porque o gate de parada falhou antes da janela de implantação.
Não se declara validado o rollback de um backend novo que não foi implantado.
Reversão do código isolado: reverter `a6c1add`, preservando recibos e evidências.

## Continuação coordenada

Falta definir uma transição de manutenção capaz de liberar o agente legado com
segurança. Até lá, mantê-lo funcionando. Após essa condição ser resolvida por
procedimento especificamente autorizado: concluir o registro confiável de peers
no bootstrap, validar o novo relay com métricas atuais, criar backup consistente
e protegido do que será substituído e testar a recuperação antes da interrupção.

Então realizar **uma implantação coordenada** de runtime/backend e Android v24,
mantendo certificado/pin, banco, identidade e configurações, com `adb install -r`
somente depois do backend íntegro. Comparar a mesma amostra Windows/telefone,
testar pausa/reconexão/indisponibilidade e registrar telas reais. Sem grants ou
comandos de jogos/energia. O APK sozinho não habilita a rota do agente legado.

TLS 10054 e demais pendências permanecem abertos, sem reprodução ou correção
incidental. Nenhum novo módulo de produto foi iniciado nesta tarefa.
