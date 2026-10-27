# Adaptadores de evidências — preparação isolada

Data: 2026-10-26. Base solicitada: `7c4ddd1`. Implementação: `1aa7d3a`.

## Resultado e alcance

Foram preparadas cinco interfaces de evidências: agente HTTPS, monitoramento,
IPC, inicialização e segurança. O caminho novo aceita **somente simulação**.
Não houve ativação de leitores reais, consulta operacional, execução nativa do
Electron, coleta de sensores, instalação ou alteração do agente.

Os adaptadores são funções de validação e classificação. Não verificam por si
mesmos um processo Windows, uma ACL ou um certificado: nesta etapa recebem
afirmações de provedores substitutos. Portanto, os estados dos exemplos anexos
não descrevem a condição atual do computador.

O contrato de relatório v1 e seus oito componentes foram preservados. A auditoria
de segurança é uma estrutura separada e versionada, incluída opcionalmente no
envelope já existente do main. O preload e os canais existentes não ganharam
novos métodos. O provedor padrão continua lendo o catálogo de simulações anterior;
o novo hub não está conectado a leitores Windows nem ao agente.

Veja [arquitetura e contrato](architecture.md) e
[plano de validação e reversão](validation-plan.md).

## Evidências de testes

| Verificação | Resultado |
|---|---|
| Python, incluindo regressões compartilhadas | 378 testes, zero falhas, erros ou testes ignorados |
| Novos testes Python de adaptadores | 43, incluídos nos 378 |
| Node, main/modelo, janela, bandeja, monitoramento e preservação | 891 asserções contadas em 12 suítes aprovadas; uma dessas suítes não informa contagem numérica |
| Cenários de evidência | 14 cenários determinísticos, identificados como simulação |
| Sintaxe JS e atualização das fixtures | Aprovadas |
| Arquivos protegidos comparados antes/depois | 1.317, nenhuma diferença |
| Sessões físicas / consultas operacionais | 0 / 0 |

As regressões abrangem autorização, contratos, IPC, cache, CPU/RAM/discos com
substitutos, instrumentação ADLX simulada, WoL, launchers Steam/CS2 simulados,
janela, widget, bandeja e políticas de distribuição. Não são uma nova homologação
física nem uma compilação Android ou Windows.

Os testes cobrem online/offline; autenticação aceita/rejeitada; processo correto
com listener divergente; IPC presente/ausente; inatividade normal; sensor sem
suporte; amostras antigas; inicialização inconclusiva; falha temporária,
recuperação e falha persistente; timestamps originais; integridade dos cartões;
reconexão com nova geração; limites e rejeição de campos privados. Os testes de
ponte/coletores não carregaram a DLL ADLX real.

### Falha inicial registrada

A primeira execução Python tinha 376 testes e um erro na regra de preservação:
o hash esperado para o preload antecedia a Central já aprovada. O arquivo atual
foi comparado diretamente ao blob de `7c4ddd1`: era idêntico. Corrigiu-se somente
o hash exato da regra para
`c20b427fea83d32c456cabacdc894fa5286df2647dbf5c693ea005b2011d3046`.
O preload não foi editado e a validação não foi dispensada. Os registros iniciais
permanecem no cache local; o resumo público registra a ocorrência. Após dois
testes adicionais e a correção dessa referência, os 378 testes passaram.

### Reprodução somente simulada

Na raiz do repositório, usando os runtimes já existentes:

```powershell
& .venv/Scripts/python.exe -B scripts/test-diagnostic-evidence.py
& 'C:/Program Files/nodejs/node.exe' scripts/test-diagnostic-evidence.cjs
& .venv/Scripts/python.exe -B scripts/prepare-diagnostic-adapter-fixtures.py --check
```

Esses comandos não ativam os leitores reais. O runner Python instala uma barreira
de auditoria contra rede, Registro, novos carregamentos nativos e subprocessos
depois do bootstrap das bibliotecas padrão. O runner Node executa testes com
substitutos; não inicia o binário Electron.

Os recibos `python-tests.json` e `node-tests.json` contêm hashes dos fontes
testados. Os exemplos `*-SIMULATED.json` representam estados do contrato, não
capturas atuais do sistema. Não foram produzidas novas capturas da instalação.

## Preservação e estado final verificável

O manifesto privado de comparação permaneceu fora do Git e dos relatórios.
Foram comparados hashes de instalações, perfil, arquivos de recuperação, backups,
runtime protegido e APK, sem abrir o banco operacional ou descriptografar dados.
As comparações estáticas antes/depois passaram para os 1.317 arquivos abrangidos.

O APK Android dev.9 preservado mantém SHA-256
`92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2`.
Não houve mudança no Android instalado, Windows dev.7 instalado ou seus assets
de produção. Não foram instaladas dependências ou criados grants.

**O estado operacional atual do agente e a contagem atual de grants não foram
consultados**, conforme a proibição desta etapa. O agente não foi iniciado,
interrompido, sinalizado ou atualizado. A preservação estática não substitui uma
prova atual de autenticação, listener ou disponibilidade. Não se afirma zero
grants recém-verificado nem serviço saudável sem essa evidência.

Não houve operação sobre HKCU Run, firewall, serviços, tarefas, certificados,
credenciais ou configurações. Não foram executados Steam, CS2, WoL ou comandos
de energia.

## Pendências preservadas

1. Reset TLS 10054: permanece aberto; sem requisições malformadas ou correção.
2. Inicialização automática recorrente: permanece sem causa conclusiva; HTTPS
   saudável não demonstraria despacho de HKCU Run.
3. Encerramento gracioso do agente: ainda sem validação operacional.
4. Crashpad 0xE9: mensagens ainda sem conclusão causal.
5. Windows dev.7: homologação física permanece parcial.

Todas aparecem como pendências conhecidas do modelo. Nenhum resultado de mocks
resolve essas observações. A quinta pendência foi incluída no catálogo visual
sem nova sessão de interface; prévias antigas não são evidência dessa alteração.

## Git

O commit `1aa7d3a` contém a implementação e os testes. A documentação é entregue
em commit posterior separado. Os checkpoints `7c4ddd1`, `a7310a4`, `8fb005c`,
`90c89b6`, `2aa5642`, `75d00eb` e `e6f2897` continuam ancestrais.

A branch corrente é `feature/modular-expansion-plan`. Durante o trabalho houve
o commit documental independente `fe2e004`, de outro planejamento, que foi
preservado como ancestral. Esta tarefa não alternou nem reescreveu a branch e
não modificou aquela documentação. A atualização exata da referência de preload
descrita acima explica por que o resultado posterior difere do diagnóstico
histórico registrado naquele planejamento.
