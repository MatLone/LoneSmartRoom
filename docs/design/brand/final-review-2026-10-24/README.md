# Revisão final da marca e diagnóstico TLS

Data: 24/10/2026, America/Sao_Paulo. Branch: `feature/ui-migration-preview`.
Base inspecionada: `529e219332e62c7779c2b8845c7a02be5abf01a7`.

A marca existente foi apresentada para aprovação, sem redesenho ou alteração de código. As duas execuções completas da suíte passaram, mas um diagnóstico isolado reproduziu o reset TLS. Portanto, a intermitência continua pendente; testes completos verdes não constituem correção dessa falha.

## Imagens para aprovação

| Arquivo | Conteúdo |
| --- | --- |
| [00-referencia-vetor-comparativo.png](00-referencia-vetor-comparativo.png) | Referência oficial completa, recorte original e logo horizontal atual lado a lado. |
| [01-detalhes-ampliados.png](01-detalhes-ampliados.png) | Símbolo angular, LONE e SMART ROOM ampliados. |
| [02-cabecalhos-android.png](02-cabecalhos-android.png) | Cabeçalhos reais da prévia nas larguras 390, 360 e 320 CSS px. |
| [03-icone-splash-propostos.png](03-icone-splash-propostos.png) | Ícone e splash propostos, referências e ícone em 48/72/96/144 pixels. |

As capturas individuais estão em [captures](captures/). As imagens completas de viewport incluem uma faixa externa de demonstração de 28 px. Os recortes PNG do cabeçalho excluem somente essa faixa, com coordenadas registradas em [header-metrics.json](header-metrics.json). Não são capturas do Samsung: são imagens da interface integrada renderizada pela prévia local, com bridges reais ausentes e ações Steam/CS2 desabilitadas. A versão pública mostrada é metadado da prévia, sem acesso às credenciais.

A comparação utiliza a [referência original preservada](../reference/approved-reference.png), de 1672 × 941 pixels, e os [PNGs já exportados](../exports/). Os cinco SVGs canônicos permanecem em `apps/android/app/src/main/assets/brand/`. Os recortes e suas coordenadas estão em [reference-crops](reference-crops/) e [comparison-crops.json](comparison-crops.json). Ampliações não recuperam detalhes ou a fonte original. A proporção de cada recorte foi preservada; na prancha de detalhes, as alturas visuais foram aproximadas para comparação.

## Avaliação visual e diferenças encontradas

- **Símbolo:** a composição angular vermelha está presente. Há diferenças visíveis na proporção do detalhe interno, nos retornos do contorno e no brilho. A resolução e a perspectiva da referência impedem comprovar equivalência exata de espessura ou geometria.
- **LONE:** a recriação tem cantos retos/chanfrados, especialmente no O; a referência aparenta contornos mais suavizados. São contornos vetoriais reconstruídos, não a fonte original identificada.
- **SMART ROOM:** os traços monolineares e o espaçamento regular diferem da aparência rasterizada da referência. O peso é particularmente fino na redução para o cabeçalho.
- **Alinhamento:** a logo mantém a proporção do SVG e margens no cabeçalho. Não houve transbordamento horizontal da página, do cabeçalho, da imagem ou da área principal nas três larguras medidas. LONE permanece legível; o subtítulo exige decisão visual antes da aprovação.
- **Ícone e splash:** a referência inclui moldura do dispositivo, perspectiva e iluminação de mockup; a proposta é uma arte plana. O ícone mantém reconhecimento do símbolo nos tamanhos apresentados, com perda natural de detalhe/brilho em 48 px. Isso não valida ainda máscaras ou áreas seguras do futuro ícone adaptativo.

| Viewport útil | Largura da logo | Altura estimada LONE | Altura estimada SMART ROOM | Traço estimado do subtítulo |
| --- | ---: | ---: | ---: | ---: |
| 390 × 844 | 216 px | 21,0 px | 5,54 px | 0,44 px |
| 360 × 800 | 194 px | 18,9 px | 4,97 px | 0,40 px |
| 320 × 740 | 194 px | 18,9 px | 4,97 px | 0,40 px |

As alturas são projeções geométricas dos contornos do SVG, não tamanhos CSS de fonte. O subtítulo em aproximadamente 5 px é uma limitação concreta de leitura nesta aplicação. Sua aprovação pode ser separada da aprovação do símbolo e de LONE. Nenhum aumento de peso, mudança de espaçamento, alteração de logo ou ajuste do layout foi aplicado nesta revisão. Não houve avaliação física no Samsung nem certificação de acessibilidade.

## Testes executados

| Verificação | Resultado desta revisão |
| --- | --- |
| `scripts/test-safe.ps1`, execução 1 | 74/74 Python, 19,651 s; teste legado com mocks aprovado; versão/comandos Android aprovado; 11 cenários WoL aprovados. |
| `scripts/test-safe.ps1`, execução 2 | 74/74 Python, 22,450 s; mesmas verificações complementares aprovadas. |
| `scripts/test-android-ui.ps1` | 60 asserções do renderer; 15 casos responsivos; bridges falsas e nenhuma requisição externa. |
| `scripts/test-android-packet.ps1` | Validação do pacote WoL Kotlin aprovada, sem envio UDP. |
| `scripts/verify-preservation.py` | 86 registros de preservação aprovados. |
| Diagnóstico TLS separado | 48 requisições independentes; 5 resets reproduzidos; zero chamadas ao executor substituto. |

Logs completos das duas execuções e do renderer estão em [evidence](evidence/). Nenhum teste existente foi modificado, ignorado ou repetido automaticamente para mascarar resultado. Não houve teste físico de WoL nesta revisão. Build, lint Android e assinatura não foram reexecutados: a nova build com recursos nativos pertence à próxima etapa após aprovação visual.

## Reset TLS: evidências e interpretação

Os registros anteriores de falha `ConnectionResetError / WinError 10054` continuam válidos, mesmo com as duas execuções completas atuais aprovadas. O experimento separado usa o servidor e a fixture originais dos testes, uma identidade temporária e banco descartável, escutando exclusivamente em `127.0.0.1` numa porta efêmera. Não usa a porta 8776, dados de pareamento reais ou grants de produção.

| Caso diagnóstico | Respostas 400 integralmente recebidas | Resets | Total |
| --- | ---: | ---: | ---: |
| JSON inválido, 4 bytes | 12 | 0 | 12 |
| JSON inválido, 1024 bytes | 12 | 0 | 12 |
| Corpo de 1025 bytes enviado integralmente | 7 | **5** | 12 |
| Content-Length 1025, sem enviar o corpo | 12 | 0 | 12 |

Nos cinco resets do corpo de 1025 bytes, três ocorreram durante a leitura do corpo da resposta, após receber status 400, e dois antes de obter o status. Logo, contar somente o código HTTP esconderia parte do problema. Não houve despacho de aplicativo. Ambiente: Python 3.13.3 / OpenSSL 3.0.16. O experimento não tem retries; seu término normal significa que registrou os resultados, não que os 48 casos passaram. Fonte e resultados completos: [tls-diagnostic.py](evidence/tls-diagnostic.py), [tls-diagnostic.json](evidence/tls-diagnostic.json). Para reprodução futura autorizada, executar o script a partir da raiz do repositório; ele grava na pasta ignorada `.cache/validation/final-review-2026-10-24/`.

**Evidência do código:** em `agent/windows/secure_http.py`, `Handler.body()` rejeita tamanho superior a 1024 e marca `_body_read` sem consumir o corpo. `reply()` só drena um corpo limitado quando essa marca é falsa. Assim, o corpo excessivo permanece potencialmente pendente quando a resposta 400 é enviada e a conexão é fechada. `StatusServer.process_request_thread()` fecha o socket sem realizar explicitamente um handshake de encerramento TLS.

**Inferência mais sustentada:** a combinação de payload pendente e encerramento da conexão explica melhor a concentração de resets no caso de 1025 bytes enviados. O significado de 10054 é conexão existente encerrada à força pelo par, conforme a [documentação oficial Winsock](https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-error-codes-2). O código do erro, isoladamente, não determina a causa. Não foi feita captura de pacotes para comprovar a sequência exata TLS/TCP, e esta amostra pequena não estima uma taxa geral de falha.

**Não demonstrado:** falha de certificado, perda de pareamento, regressão de status autenticado ou problema no launcher. O diagnóstico incide na entrega da resposta de rejeição a uma requisição excessiva; não comprova que tráfego normal apresente o mesmo sintoma.

**Proposta para etapa separada:** revisar um descarte limitado de payload inequivocamente enquadrado e moderadamente excessivo, ou um encerramento TLS ordenado com timeout, preservando rejeição de requisições ambíguas, limite funcional de 1024 e limites de recursos. A API [`SSLSocket.unwrap()`](https://docs.python.org/3.13/library/ssl.html#ssl.SSLSocket.unwrap) realiza handshake de encerramento TLS; isso é uma alternativa a avaliar, não uma correção aplicada. Antes de alterar produção, testar corpo ausente/lento/muito grande, enquadramento duplicado/ambíguo, rejeição sem despacho e regressões de HMAC, pinning, grants e status. Não aumentar limites, consumir upload ilimitado ou aceitar reset como sucesso de teste.

## Preservação e próximos passos

Os hashes dos cinco SVGs e da referência foram conferidos contra `brand-manifest.json`. A árvore de código permaneceu igual à base desta revisão. Android/Kotlin, Wake-on-LAN, armazenamento, HTTPS, certificados, credenciais, pareamento, permissões e executores Steam/CS2 não foram alterados. Nenhum aplicativo real foi iniciado; nenhum dispositivo foi atualizado. O ícone nativo e a splash nativa do Samsung permanecem como estavam.

Os checkpoints funcionais e visuais anteriores permanecem no histórico. Esta entrega contém somente documentação, imagens e evidências do diagnóstico. O [manifesto de revisão](review-manifest.json) registra hashes, dimensões, resultados e limites da validação.

Próximo passo visual: decidir sobre as diferenças do vetor e a leitura do subtítulo. Depois da aprovação, preparar separadamente ícone adaptativo, splash nativa e uma nova build preservando pacote, armazenamento e assinatura original. O reset TLS permanece como pendência técnica explícita para uma correção específica autorizada, sem alterações nesta entrega.
