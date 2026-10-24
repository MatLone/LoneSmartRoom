# Bandeja e preferências de janela — proposta separada, não implementada

## Estado aprovado atual

- Minimizar envia a janela à barra de tarefas; restauração ocorre pelos mecanismos normais do Windows.
- Fechar fecha a janela e encerra o Electron no Windows.
- Dashboard pode maximizar/restaurar e redimensionar. Widget usa dimensões compactas, navegação inferior e pode redimensionar; maximização foi desabilitada nesse modo.
- A troca de modo guarda/restaura bounds anteriores e estado maximizado apenas em memória. Não há persistência de posição/tamanho entre reinícios.
- Não existe Tray ou opção de início com o Windows. O agente é um processo separado.

Esse comportamento foi verificado no código preservado e nas evidências nativas anteriores (minimizar/restaurar/fechar e alternância de modo), cujo EXE/ASAR permanecem idênticos. O aplicativo empacotado não foi aberto para repetir o teste nesta entrega.

## Proposta futura

1. Criar `Tray` somente no main, com o ICO oficial e menu limitado a **Mostrar dashboard**, **Modo Widget**, **Preferências** e **Sair**. Manter a referência do objeto durante o ciclo de vida. Clique restaura/focaliza a mesma janela, sem duplicar instâncias. Referência: [Electron Tray](https://www.electronjs.org/docs/latest/api/tray).
2. Oferecer preferência **Minimizar para bandeja**, inicialmente desligada para preservar o padrão atual. Se ativada, esconder a janela depois de garantir que a bandeja foi criada; falha na criação conserva a barra de tarefas.
3. Separar o comportamento de fechar da opção de minimizar. Padrão continua sair; esconder ao fechar exige opção própria e explicação visível. **Sair** deve encerrar o Electron explicitamente, sem matar ou reiniciar o agente.
4. Usar uma política de instância única, com segunda abertura restaurando a janela existente. Não transformar esse mecanismo em bloqueio ou comando do agente.
5. Persistir apenas preferências visuais em schema versionado dentro de userData: modo, bounds do dashboard/widget e opção de bandeja. Escrita atômica, validação de tipos/tamanhos, debounce e recuperação de arquivo inválido. Não misturar credenciais ou grants nesse arquivo.
6. Restaurar bounds contra a área útil dos monitores atuais. Limitar posição/tamanho para evitar janelas fora da tela após desconectar monitor; considerar DPIs diferentes e restaurar dashboard maximizado separadamente de bounds normais. Testar 100/125/150% e movimento entre monitores.
7. Opção **Iniciar com o Windows**, desligada por padrão e independente de bandeja. Aplicar somente por ação explícita do usuário, no main, com caminho instalado validado e API específica de login. Não usar caminho temporário do portátil nem herdar startup do agente. Remoção da opção deve ser verificável e não afetar outros programas. API de referência: [app.setLoginItemSettings](https://www.electronjs.org/docs/latest/api/app#appsetloginitemsettingssettings-macos-windows).

## Segurança e critérios de aprovação

Não adicionar IPC genérico, caminhos enviados pelo renderer, comandos de terminal ou concessão de grants. Preload continua tipado; qualquer extensão de preferência deve validar remetente/frame, tipos e enumerações. Nenhuma ação da bandeja abre jogos ou aciona energia nesta proposta.

Testar: minimizar/restaurar repetidamente, fechar versus Sair, widget/dashboard, segunda instância, falha do Tray, perfil corrompido, dois monitores e mudança de DPI. Início com Windows exige teste físico separado, autorização e reversão documentada. A UI deve permanecer utilizável quando o agente estiver indisponível. O problema TLS não é resolvido nem contornado por bandeja/inicialização.

Nada desta proposta foi aplicado nesta preparação do instalador.
