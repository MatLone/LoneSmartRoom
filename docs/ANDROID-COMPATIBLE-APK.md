# APK Android 2.0 compatível — 2026-10-23

Atualização posterior: este candidato foi instalado após autorização expressa,
com WoL preservado e HTTPS validado no Samsung. Veja
[SAMSUNG-INSTALLATION.md](SAMSUNG-INSTALLATION.md). Abaixo permanece o registro da preparação.

## Artefato preparado, sem instalação

- Pacote: `com.lonesmartroom.app`.
- Versão: `2.0.0-dev.1`, versionCode **15** (instalado: 14).
- APK estável para revisão: `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.1-v15.apk`.
- SHA-256 do APK: `62188be1557c1c7097fac88cf7efcef8e397fa4fdd83c52b79e3c5fa1f6f539f`.
- SHA-256 do certificado: `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
- `apksigner verify --verbose --print-certs`: passou, incluindo assinatura v2.
- Tipo: build **debug**, para validação local; não é uma distribuição de produção.

A assinatura corresponde exatamente ao certificado do APK 1.4 instalado no
Samsung, verificado por ADB na tarefa anterior. O keystore original foi utilizado
diretamente no local original, fora do repositório. A assinatura bem-sucedida e a
verificação do APK comprovam agora o acesso utilizável à chave correspondente.
Não foram copiados arquivos de assinatura, senhas ou chaves privadas para o
repositório, logs ou relatórios.

## Compilação e verificação reproduzíveis

Na raiz do repositório, executar localmente no perfil Windows proprietário da chave:

```powershell
.\scripts\prepare-compatible-apk.ps1
.\scripts\test-safe.ps1
.\scripts\test-android-packet.ps1
.\.venv\Scripts\python.exe -B scripts\verify-preservation.py
```

O primeiro script roda Gradle offline, `assembleDebug` e `lintDebug`; exige caches,
SDK e JDK já preparados. Não instala dependências nem APKs. O opt-in
`-OriginalSigning` utiliza a chave debug original por uma variável de ambiente
temporária contendo somente seu caminho. A variável é restaurada ao terminar.
As credenciais padrão de assinatura debug são fornecidas em memória pelo AGP;
não foram adicionadas a scripts ou arquivos de configuração. Uma chave protegida
por credencial diferente exigirá entrada local protegida e revisão, sem gravá-la.

Builds comuns continuam usando a chave isolada. Portanto, o APK genérico de
`build/outputs` pode ser substituído por um build incompatível no futuro: usar o
artefato estável acima e conferir seu hash/certificado antes de qualquer instalação.
O verificador recusa certificado divergente, versão/pacote inesperado, assinatura
v2 ausente, recuperação alterada ou assets diferentes dos fontes revisados.
Não sobrescreve um candidato existente se seu conteúdo mudar; preservar candidatos
anteriores e definir uma nova versão nesse caso. Não se promete determinismo byte
a byte entre máquinas, ferramentas ou ambientes diferentes.

## Preservação e segurança

Nenhuma mudança em `WakeOnLan.kt`, `app.js`, ponte WakeBridge, chave
`lone-wol-settings-v1` ou manifest original. A origem WebView permanece
`file:///android_asset/index.html`, DOM storage habilitado, mesmo pacote e sem
mudança de diretório WebView. O build empacota os mesmos assets revisados. Não há
migração, limpeza ou importação automática do armazenamento WoL nesta versão.
Isso preserva o contrato de armazenamento; a persistência no aparelho ainda deve
ser conferida antes/depois da atualização autorizada.

O APK inclui o pareamento e status HTTPS já implementados. A identidade do servidor
exige pin SHA-256 do certificado, validade, assinatura própria, EKU serverAuth e
validação padrão de hostname/SAN; não há trust-all, redirecionamentos ou liberação
global de HTTP. A confirmação da identidade ocorre no diálogo nativo. Código
temporário, HMAC, identidade individual, nonces e revogação continuam ativos.

No Android, `AgentVault` mantém a chave AES-256 no Android Keystore e os dados
criptografados com AES-GCM em `noBackupFilesDir`, separados do WebView/WoL.
No Windows, as credenciais são protegidas por DPAPI do usuário. A proteção Android
foi revisada nos fontes e compilada; uso real do Keystore no Samsung ainda não
foi exercitado nesta etapa. Testes JVM não substituem esse teste no aparelho.
O canal seguro só expõe pareamento e consulta de status; rotas de energia continuam
recusadas, sem executor real de comandos conectado ao cliente Android.

## Resultados

- Build offline `assembleDebug` e `lintDebug`: passaram.
- Lint: zero erros, cinco avisos existentes: versão de Gradle, orientação de tela,
  JavaScript na WebView, X509TrustManager customizado e regras de extração Android.
  Não foram silenciados. A WebView continua local, e o pinner é coberto pelos
  testes; regras de transferência/backup em versões recentes ainda merecem revisão.
- Suite segura: 21 testes passaram, mais o teste legado com executor mock.
  Cobertura: credenciais incorretas/ausentes, replay persistido, pareamento expirado
  e uso único, revogação, certificado/pin/hostname/validade, falha de conexão,
  HTTP recusado, perfil Público bloqueado, origem fora da LAN e rotas de ação 404.
  As classes de pinagem Java e HMAC/status Kotlin de produção foram exercitadas
  contra HTTPS local real. Nenhum comando de energia foi executado.
- WoL Kotlin de produção: pacote de 102 bytes, MAC, normalização e rejeição de
  entradas inválidas passaram; nenhum pacote UDP foi enviado.
- Preservação: 86 registros de originais e recuperação passaram; hashes dos fontes
  protegidos e WakeBridge conferidos contra a base.
- Verificação do APK: pacote, versão, assets, certificado e assinatura v2 passaram.
- Nenhum ADB, instalação, desinstalação ou acesso aos dados do Samsung nesta tarefa.
  Não houve alteração de firewall, perfil de rede, roteador ou agente ativo.

## Recuperação e próxima autorização

O APK 1.4 funcional permanece em
`recovery/artifacts/android/intermediates/apk/debug/app-debug.apk`, com SHA-256
`ea0c3a74f859f97e7d4e3a80d23525e2137a3d1add94f21d09e1746611e245d7`,
assinatura original verificada e identidade byte a byte com o APK extraído do
Samsung. A cópia extraída permanece em `.cache/signing/samsung-installed-base.apk`.
O commit-base `ed0fdae90db78d721444b29ee7d9ac49c21f73df`, os snapshots e bundles
de recuperação não foram modificados. O APK é backup do programa, não dos dados.

Antes de autorizar a instalação, conferir as configurações WoL atuais e definir
uma cópia local protegida dos valores necessários, sem exportar credenciais.
Não foi criado backup dos dados do aplicativo nesta tarefa; `allowBackup=false`
não autoriza presumir recuperação por backup Android padrão ou transferência OEM.
Atualização deve preservar o pacote e os dados, sem desinstalação ou limpeza,
após reconfirmar o certificado do aplicativo instalado e o hash deste candidato.

Se houver regressão, interromper os testes e preservar os dados atuais. A opção
preferida é corrigir com nova atualização de versionCode maior e mesma assinatura.
Para recuperar o comportamento 1.4, pode-se preparar, em área separada dentro do
repositório, um build dos fontes preservados com versionCode maior que o instalado,
mesma assinatura e revisão da compatibilidade dos dados. Isso exige uma nova
aprovação antes de instalar. Não executar downgrade forçado, reinstalação limpa
ou restauração indiscriminada. O APK antigo sozinho não garante recuperar dados,
e um downgrade não é presumido seguro nem autorizado.

Somente após autorização explícita: atualizar, conferir todos os valores WoL,
testar pareamento com conferência de fingerprint, status real pelo Wi-Fi e
revogação. Teste físico WoL e Android Keystore no Samsung continuam pendentes.

Recibo público: `android-compatible-build.json`. O relatório
`SAMSUNG-VALIDATION.md` documenta o APK incompatível anterior, já superado por este
candidato separado e verificado. Nenhuma instalação está autorizada por este documento.
