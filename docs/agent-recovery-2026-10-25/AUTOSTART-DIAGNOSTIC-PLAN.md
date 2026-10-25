# Inicialização automática — plano separado, não executado

Objetivo: distinguir **despacho de HKCU Run** de **falha posterior no bootstrap**.
Este plano não modifica Registro, políticas, serviços, tarefas ou processos, não
habilita captura e não autoriza login/logoff/reinicialização. A recuperação manual
é uma prova do launcher no contexto atual, não uma prova de despacho no próximo login.

## Fatos que orientam a investigação

- A entrada `LoneSmartRoomSecureAgent` continua com o comando antigo que usa
  diretamente `secure_agent.py serve`; não aponta para o launcher validado manualmente.
- O comando Run mantém SHA-256 histórico e 221 caracteres. Sua existência e sintaxe
  plausível não demonstram que o Windows chegou a executá-lo.
- O launcher possui logs próprios, mas o caminho direto do Run não registra esse
  bootstrap. Assim, ausência de log de launcher não prova ausência de despacho.
- O Windows processa Run no login, com ordem indeterminada entre entradas; não
  presumir CWD, disponibilidade da rede ou equivalência ao ambiente manual.
  [Microsoft: Run e RunOnce](https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys).
- Rede não Privada pode deixar o agente aguardando sem listener; processo ausente
  e processo vivo aguardando são resultados diferentes. Certificado/credenciais
  íntegros não provam que o bootstrap foi alcançado.

## Fase A — proposta de inventário dirigido, somente após aprovação

Conferir o valor exato, tipo e visão nativa/32 bits de Run da conta que faz login,
associando a sessão/token do Explorer. Consultar o item específico nas visões
pertinentes de StartupApproved e políticas existentes; não interpretar ausência de
um valor como bloqueio comprovado. Preservar a divergência histórica entre leitura
direta e WMI até obter evidência da visão efetivamente usada na sessão.

Consultar logs de despacho/processo que já estejam habilitados e acessíveis.
Relacionar apenas interpretador da venv, script esperado, conta/sessão, pais,
horários de criação/saída e códigos sanitizados. Não enumerar argumentos pessoais,
variáveis de ambiente ou conteúdo de memória. Não reparar Registro ou duplicar a
entrada para fazê-la aparecer em outra interface.

Ausência de eventos em um canal desabilitado, inacessível ou sem cobertura do login
é **inconclusiva**. Nenhuma inferência de falha de despacho deve partir só disso.

## Fase B — preparar observação em isolamento, exige autorização adicional

São necessárias duas evidências independentes:

1. **Testemunha do Windows:** criação/saída do processo exato disparado no login,
   não uma sondagem periódica que possa perder um processo curto. Preferir registros
   já existentes. Avaliar captura ETW de processo ou evento 4688, se disponível.
   O 4688 depende de auditoria de criação de processos, e a presença de linha de
   comando depende de política adicional. Não habilitar auditoria global de argumentos
   nem coletar ETL amplo automaticamente: podem conter dados de outros aplicativos.
   [Microsoft: evento 4688](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688).
2. **Testemunha de bootstrap:** fases fixas, UTC, PID/pai, resultado de validação e
   código numérico, sem segredos. Os eventos existentes `attempt`, `paths_ok`,
   `child_created`, `worker_attempt`, `bootstrap_ready` ajudam na versão launcher,
   mas não tornam retroativamente observável o comando direto ainda em Run.

Antes de usar uma captura: identificar ferramentas/provedores disponíveis e os
privilégios necessários, validar filtros, ACL, tamanho/retenção e descarte de dados
alheios. Se não for possível limitar a coleta de modo adequado, apresentar a
alternativa e pedir autorização de privacidade/permissões; não instalar SDK ou
elevar automaticamente. ETW é uma possibilidade técnica, não uma ferramenta já
habilitada nesta entrega.
[Microsoft: sessões SystemTraceProvider](https://learn.microsoft.com/en-us/windows/win32/etw/configuring-and-starting-a-systemtraceprovider-session).

Validar a instrumentação com processos substitutos curtos em ambiente próprio,
incluindo falha antes do primeiro log, falha de log/ACL, filho que encerra cedo e
perda de eventos. Correlacionar PID do payload ETW com pai/horário: o cabeçalho de
um evento de criação pode apontar para o contexto criador, não para o filho.
[Microsoft: eventos de processo](https://learn.microsoft.com/en-us/windows/win32/etw/process).

Não alterar o launcher operacional validado para acrescentar instrumentação agora.
Qualquer wrapper novo deve ser versionado, testado e aprovado separadamente.

## Fase C — uma janela de login controlada, autorização própria obrigatória

1. Definir cobertura da captura e comprovar saúde do coletor antes do evento de
   login. O mecanismo para cobrir o começo da sessão também precisa ser aprovado;
   não criar tarefa/serviço nem boot trace como efeito implícito.
2. Primeiro observar **a entrada atual sem reescrevê-la**, para não mudar a causa
   sob investigação. A reprodução deve distinguir esse teste da migração futura
   para o launcher. Não abrir uma segunda instância enquanto a sessão manual está ativa.
3. Qualquer logoff/reinicialização ou liberação da sessão ativa exige autorização
   específica. Não usar parada forçada nem o encerramento gracioso ainda não validado.
4. Correlacionar conta/sessão, Run conhecido, eventos de criação/saída, fases de
   bootstrap, perfil de rede e listener. Limitar a janela e reconhecer atrasos do
   Windows; não concluir que algo nunca será despachado por uma amostra curta.
5. Estado final planejado: agente novamente ativo e Samsung Conectado. Se Run
   falhar, uma partida manual de recuperação deve estar autorizada explicitamente
   no protocolo dessa fase. Não retentar nem relançar implicitamente.

## Matriz de interpretação

| Evidência combinada | Conclusão permitida |
|---|---|
| Captura íntegra cobrindo a janela, sem criação correspondente | Nenhum despacho observado nessa janela; investigar Explorer/Run/política. Não é prova de impossibilidade permanente |
| Cobertura ausente, evento perdido, log inacessível ou captura iniciada tarde | Inconclusivo; não classificar como falha de despacho |
| Processo exato criado, mas sem primeiro log de bootstrap | Despacho ocorreu; falha antes do primeiro log ou no logger/ACL. Ausência de log não identifica a exceção |
| `attempt` seguido de `paths_invalid` / `environment_invalid` | Bootstrap alcançado; caminho/contexto rejeitado |
| `child_created` sem `worker_attempt`, com evento de saída do filho | Falha na partida/bootstrap do filho; código/ambiente a investigar |
| `bootstrap_ready`, processo vivo, sem listener | Distinguir espera por rede Privada de bind/TLS/servidor ainda não disponível |
| Listener existe e GET autenticado retorna 200 com pin validado | Comunicação funcional; validar Samsung separadamente |
| Processo encerra e há código/erro correlacionado | Falha após criação confirmada; não atribuir somente ao despacho Run |

Se instrumentar uma versão launcher depois, fazê-lo em uma fase distinta da prova
do comando direto. Comparar o resultado sem afirmar que trocar Run resolveu um
Windows que não despache a entrada.

## Recuperação e preservação

Captura futura deve usar armazenamento local restrito, sem exportar logs brutos com
informações pessoais. Não coletar dumps nem senhas/HMAC. Restaurar somente o que
vier a ser alterado e autorizado nessa etapa, usando valor Run exato preservado;
não recriar credenciais, certificados, grants ou identidade do Samsung.

Não encerrar a sessão recuperada para executar este plano agora. Coleta de sensores,
correção TLS e encerramento gracioso continuam pendências independentes.
