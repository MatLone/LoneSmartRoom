# Integração visual Windows — 24/10/2026

Dashboard aprovado em `ddb1480` integrado ao aplicativo Electron existente. Implementação: `9be26acc24788cdf2192bb555b8860f39bb55845`, branch `feature/ui-migration-preview`. Checkpoint Android/documental `d5323f7` preservado na ancestralidade. Versão **Windows 2.0.0-dev.3**, com numeração independente do Android dev.7 instalado.

## Resultado

- Três seções, marca oficial, cartões, painéis flutuantes, composição do CS2 e espaço NEX preservados da prévia aprovada.
- Título neutro: “Seu espaço, sob controle.”. Indicador separado: **COMUNICAÇÃO NÃO INTEGRADA**. Não há cliente HTTP/HTTPS operacional nesta entrega.
- Estado do PC desconhecido, energia não verificada, nenhuma consulta desktop. Sensores sem valores fictícios; dispositivos e aplicativos indisponíveis. Permissões aparecem como **não consultadas**, sem apresentar o último inventário local como autorização atual.
- Widget é uma mudança real do tamanho da BrowserWindow pelo processo principal. Tem navegação inferior, três abas, painéis roláveis e retorno às dimensões anteriores do dashboard. Redimensionamento manual permanece disponível; largura pequena também adapta a composição.
- Minimizar continua usando a barra de tarefas; fechar encerra a janela/aplicativo. A auditoria não encontrou implementação de Tray no aplicativo anterior: não foi introduzido comportamento novo de bandeja nesta etapa.
- Textos secundários receberam mais contraste. Não foram implementados sensores, IA, controles de dispositivos ou ações operacionais.

## Imagens reais

![Comparativo da aplicação integrada](00-electron-integrado.jpg)

![Escalas por processo](01-escalas-electron.jpg)

- [Janela nativa — dashboard](native-window/01-dashboard-native.png)
- [Janela nativa — widget](native-window/02-widget-native.png)
- [Janela nativa — painel do widget](native-window/03-widget-panel-native.png)
- [Origem das capturas nativas](native-window/provenance.json)
- Capturas automatizadas: [100%](review/1/result.json), [125%](review/1_25/result.json), [150%](review/1_5/result.json), com PNGs na mesma pasta.

As capturas em `native-window` usam Windows.Graphics.Capture sobre a janela real do Electron em desenvolvimento. Podem conter a marca de ativação do Windows e o cursor do sistema. As de `review` usam `webContents.capturePage` da mesma aplicação integrada, carregando package/main/preload reais, com `offscreen:false` e janela visível. Não são imagens da prévia HTML isolada. Os comparativos apenas reúnem/reduzem essas capturas para leitura.

## Estrutura e segurança efetivamente implementadas

| Arquivo em `apps/windows-ui` | Responsabilidade |
| --- | --- |
| `main.cjs` | Entry point existente, encaminha ao módulo principal |
| `desktop-main.cjs` | Janela, widget, eventos e IPC restrito |
| `desktop-policy.cjs` | Validação pura de remetente, recursos locais e dimensões |
| `preload.cjs` | Sete operações tipadas de janela/versão, sem operações do agente |
| `index.html`, `desktop.css`, `desktop.js` | Dashboard aprovado integrado, navegação e painéis |
| `assets/brand/` | Recursos oficiais SVG, PNG e ICO |

`contextIsolation:true`, `nodeIntegration:false`, `sandbox:true` e `webSecurity:true`. IPC confere a janela emissora, seu frame principal, URL exata e argumentos. Preload expõe somente `getVersion`, `minimize`, `close`, `getWindowState`, `setWindowMode`, `toggleMaximize` e `onWindowState`; não entrega o evento IPC ao renderer. Sem canal genérico para terminal, arquivos, caminhos, rede, execução ou grants.

Recursos da sessão ficam restritos à lista exata de arquivos locais da interface; navegação externa, novas janelas, webviews e pedidos de permissões são bloqueados. Os scripts legados `app.js`, `agent-status.js` e `app-launch.js` não são carregados pelo novo entry visual. Permanecem preservados para recuperação. Não foi implementado pareamento desktop nem copiada a identidade do Samsung.

Revisão usa `--lone-development-review`, disponível somente no desenvolvimento, com perfil/logs/cache em `.cache/windows-desktop-review/`. Não abre o perfil funcional anterior. Não há hook de testes operacional embutido; o bootstrap de testes é carregado externamente via NODE_OPTIONS apenas no processo de desenvolvimento.

## Validação executada

| Verificação | Resultado |
| --- | --- |
| Política de janela, preload e recursos | 49 verificações aprovadas |
| Electron real: 100%, 125%, 150% | 71 verificações por execução; **213 aprovadas** |
| Composições por escala | 9 por execução; **27 avaliadas** |
| Dashboard, widget e widget estreito | Navegação das três abas aprovada |
| Painéis, rolagem, maximizar/restaurar, minimizar e fechar | Aprovados |
| Transbordamento horizontal e contenção dos painéis | Sem falha nos casos testados |
| Rede e renderer durante os testes | 0 requisições HTTP concluídas; 0 erros de renderer |
| Regressão versão/permissões/estados dos comandos | Aprovada, executores reais não acionados |
| Regressão JavaScript WoL | 11 cenários aprovados, **0 pacotes UDP** |
| Inventário original/recuperação | **86 registros verificados** |
| Preservação desta etapa | **180 arquivos idênticos** ao snapshot anterior |
| Dependências | 311 entradas do lock preservadas; nenhuma atualização/instalação |
| Banco operacional, leitura apenas | 0 grants; 0 comandos pendentes; histórico permaneceu em 4 |

Foram exercitadas dimensões dashboard e widget 440 px e estreito 350 px, abas, rodapé, painéis de conexão/dispositivos/permissões/sensores e informações da versão. A inspeção por interface nativa confirmou alternância para widget e fechamento do painel com Escape.

**Limite da validação DPI:** fatores 1, 1,25 e 1,5 foram aplicados ao processo Electron, com `devicePixelRatio` conferido. A escala global do Windows não foi alterada. Não houve validação física de troca entre monitores com DPIs diferentes, instalação em outra máquina ou teste de todos os recursos de acessibilidade.

Comandos de reprodução a partir da raiz, com as dependências já disponíveis:

```powershell
node tests/electron-window-policy.cjs
powershell -NoProfile -File scripts/test-electron-desktop.ps1 -Scale 1
powershell -NoProfile -File scripts/test-electron-desktop.ps1 -Scale 1.25
powershell -NoProfile -File scripts/test-electron-desktop.ps1 -Scale 1.5
node tests/version-launch-ui.cjs
node tests/android-wol-ui.cjs
.venv/Scripts/python.exe -B scripts/verify-preservation.py
```

Esses testes nativos abrem e fecham somente a janela de desenvolvimento isolada. Nesta etapa não foi reexecutada a suíte Python completa do agente: ele não foi modificado. A pendência TLS não foi apagada, tolerada como aprovação ou corrigida experimentalmente. [Resumo dos testes](evidence/test-summary.json), [preservação](evidence/preservation.json) e [ajustes do harness de desenvolvimento](evidence/development-diagnostics.json).

## Empacotamento verificado, sem instalação

Build Windows x64 **unpacked** gerada em diretório separado:

```text
.cache/artifacts/windows/desktop-dev3/win-unpacked/Lone Smart Room.exe
.cache/artifacts/windows/desktop-dev3/win-unpacked/resources/app.asar
```

Usados Node 22.16.0, Electron 45.0.0 e electron-builder 26.15.3 já presentes. Versão do pacote e nome `lone-smart-room` preservam a aplicação existente; `build.appId` continua `com.lone.smartroom`. Não houve alteração das versões de dependências.

Reprodução do empacotamento, a partir de `apps/windows-ui`:

```powershell
node node_modules/electron-builder/cli.js --win --dir --x64 --config.directories.output=../../.cache/artifacts/windows/desktop-dev3 --config.electronDist=node_modules/electron/dist
```

Conferência offline: 13 recursos/fonte conferidos dentro de ASAR, 7 imagens do ICO oficial encontradas no PE, 1 grupo de ícone. Nome e versão conferidos no pacote; appId conferido na configuração fonte, pois electron-builder retira essa seção do package empacotado.

SHA-256 do EXE: `84ecf7acdc79a03307e29c51ed3e5e556f35b7bcf460833a1095da2f516d286e`.

**Authenticode: NotSigned.** Não há instalador NSIS/portable final produzido nesta validação. O EXE empacotado não foi executado; a validação de execução é do Electron real em desenvolvimento. Não afirmar que a instalação ou distribuição assinada está homologada. [Inspeção do pacote](evidence/package-inspection.json) e [metadados do EXE](evidence/windows-package-metadata.json).

## Preservação e próximos limites

Android instalado não foi acessado por ADB nem atualizado. Fonte Android, APKs, backups, Kotlin/WoL, agente Python, executores, configuração operacional, certificados, credenciais e builds Windows anteriores mantiveram seus bytes. Credenciais não foram descriptografadas. Sem chamadas à API operacional, pacotes WoL, Steam/CS2, ações de energia ou alterações em firewall/rede/serviços/drivers.

Cópia local anterior do Windows: `.cache/backups/windows-ui-ddb1480/`, além do histórico Git. Inventário privado de hashes fica na cache e não é publicado junto de caminhos/identidades sensíveis. [Plano de reversão](REVERSAL.md).

Antes de atualizar Windows: revisar esta entrega; definir distribuição/assinatura e procedimento para preservar o perfil da instalação existente; somente depois autorizar instalação. Antes de qualquer cliente desktop operacional, corrigir e validar separadamente o tratamento TLS de corpos excessivos/ambíguos. [Arquitetura proposta](DESKTOP-AUTH-ARCHITECTURE.md). O status do PC e as permissões na interface continuarão indisponíveis até essa fase.
