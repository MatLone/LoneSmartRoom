# Monitoramento — entrega da fundação isolada

Autorização: contrato, coletor independente, cache e testes simulados, preservando
`65340970bba7435cd2606900317a584d20ee9a9f` e seus ancestrais. Sem coleta física.

Implementação e testes: commit `a956004` (`feat(monitoring): add isolated collector
contracts cache and simulated tests`). Documentação e recibo registrados em commit
subsequente, separadamente do código.

## Resultado

- Pacote [monitoring](../../monitoring/README.md), sem dependências adicionais,
  provedores de hardware ou partida automática ao importar.
- Contrato v1 e 22 slots para i5-12400, RX 6750 XT/VRAM, RAM DDR4, volume/disco do
  sistema e ventoinhas opcionais. Capacidade e existência real de sensores não presumidas.
- Cadências configuráveis 1/2/60 s; inativo 5/10/60 s. Cache de até 120 amostras
  por métrica, idade monotônica, valores inválidos/antigos nulos e cancelamento próprio.
- Serviço lógico de IPC somente leitura, com política de conta/sessão, rejeição
  remota, parser e limites; [ACL/transporte nativo planejados](../../monitoring/IPC-PLAN.md),
  sem pipe ou socket aberto e sem cliente Electron implementado.

## Testes concluídos

Comando: `.venv/Scripts/python.exe -B scripts/test-monitoring-isolated.py`.

**91 testes aprovados, zero falhas, zero erros, zero skips**, na rodada final:

| Grupo | Quantidade / cobertura |
|---|---|
| Contrato/cache | 16: valores, origem, unidades, ausência, Zero RPM, NaN/inf/bool, limites, UTC, idade, histórico e publicação atômica |
| Coletor/lifecycle | 25: frequências, inatividade, erro/recuperação, provedores inválidos, deadline, memória limitada, concorrência, stop, timeout e falha de close |
| IPC lógico | 15: conta/sessão/remoto, identidade forjada em JSON, operações vedadas, parser, limites exatos, rate limit, sanitização e estado parado |
| Regressões existentes | 35: preservação Android/identidade/WoL, parsing de recuperação WoL e launchers Steam/CS2 com substitutos |

Não foi executada a suíte HTTPS com servidores de teste, nem requisição ao agente
real. Não há alegação de novo teste físico de WoL, TLS, autenticação, grants ou
conectividade Samsung. Os fontes de agente, Android e Electron não foram alterados.

A primeira tentativa do runner foi interrompida pelo guard ao carregar ctypes,
importado pelos testes antigos de preservação. Não chegou a executar a suíte ou
coleta. O bootstrap da biblioteca padrão foi antecipado, mantendo o bloqueio de
novas DLLs/operações externas durante testes. A primeira rodada completa passou
90 testes. A revisão identificou uma corrida entre stop e limpeza do evento de
despertar; foi corrigida e recebeu teste determinístico. A rodada final passou 91.
Nenhum teste com falha foi ignorado ou convertido em skip.

### Ensaio de recursos sintético

Recibo sanitizado: [tests.json](tests.json). Fixture com 22 métricas, 200 passagens
de aquecimento e 2.000 passagens adicionais, avançando o relógio simulado em 60 s.
Não houve espera correspondente a esses períodos nem leitura de sensores.

| Medida do próprio ensaio | Resultado |
|---|---:|
| Tempo de parede das 2.000 passagens com tracemalloc ativo | 0,8880 s |
| Tempo de CPU do processo de teste nessa região | 0,828125 s |
| Alocação Python rastreada retida ao final | 396.642 bytes |
| Pico de alocação Python rastreada | 404.842 bytes |
| Amostras retidas / limite com catálogo atual | 2.640 / 2.640 |
| Encerramento do coletor da fixture | Limpo |

O teste de estabilização também confirmou crescimento abaixo de 128 KiB entre
dois blocos de 1.000 passagens após aquecimento. `tracemalloc` mede alocações Python
da região rastreada, **não working set total, memória privada, consumo global de CPU,
overhead de sensores ou desempenho em jogo**. As estimativas da auditoria continuam
não medidas em coleta real. Não comparar esse laço acelerado com o orçamento a 1 Hz.

## Preservação e limites

Nenhuma alteração sob `agent/` ou `apps/`, nenhum pacote/dependência instalado,
nenhuma atualização Android/Electron ou alteração do perfil de produção. Não foram
acessados banco, certificados ou credenciais reais, nem iniciado/encerrado o agente.
Nenhum grant concedido, processo Steam/CS2 aberto, WoL enviado ou energia acionada.
Backups existentes não foram alterados; esta etapa não fez nova auditoria de sua
integridade física nem reconsultou o estado do Samsung ou da porta 8776.

Mantém-se a decisão de preservar o legado ativo e o último estado conhecido Samsung
Conectado, sem apresentá-los como nova observação. A pendência
[TLS](../design/brand/compact-review-2026-10-24/TLS.md) e o teste adiado de
[encerramento do agente](../legacy-release-gate-2026-10-24/README.md) continuam separados.

Limitações: não há segurança nativa de IPC comprovada, sensor real detectado,
provider Win32/psutil/ADLX/LHM, isolamento de provider nativo em subprocesso ou
integração no dashboard. Thread Python não pode ser interrompida com segurança;
timeout de read/close não vira sucesso nem autoriza kill. Provedor futuro deverá
respeitar deadlines e devolver dados frescos; falha deve gerar indisponibilidade.

## Próxima fase proposta — NÃO executada

Mediante autorização específica:

1. Implementar provedores básicos com APIs Win32 documentadas em ambiente separado,
   primeiro validando wrappers com mocks. Preferir biblioteca padrão para esta prova;
   instalar psutil só se houver necessidade e autorização. Sem temperatura CPU, RPM,
   ADLX, SMART, novos drivers, elevação ou dependência do agente.
2. Revisar código para permitir exclusivamente utilização CPU, RAM e capacidade/
   espaço/I/O do volume/disco do sistema. Resolução local do volume e associação ao
   disco precisam de leitura autorizada; não presumir que uma partição é um disco.
3. Executar **uma sessão isolada de até 90 segundos**, sem listener TCP/pipe, sem
   acoplar ao Electron/Android. CPU/RAM/I/O a cada 1 s, espaço a cada 60 s; primeira
   amostra de taxas em aquecimento. Se contador indisponível, retornar null, sem
   habilitá-lo ou reparar Windows. Não executar benchmark de carga ou jogo.
4. Conferir coerência (RAM usada + disponível = total utilizável na mesma amostra,
   bytes/percentuais e quotas), idade, cadência e limites. Comparação com Gerenciador
   de Tarefas somente se aprovada, respeitando diferenças de definição e instante.
5. Registrar somente resultados necessários, sem serials, nomes de arquivos ou
   processos pessoais. Medir custo do próprio coletor separadamente dos valores do
   PC; este é o teste que poderá validar as estimativas de desempenho.
6. Encerrar somente o coletor pelo mecanismo cooperativo; verificar que suas threads
   terminaram. Timeout/falha interrompe a sequência, sem forçar processos ou tocar
   no agente legado. Nenhuma repetição automática ou instalação.

O resultado esperado é uma primeira prova de sensores básicos, **sem mudar a
conectividade do Samsung**. Temperaturas/fans/GPU e integração de interfaces exigirão
fases próprias. Esta documentação não constitui autorização para o teste acima.

## Reversão

Esta etapa adiciona somente `monitoring/`, `tests/monitoring/`, o runner isolado e
esta documentação; não substitui arquivos operacionais. Reverter os commits desta
entrega com `git revert`, em ordem inversa e após revisar alterações posteriores,
remove a fundação: primeiro o commit documental, depois `a956004`. Não usar reset --hard, limpeza de perfil ou restauração de
credenciais. Os recibos em `.cache/validation/monitoring-foundation/` são ignorados
pelo Git e não precisam ser apagados. Nenhum rollback físico é necessário.
