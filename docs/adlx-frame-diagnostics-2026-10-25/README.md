# Diagnóstico sanitizado de frames ADLX — 25/10/2026

Base preservada: `a5cdc75`, `05e471c`, `ac56a30` e checkpoints anteriores.
**Nenhuma nova execução da DLL ADLX, coleta GPU, sessão Electron ou instalação.**
Somente revisão de código/evidências, compilação de desenvolvimento e testes simulados.

## Conclusão sobre a rejeição original

Foi identificada a **etapa**, mas não é possível recuperar a regra primitiva exata
da tentativa física anterior. Em a5cdc75, dez condições diferentes geravam o mesmo
`invalid_frame`, antes de validar os valores dos sensores e calcular a idade de fila.
O frame rejeitado não foi preservado; clock_sources vazio apenas localiza essa etapa.

O replay isolado do fonte arquivado, conferido por SHA-256 contra o recibo físico,
comprovou que dois inputs diferentes — idade null e relógio não contratado — produzem
os mesmos code, events e clock_sources observados anteriormente. Esses exemplos são
**simulados**: não são uma reconstrução do frame real. Evidência:
`evidence/archived-guard-analysis.json`.

| Evidência | O que permite concluir |
|---|---|
| Fases runtime_verified/adlx_loaded/adlx_initialized, preservadas | A sessão anterior carregou e inicializou a biblioteca |
| invalid_frame antes de clock_sources.add | Falha na guarda de estrutura/tempo; não no valor de um sensor ou na soma da fila |
| Dez condições com um único código antigo | O recibo antigo não distingue campo, tipo, idade ou relógio |
| Mock C++ clock_unmatched → age null → age_null | Caminho determinístico reproduzível no produtor; não confirma o episódio real |
| Sem frame bruto antigo | Ainda não há evidência para escolher entre amostra inicial, epoch desconhecido ou outra condição |

Portanto, **timestamp continua hipótese, não causa comprovada**. Não foi aplicada
correção de epoch, espera inicial presumida ou conversão automática para obter dados válidos.

## Formato, tipos e unidades auditados

| Campo v1 | Contrato | Rejeições agora distinguíveis |
|---|---|---|
| v | int 1, exclui bool | versão ausente/incompatível |
| event | frame | evento inválido |
| timestamp_ms | int entre 0 e 2^63−1 | null, string/float/bool, negativo ou fora de faixa |
| age_seconds | número finito não negativo | null, tipo incorreto, NaN/inf, negativo |
| clock_source | domínio explicitamente contratado | tipo incorreto ou domínio desconhecido |
| readings | objeto com os sete IDs dinâmicos exatos | ausência, campos extras, tipo/conjunto incorreto |
| cada Reading | state e value | disponibilidade inválida, null/zero indevidos, tipo ou não finito |
| diagnostic | apenas no perfil opt-in negociado | formato, unidades, contagem, domínio e conversão inconsistentes |

O header oficial fixado descreve TimeStamp como duração **em ms desde o epoch do
sistema**. Não especifica, por esse texto, equivalência garantida a Unix, FILETIME
ou uptime neste driver. Nenhuma chamada real foi feita para descobrir isso nesta fase.

O código compara três candidatos: uptime/GetTickCount64, Unix UTC ms e Windows epoch
ms. A subtração de FILETIME para Unix usa ms; a idade é delta_ms/1000. Não há aplicação
de fuso local ou ajuste de três horas nessa cadeia. Horário local aparece apenas em
relatórios. Testes com datetimes UTC e UTC−3 equivalentes confirmam o mesmo epoch numérico.
Texto ISO de horário não é aceito no campo inteiro timestamp_ms.

A janela de 5.000 ms escolhe um domínio candidato; **não** autoriza amostras de cinco
segundos. O AdlxProvider mantém o limite de frescor de 1,5 s, timestamp progressivo e
rejeição de amostras repetidas. A fila positiva continua somada à idade SDK. Cache
continua derivando stale e preservando o último horário válido, sem renovar dados antigos.

Zero de timestamp só pode ser válido num domínio/idade demonstrados, por exemplo
uptime zero em fixture contratada. Zero de sensor com sucesso/suporte é válido;
sensor ausente tem null. Um frame inicial sem domínio demonstrado continua rejeitado,
não convertido em leitura válida ou declarado aquecido por conveniência.

## Instrumentação preparada

- `monitoring/adlx_diagnostics.py`: buffer de diagnósticos sanitizados.
- `monitoring/adlx_bridge.py`: códigos específicos por etapa/campo; mantém code legado.
- `monitoring/adlx_provider.py`: informa limite de idade, repetição e erro de leitura,
  sem mudar os estados, cache ou resultado das métricas.
- `native/adlx/bridge.cpp`: opção local fixa `--diagnostics`, perfil negociado e
  metadados da comparação de relógios. Nenhuma nova API GPU de consulta ou controle.

Exemplo **sintético** de rejeição: stage=time, rule=age_null, field=age_seconds,
timestamp tipo int/ms, idade tipo null/segundos, native_rule_reported=clock_unmatched,
deltas candidatos e resultados de conversão diagnóstica. Os estados/unidades/tipos
dos sensores aparecem sem seus valores. `frame_structure_accepted` indica somente
que a estrutura passou; não é confirmação final de leitura válida pelo provedor.

O buffer fica **desativado por padrão**, em memória e sem escrita automática em disco.
Limites: 16 registros, 32 KiB serializados no total, 4 KiB por registro. A primeira
rejeição é preservada e os registros recentes substituem os demais quando necessário;
o contador informa descarte. Isso não representa um limite de RSS total do processo.
Exportação futura deve ser explícita e local, em perfil de desenvolvimento autorizado.

Logs não contêm payloads brutos, memória, valores de sensores, exceções livres,
nomes/chaves desconhecidos, caminhos pessoais, certificados, credenciais ou tokens.
Domínios e unidades inesperados viram unknown, sem copiar o conteúdo recebido.
Os exemplos em `evidence/sanitized-fixture-example.json` são marcados como simulados.

Sem a opção, hello/frame mantêm o conjunto de campos anterior. Com a opção, o cliente
exige o perfil e valida estritamente o objeto adicional. Não foram ampliadas APIs
preload, allowlists desktop, unidades do catálogo básico ou contrato de métricas v1.

## Correção isolada comprovada

Foi encontrado um defeito **independente da falha original**: o cálculo antigo usava
`max(0, agora_monotonico - recebido_em)`. Em fixture com agora=10 s e recebido=20 s,
a diferença −10 s era apagada e o adapter devolvia idade 0,1 s como se a fila fosse zero.
Recibo anterior à correção: `evidence/future-receipt-before-fix.json`.

Agora relógios futuros ou não finitos do transporte geram `transport_time_future`
ou `transport_time_nonfinite`, sem publicação do frame. A regressão confirma rejeição,
idade positiva de fila continua somada e nova resposta válida pode recuperar sem reinício.
Recibo: `evidence/future-receipt-after-fix.json`.

Essa correção não pode explicar a rejeição física anterior: o ponto corrigido fica
depois de clock_sources.add, enquanto o registro antigo permaneceu vazio. Não foi
alterada a janela do SDK, o frescor, o relógio escolhido ou a escala de timestamps.

## Testes executados

| Suíte | Resultado |
|---|---:|
| Ponte/regressões originais | 25 testes |
| Novos diagnósticos/tempo/privacidade/retenção | 34 testes |
| Núcleo ADLX | 28 testes |
| Sessão e recursos simulados | 10 testes |
| Monitoramento básico, contratos, cache, WoL e launchers | 133 testes |
| IPC/lifecycle | 28 testes |
| Electron/políticas/renderer/distribuição | 296 verificações Node |
| Manutenção/reconexão/stale | 23 verificações Node |
| Política nativa dentro da suíte mock | 31 asserts C++ |

Total: **258 testes Python e 319 verificações Node aprovados**, sem falhas ou skips.
Os 31 asserts estão dentro da suíte da ponte. Somente o binário mock separado pôde
ser iniciado pelo runner (22 processos no teste final, zero residuais); audit hooks
recusam sockets, Registro, cargas ctypes e executáveis reais. O binário mock não
contém o nome da DLL ADLX nem compila o backend de carga real.

Cenários incluem UTC, uptime contratado, futuro/antigo, segundos/ms, timestamp
ausente/null/zero, primeiro frame, disponibilidade parcial/total, zero legítimo,
NaN/inf/overflow, campos/versão incompatíveis, sequências válidas/inválidas,
recuperação, log desligado, descarte limitado e preservação da primeira rejeição.
Conversões explícitas em helper são diagnósticas; nunca reescrevem um timestamp operacional.

Compilação x64 real e mock passou com as ferramentas já existentes, sem executar o
worker real ou o verificador de runtime. Os 12 arquivos do build anterior foram
copiados e conferidos antes de atualizar apenas os artefatos de desenvolvimento.
Nenhum pacote Windows/Android foi reconstruído ou instalado, nem SDK/dependência baixado.

## Preservação e condição separada do agente

Instalação Windows (109 arquivos), perfil (77), backups dev.3 (341), dev.4 (75), dev.5
(156), 86 arquivos operacionais protegidos e evidências físicas anteriores sem diferenças
de SHA-256. Banco íntegro, identidades/segredos cifrados/schema/revogações preservados;
zero grants e comandos pendentes. Os inventários privados permanecem em cache ignorado.
Marcador da tentativa física anterior mantido; nenhum marcador novo ou sessão GPU criada.

**Disponibilidade final: agente offline.** A checagem por identidade não encontrou
processo do agente e a porta 8776 não tinha listener. O Windows informou último boot
às **22:03:59 de 25/10**, e a inspeção foi às **23:03:59**, America/Sao_Paulo. A presença
isolada do PID histórico 8680 não foi aceita como identidade de agente.

Não se iniciou ou reiniciou o agente, nem se fez GET autenticado contra endpoint
ausente. Não foi investigada a causa do bootstrap nesta etapa. Não há evidência que
atribua essa indisponibilidade aos mocks. HKCU Run e regras de firewall permanecem
idênticos por hash. A recuperação depende de autorização separada; ela não está
implícita numa futura autorização de teste GPU.

Nenhum processo de monitoramento/Electron residual. Não foram executados Steam,
CS2, WoL, energia ou novas coletas. Android, Electron instalado, certificados,
credenciais e permissões não foram alterados. TLS, Crashpad e encerramento gracioso
permanecem tarefas separadas.

## Plano proposto de sessão física — não executado/não autorizado

1. Resolver separadamente a indisponibilidade do agente, com autorização própria;
   confirmar identidade, HTTPS autenticado, listener único 8776 e zero grants.
2. Preparar diretório e ID novos de evidência, sem apagar ou reutilizar o marcador
   anterior. Congelar fonte/build/recibos correspondentes e repetir somente gates necessários.
3. Selecionar explicitamente o perfil de diagnóstico no runner isolado, sem Electron,
   Named Pipe operacional ou interface de rede nova. Logs sanitizados locais e limitados.
4. Uma inicialização ADLX, até 90 s totais, cadência aproximadamente 2 s; somente
   getters autorizados, sem jogos/carga, tuning, parâmetros livres ou alteração do driver.
5. Registrar a primeira rejeição com regra, tipos, unidades, timestamp e comparação
   nativa. Se houver erro, encerrar normalmente e apresentar evidências; não repetir,
   calibrar epoch automaticamente ou aceitar a leitura rejeitada.
6. Se as leituras forem válidas, medir estabilidade/cadência/CPU/RSS na mesma sessão.
   Até lá, não presumir desempenho sustentado ou validar uma correção de epoch inexistente.
7. Parada local normal do próprio worker/coletor, confirmação de liberação, ausência
   de residuais, agente íntegro e zero grants. Timeout não autoriza force/kill.

O objetivo inicial dessa nova sessão será **identificar a regra no hardware**. A
correção de relógio de transporte passou em mocks; a causa temporal do SDK ainda
não foi demonstrada. Integração ao dashboard/widget continua pendente de dados reais válidos.

## Commits e reversão

- a557428: instrumentação opt-in, regras por etapa, perfil e mocks temporais.
- e787f16: correção isolada de relógio futuro/não finito do transporte.
- be18749: retenção da primeira rejeição e testes de contrato/limites.

Reversão proposta, não executada: árvore limpa, revisar os diffs e usar
`git revert be18749 e787f16 a557428`, preservando relatórios/evidências. Executar
regressões correspondentes. Não restaurar banco/perfis, reinstalar aplicativos ou
iniciar o agente. Artefatos de cache não possuem autostart; os originais foram preservados.
Todos os checkpoints anteriores permanecem ancestrais da branch.
