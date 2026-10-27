# Preparação para homologação real da telemetria — 27/10/2026

Base aprovada `258ddf4`, branch `feature/telemetry-android-development`.
**Resultado parcial:** candidato Android assinado e correção de contrato testada;
o transporte vivo ainda precisa de nova validação. Não instalar nem ativar em produção.

## 1. PID residual 11724 — leitura apenas

- Ainda ativo; executável do Electron existente em
  `apps/windows-ui/node_modules/electron/dist/electron.exe` neste repositório.
- Linha de comando: `electron.exe scripts/capture-night-development.cjs`.
- Conta `DEV-PC\LOCAL_USER`; criação em 27/10/2026 07:25:19,823 −03:00.
- Pai PID 11628, `pwsh.exe`, criado às 07:25:19,489, antes do filho; relação temporal
  compatível, além da associação explícita pela linha de comando.
- Janela principal não identificada (handle zero); nenhuma conexão TCP encontrada.
  Isso não prova ausência de toda janela secundária ou handle interno.
- A associação de pipes por PID não foi verificada: não se abriram endpoints nem
  se fez varredura de handles potencialmente sensíveis. O namespace de pipes LSR
  foi enumerado separadamente e estava vazio.
- Corresponde à prévia malsucedida anterior. Não é o Electron instalado. Nenhum
  sinal, tentativa de fechar, kill, restart ou alteração desse processo nesta etapa.

Evidência: [residual-process.json](evidence/residual-process.json).

## 2. Estado operacional antes/depois

Identidades verificadas por imagem, argumentos, criação, SID, sessão, parentesco
e ausência de elevação; não apenas pelos números de PID:

| Função | PID efetivo | Redirecionador da venv |
|---|---:|---:|
| Supervisor original | 2096 | 16828 |
| Worker HTTPS original | 14908 | 8592 |

Listener único privado 8776 no worker 14908. Consultas normais `/v2/status`:
HTTP 200, TLS 1.3, certificado/hostname/pinagem verificados. Banco em modo leitura
passou `PRAGMA quick_check`; **zero grants**, mesmas identidades, credenciais e
permissões. Configuração, certificado e chave protegidos mantiveram os hashes.
Somente o registro normal de nonces das consultas autenticadas pode evoluir;
não houve escrita direta no banco operacional.

Windows dev.7: FileVersion `2.0.0-dev.7`; 116 arquivos da instalação conferiram com
o inventário conhecido, antes e depois. Perfil de produção: 78 arquivos idênticos.
Backup `Windows-before-dev7-20261026T152048Z`: manifesto e hashes dos 194 arquivos
verificados. Hash da entrada HKCU Run permaneceu igual; não se investigou ou
corrigiu sua falha de despacho/bootstrap. Firewall, serviços e tarefas não foram
alterados por esta tarefa; não houve nova auditoria integral dessas configurações.

ADB já estava disponível, mas listou **nenhum aparelho conectado**. Portanto,
Android dev.9 instalado é o último estado homologado conhecido, não uma nova
constatação por ADB. O APK dev.9 preservado foi conferido: SHA-256
`92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2`,
assinatura original válida. Não houve instalação, abertura ou teste do Samsung.

Evidência: [preservation-after.json](evidence/preservation-after.json).

## 3. Única sessão viva isolada — parcial

27/10/2026, aproximadamente 09:30:35–09:31:06 −03:00. Duração total **31,253 s**;
observação planejada de 30 s. Servidor exclusivamente `127.0.0.1:58149`, TLS 1.3,
certificado e identidade temporários próprios, diretório com ACL restrita à conta.
Não se reutilizou a identidade do Samsung nem o certificado privado operacional.
Nenhum listener operacional foi substituído. DLL ADLX existente: assinatura Valid,
versão `1.4.0.121`, SHA-256
`992f6db497a3c8af8d26e578c7b7fce90ed67e506d7790cc3221e4a01b67852a`.
Ponte existente íntegra e revisão SDK fixada, sem recompilação/instalação de driver.

| Componente próprio | PID | Resultado |
|---|---:|---|
| Intermediário + broker + HTTPS temporário | 8876 | Encerrado normalmente |
| Coletor de desenvolvimento | 7632 | Encerrado normalmente |
| Ponte ADLX | 16116 | Encerrada normalmente |

O Named Pipe protegido respondeu **30/30** consultas, sem rejeições ou timeouts;
o cache registrou 482 entradas de amostra, que podem incluir estados indisponíveis.
O cliente de testes recebeu **15 respostas HTTP 200 autenticadas**, todas em
TLS 1.3, com hostname/pin verificados. **As 15 tinham `snapshot:null`.** Não houve
exportação de medições atuais pelo HTTPS, portanto não há mínimos/médias/máximos
atuais de CPU/GPU/RAM/discos a apresentar como resultado deste transporte.
O início/encerramento da ponte não comprova suporte ou validade de cada sensor.

Não se simulou sucesso. A primeira instrumentação não guardava a regra de rejeição
do broker nem snapshots rejeitados. Essa limitação impede provar a condição exata
de cada rejeição dessa sessão. Os hashes do código executado antes da correção
foram preservados em [recibo específico](evidence/live-session-pre-fix-source-hashes.json).

**Encerramento:** EOF dos componentes próprios, sem força; nenhum PID novo residual,
porta 58149 liberada e namespace LSR vazio. Identidade de leitura temporária
revogada e allowlist DEV esvaziada. PID 11724 anterior permanece intocado.
Não houve segunda coleta física após a falha de exportação.

Evidências: [sessão](evidence/live-session-summary.json), [limpeza](evidence/cleanup.json).

### Custo observado, escopo limitado

| Processo Python | CPU normalizada média | RSS médio / pico |
|---|---:|---:|
| Intermediário + HTTPS | 0,0770% | 30,42 / 31,51 MiB |
| Coletor | 0,0487% | 30,77 / 30,81 MiB |

Método: diferenças de GetProcessTimes, tempo de parede e processadores lógicos;
RSS amostrado a cada ~1 s. Exclui ponte nativa, cliente/observador e custo de
inicialização anterior à primeira amostra. Páginas compartilhadas podem aparecer
em ambos RSS. Não é o custo total da telemetria nem a utilização do PC medida
pelo sensor; não comprova a meta global de desempenho.

## 4. Causa reproduzida offline e correção

Snapshots reais já registrados em 26/10 foram rejeitados deterministicamente por
`inconsistent_capacity`. O código aplicava `usado + livre == total` a RAM **e discos**.
Nos registros históricos, as diferenças de C: e D: eram 32.415.744 e 13.598.720 bytes.

A estrutura oficial [DISK_SPACE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-disk_space_information)
mantém campos distintos para espaço usado, disponível, reservado e indisponível.
A soma de apenas usado/livre não é uma decomposição exaustiva da capacidade.
Não foi determinado qual componente explica cada diferença histórica; não se
inventou nem se adicionou um sensor de reserva.

Correção isolada: **RAM mantém igualdade; discos permitem usado+livre ≤ total**,
com valores originais preservados, limites individuais e razão de ocupação
coerentes. Aplicada ao servidor, modelo Android e projeção Kotlin. Não alterou
coletor, Windows instalado, driver, TLS ou relógios. Também se acrescentaram
contadores/regras sanitizados de rejeição, sem payloads ou exceções livres.

Com a correção, o replay histórico passou contrato → HTTPS isolado → modelo
Android, preservando **29 métricas e seus timestamps de 26/10**. É replay,
**não coleta viva corrigida**. O teste também envelhece as amostras até hoje e
confirma que seus valores ficam nulos/desatualizados, nunca atuais.

Isso prova um defeito do contrato com medições reais históricas e sua correção.
É uma explicação fortemente sustentada para a exportação vazia, mas a ausência
da regra registrada na sessão atual impede afirmar que foi sua única causa.
Nova sessão instrumentada ainda é necessária; não foi executada automaticamente.

Evidências: [validação Android do replay](evidence/android-replay-validation.json),
[payload histórico sanitizado via HTTPS](evidence/recorded-real-https-replay.json).

## 5. Android candidato

**2.0.0-dev.10, código 24**, `com.lonesmartroom.app`. A numeração não existia no
histórico Android consultado nem nos artefatos preparados antes desta tarefa.

Arquivo final para revisão, sem instalação:
`.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.10-v24-disk-space-contract.apk`

- Tamanho: **1.299.594 bytes**.
- SHA-256: `06f1dfe8693e8489a7d3b82e51c730ca5333b5435f826e94b1be3457109d4078`.
- Certificado: `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
- Assinatura v2 válida, mesmo certificado do APK dev.9 conferido.
- Assets de telemetria, marca e componentes nativos verificados dentro do APK.
- Build/lint aprovados: **0 erros, 10 avisos preexistentes**.

O primeiro candidato dev.10/v24, SHA `b61d83f60f8552ef868c1f167aa72945e36c25062311388322b7a2f817f6d92d`,
foi preservado no nome original; está superado pelo arquivo final com sufixo.
Nenhum candidato dev.10 foi instalado. O APK dev.9 e os anteriores continuam intactos.

A interface usa o cliente HTTPS autenticado existente, pausa por aba/visibilidade,
mantém origem, validade e nulos, e não modifica pareamento, WoL ou preferências.
**Instalar o APK sozinho não disponibilizará métricas:** o agente original ainda
não oferece a rota e não existe relay operacional entre seus processos e o cache.

Recibo: [android-candidate.json](evidence/android-candidate.json).

## 6. Testes e limites

18 testes Python de contrato/broker/HTTPS, 378 regressões Python, 3 testes de
preservação Android; 11 testes mock do runner, incluindo timeout/EOF/sem kill e
diagnóstico sanitizado. Node: 891 verificações de regressão, 24 de telemetria,
19 de estados Android, 10 de replay histórico, além de histórico/diagnóstico/gamer
existentes (1.928/70/127). O pinner e HMAC Kotlin reais rodaram em JVM contra HTTPS
sintético. Nenhuma dependência nova foi instalada.

Cobertura: ausência de coletor, GPU indisponível, stale, reconexão sem reutilizar
valores antigos, resposta inválida, timeout, pausa fora da aba, tamanho/frequência,
autenticação, pin e autorização de leitura separada. Projeção JSONObject Kotlin
compilada/lintada; execução no Android físico e coleta viva após o ajuste pendentes.
O runner agora rejeita automaticamente a homologação só por HTTP 200/clean stop:
exige presença das métricas essenciais válidas e inclui o tempo de transporte na idade.
Essa proteção foi testada com substitutos após a sessão física, sem nova coleta.

## 7. Implantação, reversão e próximo passo

Ver [plano coordenado](DEPLOYMENT.md). Nada foi ativado no agente, Electron instalado
ou Samsung. Commits: `8a0ded7` contrato/diagnóstico; `2e4e472` runner e testes Android;
`7e842ea` versão e preparação assinada; `e0a2315`/`f316189` critério de sucesso
baseado em dados e frescor efetivos. O relatório/evidências têm checkpoint
documental próprio. Reverter somente esses commits na branch de desenvolvimento,
sem reset de checkpoints, downgrade Android ou exclusão de backups.

Próximo passo recomendado: autorizar nova sessão loopback curta e instrumentada
para a correção, com pasta/recibo novos e preservação do marcador consumido.
Somente depois planejar a homologação física do candidato no Samsung.

Continuam abertas e separadas: TLS 10054, startup, encerramento gracioso do agente,
Crashpad, GPU após bandeja, splash nativa e temperatura de CPU. HTTP 200 normal
não foi usado como evidência de resolução dessas pendências.
