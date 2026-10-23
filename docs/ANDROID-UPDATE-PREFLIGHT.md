# Atualização controlada — verificação antes da autorização

Atualização posterior: o usuário autorizou expressamente o comando; instalação,
preservação WoL e comunicação HTTPS reais foram validadas. Consulte
[SAMSUNG-INSTALLATION.md](SAMSUNG-INSTALLATION.md). O restante registra o preflight histórico.

Data: 2026-10-23. Branch: `feature/secure-pairing-status`.
**Procedimento interrompido antes da instalação. Autorização expressa pendente.**

## Configurações atuais preservadas

O Samsung SM-S731B continua conectado por ADB sem fio. A instalação atual permanece
`com.lonesmartroom.app`, versão 1.4.0, código 14. O aplicativo não foi aberto,
interrompido ou alterado para esta inspeção.

A entrada salva `lone-wol-settings-v1` da origem `file://` foi lida usando
`run-as` permitido pelo pacote DEBUGGABLE. Foram extraídos somente os campos
MAC, broadcast e porta UDP. Eles foram validados e salvos, sem exibição de valores,
em um arquivo criptografado por DPAPI do usuário Windows atual:

`recovery/device-settings/samsung-wol-20261023T134711892134Z.dpapi`

SHA-256 do arquivo criptografado:
`3ed0e4ebc90430b6905474e3f71c9acac7818153de52e2af02d8eda1a0489384`.

O backup gravado foi descriptografado em memória e comparado integralmente com o
conteúdo selecionado. Nenhum valor WoL, credencial ou banco bruto foi gravado em
texto claro ou incluído no Git. Dados de outras entradas passaram apenas pela
memória necessária à leitura do WAL e não foram exportados. Duas leituras do WAL
e da listagem coincidiram; os checksums CRC32C foram conferidos.

O script `scripts/backup-wol-readonly.py` suporta somente o layout observado:
um WAL e nenhum SST/arquivo compactado. Recusa formatos desconhecidos, dados
incompletos, corrupção, chave apagada ou schema inesperado. Cinco testes com
dados sintéticos passaram, incluindo CRC conhecido, fragmentação, último valor,
origem divergente e rejeição de corrupção/exclusão.

Esse é um backup dos três valores WoL, não um backup completo do aplicativo.
A recuperação depende do perfil Windows proprietário e do DPAPI utilizável.
Se necessário, ler/descriptografar localmente em memória e reintroduzir somente
esses campos pela interface do aplicativo, sem publicar os valores ou sobrescrever
o banco LevelDB. Não há restauração automática nem autorização para escrever no
Samsung. Se o usuário editar as configurações antes da atualização, repetir a
inspeção e preservar uma nova cópia, sem apagar a anterior.

Referências do leitor: [formato WAL LevelDB](https://github.com/google/leveldb/blob/main/doc/log_format.md),
[WriteBatch](https://github.com/google/leveldb/blob/main/db/write_batch.cc),
[CRC32C](https://github.com/google/leveldb/blob/main/util/crc32c.h) e
[schema Chromium localStorage](https://github.com/chromium/chromium/blob/140.0.7339.0/components/services/storage/dom_storage/local_storage_impl.cc).

## APK e contrato de armazenamento

Foi extraída outra cópia do APK atualmente instalado para
`.cache/update-preflight/installed-v14.apk`. Seu hash continua idêntico ao APK
funcional de recuperação:
`ea0c3a74f859f97e7d4e3a80d23525e2137a3d1add94f21d09e1746611e245d7`.

O candidato continua sendo
`.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.1-v15.apk`, com pacote
`com.lonesmartroom.app`, versionName `2.0.0-dev.1` e versionCode **15**.
SHA-256 do candidato:
`62188be1557c1c7097fac88cf7efcef8e397fa4fdd83c52b79e3c5fa1f6f539f`.

As assinaturas dos dois APKs foram verificadas novamente com `apksigner`.
Ambos apresentam exatamente o certificado:
`02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
O candidato não contém o atributo `testOnly`, portanto não requer a opção `-t`.

O diretório atual é `/data/user/0/com.lonesmartroom.app`. O pacote, a URL
`file:///android_asset/index.html`, o DOM storage, a chave WoL e o contrato de
diretório WebView continuam iguais. Não há troca de origem/perfil nem rotina nova
de limpeza ou migração dos dados existentes. Os assets do APK foram comparados
com os fontes revisados; cinco testes de preservação passaram e os 86 registros
de originais e recuperação continuam íntegros. Não houve recompilação ou mudança
nos fontes funcionais nesta tarefa.

`install -r` solicita substituição mantendo os dados do pacote. A compatibilidade
prévia foi conferida; a persistência efetiva dos valores só poderá ser confirmada
depois da atualização autorizada, antes de executar o teste físico de WoL.

## Comando preparado — não executado

```powershell
& "<USERPROFILE>\AppData\Local\Android\Sdk\platform-tools\adb.exe" -s "adb-RXCYA00SRWB-c012Pr._adb-tls-connect._tcp" install -r "<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\android\LoneSmartRoom-2.0.0-dev.1-v15.apk"
```

Antes de executá-lo, obter autorização expressa e reconfirmar aparelho, hashes,
certificados e versão instalada. Se o transporte ADB mudar, confirmar o mesmo
aparelho e registrar o comando correspondente antes de instalar. Se houver
qualquer erro de assinatura, interromper. Não desinstalar, limpar dados, forçar
substituição ou usar downgrade como correção.

## Sequência após autorização e atualização

1. Conferir os valores WoL persistidos contra o backup protegido, antes de enviar
   qualquer pacote. Se divergirem, interromper os testes e revisar a recuperação.
2. Validar o despertar físico do PC em condição apropriada, coordenada com o
   usuário. Não desligar/suspender o PC automaticamente para preparar esse teste.
3. Parear HTTPS pela LAN autorizada, comparando o fingerprint com o Windows por
   um canal confiável, sem registrar o código temporário.
4. Consultar status real e última comunicação; ausência de resposta não confirma
   PC desligado. Conferir falhas, revogação e armazenamento protegido Android.
5. Manter bloqueados desligamento, reinicialização, suspensão e execução remota
   de aplicativos. Nenhum desses comandos foi executado nesta preparação.

Recibo público sem valores: `android-update-preflight.json`.
Plano geral de recuperação do APK: `ANDROID-COMPATIBLE-APK.md`.
