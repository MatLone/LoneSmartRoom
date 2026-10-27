# Entrega: telemetria real Windows → HTTPS → cliente Android de testes

**Fluxo de desenvolvimento comprovado com medições novas. Nenhuma implantação.**
Branch `feature/telemetry-android-development`, marco funcional `af40096`.

## Sessão e resultado

Autorização explícita diretamente no chat, após `b27e2fb`. Novo recibo exclusivo:
`30bee0addb69b48e9486a9ffcf1cbd43`, referência
`direct-user-2026-10-27-after-b27e2fb-one-loopback-60s`.

- Início: **27/10/2026 10:21:00,906434 −03:00**.
- Lançamento até verificação de encerramento: **31,1869943 s**.
- Recibo até gravação final do resultado, incluindo revogação DEV: **31,195784 s**,
  medido pelos timestamps do recibo e do arquivo final. Ambos dentro de 60 s.
- Observação planejada: 30 s; somente uma execução, sem carga artificial.
- Marcador anterior preservado, 123 bytes, SHA-256
  `098efb46d367616a6e8aa72f263ab23668acd70a20402787373d49334cd29dc8`.

| Etapa | Evidência |
|---|---|
| Coletor real/cache | 475 entradas de cache, incluindo estados indisponíveis; pelo menos 420 leituras distintas e válidas observadas pelo IPC |
| Named Pipe protegido | 30 respostas / 30 consultas, sem rejeição ou timeout |
| Contrato e publicação | 30 snapshots aceitos, zero rejeitados; 30 recibos sanitizados, abaixo do limite 40 |
| HTTPS autenticado | 15 respostas 200 com snapshots, zero `snapshot:null` |
| Modelo Android real | 15 snapshots aceitos, 270 leituras distintas válidas, 29 identificadores de métricas |
| Continuidade | Sequência, origem, valor, unidade e timestamp conferidos contra a mesma leitura IPC; seis respostas com todos os 29 indicadores válidos |
| Cartões Android | Código `telemetry-ui.js` efetivamente executado com respostas desta sessão; formatação e pausa verificadas |

As 270 leituras no cliente são distintas por identificador e timestamp. Não são
270 snapshots ou a contagem total de todas as leituras internas do coletor.
O HTTPS consulta a cada ~2 s e o IPC a cada ~1 s; a diferença é esperada.

O teste de cartões usa o modelo e o renderer reais do Android, com DOM/bridge
substituídos no Node. A reprodução dos cartões após o encerramento é identificada
como reprodução de uma resposta desta sessão, **não uma tela atualmente ao vivo**.
Não houve execução do APK no Samsung ou em emulador; o JSONObject Kotlin está
compilado no candidato, mas sua execução física ainda depende da homologação.
Pinner e HMAC Kotlin reais foram testados em JVM contra HTTPS isolado.

## `snapshot:null`: defeito e alcance da conclusão

A validação antiga exigia `usado + livre == total` para RAM **e discos**.
A igualdade permanece correta para o contrato de RAM, mas os dados de disco
podem possuir espaço reservado/indisponível fora desses dois campos.

Os dados atuais desta sessão comprovam o problema:

| Volume | Total (bytes) | Usado (bytes) | Livre (bytes) | Diferença |
|---|---:|---:|---:|---:|
| C: | 510677479424 | 262184235008 | 248449118208 | 44126208 |
| D: | 480101003264 | 220130455552 | 259957473280 | 13074432 |

A regra antiga rejeitaria todos esses grupos de capacidade. A regra corrigida
`usado + livre <= total` aceitou os valores originais, sem preenchimento artificial
ou alteração das leituras. Nesta sessão, nenhuma outra regra rejeitou snapshots.
Isso confirma o defeito determinístico e o funcionamento da correção com dados
novos. A sessão antiga não registrava a regra de cada rejeição; portanto não se
declara provado que esse foi seu único problema histórico.

Nenhuma validação temporal, pinagem ou limite foi flexibilizado.

## Métricas efetivamente recebidas

Primeira resposta: geração `2026-10-27T13:21:02.588Z`, recebida
`2026-10-27T13:21:02.601075+00:00`; sequência 10, 28 métricas válidas naquele instante.
As fontes foram `win32.systemtimes`, `win32.memory`, `win32.volume.c/d`,
`win32.pdh.logicaldisk` e `amd.adlx`. Valores abaixo são da sessão, não valores atuais.

| Indicador | Mínimo | Média | Máximo |
|---|---:|---:|---:|
| CPU utilização | 5,08% | 10,63% | 21,94% |
| RAM utilizada | 8,32 GiB | 8,40 GiB | 8,57 GiB |
| RAM percentual | 52,80% | 53,28% | 54,34% |
| GPU utilização ADLX | 0% | 0% | 0% |
| Temperatura GPU | 52 °C | 52,47 °C | 53 °C |
| Hotspot GPU | 55 °C | 55,20 °C | 56 °C |
| VRAM utilizada | 826 MB | 826,4 MB | 829 MB |
| Clock fornecido pelo ADLX | 0 MHz | 0,2 MHz | 3 MHz |
| Potência GPU | 34 W | 35,93 W | 41 W |
| Ventoinhas GPU | 482 RPM | 485,6 RPM | 492 RPM |

RAM total 15,76 GiB; VRAM total reportada pelo ADLX 12.272 MB. Leituras de clock e
utilização acima são as fornecidas pela API sem carga induzida; não demonstram
precisão sob jogo ou equivalência a outros monitores. Não houve coleta térmica CPU.

C: total 475,6 GiB, ocupação 51,34%; D: total 447,1 GiB, ocupação 45,85%.
Leitura/gravação C: médias 5.395,45 / 372.069,33 bytes/s. D: ambas zero válido.
Atividade PDH: C: 13/15 respostas válidas; D: 6/15. As outras **11 observações
de atividade** permaneceram `null/unavailable`, sem substituição por zero.
A causa específica dessas indisponibilidades opcionais não foi determinada.
Houve 76 observações de zero válido no cliente, incluindo GPU/I/O; isso é
distinto de contagem de leituras únicas.

Cadência média observada na origem: CPU ~1,0114 s; RAM ~1,0115 s; I/O ~1,0114 s;
GPU ~2,0074 s. Capacidade foi coletada uma vez nesta janela; a cadência de 60 s
não pode ser mensurada numa sessão de 30 s.

Idade máxima observada no cliente: CPU ~0,2572 s; GPU dinâmica ~1,4679 s.
Capacidade chegou a ~29,57 s, dentro de seu TTL de 180 s. Ingresso ADLX observado
~0,0031–0,6451 s, abaixo de 1,5 s. GPU ativa 3 s / inativa 11 s preservadas.
Reconexão, expiração, perda de GPU, ausência de coletor e respostas inválidas foram
testadas com mocks; não se induziram falhas no hardware ou no agente real.

## Recursos e encerramento

| Componente medido | CPU média total da máquina | Máxima amostrada | RSS médio / pico |
|---|---:|---:|---:|
| Intermediário/broker/HTTPS (PID 10900) | 0,0894% | 1,5374% | 30,70 / 32,08 MiB |
| Coletor Python (PID 19164) | 0,0221% | 0,1295% | 31,02 / 31,07 MiB |

GetProcessTimes por diferença de CPU/tempo/processadores lógicos, RSS a cada ~1 s.
O somatório das médias Python é ~0,1116% e ~61,73 MiB; não representa o custo total.
Exclui ponte nativa ADLX, cliente/observador, custo anterior à primeira amostra e
processos externos. RSS pode contar páginas compartilhadas mais de uma vez.

EOF e finalização cooperativa, sem força: intermediário 10900, coletor 19164 e
ponte ADLX 16716 encerrados. Nenhum novo processo residual, pipe LSR ou listener
temporário 55950 restante. Identidade DEV revogada e allowlist DEV esvaziada.

## Segurança e preservação

HTTPS somente em `127.0.0.1:55950`, identidade/certificado temporários próprios,
TLS 1.3 com hostname e pin verificados antes do envio de identidade/HMAC.
Leitura explicitamente autorizada, separada de grants operacionais. Diretório
DEV com ACL restrita à conta; não se copiou o pareamento Samsung. A ACL por conta
não protege completamente contra outro processo malicioso da mesma conta.

Após o teste, agente original supervisor 2096 / worker 14908 preservado; listener
privado único 8776, HTTP 200 autenticado em TLS 1.3, hostname/pin válidos. Banco
íntegro, zero grants, identidades/credenciais/permissões e arquivos protegidos
inalterados. Consultas normais podem produzir registros normais de nonce.

Instalação dev.7: 116 arquivos originais e `debug.log` adicional (117 ao todo)
preservados por hash. Perfil: mesmos 78 arquivos; backup dev.7: 194 hashes
conferidos. PID 11724 preservado. HKCU Run com o mesmo hash; nenhuma alteração de
firewall, serviços ou tarefas realizada. Não houve auditoria integral nova desses
subsistemas. Android/Samsung não foi acessado ou modificado.

## Testes, artefato e próximo passo

Nesta entrega: **21 testes do runner, 18 contrato/broker/HTTPS, 19 verificações de
estados Android e 24 de modelo/UI**, mais a prova com dados reais descrita acima.
As regressões extensas aprovadas na etapa anterior não foram repetidas sem motivo.

APK candidato dev.10/v24 permanece exatamente o arquivo assinado previamente:
`.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.10-v24-disk-space-contract.apk`,
SHA-256 `06f1dfe8693e8489a7d3b82e51c730ca5333b5435f826e94b1be3457109d4078`.
Nenhum código/asset Android mudou nesta entrega, portanto não se recompilou ou
substituiu desnecessariamente o candidato aprovado.

**Concluído em desenvolvimento:** amostras novas → cache/IPC → contrato → HTTPS
autenticado → interpretação e cartões do código Android. **Pendente em produção:**
relay de cache para o processo separado do agente, habilitação revisada da rota e
instalação/homologação no Samsung. O APK sozinho não fornece esses componentes.

Um único [plano coordenado](DEPLOYMENT.md) reúne implantação e reversão. TLS 10054,
inicialização automática e encerramento gracioso permanecem abertos, sem correções
incidentais. Nenhum componente operacional foi instalado, ativado ou atualizado.

Reversão do código: reverter `af40096` apenas na branch de desenvolvimento. Manter
todos os recibos, evidências e checkpoints; não apagar marcadores para repetir.
