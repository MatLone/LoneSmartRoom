# Telemetria loopback — instrumentação pronta; sessão não iniciada

Data: 27/10/2026. Base `dd3964a`, branch `feature/telemetry-android-development`.
Implementação isolada: `d19890f`. **Não houve uma nova sessão física.**

## Bloqueio de aprovação do ambiente

O pedido anexado autorizava uma nova sessão de até 60 segundos. Sua leitura foi
realizada, mas a revisão automática rejeitou duas propostas de alteração do
runner para criar um recibo independente sem apagar o anterior. A segunda
proposta também verificava o hash do pedido anexado.

A revisão informou que não aceita o anexo como autorização confiável para mudar
a trava e exige confirmação escrita diretamente no chat. Não foi utilizado
outro script, alteração manual de marcador, execução indireta ou qualquer
alternativa para contornar a rejeição. A regra original permanece intacta,
inclusive coberta por teste específico.

O marcador da sessão anterior continua com `started_at`
`2026-10-27T12:30:35.036865+00:00`, 123 bytes, SHA-256
`098efb46d367616a6e8aa72f263ab23668acd70a20402787373d49334cd29dc8`.
Não representa uma nova execução. A nova autorização não foi consumida.

Próxima confirmação necessária, diretamente no chat: autorizar um novo recibo
independente para UMA sessão real instrumentada de até 60 segundos, preservando
o marcador antigo, o PID 11724 e todas as restrições operacionais. Após isso,
renovar os gates antes de iniciar. Não há autorização para repetição automática.

## Instrumentação implementada e testada

- Recibo por tentativa de publicação no broker, com sequência, aceitação,
  rejeição e código sanitizado da regra efetivamente reportada pelo broker.
- Até 40 recibos; nenhum payload bruto, segredo ou texto livre de exceção nesses
  registros. Instrumentação do intermediário desativada por padrão.
- O runner explícito solicita `--validation-trace`, mas continua impedido de
  executar uma nova sessão pelo marcador consumido.
- Até 40 snapshots de IPC projetados pela allowlist do contrato, preservando
  fonte, valor, unidade, timestamp, idade e validade para futura comparação com
  HTTPS. Uma projeção inválida conserva somente tipo e sequência, sem campos
  livres do payload rejeitado.
- Recepção, validação, publicação e HTTPS terão evidências separadas. HTTP 200
  ou encerramento limpo continuam insuficientes para homologação.
- Sem alteração da regra de discos, limites temporais, autenticação, cache
  operacional, Android, coletor instalado ou agente original.

Essa instrumentação foi testada com substitutos. Ainda não foi validada ao vivo.

## Testes executados nesta etapa

| Suíte | Resultado |
|---|---:|
| Validador e instrumentação, mocks | 18 testes aprovados |
| Contrato/broker/HTTPS isolado, incluindo pinner e HMAC Kotlin | 18 testes aprovados |
| Regressões Python com operações externas negadas | 378 testes aprovados |
| Estados Android, timers virtuais | 19 verificações aprovadas |
| Modelo/UI Android de telemetria | 24 verificações aprovadas |
| Replay HTTPS histórico, explicitamente identificado | 10 verificações aprovadas |

O teste novo da trava inicialmente encontrou uma restrição de escrita no diretório
temporário do sandbox. Foi convertido para mock de filesystem; a suíte final
passou sem criar arquivos temporários ou executar hardware. A primeira tentativa
de gerar o recibo passivo também encontrou um nome relativo de hash tratado como
absoluto; corrigiu-se apenas a resolução no verificador e a inspeção foi concluída.
Nenhum desses erros representa falha de sensor ou do agente operacional.

## Verificação operacional passiva

Última evidência: **27/10/2026 10:11:53 −03:00**.

- Supervisor efetivo 2096 e worker efetivo 14908; redirecionadores da venv 16828 e
  8592. Mesmas identidades nativas, argumentos e cadeia anterior.
- Listener privado único em 8776, PID 14908. Status autenticado HTTP 200,
  TLS 1.3, hostname e pinagem verificados.
- Banco íntegro em consulta somente leitura; zero grants. Mesmas identidades,
  credenciais e permissões; arquivos protegidos mantiveram hashes.
- Perfil de produção: mesmos 78 arquivos e hashes.
- Backup `Windows-before-dev7-20261026T152048Z`: 194 arquivos verificados por hash.
- Os 116 arquivos do inventário da instalação Windows estão presentes e
  inalterados. Há **um arquivo adicional `debug.log`**, 664 bytes. Não se atribui
  sua criação a esta tarefa ou a um componente sem evidência. Ele não foi
  apagado nem alterado. O inventário completo atual tem 117 arquivos.
- Nenhum processo de monitoramento identificado pelo leitor. A enumeração do
  namespace de pipes retornou **não verificável**, portanto não se afirma que
  esteja vazio com base nesta nova leitura.
- PID 11724 ainda ativo: Electron de desenvolvimento com
  `scripts/capture-night-development.cjs`, pai 11628. Sem sinais ou alterações.
- Hash da entrada HKCU Run preservado. Sem alterações de firewall, serviços,
  tarefas, instalações, credenciais ou configurações realizadas por esta tarefa;
  não houve nova auditoria integral desses subsistemas.
- Nenhum Samsung conectado/consultado nesta etapa. APK candidato dev.10/v24
  preservado: SHA-256
  `06f1dfe8693e8489a7d3b82e51c730ca5333b5435f826e94b1be3457109d4078`.

As consultas normais autenticadas podem produzir seus registros normais de nonce;
não houve escrita direta no banco operacional. Nenhum teste TLS malformado.

## Resultado e limites

Duração da nova sessão física: **não iniciada**. Amostras novas de hardware:
**zero**. Não há novo consumo de CPU/RAM dos componentes reais a relatar.

A causa da exportação vazia anterior continua parcialmente estabelecida: o
contrato rejeitava dados históricos reais pela igualdade inadequada de capacidade
de discos, corrigida em `8a0ded7`. Não se provou que essa foi a única causa da
sessão anterior. O replay histórico passa; não é comprovação atual do transporte.

Nenhum endpoint operacional, relay, permissão de leitura operacional ou APK foi
implantado. A implantação no Samsung depende primeiro da nova validação viva e
de autorização separada para a atualização coordenada do relay/cache, agente e
Android. Ver o [plano anterior](../telemetry-homologation-preparation-2026-10-27/DEPLOYMENT.md).

TLS 10054, inicialização automática, encerramento gracioso e demais pendências
continuam abertos. Nenhuma correção incidental foi aplicada.

## Reversão

Reverter somente `d19890f` na branch de desenvolvimento, se necessário. Não
alterar marcadores consumidos, instalações, perfis, certificados ou backups.
O checkpoint documental acrescenta apenas este relatório e evidências sanitizadas.
