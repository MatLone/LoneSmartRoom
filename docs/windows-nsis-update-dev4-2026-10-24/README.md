# Atualização instalada Windows dev.4 — 24/10/2026

**Atualização NSIS assistida concluída e arquivos verificados. O dashboard não foi executado.** Instalação alterada de `2.0.0-dev.3` para `2.0.0-dev.4`, exclusivamente pelo NSIS já preparado e expressamente autorizado. O agente HTTPS não foi iniciado ou reiniciado.

Branch `feature/ui-migration-preview`, sobre o commit documental `c635d4856b83460d5adb4983fb5fe4c668aed102`. Preservados `3d56561`, `ced82d0`, os demais checkpoints e backups. Não houve alteração do código funcional, compilação nova, execução do portátil ou importação de perfil demonstrativo. Este commit registra somente a instalação autorizada e suas evidências.

## Preparação repetida

Às **16:54:24 (UTC−03:00)**, antes de iniciar o NSIS:

- Versão do arquivo e registro de desinstalação: `2.0.0-dev.3`; destino registrado correto.
- Zero processos Electron, zero processos do agente e nenhum listener em 8776.
- NSIS com 101.606.566 bytes e SHA-256 exato `e54710fa58103e8c0573f0d1dabbf7ed7e68b3abcc5eda3d85f4305ab32c3570`.
- 1.257 arquivos previamente protegidos revalidados, sem divergências; zero grants por consulta SQLite somente leitura.
- Backup `Windows-before-dev4-20261024T174801Z` novamente aprovado: 72 arquivos, 27 diretórios, 8.589.376 bytes, hashes/tamanhos e ACLs restritas ao usuário corretos.
- Retratos somente leitura das entradas Run/RunOnce, pastas de inicialização, configurações dos serviços, XML das tarefas e regras persistentes do firewall. Nenhuma configuração foi alterada por esses levantamentos.

O perfil de produção continuava igual ao snapshot; não foi necessária nova cópia nem encerramento de processos.

## Execução assistida

Foi enviado **um único comando de abertura** do arquivo:

`<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\windows\desktop-dev4-tray-distribution\Lone-Smart-Room-2.0.0-dev.4-x64-Setup-DEV.exe`

Sem parâmetros silenciosos ou de abertura do aplicativo. O assistente exibiu `Instalando`, com produto e versão dev.4. O usuário confirmou posteriormente que interagiu manualmente no assistente. Nenhum clique de instalação ou de abertura do dashboard foi enviado pelas ferramentas de automação.

A janela transitou entre identificadores e encerrou antes de capturar a página final; a captura disponível é [a etapa Instalando](screenshots/nsis-installing.png), não uma captura de conclusão. O código de saída do NSIS não foi obtido pela API de abertura. A conclusão é sustentada pela nova versão registrada, arquivos instalados correspondentes ao payload e ausência de processos remanescentes, sem presumir um exit code 0 não observado.

Não foi observado aviso de bloqueio de segurança nas capturas disponíveis. Nenhuma proteção foi desabilitada ou contornada. O pacote e o executável instalado continuam **sem assinatura Authenticode (`NotSigned`)**.

## Resultado da inspeção instalada

| Item | Resultado |
|---|---|
| Executável | `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe` |
| Versão / produto | `2.0.0-dev.4` / Lone Smart Room, incluindo DisplayVersion registrado |
| Identidade | `com.lone.smartroom`; pacote `lone-smart-room`; GUID NSIS `49c682c0-0c26-5957-855e-4881f73b25df` preservado |
| Arquivos da aplicação | **74 arquivos** iguais ao payload revisado, por SHA-256 |
| Total instalado | 76 arquivos: 74 do payload + desinstalador e `uninstallerIcon.ico` esperados |
| EXE SHA-256 | `5b0251e693f1915b3736cdee120cf68ccc5725489439f383cb9053a0aa5634bb` |
| ASAR SHA-256 | `c225aa0f9bfde8cc3575170eb3dd3fedeac301b00dbf0aeb18868828c6b7b447` |
| Bandeja / marca | Módulos desktop-main/window/preferences/policy, preload, ICO/PNG oficial e logo horizontal presentes e idênticos às fontes revisadas |
| Segurança estática | contextIsolation habilitado, nodeIntegration desabilitado, sandbox e CSP sem rede operacional; bloqueio de instância única presente |
| Atalho Menu Iniciar | Existe, destino correto, sem argumentos, diretório de trabalho correto, ícone do executável instalado |
| Perfil de produção | **72 arquivos com os mesmos hashes e mesmo conjunto de caminhos** |
| Preferência visual dev.4 | `desktop-window-state.json` continua ausente; nenhum perfil de primeira execução ou preferência automática de bandeja foi criado |

Atalho verificado:

`<USERPROFILE>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Lone Smart Room.lnk`

Perfil preservado:

`<USERPROFILE>\AppData\Roaming\Lone Smart Room`

Os recursos de bandeja foram inspecionados **sem executar o código instalado**. A aparência na bandeja, restauração, menu e encerramento em runtime continuam pendentes do primeiro teste físico autorizado.

## Preservação e estado final

- **1.181 arquivos protegidos fora da instalação permanecem idênticos**, incluindo perfil, backups anteriores, pacotes, código do projeto, Android e material do agente. Os 76 arquivos da instalação foram separados dessa comparação porque são o alvo autorizado da atualização.
- Configurações de serviços, tarefas agendadas, regras persistentes de firewall, entradas Run/RunOnce e arquivos das pastas de inicialização com os mesmos retratos antes/depois. Nenhuma entrada de autostart Electron foi criada. Entrada existente do agente preservada; sem interferência na tarefa OneSettings\RefreshCache.
- Novo backup de produção revalidado após a atualização, com hashes e permissões privados corretos. Manifesto esperado: `13c12ff4d0e896dda9915b4d8d9b337aa480565059e844ac6bc41a9932444dcc`.
- **86 registros de originais e cópias de recuperação aprovados** pelo verificador do projeto.
- Zero grants; nenhum Steam, CS2, WoL ou comando de energia executado. Sem alterações no Android, certificados, credenciais, HMAC, pareamento, drivers ou rede.
- Consulta final às **16:58:11 de 24/10/2026**: zero Electron, zero processo NSIS dev.4, zero processo do agente e zero listener 8776.
- Nenhum evento Application 1000/1001/1002/1026 correlacionado aos componentes consultados desde o retrato pré-instalação. Isso não substitui teste de runtime.

**Agente permanece offline**, como antes; não houve tentativa de corrigi-lo. A investigação da inicialização pós-reboot e a pendência de tratamento TLS excessivo/ambíguo continuam separadas e abertas. O Electron continua sem cliente operacional autenticado e não recebeu identidade ou credenciais do Samsung.

Backup preservado fora do Git:

`<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev4-20261024T174801Z`

O backup anterior `Windows-before-dev3-20261024T145523Z` e os pacotes dev.3/dev.4 foram mantidos. Não houve rollback ou restauração.

## Limitações e ajustes nos verificadores

Uma consulta CIM inicial não tinha acesso no sandbox; foi repetida sob revisão de aprovação para leitura do sistema. Um levantamento inicial de tarefas avisou sobre profundidade de serialização; foi substituído **antes da instalação** por exportação de XML somente leitura, usada em ambos os retratos.

A primeira inspeção auxiliar do ASAR usou separadores `/` para caminhos internos aninhados, rejeitados pela biblioteca nessa plataforma. A listagem confirmou os assets; o verificador foi corrigido para `path.normalize()` e passou. **Não havia ícone ausente e nenhum arquivo instalado foi corrigido.** Uma leitura inicial de metadados usou LOCALAPPDATA redirecionado pelo sandbox; a consulta foi repetida com o caminho absoluto validado. Esses ajustes afetaram somente scripts locais de inspeção, sem executar ou alterar o aplicativo.

Os recibos públicos não contêm conteúdo do perfil, lista de credenciais ou configurações privadas descriptografadas. Mapas privados de arquivos e retratos completos de inicialização permanecem apenas na pasta de validação local ignorada pelo Git.

## Primeiro teste físico proposto — ainda não autorizado

1. Confirmar ausência de outra instância e manter agente offline, zero grants e cliente operacional desabilitado. Preservar o estado do perfil antes da sessão.
2. Abrir **uma única sessão do executável instalado dev.4**, sem portátil, instalador ou dados demonstrativos.
3. Conferir versão, logo e as três seções; observar estabilidade por pelo menos 60 segundos e capturar o dashboard real.
4. Testar minimizar normal na barra de tarefas e restaurar; usar separadamente **Minimizar para bandeja**, confirmar ícone oficial e restaurar a mesma janela por clique.
5. Pelo menu da bandeja testar **Abrir dashboard** e **Modo Widget**, incluindo ocultar/restaurar no Widget, navegação, dimensões e janela na área visível. Nenhuma ação operacional.
6. Encerrar por **Sair**, confirmar destruição do Tray e ausência de processos. Registrar preferências visuais criadas normalmente. Testes adicionais de segunda invocação e encerramento por X podem ser autorizados expressamente em um protocolo posterior.
7. Se surgir `Error`, registrar mensagem, horário e processo, parar sem nova abertura automática ou correção. Não confundir a pendência anterior com falha comprovada dessa versão.

**Aguardar autorização específica antes de abrir o dashboard ou testar a bandeja.** O plano de recuperação anterior permanece disponível em `docs/windows-dev4-preflight-2026-10-24/UPDATE-AND-RECOVERY.md`, sem restauração automática autorizada.
