# Procedimento futuro de atualização e recuperação

**Plano; não executado.** Não contém autorização para instalar, abrir o aplicativo ou restaurar dados. Referência: [relatório de pré-instalação](README.md).

## Antes da atualização autorizada

1. Revalidar dev.3, GUID `49c682c0-0c26-5957-855e-4881f73b25df`, appId `com.lone.smartroom` e destino `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room`. Parar em caso de divergência ou outra instalação.
2. Confirmar que nenhum Electron do Lone está ativo. Se estiver, solicitar encerramento normal pelo usuário; não forçar. Não iniciar nem encerrar o agente.
3. Revalidar o backup privado abaixo. Se o perfil tiver mudado, obter snapshot atualizado com a mesma proteção e verificação antes de instalar. Preservar todos os anteriores.
4. Conferir SHA-256 e tamanho do NSIS dev.4. Não usar o portátil, não recompilar/substituir o artefato silenciosamente.
5. Registrar o estado do perfil e zero grants antes da atualização, sem revelar conteúdo ou credenciais. O agente offline deve continuar registrado separadamente; sua inicialização não faz parte do procedimento.

### Verificação de backup somente leitura

Executar no repositório, com a conta Windows original:

```powershell
& '.\docs\windows-dev4-preflight-2026-10-24\Verify-ProfileBackup.ps1' `
  -BackupRoot '<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev4-20261024T174801Z' `
  -ExpectedManifestSha256 '13c12ff4d0e896dda9915b4d8d9b337aa480565059e844ac6bc41a9932444dcc'
```

Esperado: `ok=True`, 72 arquivos, 8.589.376 bytes, 27 diretórios, hashes e ACLs privados válidos. Interromper se houver divergência. Não descriptografar o perfil para verificar o backup.

## Instalação futura, somente após autorização específica

1. Abrir uma única vez o NSIS assistido:

   `<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\windows\desktop-dev4-tray-distribution\Lone-Smart-Room-2.0.0-dev.4-x64-Setup-DEV.exe`

   SHA-256: `e54710fa58103e8c0573f0d1dabbf7ed7e68b3abcc5eda3d85f4305ab32c3570`; 101.606.566 bytes. Sem parâmetros de instalação silenciosa, exclusão de dados ou execução automática. Esta linha é apenas identificação do arquivo, não foi executada.
2. Manter proteções do Windows. Se SmartScreen, Defender, política ou pedido inesperado de elevação impedir o processo, parar e registrar; não contornar.
3. No assistente, confirmar atualização da instalação existente somente sob a autorização específica, para o mesmo destino por usuário. Resposta padrão à substituição é Não. Se destino/identidade/opções divergirem, cancelar.
4. O NSIS pode chamar internamente o desinstalador antigo com preservação de dados para substituir arquivos. Não iniciar manualmente o desinstalador, não apagar perfil e não fornecer `--delete-app-data`.
5. Não selecionar/forçar abertura do aplicativo ao concluir. `runAfterFinish:false` já está configurado. Não criar autostart, serviços ou regras de firewall.

## Inspeção posterior antes da primeira abertura

1. Confirmar executável dev.4 no mesmo destino, appId/GUID, metadados e ícone oficial. Comparar EXE com SHA-256 `5b0251e693f1915b3736cdee120cf68ccc5725489439f383cb9053a0aa5634bb` e ASAR com `c225aa0f9bfde8cc3575170eb3dd3fedeac301b00dbf0aeb18868828c6b7b447`, além do manifesto do payload.
2. Confirmar que o perfil permaneceu no mesmo caminho e comparar arquivos/hashes com o retrato imediatamente anterior à instalação. Antes da primeira abertura não há motivo esperado para migração pelo Electron.
3. Verificar preservação de backups, atalhos, ausência de autostart novo e zero grants. Conferir estado da porta 8776 sem iniciar o agente ou testar ações reais.
4. Registrar avisos e eventos relevantes. Se dados, identidade ou segurança divergirem, parar; não tentar corrigir com exclusão de dados, reinstalações repetidas ou rollback automático.
5. Solicitar autorização separada para a primeira execução dev.4: uma sessão visual, dashboard/widget/bandeja, X normal e Sair completo; sem cliente operacional, Steam, CS2, WoL ou energia. Observar a pendência Error e capturar texto/PID/horário se reaparecer.

## Recuperação futura, somente se necessária e autorizada

No estado atual não há alteração instalada a reverter: dev.3 permanece íntegra.

1. Encerrar Electron normalmente com o usuário. Preservar uma cópia privada adicional do perfil então existente e da evidência do problema antes de qualquer restauração. Não encerrar à força, apagar ou mesclar dados às cegas.
2. Verificar novamente backup e NSIS dev.3 preservados. O instalador anterior está em:

   `<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\windows\desktop-dev3-distribution\Lone-Smart-Room-2.0.0-dev.3-x64-Setup-DEV.exe`

   SHA-256 `c405093ec9f45fbee8abedd3fbba103d53292cb7b57a901d5969cc74d73d0000`.
3. Avaliar primeiro o defeito e se apenas o binário necessita retorno. Instalação assistida da versão anterior exige autorização específica e aceitação da política de versão do NSIS. Se bloqueada, parar e rever o plano; não forçar downgrade ou desinstalação. Não presumir que um retorno de versão preserve automaticamente a compatibilidade do perfil.
4. Restaurar o perfil **somente se necessário**, com Electron fechado, usando o snapshot `Windows-before-dev4-20261024T174801Z\data\profile` verificado, na mesma conta Windows e caminho original. Planejar a substituição controlada do diretório preservando o perfil mais recente em local protegido, em vez de apagá-lo ou misturar LevelDB. Revalidar hashes e ACLs após a operação. Este relatório não executa essa restauração nem fornece comando destrutivo automático.
5. Não importar os perfis demonstrativos de `Windows-before-dev3-20261024T145523Z`. Não restaurar dados do agente ou Android como parte do Electron. Credenciais protegidas podem depender da conta/máquina original; não exportar segredos em texto.
6. Confirmar integridade, versão e dados antes de uma abertura futura autorizada. Manter todos os checkpoints e pacotes. Para revisão de código usar commits/checkouts separados; não aplicar `reset --hard` ou limpeza destrutiva no projeto atual.

Nenhuma recuperação, instalação, abertura ou mudança no sistema foi executada por este documento.
