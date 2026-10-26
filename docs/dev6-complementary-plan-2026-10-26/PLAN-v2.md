# Plano complementar v2 — 120 segundos, ainda não executado

Atualizado em 26/10/2026 após a [correção de retomada GPU](../gpu-resume-fix-2026-10-26/README.md).
Substitui o planejamento prospectivo do README desta pasta, preservado como
registro histórico. Não altera os resultados da primeira sessão nem apaga sua
falha de prazo. **Nova sessão física exige autorização específica.**

## Condições antes de lançar

1. Escolher o alvo autorizado e registrar seu hash/commit. A instalação dev.6
   original permanece inalterada e não contém a correção; não serve para homologar
   a mudança de fonte. Não recompilar, empacotar ou instalar sem escopo aprovado.
2. Confirmar integridade/perfil/backup, ausência de duplicatas e componentes
   residuais, agente original autenticado, listener único 8776 e zero grants.
3. Ensaiar com mocks o relógio e o fluxo normal Sair. Operador pronto na bandeja,
   antes da abertura, e cronômetro independente disponível. Se a ferramenta não
   puder operar a bandeja, combinar previamente o clique manual do usuário.
4. Contar desde a **criação do processo**, usando relógio monotônico, e registrar
   também o horário UTC. Não reiniciar o relógio após ferramentas, restauração ou
   mudança de modo. Não iniciar chamadas cuja duração prevista consuma a reserva.

## Agenda e orçamento

| Desde a abertura | Verificação |
| --- | --- |
| 0–15 s | Única janela/componentes, dados válidos; primeira captura prioritária |
| 15–30 s | Bandeja explícita, inatividade e restauração da mesma janela; Atualizando, seguida de amostra nova |
| 30–45 s | Widget/redimensionamento e segunda captura; cortar itens opcionais se faltar margem |
| **45 s** | **Parar novas verificações e selecionar Sair normalmente** |
| 45–90 s | Confirmar encerramento cooperativo e liberação dos componentes/pipes |
| 90–120 s | Reserva exclusiva para fechamento/inspeção; nenhuma nova tarefa |
| **120 s** | Prazo vencido sem confirmação completa: reprovação temporal e interrupção da sequência |

Se Sair não estiver acessível no primeiro intento, acionar imediatamente o
operador manual já preparado. Não iniciar longa troca de mensagens para só então
planejar a saída. Até duas capturas; não repetir a auditoria de todas as abas.
Não programar observação de desempenho de 150 s nesta sessão curta.

O limite é um critério de aprovação, não uma promessa de matar um processo
travado. Não haverá kill, reinício, logoff ou repetição automática. Se o fechamento
normal não concluir antes de 120 s, registrar a falha e solicitar decisão sobre
recuperação; confirmação tardia não pode tornar o resultado aprovado.

## Verificações e critérios

- Retomada mostra Atualizando até leitura dinâmica válida, recente e posterior
  à restauração. Uma rejeição não conclui sucesso. Falha persistente por 10 s
  mostra indisponibilidade explícita, continuando apta a recuperar por leitura
  válida. **Esse orçamento visual não flexibiliza frescor.**
- Ingresso ADLX permanece <=1,5 s, expiração ativa 3 s e inativa 11 s. Valores
  nulos/erros não viram zero; zero válido continua zero. Amostra antiga de outro
  sensor não é promovida a atual quando a recuperação é parcial.
- Não provocar erros reais, desconectar transporte, executar jogos ou gerar
  carga para obter evidências: cenários determinísticos de falha são cobertos
  pelos mocks. Se não ocorrerem naturalmente, registrar não observados no hardware.
- Identificação das idades/contagens deve vir apenas de observabilidade já
  autorizada. Não inferir frames do número de snapshots ou métricas. Se o alvo
  não expuser contagens exatas, o item permanece não verificado; não abrir debug,
  adicionar endpoints ou instrumentar silenciosamente a instalação.
- Widget e dashboard compartilham leituras; bandeja restaura a mesma janela;
  redimensionamento mantém limites visíveis; nenhuma instância duplicada.
- Confirmar Electron, coletor, intermediário e ADLX encerrados e pipes liberados
  **antes de 120 s**. Não inferir limpeza apenas do envio de Sair.
- Agente original ativo/autenticado, zero grants e perfil/backup preservados ao
  final. Nenhuma alteração a Android, agente, rede, autostart ou segurança.
- Crashpad permanece pendência separada: registrar mensagens existentes/novas,
  sem desativar reporting. Crash/travamento relevante reprova. Aceitação de uma
  pendência delimitada precisa ser explícita. OneSettings permanece inconclusiva.

A especificação de prazo simulada existente em
`tests/helpers/complementary-session-policy.cjs` rejeita confirmações >=120 s,
componentes remanescentes e relógio inválido. Não é um watchdog operacional.
Os novos testes da recuperação e a regressão originalmente falha estão verdes;
isso não substitui validação física nem autoriza executá-la agora.
