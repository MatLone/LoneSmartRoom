# Recuperação manual do agente HTTPS — 25/10/2026

**Recuperação aprovada: agente ativo, HTTPS autenticado e Samsung Conectado com o
pareamento anterior. Uma única inicialização real; nenhum encerramento realizado.**

Base preservada: `d5eeeb6862b31ceb5e81427842339a35d59deecd`, incluindo
`33765ab6a5b1745509185a777ca906e9f6f986cf` e os checkpoints anteriores. Branch
`feature/ui-migration-preview`. Esta entrega acrescenta documentação/evidências;
nenhum fonte operacional foi alterado.

## Verificações anteriores à partida

Recibos de [pré-verificação](preflight.json) e [estado inicial](system-before.json):

- Zero processos Python de `agent_launcher.py`, `secure_agent.py` ou
  `graceful_launcher.py`; nenhum listener TCP 8776.
- Sete arquivos da implementação/testes correspondem ao manifesto usado na
  validação física anterior. `agent/windows/agent_launcher.py` mantém SHA-256
  `8f137269555ad33b744c4b19b65ac5726785f6d1482ff3182f5f3a495ee32a08`.
- 268 arquivos protegidos, exceto banco mutável de replay, correspondem ao recibo
  histórico. Identidades, segredos ainda cifrados, revogações, permissões e esquema
  do banco correspondem logicamente ao teste validado anterior.
- `quick_check=ok`, zero grants, zero comandos pendentes, uma identidade autorizada.
- Certificado vigente e pin TLS original correspondente. A chave cifrada existente
  foi carregada com seu certificado em SSLContext local, sem listener, sem alterar
  os arquivos e sem persistir material descriptografado.
- Configuração da LAN corresponde à aprovada, perfil Privado, token não elevado.
- ACL exclusiva da conta nos logs existentes. Hashes Run/firewall correspondentes
  aos recibos históricos, sem alteração.

Somente a entrada **`agent_launcher.py`** foi escolhida. `graceful_launcher.py`,
`local_shutdown.py` e o runtime novo não foram usados. Não houve concessão de grants,
nova identidade, pareamento ou alteração de configuração para viabilizar a recuperação.

## Partida única

Às **01:18:26,940 local / 04:18:26.940 UTC**, iniciado uma única vez:

```text
"<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.venv\Scripts\pythonw.exe" -I -B "<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\agent\windows\agent_launcher.py"
```

CWD explicitamente definido como a raiz `Lone_Smart_Room_2.0`, janela oculta,
sem RunAs/elevação. Um marcador criado em modo exclusivo **antes** de Start-Process
impediu nova tentativa. [Recibo de lançamento](launch-attempt.json).

Um erro de conversão de data no helper PowerShell ocorreu antes do marcador e
antes de Start-Process. A ausência de marcador foi confirmada, o helper corrigido
e a pré-verificação atualizada. Isso não foi uma partida nem uma falha do agente.
Depois da partida real, não houve retry ou segunda inicialização.

| Papel | PID | Pai | Identidade |
|---|---:|---:|---|
| Redirecionador inicial Pythonw da venv | 17772 | 13852 | Entrada validada e imagem esperada |
| Supervisor Pythonw base | **400** | 17772 | Mesma conta, token não elevado, imagem esperada |
| Redirecionador Pythonw do worker | 10996 | 400 | Entrada interna `--worker` |
| Agente/worker Pythonw base | **8680** | 10996 | Mesma conta, token não elevado, proprietário de 8776 |

São uma sessão supervisor/agente e dois redirecionadores da venv, não quatro agentes.
Todos usam a entrada validada; nenhum processo de launcher gracioso ou `serve`
direto paralelo foi encontrado. Os horários de criação ficaram iguais no início e
no final. [Árvore iniciada](system-started.json), [verificação nativa](native-readonly.json).

## Comunicação e estabilidade

| Verificação | Resultado |
|---|---|
| Listener | Único em 8776, PID 8680, endereço LAN sem wildcard/loopback |
| Mutex | Objeto existente aberto, proprietário/DACL conferidos; tentativa de espera zero retornou ocupado. Nenhum segundo launcher foi criado |
| GET `/v2/status`, início/final | HTTP 200, `agent=online`, TLS 1.3 |
| GET `/v2/apps`, início/final | HTTP 200, `allowed_apps=[]`, TLS 1.3 |
| Identidade TLS | Cadeia de confiança local, hostname e pin conferidos antes do envio da autenticação |
| Credencial de consulta | Identidade existente, somente em memória; nenhuma identidade desktop criada e nenhum segredo copiado para arquivo/log/Git |
| Observação dedicada | **67,238 segundos**, 13 amostras, mesmos PIDs/horários de criação e listener esperado em todas |
| Logs | Um arquivo, dez registros no total; cinco novos eventos de bootstrap esperados, zero eventos novos de erro, esquema sanitizado e ACL exclusiva |
| Verificação final | Mesma árvore/listener às 01:22:24 local; integridade/grants novamente conferidos às 01:23:20 local |

Os intervalos entre amostras não garantem observabilidade de todos os estados
transitórios. Esta é uma prova curta de recuperação/estabilidade, não teste de
boot automático ou ensaio prolongado de disponibilidade.

Recibos: [GETs iniciais](authenticated-initial.json), [GETs finais](authenticated-final.json),
[observação](observation.json), [amostras](observation-samples.json).

## Validação física do Samsung

Após orientação para abrir o Lone Smart Room e atualizar **somente status**, o
usuário confirmou diretamente: **“Abriu e mostra Conectado, sem novo pareamento”**.

Essa é uma confirmação física do usuário no Galaxy S25 FE; não houve captura ADB,
instalação, atualização, limpeza de dados ou alteração do armazenamento Android.
O pareamento anterior foi reutilizado. Não foram enviados Steam, CS2, WoL ou energia.

## Preservação e estado final

[Verificação final](preservation-after.json):

- Zero diferenças nos 268 arquivos protegidos fora do banco de replay.
- Banco íntegro; identidades, segredos cifrados, revogações, permissões e esquema
  logicamente iguais aos da pré-verificação; **zero grants e zero comandos pendentes**.
- As consultas autenticadas consomem nonces no banco normalmente. Essa escrita
  anti-repetição não representa troca de credencial, novo pareamento ou concessão.
- Run e firewall mantêm os hashes originais. Nenhum serviço, tarefa, driver,
  roteador, início automático ou configuração Windows foi alterado.
- Android dev.7 e Electron dev.4 não foram modificados ou instalados novamente.
  Checkpoints, fontes, APKs e backups não foram substituídos. Não foi realizada
  nova auditoria física completa dos backups nesta tarefa.
- Não houve coleta real de sensores, correção TLS ou ativação do encerramento
  gracioso. Não houve dump, leitura/escrita de memória dos processos ou injeção.

**Agente deixado ativo deliberadamente, PID 8680; supervisor 400; porta 8776 ativa;
Samsung confirmado Conectado.** Não se tentou encerrar o serviço para finalizar
o teste. Helpers de diagnóstico retornaram normalmente; não há nova instância
operacional paralela criada por eles.

## Pendências e próxima autorização

- Inicialização automática permanece sem validação: Run ainda chama o agente
  diretamente e a recuperação manual não prova que o Windows o despachará no login.
- [Plano separado para distinguir despacho e bootstrap](AUTOSTART-DIAGNOSTIC-PLAN.md),
  com evidência independente do Windows e matriz de interpretação. Não foi iniciado
  trace, habilitada auditoria, alterado Run ou executado login/logoff/reboot.
- [TLS de corpos excessivos/ambíguos](../design/brand/compact-review-2026-10-24/TLS.md)
  continua pendente; esta validação enviou apenas GETs normais autenticados.
- [Encerramento gracioso](../graceful-shutdown-2026-10-24/README.md) continua sem
  validação física e não pode ser presumido disponível nesta sessão antiga.
- [Coleta física de métricas](../monitoring-basic-2026-10-25/README.md) continua adiada;
  nenhuma autorização implícita de retomada decorre da reconexão do Samsung.

Reversão desta entrega: reverter apenas o commit documental se necessário. Isso
não encerra o agente nem reverte o consumo normal de nonces. Qualquer parada ou
transição operacional futura exige procedimento e autorização próprios; não usar
rollback de banco, remoção de credenciais ou encerramento forçado como reversão.
