# Retomada GPU — correção isolada e regressões

26/10/2026. Branch `feature/ui-migration-preview`. Base: `0b62854`, preservando
`b52c918`, `36cfe6e` e o histórico anterior.

**Correção concluída no código de desenvolvimento, sem implantação.**
Nenhuma sessão física foi realizada, nenhuma versão foi empacotada e a dev.6
instalada continua com os mesmos arquivos. A aprovação dos testes abaixo não
equivale à homologação física da correção ou de um novo pacote.

## Causa e alteração

Em `monitoring-host.cjs`, a condição que concluía a retomada verificava a origem
GPU, cadência ativa e idade posterior à restauração, mas não exigia uma leitura
válida. Um resultado `error`, com valor nulo e timestamp recente, satisfazia essa
condição e retirava Atualizando. A hipótese foi reproduzida deterministicamente
nos mocks da etapa anterior; não era necessário carregar a DLL para confirmá-la.

A alteração em `apps/windows-ui/monitoring-host.cjs`:

- Conclui a recuperação somente com métrica GPU **dinâmica**, disponível,
  válida, não expirada, da cadência ativa de 2 s e produzida após a retomada.
  Capacidade estática de VRAM não comprova recuperação dinâmica.
- Leituras inválidas/rejeitadas não concluem a recuperação nem renovam seu prazo.
- Mesmo com recuperação parcial, outra métrica antiga ainda válida no cache não
  é promovida a leitura atual. Cada indicador anterior à retomada fica sem valor
  até sua substituição/expiração. Sensores não suportados continuam nulos.
- Usa **10 s como orçamento de espera da apresentação**, medidos pelo relógio
  monotônico já existente. Ao vencer, o estado é explicitamente `unavailable`,
  não sucesso de atualização. A recuperação posterior ainda requer amostra
  válida nova; erros repetidos não reiniciam esse orçamento.
- Após perda de IPC em atividade, a recuperação GPU também exige uma amostra
  nova. Recuperar o transporte não significa recuperar os sensores.

`monitoring-renderer.js` apresenta a indisponibilidade persistente no aviso e na
legenda GPU. Dashboard e widget usam os mesmos indicadores; cartões e textos
continuam sem valores quando indisponíveis. A identidade visual não mudou.

O campo aditivo `gpu_resume_state` descreve apenas o estado de apresentação no
envelope local: `disabled`, `idle`, `updating`, `ready` ou `unavailable`.
Não altera o contrato métrico v1 nem o protocolo Named Pipe. A flag `refreshing`
continua indicando a espera ativa; `false` com `gpu_resume_state=unavailable`
não pode ser interpretado como leitura bem-sucedida.

O orçamento de 10 s **não aumenta o frescor permitido**. Não há novo timer,
polling, thread ou processo para ele: o estado é calculado ao consultar/publicar
a visão do host pelo fluxo já existente. Uma interface oculta não executa trabalho
DOM adicional. Não há afirmação de precisão física de publicação sem uma sessão
autorizada; os limites do cálculo foram testados com relógios substitutos.

Continuam intactos: ingresso ADLX **1,5 s**, expiração ativa **3 s**, inativa
**11 s**, contrato v1, unidades, timestamps, validações estruturais/temporais,
rejeição de NaN/infinito/futuro e preservação de zero válido. Nenhum valor nulo
foi substituído por zero. Nenhuma mudança em CPU, RAM, armazenamento, provedor
ADLX, bridge C++, transporte, permissões ou executores.

## Regressão originalmente falha

[`tests/dev6-restore-diagnostic.cjs`](../../tests/dev6-restore-diagnostic.cjs)
mantém a asserção original, sem inverter expectativa nem introduzir skip/xfail:

| Caso | Antes | Agora |
| --- | --- | --- |
| Erro novo mantém Atualizando | Falha | **Passou** |
| Erro não expõe valores GPU numéricos | Passou | Passou |
| Próxima leitura válida recupera sem respawn | Passou | Passou |

Resultado atual: **3/3, exit code 0**. O relatório anterior e seu recibo versionado
continuam intactos como evidência histórica da falha; o recibo desta correção é
[restore-regression.json](evidence/restore-regression.json).

## Testes executados

| Suíte | Quantidade | Resultado |
| --- | --- | --- |
| Python básico/preservação/launchers | 133 | Aprovados |
| Python IPC protegido | 28 | Aprovados |
| Python provedor ADLX | 28 | Aprovados |
| Python sessão ADLX simulada | 10 | Aprovados |
| Python composição/ownership GPU | 26 | Aprovados |
| Python admissão temporal e contagens | 5 | Aprovados |
| Python integração com bridge nativa **mock** e diagnóstico | 59 | Aprovados |
| **Total Python** | **289** | **Zero falhas, erros e skips** |
| Node regressões existentes, plano e diagnóstico original | 461 | Aprovadas |
| Node retomada/recuperação novas | 65 | Aprovadas |
| **Total Node** | **526** | **Zero falhas e skips** |
| C++ `bridge-mock.exe --self-test` | **35** | **Aprovadas** |

O novo [`gpu-resume-recovery.cjs`](../../tests/gpu-resume-recovery.cjs) cobre erro
temporário, múltiplas rejeições, recuperação antes/depois da indisponibilidade,
provedor incompatível/ausente/sem permissão/em aquecimento, `age_null` como
resultado indisponível, dados antigos, futuros e não finitos, prazo de ingresso,
recuperação parcial sem promover dados antigos, IPC e reapresentação. Também usa
as fixtures reais dos testes de janela/DOM para modos, bandeja, redimensionamento,
fechamento cooperativo e preservação de CPU/RAM/discos.

Os testes Python exercitam a rejeição de `age_null` na fronteira ADLX e as
conversões reais do adaptador usando mensagens sintéticas, além de contrato,
cache, HMAC/HTTPS, allowlist e preservação WoL já existentes. Contagens de frames
são contagens da fixture, não telemetria física da instalação.

A suíte nativa iniciou 22 processos da fixture mock, todos encerrados normalmente,
sem residuais. O self-test C++ separado também terminou normalmente. A integridade
do executável foi conferida com o recibo e o hash da fonte C++ atual; a fixture
não contém o caminho da DLL ADLX. **Nenhuma DLL ADLX real foi carregada.**
Não houve compilação, instalação de ferramenta, empacotamento ou execução do
Electron. Os 35 checks C++ são asserções da fixture, não 35 sensores físicos.

Comandos individuais e hashes dos logs: [test-results.json](evidence/test-results.json).
Para repetir os novos casos, sem sensores/GUI:

```powershell
& 'C:/Program Files/nodejs/node.exe' 'tests/gpu-resume-recovery.cjs'
& 'C:/Program Files/nodejs/node.exe' 'tests/dev6-restore-diagnostic.cjs'
& '.venv/Scripts/python.exe' -B 'scripts/test-dev6-complementary-isolated.py'
```

## Homologação complementar

O [plano atualizado v2](../dev6-complementary-plan-2026-10-26/PLAN-v2.md) mantém
120 s desde o lançamento, verificações essenciais até aproximadamente 45 s e
Sair com reserva para conclusão/inspeção, sem força ou repetição automática.

A instalação atual **não contém esta correção**. Antes de uma validação física,
é preciso escolher explicitamente um alvo que a contenha: desenvolvimento isolado
autorizado ou artefato corrigido preparado/instalado com autorização específica.
Não se executará silenciosamente a instalação antiga para alegar validação da
mudança de fonte. Não se preparou nem instalou novo pacote nesta entrega.

Pendências TLS, Crashpad, encerramento gracioso do agente e observação OneSettings
continuam separadas. Nenhuma correção dessas áreas foi incluída. Contagens físicas
exatas de frames permanecem não disponíveis sem observabilidade adicional aprovada.

## Preservação e estado final

Conferência de 26/10 às **10:44 (UTC−3)**:

- Dev.6 instalada e fechada. Instalação: 117 arquivos; perfil: **77**, todos
  byte a byte iguais ao início. Backups dev.3/4/5/6 também iguais, sem substituição.
- Mesmos supervisor **5024** e worker **18304**, identidade completa, cadeia de
  processos e criação verificadas, incluindo redirectors 19996/20352.
- Listener único LAN **8776** no worker esperado; TLS 1.3, certificado/hostname/pin
  conferidos antes do envio da credencial, status/apps autenticados HTTP 200.
- **Zero grants e zero comandos pendentes**; integridade SQLite, identidades
  cifradas, esquema e revogações preservados. Nenhuma identidade nova.
- 86 arquivos operacionais protegidos inalterados. Dos 97 arquivos de fonte
  preparados, somente host/renderer acima mudaram, conforme autorização;
  95 ficaram iguais. Android e executores preservados.
- Zero Electron, coletor, intermediário, ponte ADLX ou instalador residual.
- HKCU Run/RunOnce, Inicializar, serviços e firewall sem diferenças. OneSettings
  RefreshCache teve novamente alteração de hash, sem ator identificado; permanece
  inconclusiva. Não houve escrita de configuração do Windows nesta tarefa.
- Nenhum Steam, CS2, WoL, ação de energia, sensor real ou aplicativo instalado
  foi executado. Não houve atualização/reinício/sinalização do agente.

Os GETs autenticados foram consultas locais de leitura com a identidade existente,
usada somente em memória. Não houve nova validação física no Samsung. Nonces e
last-seen podem evoluir normalmente no banco; não se exige igualdade byte a byte
de um banco operacional que atende consultas. [Recibo](evidence/preservation-final.json).

## Commits e reversão

Implementação e testes: **`3dc783c10f9ec19c98b7d9fa2576cc4c3a1d2ffc`**.
O commit documental seguinte registra esta entrega e o plano v2; hash informado
na resposta. Nenhum checkpoint foi reescrito.

Para reverter a correção de fonte, em branch de revisão, usar
`git revert 3dc783c10f9ec19c98b7d9fa2576cc4c3a1d2ffc` e executar as regressões
pertinentes. Isso recoloca o defeito conhecido; a expectativa original voltará a
falhar. Não inverter seu teste para mascará-lo. Se for necessário reverter também
a documentação, reverter o commit documental antes do commit de código.

Nenhum rollback, desinstalação, restauração de perfil ou parada do agente é
necessário para reverter este trabalho. Backups e pacotes anteriores foram
preservados. Arquivos privados de comparação/logs ficam somente em
`.cache/validation/gpu-resume-fix-2026-10-26/`, fora do Git; os recibos versionados
são sanitizados e não incluem segredos.

Preferência de trabalho recebida: operações rotineiras de desenvolvimento dentro
da tarefa autorizada seguem com autonomia. Permissões efetivas do ambiente e os
limites explícitos para produção, testes físicos, segurança, credenciais,
instalações de terceiros e ações destrutivas continuam valendo.
