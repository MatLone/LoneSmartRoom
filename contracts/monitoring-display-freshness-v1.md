# Frescor de exibição v1 — Windows dev.6

Esta política não muda a admissão de frames ADLX nem o contrato v1 existente.

| Camada | Relógio / significado | Regra |
|---|---|---|
| Ingresso nativo | Timestamp SDK reconhecido + idade na fila privada, relógios explicitamente contratados | Idade finita entre 0 e **1,5 s**; rejeitar futuro, `age_null`, não finito e timestamp não avançado |
| Cache v1 | Monotônico desde o início da tentativa Python; `collected_at` é UTC dessa tentativa, não o epoch SDK | Retém o TTL existente de 3 × cadência e o histórico limitado; não renova idade num snapshot |
| Exibição GPU dinâmica | Idade do cache acrescida do tempo transcorrido no main e renderer | Prazo estrito **cadência + 1 s**: 3 s ativa / 11 s inativa; no limite, `stale`, `valid=false`, valor `null` |
| Informação GPU | `ingress_age_seconds` + idade do cache/exibição | Estimativa conservadora da idade do conteúdo; até <4,5 s ativa / <12,5 s inativa, não uma nova medição |
| Capacidade VRAM / discos | Consulta de inventário a cada 60 s | Mantém TTL v1 de 180 s; não aplicar cadência dinâmica a capacidade |
| CPU / RAM / I/O / PDH | APIs Windows, cadências 1 s ativa / 5 s inativa | Mantêm validação e TTL v1; PDH opcional, null não se torna zero |

O segundo adicional da exibição corresponde ao polling/aging de 1 s da interface
ativa, e não é uma ampliação da idade aceita pelo SDK. Uma resposta lenta pode
expirar na chegada, de forma segura. O cache pode conservar um frame admitido
enquanto o renderer já o apresenta desatualizado. O limite antigo de 3 × cadência
não era suficiente para explicar ao usuário os 2,69 s observados: agora há
campos e metadados distintos. Um conteúdo com cache de 2,69 s não é anunciado
como tendo idade SDK ≤1,5 s nesse instante.

Campos opcionais adicionais em observações GPU disponíveis:
`ingress_age_seconds` (idade SDK + fila na validação, ≤1,5 s) e
`information_age_seconds` (idade acima + cache). Não são colocados em leitura
inválida ou capacidade estática. A idade do cache começa antes do read; por isso
esta soma pode contar conservadoramente parte da duração do read, sem subestimar
o envelhecimento. Os clientes v1 anteriores continuam recebendo seus campos
originais. O renderer valida a coerência da soma e não converte timestamps SDK
em UTC por aproximação. A validação 1,5 s continua no provedor; não é delegada à UI.

Ao restaurar/focar, o main muda seu único timer de 10 s para 1 s e pede um snapshot
imediatamente. As leituras autorizadas existentes reativam a cadência do coletor
(sem nova operação no protocolo). Até receber uma amostra em cadência ativa
cuja tentativa começou após a restauração, a GPU aparece como **Atualizando**,
sem reutilizar os números antigos. Não marcar uma leitura antiga como atual para
evitar a transição visual. Falha de IPC continua sendo **Desconectado**, separada
de aquecimento/erro de sensor. `age_null` inicial permanece erro/null; o próximo
frame pode recuperar no mesmo processo, sem reinicialização nativa automática.

Os metadados mostram origem, unidade, horário, estado, idade do cache, cadência,
idade no ingresso e idade da informação. Não há SLA de tempo real: Windows,
driver e IPC podem atrasar; nesse caso os dados expiram. Estas regras têm testes
de fronteira e relógios simulados; a dev.6 empacotada ainda exige teste físico.
