# Contratos e fontes previstas

## Fluxo preparado

```text
MockEvidenceSource (finito)
  → EvidenceFrame v1 (simulated)
  → adaptador específico
  → EvidenceHub / DiagnosticEngine / cache limitado
  → relatório diagnóstico v1 + auditoria de segurança separada
  → provider simulado injetável no Electron main
  → validação estrita do envelope
  → preload existente e restrito
  → modelo dos cartões da Central
```

O hub é dirigido pelo chamador. Não instala timers, threads de coleta, leitores,
endpoints ou mecanismos de reparação. A fonte padrão do main permanece o catálogo
local aprovado de simulações. A ligação hub/main foi validada por substitutos e
fixtures; não há supervisor Python novo rodando no aplicativo instalado.

## Interfaces

| Adaptador | Evidência aceita na simulação | Fonte futura prevista, condicionada a revisão e autorização |
|---|---|---|
| Agente HTTPS | Identidade e criação de supervisor/worker; relação entre processos, usuário/sessão e elevação; listener, proprietário e rede; recibo de status/autenticação/TLS/hostname/pin e horário original | Leitores locais já aprovados e recibo da consulta fixa de status existente; nenhum cliente desktop operacional novo |
| Monitoramento PC | Ciclo de vida, geração da conexão, snapshot métrico versionado e disponibilidade, ponte ADLX | Estado do host de monitoramento e cache já autorizado; não iniciar sensores para produzir saúde |
| Comunicação IPC | Conexão, geração, contrato e verificações de SID/sessão/identidade/ACL/localidade | Recibos do transporte protegido existente, sem abrir acesso genérico a pipe |
| Inicialização | Evidências correlacionáveis de login, despacho e bootstrap | Logs/registros existentes somente leitura; leitura de configuração Run não prova despacho |
| Segurança | Verificações enumeradas, autorização, resultado e timestamp; pendências conhecidas | Resultados sanitizados de verificadores específicos autorizados; nenhuma chave, token, certificado privado ou texto livre |

As interfaces não aceitam um comando, URL, caminho executável ou factory de
leitor. A aplicação não pode solicitar execução arbitrária através delas.

## Contratos e limites

`EvidenceFrame` exige versão 1, adaptador enumerado, sequência inteira positiva,
UTC válido, relógio monotônico finito, bytes limitados e identificação explícita
de simulação. Outro tipo de evidência é rejeitado com
`operational_evidence_not_authorized`. O payload é validado por esquema específico,
com rejeição de campos inesperados e tipos incorretos.

| Limite | Política |
|---|---|
| Payload de ingresso | 32 KiB por frame |
| Frequência por fonte | Intervalo mínimo de 500 ms |
| Sequência / tempo | Rejeitar repetição, regressão e evidência futura |
| Cache | Oito registros diagnósticos e uma auditoria de segurança; cinco marcas de sequência; sem histórico de payloads |
| Fonte mock | Até 64 frames |
| Relatório diagnóstico serializado | 16 KiB |
| Auditoria serializada | 8 KiB |
| Envelope main com sidecar | 18 KiB; limite agregado adicional |
| Solicitação da Central | Intervalo mínimo de 500 ms; uma solicitação em voo; timeout de 1 s |

Esses são limites lógicos de contrato/serialização. Não equivalem a uma medição
de heap/RSS nem protegem, sozinhos, a alocação anterior à desserialização de um
transporte futuro. Um leitor real deverá limitar os bytes antes do parse.

O relatório v1 não recebeu componentes novos nem campos privados. O envelope
aceita uma auditoria opcional separada, também v1 e explicitamente simulada. O
renderer recebe somente relatório e auditoria normalizados, não recibos brutos,
PIDs, caminhos pessoais, credenciais ou objetos de exceção.

## Classificação e tempos

- **Saudável:** evidência afirmativa suficiente e ainda fresca. Processo em
  execução sozinho não satisfaz a saúde do agente.
- **Inativo normalmente:** ciclo de vida indica aplicação fechada e componentes
  de monitoramento não esperados; não é alerta de falha.
- **Indisponível:** ausência ou falta de suporte identificada, sem valor fictício.
- **Desatualizado:** evidência envelheceu; consulta ao cache não renova seu tempo.
- **Falha:** resultado negativo comprovado, por exemplo identidade divergente ou
  autenticação rejeitada. Não representa diagnóstico de causa raiz do Windows.
- **Não verificado:** evidência ausente, parcial, inválida ou inconclusiva.

Datas de verificação e última comunicação válida conservam os tempos originais.
Uma falha posterior não apaga a última comunicação conhecida nem a transforma
em comunicação atual. Evidência de HTTPS não modifica a conclusão de startup.

Desconexão ou mudança de geração invalida saúde antiga do monitoramento. Para
recuperar, exige-se peer validado e fresco (menos de 5 s), geração correspondente
e amostra nova posterior à reconexão. Uma consulta sem amostra nova não recupera
cartões. Cadências e frescor são conceitos diferentes.

As políticas existentes de ingresso ADLX de 1,5 s e frescor GPU de 3 s ativa /
11 s inativa permanecem. CPU/RAM respeitam a cadência inativa existente. Nulos,
zero válido e dados antigos continuam distintos. O cache não altera o executor
operacional de retomada GPU ou o limite de falha persistente de 10 s.

Na auditoria de segurança, verificações sem autorização ou evidência não se
tornam saudáveis. Resultado negativo fresco prevalece sobre outras verificações
antigas. A lista de cinco pendências continua aberta, mesmo quando mocks
produzem verificações positivas. A composição visual não esconde falha conhecida
de agente/listener em razão de uma auditoria parcial.

## Segurança e impacto projetado

O código novo não abre rede, Registro, processos, pipe ou DLL. Não importa os
leitores operacionais para executá-los. Não há reparo automático nem API preload
genérica. `contextIsolation` e `nodeIntegration` não foram modificados.

Os mocks comprovam regras do contrato, não a veracidade de um remetente real.
ACL por usuário não isola totalmente processos sob a mesma conta. Provas de SID,
identidade, TLS e HMAC precisam continuar sendo produzidas por mecanismos
específicos confiáveis. Não copiar a identidade do Samsung para um futuro cliente
desktop. Não declarar autenticação forte com base apenas em booleanos recebidos.

O estado é limitado e a classificação é executada sob demanda, sem novo polling
permanente. Espera-se custo pequeno por frame, mas **CPU percentual, heap e RSS
não foram medidos nesta etapa**. Não há estimativa numérica homologada nem
garantia de consumo. Validar separadamente custo dos leitores, serialização,
cache, main e renderer na futura sessão autorizada; o tamanho serializado não é
o consumo residente.

## Arquivos principais

- `diagnostics/evidence_contract.py`: envelope e enums.
- `diagnostics/evidence_adapters.py`: cinco validadores e projeções.
- `diagnostics/evidence_cache.py`: correlação, limites e invalidação.
- `diagnostics/mock_evidence.py`: fonte finita e cenários determinísticos.
- `apps/windows-ui/diagnostics-model.js`: validação e composição dos cartões.
- `apps/windows-ui/diagnostics-host.cjs`: provider simulado e envelope no main.
- `tests/test_evidence_adapters.py` e `tests/diagnostic-evidence.cjs`: testes novos.
- `scripts/test-diagnostic-evidence.py` e `.cjs`: regressões isoladas.
- `scripts/preservation_rules.py`: referência exata do preload já aprovado.

As fixtures novas estão em `tests/fixtures`, fora dos recursos distribuídos da
interface. Nenhuma instalação foi empacotada ou substituída.
