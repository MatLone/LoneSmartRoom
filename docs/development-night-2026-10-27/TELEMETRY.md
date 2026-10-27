# Telemetria Windows → Android — desenvolvimento isolado

Implementação em `feature/telemetry-android-development`, a partir de `db635c1`.
Os checkpoints `7eed61a`, `97c82ca` e `1aa7d3a` são ancestrais desse ponto;
nenhum merge ou atualização operacional foi realizado.

## Caminho implementado

Provedores existentes → cache v1 → Named Pipe protegido existente → intermediário
Python existente → `SnapshotBroker` em memória → `GET /v2/telemetry` autenticado →
`AgentClient.telemetry` → projeção Kotlin de campos permitidos → bridge restrita →
modelo JavaScript → cartões da aba Monitoramento PC.

O intermediário recebe um callback opcional e reutiliza a mesma leitura do pipe.
O wrapper `monitoring-telemetry-client.py` substitui somente o intermediário na
composição opt-in de desenvolvimento; não cria um segundo coletor. A implementação
aprovada de `monitoring-host.cjs`, o servidor operacional `secure_http.py`,
`secure_agent.py` e o launcher original permanecem intactos.

`DevelopmentTelemetryServer` é uma composição separada: rota desativada por
padrão. O wrapper só aceita identidade de desenvolvimento previamente preparada
em `.cache/telemetry-development/<session>` e usa loopback/porta efêmera.
Não lê o banco, certificados ou credenciais operacionais. A ativação LAN e sua
configuração de descoberta/porta continuam dependendo de homologação separada.
O wrapper não prepara identidades automaticamente. O pacote Windows não foi
regenerado nem recebeu esses componentes de desenvolvimento.

## Contrato e segurança

- Envelope `telemetry_version:1`, geração aleatória por sessão, snapshot v1,
  sequência, origem, unidade, timestamp UTC, idade e limite de validade.
- Lista fechada de 29 métricas: CPU, RAM, C:/D: e oito canais ADLX. Sem temperatura
  fictícia de CPU. VRAM mantém MB do SDK; memória física mantém bytes/GiB na tela.
- Campos desconhecidos não são encaminhados ao renderer; fontes e unidades
  são conferidas. Nulos, zero válido, aquecimento, erro e desatualizado são distintos.
- HMAC da rota exata, nonce/antirreplay e revogação usam o mecanismo existente.
  Pareamento autoriza leitura; grants continuam exclusivos dos comandos. Nenhum
  grant é criado. Certificado, hostname, pinagem e redirects proibidos são mantidos.
- Resposta ≤32 KiB; bucket global limitado (2 consultas/s, burst 4), timeout
  Android de conexão/leitura 5 s cada. Sem parâmetros de caminhos ou comandos.
- Idade inclui atraso no servidor, residência no cache e tempo de transporte.
  Releitura da mesma sequência não renova amostras. ADLX ≤1,5 s, GPU 3/11 s
  conforme cadência, capacidades 180 s. Nenhum limite foi relaxado.
- Android consulta a cada 2 s com backoff, uma requisição pendente, somente na aba
  visível e com atividade em primeiro plano. Resultados tardios são descartados.
  Após retomada/reconexão, cada métrica antiga fica oculta até timestamp novo.

## Validação executada

- 10 testes Python: cache/projeção e HTTPS real **apenas em loopback**, identidade
  e banco sintéticos, sem porta 8776. Autenticação, replay, revogação, rota assinada,
  rate limit, certificado não confiável, resposta sanitizada e expiração.
- 23 verificações Node: resposta HTTPS de teste → modelo/UI Android reais,
  origem simulada explícita, zero/nulo, retomada, sequência, fonte/unidade/idade.
- Regressões: 378 testes Python, sem operações externas; 891 verificações Node
  contadas em 12 suítes (uma suíte adicional sem contador próprio nesse total).
- Renderer Android real em Chromium isolado: 352 verificações, 63 combinações
  responsivas, zero acesso a dispositivo/sensores ou requisições externas.
- `assembleDebug`, `lintDebug`: aprovados; 0 erros, 10 avisos preexistentes.
  `testDebugUnitTest` retornou NO-SOURCE; não representa testes Kotlin executados.
  Teste JVM do código WoL aprovado, sem envio UDP.

A sandbox bloqueou inicialmente sockets loopback (10013) e a conexão local do
Gradle. Os mesmos testes isolados foram executados com a permissão de ferramenta
necessária, sem mudança de firewall. Uma regressão visual encontrou texto longo
e CSS inline incompatível com CSP; ambos foram corrigidos mantendo CSP restrita.
Não foram adicionadas dependências. Testes de recursos que precisam `sharp`
dependem do runtime já fornecido pelo ambiente; a primeira chamada sem caminho
do módulo falhou e não foi tratada como aprovação.

## Limites e próxima homologação

Não houve leitura física de sensores, consulta ao agente ativo, conexão ADB ou
instalação. O parser Kotlin foi compilado/lintado; os testes executáveis de payload
usaram o modelo/UI JavaScript real, não um dispositivo Android. O fluxo LAN no
Samsung ainda precisa de uma composição de desenvolvimento autorizada, identidade
própria e validação física posterior. O APK aprovado dev.9/v23 foi preservado;
o `app-debug.apk` regenerado é somente produto de compilação local, não atualização
aprovada e não deve ser instalado com a numeração atual.

TLS 10054, startup, encerramento gracioso, Crashpad, GPU após bandeja, splash
nativa e sensor térmico da CPU continuam pendentes. HTTP 200 em loopback não
resolve essas pendências. Não houve nova verificação operacional de grants;
nenhum código desta etapa concede permissões.

Reversão: reverter o commit desta etapa na branch de desenvolvimento. Não há
migração de dados, Registro ou instalação a desfazer. Não reverter checkpoints
anteriores nem substituir o APK aprovado.
