# Validação do inventário e plano — 26/10/2026

**Plano entregue; gate global de regressão não aprovado.** Não houve alteração de
código operacional nem tentativa de corrigir a divergência por atualização cega
de hashes. Não avançou integração real ou aplicação de ajustes.

| Verificação | Resultado observado |
|---|---|
| Python, 18 módulos existentes | 375 testes: 374 passaram, um erro de preservação, zero skips |
| Node, 12 suítes de contrato/UI substituída | Todas passaram: 690 verificações contabilizadas e uma suíte sem contagem declarada |
| Comparação do checkpoint | 1.869 arquivos comparados; três arquivos não versionados de diagnóstico mudaram concorrentemente |
| Fontes já versionados no instante da comparação Python | Nenhum diff; preload idêntico ao blob do HEAD inicial; edições concorrentes posteriores descritas abaixo |
| HTTPS operacional, sensores e WoL reais | Não executados; não são validados por estas regressões |

## Divergência encontrada

`test_baseline.BaselinePreservation.test_functional_sources_unchanged`, subteste
`apps/windows-ui/preload.cjs`, lança `ValueError` em
`scripts/preservation_rules.py:40`: “Windows visual entry/bridge differs from
reviewed revision”. O pin esperado é
`5fc9553bd9f9cddb98f099a8fc1c0d7ea53ae197c12e87eb5f628755a6481eba`;
o SHA-256 do checkpoint e do arquivo atual é
`c20b427fea83d32c456cabacdc894fa5286df2647dbf5c693ea005b2011d3046`.
O blob Git do HEAD e do working tree é o mesmo:
`58bef762cef4fd8cba2c0fc567853a190cf92b0c`.

Portanto, a divergência de pin já estava na base desta tarefa; não foi introduzida
pelo plano. A Central de Diagnóstico e as outras guardas Node passaram, mas isso
não autoriza ignorar o gate de preservação. Antes de C1, revisar o diff histórico
da ponte/preload contra o pin aprovado e justificar qualquer atualização do pin;
nunca ampliar a exceção para aceitar qualquer conteúdo.

## Alterações concorrentes

Entre o checkpoint e os testes mudaram `diagnostics/evidence_adapters.py`,
`diagnostics/evidence_cache.py` e `diagnostics/mock_evidence.py`, todos fora do
Git. A primeira inspeção viu três arquivos; o checkpoint viu quatro, incluindo
`mock_evidence.py`. Esses arquivos não foram escritos por esta tarefa e não foram
restaurados, adicionados ao commit ou promovidos a integração operacional.
Não se afirma uma fotografia atômica do workspace nem preservação integral dos
arquivos não versionados durante trabalho concorrente. O comparador permanece
reprovando diferenças, sem whitelist silenciosa.

Na conferência posterior aos testes também apareceram mudanças concorrentes em
`apps/windows-ui/diagnostics-host.cjs`, `apps/windows-ui/diagnostics-model.js` e
`tests/diagnostic-center.cjs`. Não foram feitas por esta tarefa nem incluídas em
seu commit. Os resultados anexados representam a execução anterior, não homologam
essas edições posteriores. Antes de C1, estabilizar o workspace e executar novamente
as regressões do diff consolidado. Nenhum arquivo concorrente foi descartado.

## Método e recibos

Runner novo: `scripts/test-modular-expansion-offline.py`, executado com
`.venv/Scripts/python.exe -B`. Importa ctypes/SSL da stdlib antes da guarda;
depois bloqueia sockets, Registro, processos, shell/startfile e novas chamadas
ctypes. Reutiliza testes existentes de launchers, WoL, monitoramento, ADLX, IPC
e diagnóstico com provedores substituídos. Não faz TLS end-to-end em loopback,
não acessa o banco operacional nem valida novos módulos ainda não implementados.
O runner requer o checkpoint local desta sessão; não é um comando de CI portátil.

Suítes Node executadas com o Node existente, cada uma em processo próprio:
`diagnostic-center`, `electron-window-policy`, `electron-tray`,
`electron-monitoring`, `windows-dev5-monitoring`, `windows-dev5-renderer`,
`windows-distribution-policy`, `windows-dev6-monitoring`,
`windows-dev7-packaging`, `version-launch-ui`, `android-wol-ui`,
`gpu-resume-recovery`. São testes estáticos/substituídos; nenhum Electron,
instalador, jogo ou provedor real foi iniciado por eles.

Recibos desta execução: [Python](python-tests.json), [Node](node-tests.json).
Logs completos e checkpoint inicial ficam no diretório local
`.cache/modular-expansion-2026-10-26/`. Nenhum recibo histórico de outra etapa
foi sobrescrito. Alterações desta entrega: somente esta documentação, os dois
recibos sanitizados e o runner offline; sem novos endpoints ou comandos.

Não houve build, instalação, atualização, alteração de assinatura, credenciais,
grants, políticas, firewall, driver, Registro ou configurações do Windows.
Essa afirmação descreve as ações desta tarefa; o estado operacional desses
componentes não foi reconsultado.
