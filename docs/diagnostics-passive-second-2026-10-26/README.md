# Segunda validação passiva — 26/10/2026

**Aprovada no escopo observado: parser, identidade do agente, listener e status
HTTPS autenticado. Cobertura completa do autodiagnóstico ainda não homologada.**

Uma única sessão de **2,479 segundos**, dentro do teto de 60 segundos, sem
repetição. Não foram alterados os leitores, o agente ou aplicativos instalados.
A tentativa anterior e seu marcador permaneceram preservados.

## Pré-verificação

- Branch `feature/ui-migration-preview`, inicialmente limpa, em `87e1b40`.
- **150 testes aprovados**, sem falhas, erros ou skips; hashes de **19 fontes e
  testes** correspondem ao código efetivamente usado, incluindo a correção
  `3ee871c`. As opções `-I -B` e a rejeição de comandos/argumentos não permitidos
  foram novamente testadas com mocks.
- Audit hook bloqueou operações externas durante os testes. O bootstrap padrão
  de `ctypes`/SSL ocorre antes do bloqueio, sem sondas ou inicialização ADLX.
- Nenhum leitor residual; agente já ativo e identificado; um listener 8776;
  banco íntegro e zero grants. Nenhuma instância do agente foi iniciada.
- **1.338 arquivos protegidos e quatro arquivos de runtime** idênticos ao
  baseline anterior: instalação Windows, perfil, backups, arquivos de recuperação,
  código protegido, assets e configuração/certificados. APK dev.9 conferido.

Ver [preflight.json](preflight.json), [tests-summary.json](tests-summary.json) e
[preservation-before.json](preservation-before.json).

## Resultado físico

O inventário inicial foi registrado às **20:06:58 UTC / 17:06:58 Brasília**.
A última resposta autenticada foi registrada às **20:07:00.660 UTC**.
Recibo completo: [session.json](session.json).

| Item | Evidência | Resultado |
|---|---|---|
| Supervisor | PID **5024**; redirecionador da venv 19996 | Identidade aprovada |
| Worker HTTPS | PID **18304**; redirecionador da venv 20352 | Identidade aprovada |
| Cadeia de processos | 19996 → 5024 → 20352 → 18304; SID/sessão, imagem, criação, parentesco e argumentos conferidos | Mesma identidade no início e no final, sem elevação |
| Parser | Formato fixo do launcher com `-I -B`, com/sem `--worker` | Correção reconhecida no ambiente real |
| Listener | Exatamente **um**, porta **8776**, pertencente ao worker 18304, binding privado específico | Saudável |
| HTTPS | Dois GETs fixos `/v2/status`, HTTP **200**, **TLS 1.3** | Saudável durante a sessão |
| Identidade TLS | CA/certificado, hostname e pin antes do envio de identidade/HMAC | Validados; sem aceitar certificados indiscriminadamente |
| Banco | `quick_check` OK; hashes de identidade e permissões iguais antes/depois | Íntegro; **zero grants** |
| Electron/coletores/ADLX | Zero processos identificados dos componentes de monitoramento | **Inativos normalmente**, sem comprovar falha |
| Named Pipe | Consulta do namespace devolveu resultado não verificável (`available=false`, contagem `null`) | **Não verificado**; não confundir com ausência confirmada |
| Métricas/frescor | Cache em memória não acessível por interface passiva autorizada, aplicativo fechado | Sem medição atual; valores e idades não foram fabricados |
| Inicialização automática | Run presente com mesmo hash do histórico; 15 registros permitidos do log, ACL verificada | Bootstrap histórico observado; despacho após login **não verificado** |

Os quatro processos Python fazem parte da cadeia de redirecionamento da venv e
launcher; não representam quatro agentes HTTPS. Não houve outro listener nem
inicialização de agente durante o procedimento.

As duas consultas usaram exclusivamente a identidade existente em memória, pelo
mecanismo de auditoria já validado. Nenhuma identidade desktop ou permissão foi
criada. Nonces/última comunicação podem ter sido atualizados normalmente pelo
agente ao autenticar os GETs, conforme autorizado; credenciais e permissões foram
comparadas por hashes lógicos, não por igualdade binária do banco operacional.
Não houve nova validação física do Samsung.

## Categorias e disponibilidade

Os 150 testes confirmam as categorias **Saudável, Indisponível, Desatualizado,
Falha e Não verificado**. **Inativo normalmente** é um motivo explícito
`application_normally_inactive` dentro de Indisponível, não uma Falha e não uma
nova versão incompatível do contrato. Na futura interface esse motivo deve ser
apresentado de forma visível, sem exigir que o usuário interprete um código.

Nesta sessão ocorreram estados Saudável, Não verificado e Indisponível por
inatividade normal. Não foram provocadas falhas nem coletadas amostras antigas
para exibir artificialmente os outros estados. Desatualizado/Falha foram
verificados com mocks, sem sondas adversariais ao agente ou sensores.

O relatório é uma fotografia do horário registrado; sua consulta posterior não
renova timestamps nem garante saúde contínua. O último `bootstrap_ready` é de
**02:41:17.735 UTC**, anterior à sessão. Esse registro não prova que HKCU Run o
originou e não foi promovido a evidência de inicialização automática saudável.
A entrada Run não foi alterada.

## Encerramento, recursos e preservação

- O leitor terminou normalmente; seus handles foram fechados.
- Zero processos próprios de inventário ainda ativos ao encerrar.
- Conferência posterior: **zero leitores residuais**; não foram criados Electron,
  coletores, intermediário de monitoramento ou ponte ADLX.
- Agente original preservado: mesma identidade e listener no final; último GET
  autenticado retornou 200/TLS 1.3; banco e zero grants conferidos novamente.
- **CPU do leitor Python:** 0,046875 s acumulados, equivalentes a aproximadamente
  **0,158% da CPU total da máquina**, em média na janela observada. Método:
  diferença de tempos de CPU do próprio processo, dividida pelo tempo monotônico
  decorrido e pelo número de processadores lógicos.
- **RSS final do leitor:** **30,348 MiB**. Não é média nem pico de memória.
- PowerShell/CIM transitórios não foram incluídos nesses números. A sessão curta
  não permite estimar consumo contínuo, custo total ou comparar com o Electron.
- Preservação posterior aprovada: **1.338 arquivos + quatro de runtime**;
  perfil, backups, configurações, credenciais cifradas, certificados e APK iguais
  ao baseline. Nenhuma instalação, atualização ou comando operacional.

Ver [residuals-after.json](residuals-after.json),
[preservation-after.json](preservation-after.json) e
[validation-summary.json](validation-summary.json).

## Limitações ainda abertas

1. Presença/ausência do Named Pipe continua inconclusiva. Não ampliar ACLs nem
   contornar a validação do intermediário original para forçar resultado saudável.
2. IPC, saúde de amostras e sensores não foram validados fisicamente com o
   Electron fechado. Não iniciar componentes para mudar o diagnóstico.
3. O leitor de logs existentes funciona em modo limitado/ACL verificada, mas
   não comprova despacho de HKCU Run ou correlação com o login.
4. **TLS 10054 continua pendente.** HTTP 200 normal não resolve o reset em
   corpos excessivos/ambíguos. Nenhuma reprodução ou alteração TLS foi feita.
   Mantém-se a [recomendação separada](../diagnostics-passive-2026-10-26/TLS-PLAN.md).
5. ACL por usuário não isola código malicioso executado pela mesma conta.
   Validação de processo não é atestado do conteúdo da memória.
6. O stdout do CLI original contém um caminho de evidência fixo da primeira
   fase. Nesta validação, o diretório de saída foi redirecionado explicitamente
   para `.cache/validation/diagnostics-passive-second-2026-10-26`; os arquivos
   reais estão ali. A primeira fase não foi sobrescrita. Não houve correção do
   CLI neste escopo de validação.

## Plano de integração visual — não executado

1. Após autorização separada, preparar em desenvolvimento isolado uma projeção
   limitada dos estados ao processo principal do Electron. Não copiar a
   identidade Android para um novo cliente desktop.
2. API preload somente leitura, com contrato versionado, sem comandos genéricos,
   caminhos, segredos, acesso direto ao Registry ou ao pipe pelo renderer.
   Manter `contextIsolation` e Node desabilitado no renderer.
3. Para o monitoramento aberto, reutilizar o estado já validado do host em
   memória. Não conectar um cliente adicional ao pipe que aceita apenas seu
   intermediário autorizado. Separar processo existente, transporte e amostra.
4. Cartões claros: Saudável; Indisponível; Desatualizado; Falha; Não verificado;
   motivo **Inativo normalmente**. Mostrar horário da evidência e última
   comunicação autenticada, sem renovar leituras antigas pelo polling da UI.
5. Cadência baixa/configurável e pausa com painel oculto. Aplicativo fechado é
   inatividade, não falha. Sem reparo automático, novos grants ou comandos.
6. Testar essas projeções com mocks e isolamento de perfil antes de solicitar
   qualquer execução física. Um novo cliente HTTPS operacional continua
   condicionado à resolução/validação da pendência TLS relevante.

Nenhuma alteração visual, integração operacional ou atualização instalada foi
executada nesta tarefa.

## Histórico, evidências e reversão

Os commits `86ab555`, `3ee871c`, `139e1c8`, `87e1b40` e os demais checkpoints
verificados permanecem ancestrais. Os 19 fontes/testes ficaram inalterados.
Houve apenas nova documentação versionada desta sessão.

O driver de validação usou o mesmo `run_session` e os mesmos leitores, com fase
independente e marcador exclusivo. Os hashes dos scripts auxiliares locais
estão em [validation-driver-hashes.json](validation-driver-hashes.json);
os hashes das evidências públicas em [evidence-sha256.json](evidence-sha256.json).
Nenhum caminho privado, SID, header HMAC, segredo ou conteúdo cifrado do banco
foi exportado nos recibos públicos.

Não há implantação ou alteração operacional a reverter. Se necessário, reverter
somente o commit documental em branch de revisão, preservando as evidências
locais. Não restaurar o banco para desfazer bookkeeping normal dos GETs, não
apagar nonces/credenciais e não reiniciar o agente. Os backups permanecem intactos.
