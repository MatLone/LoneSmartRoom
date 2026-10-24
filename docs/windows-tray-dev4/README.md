# Windows 2.0.0-dev.4 — System Tray

Implementação sobre a branch `feature/ui-migration-preview`, preservando o checkpoint `0af70b5618863611d03a10e21d0a0b29c6cfcc4f`. Código no commit `3d56561`. **A instalação Windows permanece dev.3; os pacotes dev.4 não foram instalados nem executados.**

## Comportamento implementado

| Ação | Resultado |
|---|---|
| Botão Minimizar já existente | Minimiza na barra de tarefas, como antes |
| Novo botão **Minimizar para bandeja** | Salva o estado visual e oculta a mesma janela, somente se o Tray estiver disponível |
| Clique/clique duplo no ícone da bandeja | Exibe, restaura e focaliza a mesma janela no modo atual, inclusive Widget |
| **Abrir dashboard** no menu | Restaura a mesma janela em modo completo |
| **Modo Widget** no menu | Restaura a mesma janela em modo compacto, com navegação inferior |
| **Sair** no menu | Salva preferências visuais, destrói o Tray e encerra o Electron |
| X | Fecha normalmente e encerra o aplicativo; não foi convertido em ocultar |
| Segunda abertura no mesmo perfil | Segundo processo sai; primeiro restaura a janela existente. Argumentos/caminhos recebidos são ignorados |
| Falha na criação do Tray | Mantém janela utilizável e desabilita o novo botão; não esconde uma janela sem meio de restauração |

O ícone é o ICO oficial já aprovado, sem mudanças na marca. A referência ao Tray permanece no processo principal durante seu ciclo de vida. Não há autostart, serviços ou cliente do agente.

Foram usadas as APIs oficiais [Tray](https://www.electronjs.org/docs/latest/api/tray) e [requestSingleInstanceLock](https://www.electronjs.org/docs/latest/api/app#apprequestsingleinstancelockadditionaldata). O bloqueio é por perfil de usuário/instalação: perfis de revisão estão separados do instalado. O dev.3 anterior não implementava esse bloqueio; antes de uma atualização futura será necessário confirmar seu encerramento.

## Organização e segurança

- `apps/windows-ui/desktop-window.cjs`: ciclo de vida da janela, modos, menu, bandeja, encerramento e reação à remoção/mudança de monitor.
- `apps/windows-ui/desktop-preferences.cjs`: schema estrito de preferências visuais e escrita local atômica.
- `apps/windows-ui/desktop-policy.cjs`: validação de geometria, restauração na área útil atual, identidade de remetente/frame e allowlist de recursos locais.
- `apps/windows-ui/desktop-main.cjs`: composição desses módulos, instância única e IPC delimitado.
- Preload ganhou **somente `minimizeToTray()`**, sem argumentos. Agora são oito métodos de janela/versão/eventos, sem leitura de caminhos, execução, rede ou concessão de permissões. O main revalida remetente, frame, origem e quantidade de argumentos.
- HTML ganhou um botão separado; navegação, cartões, marca e ações indisponíveis foram mantidos. Nenhum coletor/sensor ou executor foi integrado ao desktop.
- `contextIsolation=true`, `nodeIntegration=false`, sandbox e `connect-src 'none'` preservados. A bridge revisada continua fixada por hash exato em `scripts/preservation_rules.py`; exceções Android/WoL não foram ampliadas.

## Persistência

Arquivo fixo **`desktop-window-state.json` dentro de `app.getPath('userData')`**. Em uma futura execução instalada, permanece o mesmo perfil `<USERPROFILE>\AppData\Roaming\Lone Smart Room`, sem migrar, importar ou apagar seus dados.

Schema 1 admite exclusivamente: último modo, bounds separados de dashboard/Widget, maximização do dashboard e booleano `minimizeToTray`. Nenhuma credencial, certificado, grant, URL ou caminho é salvo nesse documento.

**A preferência `minimizeToTray` foi preparada e testada no schema, com padrão `false`, sem interface ou ativação automática nesta etapa.** Mesmo um valor `true` carregado não remapeia silenciosamente o botão Minimizar ou o X. A ação explícita de bandeja já funciona; uma configuração que mude o comportamento padrão exige decisão posterior.

Validação limita tipos, chaves, coordenadas finitas, dimensões e arquivo a 8 KiB. Bounds são confrontados com as áreas úteis dos monitores atuais; posições de monitores removidos são recolocadas em área visível. Coordenadas negativas válidas de outro monitor são preservadas. Alterações de monitor durante a sessão também são tratadas. Não se persiste o estado oculto: uma nova sessão sempre mostra a janela.

Escrita com debounce, temporário exclusivo, `fsync` e substituição atômica; flush ao fechar/sair. Falha de escrita não impede encerramento. Conteúdo inválido, schema desconhecido e alvos simbólicos/reparse não são sobrescritos automaticamente: usa-se padrão em memória, conservando o arquivo para diagnóstico. Arquivo temporário preexistente não é apagado. O armazenamento contém apenas preferências visuais; não é um cofre de credenciais.

A primeira exibição a 125% revelou ajuste nativo de geometria: pedido 354 × 652, retorno 360 × 657. A implementação reaplica os bounds validados após a primeira exibição; a restauração final ficou em 355 × 653, dentro da tolerância de 2 DIP do teste. A 100% os bounds coincidiram exatamente. Não se alterou o DPI do Windows.

## Testes finais

| Grupo | Resultado |
|---|---|
| Tray, instância, ciclo de vida, persistência e monitores simulados | **85 assertions aprovadas** |
| Política de janela, preload e IPC | **51 assertions aprovadas** |
| Política de distribuição e extração estática do uninstaller | **44 assertions aprovadas** |
| Electron real isolado a 100%, 125% e 150% | **250 assertions; 27 layouts; zero erros de renderer; stderr final vazio nas três escalas** |
| Instância única nativa | Segundo processo terminou com saída 0 nas três escalas; uma janela mantida |
| Encerramento nativo pelo menu | Tray destruído antes da saída nas três escalas |
| Regressões Python | **76 testes aprovados**; executores substituídos e servidores temporários de loopback |
| Versão/comandos Android e armazenamento WoL | Verificações aprovadas; **11 cenários WoL; zero pacotes reais** |
| Preservação original/recuperação | **86 registros aprovados** |
| Conteúdo NSIS/portátil, PE, ASAR, ícones e ausência de credenciais | **172 verificações offline aprovadas** |
| Recursos do pacote | 24 arquivos ASAR iguais às fontes; sete imagens do ICO oficial no PE |
| Preservação local desta etapa | **1.150 hashes idênticos** antes/depois, incluindo instalação, perfil instalado, dados protegidos, pacotes anteriores e backup |

A execução nativa usa o main/preload reais com instrumentação somente em `tests/`, por `NODE_OPTIONS`. Esses arquivos não entram no pacote. Há um Tray real do Windows; os testes automatizados invocam callbacks reais de menu/clique e a API de janela, sem fingir que foram testes físicos da instalação dev.4. A matriz confirma ausência de overflow horizontal, funcionamento das três seções, painéis, rolagem e indisponibilidade das ações operacionais. Os testes de monitores removidos são simulados: nenhum monitor foi desconectado fisicamente.

Além disso, duas sessões visuais isoladas foram capturadas pela ferramenta nativa: dashboard/Widget e menu real. O X na primeira e **Sair** no menu na segunda terminaram com código **0**, Tray destruído e nenhum processo Electron restante. Nenhum EXE gerado ou aplicativo instalado foi usado para essas sessões.

Os erros intermediários não foram descartados: `evidence/development-diagnostics.json` registra a instrumentação inicial do menu, a reprovação inicial do guard do preload, o desvio real de geometria a 125%, e a verificação inadequada de LASTEXITCODE no wrapper PowerShell. A primeira regressão reprovada também foi preservada em `evidence/regression.txt`. Uma mensagem GPU apareceu após abortar o primeiro teste; não apareceu nos stderr finais, sem qualquer mudança de driver.

**Limitação adicional:** a primeira enumeração visual listou transitoriamente uma janela Electron intitulada `Error`; ela desapareceu antes de ser inspecionada, sem texto ou stderr disponível. Sua origem não foi comprovada. Não se repetiu na sessão separada do menu; não é classificada como crash confirmado nem omitida dos diagnósticos. O teste futuro da instalação deverá observar também eventual reaparecimento dessa janela.

## Capturas e prévia do ícone

- `native-review/01-dashboard-desenvolvimento.jpg`: Electron real com botão explícito de bandeja.
- `native-review/02-widget-desenvolvimento.jpg`: Widget real e navegação inferior.
- `native-review/03-menu-nativo-bandeja.jpg`: **menu nativo real**, exibido dentro da área da janela pela fixture de revisão.
- `native-review/04-menu-nativo-detalhe.jpg`: região nativa do menu capturada separadamente pela ferramenta.
- `native-review/05-icone-oficial-escalas.svg`: prévia de escala do PNG oficial a 16/24/32/48/80 px, identificada como composição, não captura da barra de tarefas.
- `native-review/provenance.json`: Tray real registrado pelo Windows, área 32 × 48 px nesta sessão; uma janela, perfil isolado e nenhum cliente operacional.
- `review/1`, `review/1_25`, `review/1_5`: capturas nativas automatizadas das três seções, Widget, painéis e menor largura.

A ferramenta não forneceu uma janela capturável da área de notificação do Explorer; não se apresenta uma montagem como captura real do ícone na barra do Windows. O recurso oficial, criação real do Tray, bounds retornados pelo shell e menu nativo estão comprovados separadamente. A posição final/overflow do ícone após instalar continua sujeita às preferências do Windows do usuário, que não foram alteradas.

## Pacotes preparados

Pasta: `<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\windows\desktop-dev4-tray-distribution`.

| Artefato | Bytes | SHA-256 |
|---|---:|---|
| `Lone-Smart-Room-2.0.0-dev.4-x64-Setup-DEV.exe` | 101606566 | `e54710fa58103e8c0573f0d1dabbf7ed7e68b3abcc5eda3d85f4305ab32c3570` |
| `Lone-Smart-Room-2.0.0-dev.4-x64-Portable-DEV.exe` | 101320430 | `0fd73fb56ddbf56d84e80ac9a03ab25d2e84e7d740fbb5278e0ef408c6f84075` |

Nome **Lone Smart Room**, versão **2.0.0-dev.4**, appId **com.lone.smartroom** e perfil existente preservados. Ambos **NotSigned**, uso local de desenvolvimento. As mensagens genéricas de “signing with signtool” do builder não comprovam assinatura: tabela de certificado PE vazia e inspeção Authenticode confirmam ausência de assinatura. Nenhuma proteção do Windows foi desabilitada.

NSIS assistido, somente usuário atual, sem elevação, sem execução após concluir e com confirmação explícita para instalação anterior. O aplicativo embarcado é **x64 (PE 8664)**; os wrappers NSIS são bootstrap x86, como no pacote anterior. Não há agente, certificados, bancos, credenciais, serviços ou regras de firewall no payload. A extração do uninstaller foi estática, sem executar os EXEs gerados. O builder recusa sobrescrever a pasta de artefatos já existente.

## Preservação e pendências

- Instalação dev.3 e seu perfil permaneceram byte a byte iguais nos arquivos inventariados; backups e pacotes antigos não foram sobrescritos.
- Backup `Windows-before-dev3-20261024T145523Z`: 336 arquivos de dados, 35.980.960 bytes, 139 diretórios, hashes e ACLs restritas ao usuário verificados.
- Android/Samsung, WoL, HTTPS, pareamento, certificados, credenciais, executores e permissões não foram modificados. **Zero grants e quatro comandos históricos inalterados**.
- **Porta 8776 sem listener tanto na leitura inicial quanto final.** O agente não foi iniciado, encerrado ou reconfigurado. A UI/tray funcionou sem agente; não se afirma disponibilidade operacional HTTPS. Eventual investigação do agente offline fica em escopo separado.
- Não houve Steam/CS2, pacotes WoL, energia, autostart, alteração de serviços/drivers/firewall/Registro ou acesso/modificação à tarefa OneSettings RefreshCache.
- A pendência TLS mantém seu hash e conteúdo original. Passar na suíte desta execução não resolve o problema intermitente de corpos excessivos/ambíguos; cliente operacional continua bloqueado.
- Nenhuma nova dependência foi instalada. Electron 45.0.0 e electron-builder 26.15.3 existentes foram reutilizados.

## Atualização e reversão — não executadas

1. Após autorização específica, confirmar fechamento de dev.3 e demais sessões de teste; dev.3 não coopera com o novo bloqueio de instância única.
2. Fazer novo backup protegido do perfil instalado atual, além de conservar o backup pré-dev.3. Este último precede a primeira execução e não contém o perfil de produção criado depois dela.
3. Revalidar SHA-256/Authenticode e executar somente o NSIS assistido autorizado, com atualização explícita e sem iniciar automaticamente. Não desativar SmartScreen/Defender.
4. Mediante autorização de execução, testar posição/visibilidade real do Tray, clique, menu, Widget, minimizar versus X/Sair e persistência, sem cliente ou comandos operacionais.
5. A instalação atual não precisa de reversão, pois não foi alterada. Para reverter o código, usar um commit de `git revert 3d56561` em árvore limpa, após decisão do usuário; nunca reset destrutivo. As evidências documentais podem permanecer como histórico.
6. Se uma futura atualização instalada precisar de retorno, preservar primeiro o perfil corrente, usar o pacote dev.3 preservado mediante revisão/consentimento do instalador e restaurar dados somente se necessário e autorizado. Dev.3 ignora o novo arquivo de estado visual; não limpar userData nem presumir downgrade de dados seguro.

**Parada obrigatória agora:** pacotes prontos para revisão; instalação, substituição e primeira execução do pacote final dependem de nova autorização do usuário.
