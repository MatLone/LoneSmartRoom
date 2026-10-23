# Restabelecimento controlado do agente HTTPS — 23/10/2026

O agente existente foi iniciado uma única vez, às 19:49:32 (America/Sao_Paulo),
sem mudança de código funcional, configuração, firewall ou mecanismo de login.
Fonte validada: `267dd13fae5d2472855ad917ea50f55541112c62`; executor direto Steam
do commit `af89e9a61a622ef58811c472247554496f2e7bff`.

## Estado e evidências

- Um listener HTTPS em `172.31.161.169:8776`, pertencente ao PID 6204. O PID 23228
  é o wrapper pythonw da venv, pai desse processo; não representa outra instância
  independente do agente. Sessão interativa 1, execução não elevada.
- Configuração DPAPI, certificado, chave criptografada e passphrase protegida
  mantiveram seus hashes. Certificado vigente, fingerprint original e chave
  carregados com sucesso. Identidades/credenciais cifradas e revogações no banco
  permaneceram idênticas; nenhum novo pareamento foi criado.
- GET `/v2/status` real: **200**, agente online, com autenticação da identidade
  existente; **401** sem autenticação. Cliente local validou certificado exato,
  cadeia configurada e SAN/nome do servidor. Segredo usado somente em memória.
- **Zero grants Steam/CS2**, dois comandos históricos e zero pendentes antes e
  depois. Nenhum POST de abertura foi enviado nesta tarefa.
- Firewall permaneceu TCP 8776, entrada Privada, IP local específico, sub-rede
  `172.31.145.10/24`, programa pythonw aprovado e edge traversal bloqueado.
- Nenhuma saída/erro no stderr/stdout capturado da inicialização controlada.
  Isso não equivale a um log completo de acessos: o agente evita registrar
  requisições e cabeçalhos de autenticação.

## Samsung: reconexão confirmada manualmente

Galaxy S25 FE identificado por ADB sem fio na mesma LAN. Aplicativo instalado
continua `com.lonesmartroom.app`, 2.0.0-dev.2, código 16; não houve instalação.
A WebView apresentou **Conectado**, última comunicação **19:50:00**, usando o
pareamento já existente. A consulta seguinte, às **19:50:49**, terminou como
**Desconectado**, preservando a última comunicação e sem afirmar que o PC desligou.
Os botões Steam e CS2 estavam desabilitados; o cabeçalho mostrou a versão correta
e a origem permaneceu `file:///android_asset/index.html`.

Uma tentativa posterior de observação da WebView por encaminhamento ADB local
não respondeu, embora o dispositivo continuasse listado por ADB. A consulta de
atividade não confirmou o Lone Smart Room como atividade retomada. Isso **não
comprova** causa de rede, TLS, credenciais ou segundo erro do endpoint. A tentativa
de observação foi encerrada, e o encaminhamento temporário foi removido.
Solicitada confirmação no próprio celular, desbloqueado, usando apenas atualizar
status. Após a entrega inicial deste relatório, o usuário respondeu **Conectado**.
Essa confirmação manual conclui a validação de reconexão com o pareamento
existente; não representa um teste prolongado de estabilidade e não elimina a
falha intermediária registrada acima, cuja causa permanece inconclusiva.
Nenhum mecanismo de segurança foi reduzido. Não foram executados novos comandos,
concedidos grants ou iniciados aplicativos em decorrência dessa confirmação.

## Agente anteriormente offline

Os eventos 1074/6006 às 15:11 e o novo boot/evento 6005 às 18:54 contextualizam
o encerramento da sessão anterior. A entrada HKCU Run existente está correta,
com executável/script presentes e comando de 221 caracteres. Não foram encontrados
crashes Python 1000/1001 desde esse boot, bloqueio específico de StartupApproved
ou políticas de desativação de Run. Sem log persistente do processo anterior,
a causa exata da ausência após o login **permanece inconclusiva**. O início manual
controlado comprova que a configuração atual pode servir HTTPS; não comprova
funcionamento do autostart no próximo login. Nenhum novo autostart foi criado.

## Testes e preservação

- **57 testes automatizados passaram**, 17,949 s; launcher com Popen substituído,
  caminhos inválidos/ausentes, allowlist, permissões, repetição, HMAC, TLS/pinning,
  status e indisponibilidade. Verificações JavaScript de versão/permissões/estados
  também passaram. Nenhum programa real foi aberto pelos testes.
- Verificação de preservação: **86 registros** de originais/recuperação íntegros.
  Nenhuma modificação de Kotlin, ponte JS, armazenamento WoL, Android, Electron,
  autenticação ou launcher nesta tarefa. Não foi realizado novo teste físico WoL.
- Steam já aberta permaneceu com o mesmo PID 1564 e processos associados; nenhum
  encerramento ou nova abertura. CS2 não foi iniciado. Dumps não foram alterados.
- Recibos locais sanitizados e logs ficam em `.cache/validation/agent-reconnect-*`;
  snapshots cifrados/checksums internos e utilitários de validação não são
  versionados. Credenciais não constam deste relatório nem dos logs publicados.

## Procedimento futuro, ainda sem autorização de execução

1. Confirmar status autenticado Conectado estável no Samsung e HTTPS ativo.
2. Solicitar fechamento manual da Steam; confirmar ausência do cliente,
   WebHelpers e CS2. Se persistirem processos associados, interromper e avaliar
   sem encerrá-los automaticamente.
3. Obter autorização expressa para **uma única abertura remota** e um grant
   temporário **Steam somente** para a identidade Samsung existente. Não criar
   nova identidade, habilitar CS2, usar URI nem modificar o APK.
4. Registrar eventos/processos prévios, conceder somente esse grant, atualizar
   permissões no Samsung e confirmar uma única solicitação na interface Android.
   Não fazer retentativa automática após timeout ou falha.
5. Observar biblioteca/janela efetiva, processos e eventos Windows por 60 segundos
   a partir da abertura real. “Executado”/Popen isoladamente não comprovam sucesso.
6. Revogar o grant Steam ao final, inclusive em falha/interrupção, verificar zero
   permissões e que status continua acessível. Preservar dumps em eventual crash.

O mecanismo atual de grants não tem expiração automática: “temporário” exige
revogação local explícita. Caso o acompanhamento seja interrompido, a revogação
precisa ser concluída antes de encerrar a futura validação. Nenhum grant foi
concedido ou teste físico preparado para execução automática nesta entrega.
