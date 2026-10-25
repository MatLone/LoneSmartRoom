# Atualização controlada Windows dev.4 → dev.5 — 25/10/2026

**Instalação assistida concluída, sem abrir o Lone Smart Room.**
Uma única abertura do NSIS, uma confirmação de atualização, um clique em Instalar
e um clique em Concluir. Não houve execução do portátil, dashboard, widget,
runtime de monitoramento, sensores ou Named Pipe.

Horários abaixo em **America/Sao_Paulo (UTC−03:00)**. As evidências JSON mantêm UTC:

- 07:41:28: criação do novo backup protegido.
- 07:43:36: abertura da única sessão NSIS, PID 1480.
- 07:45:24: confirmação da substituição autorizada.
- 07:45:59: clique único em Instalar, no destino existente.
- 07:47:49: Concluir, sem opção de executar o aplicativo.
- 07:48:38–07:48:43: verificações de sistema e HTTPS após a instalação.

## Pré-verificação

- Instalação e registro identificavam **2.0.0-dev.4**. Nome registrado pelo NSIS:
  `Lone Smart Room 2.0.0-dev.4`; `appId=com.lone.smartroom` e destino preservados.
- Zero processos Electron do aplicativo, de monitoramento ou de instaladores
  residuais. Nenhum processo foi encerrado.
- Os hashes da instalação, dos 76 arquivos do perfil de produção e dos backups
  anteriores ainda coincidiam com o inventário aprovado durante a preparação dev.5.
- Agente original: supervisor 400, worker 8680, redirectors 17772/10996. Imagens,
  proprietário, parentesco e horários de criação foram verificados; não apenas PIDs.
- Listener único **8776 → 8680**. GETs autenticados de status/permissões: HTTP 200,
  TLS 1.3, validação de hostname/cadeia/pin antes de enviar autenticação.
- Zero grants e zero comandos pendentes; banco íntegro e identidades cifradas,
  revogações e esquema preservados. Não foi feito backup do banco do agente.

## NSIS utilizado

```text
<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\windows\desktop-dev5-monitoring-distribution-attempt2\Lone-Smart-Room-2.0.0-dev.5-x64-Setup-DEV.exe
```

SHA-256 recalculado antes da abertura:
`fe616c66c71f30f7d6c220b49864b60b6aba5cbd4c6ee0a14a76763ddf776c49`.
Tamanho: **105.525.755 bytes**. Versão **2.0.0-dev.5**, identidade oficial verificada.
Wrapper NSIS padrão x86 com payload Electron/runtime **x64**, igual à arquitetura
de distribuição preparada. Hash do arquivo completo corresponde exatamente ao
pacote autorizado e ao relatório de inspeção anterior.

A inspeção estática confirmou payload/ASAR, manifesto do runtime, ícone oficial,
instalação assistida por usuário, `asInvoker`, `allowElevation=false`,
`runAfterFinish=false`, `deleteAppDataOnUninstall=false`, confirmação explícita de
atualização e mesmo identificador. O desinstalador foi extraído estaticamente para
comparação, sem executá-lo como operação independente.

O pacote e o executável instalado permanecem **NotSigned**. Não foi observado
bloqueio de SmartScreen/Defender, pedido de elevação, solicitação de encerramento
de processos ou reinicialização. Nenhuma proteção foi desativada ou contornada.

## Backup novo, fora do Git

```text
<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev5-20261025T104128Z
  data/installation/  ← instalação dev.4 completa
  data/profile/       ← perfil Electron de produção completo
  manifest.json
  SHA256SUMS.txt
  RECOVERY-NOTES.txt
```

- **153 arquivos de dados**, **383.291.958 bytes**, **30 diretórios de origem**:
  77 arquivos da instalação e 76 do perfil.
- Cada arquivo de origem foi aberto exclusivamente para leitura antes da cópia.
  Não houve arquivo bloqueado, cópia forçada ou divergência.
- Hash SHA-256 antes/depois da origem, hash/tamanho da cópia e conjunto de caminhos
  verificados. A verificação independente confirmou a estrutura e todos os hashes.
- ACL da nova raiz sem herança externa; proprietário e acesso somente da conta
  autorizada. Filhos herdam essa restrição. **188 objetos** conferidos antes de instalar.
- Perfil copiado opacamente, sem descriptografar credenciais. Nenhum dado do agente,
  certificado privado ou dump foi incluído. Manifesto detalhado/inventários ficam
  no backup protegido ou cache ignorado, nunca no Git.
- SHA-256 do `manifest.json`:
  `0eada1b6a75dda44d146bbb32bd938b2faaff5cb3bb0a3aa5f91743a065ca408`.
- Após instalar, nova verificação confirmou todos os arquivos e o manifesto do
  backup. Os backups pré-dev.3 e pré-dev.4 também mantiveram seus hashes e ACLs:
  **783 objetos** verificados nos três backups, sem alterar suas permissões.

## Resultado estático da instalação

Destino e executável:
`<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe`.

- **FileVersion e versão registrada: 2.0.0-dev.5**. ProductVersion numérico PE
  continua `2.0.0.0`, como no pacote preparado; o ASAR identifica dev.5.
- **106 arquivos do payload** correspondem byte a byte ao diretório desempacotado
  aprovado. Total instalado: **108 arquivos**, incluindo desinstalador e seu ícone.
- Desinstalador corresponde ao bloco extraído do NSIS; seu ícone corresponde ao
  ICO oficial. O `debug.log` antigo da pasta de programas não permaneceu na nova
  instalação, mas está preservado integralmente no backup da dev.4.
- Hash do executável instalado:
  `b8f99a278afbed1729e4a2cd82fb1bd12d9644b6fc919a7c0d8943d718ebab1e`.
- Hash de `resources/app.asar`:
  `c4e81be7c9a5d09719996e2ccbcd6d09e50c937bf54003de8ab0af0595aa02dd`.
- Dezoito recursos ASAR conferidos, incluindo logo, ícone, preload, Tray, widget,
  modelos e componentes de monitoramento. Manifesto e arquivos do Python privado
  foram verificados por hash **sem executar o interpretador incluído**.
- CSP, `contextIsolation`, sandbox, `nodeIntegration=false`, API preload restrita
  e ausência de cliente operacional Electron–agente preservados.
- Atalho do Menu Iniciar aponta para o mesmo executável/destino. Foi apenas lido;
  não foi acionado nem salvo pela verificação.
- Os **76 arquivos do perfil** mantiveram conjunto e hashes. Preferências válidas
  no esquema 1, último modo `widget`, minimização automática para bandeja **desligada**.
  Dimensões e posição foram preservadas pelos mesmos arquivos; não houve importação
  de perfil de desenvolvimento ou migração de dados.

## Preservação e estado final

- **Zero processos Electron, monitoramento ou instaladores residuais.** O NSIS
  fechou; não houve primeira execução da dev.5.
- Comparação antes/depois: **34 entradas Run/RunOnce**, três arquivos de pastas
  Inicializar, **323 serviços**, **196 tarefas** e **708 regras persistentes de
  firewall** sem adições, remoções ou diferenças nas configurações comparadas.
  O XML das tarefas, incluindo as existentes, foi somente lido; não houve acesso
  para modificá-las. Não foi alterada OneSettings\RefreshCache.
- Fora da instalação explicitamente autorizada e da UI já preparada, **162 arquivos
  protegidos** mantiveram seus hashes. Não se reivindica que os antigos arquivos
  dev.4 do destino tenham permanecido inalterados: eles foram substituídos conforme
  autorizado e comparados separadamente ao payload dev.5.
- Backups anteriores pré-dev.3 (**341 arquivos**, com metadados) e pré-dev.4
  (**75 arquivos**, com metadados) intactos; novo backup completo e íntegro.
- Supervisor **400**, worker **8680** e redirectors continuam com as mesmas
  identidades e horários de criação. Listener único **8776 → 8680** preservado.
- GETs finais `/v2/status` e `/v2/apps`: **200/TLS 1.3**, certificado e pin válidos,
  `agent=online`, lista de aplicativos autorizados vazia. **Zero grants**, zero
  comandos pendentes, banco/identidades/esquema preservados. Credencial existente
  usada apenas em memória para esses GETs; nenhum segredo foi registrado.
- Android dev.7, WoL, pareamento, certificados, HMAC e executores não foram alterados.
  Não houve Steam, CS2, envio WoL, energia, drivers, login/logoff ou reinicialização.
- Pendências TLS e encerramento gracioso do agente continuam separadas e intactas.
  Nenhum teste físico de monitoramento foi realizado nesta atualização.

## Ocorrências dos verificadores — sem correção do aplicativo

1. O verificador inicial esperava DisplayName sem versão; o NSIS registra
   normalmente `Lone Smart Room 2.0.0-dev.4`. A comparação foi ajustada ao formato
   real e validada antes da instalação. Não houve divergência da identidade.
2. A leitura estática inicialmente recebeu LOCALAPPDATA redirecionado pelo sandbox
   e depois utilizou separadores inadequados na consulta ASAR do ícone. Ambas as
   verificações foram corrigidas no ferramental isolado e passaram antes de instalar.
3. O último mini-gate comparou string ISO com objeto DateTime convertido pelo
   PowerShell e sinalizou falsamente alteração do agente. Por falha no encadeamento
   do assistente, o NSIS foi aberto antes de consolidar esse gate. A ocorrência foi
   comunicada. O diálogo permaneceu aguardando, **sem confirmação de substituição**.
   Leitura independente confirmou horários/parentesco idênticos, versão instalada
   ainda dev.4, listener e zero grants; só então a atualização foi confirmada.
   A abertura única foi registrada; não houve relançamento do NSIS.
4. Após confirmar, o diálogo modal foi substituído pela janela principal do NSIS.
   A ferramenta precisou reobter o vínculo da janela; a confirmação não foi repetida.
5. A primeira comparação pós-instalação incluiu equivocadamente os arquivos de
   programas autorizados a mudar no conjunto imutável. As quatro diferenças eram
   exclusivamente `debug.log`, executável, desinstalador e ASAR. Nenhuma diferença
   fora da instalação. O checker separou corretamente o payload atualizado dos
   arquivos protegidos; a verificação completa passou.

Não houve falha do instalador nem necessidade de corrigir/reinstalar o aplicativo.
Os ajustes acima foram feitos somente em scripts de auditoria no cache ignorado,
sem alterar fontes funcionais, agentes, perfis ou permissões operacionais.

## Recuperação preparada — não executada

1. Caso seja necessário retorno, obter autorização específica e confirmar que
   Electron e seus próprios componentes estejam normalmente encerrados. Não tocar
   no agente HTTPS.
2. Preservar o perfil corrente numa nova cópia protegida antes de qualquer restauração.
   Verificar manifesto/hash acima e cada entrada de `SHA256SUMS.txt`, estrutura e ACL.
3. Usar o NSIS dev.4 preservado, SHA-256
   `e54710fa58103e8c0573f0d1dabbf7ed7e68b3abcc5eda3d85f4305ab32c3570`, após revisar a
   aceitação de versão anterior. Não executar instalador silencioso, desinstalação
   ou limpeza de userData para contornar erro. Não presumir downgrade de dados seguro.
4. Se necessária e autorizada, restaurar a estrutura da instalação e o perfil a
   partir de `data/installation` e `data/profile`, conservando a conta Windows
   original. Não descriptografar credenciais nem importar perfis demonstrativos.
   Verificar hashes e registro da instalação após a recuperação. Não restaurar o
   antigo `debug.log` como requisito para funcionamento; ele está guardado como histórico.

## Próxima etapa — exige nova autorização

Uma primeira execução controlada da **instalação dev.5** iniciará o monitoramento
local e o Named Pipe. Proposta: uma sessão de até 90 s, verificando dados reais de
CPU/RAM/C:/D:, estados nulos/validade, dashboard/widget/Tray, uso de recursos e saída
normal com ausência de processos residuais. Preservar o agente ativo e zero grants;
sem Steam, CS2, WoL, energia, temperaturas, GPU ou alterações de sistema.

**Essa execução não foi autorizada nem realizada nesta etapa.** Checkpoints
`c368c4e`, `74d942e`, `0a73b70`, `af2d6d6`, `216dcba` e `3abd308` continuam ancestrais.
Esta entrega acrescenta somente documentação sanitizada ao Git.
