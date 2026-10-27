# C1 — diagnóstico das leituras de hardware

Continuação de `fe2e004`, em `feature/hardware-readonly-c1`, checkout isolado
`LSR-hardware-readonly-c1`. **Implementado em desenvolvimento, sem implantação.**
C1 avança na projeção do hardware; diagnóstico operacional completo de HTTPS,
autostart e segurança permanece pendente. Nenhum ganho de desempenho foi medido.

## Entrega

Monitoramento PC recebe uma seção recolhida “Diagnóstico das leituras de hardware”.
Ao abrir ou clicar em “Consultar cache existente”, usa exclusivamente o
`loneDesktop.getMetrics()` existente. O main devolve o cache envelhecido do host
já proprietário do coletor; não inicia outra leitura nativa por causa da consulta.
Não existe novo canal IPC, endpoint HTTPS, grant, serviço ou comando privilegiado.

São sete grupos: CPU/utilização, RAM, GPU/ADLX e capacidade/atividade separadas
dos volumes C: e D:. Estados: leituras disponíveis, suporte parcial, não
verificado, sem leitura, não suportado, desatualizado, erro, acesso não permitido,
aquecimento e coleta desativada. A interface descreve disponibilidade de leituras;
não certifica saúde física, segurança, SSD/SMART ou estabilidade do sistema.
Temperatura da CPU e SMART continuam explicitamente sem integração.

O resultado é **pontual**, com horário da consulta e timestamp/sequence original
do snapshot. Cada evidência mostra fonte, coleta, idade na consulta e limite.
Não há atualização periódica adicional nem reaproveitamento da hora da consulta
como hora da coleta. Fechar, esconder ou consultar novamente limpa a apresentação
anterior; respostas atrasadas não restauram um recibo descartado. Ao voltar à
visibilidade, um painel aberto consulta novamente o cache. Uma resposta que não
chegue pode ser descartada fechando a seção; não há retry ou timer adicional.

Simulação aparece em destaque e jamais se transforma em origem real. Ausência de
cache, desconexão e sessão encerrada não apresentam leituras como atuais. Um grupo
incompleto fica não verificado. Zero válido permanece válido. Suporte parcial não
vira disponibilidade total; erro de leitura não afirma defeito físico.

## Fronteiras e preservação

`hardware-diagnostics.js` é uma projeção pura: revalida o contrato métrico existente,
proveniência, unidades, cadência, números, timestamps, limites ADLX e idade antes
de projetar. Aceita até 64 KiB UTF-8; qualquer inconsistência rejeita a projeção
inteira. Trata apenas o campo derivado `information_age_seconds=null` do host sem
ingresso como campo opcional ausente no normalizador wire. Nenhum valor de métrica
é reparado ou fabricado. GPU em retomada/timeout não conta amostras retidas como
utilizáveis. TTLs existentes de 3/11 s GPU e os demais contratos não mudaram.

`hardware-diagnostics-renderer.js` cria sete grupos fixos com `textContent`, sem
HTML de provedor, filesystem, rede, Registry, imports dinâmicos ou shell. Há apenas
duas novas URLs locais exatas na allowlist e no manifesto de arquivos empacotados.
CSP, sandbox, isolamento e validação de sender/frame permanecem intactos. A seção
é independente da Central simulada, que continua com seus gates originais.

Fontes de Android, agente, NEX existente, WoL, HTTPS, HMAC, antirreplay, DPAPI,
pinagem, grants, launchers, coletores, ponte nativa, host/modelo/renderer de
monitoramento, main e preload **não foram alterados**. Versão, dependências,
lockfile, assinatura, aplicação instalada e perfis de produção não foram modificados.
Os testes não enviam pacotes WoL, nem executam Steam/CS2, otimização, limpeza,
debloat, mudanças de Registro/serviços, driver ou exclusões do Defender.

## Origem da divergência do preload

O pin em `scripts/preservation_rules.py` foi atualizado por último em
`2d172871eb1e7012112871ad4cf9ed73435d4bc0`, para
`5fc9553bd9f9cddb98f099a8fc1c0d7ea53ae197c12e87eb5f628755a6481eba`.
O commit `a7310a4d72e101b11d914ce280534f96e212f4a3` acrescentou exatamente cinco
linhas: `getDiagnostics(scenario)`, validação da enumeração e envio de
`{v:1,scenario}` a `diagnostics:snapshot`. A regra de preservação ficou com o pin
anterior. O preload da base `fe2e004` já contém esse delta, com SHA-256
`c20b427fea83d32c456cabacdc894fa5286df2647dbf5c693ea005b2011d3046`.

A revisão conferiu o diff histórico, a enumeração fechada, a cardinalidade e
sender/frame no main, e a habilitação da demonstração apenas no modo de revisão
não empacotado. Nenhuma API genérica ou operacional foi adicionada por esse delta.
O teste novo `test_preload_review.py` remove **somente esse trecho exato**, exige
o hash antigo e confirma o novo pin exato. As regressões Node revalidam as
fronteiras. Após essa prova, o pin foi corrigido manualmente no checkout isolado;
não há atualização automática, aceite de hash arbitrário ou mudança no preload.
O gate de preservação Python passa novamente neste checkout.

## Trabalho concorrente e isolamento

Os três documentos C0 foram lidos antes de qualquer edição. No checkout original
já havia mudanças em `diagnostics-host.cjs`, `diagnostics-model.js`,
`preservation_rules.py`, `tests/diagnostic-center.cjs` e arquivos novos de
adaptadores/fixtures. A correção concorrente do pin também já estava lá. Esses
arquivos não foram copiados como implementação nem sobrescritos.

A ferramenta de worktree da aplicação retornou “Not a git repository”, porque
o diretório da conversa é o pai do repositório. Foi usado `git worktree add` no
repositório real, partindo exatamente de `fe2e004`, com branch própria. A branch
e os arquivos concorrentes do checkout original continuam separados. A criação
só acrescentou os metadados Git de worktree/branch; não fez stash, reset ou merge.

Para os testes foram copiados apenas insumos locais já existentes para caminhos
ignorados do checkout isolado: cinco originais de preservação, pyvenv.cfg, build
ADLX, runtime dev.7, classes Kotlin e stdlib Kotlin. Não foram copiados credenciais,
perfil instalado, banco operacional, certificados privados ou configuração do agente.

Ao reconciliar as branches, comparar a correção concorrente de
`preservation_rules.py` e manter um único pin revisado. Não substituir o arquivo
inteiro pelo desta branch; as mudanças de diagnóstico concorrentes não foram
homologadas pelos resultados deste checkout. Nenhum merge foi executado.

## Testes e limitações

| Gate final | Resultado |
|---|---|
| Python offline com audit hook | 376 testes, zero falhas/erros/skips |
| Node estático/substituído | 13 suítes aprovadas; 749 verificações contabilizadas e uma suíte sem contagem declarada |
| HTTPS temporário em 127.0.0.1 | 16 testes aprovados, incluindo Java/Android pinner/status |
| Comandos temporários em 127.0.0.1 | 20 testes aprovados, incluindo Java/Android HMAC POST e executores falsos |
| Novos arquivos JS e diff | Sintaxe e whitespace aprovados |

Os 59 testes novos Node cobrem cache recebido do host existente, expiração exata,
grupo incompleto, suporte parcial, recuperação/retomada, rejeição de dados
malformados, limite UTF-8, zero válido, origem simulada e renderer com DOM
substituído, consulta explícita, visibilidade, falha, cancelamento e resposta tardia.
O teste Python novo prova o delta do preload. O total Python final é 412 testes
entre offline e loopback, todos aprovados; os ambientes de execução são distintos.

A primeira rodada offline teve cinco erros porque o novo worktree ainda não
continha `.cache/adlx-build`, exigido pelos mocks de integridade. Os logs/recibo
iniciais foram preservados antes de copiar o insumo e repetir o gate. O teste de
integração do host também precisou do pyvenv.cfg local; nenhum executor nativo
foi acionado. Isso não exigiu modificar as suítes ou coletores existentes.

A primeira tentativa loopback no sandbox falhou com WinError 10013 e
`Permission denied: getsockopt` no Java. As duas suítes foram repetidas com a
permissão de execução revisada, em bancos/certificados temporários sob
`.cache/tests`, com portas efêmeras e executores substituídos. Passaram integralmente.
Não se relaxou TLS/pinagem, não se mudou firewall e não se consultou 8776.

Recibos: [Python offline](python-tests.json), [Node](node-tests.json),
[HTTPS loopback](https-loopback.txt), [comandos loopback](app-commands-loopback.txt),
[resumo e preservação](validation.json). Logs completos ficam em
`.cache/hardware-readonly-c1/`, incluindo tentativas iniciais. Não houve download,
build/instalação de APK/NSIS nem uso de dispositivo Android real.

**Limites:** não houve sessão com sensores reais, benchmark, revisão visual nativa
da seção ou validação física do aplicativo instalado. Snapshots de teste são
sintéticos, inclusive os com metadados `real`, usados para testar proveniência.
Os testes em loopback exercitam código real de TLS/DPAPI/Android, não o agente
operacional nem o Samsung. Não comprovam desempenho em CS2 ou ausência absoluta
de impacto no hardware. O caminho funcional lê dados reais quando o coletor
existente já está ativo no aplicativo; não foi ativado para esta tarefa.

Continuam abertas: TLS 10054 operacional, autostart inconclusivo, encerramento
gracioso do agente, homologação física parcial dev.7 e integração real completa
da Central. Nenhuma delas foi encerrada pelo sucesso dos testes locais.

## Reproduzir e reverter

No checkout isolado, com Python/Node e os insumos locais descritos:

```powershell
python -B scripts/test-hardware-c1-offline.py
node tests/hardware-diagnostics.cjs
python -B -m unittest discover -s tests -p test_secure_agent.py -v
python -B -m unittest discover -s tests -p test_app_commands.py -v
```

As duas últimas suítes precisam de conexão loopback permitida, cryptography/DPAPI,
JDK e classes Kotlin locais existentes. Não são testes com o agente instalado.
Nenhum teste foi marcado skip para contornar dependência ou falha.

Reversão: reverter apenas o commit desta branch após revisar o diff; se outras
mudanças dependerem dos recursos novos, removê-las primeiro. Não reverter banco,
nonces, pareamento, configuração, instalação ou arquivos concorrentes. Não usar
o hash antigo para invalidar o preload já revisado de outra branch sem conferir
seu histórico. Este checkout foi mantido para revisão; não foi integrado ao original.
