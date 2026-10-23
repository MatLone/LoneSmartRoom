# Etapa 2 — comunicação e pareamento seguros

Branch: `feature/secure-pairing-status`. Base preservada:
`ed0fdae90db78d721444b29ee7d9ac49c21f73df`.

Atualização operacional posterior: a LAN foi ativada após autorização explícita.
Perfil Privado, firewall restrito e testes no listener ativo estão documentados em
LAN-ACTIVATION.md. As observações de ausência de listener/firewall neste relatório
descrevem o estado anterior à ativação.

## Implementação

Agente Python separado em armazenamento DPAPI, protocolo/SQLite, identidade TLS,
servidor HTTPS e gerenciamento local. O canal v2 oferece somente pareamento e
consulta autenticada de status. O legado 1.5 permanece intacto; não é iniciado pelo
novo serviço. Nenhuma ação real de energia/aplicativo foi habilitada no Android.

Android Kotlin: diálogo nativo para importar e confirmar identidade, pinagem exata
de certificado com validade e hostname, cliente HTTPS/HMAC e cofre AES-GCM/Keystore.
Nova ponte `LoneAgent` expõe apenas diálogo de pareamento e atualização de status.
Código, chaves e credenciais nunca são enviados ao renderer JavaScript.

Nova seção na aba Controles distingue conectado, desconectado e desconhecido e
exibe a última consulta bem-sucedida. Após reiniciar o app, o último horário é
preservado, mas o estado começa desconhecido. Não há inferência de PC desligado.
O refresh é iniciado ao carregar a interface e pelo botão; não há heartbeat móvel
em segundo plano nesta etapa. Cores e três abas são preservadas.

Protocolo completo: `contracts/secure-status-v2.md`.

## Assinatura e dados do Samsung

A chave debug original em `.android` está disponível e seu certificado corresponde
ao APK de recuperação. Nenhum conteúdo privado ou senha foi copiado para o Git.
ADB não encontrou dispositivo conectado: não foi possível verificar o certificado
do APK realmente instalado no Samsung. O APK de desenvolvimento continua usando
a chave isolada da etapa anterior; configuração de assinatura e applicationId não
foram alterados. Não houve instalação, desinstalação nem limpeza de dados.

Plano obrigatório antes de atualizar:

1. Conectar o Samsung, consultar o caminho do pacote e copiar apenas o APK instalado
   para inspeção local, sem alterar o dispositivo.
2. Comparar seu certificado com a chave original e o APK de recuperação.
3. Se coincidirem, preparar assinatura de atualização com a mesma chave, fornecendo
   credenciais por mecanismo local protegido, fora do Git. Preservar applicationId,
   origem WebView, armazenamento e configurações WoL. Validar e revisar esse build.
4. Se não coincidirem, obter a chave correta; não usar desinstalação como contorno.
5. Somente após essa validação autorizar um teste controlado de atualização sem
   limpeza, verificando todos os valores WoL antes e depois.

## Inicialização e rede

Atualização após autorização do usuário: a Ethernet foi alterada para o perfil
Privado e a mudança foi confirmada pelo Windows. Não foi criada regra de firewall
nem iniciado o listener de produção. As observações sobre perfil Público abaixo
descrevem a situação encontrada durante a implementação, antes dessa autorização.

Identidade HTTPS local criada em `.runtime/secure-agent`. Entrada por usuário
`LoneSmartRoomSecureAgent` registrada no Run do Windows com pythonw da .venv.
Não depende do widget ou Electron. O caminho do projeto/.venv deve permanecer
estável. As entradas legadas não foram alteradas; nenhuma estava registrada.

A Ethernet observada está no perfil Público. Nenhum perfil foi alterado e nenhuma
regra de firewall foi aberta. O agente espera a interface/IP configurados estarem
no perfil Privado antes de escutar; a checagem também protege cada nova conexão.
Ele fecha o listener ao detectar perda do perfil Privado. Não foi iniciado um
listener de produção nesta sessão. Registro de startup foi verificado; login real
e retomada de rede após login ainda precisam de teste operacional.

Depois de revisar a confiança da rede, pode-se usar, com administrador, o script
`scripts/configure-secure-firewall.ps1`: ele recusa perfil Público, limita origem,
destino, porta TCP e perfil Privado, bloqueia edge traversal e não substitui regras
existentes. Não configurar encaminhamento de portas no roteador.

## Operação local (não executar pair em logs ou terminal compartilhado)

```powershell
.\scripts\prepare-agent.ps1
.\scripts\manage-agent.ps1 -Action serve
.\scripts\manage-agent.ps1 -Action pair
.\scripts\manage-agent.ps1 -Action devices
.\scripts\manage-agent.ps1 -Action revoke -DeviceId <id-da-lista>
```

O código temporário aparece apenas no comando local pair, deve ser comparado no
Android e não deve ser enviado por canais não confiáveis. Gerar outro código
invalida o anterior. Revogar bloqueia a próxima consulta desse dispositivo.

## Verificação automatizada

- Testes HTTP/HMAC legados com executor substituto, sem ações reais.
- Integração HTTPS em loopback e DPAPI real do usuário Windows: credencial ausente
  e incorreta, expiração, replay persistente, revogação individual, pareamento de
  uso único/expirado, rate limit, tamanho de corpo, certificado inválido, API sem
  ações, origem fora da rede e perfil Público/indisponível.
- JVM executa a pinagem Java de produção contra HTTPS: aceita identidade esperada
  e rejeita pin errado, hostname divergente e certificado expirado.
- A assinatura HMAC Kotlin de produção também consulta o servidor Python real
  em loopback: aceita a credencial correta e rejeita repetição e chave incorreta.
- JVM valida o estado Kotlin: conexão perdida preserva horário; reinício retorna
  a desconhecido. Não transforma ausência de resposta em PC desligado.
- Pacote WoL Kotlin de produção validado sem envio UDP; hashes do emissor e app.js
  permanecem iguais à base e o bloco WakeBridge é comparado byte a byte com a base.
- Smoke Electron 45 com janela oculta, dados isolados: três abas, quatro cartões,
  campos WoL e estados de conexão preservados, sem habilitar ações de energia.
- Android assembleDebug e lintDebug passam; o recurso API 27 foi isolado em
  values-v27. Warnings não foram silenciados.
- Windows: NSIS e portátil x64 gerados, sem instalar; artefatos não assinados.
  Esses pacotes distribuem a interface Electron; o agente seguro ainda executa
  da .venv local e não foi incorporado ao instalador.
- npm audit: de 14 entradas (13 altas, uma crítica) para zero na consulta realizada.
  Electron 38.0.0 → 45.0.0 e electron-builder 26.0.0 → 26.15.3. A mudança principal
  do runtime foi necessária aos avisos restantes; teste funcional oculto e builds
  cobrem a superfície usada. Electron 45 requer instalação explícita do runtime,
  tratada no postinstall. Avisos de dependências obsoletas ainda podem aparecer.

## Limites e riscos remanescentes

Não houve teste ponta a ponta no Samsung, instrumentação Android Keystore no
aparelho, atualização de instalação, teste físico WoL ou novo login Windows.
A validação automatizada comprova o contrato, pinagem e preservação dos fontes,
não substitui esses testes físicos. A rede Pública e o firewall não configurado
impedem afirmar que a comunicação pela LAN já foi validada neste computador.

O provisionamento depende da tela Windows confiável; aceitar um código vindo de
um atacante também aceitaria a identidade desse atacante. O relógio dos dois
dispositivos precisa estar correto. O certificado expira em um ano: renovação
exigirá rotação explícita e novo pareamento; não existe fallback sem verificação.
DPAPI depende do perfil Windows; perda desse perfil pode exigir nova identidade
e pareamento. Keystore protege a chave, mas hardware-backed não foi comprovado.

O servidor é mínimo, limitado e restrito à LAN, sem auditoria externa. Não é um
serviço para internet. Zero avisos npm não comprova ausência de vulnerabilidades.
Não há dashboard de administração do agente ou pareamento por QR nesta etapa;
o método implementado é código temporário local e confirmação nativa no Android.
