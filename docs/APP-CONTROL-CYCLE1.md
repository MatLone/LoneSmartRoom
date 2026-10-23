# Controle remoto seguro — primeiro ciclo, 2026-10-23

Validação posterior autorizada: [atualização v16 e testes físicos](APP-CONTROL-PHYSICAL-VALIDATION.md).
O registro abaixo descreve a implementação e os testes anteriores à instalação.

## Implementado

Branch `feature/secure-pairing-status`, preservando como ancestral o checkpoint
`374ffec81d933bdcc15976f5df08c864d07be467` e a base inicial anterior.

- `secure_apps.py`: permissões locais por dispositivo/app, fila limitada, IDs
  idempotentes persistidos e resultados consultáveis.
- `secure_http.py`: três rotas específicas de apps; HMAC cobre método, caminho e
  corpo integral. Mantidos HTTPS, CIDR, perfil Privado e nonces persistidos.
- O adapter chama o executor v1.5 **inalterado** exclusivamente para `steam` e
  `cs2`. As URIs são fixas (`steam://open/main` e `steam://rungameid/730`).
- A execução real é recusada se o processo estiver elevado ou na sessão 0 de
  serviço. O agente deve continuar no login do usuário, sem depender do Electron.
- Android exige confirmação nativa com nome do aplicativo e endereço do Windows.
  A permissão específica também precisa existir no Windows, separada do pareamento.
- A interface distingue Solicitado, Aceito, Executado e Falha. Resultado incerto
  deve ser consultado, sem reenvio automático. Estado de comando não altera o
  estado de energia do PC nem libera botões de energia.

Contrato detalhado: [app-launch-v2.md](../contracts/app-launch-v2.md).

## Cabeçalho e preservação

Android obtém a versão por `BuildConfig.VERSION_NAME` na ponte pública de metadados
`LoneAppInfo`; Electron obtém de `app.getVersion()` via preload isolado. Não há
versão fixa no cabeçalho/handlers do produto. O pacote Electron também passou a
2.0.0-dev.2. O teste oculto confirmou a versão do metadado pelo preload real.

O JavaScript legado teve somente **duas expressões de versão** substituídas. O
guard de preservação compara o resto byte a byte à recuperação, aceitando apenas
essas substituições e as duas adições IPC de versão revisadas. Não foi simplesmente
liberado todo o arquivo para mudanças. `WakeOnLan.kt`, o bloco WakeBridge, o
armazenamento `lone-wol-settings-v1`, a origem WebView e o manifest continuam
preservados. A ponte WoL permanece independente do agente e de permissões de apps.

`AgentVault` não foi alterado: mesmo alias Android Keystore, AES-GCM, arquivo em
noBackupFilesDir e configuração existente. `pending_launch` é campo opcional
adicionado ao JSON cifrado, sem limpar os valores existentes. As novas tabelas
Windows são aditivas; nenhum dispositivo ganha permissão automaticamente e
nenhum token/certificado é rotacionado. Nenhuma dependência nova foi adicionada.

## Builds

- Android: **2.0.0-dev.2 / código 16**, `com.lonesmartroom.app`.
- APK: `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.2-v16.apk`.
- SHA-256: `a6fcf7f36885777def7d55ecd758f16ccd1f907eba8dbf7105cf8404b58f62b3`.
- Certificado SHA-256: `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
- Build offline assembleDebug/lintDebug e assinatura v2 verificada com apksigner.
  Chave original utilizada em seu local existente, sem senha/chave copiada para
  Git, relatório ou logs. APK debug para validação, não release de produção.
- Lint: zero erros e cinco avisos existentes (Gradle, orientação, JavaScript,
  X509TrustManager customizado e extração/backup). Também permanecem dois avisos
  de compilação por setters WebView depreciados, mantidos explicitamente false.
- Windows Electron: NSIS e portátil x64 **2.0.0-dev.2**, gerados e não executados:
  `apps/windows-ui/dist/Lone Smart Room Setup 2.0.0-dev.2.exe` e
  `apps/windows-ui/dist/Lone Smart Room 2.0.0-dev.2.exe`.
- Pacotes Windows sem assinatura Authenticode. O ASAR contém os novos módulos e a
  versão correta. Esses instaladores distribuem a interface Electron, não embutem
  o agente Python/.venv, conforme a arquitetura anterior.

O APK funcional 1.4, o APK v15 validado e os backups DPAPI permanecem preservados.
Nada foi instalado, desinstalado, limpo ou acessado no Samsung nesta tarefa.
O cabeçalho no aparelho só será corrigido depois da atualização autorizada.

## Testes automatizados

**42 testes passaram**, incluindo 16 novos de controle de apps, mais a suíte
legada com executor mock, teste JVM WoL, teste Node de versão/estados e smoke
Electron oculto. Não houve envio UDP, comando de energia ou abertura real de
Steam/CS2 pelos testes.

Cobertura nova: pareamento sem permissão; grants separados; HMAC Kotlin de produção
com corpo POST contra HTTPS real em loopback; credenciais erradas; timestamp
expirado; replay; adulteração de corpo; JSON inválido/duplicado; headers duplicados;
campos de escopo/caminho/argumentos recusados; rotas remotas de grant inexistentes;
Steam/CS2 únicos permitidos; energia e shell recusados; resultado isolado por
dispositivo; duplicata concorrente executada uma vez; revogação de app/dispositivo
na fila; perfil Privado reavaliado; expiração; fila/taxa/histórico limitados;
falha do executor; recuperação sem redisparo; execução elevada/sessão 0 recusada.

Mantidos os testes existentes de pin/hostname/certificado expirado, conexão
indisponível, status, replay após reinício e rede Pública/fora da LAN. O teste
WoL usa Kotlin compilado, sem enviar pacote. Os 86 registros de originais e
recuperação passaram; o bloco WakeBridge continua igual à base.

## Revisão de segurança e limites

Não há endpoint de autorização remota nem interpretação de texto como shell.
O router não recebe executável, argumento ou URI. A lista explícita é aplicada
antes do adapter v1.5; o dispatcher nunca encaminha comandos de energia para ele.
O import do módulo legado não inicia seu servidor HTTP ou sua rotina main.

Credenciais permanecem fora do JavaScript/localStorage/logs. HMAC autentica o
corpo exato; o ID de comando complementa a proteção de replay para permitir
recuperar resultados sem duplicar efeitos. Payload tem limite de 1 KiB, conexões
e leitura têm limites existentes e a fila limita recursos do launcher.

Limites a considerar na revisão:

1. **Executado significa despacho ao Windows.** O retorno v1.5 de os.startfile
   não prova PID, janela, login Steam ou CS2 carregado. O teste físico ainda é
   obrigatório; nada disso foi substituído por dados simulados no produto.
2. A associação local `steam://` é confiada ao Windows do usuário. O preflight
   encontrou Steam, handler e arquivos CS2, mas não atestou integridade/assinatura
   dos binários instalados, login, atualizações pendentes ou estado do jogo.
   CS2 pode iniciar Steam como dependência, mesmo com grant específico apenas CS2.
3. Não há limite de duração imposto ao os.startfile legado. Um travamento ocupa
   o único worker; a fila permanece limitada. Uma futura manutenção pode isolar
   o launcher em processo com timeout. Não há retry automático em resultado incerto.
4. Revogar impede pedidos futuros e itens ainda não iniciados; não cancela uma
   solicitação já entregue ao Windows. Permissões pressupõem um dispositivo
   pareado confiável. A confirmação nativa não é uma atestação biométrica.
5. O histórico para em 1000 registros/dispositivo; manutenção futura deve preservar
   tombstones/IDs de deduplicação. Não foi criado apagamento automático inseguro.
6. O novo diálogo/fluxo nativo e a persistência de pending_launch **ainda não foram
   testados no Samsung**, pois o APK não foi instalado. Java/Kotlin de autenticação
   e pin foram exercitados na JVM; UI em Node/Electron. Não equivalem ao teste físico.

O agente real não foi reiniciado/recarregado por esta tarefa, nem foram concedidas
permissões ao dispositivo real. A ativação deve ser confirmada no teste aprovado;
o status/pareamento existentes continuam sendo a referência funcional em uso.

## Procedimento físico proposto — aguardando autorização

1. Obter autorização expressa para **instalar o APK v16** e, separadamente ou no
   mesmo consentimento explícito, **abrir Steam e CS2 reais**. Não há execução
   física autorizada por este relatório.
2. Antes da atualização, reconfirmar aparelho/pacote/certificado, valores WoL e
   backup protegido. Instalar exclusivamente por `adb install -r`; interromper em
   erro, sem desinstalação, limpeza ou downgrade. Conferir versão dinâmica, WoL,
   pareamento e status existentes após a atualização.
3. Preservar uma cópia consistente do SQLite por SQLite backup, fora do Git;
   manter config DPAPI e identidade TLS. Recarregar somente o agente verificado
   deste repositório, como usuário normal, mantendo startup e regra Privada/LAN.
   Não iniciar o servidor HTTP legado nem alterar firewall/roteador/certificado.
4. Confirmar status com as credenciais antigas. Escolher o ID correto no Windows
   e conceder apenas `steam` pelo comando local do contrato. No Android, verificar
   permissões: Steam habilitado, CS2 ainda bloqueado. Nenhum grant é feito por API.
5. Confirmar no diálogo Android a abertura de Steam. Registrar ID/estados públicos
   e observar a janela/processo real. Se pedir login, o usuário o faz diretamente;
   não coletar senhas. Não baixar/instalar ou alterar configurações automaticamente.
6. Após sucesso Steam e dentro da autorização para CS2, conceder `cs2`, atualizar
   permissões e confirmar a abertura. Observar CS2 real. Se houver atualização,
   instalação ou licença pendente, interromper e registrar, sem tratar “Executado”
   como prova de jogo carregado. Não encerrar processos/jogos do usuário à força.
7. Consultar a mesma solicitação para confirmar ausência de nova abertura; validar
   recusa depois de revogar o app. Ao final, remover grants concedidos só para o
   teste, preservando status/pareamento, salvo autorização de uso permanente.
8. Suspender/Reiniciar/Desligar permanecem bloqueados. Não repetir o teste S3 ou
   qualquer outra ação de energia neste ciclo.

Recibo público: `app-control-cycle1-results.json`. Nenhum segredo foi incluído.
