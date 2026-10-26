# TLS 10054 — recomendação separada, sem correção operacional

Esta sessão não enviou corpos excessivos, ambiguidades HTTP ou requisições
malformadas. Nenhuma consulta HTTPS foi alcançada devido ao gate de identidade.
Não existe evidência nova sobre a pendência TLS; ela **não está resolvida**.

## Evidência existente

- [Investigação de limites TLS de 24/10](../design/brand/compact-review-2026-10-24/TLS.md):
  resets concentrados em rejeições de corpos excessivos/ambíguos; descarte
  limitado melhorou casos moderados na fixture, sem resolver todos os casos.
  `unwrap()` isolado não foi uma solução demonstrada.
- [Ocorrência intermitente da suíte anterior](../diagnostics-adapters-2026-10-26/validation-results.json):
  `test_pair_rate_limit_and_request_limit`, corpo de 1.025 bytes e erro ao ler
  resposta esperada 400. Execuções subsequentes aprovadas não eliminaram a falha.
- No fonte atual `agent/windows/secure_http.py`, `body()` rejeita excesso acima
  de 1.024 e marca `_body_read=True` antes de consumir. `reply()` só faz descarte
  quando essa marca é falsa. Pode restar corpo pendente ao enviar 400 e fechar.

Rejeitar a requisição é intencional; `Connection: close` também. O defeito de
entrega observado é o cliente receber reset antes de ler a resposta completa.
Fechamento com dados pendentes é a hipótese mais sustentada pelas fixtures;
não há nova captura de rede provando a sequência exata no agente operacional.

## Proposta mínima para etapa autorizada futura

Separar estado de enquadramento inválido de estado de corpo efetivamente
consumido. Para enquadramento inequívoco (Content-Length único, decimal ASCII,
Content-Type JSON único e ausência de Transfer-Encoding), avaliar descarte
somente do excesso moderado **1.025–4.096 bytes**, com teto absoluto de bytes e
deadline curta absoluta. Depois devolver 400 e fechar. **O limite de aceitação
continua 1.024 bytes**, sem encaminhar excesso à autenticação ou a executores.

Para comprimentos maiores, duplicados, ambíguos ou upload incompleto/lento,
preservar rejeição e recursos limitados. Definir explicitamente a garantia de
protocolo: entrega integral de resposta versus fechamento seguro sem despacho.
Não alterar testes para tolerar silenciosamente o reset, aceitar requisições
antes rejeitadas, desativar TLS ou aumentar o corpo funcional permitido.

Antes de qualquer aplicação, executar fixtures isoladas de 0/1/1.024/1.025/4.096/
4.097 bytes, cabeçalhos duplicados, TE+CL, envio parcial/lento, timeout e 12
conexões simultâneas, com orçamento agregado limitado. Conferir ausência de
despacho, HMAC/replay/revogação/grants, fechamento e entrega da resposta. Só
depois, mediante autorização específica, validar compatibilidade Android.

Nenhum arquivo do agente, certificado, limite ou instalação foi alterado aqui.
