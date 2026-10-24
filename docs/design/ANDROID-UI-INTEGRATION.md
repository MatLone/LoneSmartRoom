# Integração funcional Android — 2.0.0-dev.3

Implementação na branch `feature/ui-migration-preview`, commit
`6b9a6b3c801b0466cebffd3406df35e34c43c5b2`. O checkpoint
`885046658b6d62ece25f70579e0a14c7691f01e4` permanece ancestral, assim como os
avanços funcionais posteriores. Nenhum projeto original, backup ou dump foi
modificado. Nenhuma instalação ou operação ADB foi executada nesta entrega.

## Comportamento implementado

O mesmo aplicativo Android passa a carregar uma apresentação própria a partir
de `file:///android_asset/index.html`. A navegação inferior oferece Controles,
Monitoramento PC e Gamer Launcher. A versão do cabeçalho continua vindo de
`LoneAppInfo.getVersionName()`, sem número fixo no HTML.

| Módulo | Responsabilidade |
| --- | --- |
| `mobile-shell.js` / `mobile-v2.css` | Layout, abas, foco e painéis flutuantes; nenhuma ação nativa |
| `agent-status.js` | Cliente de status e abertura do diálogo nativo de pareamento, sem alterações |
| `app-launch.js` | Consulta de permissões e resultados; Steam/CS2 com IDs fixos, sem alterações |
| `mobile-bindings.js` | Apresentação dos callbacks existentes e bloqueio adicional enquanto desconectado ou sem permissões atualizadas |
| `wol-ui.js` | Formulário e envio WoL pela mesma bridge e contrato persistido |

Controles apresenta estado autenticado desconhecido/conectado/desconectado,
última comunicação, atualização manual e configuração WoL. O estado de energia
é explicitamente **não verificado**: falha de conexão não significa PC desligado,
e envio UDP não comprova despertar. Não há dependência de HTTPS para enviar WoL.

O painel de conexão reapresenta o status/última comunicação e acessa o fluxo
nativo de pareamento existente. Não exporta URL, identidade de dispositivo,
credenciais ou certificados do cofre para o JavaScript. A comprovação de
identidade e os dados necessários ao pareamento continuam no diálogo nativo.

Steam e CS2 continuam dependentes das permissões individuais concedidas no
Windows e da confirmação nativa. Na reconexão, os botões aguardam nova consulta
de permissões. A tela distingue Solicitado, Aceito, Executado e Falha; Executado
é despacho ao Windows e não confirmação de biblioteca/menu carregado. Consultar
resultado não reenvia a abertura. Uma consulta somente de leitura ao banco de
produção confirmou **zero grants**; nenhuma permissão foi concedida ou revogada.

CPU, GPU, RAM e coleta de sensores/temperaturas não têm integração nesta entrega;
os indicadores permanecem indisponíveis, sem percentuais ou gráficos fictícios.
Os cartões de dispositivos abrem painéis informativos, com alimentação e demais
controles desabilitados. NEX é somente espaço reservado. Suspender, Reiniciar,
Desligar, controle de RPM e otimizações não possuem ações nesta interface.

A marca permanece pendente em `#brandAsset`, isolada para substituição futura
pela arte original. Não foi usado o antigo ícone de casa no cabeçalho nem criada
uma aproximação da Variante 3. Os ícones Android já existentes não foram alterados.

## Preservação e segurança

- Package `com.lonesmartroom.app`, origem WebView, diretório de dados, DOM storage
  e assinatura mantidos. Nenhum código Kotlin/Java ou arquivo do agente/Windows
  foi alterado. Não houve novo canal nativo, alteração de firewall ou serviço.
- Chave `lone-wol-settings-v1`, campos MAC/broadcast/porta e bridge
  `LoneAndroid.sendWake` / `onLoneWakeResult` preservados. O formulário reaproveita
  o registro existente, inclusive campos adicionais; abrir/fechar/navegar não
  grava defaults. Salvar exige ação explícita e validação (UDP 7 ou 9).
- Registro ilegível permanece intacto até uma gravação explícita válida. Falha
  de persistência mantém a configuração anterior. Edição cancelada não altera
  o pacote enviado; envios em andamento têm guarda contra duplo toque, sem retry.
- `app.js` e `styles.css` antigos foram mantidos byte a byte, inclusive como
  referência recuperável. O novo HTML não carrega `app.js`, portanto suas
  simulações de dispositivos/telemetria/NEX não são executadas.
- HTTPS, pinning TLS, HMAC, anti-replay, Android Keystore e cofre nativo não
  sofreram alterações. Não há credenciais no renderer. O CSP do novo HTML
  bloqueia conexões JavaScript, recursos externos e scripts inline. O tráfego
  autenticado continua exclusivamente no cliente nativo já validado.
- Autorizações no backend e validações nativas permanecem decisivas. Desabilitar
  botões é proteção de interface adicional. Não são aceitos novos caminhos,
  argumentos, shell, PowerShell ou comandos genéricos vindos do Android.

## Verificação realizada

| Verificação | Resultado |
| --- | --- |
| Suíte Python | **71 aprovados** (70 anteriores + contrato da nova entrada Android) |
| Agente legado com executor mock | Aprovado, sem ação física |
| TLS/HMAC, expiração, replay, revogação e requisições indevidas | Regressão aprovada em fixtures locais |
| Estado/versão e comandos na interface compartilhada | Aprovado |
| WoL na nova interface | **11 cenários**: persistência, cancelamento, validação, corrupção, indisponibilidade e timeout |
| Renderizador Android com bridges substitutas | **56 verificações**, incluindo **15** combinações de largura/aba (320, 360, 390, 412 e 800 CSS px) |
| Permissões | Grant vazio, grant individual, revogação/desconexão, reconexão sem permissão fresca e tentativa de forçar botão habilitado bloqueados |
| Pacote Kotlin WoL de produção | Bytes e validação aprovados; nenhum UDP enviado |
| Fontes e recuperação | **86 registros** do manifesto preservados; WakeBridge inalterada |
| Android offline `assembleDebug` + `lintDebug` | Sucesso; **0 erros, 5 avisos** |
| Assinatura/manifesto/empacotamento | Certificado original, package, versão e assets conferidos |

O renderizador usa perfil separado, preload de testes explícito e métodos que
somente registram chamadas em memória. Requisições externas são bloqueadas e
permissões são negadas. Nenhum teste lança Steam/CS2, envia WoL real, acessa o
Samsung ou concede grants de produção. Os testes HTTPS usam servidores de
fixture locais, sem iniciar/reiniciar o agente real.

As capturas em `android-integrated-previews/` usam **somente dados sintéticos**.
Não representam uma nova conexão física verificada. Os protótipos anteriores
permanecem em `prototype/` e `previews/`. O recibo técnico desta entrega está em
`android-ui-validation.json`.

Comandos de reprodução (a partir da raiz do repositório, dependências existentes):

```powershell
./scripts/test-safe.ps1
./scripts/test-android-ui.ps1
./scripts/prepare-compatible-apk.ps1 -SdkRoot '<USERPROFILE>\AppData\Local\Android\Sdk'
./scripts/test-android-packet.ps1
./.venv/Scripts/python.exe -B scripts/verify-preservation.py
```

O teste de renderer precisa de permissão para criar o processo Electron oculto;
os testes HTTP/TLS de fixture precisam de loopback. No sandbox restrito, as
primeiras tentativas foram impedidas pelo ambiente (erro de processo e
WinError 10013); as execuções com essas permissões passaram. Não foram contornadas
as restrições do aplicativo ou alterada qualquer regra de rede do Windows.
Se Git exigir reconhecimento do proprietário, usar `safe.directory` apenas no
processo para este checkout, sem alterar a configuração global.

## APK preparado — não instalado

- Versão **2.0.0-dev.3**, `versionCode` **17**, package `com.lonesmartroom.app`.
- Arquivo `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.3-v17.apk`.
- SHA-256 do APK:
  `893b121b387a534ec4de24ae36bcc0b433ab42eaafa01c1031b73b651b0d9ebe`.
- SHA-256 público do certificado, confirmado com `apksigner`:
  `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
- Esquema APK v2 verificado. Chave original usada localmente, sem cópia ou
  versionamento de arquivo de assinatura ou credenciais.
- APK funcional 1.4 e candidatos anteriores permanecem preservados em
  `recovery/artifacts/android/` e `.cache/artifacts/android/`.

A compatibilidade de origem e armazenamento foi conferida no código e no APK;
a preservação efetiva após atualização ainda precisa de validação no Samsung.
O certificado compatível permite planejar atualização com `adb install -r`,
mas **não autoriza executá-la**.

## Pendências e próximo procedimento

1. Revisar o visual integrado; os detalhes estéticos continuam sujeitos à
   aprovação. Fornecer a arte original da marca para substituir o placeholder.
2. Os cinco avisos de lint preexistentes envolvem versão de Gradle, orientação
   fixa, JavaScript da WebView, TrustManager personalizado e regras de extração
   de dados Android 12+. O compilador também avisa sobre duas APIs WebView
   depreciadas. Nenhum desses mecanismos foi modificado nesta migração. A
   regressão de certificado inválido passa, mas o aviso genérico de TrustManager
   não equivale a uma auditoria completa de toda a implementação TLS.
3. Após autorização expressa de atualização, conferir pacote/certificado e
   registrar recuperação local dos dados WoL; instalar somente com preservação
   de dados, sem desinstalar, limpar ou fazer downgrade automático.
4. No aparelho: validar WoL salvo, pareamento, credenciais, status real, modais,
   teclado/voltar, fontes ampliadas e áreas do sistema. Não há validação de UI
   em WebView real/API 26–36 nesta entrega. O Electron é uma verificação preliminar.
5. Manter grants zerados no teste inicial. Abrir Steam/CS2 ou testar suspensão
   exige autorização separada; esta entrega não repetiu as validações físicas.
6. Evoluir o dashboard Windows somente depois da revisão Android, sem substituir
   o backend ou suas identidades.

Reversão de desenvolvimento: reverter o commit isolado de integração em nova
branch/commit, sem resetar os checkpoints. Como nada foi instalado e nenhum
dado foi migrado, o Samsung não precisa de reversão. Depois de eventual
atualização, preferir correção assinada com versionCode maior; não presumir que
um downgrade preserve dados, nem desinstalar para contornar falhas de assinatura.
