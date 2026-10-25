# Encerramento gracioso — implementação isolada, 24/10/2026

**Implementado e testado somente em isolamento; não ativado no agente operacional.**
Checkpoint preservado: `0ddcd8c8d395406ede1d27af9d8d4c62eb4cd04b`, branch
`feature/ui-migration-preview`. Código: `2d345f8cd60ff4fd6ed8241b1ad030c09dca6d6f`.
O agente legado continua com os mesmos processos, listener, configuração e credenciais.

## Arquivos e integração

Todos os módulos são novos; nenhum fonte carregado pelo agente atual foi alterado.

| Arquivo em `agent/windows/` | Responsabilidade |
|---|---|
| `graceful_launcher.py` | Entrada opt-in `start`, `stop` e bootstrap interno `_worker`; supervisor aguarda filho, sem retries/kill |
| `local_shutdown.py` | Eventos Windows locais de solicitação/conclusão, com ACL exclusiva à conta |
| `graceful_runtime.py` | Admissão, drenagem de requisições, cancelamento da fila e coordenação do encerramento |
| `lifecycle_logs.py` | Esquema fechado de logs com eventos de encerramento, preservando o logger operacional antigo |

O launcher anterior, `secure_agent.py`, `secure_http.py`, `secure_apps.py`, TLS,
armazenamento, HMAC, executores e clientes Android/Electron permanecem intactos.
Não há instalação, atualização do processo ativo, monkeypatch operacional ou hot reload.
Não há endpoint HTTP de encerramento, nova permissão remota ou bridge genérica.

O novo runtime reutiliza `Store`, `AppRegistry`, handler HTTPS, certificados, validação
da LAN/perfil privado e `launch_allowed`. `DrainingServer` envolve apenas a admissão
e o acompanhamento das threads; o processamento TLS, framing e autenticação é herdado
sem alterações. `DrainingDispatcher` herda a validação/submissão original e usa os
mesmos `claim`/`finish`, incluindo autorização, expiração e proteção contra repetição.

## Solicitação local autorizada

Dois eventos manual-reset do kernel Windows: solicitação `.stop` e conclusão `.done`.
O nome deriva de SID da conta e caminho da instalação via SHA-256. O bootstrap cria
o canal **depois de adquirir o mutex de instância já existente**; o cliente local
apenas abre objetos existentes. Não cria eventos para um agente ausente.

Descritores têm proprietário atual e DACL protegida concedendo acesso somente à
conta, sem herança de handles. O cliente abre `.stop` com EVENT_MODIFY_STATE e
READ_CONTROL; `.done` com SYNCHRONIZE e READ_CONTROL. Verifica proprietário/DACL antes
de sinalizar ou esperar. Contexto elevado e argumentos extras são recusados.

Não há senha nova, token de rede, alteração de grants ou uso da identidade do Samsung
nesse controle. A autorização é a conta local do Windows: processos da mesma conta
pertencem à mesma fronteira de confiança. Administradores com tomada de posse e
malware executando como o próprio usuário não são barrados por ACL por usuário.
Fontes: [Microsoft — CreateEventW](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createeventw)
e [direitos de objetos de sincronização](https://learn.microsoft.com/en-us/windows/win32/sync/synchronization-object-security-and-access-rights).

Eventos existentes nunca são resetados/adotados por um novo worker. Se um cliente
antigo mantiver referências, a nova criação falha fechada até as referências serem
liberadas. Não há arquivo de lock ou exclusão automática de estado de outra sessão.

## Sequência de encerramento

1. O cliente local sinaliza a solicitação. Chamadas simultâneas são idempotentes.
2. Um único coordenador fecha a admissão de novas requisições e bloqueia submissões
   de aplicativos. Não modifica o protocolo de autenticação.
3. Itens aceitos **ainda na fila** recebem falha `agent_stopping`; não são disparados.
   Uma operação já reclamada/confiada ao executor conclui sua chamada normalmente.
4. A thread de aceitação é parada; o listener é fechado. Requisições já admitidas,
   incluindo threads ainda iniciando, são acompanhadas até seu término.
5. Aguarda o executor e sua persistência de resultado; faz join das threads HTTPS,
   de aplicativo e do watchdog. Não espera o usuário fechar Steam/CS2: drenagem é da
   chamada do executor, não da vida inteira de um aplicativo externo.
6. O runtime retorna ao bootstrap. O mutex é liberado **antes** de sinalizar conclusão.
7. Bootstrap fecha handles e sai; supervisor registra `child_exit` e sai. Os
   redirecionadores da venv encerram naturalmente quando seus filhos terminam.

O ACK confirma limpeza do runtime e liberação do mutex. Ainda pode haver um breve
intervalo até supervisor/redirecionadores saírem: a verificação física deve conferir
os PIDs e não deduzir ausência de processos somente pelo ACK.

## Prazo, falhas e logs

- Após **15 segundos**, registra `shutdown_deadline_exceeded` uma vez e continua
  aguardando. Não mata threads/processos nem libera o mutex com operações pendentes.
- O cliente aguarda até **30 segundos**: exit 0 = conclusão; 24 = timeout; 25 =
  canal ausente. Timeout **não confirma encerramento** e não cancela a solicitação.
  Canal ausente também não prova que o PC ou um agente legado esteja desligado;
  significa somente ausência do canal local desta versão compatível.
- Se uma operação nunca terminar, o processo pode permanecer quiescido indefinidamente.
  Falha na limpeza também mantém o lease e não gera ACK de sucesso; requer diagnóstico
  e autorização posterior. Nenhum fallback forçado ou reinício automático.
- Falha de escrita de log não pula a limpeza. O runtime sinaliza resultado não saudável
  (26); não confirma uma conclusão normal ao cliente como se os registros estivessem íntegros.
- Falha do worker é propagada pelo supervisor; não produz ACK normal. Ausência de worker
  e falha de criação do filho são distintas e não geram um agente substituto.

Destino futuro: `.runtime/agent-lifecycle-logs/`, **não criado nesta tarefa**.
JSONL com UTC, PID, evento/fase enumerados e código numérico/dependência permitida.
Sem mensagens livres de exceção, traceback, cabeçalhos, argumentos, credenciais,
chaves ou dados de memória. ACL exclusiva, 64 KiB por arquivo, três rotações além
do atual (até 256 KiB normais); diretórios e arquivos rotacionados ignorados no Git.
Não há mudança no log operacional existente.

## Testes

**37 testes novos + 77 regressões Python = 114 aprovados, zero falhas/erros/skips.**

| Requisito | Evidência isolada |
|---|---|
| Encerramento normal | Ordem de fechamento, joins e ACK após mutex liberado |
| Solicitações em andamento | Handler TCP substituto conclui após listener fechado; executor substituto conclui; fila pendente cancelada |
| Solicitações simultâneas | Quatro chamadas ao coordenador; três clientes de evento nativo, uma conclusão |
| Supervisor sem worker | Popen simulado falha, sem criação de canal ou relançamento |
| Worker termina inesperadamente | Helper descartável encerra com 7; supervisor propaga; sem ACK falso ou lease permanente |
| Mutex e processos | Lease reutilizável; supervisor/worker substitutos terminam; nenhum helper remanescente |
| Porta reutilizável | Bind de porta TCP efêmera em loopback após fechamento; sem SO_REUSEADDR novo |
| Logs | Sanitização, ACL nativa, rotação e falha de escrita sem pular limpeza |
| Prazo excedido | Aviso sem kill/ACK; lease segue ocupado até a operação substituta terminar |
| Rede e bootstrap | Espera por perfil Privado interrompível, falha de fábrica limpa listener, recuperação de rede e stop antes do bind |

O runner novo permite somente helpers `graceful_substitute.py`, namespace
`Global\LoneSmartRoom.GracefulTests.<uuid>` e portas efêmeras IPv4 em loopback.
**8776, eventos de produção e descriptografia DPAPI operacional são bloqueados.**
O helper não importa configuração/credenciais do agente. O teste de crash usa
`os._exit` somente no processo descartável. Nenhum TerminateProcess/Stop-Process/kill.
Fixtures TCP substituem o handler/TLS em teste, sem se passar por comunicação HTTPS real.

Comandos reproduzíveis:

```powershell
& .venv/Scripts/python.exe -B scripts/test-graceful-shutdown-isolated.py
& .venv/Scripts/python.exe -B scripts/test-agent-launcher-isolated.py
```

O sandbox inicialmente bloqueou a conexão de loopback do fixture (WinError 10013).
A suíte final rodou no contexto não elevado do usuário com os guards acima e passou.
Não se alterou firewall para contornar a restrição. A suíte registra zero threads
de ciclo de vida residuais; leitura do sistema confirmou zero helpers/novo launcher.

Também aprovados: 11 cenários WoL em Node, 85 assertivas de bandeja e 51 de política
Electron/preload. Os 86 registros de originais/recuperação continuam válidos.
Não foram repetidos testes malformados/excessivos TLS nem testes físicos no Samsung.

## Preservação do agente ativo

Verificações somente em leitura antes/depois confirmaram a mesma árvore:
5580 → **supervisor 6396** → 7672 → **worker/agente 17992** e listener 8776 nesse worker.
Horários de criação e imagens inalterados. Nenhuma solicitação HTTPS ou sinal local
foi enviado a esses processos nesta tarefa.

268 arquivos protegidos, excluído o banco de replay em uso, sem diferenças;
identidades, segredos criptografados, revogações, esquema e permissões do banco
inalterados. **Zero grants e zero comandos pendentes.** Não houve descriptografia.
Hash de Run e da regra de firewall idênticos antes/depois.

Backup `Windows-before-dev4-20261024T174801Z` novamente íntegro: 72 arquivos, 27
diretórios, 8.589.376 bytes, hashes/tamanhos e ACL exclusiva válidos. Android dev.7,
Electron dev.4, certificados e executores intactos. Pendência TLS continua separada.

## Reversão

O commit de código só adiciona oito arquivos. Enquanto não ativado, um `git revert`
de `2d345f8cd60ff4fd6ed8241b1ad030c09dca6d6f` retira a preparação sem mudar o agente
atualmente ativo, o Registro ou `.runtime`. Não usar reset destrutivo ou apagar dados.
Após uma ativação futura, primeiro parar normalmente a versão que usa esses arquivos
e conferir ausência de processos; somente depois reverter o código. Nenhuma reversão
ou alteração de Run foi executada.

## Procedimento físico futuro — exige autorização

**O agente legado ativo não conhece o novo canal.** Esta implementação não permite
encerrá-lo retroativamente de forma graciosa. É necessário decidir separadamente o
destino dessa sessão, por procedimento explicitamente autorizado. Não iniciar uma
nova versão enquanto o mutex/porta estiverem ocupados; não forçar a antiga neste teste.

Com o agente anterior já encerrado por procedimento aprovado:

1. Conferir checkpoint, backup, hashes, mesma conta não elevada, rede Privada, zero
   grants e ausência de listeners/processos. Não alterar Run ou certificados.
2. Autorizar **uma** abertura da entrada nova com Pythonw da venv, `-I -B`, caminho
   absoluto `agent/windows/graceful_launcher.py start`, CWD explícito na raiz.
3. Validar status autenticado no Samsung, zero permissões, mutex e listener; observar
   por 60 segundos, sem Steam/CS2, ações de energia ou testes TLS malformados.
4. Enviar **uma** solicitação local com Python CLI da mesma venv:

   ```text
   python.exe -I -B <caminho absoluto de graceful_launcher.py> stop
   ```

   Não executar este exemplo agora. O comando não recebe PID, caminho de executável
   alvo ou parâmetros remotos.
5. Conferir logs de listener fechado, conclusão, liberação do mutex e saída do filho;
   confirmar todos os PIDs/redirecionadores encerrados e ausência de listener 8776.
   Teste físico de bind/close nessa porta, se desejado, deve constar da autorização.
6. Se houver timeout, não repetir stop, não matar processos e não reiniciar Windows.
   Registrar estado e pedir autorização para diagnóstico. Só considerar aprovado
   quando listener, threads, mutex e processos estiverem efetivamente encerrados.

**Parar antes de qualquer teste físico ou migração de HKCU Run.**
