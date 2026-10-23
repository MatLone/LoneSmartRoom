# Abertura de aplicativos permitidos — extensão HTTPS v2

Compatível com o pareamento e `/v2/status` existentes. Parear não concede
permissão para executar aplicativos. Identificadores válidos: **steam**, **cs2**.
Não existem parâmetros de caminho, URI, argumentos, terminal ou script.

## Permissões locais

`app_permissions(device,app)` é criado de forma aditiva no mesmo SQLite. Dispositivos
existentes e novos começam sem linhas/permissões. Não há endpoint remoto para
conceder permissões. No Windows, o operador seleciona o dispositivo e os apps:

```powershell
# Substituir pelo identificador escolhido na listagem LOCAL de dispositivos.
$deviceId = 'IDENTIFICADOR_HEXADECIMAL_DE_32_CARACTERES'
.\scripts\manage-agent.ps1 -Action app-permissions -DeviceId $deviceId
.\scripts\manage-agent.ps1 -Action grant-apps -DeviceId $deviceId -Apps @('steam')
.\scripts\manage-agent.ps1 -Action revoke-apps -DeviceId $deviceId -Apps @('steam')
```

Esses comandos alteram permissões, sem abrir aplicativos. Revogar o dispositivo
com o comando existente bloqueia também as APIs novas. Revogar apenas um app
preserva status/pareamento. A autorização é reavaliada antes do despacho de cada
item da fila; não cancela uma abertura já entregue ao Windows.

## Autenticação e rotas

Mesmos quatro headers X-Lone e HMAC-SHA256 existentes. O canonical agora é usado
também para POST e inclui **os bytes integrais do corpo**, sem normalizar JSON:

```text
LSR2\n{device}\n{timestamp}\n{nonce}\n{METHOD}\n{PATH}\n{body bytes}
```

O atalho Kotlin de quatro argumentos de status continua gerando o canonical antigo.
Timestamp ±60 s e nonce persistido continuam obrigatórios. Headers de autenticação
duplicados são recusados. HTTPS/pin, hostname, CIDR e perfil Privado são preservados.

| Rota | Resultado |
| --- | --- |
| `GET /v2/apps` | 200, `allowed_apps`: lista autorizada para o dispositivo autenticado |
| `POST /v2/apps/commands` | 202 para solicitação aceita; duplicata pode devolver o resultado já conhecido |
| `GET /v2/apps/commands/{request_id}` | Resultado somente do próprio dispositivo; 404 para outro proprietário |

POST exige objeto UTF-8, até 1024 bytes, Content-Type application/json e exatamente:

```json
{"request_id":"0123456789abcdef0123456789abcdef","app":"steam","confirmed":true}
```

`confirmed` precisa ser o booleano true. A confirmação nativa Android é adicional
à permissão Windows; esse campo sozinho não concede autorização. Campos extras,
nomes desconhecidos, duplicidade de chaves, NaN/Infinity, framing ambíguo, queries
na rota e IDs fora do formato são recusados. O servidor não recebe texto livre.

401: autenticação/replay; 403: permissão ausente; 400: payload inválido;
409: ID já usado com outro app; 429: fila/taxa/histórico; 503: serviço de apps
indisponível. As antigas rotas genéricas `/v1/action` e `/v2/action` continuam 404.
Sleep/restart/shutdown nunca são apps permitidos.

## Estados, idempotência e limites

| Estado apresentado | Evidência |
| --- | --- |
| Solicitado | Android salvou ID/app no cofre e iniciou o envio; ainda não há aceite confirmado |
| Aceito | Registro durável e entrada na fila; execução ainda não confirmada |
| Executado | Executor v1.5 retornou após entregar a URI fixa ao Windows |
| Falha | Recusa, expiração, falha do launcher ou resultado incerto explicado ao usuário |

`executed` **não confirma processo/janela/jogo carregado**. A resposta inclui
`process_running_verified=false`, e a interface explica essa limitação. O executor
v1.5 fornece confirmação de despacho, não PID. A comprovação visual fica para o
teste físico autorizado.

`(device,request_id)` é persistido e nunca é redisparado automaticamente. ID igual
com corpo de outro app gera conflito. Repetir a requisição HMAC original gera 401;
consultar/repetir o mesmo ID com nonce novo devolve estado, sem nova abertura.
O cliente não repete POST em timeout e preserva `pending_launch` no cofre para GET.

Um único worker e fila de oito itens, além do item em execução. Máximo de seis
novos pedidos por minuto/dispositivo e 1000 registros por dispositivo. Registros
não são apagados automaticamente para não perder a proteção contra duplicação.
Uma fila com espera superior a 30 s é recusada antes de executar. Perfil Privado,
revogação e permissão do app são conferidos novamente nessa etapa.

Antes do despacho, o estado interno `dispatching` é persistido. Após reinício,
itens aceitos pendentes viram `failed/agent_restarted`; os que estavam em despacho
viram `failed/execution_uncertain`. Nunca há redisparo automático. A incerteza
entre entrega ao Windows e gravação do resultado é preservada, sem promessa de
execução exatamente uma vez em caso de falha do sistema.
