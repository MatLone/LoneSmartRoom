# Preparação do launcher CS2 — 23/10/2026

**Implementado e testado com processos substituídos; nenhum lançamento real.**
Checkpoint preservado: `0ee8f870a54fe22e87c3f757f7fb4be0e3ac425d`.
Commit de código/testes: `fa7071034cd49b7944b0e50ee37509241c8eee81`, na branch
`feature/secure-pairing-status`.

## Executor selecionado

O ramo CS2 do agente seguro agora chama `cs2_launcher.launch_cs2()`. Antes ele
chamava `agent.execute_action('cs2')`, que usava `steam://rungameid/730`.
O agente legado foi preservado, mas não é mais chamado por esse ramo novo.
O ramo Steam e o arquivo `steam_launcher.py` estão **idênticos ao checkpoint**.

O novo despacho é exclusivamente:

```python
subprocess.Popen([str(executable), '-applaunch', '730'],
                 executable=str(executable), cwd=str(executable.parent),
                 shell=False, close_fds=True,
                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                 stderr=subprocess.DEVNULL)
```

`executable` vem do resolvedor Steam já validado: valores fixos locais do Registro,
caminho absoluto sem redirecionamentos, identidade Authenticode Valve e cache local
de confiança/revogação. O CS2 usa esse resolvedor sem modificar sua implementação.
Nenhum caminho, AppID, argumento extra ou comando de shell vem do Android. Não há
URI, fallback, elevação, inicialização direta de cs2.exe, flags de VAC ou retry.
O guard existente de sessão interativa/usuário não elevado permanece no adapter.

Referências: o uso de Steam com `-applaunch <AppID>` consta na
[Valve Developer Community, página indexada de opções](https://developer.valvesoftware.com/wiki/CHILLMODEA/Pages/Command_line_options).
A [página Valve do CS2](https://store.steampowered.com/app/730/CounterStrike_2/)
associa o jogo ao AppID 730 e informa uso de VAC. A consulta direta da
[página principal de opções](https://developer.valvesoftware.com/wiki/Command_line_options#Steam)
retornou HTTP 403 nesta sessão; não se afirma ter lido integralmente sua revisão
atual. A compatibilidade física desta opção com a instalação local ainda será testada.

## Instalação local e validações

A inspeção somente leitura confirmou:

- Steam: `C:\Program Files (x86)\Steam\steam.exe`, assinatura validada.
- `libraryfolders.vdf` associa 730 à biblioteca `D:\SteamLibrary`.
- `D:\SteamLibrary\steamapps\appmanifest_730.acf`: AppID 730, StateFlags 4,
  build 26144732, installdir `Counter-Strike Global Offensive`.
- Executável esperado: `D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe`,
  presente, 2.967.704 bytes. Nenhum executável foi iniciado para essa validação.

O preflight do novo launcher repete a leitura do cadastro de bibliotecas e do
manifesto, exige uma única biblioteca contendo 730, manifesto correspondente,
estado instalado e diretório filho simples. Recusa metadados ambíguos, caminhos
relativos/UNC/ADS, travessia, redirecionamentos, arquivo ausente ou sem cabeçalho
esperado. O parser local aceita o subconjunto KeyValues necessário, com tamanho,
tokens e profundidade limitados; recusa chaves duplicadas, includes e sintaxes
desconhecidas. Não lê userdata, senhas ou opções de inicialização pessoais.
Essas checagens não substituem a integridade de conteúdo administrada pela Steam.

## Testes e preservação

| Verificação | Resultado |
| --- | --- |
| Suíte automatizada completa | **70 testes**, 19,231 s, todos aprovados |
| Novos testes unitários CS2 | **11**, Popen substituído; nenhum processo real de aplicativo |
| Novos testes HTTPS → adapter CS2 | **2**, grant independente, argumentos fixos, repetição, ausência de instalação e resultado sem prontidão |
| Regressão launcher Steam | **13** testes existentes aprovados; código preservado |
| Segurança comum | HMAC, credencial incorreta, repetição, revogação, expiração, rede Privada, allowlist, parâmetros extras e TLS/pinning aprovados |
| Interface | Versão dinâmica, permissões e quatro estados aprovados |
| WoL Kotlin compilado | Pacote, normalização e rejeições aprovados; nenhum UDP enviado |
| Originais/recuperação | **86 registros íntegros** |
| Validação com instalação local | Somente resolvedores, Popen bloqueado por sentinela; nenhum dispatch |
| Banco real | **Zero grants**, zero pendentes, três comandos históricos, sem novos pedidos |

Os testes criam identidades/bancos sintéticos e HTTPS apenas em loopback, sem
alterar o pareamento de produção. Certificado, configuração DPAPI e credenciais
cifradas de produção mantêm seus hashes. Android, Electron, Kotlin/ponte WoL,
origem WebView, armazenamento, HTTPS/HMAC, startup, firewall, drivers, Registro e
arquivos/opções do jogo não foram modificados. Nenhum APK foi instalado. Não
foram executados comandos de energia ou testes físicos adicionais.

O agente real não foi reiniciado: continua com o adapter anteriormente carregado
em memória. A implementação nova está no repositório e **precisa de recarga
controlada do agente antes de qualquer grant CS2**. Nunca conceder CS2 ao processo
antigo esperando que ele já use a implementação nova. A Steam existente, PID
8916, permaneceu aberta e não foi encerrada/reaberta nesta tarefa.

## Riscos e limites

- Não existe validação física CS2 nesta entrega. O sucesso da Steam não exclui
  falhas específicas de inicialização, GPU/AMD, SteamUI, conteúdo ou atualizações.
  A causa original da recursão GameManager64 permanece inconclusiva.
- Steam pode precisar atualizar conteúdo, processar shaders ou exibir diálogos.
  O teste deve parar para avaliação se isso impedir a abertura; não alterar
  launch options, arquivos, VAC, drivers ou configurações para contornar o bloqueio.
- Launch options pessoais já salvas podem influenciar o jogo quando a Steam o
  iniciar. O agente não as lê, substitui nem acrescenta parâmetros de jogo.
- Formatos KeyValues antigos/novos não suportados, metadados em transição,
  instalações redirecionadas ou cache de assinatura ausente resultam em recusa
  segura, sem reduzir validações ou tentar outra rota.
- O PID retornado por Popen é da chamada ao cliente Steam e pode terminar após
  encaminhar o pedido ao cliente já aberto. Não identifica o processo do jogo.
  `process_running_verified=False` permanece no contrato. “Executado” não atesta
  cs2.exe ativo, menu carregado, usabilidade ou validação VAC.

## Um único teste físico proposto, pendente de autorização

1. Obter autorização específica para recarregar **somente o processo do agente**,
   preservando certificados/configuração/credenciais e sem nova inicialização
   automática. Manter todos os grants zerados durante a recarga; verificar uma
   instância, listener 8776, código novo e status autenticado no Samsung.
2. Manter a Steam atual aberta. Verificar ausência de cs2.exe, instalação ainda
   válida e nenhuma atualização/diálogo pendente informado na Steam. Se já houver
   CS2 ativo, interromper e pedir fechamento manual; não encerrar processos.
3. Registrar processos/eventos prévios e preservar dumps existentes. Preparar
   revogação em finally e limite para a janela de autorização, com tempo separado
   para observar o jogo após a prontidão. Não reutilizar o limite total de 240 s
   do teste Steam como se fosse o período pós-carregamento.
4. Conceder **somente CS2** temporariamente à identidade Samsung existente.
   Atualizar permissões, tocar uma única vez em Abrir CS2 e confirmar o diálogo.
   Nunca gerar nova solicitação após timeout ou resultado incerto.
5. Correlacionar o único request_id ao resultado do agente. Após despacho terminal,
   revogar o grant para impedir novos pedidos, mantendo CS2/Steam sem autorização.
6. Detectar cs2.exe por caminho absoluto esperado na biblioteca validada, PID novo,
   horário de criação posterior ao pedido e sessão do usuário interativo. Usar
   metadados de processo somente leitura; não depender de um PID de bootstrap ou
   apenas do nome do processo, nem abrir memória, debugger ou injetar módulos.
7. Confirmar janela/menu principal renderizado e utilizável com observação direta
   ou confirmação do usuário. Se a ferramenta não enxergar a janela, registrar a
   limitação e exigir confirmação manual. Não entrar em partida para este teste.
8. Observar por **60 segundos após a confirmação de menu utilizável**, com processo
   ativo/respondendo, sem crash/hang correlato e sem novos dumps. Confirmar a
   usabilidade ao final; presença de processo isolada não atende ao critério.
9. Conferir zero grants, HTTPS/status funcional, Android preservado e nenhuma
   segunda abertura. Em falha, parar, preservar evidências/dumps e não repetir.
   Não encerrar Steam/CS2 automaticamente ao concluir.

**Reversão:** manter grants zerados e parar a validação. Caso seja necessário e
autorizado, reverter somente o commit CS2 e recarregar apenas o agente de forma
controlada. Nunca usar a URI legada como tentativa de recuperação física; manter
CS2 sem grant até uma nova revisão. Checkpoint Steam, dados Android, identidades e
dumps não precisam ser substituídos ou restaurados por esta alteração de fonte.
