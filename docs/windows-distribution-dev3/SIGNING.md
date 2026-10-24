# Authenticode — situação e requisitos futuros

Setup, Portable, aplicativo e desinstalador desta entrega **não estão assinados**. A inspeção PE encontrou tabelas de certificados vazias; `Get-AuthenticodeSignature` confirmou NotSigned nos três EXEs externos inspecionados. São builds de desenvolvimento para uso local. Não há identidade de publicador validada por esses pacotes.

Nenhum certificado foi criado, adquirido, importado ou procurado no repositório para assinar Windows. Nenhuma assinatura foi simulada. A chave Android e a identidade TLS do agente não devem ser reutilizadas como identidade Authenticode. Os dados de assinatura foram removidos apenas do ambiente do processo de build e restaurados ao terminar, sem exibir valores.

Para uma futura distribuição, definir o publicador legal e obter certificado de code signing apropriado de uma autoridade confiável ou serviço gerenciado com elegibilidade confirmada. Proteger a chave fora de Git e do pacote, com controle de acesso e mecanismo seguro do fornecedor. Custos, disponibilidade e requisitos de validação precisam ser avaliados naquele momento; não houve compra ou cadastro nesta tarefa.

Integrar a assinatura ao pipeline para EXE da aplicação, desinstalador e wrappers finais, com timestamp confiável e digest SHA-256. Exigir falha na build de distribuição se a assinatura faltar. Validar cadeia, revogação, timestamp e política Authenticode antes de liberar; calcular novos hashes somente após assinar. O [Microsoft SignTool](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool) permite assinar, carimbar tempo e verificar esses atributos; o [timestamp Authenticode](https://learn.microsoft.com/en-us/windows/win32/seccrypto/time-stamping-authenticode-signatures) faz parte dessa revisão.

Não desativar SmartScreen/Smart App Control/antivírus, não tratar hash local como assinatura e não garantir ausência de alertas apenas por obter certificado. Qualquer bloqueio real exige análise antes de prosseguir.
