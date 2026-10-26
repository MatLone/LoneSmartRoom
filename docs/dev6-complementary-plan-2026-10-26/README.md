# Dev.6 — investigação e plano complementar, sem sessão física

Data: 26/10/2026. Base preservada: `36cfe6e`, branch
`feature/ui-migration-preview`. Horários deste relatório em Brasília (UTC−3).
**Homologação permanece parcial.** Nenhum Electron, sensor, DLL ADLX ou instalador
foi executado nesta etapa. Foram adicionados somente testes e documentação;
nenhuma correção funcional foi aplicada, inclusive ao código de desenvolvimento.

## Resultado principal

1. O excesso de prazo decorreu do procedimento de observação e encerramento.
   O observador anterior tinha corte em **185 s**, embora a autorização fosse
   180 s, e não solicitava Sair. A interação manual foi solicitada tarde.
2. Os mocks preservam os limites **3 s / 11 s / 1,5 s**, mas identificaram uma
   discrepância determinística: uma leitura GPU nova com estado `error` pode
   retirar **Atualizando** sem uma leitura válida. Os valores continuam `null`.
3. Crashpad `0xE9` indica falha de comunicação com a outra ponta do pipe.
   A causa dessa indisponibilidade e o estado do crash reporting permanecem
   inconclusivos. Não há comprovação de crash do dashboard nesses registros.

## Prazo da sessão anterior: o que aconteceu

O arquivo histórico privado `observe-owned.py`, linha 107, contém
`if not live or elapsed>=185:break`. Ele é um observador passivo, sem comando de
Sair ou controle da janela. Interromper a medição não encerra o aplicativo.
Seu próprio resultado `ok` exigia duração menor que 180 s e ficou falso;
esse resultado não foi convertido em aprovação temporal.

O relógio estava corretamente ancorado na criação do processo principal:
**09:12:20,345629**, e não na conclusão da ferramenta de abertura. Portanto não
foi identificado defeito na origem do relógio. O defeito do procedimento foi
usar outro limite e depender de uma interação manual sem margem suficiente.

| Momento relativo ao lançamento | Evidência existente |
| --- | --- |
| 10,2–128,3 s | Oito capturas e verificações consumiram grande parte do orçamento |
| Aproximadamente 145 s | Minimização para bandeja e solicitação de restauração/Sair ao usuário |
| 180 s | Prazo autorizado sem encerramento confirmado |
| 185,314 s | Observador termina; aplicativo e componentes ainda ativos |
| 323,845 s | Nova inspeção ainda encontra o aplicativo ativo |
| Depois da confirmação manual | Encerramento e ausência de filhos/pipes confirmados, sem força |

O instante exato de Sair não foi capturado. Não é correto chamar 185 s de duração
total da sessão, nem concluir que Sair foi recebido a tempo e falhou. A dependência
de resposta no chat e ferramentas que não permitem controle direto da bandeja
foi uma limitação conhecida, tratada tarde. Minha condução anterior não reservou
tempo suficiente; o limite autorizado não foi cumprido.

Preparou-se agora uma **especificação executável apenas de teste**,
[`complementary-session-policy.cjs`](../../tests/helpers/complementary-session-policy.cjs).
Ela não instala watchdog, não tem temporizadores ou APIs de processos e não é
importada pelo aplicativo. Ensaios com relógio falso comprovam que atraso,
pendências de limpeza e confirmação depois do limite nunca produzem sucesso.

## Frescor, disponibilidade e contagem de frames

Os testes exercitam o modelo/host existentes, com processos, transporte e relógios
substitutos; não alteram o contrato v1:

- GPU ativa: idade menor que 3 s válida; **a partir de 3 s**, expirada e valor nulo.
- GPU inativa: idade menor que 11 s válida; **a partir de 11 s**, expirada.
- Ingresso ADLX: idade até **1,5 s** aceita; 1,500001 s, idade negativa,
  NaN e infinito rejeitados. Nenhuma tolerância foi aumentada.
- Amostra anterior à restauração não retira Atualizando. Uma amostra válida nova
  substitui a antiga. Expiração no renderer não renova timestamp.
- Zero válido continua zero; indisponível, erro, incompatível e aquecimento
  permanecem sem valor numérico. Versão/estrutura inválida não vira medição.
- Sequências inválida/válida, duplicata, erro e recuperação mantêm uma única
  abertura do transporte simulado. Aquecimento é contabilizado separadamente.

**Falha exposta, não ignorada:** o diagnóstico
[`dev6-restore-diagnostic.cjs`](../../tests/dev6-restore-diagnostic.cjs) retorna
exit code **1**: 2 de 3 verificações passam e uma falha.
Após minimizar, esperar e restaurar, uma resposta com timestamp recente e
sensores em `error` faz `refreshing` tornar-se falso. A condição de saída em
`apps/windows-ui/monitoring-host.cjs` considera ID, cadência e idade, sem exigir
`m.valid`. Todos os valores dinâmicos permanecem nulos; a leitura válida seguinte
recupera a apresentação sem recriar o processo. Trata-se de uma discrepância do
estado visual de retomada, não de vazamento de valores antigos ou falha TLS.

**Correção mínima proposta, não aplicada:** exigir leitura dinâmica GPU válida,
disponível e fresca, produzida após a retomada, para concluir a atualização com
sucesso. Definir separadamente o resultado terminal de sensores permanentemente
incompatíveis/indisponíveis, para não deixar Atualizando indefinidamente: apresentar
Indisponível com motivo, sem tratá-lo como sucesso de leitura. Essa semântica
precisa de aprovação e testes de regressão antes de encerrar a pendência.

O novo teste Python conta frames **na fronteira de admissão do provedor**, usando
o timestamp SDK aceito antes/depois. Um frame com oito métricas conta uma vez;
40 frames não são 320 frames. Um frame estruturalmente válido com todos os
sensores indisponíveis pode ser admitido sem possuir leituras numéricas válidas.
As contagens existem **apenas na fixture**, não foram adicionadas ao aplicativo
instalado. Quantidades operacionais exatas ainda exigem observabilidade aprovada.

## Ciclo de vida testado com substitutos

As regressões e ensaios novos cobrem: ocultar pela bandeja e restaurar a mesma
janela; dashboard/widget; persistência do redimensionamento; cadência inativa
e retorno a um único timer ativo; recusa de inicialização duplicada; Sair
simultâneo consolidado em uma solicitação; espera cooperativa dos componentes;
remoção dos timers e destruição do Tray depois da limpeza. As regressões Python
cobrem ACL/identidade do cliente, limites, recuperação e fechamento de handles.

Liberação de pipes e ausência de órfãos nesta etapa são verificações de
**handles/processos simulados**, não uma nova comprovação física Windows.
Não foi criado Named Pipe real. Não se concede garantia de encerramento de
uma biblioteca nativa travada a partir desses mocks.

## Resultados reproduzíveis

| Grupo executado | Resultado |
| --- | --- |
| Python básico/preservação/launchers | 133 aprovados |
| Python IPC protegido | 28 aprovados |
| Python provedor ADLX | 28 aprovados |
| Python sessão ADLX simulada | 10 aprovados |
| Python composição GPU e ownership | 26 aprovados |
| Python admissão e contagens novas | 5 aprovados |
| **Total Python** | **230 aprovados, zero falhas/erros/skips** |
| Node janela/preload, bandeja, monitoramento, runtime/renderização, distribuição, manutenção e GPU/dev.6 | 415 aprovadas |
| Node plano e limites novos | 43 aprovadas |
| Node diagnóstico estrito de retomada | **2 aprovadas e 1 falha** |
| **Total Node, incluindo diagnóstico** | **461 verificações, 460 aprovadas, 1 falha** |

Não se declara suíte totalmente verde. Não houve compilação nem execução dos
testes nativos C++/DLL: os arquivos nativos não mudaram. Artefatos e fontes
operacionais conservaram seus hashes. Campos históricos de recibos antigos,
como `developmentSourceChanged`, não significam mudança de fonte nesta etapa.

Novos testes, sem Electron físico:

```powershell
& '.venv/Scripts/python.exe' -B 'scripts/test-dev6-complementary-isolated.py'
& 'C:/Program Files/nodejs/node.exe' 'tests/dev6-complementary-plan.cjs'
& 'C:/Program Files/nodejs/node.exe' 'tests/dev6-restore-diagnostic.cjs'
```

O último comando deve atualmente retornar 1, exibindo a falha conhecida. Não foi
incluído como sucesso esperado, skip ou falha silenciosamente tolerada.
Recibos e inventário dos comandos: [evidências](evidence/test-results.json).

## Crashpad: correlação e limites da evidência

Reutilizado somente o `debug.log` anterior, 332 bytes, SHA-256
`9144f2dc7ef0980c4478a0f5c020275765dc7a301ea505567b136c57c9979ad2`.
Não foram gerados novos logs do Electron ou lidos dumps/memória.

| Registro | Relação com os processos observados |
| --- | --- |
| 09:12:21,394 / T+1,048 s | Logo após criação dos filhos Electron 1688, 21668 e 20708; antes do coletor/ADLX |
| 09:14:21,399 / T+121,053 s | 20,565 ms após criação do filho Electron transitório 21760 |

Separação: **120,005 s**. O filho 21760 apareceu em somente uma amostra; sua linha
de comando/função não foi registrada. O log não informa PID. Não há base para
identificá-lo como handler Crashpad ou atribuir a ele a mensagem. Também não há
base para concluir que esse intervalo prova um retry periódico específico.

Na [documentação Microsoft](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-),
233/0xE9 é `ERROR_PIPE_NOT_CONNECTED`: a outra ponta não tem processo conectado.
Não é acesso negado nem o código 0xE8. No
[código oficial Crashpad](https://chromium.googlesource.com/crashpad/crashpad/+/refs/heads/main/util/win/registration_protocol_win.cc),
`SendToCrashHandlerServer` registra a falha de `TransactNamedPipe` e retorna falso;
isso descreve uma transação de registro/comunicação, não uma exceção fatal do
renderer. Fonte consultada: blob `95111f9c5f9bea9e938130df2fb882ef347867f2`.
A revisão exata do Crashpad embarcado não foi determinada; a fonte consultada
serve para interpretar a operação, sem assegurar correspondência binária integral.

O aplicativo e os componentes principais continuaram ativos, com atualizações
nas capturas. A consulta anterior aos eventos 1000/1001 e 4101 entre 09:12:19 e
09:49 não encontrou eventos relevantes. Ausência desses eventos não garante que
crash reporting esteja íntegro nem descarta toda falha transitória de subprocesso.

Hipóteses ainda abertas: inicialização/terminação de uma ponta antes do registro,
falha de bootstrap do handler ou criação transitória de outro cliente. Não existe
evidência suficiente para escolher uma como causa. A falha inicial antecedeu o
carregamento ADLX, o que enfraquece sua atribuição à consulta GPU, sem provar
causalidade alternativa. O pipe citado pertence a Crashpad; não é evidência de
falha do Named Pipe métrico ou HTTPS. Nenhuma desativação ou correção proposta
de Crashpad será aplicada sem diagnóstico adicional autorizado.

Investigação futura de menor risco: inspecionar offline os metadados existentes
da versão Electron/Crashpad e as rotas de inicialização. Se for indispensável
capturar função de subprocesso/exit code, preparar instrumentação local restrita
e sanitizada para uma sessão autorizada, sem habilitar depuração genérica,
transmitir dumps ou desativar reporting. Isso não foi executado agora.

## Sessão complementar proposta — autorização futura obrigatória

**Limite proposto: 120 s**, contados desde a criação do processo instalado,
sem reiniciar o relógio após uma ferramenta ou restauração. Objetivo de duração
normal: até 90 s; os 30 s restantes são reserva, não novas verificações.
O plano abaixo não está autorizado a ser executado nesta entrega.

Antes de lançar: gates de integridade/agente/grants/perfil/backup; operador já
posicionado na bandeja, canal de Sair disponível e cronômetro independente pronto.
Se a ferramenta não puder operar a bandeja, combinar previamente a ação manual
do usuário, sem depender de uma resposta tardia no chat. Uma chamada longa ou
sem prazo compatível não deve começar durante a janela de observação.

| Janela | Ação prioritária |
| --- | --- |
| 0–15 s | Um lançamento; identificar janela/filhos; uma captura de dados reais |
| 15–30 s | Minimização explícita; inatividade; restauração da mesma janela; observar Atualizando e leitura nova |
| 30–45 s | Widget e redimensionamento; uma captura; se faltar tempo, registrar não testado e passar a Sair |
| **45 s** | **Interromper novas verificações e selecionar Sair normalmente** |
| 45–90 s | Acompanhar fechamento cooperativo e confirmar zero componentes/pipes; preservar evidências |
| 90–120 s | Apenas reserva de encerramento e confirmação; nenhuma nova navegação/captura opcional |
| **120 s** | Se ainda ativo ou fechamento não confirmado: **reprovado por prazo**, registrar e interromper a sequência, sem força/reabertura |

Se o acesso a Sair falhar no primeiro intento, priorizar imediatamente o operador
manual já preparado. O procedimento não pode garantir uma duração física máxima
sob travamento respeitando a proibição de força. O limite é um **critério rigoroso
de aprovação**, não uma alegação de que um script terminará qualquer processo.
Ao excedê-lo, nenhuma recuperação operacional adicional será feita sem autorização.

Máximo de duas capturas prioritárias durante a janela; abas já aprovadas não
serão novamente percorridas antes de Sair. Não medir desempenho por 150 s nesta
sessão curta. Zero carga artificial, jogos, comandos remotos ou alterações.

## Critérios objetivos para homologação

- Antes: ausência de componentes de desenvolvimento e duplicatas; agente original
  identificado, listener único 8776, autenticação válida e zero grants.
- Frescor: limites 3/11/1,5 mantidos; amostra anterior à restauração não aparece
  atual; retomada sinaliza Atualizando até uma amostra válida ou estado terminal
  de indisponibilidade explicitamente definido e aprovado. **A discrepância
  demonstrada precisa ser resolvida/aprovada antes da homologação integral.**
- Contagem: distinguir frames admitidos/rejeitados/aquecimento de métricas válidas;
  não inferir contagem do número de snapshots. Para exigência de contagens exatas
  físicas, aprovar antes telemetria somente leitura, limitada e sanitizada no
  ponto de admissão. Essa observabilidade ainda não existe no pacote operacional.
- Interface: bandeja restaura a mesma janela; widget redimensiona e retém limites
  visíveis; nenhuma duplicata; cadência reduzida e retomada sem respawn indevido.
- Sair confirmado com todos os componentes próprios e pipes liberados **antes de
  120 s**. Um fechamento posterior não transforma a sessão em sucesso temporal.
- Nenhum crash/travamento relevante. Estado de Crashpad deve ser esclarecido ou
  aceito explicitamente como pendência delimitada; as mensagens não serão ocultadas.
- Depois: agente original ativo/autenticado, zero grants e dados/backup preservados.
  Se um item não puder ser observado, registrar **não verificado**, sem aprovação
  presumida. Homologação parcial não é homologação integral.

## Preservação e reversão

Conferência final às **10:24**: supervisor 5024 e worker 18304, mesmos executáveis,
argumentos, criação e cadeia de processos, incluindo redirectors 19996/20352.
Único listener LAN 8776 no worker; TLS 1.3, certificado/hostname/pin verificados,
GET status/apps HTTP 200, zero grants e zero comandos pendentes. Não houve nova
validação física do Samsung; as consultas usaram a identidade existente somente
em memória, sem criar identidade ou registrar segredos.

Instalação (117 arquivos), perfil (77) e quatro árvores de backups (341/75/156/189)
permanecem byte a byte iguais ao início desta etapa. Os 189 do backup dev.6 incluem
186 arquivos de dados e três metadados. Não houve novo backup nem restauração.
97 fontes preparados e 86 arquivos operacionais protegidos sem diferenças;
integridade SQLite, identidades cifradas, revogações e esquema preservados.
Sem processos Electron, monitoramento, ADLX ou instaladores ao final.

Run/RunOnce, Inicializar, serviços e firewall sem alterações na comparação.
Uma tarefa teve mudança de hash: OneSettings/RefreshCache, novamente sem alteração
de contagem ou identificação do ator. Mantida como **observação inconclusiva**;
não se atribui a Lone Smart Room, nem se interfere na tarefa. Não há vínculo
comprovado com Crashpad. [Recibo de preservação](evidence/preservation-final.json).

Reversão deste trabalho é somente `git revert` dos novos commits de testes e
documentação, em ordem inversa, após revisão. Não restaurar perfil, desinstalar,
fazer downgrade ou tocar no agente para reverter estes arquivos. Checkpoints,
APKs, instaladores e backups anteriores continuam preservados. TLS e encerramento
gracioso do agente seguem como investigações separadas, sem alterações.

Próxima decisão: autorizar ou rejeitar a correção mínima de retomada e a
observabilidade complementar; depois revisar e autorizar separadamente uma sessão
física curta. **Nenhuma segunda sessão foi realizada.**

Commit isolado dos testes:
`b52c918780d5301d8b32c5190cfd2af1532fa3cf`.
O commit documental seguinte registra este relatório e recibos sanitizados;
seu hash é informado na entrega. A branch continua derivada de `36cfe6e`,
sem reescrita de histórico. Os arquivos privados de comparação permanecem
somente em `.cache/validation/dev6-complementary-plan-2026-10-26/`, fora do Git.
