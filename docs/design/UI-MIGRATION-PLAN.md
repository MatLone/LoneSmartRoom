# Evolução visual 2.0 — análise, protótipos e migração

Referência funcional: `885046658b6d62ece25f70579e0a14c7691f01e4` e todos os
descendentes existentes ao iniciar esta rodada. **Android primeiro, Windows
depois.** Esta entrega altera somente documentação, protótipos de revisão e seu
teste isolado; nenhum fonte em apps/agent, APK instalado, dado local, grant,
certificado ou serviço é alterado. Não representa uma segunda aplicação de
produção nem substitui o projeto atual.

## O que existe hoje

| Área | Implementação verificada | Consequência para a evolução |
| --- | --- | --- |
| Android | Activity Kotlin com WebView local, HTML/CSS/JS em `apps/android/app/src/main/assets` | Evoluir o renderer atual; não migrar framework ou reconstruir backend nesta fase |
| Origem/identidade | `com.lonesmartroom.app`, `file:///android_asset/index.html`, versão pelo `LoneAppInfo` | Preservar pacote, origem e assinatura; manter versão dinâmica também no título |
| WoL real | `WakeOnLan.kt`, `MainActivity.WakeBridge`, chamada JS `LoneAndroid.sendWake` e callback `onLoneWakeResult` | Preservar o emissor Kotlin e o contrato da ponte; não vincular WoL ao estado do agente |
| Configuração WoL | `lone-wol-settings-v1`, leitura/validação/gravação em `app.js` | Manter chave e esquema; não inicializar campos com valores padrão sobre dados existentes |
| HTTPS e status | `AgentBridge`, `AgentClient`, `PinnedTls`, `AgentVault`, `agent-status.js` | Renderer recebe estado; segredo e pinning permanecem no cliente nativo |
| Aplicativos | `app-launch.js`, confirmação nativa e permissões por app/dispositivo no agente | Preservar IDs Steam/CS2, allowlist, HMAC, anti-replay, grants e deduplicação |
| Interface legada | Abas superiores, estilos pequenos de widget, cartões de dispositivos, métricas/cenas/voz/otimizações demonstrativas em `app.js` | Novo layout deve deixar recursos sem integração indisponíveis, sem executar transições demonstrativas |
| Electron atual | Janela de widget 465×830; preload expõe apenas versão/minimizar/fechar | Ainda não é dashboard completo nem possui cliente seguro nativo de status/launch/WoL |
| Status duplicado | Área HTTPS real e área antiga de energia/simulações, com descrições desatualizadas | Uma apresentação coerente com fontes de verdade separadas, sem substituir código real por simulação |

O backend expõe presença/status do agente, não telemetria completa ou confirmação
de estado de energia. “Conectado” significa comunicação autenticada com o agente.
Não se pode inventar CPU/GPU/RAM, confirmar “PC desligado” por timeout nem concluir
“jogo aberto” a partir de despacho.

## Identidade visual e busca da logo

Referência informada pelo usuário: **Variante 3 — Contorno Luminoso**, símbolo
angular vermelho neon e tipografia futurista LONE SMART ROOM. O histórico de
“Design e Identidade visual” confirma aprovação, mas suas referências de imagem
não são retornadas pela leitura disponível e não havia anexos recuperáveis.

Não foram localizados:

- `Painel de identidade Lone Smart Room.png`
- `Lone_Smart_Room_Marca_Oficial.zip`
- `Lone_Smart_Room_v1.5_Logo_Oficial_Aplicada.zip`

Busca de nomes em Documents, Downloads, Desktop, Pictures e OneDrive do usuário,
incluindo pastas antigas e recuperação; também foram procuradas pastas relacionadas
na raiz C:/D:. Não se afirma ausência em todo disco, serviços remotos ou arquivos
renomeados sem indicação de origem. Imagens pessoais sem relação identificada
não foram abertas.

Pacotes inspecionados em leitura, sem executar ou extrair seu conteúdo:

| Caminho completo | Resultado |
| --- | --- |
| `<USERPROFILE>\Downloads\Lone_Smart_Room_Etapa_1.3.zip` | assets/icon.svg, icon.png e icon.ico; SVG idêntico ao ícone antigo de casa |
| `<USERPROFILE>\Downloads\Lone_Smart_Room_Etapa_1.4.zip` | Mesmos recursos antigos; nenhum correspondente à Variante 3 |
| `<USERPROFILE>\Downloads\Lone_Smart_Room_Android_WoL_v1.4.zip` | Nenhum recurso raster/SVG de marca |
| `<USERPROFILE>\Downloads\Lone_Smart_Room_Windows_Agent_v1.5.zip` | Nenhum recurso de marca |
| `<USERPROFILE>\Downloads\Lone_Smart_Room_Windows_Agent_v1.5 (1).zip` | Nenhum recurso de marca |

Hashes dos cinco pacotes iguais antes/depois da inspeção. Cópias de recuperação
existentes não foram modificadas. [Recibo de busca](brand-search.json).

**Decisão:** área “MARCA PENDENTE” em todos os protótipos. Nenhuma logo angular
foi inventada, nem o ícone de casa apresentado como definitivo. A importação do
asset original exigirá comparação visual e confirmação de correspondência pelo
usuário. Não alterar ícone/splash/identidade instalada enquanto isso estiver pendente.

Paleta proposta, ainda sujeita à arte original: fundo `#0b0b0e`, superfícies
`#151518`/`#1d1d22`, bordas grafite, vermelho de destaque `#ff2945`, ação principal
`#d91432`, texto claro e cinzas de apoio. Ícones lineares locais, raios de 12–22 px,
tipografia do sistema, sem fontes/CDNs externos. A tipografia de interface não
recria a tipografia da logo aprovada.

## Protótipos para revisão

- [Android navegável](prototype/android.html): três destinos na navegação inferior,
  cartões de PC e dispositivos, status e ajustes, monitoramento sem dados falsos,
  Gamer Launcher e espaço NEX. Navegação fixa; conteúdo rola acima dela.
- [Windows navegável](prototype/windows.html): mesmos componentes/tokens, menu
  lateral, dashboard amplo e painel contextual NEX/capacidades. Não anuncia como
  implementado um cliente Windows que o preload atual não possui.
- Botões de configurações abrem painéis; abas e teclado funcionam. Interruptores,
  sliders e ações de dispositivo ficam desabilitados, com motivos explícitos.
- Todos os campos exibem placeholders de preservação, sem MAC/IP, certificado,
  segredo, histórico ou nome de dispositivo extraído do ambiente real.
- “PRÉVIA VISUAL · SEM CONEXÃO” permanece visível. Sem métricas aleatórias,
  conexão fictícia, assistente respondendo, cenas aplicadas ou toast de envio.

As páginas não carregam scripts do aplicativo, não usam ponte nativa/IPC, fetch,
WebSocket ou localStorage. CSP bloqueia conexões e submissão de formulários. As
prévias são artefatos de revisão **dentro do mesmo repositório**, não outro produto.

## Migração em etapas pequenas

### A. Aprovar desenho e resolver marca

Revisar três abas Android, leitura dos cartões e painéis; confirmar proporções e
vermelho com o arquivo original quando recuperado. Refinar acessibilidade/tamanho
de texto antes de portá-los para assets de produção. Não instalar APK nesta etapa.

### B. Portar estrutura Android preservando contratos

Adicionar tokens/componentes ao renderer existente, mantendo ponto de entrada
e origem da WebView. Portar navegação inferior e conteúdo das três abas.
Separar apresentação dos trechos demonstrativos de `app.js`: o layout novo não
deve inicializar seus timers, sensores falsos, voz ou transições de energia.
Preservar o armazenamento legado `lone-smart-room-demo-v1` sem apagá-lo ou
reinterpretá-lo como estado real. Não remover handlers reais por uma troca ampla
de arquivo sem testes de regressão.

| Contrato preservado | Apresentação nova |
| --- | --- |
| `LoneAndroid.sendWake` / `onLoneWakeResult` | Botão WoL + resultado de envio; nunca “PC ligado” automaticamente |
| `lone-wol-settings-v1` | Painel editável com dados existentes, validação atual e gravação somente por alteração válida |
| `LoneAgent.showPairing` | Acesso ao diálogo nativo de identidade; nenhum segredo transitando no formulário Web |
| `onLoneAgentStatus` | Desconhecido / Conectado / Desconectado, mensagem e última comunicação preservada |
| `refreshAppPermissions` / `requestAppLaunch` | Botões bloqueados por padrão; habilitação somente pelo estado de autorização retornado; confirmação nativa mantida |
| `refreshLaunchResult` / `onLoneAppLaunch` | Solicitado / Aceito / Executado / Falha; não criar request_id novo ao consultar resultado |
| `LoneAppInfo.getVersionName` | Versão real em cabeçalho/título; não fixar “1.4” ou versão de prévia |

Estado de energia, entrega de WoL, acessibilidade HTTPS e prontidão de aplicativo
permanecem independentes. WoL não depende de HTTPS, credencial ou grant de abrir
apps. Falha/certificado inválido/revogação mantém ações seguras bloqueadas.
Suspender/Reiniciar/Desligar continuam sem ações disponíveis.

### C. Validar Android antes de atualização

1. Testes de DOM/estado com bridges substituídas: concessão/revogação, ocupado,
   consulta sem reenvio, falha de conexão, callback WoL e indisponibilidade.
2. Testar migração com fixture de `lone-wol-settings-v1` existente, não valores
   reais: abrir/navegar não deve modificar campos ou escrever defaults.
3. Reexecutar os 70 testes do backend/contratos, teste Kotlin de pacote WoL e
   preservação de arquivos; nenhuma ação física para validar layout.
4. Conferir 320–412 CSS px, safe areas/API 26–36, teclado, foco, contraste,
   acessibilidade/tamanho de fonte ampliado e rolagem com navegação inferior.
   O teste de renderer desktop não substitui WebView/Samsung reais.
5. Gerar APK com assinatura original, package e origem preservados, versionCode
   superior ao instalado; não incluir keystore/segredos no Git. Conferir certificado
   original já validado e plano de recuperação dos dados antes de instalar.
6. Apresentar APK e resultado para **autorização expressa de atualização**. Não
   instalar, desinstalar, limpar dados ou testar energia a pretexto de validar UI.

### D. Windows depois do Android aprovado

Expandir `apps/windows-ui`, preservando Electron, para dashboard com menu lateral.
Manter `contextIsolation`, sandbox e ausência de Node no renderer. Um adaptador
IPC estreito no processo principal, validando emissor e entradas, poderá ligar a
apresentação ao agente HTTPS existente. O renderer nunca receberá segredos DPAPI,
chave de assinatura ou acesso arbitrário ao sistema. Não reutilizar credencial
do Samsung para uma nova identidade Windows. A escolha do cliente/armazenamento
nativo Windows será revisada antes da implementação dessa etapa.

Referência: [segurança oficial Electron](https://www.electronjs.org/docs/latest/tutorial/security).
Não trocar a origem Android por um protocolo novo apenas para seguir uma
recomendação Electron: essa migração teria implicações de armazenamento e deve
ser avaliada separadamente. Novo dashboard, futuro widget/tray e agente
autoiniciado por login são responsabilidades distintas; o agente continua
independente da abertura da interface.

O Electron atual não expõe ponte de WoL ou cliente autenticado; até existir
implementação real, esses controles Windows permanecem indisponíveis. Não dar
aparência funcional a botões de simulação. Monitoramento de hardware,
SignalRGB/Home Assistant e NEX continuam capacidades futuras, explicitamente
indisponíveis. Espaço NEX não solicita microfone, modelo, chave API ou conversa.

## Critérios de aceitação

**Nesta entrega:** 21 combinações de plataforma/largura/aba testadas sem overflow,
três destinos corretos, modais e teclado funcionando, botões reais desabilitados,
zero solicitações externas, zero acesso a ponte/IPC e zero gravação de storage.
Prévias PNG verificadas visualmente; marca pendente clara. Nenhuma mudança em
apps/agent ou dispositivo instalado.

**Na integração:** não regredir WoL, pareamento, pinning, HMAC, grants, consulta de
status ou lançadores. Nenhum indicador falso de potência, telemetria ou jogo
aberto. Atualização compatível preserva dados e exige autorização. Integrações
ausentes não aceitam ações. Android aprovado antes de portar o dashboard Windows.

**Reversão:** nesta entrega basta deixar de usar os protótipos; não há migração
de dados nem backend a reverter. Na integração futura, commits pequenos separam
estrutura, estilos e bindings; reverter fonte não implica downgrade automático
do APK ou preservação automática de dados em downgrade. Manter os artefatos de
recuperação e confirmar compatibilidade antes de qualquer operação no Samsung.
