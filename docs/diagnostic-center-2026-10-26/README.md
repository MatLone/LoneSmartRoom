# Central de Diagnóstico — integração visual isolada

**Implementada no Electron existente, somente com dados simulados.** A Central
fica dentro de **Monitoramento PC**; Controles, Monitoramento PC e Gamer Launcher
continuam sendo as três abas. Não foi instalada uma nova versão, iniciado um
leitor operacional ou executada uma consulta HTTPS ao agente nesta tarefa.

Implementação: **`a7310a4`**; regressões adicionais do renderer: **`8fb005c`**, na branch `feature/ui-migration-preview`, a partir do
checkpoint preservado `2aa5642`. Versão de desenvolvimento do código continua
2.0.0-dev.7; não há novo NSIS, portátil ou APK.

## Revisão visual

[Abrir a galeria das 16 capturas](review.html). São capturas do **Electron de
desenvolvimento real**, carregando main, preload e renderer existentes, com
perfis próprios e relatórios de demonstração. Não são screenshots da instalação
de produção nem apenas renderizações de um HTML independente.

- [Dashboard](preview-electron/100/02-central-dashboard.png)
- [Detalhes HTTPS](preview-electron/100/03-detalhes-https.png)
- [Segurança e pendências](preview-electron/100/02b-seguranca-pendencias.png)
- [Widget](preview-electron/100/04-widget.png)
- [Inatividade normal no widget](preview-electron/100/05-widget-inativo.png)
- [Widget em 360 px](preview-electron/100/07-widget-360.png)
- [Escala 125%](preview-electron/125/02-central-dashboard.png)
- [Escala 150%](preview-electron/150/02-central-dashboard.png)

Identidade preto/grafite e vermelho **#FF153F**, logo oficial com apenas o E
vermelho e demais assets preservados byte a byte. A seção tem sete cartões,
seis apresentações de saúde, horário da verificação simulada, resumo e detalhes
técnicos expansíveis. Retorno ao monitoramento devolve o foco ao botão de origem.
O widget conserva navegação inferior e rolagem; não há transbordamento horizontal
detectado nos testes. Conteúdo vertical continua acessível pela rolagem normal.

Há indicação **SIMULAÇÃO** no painel, **SIMULADO** em cada cartão e relógio de
fixture explicitamente fixo. Não são exibidas temperaturas, percentuais ou outras
medições inventadas como se fossem leituras reais. Os indicadores de hardware
do monitoramento existente permanecem indisponíveis na revisão sem coletor.

## Cartões e significado dos estados

| Cartão | Evidência representada na demonstração |
|---|---|
| Agente HTTPS | Status autenticado e identidade do listener, tratados separadamente nos detalhes |
| Monitoramento PC | Coletor CPU/GPU/RAM e disponibilidade |
| Named Pipe | Comunicação local e validação do peer/contrato |
| Ponte AMD ADLX | Execução e disponibilidade do último quadro |
| Sensores | Validade, idade e frescor dos recibos de métricas |
| Inicialização automática | Correlação de login, despacho e bootstrap |
| Segurança | Verificações parciais disponíveis, sem certificar a segurança global |

Estados: **Saudável, Inativo normalmente, Indisponível, Desatualizado, Falha,
Não verificado**. Inatividade é um motivo explícito no contrato existente,
projetado como rótulo próprio. Erro confirmado do provedor indica falha na
verificação e não comprova defeito do componente. Ausência de evidência permanece
Não verificado. Uma conexão ausente não confirma computador desligado.

O cartão Segurança permanece **Não verificado** mesmo com subconjuntos saudáveis
na simulação, pois existem investigações abertas. As quatro pendências ficam
sempre visíveis: **TLS 10054**, inicialização automática inconclusiva, encerramento
gracioso do agente não validado operacionalmente e homologação física parcial da
Windows dev.7. Nenhuma foi corrigida ou encerrada por esta integração.

## Arquitetura e limites

```text
Contrato/reducer Python v1 (fixtures puras)
  → bundle de demonstração gerado e verificado
  → diagnostics-host.cjs no processo principal
  → IPC diagnostics:snapshot, remetente/frame exatos
  → preload getDiagnostics(cenário enumerado)
  → validação e projeção no renderer
  → sete cartões e detalhes sanitizados
```

- `scripts/prepare-diagnostic-fixtures.py`: gera 13 cenários usando o reducer e
  adaptadores puros já aprovados. `--check` detecta divergência sem escrever.
  Não importa/inicializa leitores Windows, sensores, HTTPS ou Named Pipes.
- `diagnostics-contract.js` deriva das enumerações/mensagens do contrato Python.
  `diagnostics-fixtures.json` contém apenas relatórios diagnósticos simulados;
  não contém valores de telemetria, credenciais ou logs privados.
- `diagnostics-host.cjs`: fonte fixa local, sem módulos de rede, execução de
  processos ou ponte nativa. Bundle máximo **128 KiB**, relatório **16 KiB**,
  envelope **18 KiB**, requisição lógica **96 bytes**. Um pedido em andamento,
  intervalo mínimo **500 ms** e espera limitada a **1 s** para o provedor.
- A rota principal exige remetente e frame principal da janela original,
  cardinalidade exata e pedido `{v:1, scenario:enum}`. Não aceita caminhos,
  endpoints, comandos, funções ou argumentos operacionais.
- Preload acrescenta somente `getDiagnostics`. Node permanece desabilitado no
  renderer; `contextIsolation`, sandbox, webSecurity, bloqueio de navegação e CSP
  com `connect-src 'none'` permanecem habilitados. O arquivo JSON de fixtures não
  faz parte da allowlist de recursos acessíveis ao renderer.
- Renderer revalida versão, origem simulada, tamanho, campos, datas, tipos,
  validade e TTL. Estado saudável exige código/detalhe compatível; evidência
  futura, antiga, não finita, ambígua ou de origem real não passa como saudável.
  Conteúdo variável é inserido com `textContent`, sem HTML de provedor.
- Não há polling periódico adicional. As consultas ocorrem ao abrir a Central,
  trocar o cenário ou solicitar atualização. Ao falhar/rejeitar uma mensagem,
  cartões anteriores não permanecem apresentados como estado atual.

O modo de demonstração exige **aplicação não empacotada**, revisão de
desenvolvimento e `--lone-diagnostics-preview`. Fora disso, a consulta retorna
desabilitada/sem evidência. Os cenários não são silenciosamente ativados na
produção. Mesmo com flags de desenvolvimento de monitoramento presentes, o modo
diagnóstico impede criar o host de sensores nessa revisão.

Perfis de revisão ficam exclusivamente em
`.cache/windows-diagnostics-review/<id>/...`; produção não é importada. O
empacotamento existente recebeu apenas a lista de recursos da nova seção para
uma versão futura, sem gerar artefatos ou alterar identificador/versão.

## Testes e evidências

- **160 testes Python** aprovados, sem falhas, erros ou skips: contrato/reducer,
  leitores substituídos, apresentação e geração determinística das fixtures.
- **625 asserções Node contabilizadas**, em 11 suítes aprovadas; uma dessas
  suítes legadas não declara contagem numérica e é contabilizada só como aprovada.
  A Central tem **254 asserções específicas** dentro desse total.
- **101 verificações nas revisões Electron finais**, com capturas reais em
  100%, 125% e 150%, widget e largura de 360 px. As escalas são opções por processo;
  não houve alteração do DPI ou das configurações do Windows.
- Cobertura: online/offline, identidade de listener incorreta, autenticação
  inválida, pipe ausente, inatividade normal, sensor indisponível, expiração,
  recuperação após falha, login inconclusivo, erros/timeout do provedor,
  pedidos/dados inválidos, limites de tamanho/frequência, cancelamento da
  apresentação, validação do remetente/frame e ausência de APIs genéricas.
- Regressões de janela, três abas, menus/bandeja, widget, persistência, ciclo de
  vida, CPU/GPU, IPC, distribuição estática, WoL e comandos com executores
  substituídos aprovadas. Nenhum jogo, pacote WoL ou executável empacotado rodou.
- As revisões nativas confirmam um único window por processo, host de
  monitoramento ausente, zero tentativas de processos externos do aplicativo,
  zero requisições HTTP completadas, zero erros/crashes do renderer e saída normal.

Recibos: [Python](python-tests.json), [Node](node-tests.json),
[resumo](validation-summary.json), [capturas e SHA-256](screenshots.json).

### Ocorrências preservadas

A primeira tentativa de captura não passou na verificação de visibilidade porque
o helper iniciou com `SW_HIDE`; ela fechou normalmente. O script de revisão passou
a exibir explicitamente a própria janela isolada. Não foi uma correção do
aplicativo instalado; a tentativa foi arquivada localmente.

O stderr das revisões registrou um aviso do Chromium:
`GPU state invalid after WaitForGetOffsetInRange`. Não houve evento de crash do
renderer, falha visual identificada nas imagens ou processo residual. Não foi
atribuída causa à AMD/ADLX e não houve alteração de driver, flags gráficas ou
crash reporting para ocultar o aviso. Não ocorreram mensagens Crashpad `0xE9`
nas três revisões finais. O aviso permanece uma observação separada, não resolvida.

As duas falhas iniciais de regressão Node foram expectativas antigas da lista
de APIs e um mock que ainda não resolvia o novo módulo. As allowlists dos testes
foram ampliadas estritamente para a única consulta de diagnóstico, mantendo
rejeição de canais/argumentos arbitrários; todas as regressões finais passaram.

## Preservação e estado final

**1.312 arquivos imutáveis e quatro arquivos de runtime preservados**, incluindo
instalação Windows dev.7, perfil de produção, backups, recuperação, agente,
Android e assets oficiais Windows. O conjunto exclui os fontes Electron
explicitamente autorizados para edição nesta tarefa, por isso a contagem difere
do inventário anterior de 1.338. Não houve exclusão de arquivos/backups.

Banco `quick_check` OK, hashes lógicos de identidade/permissões iguais e **zero
grants**. APK Android dev.9 permanece com SHA-256
`92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2`.

Metadados finais confirmam a cadeia original do agente com imagem e criação
compatíveis e listener único 8776 do worker esperado. Não houve novo GET
autenticado nesta tarefa: a Central não consulta o agente e o status de
autenticação real não foi revalidado pela demonstração.

**Zero processos Electron de desenvolvimento ou monitoramento residuais**.
Todas as prévias encerraram normalmente, destruíram sua bandeja e fecharam seu
host de fixtures. Nenhum APK/NSIS foi instalado; nenhuma configuração, serviço,
tarefa, HKCU Run, firewall, certificado, credencial ou permissão foi alterada.
Android e Windows instalados permanecem preservados.

Ver [preservação posterior](preservation-after.json) e
[processos/listener](process-preservation.json).

## Limitações e próxima etapa, mediante autorização

1. Esta é uma integração de apresentação **simulada**, não homologação de saúde
   do computador. Relatórios reais são rejeitados deliberadamente neste modo.
2. Limites de mensagens são lógicos, aplicados após a desserialização do IPC;
   não são uma garantia de limite de memória do transporte Electron. Código
   malicioso sob a mesma conta não é isolado por uma ACL por usuário.
3. Timeout do host limita a espera da UI; não preempta JavaScript síncrono nem
   cancela um provedor externo arbitrário. O provedor atual é somente memória
   limitada. Um futuro leitor real exigirá deadline/cancelamento cooperativos
   próprios e isolamento de execução; não reutilizar essa espera como tal garantia.
4. Bandeja e persistência continuam cobertas por mocks; não se realizou outra
   homologação física da instalação dev.7 nem interação física com hardware.
5. Não se ativaram leitores reais para Named Pipes, sensores ou startup. As
   limitações da validação passiva anterior permanecem explícitas.

Plano recomendado: após autorização, desenvolver um adaptador de recibos reais
em perfil isolado, começando por projeções somente leitura de evidências já
validadas. Para IPC e sensores, reutilizar o `monitoringHost` autorizado do
processo principal e seu cache; não ampliar a ACL nem conectar outro cliente ao
pipe que valida o intermediário original. Preservar origem, timestamp original,
null, zero válido, ingressos ADLX de 1,5 s e frescor GPU de 3/11 s.

Esse adaptador deverá habilitar origem real por decisão explícita, com novos
testes, e manter o modo de demonstração separado. Não basta trocar uma flag para
apresentar fixtures como dados reais. Não iniciar coletores para obter cartões
saudáveis. Não promover ausência de prova de login a falha de inicialização.

Para HTTPS, não transformar o helper de auditoria que usa identidade existente
em cliente operacional do Electron. Uma futura integração autenticada desktop
deve ter identidade independente e depender da correção/validação TLS relevante,
com aprovação específica. Nenhuma credencial Samsung será copiada para esse fim.
Não haverá reparo automático nesta próxima proposta.

## Reprodução e reversão

Testes puros:

```powershell
.venv/Scripts/python.exe -B scripts/prepare-diagnostic-fixtures.py --check
.venv/Scripts/python.exe -B scripts/test-diagnostic-center.py
node scripts/test-diagnostic-center.cjs
```

Prévia opcional, apenas em desenvolvimento, sem instalar e com perfil próprio:

```powershell
apps/windows-ui/node_modules/electron/dist/electron.exe apps/windows-ui --lone-development-review --lone-diagnostics-preview
```

O código dos testes nativos fica em `tests/electron-diagnostic-*.cjs` e não é
incluído na lista de empacotamento. Capturas preservadas aqui são das execuções
instrumentadas; o comando de prévia simples não grava capturas automaticamente.

Não há instalação a reverter. Em branch de revisão, reverter primeiro
`8fb005c` (testes dependentes) e depois `a7310a4` (implementação), mantendo o
relatório/evidências. Essa ordem evita conflito ao remover o teste criado pela
implementação e ampliado posteriormente. Não executar
rollback, reinstalação ou restauração do perfil/banco. Todos os checkpoints e
backups anteriores permanecem preservados. A integração real e qualquer
implantação exigem autorização separada.
