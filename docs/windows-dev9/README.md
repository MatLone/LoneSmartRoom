# Windows 2.0.0-dev.9 — candidata consolidada

Base `da02efb`, branch `feature/windows-control-center`. **Não instalada nem
executada como pacote.** A instalação operacional continua dev.8, fechada.
Android congelado. Esta candidata integra melhorias concretas; não significa que
todas as integrações externas ou a inicialização automática estejam homologadas.

## Entrega implementada

- **Retomada GPU:** o controller invalida as leituras antes de mostrar a janela,
  inclusive quando outro painel manteve o coletor ativo. O renderer limpa a
  superfície antiga na mudança de visibilidade. Resposta pendente não deixa
  Atualizando indefinidamente: indisponibilidade explícita após 10 s.
- Mantidos ingresso ADLX 1,5 s, expiração ativa 3 s/inativa 11 s, null distinto
  de zero e descarte do primeiro frame inválido. A comprovação física da retomada
  continua pendente; esta rodada usou substitutos.
- **Saída e duração:** tray Sair e modo de validação usam `controller.quit`, com
  espera cooperativa dos componentes próprios. O modo explícito
  `--lone-validation-session` solicita saída aos 45 s, contado desde o início do
  main, e registra falha se exceder 120 s. Uso comum não recebe esse temporizador.
  Nunca termina processos à força. A sessão real de desenvolvimento terminou em
  **45,028 s**, pedido de saída em **45,008 s**, sem interação no chat.
- **Inicialização do agente:** novo ponto de entrada opt-in
  `agent/development/reliable_bootstrap.py`, reutilizando o launcher/mutex/logs
  protegidos e o worker cooperativo existentes. Python absoluto, `-I -B`, cwd
  fixo, sem elevação, shell ou registro automático. Lease separado do supervisor;
  lease do worker continua compartilhado com o mecanismo existente.
  Uma tentativa por padrão. Recuperação adicional somente por configuração
  explícita do host, limitada a três, após saída observada e nova verificação
  de ausência de legado/listener. Não reinicia um filho cujo estado seja desconhecido.
- **Inventário:** falhas do helper agora distinguem timeout, ausência do helper,
  limite de resposta e erro de execução, sem texto livre da exceção. Isso melhora
  o diagnóstico; não demonstra que a falha intermitente da dev.8 tenha sido corrigida.
- **Gamer Launcher:** acesso direto à biblioteca/perfis/sessões; provedor de
  acompanhamento de CSV PresentMon externo, integrado ao main, preload, cartões
  numéricos, gráfico limitado de frametime, arquivo de sessões e overlay.
  Não instala ou inicia PresentMon, jogos, ETW, serviços ou hooks.
- **Desempenho:** evita a segunda atualização de DOM no mesmo intervalo em que
  uma mensagem de métricas já atualizou a interface. Fonte FPS só tem timer quando
  selecionada; consultas da tela param ao sair da área. Não afirmamos redução de
  consumo frente à dev.8 sem comparação equivalente.

### Limites da inicialização automática

O HKCU Run operacional **não foi alterado** e ainda aponta para o caminho direto
antigo. A nova entrada é código funcional preparado, não ativado. Não é possível
afirmar que o despacho após login foi corrigido sem implantar o comando aprovado
e observar um login real. Ausência de log também pode ocorrer antes da criação do
logger; não equivale, isoladamente, a prova de falha de despacho do Windows.
O manifesto em `evidence/agent-candidate-manifest.json` fixa os fontes necessários.
Nenhum deles, nem certificados ou credenciais, é instalado pelo NSIS do Electron.
O leitor reconhece a nova cadeia somente com opt-in interno `candidate=True`,
caminhos completos e `-I -B` fixos. O modo legado continua padrão. Nenhum leitor foi ativado.

### Fonte FPS e metodologia

O usuário escolhe o CSV por diálogo nativo; o renderer não fornece caminhos ou
argumentos. Só contam linhas completas acrescentadas **depois** da seleção.
Arquivo limitado a 2 MiB, 32 streams, polling de 1 s, sem symlinks/hardlinks;
disponibilidade expira após 3 s sem relatório novo. A tela consulta a cada 2 s
enquanto está visível. Rotação/truncamento volta ao aquecimento, sem reutilizar
frames anteriores. Exceder o limite deixa a fonte indisponível.

Streams de aplicativo/PID/swapchain não são misturados. O overlay só apresenta
FPS quando há um stream inequívoco. Resumos são limitados a 20 sessões/1 MiB.
Horário de observação do arquivo e importação **não são o horário original dos
frames nem prova de jogo em execução**; `live_game_verified` permanece false.

- FPS médio = quantidade de frames × 1.000 / soma dos frametimes em ms.
- Frametime médio = soma / quantidade.
- 1% Low = 1.000 / média dos `ceil(quantidade × 0,01)` frametimes mais lentos;
  indisponível com menos de 100 frames.
- Gráfico tem até 120 pontos amostrados; não reconstrói timestamps absolutos.

Somente `MsBetweenPresents`/`msBetweenPresents` é aceito. Não reinterpretamos
outros campos como substitutos. O relatório derivado também passa pelo validador
canônico das sessões: overflow numérico não pode ser publicado como leitura válida. São frames apresentados, não FPS exibidos. A
[documentação oficial PresentMon](https://github.com/GameTechDev/PresentMon/blob/main/README-ConsoleApplication.md)
descreve saída CSV e a unidade em milissegundos. A captura ETW externa, permissões
e compatibilidade operacional da ferramenta ainda precisam de revisão própria.
Não houve instalação, injeção, acesso ao VAC ou execução de Steam/CS2.

## Instalador: preservação de runtime

O problema do `debug.log` motivou duas proteções:

1. Antes de chamar o desinstalador antigo, o NSIS prepara cópia verificada dos
   arquivos que não pertencem aos inventários dos pacotes dev.8/dev.9. Isso cobre
   a atualização a partir do desinstalador antigo, que removia a pasta inteira.
2. O novo desinstalador remove somente caminhos explicitamente pertencentes ao
   pacote; não utiliza remoção recursiva da instalação.

O helper fixo PowerShell é incorporado ao NSIS. Não contorna política de execução;
qualquer impedimento falha antes de remover a versão antiga. Cópias ficam em
`%LOCALAPPDATA%\LoneSmartRoom-RuntimePreservation\<id>`, com ACL somente da conta,
manifesto SHA-256 e retenção da cópia após a restauração. Não sobrescreve arquivos
divergentes. Limites: 256 arquivos desconhecidos/64 MiB; reparse points e manifestos
com caminhos inseguros são recusados. Instalação é interrompida se a preservação
falhar. Perfil Electron e banco do agente não entram nesse mecanismo.

**Validado com arquivos descartáveis, ACL nativa e compilação/inspeção NSIS;
atualização real ainda não executada.** Esse teste não é uma homologação física
do assistente. A segurança por conta não isola processos maliciosos do mesmo usuário.

## Matriz final por capacidade

**1 — Funcional e validado:** fonte real apropriada, no escopo indicado.
**2 — Implementado em desenvolvimento:** código funcional, homologação operacional pendente.
**3 — Preparado:** depende de integração externa/ativação aprovada.
**4 — Não implementado:** função efetivamente ausente.

| Capacidade | Classe | Evidência / dependência específica |
|---|---:|---|
| Navegação três abas + 12 áreas, layout e janelas | 1 | Electron real de desenvolvimento em 100/125/150%; não prova todos os backends |
| CPU/RAM/discos/GPU: coleta normal | 1 | Fonte real comprovada na dev.8; núcleo dos provedores preservado; nenhuma nova coleta física nesta tarefa |
| Retomada GPU e barreira antes de mostrar | 2 | Testes com relógio/streams/DOM substitutos; falta confirmar no hardware instalado |
| Widget, restauração, instância única e menu Sair | 2 | Regressões do controller e janelas reais de desenvolvimento; menu físico Windows ainda pendente |
| Saída temporizada independente do chat | 1 | Electron de desenvolvimento encerrou pelo main aos 45,028 s; variante empacotada não executada |
| Bootstrap/supervisor/encerramento do agente | 2 | 110 testes com mocks e 37 fixtures isolados; nenhum agente operacional iniciado |
| Inicialização automática após login | 3 | Entrada nova pronta; alterar Run e observar login exige autorização; causa recorrente ainda inconclusiva |
| Histórico/gráficos/exportação CSV de hardware | 1 | CSV real e histórico já comprovados na dev.8; código reutilizado |
| Central de Diagnóstico: cache de sensores/IPC | 1 | Evidência local já validada; sem novas sondas ou alegação de autenticação do agente |
| Diagnóstico operacional de HTTPS/login | 3 | Leitores/fundação existentes; ativação não executada nesta candidata |
| Inventário de aplicativos | 1 | Fonte real do Registro validada na dev.8; sem instalar/atualizar programas |
| Inventário CPU/RAM/drivers/processos/serviços | 2 | Helpers tipados e testes; falha intermitente CPU ainda requer evidência de causa |
| Prévia de temporários/cache | 2 | Correções de raiz ausente e limite global incluídas; testes de metadados, sem exclusão |
| Exclusão/quarentena de temporários pessoais/Windows | 4 | Nenhum executor adicionado; somente prévia |
| Planos de reparo e otimização | 3 | Privilégios/efeitos/reversão descritos; execução deliberadamente ausente |
| Perfis locais, listas de aplicativos e importação/exportação | 2 | Persistência/validação/round-trip em armazenamento isolado; não aplica tuning Windows |
| Otimização efetiva de Registro/serviços/energia/debloat | 4 | Fora do escopo operacional autorizado |
| Mouse/teclado em foco | 2 | Captura de eventos do navegador e estatísticas; não mede latência/polling físico |
| Microfone local por consentimento | 2 | Fluxo e cancelamento testados; não ativado fisicamente nesta tarefa |
| Bateria, DPI, firmware e latência calibrada | 4 | Provedores específicos ausentes |
| Padrões de tela/consulta de monitores | 2 | Interface real de desenvolvimento; calibração e ensaio no monitor físico pendentes |
| Ping/DNS sob demanda e cálculos RTT/jitter/perda | 2 | API fixa e validação com testes; nenhum destino operacional sondado nesta rodada |
| Speedtest e alterações de rede | 4 | Não implementados |
| Biblioteca manual/manifestos Steam/perfis por jogo | 2 | Código integrado e persistência local; detecção não inicia Steam; ensaio instalado pendente |
| Importação PresentMon/FPS/frametime/1% Low | 2 | Parser, arquivo e fluxo arquivo→main→preload→UI comprovados com CSV explicitamente simulado |
| Acompanhamento CSV externo + histórico e overlay | 2 | Integrado e testado; limite 2 MiB, sem comprovação de jogo real |
| Iniciar captura ETW/FPS automaticamente | 4 | PresentMon não instalado/iniciado; permissões/seleção de processo requerem validação própria |
| Monitoramento CPU/GPU durante jogos | 2 | Compartilha o coletor existente; nenhum jogo ou benchmark foi executado |
| Overlay e Touch Panel configuráveis em tamanho/posição | 2 | Janelas Electron reais e persistência; touchscreen/tela cheia exclusiva pendentes |
| Dispositivos/cenas e prévias RGB | 2 | Configuração local e prévia tipada; nenhum equipamento acionado |
| Home Assistant/OpenRGB/SignalRGB/IR/controle de ventoinhas | 3 | Catálogo/contratos; faltam serviço, hardware, credenciais e provedor homologado |
| NEX local por regras e navegação | 2 | Main/preload/renderer integrados e testados; sem comandos arbitrários ou reparos |
| IA externa, STT/TTS e automações físicas | 4 | Não implementados |
| Auditoria e backup/restauração das configurações do LSR | 2 | Contrato v1, persistência atômica e importação validada; sem segredos |
| Backup/restauração completa do Windows/pontos de restauração | 4 | Não implementados nem simulados como funcionais |
| Novo instalador preservando arquivos extras | 2 | Helper testado em fixture + fonte incorporada conferida; falta atualização real autorizada |

## Testes e desempenho

- Node: **21 suítes / 3.284 verificações**.
- Python monitoramento: **268 testes**, 22 processos mock, zero resíduos.
- Bootstrap/política/launcher/leitores: **110 testes**, processos reais/rede bloqueados.
- Encerramento cooperativo: **37 testes** com workers substitutos, eventos
  exclusivos de teste e portas loopback efêmeras; 8776/credenciais reais proibidos.
- C++: **35 verificações**, executável mock identificado por hash; ADLX real não carregado.
- Runtime: **2.323 verificações**, 39 arquivos e 527 fontes stdlib; nenhum executável
  empacotado executado. Inspeção dos pacotes: **482 verificações**.
- Preservação de runtime: **8 verificações** em fixtures, incluindo conflito,
  ACL, hash, caminho inseguro e limite excedido. Nenhum instalador executado.
- Electron real de desenvolvimento: **93 verificações / 48 capturas**, três escalas,
  sem erros de renderer ou acesso externo; hashes dos fontes finais registrados.

O teste temporizado final amostrou 44 intervalos do próprio Electron:

| Fase | Soma média `percentCPUUsage` da API | RSS médio somado | Maior RSS somado |
|---|---:|---:|---:|
| Dashboard | 0,2962 | 334,60 MiB | 342,53 MiB |
| Widget | 0,2727 | 314,03 MiB | 321,62 MiB |
| Bandeja | 0,2113 | 303,46 MiB | 303,47 MiB |
| Restaurado | 0,3485 | 306,06 MiB | 310,86 MiB |
| Geral | 0,3014 | 311,58 MiB | 342,53 MiB |

A API informa médias por intervalo, primeira chamada descartada; ver
[CPUUsage do Electron](https://www.electronjs.org/docs/latest/api/structures/cpu-usage).
RSS pode somar páginas compartilhadas. Compositor de software, perfil novo, sem
coletores ou jogos. **Não comparar esses 311,58 MiB com os ~470 MiB conjuntos da
dev.8**, nem declarar ganho de desempenho ou ausência de vazamento de longa duração.
O runner permite repetir exatamente o cenário: `scripts/test-development-deadline.ps1`.

Falhas durante o desenvolvimento não foram ocultadas: sandbox bloqueou sockets/
eventos/compilador; 37 testes passaram depois no contexto normal sem elevação.
A primeira carga do harness de deadline ocorreu cedo demais; foi corrigida com
bootstrap de teste. Builds intermediárias falharam por includes NSIS, LogicLib e
CRLF do inventário; foram preservadas em diretórios distintos. A r7 passou em
todas as inspeções finais. Assertivas antigas de UI foram atualizadas para exigir
limpeza da superfície na retomada, mantendo os testes temporais/segurança.

## Artefatos

Diretório local `.cache/artifacts/windows/desktop-dev9-consolidated-candidate-r7/`.
Aplicação x64, identificador `com.lone.smartroom`, nome Lone Smart Room.
Wrappers NSIS/portátil x86 carregam o mesmo payload x64. **NotSigned**, asInvoker.

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| Lone-Smart-Room-2.0.0-dev.9-x64-Setup-DEV.exe | 105.788.573 | `992f5a10896038781d7c4f045f2a8d28a94f8c7de95098e674e071ba23f33fe3` |
| Lone-Smart-Room-2.0.0-dev.9-x64-Portable-DEV.exe | 105.498.222 | `f115894aa05191b60502d2ca39773b630f5a6bb592c052210e5c7791b4efe0fa` |

Identidade oficial preservada. Licenças CPython/ADLX e avisos existentes incluídos;
nenhum driver DLL AMD, SDK adicional ou binário PresentMon distribuído. Build local
de desenvolvimento; redistribuição externa requer revisão das condições aplicáveis.
Nenhum segredo, certificado privado, banco de pareamento ou agente operacional no pacote.

## Preservação e pendências

Conferência antes/depois: **118 arquivos instalados e 83 do perfil idênticos**;
195 arquivos do backup before-dev8 conferidos. Banco íntegro, identidades mantidas,
zero grants/pendências; quatro arquivos protegidos e comando Run com hashes
preservados. Zero processos relevantes de desenvolvimento/monitoramento ao final.
O agente já estava offline: **zero listener 8776**, nenhuma tentativa de inicialização
ou consulta autenticada a um serviço ausente. Android e instalação dev.8 não foram abertos nem atualizados; nenhum APK foi gerado. Não se declara auditoria diferencial global do firewall/
Registro/serviços: nenhuma operação nossa os modificou; Run foi comparado por hash.

Continuam abertos: inicialização automática operacional, TLS 10054, encerramento do
agente com sua configuração real, Crashpad, retomada GPU física, inventário CPU
intermitente, sensor térmico CPU, captura FPS real e integrações físicas externas.
Nenhuma dessas pendências foi declarada resolvida por testes com mocks.

## Plano único de implantação, homologação e reversão

1. Após autorização específica, verificar hashes/candidata, agente/grants/processos,
   backup novo da dev.8 e perfil. Preservar o backup dev.7 existente. Revisar os limites
   do novo helper antes de executar o assistente; não contornar proteções Windows.
2. Executar uma atualização NSIS assistida, não portátil, sem abrir ao concluir.
   Conferir hashes, recursos, perfil e logs restaurados; interromper se houver erro.
3. Autorizar sessão instalada com `--lone-validation-session`: priorizar sensores,
   widget e ocultar/restaurar nos primeiros 30 s; captar GPU ao restaurar e ~2/5/10 s.
   Não induzir falhas. Sair normal será solicitado pelo mesmo controller aos 45 s.
   Confirmar todos os componentes/pipes liberados antes de 120 s; timeout é falha,
   sem força ou repetição automática. O menu físico Sair ainda deve ser observado.
4. Validar ferramentas locais com arquivos descartáveis/CSV conhecido e nenhum
   reparo, jogo ou atuador. Captura FPS real e implantação do bootstrap do agente
   exigem autorização operacional própria; não estão incluídas implicitamente.
5. Para o agente, revisar o manifesto, backup/estado e comando fixo futuro, depois
   aprovar separadamente sua implantação/Run e um login controlado pelo usuário.
   Correlacionar evidências de despacho, começo do bootstrap, worker/listener e
   autenticação; preservar certificados e grants, sem reiniciar o Windows automaticamente.

Reversão do app, se autorizada: fechar normalmente, preservar o perfil dev.9 novo,
reinstalar a dev.8 original preservada e recuperar somente configurações próprias
necessárias do backup. Não apagar dados ou restaurar o banco do agente. O diário
de runtime adicional deve permanecer disponível até a conferência por hash.
Reversão do código: reverter os commits desta entrega, sem reset destrutivo; isso
não altera instalações ou Run. Nenhuma restauração/rollback foi executada aqui.

## Capturas de desenvolvimento

Todas são do Electron real, perfil isolado. Sensores não foram ligados. A tela FPS
contém faixa explícita de **CSV simulado, sem jogo**. Outras leituras ausentes aparecem
indisponíveis. Galeria em `captures/scale-1`, `scale-1_25` e `scale-1_5`.

![Biblioteca e FPS, fixture identificado](captures/scale-1/games.png)

![Widget de desenvolvimento](captures/scale-1/widget.png)

![Touch Panel de desenvolvimento](captures/scale-1/touch.png)

Recibos, hashes dos fontes e métricas detalhadas estão em `evidence/`.

## Checkpoints

- `8508e7e`: bootstrap cooperativo e reconhecimento opt-in da cadeia de identidade.
- `fc82125`: integração Windows dev.9, retomada GPU, temporizador, preservação NSIS e FPS externo.
- `25f2c1e`: rejeição de resultados FPS não finitos e candidata final r7.
- O commit documental posterior contém a matriz, capturas, recibos e scripts de
  consolidação/verificação. Árvore esperada limpa após esse commit, sem merge.
