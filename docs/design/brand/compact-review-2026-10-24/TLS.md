# TLS: requisições excessivas e encerramento de conexão

## Resultado e escopo

A falha de transporte foi reproduzida no código atual, apesar de a suíte completa passar nesta execução. A rejeição de corpos superiores a **1024 bytes** é intencional e permanece correta. O defeito investigado é perder a resposta de erro durante o fechamento da conexão, não permitir um comando excessivo.

O diagnóstico usa Python 3.13.3 / OpenSSL 3.0.16, certificados temporários com validação ativa, banco e dispositivo sintéticos da fixture existente, sem grants de aplicativos, servidores em `127.0.0.1` e portas efêmeras. Nenhuma chamada atinge o serviço operacional na porta 8776. São 12 rodadas independentes de 12 cenários para cada uma de três variantes, **432 requisições na matriz final**, sem retries.

1. **Atual:** `StatusServer` e `Handler` originais, sem mudanças.
2. **Proposta de descarte limitado:** herda o handler e altera apenas o tratamento de corpos inequivocamente enquadrados, de 1025 a 4096 bytes. Consome no máximo o tamanho declarado, com prazo absoluto de 0,5 s, e continua respondendo 400. Não parseia esse corpo nem o autentica/despacha como comando.
3. **Proposta de unwrap isolado:** mantém o handler original e tenta handshake de encerramento TLS com timeout de 0,5 s após a resposta. Não drena o corpo.

As duas propostas existem somente no script diagnóstico. Nenhuma foi aplicada ao agente ou à suíte de regressão existente.

## Matriz final

Cada célula contém **respostas 400 completas / total 12**. Uma resposta só é completa após ler todo o JSON `ok:false` e conferir seu Content-Length. Receber somente o status 400 não basta.

| Cenário | Atual | Descarte limitado | Unwrap isolado |
| --- | ---: | ---: | ---: |
| JSON inválido, 1 byte | 12/12 | 12/12 | 12/12 |
| JSON inválido, 1023 bytes | 12/12 | 12/12 | 12/12 |
| JSON inválido, 1024 bytes | 12/12 | 12/12 | 12/12 |
| Corpo de 1025 bytes | **9/12** | **12/12** | 12/12 |
| Corpo de 4096 bytes | **9/12** | **12/12** | 12/12 |
| Corpo de 4097 bytes | 9/12 | 10/12 | 12/12 |
| Corpo de 65536 bytes | 6/12 | 10/12 | 11/12 |
| Declara 1025, não envia corpo | 12/12 | 12/12 | 12/12 |
| Declara 1025, envia 17 bytes | 11/12 | 12/12 | 12/12 |
| Declara 1025, tenta enviar 64 bytes aos poucos | **0/12** | **12/12** | **0/12** |
| Content-Length duplicado | 10/12 | 12/12 | 12/12 |
| Transfer-Encoding junto com Content-Length | 10/12 | 10/12 | 12/12 |

No caso lento, o cliente envia blocos de 16 bytes com intervalos de 0,15 s. Quando a conexão fecha durante o envio, a carga pode não ser inteiramente transmitida: o campo `sentBytes` dos registros representa a carga planejada, não confirmação de entrega ao servidor. O código atual produziu 12 `ConnectionResetError`; o unwrap isolado produziu 12 `ConnectionAbortedError`, portanto **zero resets não significa sucesso**. O descarte limitado entregou 12 respostas completas nesse caso, com maior duração observada de 0,514 s. Corpo ausente e parcial tiveram máximos de aproximadamente 0,520 e 0,530 s, incluindo processamento e agendamento além do orçamento de leitura.

Nas demais células incompletas da matriz final houve `ConnectionResetError`. O unwrap isolado não completou nenhum dos 147 handshakes de encerramento contabilizados: retornou erros de conexão ou SSL. Não é recomendado como correção isolada a partir desta amostra. A documentação Python descreve [`unwrap()` como handshake de encerramento TLS](https://docs.python.org/3.13/library/ssl.html#ssl.SSLSocket.unwrap); sua mera chamada não garante que o par coopere.

Após cada variante, a fixture confirmou status autenticado 200, lista de permissões vazia e comando sem grant rejeitado com 403. **Zero chamadas ao executor substituto**, além de zero programas reais abertos. Essas verificações são complementares à suíte completa de autenticação, replay, revogação, TLS, Steam/CS2 e WoL.

## Evidências e causa provável

Em `agent/windows/secure_http.py`, `body()` rejeita tamanho superior a 1024 antes da leitura e marca `_body_read=True`. O descarte existente em `reply()` só ocorre quando essa marca é falsa. Assim, um corpo excessivo pode continuar pendente quando o servidor escreve a resposta e fecha a conexão TLS.

Separação dos comportamentos:

- **Rejeição intencional:** corpo inválido, excessivo ou ambíguo não deve virar um comando; o resultado lógico permanece 400 e não há despacho.
- **Fechamento intencional:** a resposta anuncia `Connection: close`; terminar a conexão é parte da política atual, especialmente para enquadramento inseguro.
- **Reset inesperado para a suíte:** o cliente recebe reset antes de consumir a resposta 400 completa. Isso quebra a expectativa de entrega dessa resposta, mesmo que o servidor tenha rejeitado o comando corretamente. O código 10054 indica encerramento forçado pelo par, conforme [Winsock](https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-error-codes-2); sozinho ele não identifica a causa.

**Hipótese mais sustentada:** fechamento com dados de requisição pendentes causa a perda intermitente da resposta em Windows/TLS/TCP. A concentração nos corpos excessivos e a melhora com descarte limitado sustentam essa interpretação. O teste sem corpo e os JSONs inválidos dentro do limite ajudam a separar excesso/framing de um erro geral de certificado. Ainda não há captura de pacotes que demonstre a sequência exata. A amostra não comprova a ausência futura de resets nem estima taxa de produção.

## Correção mínima proposta, não aplicada

Revisar exclusivamente o descarte de corpo moderadamente excessivo em `body()`/`reply()`: Content-Length único, ASCII decimal, tipo JSON único, ausência de Transfer-Encoding, tamanho **1025..4096**, consumo limitado ao declarado e **deadline absoluta curta**, restaurando o timeout original. Em seguida rejeitar com 400 e fechar. O limite funcional permanece **1024**; os bytes descartados não chegam à autenticação de comando ou ao executor.

Para corpo maior que o teto de descarte, framing duplicado/ambíguo e dados recebidos após a deadline, preservar rejeição rápida e limite de recursos. Nesses casos, a política precisa explicitar se garante apenas fechamento sem despacho ou se também pretende garantir entrega de 400; não se deve trocar silenciosamente a asserção atual por tolerância a reset. Mesmo na proposta limitada, os casos de 4097, 65536 e Transfer-Encoding ainda tiveram resets. A proposta resolve o alvo moderado na amostra, **não todos os fechamentos adversariais**.

Antes da aplicação: revisar o orçamento agregado das 12 conexões simultâneas, concorrência de clientes lentos e casos de delimitadores duplicados/comprimentos malformados; converter os casos relevantes em regressões estáveis; validar o comportamento com cliente Android; repetir testes de segurança sem alterar HMAC, replay, grants, endpoints ou TLS. Não adotar descarte ilimitado, aumentar o limite de aceitação ou registrar conteúdo/autenticação.

## Reprodução e registros

Execução explícita a partir da raiz do repositório, com o ambiente já instalado:

```powershell
.venv/Scripts/python.exe -B tests/diagnostics/tls_body_limits.py --output .cache/validation/compact-brand-2026-10-24/tls-body-limits-final.json
```

O script valida que a saída permanece na pasta ignorada de validação. CLI concluída significa coleta concluída, não que todos os transportes passaram. Os resultados finais estão em [evidence/tls-body-limits-final.json](evidence/tls-body-limits-final.json). Também foi preservada a [matriz inicial](evidence/tls-body-limits-initial.json), de 396 requisições, anterior ao refinamento do prazo absoluto e à adição do caso lento. Os resultados anteriores de 5/12 resets na revisão precedente continuam registrados; diferenças de frequência são esperadas numa falha intermitente e não foram apagadas.
