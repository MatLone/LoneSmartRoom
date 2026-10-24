# Atualização proposta — não executada

Alvo: mesmo Galaxy S25 FE e pacote `com.lonesmartroom.app`; candidato dev.5 / código 19. Exige autorização expressa após revisão das imagens, da diferença da splash nativa e da pendência TLS relatada. Não executar este procedimento apenas por abrir este documento.

1. Confirmar ADB autorizado, aparelho correto e versão instalada. Se a versão atual divergir do v18 validado anteriormente, reavaliar a atualização.
2. Revalidar hash do APK final e certificado original, além do certificado da instalação viva. Interromper em caso de divergência.
3. Registrar estado, ler somente os dados WoL necessários e preservar recibos/cópias protegidos pelo mecanismo existente, sem publicar MAC, broadcast ou credenciais. Não exportar chaves do AndroidKeystore.
4. Após autorização expressa, executar exatamente uma atualização, com o serial confirmado no momento:

```powershell
& '<USERPROFILE>\AppData\Local\Android\Sdk\platform-tools\adb.exe' -s '<SERIAL_VALIDADO_NO_MOMENTO>' install -r '<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\android\LoneSmartRoom-2.0.0-dev.5-v19.apk'
```

5. Se houver erro, parar; não desinstalar, limpar dados, fazer downgrade ou repetir automaticamente. Não usar `-d` ou `pm clear`.
6. Em caso de sucesso, conferir v19/certificado, identidade de dados, valores WoL preservados, ícone, splash e três abas. Consultar apenas status/permissões; confirmar pareamento existente, HTTPS autenticado e zero grants.
7. Não enviar WoL nem abrir Steam/CS2 nesta validação; esses testes dependem de autorização separada. Não alterar permissões ou reiniciar o agente como parte da atualização visual.

SHA-256 final: `1acb6d927a3c8db3bb0f0a6be754d442b603a4b3b526dd79cc447e8235abd7e1`.

Certificado SHA-256: `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.

Recuperação: v18 e versões anteriores permanecem em `.cache/artifacts/android/`; APKs extraídos e backups protegidos do aparelho permanecem nos locais registrados na validação física dev.4. Uma cópia de APK ou do cofre cifrado não garante restauração de todos os dados nem das chaves Keystore. Não se presume segurança de downgrade automático.
