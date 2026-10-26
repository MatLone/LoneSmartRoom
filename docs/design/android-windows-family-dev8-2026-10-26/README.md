# Android dev.8 — identidade Windows adaptada ao celular

Implementação local baseada nos componentes reais `apps/windows-ui/index.html`, `desktop.css` e `desktop.js`, preservando o aplicativo Android existente. Commit funcional: `874753f`. Nenhuma instalação, conexão ADB ou acesso ao Samsung foi realizado.

## Revisão visual

- [Comparativo das três abas](comparison-three-tabs.png) e [prancha HTML navegável](review.html).
- [Controles 390 × 844](390-controls.png), [Monitoramento PC](390-monitor.png), [Gamer Launcher](390-gamer.png).
- [Controles 360 × 800](360-controls.png), [Monitoramento menor](360-monitor.png), [Launcher menor](360-gamer.png).
- [Painel de conexão](390-connection-panel.png), [painel de dispositivo](390-device-panel.png).
- [Conectado demonstrativo](390-connected-demonstration.png), [desconectado demonstrativo](390-disconnected-demonstration.png), [zero grants demonstrativo](390-gamer-zero-grants-demonstration.png).
- Capturas com sufixo `-bottom` mostram o final rolado das três abas em 390 px.

São renderizações reais dos assets Android em Chromium/Electron offscreen com perfil exclusivo de teste, rede bloqueada e bridges explicitamente simuladas. **Não são capturas do Samsung, do WebView Android ou de sensores reais.** A barra de sistema e os estados de conexão demonstrativos estão identificados nas imagens; nenhum dos estados simulados altera o agente ou suas permissões.

## Mudanças

- Paleta principal idêntica à referência Electron: fundo `#0b0b0e`, superfície `#151518`, elevação `#1e1e23`, vermelho `#ff153f`, primária `#df0c32`.
- Mesmos SVGs oficiais de marca e família gráfica; mesma tipografia de interface com fallback Roboto/Arial, sem baixar fontes. A tipografia futurista LONE permanece na arte vetorial oficial.
- Cartões de PC, dispositivos, sensores, Steam/CS2, permissões, modal e espaço NEX seguem a família Windows. Dimensões, coluna única, alvos de toque e navegação inferior foram adaptados ao celular.
- Título neutro “Seu espaço, sob controle.”, estado HTTPS separado e texto explícito sobre energia não confirmada.
- Safe area superior já aprovada foi preservada: `max(32px, env(safe-area-inset-top)) + 12px`, sem duplicar offsets no logo. Insets inferior e laterais protegem navegação e conteúdo; modais respeitam a área útil.
- Navegação por teclado passou a usar roving tabindex. Sem gravação de preferências ou mudança de bridges.
- CPU/GPU/RAM, temperaturas, VRAM e armazenamento **continuam indisponíveis no Android**. O Windows tem coleta local, mas o transporte remoto dessas métricas ainda não foi implementado. Não há números, barras preenchidas ou gráficos fictícios.
- O CSS da família Windows é uma camada de apresentação sobre a base móvel existente; não carrega os handlers nem o preload do desktop.

## Preservação

50 arquivos Android anteriores à mudança estão fixados em `tests/fixtures/android-functional-baseline.json`: Kotlin/Java, manifesto, recursos nativos, marca, WoL e clientes/bridge bindings. As regressões confirmam identidade byte a byte. Não foram alterados Wake-on-LAN, origem `file:///android_asset/index.html`, `lone-wol-settings-v1`, HTTPS, certificados/pinagem, HMAC, antirreplay, credenciais, grants, executores ou preferências.

O botão WoL da prévia usa bridge substituta que apenas registra chamadas; não enviou UDP. Steam/CS2 permaneceram bloqueados quando faltam permissões, incluindo tentativas sintéticas e adulteração visual de `disabled` nos testes existentes. Autorização e confirmação nativa continuam obrigatórias no aplicativo real.

## Build e assinatura

- Android **2.0.0-dev.8 / versionCode 22**, numeração livre no histórico local; package `com.lonesmartroom.app`.
- APK local: `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.8-v22.apk`.
- SHA-256 APK: `a3c43e396c67eb34a0e965a4fc80ef0a956661812fdaea024f3cd93d636fd281`.
- Certificado SHA-256: `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`; apksigner validou assinatura v2 compatível.
- Compilação offline `assembleDebug` e `lintDebug` concluídas com o JDK/SDK já existentes. Nenhuma dependência instalada. Chave original usada no local existente, sem copiar chave ou senha para Git/relatórios.
- APK é candidato de desenvolvimento assinado, **não instalado**. APKs anteriores e APK funcional de recuperação foram preservados. Ver [recibo](apk-verification.json).

## Testes

| Suíte | Resultado |
|---|---|
| Python geral, contexto normal da conta | 159 iniciais; 206 finais após a fundação de diagnóstico |
| Preservação específica do redesign | 3 aprovados, 50 arquivos fixados |
| Monitoramento básico, somente mocks com I/O externo bloqueado | 133 aprovados |
| Renderer Android existente | 65 assertions; 15 combinações responsivas |
| Safe areas existentes | 60 casos de cabeçalho/inset/aba |
| Nova suíte visual Windows/Android | 352 assertions; 63 casos responsivos; zoom 125%/150%; modais e estados |
| WoL JavaScript | 11 cenários, sem UDP |
| Pacote WoL Kotlin via JVM | aprovado, sem transmissão |
| Versão/estados/autorização JavaScript | aprovado, sem abrir aplicativos |
| Gradle/lint | build aprovado; 0 erros, 10 avisos |

As suítes têm sobreposição e não devem ser somadas como testes únicos. Larguras 320, 360, 390, 412, 600, 800 e 844 px, inclusive orientação horizontal, foram verificadas com diferentes insets. Houve verificação de overflow, rolagem até o final, fechamento dos modais, foco, alvos de 44 px e separação da navegação.

Falhas iniciais foram registradas: o contexto restrito bloqueou sockets/ACLs de fixtures (`WinError 10013/5`) e o Chromium encerrou antes de inicializar. A execução no contexto normal autorizado passou, sem elevação administrativa ou alteração de proteções. Uma assertion de zoom falhou inicialmente; o zoom inicial do perfil de teste agora é definido explicitamente e a suíte completa final passou. A falha não foi ocultada nem atribuída ao hardware. A verificação avulsa do APK também exigiu definir explicitamente `JAVA_HOME` para o JDK existente; passou sem alterar a assinatura.

Os dez avisos lint incluem ferramentas com versão mais nova disponível, APIs WebView, trust manager customizado, recursos de ícone/splash e regras de extração. Não foram suprimidos nem corrigidos alterando segurança nesta tarefa. Os testes de certificado/pinagem do código de produção passaram em fixture TLS loopback; a pendência conhecida de corpos TLS excessivos permanece separada e não foi aplicada ao agente.

## Limitações e aprovação

Existe AVD API 36 configurado, mas a verificação de aceleração não comprovou prontidão e apresentou diagnóstico de Hyper-V/WHP. Não foi iniciado, reparado ou reconfigurado. Nenhuma ferramenta foi instalada. As prévias locais não homologam One UI, navegação gestual, comportamento IME/teclado, escala de fonte do sistema ou acessibilidade com TalkBack.

Quando o usuário retornar, revisar estas imagens; somente após autorização expressa realizar pré-verificações do Samsung e atualização `adb install -r` do candidato confirmado, preservando dados. Não executar esse comando agora. A atualização física, validação WebView, WoL real e comandos remotos continuam fora desta entrega.

O rollback de desenvolvimento deve reverter separadamente o commit visual e sua documentação. Não usar reset destrutivo, limpar dados ou restaurar produção automaticamente. O Windows dev.7 instalado e a homologação física parcial permanecem intactos; não houve nova sessão física Windows.
