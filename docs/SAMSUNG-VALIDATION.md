# Validação do Samsung — 2026-10-23

## Identificação e verificação somente leitura

ADB sem fio encontrou o Samsung SM-S731B (Galaxy S25 FE informado pelo usuário),
Android 16 / API 36, na LAN autorizada. O pacote instalado é
`com.lonesmartroom.app`, versão 1.4.0, versionCode 14, minSdk 26 e targetSdk 35.
O pacote é de desenvolvimento (DEBUGGABLE / TEST_ONLY).

Somente metadados do pacote e seu APK foram lidos. A cópia está em
`.cache/signing/samsung-installed-base.apk`, ignorada pelo Git. Essa cópia contém
o programa, **não é backup dos dados ou das configurações do aplicativo**.
Não houve instalação, abertura do aplicativo, desinstalação, limpeza, leitura de
dados privados do aplicativo, modificação das configurações de rede ou envio WoL.

`apksigner verify --print-certs` verificou os três APKs com sucesso:

| APK | SHA-256 do certificado público |
| --- | --- |
| Instalado no Samsung | `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8` |
| Recuperado funcional | `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8` |
| Nova compilação 2.0 atual | `d446fc2d0afa14b7e64a561d897e908304df6a1c3fa3376f55ae4d78288fa313` |

O APK instalado e o recuperado são idênticos byte a byte:
SHA-256 `ea0c3a74f859f97e7d4e3a80d23525e2137a3d1add94f21d09e1746611e245d7`.
A nova compilação tem hash
`fdd823f8aaac8be256d5ed4b2dca094e39be44c330d30e6b384e92bb2454f1e9`.

**O APK 2.0 atual é incompatível para atualização. Não instalar.** Ele usa a chave
isolada de desenvolvimento, conforme configurado na etapa 1.

O arquivo original `%USERPROFILE%\.android\debug.keystore` continua disponível
(2618 bytes). A auditoria anterior já verificou que seu certificado corresponde
ao APK recuperado; a comparação atual prova que esse APK também corresponde ao
instalado. Nesta validação o keystore não foi desbloqueado novamente. A consulta
sem senha não forneceu o certificado, portanto não conta como nova prova de
acesso à chave privada. Nenhuma senha ou chave privada foi exibida ou registrada.

## Plano seguro de compatibilização e atualização

1. Revisar este resultado antes de prosseguir com assinatura. Não trocar o
   identificador, desinstalar, limpar dados ou tentar instalar o APK incompatível.
2. Preparar um artefato separado assinado com a chave original, usando mecanismo
   local protegido para a credencial, sem copiar o keystore para o projeto/Git.
   Confirmar acesso à chave e repetir a verificação do certificado do artefato.
   Não é necessário migrar o armazenamento para outro pacote: a identidade original
   pode ser preservada se a chave continuar utilizável.
3. Manter `com.lonesmartroom.app`, a origem da WebView, a chave localStorage
   `lone-wol-settings-v1`, o emissor Kotlin e a ponte JavaScript WoL. Conferir
   versionCode e as condições de atualização do pacote TEST_ONLY. Não reduzir a
   versão nem usar substituição forçada como contorno de assinatura.
4. Antes da instalação, conferir os valores WoL no aplicativo e definir uma cópia
   de recuperação local protegida desses valores. `allowBackup=false` impede
   presumir que o backup padrão do Android assegure recuperação. Não exportar
   indiscriminadamente dados privados, credenciais ou diretórios da aplicação.
   A cópia do APK não garante recuperação das configurações. Não foi criada uma
   cópia das configurações nesta tarefa.
5. Repetir build/lint e testes de preservação no artefato compatível. Registrar
   hash e certificado e solicitar confirmação explícita do usuário para instalar
   como atualização, preservando dados. **Nenhuma instalação está autorizada por
   este relatório.** Se a chave original não puder ser utilizada, interromper e
   recuperar a chave correta; um novo pacote com migração/exportação explícita
   exigirá um plano separado e aprovação, mantendo o aplicativo original.
6. Após confirmação, atualizar sem desinstalação ou limpeza. Conferir os valores
   WoL antes de qualquer teste físico. Preservar os backups e não presumir que
   reinstalar o APK antigo restaure os dados em caso de falha.
7. No Wi-Fi autorizado, iniciar o pareamento no Windows, conferir URL e fingerprint
   pelo canal local confiável e usar o código temporário sem registrá-lo. Verificar
   status autenticado real, última comunicação, desconexão sem indicar PC desligado,
   revogação e rejeição de nova consulta. Manter comandos de energia bloqueados.

## Testes e limites

- Preservação: 86 registros de originais e cópias de recuperação passaram.
- Pacote WoL Kotlin de produção: tamanho/conteúdo, normalização de MAC e rejeição
  de entradas inválidas passaram na JVM, sem envio UDP.
- Revisão do índice Git verifica hashes dos fontes protegidos e igualdade da ponte
  WakeBridge com o commit-base. Nenhum fonte funcional foi alterado nesta tarefa.
- Nenhum build foi repetido: os APKs existentes foram verificados, sem mudança de
  código/configuração. Os builds anteriores não substituem a validação do futuro
  APK assinado com a chave original.
- Pareamento/status no Samsung, travessia Wi-Fi–Windows e funcionamento físico WoL
  após atualização permanecem pendentes. Os testes locais anteriores não comprovam
  esses resultados no aparelho. Não houve teste de comandos de energia.

Evidência estruturada sem credenciais: `signing-investigation.json`.
