# Launcher direto Steam — implementação e validação, 23/10/2026

**Implementado, sem teste físico:** o executor Steam autorizado do agente seguro
agora inicia somente o executável Steam local validado. Não utiliza
`steam://open/main`, shell, argumento de rede, busca em PATH ou fallback.
Commit isolado: **`af89e9a61a622ef58811c472247554496f2e7bff`**, branch
`feature/secure-pairing-status`.

Esta é uma tentativa controlada de contornar o caminho que apresentou falha,
não uma correção comprovada da recursão AMD. Steam e CS2 não foram abertos.
[Recibo sanitizado](steam-direct-launch-validation.json).

**Mudança efetiva.** Apenas a integração Steam em
`agent/windows/secure_apps.py::launch_allowed` mudou de executor. Ela continua
validando a allowlist e exigindo usuário não elevado/sessão interativa antes de
chamar o novo módulo `steam_launcher.py`. Claim, fila, grants, HMAC, deduplicação,
TLS, rede Privada/LAN, status e startup não foram alterados. O executor legado
`agent.py` v1.5 foi preservado, incluindo o código CS2, sem conceder permissão para
executá-lo. Nenhum código Android/Electron ou comando de energia foi alterado.

O módulo novo lê somente valores fixos SteamExe/SteamPath/InstallPath do Windows,
em HKCU/HKLM e visões 32/64. Exige convergência para um executável absoluto local
chamado steam.exe; rejeita conflito, caminho relativo/UNC/device path, expansão
de variável, argumentos anexados, ADS, arquivo ausente, componente redirecionado
por reparse point e arquivo sem cabeçalho executável esperado. Não recebe qualquer
caminho ou argumento do cliente.

A identidade é verificada por WinVerifyTrust e pela organização do signatário
validado (`Valve Corp.`), com libs do System32, sem UI, shell ou download auxiliar.
A verificação usa cache local de cadeia/revogação, rejeita MD2/MD4 e falha fechada
se não conseguir estabelecer confiança. O estado nativo é fechado inclusive em
falha; ausência de estado/signatário também é recusada. Alterações de identidade,
tamanho ou mtime durante a verificação são recusadas e redirecionamentos são
rechecados imediatamente antes do despacho.
[Microsoft: WinVerifyTrust](https://learn.microsoft.com/en-us/windows/win32/api/wintrust/nf-wintrust-winverifytrust),
[Microsoft: WINTRUST_DATA e flags de cache/revogação](https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_data).

O despacho é exatamente uma chamada `subprocess.Popen` com argv de um item,
`executable` absoluto, `cwd` da pasta Steam, `shell=False`, `close_fds=True` e
stdio em DEVNULL. Não há runas, credencial alternativa, flags de debugger,
breakaway de Job, retry ou fallback. Uma falha termina como `launcher_failed`
na infraestrutura existente, sem revelar paths/erros privados ao Android.
O retorno informa que o pedido foi entregue ao Windows, com janela não verificada.
O contrato continua com `process_running_verified=False`; a interface existente
já explica que “Executado” não comprova janela/jogo carregado.

**Testes executados.**

| Validação | Resultado |
| --- | --- |
| Suíte Python completa | **57 testes passaram**, 18,206 s na execução final |
| Novos testes específicos do launcher | **13 passaram**, incluídos nos 57 |
| HTTPS → executor de produção com Popen substituído | Grant obrigatório, CS2 sem grant recusado, despacho único, sem URI e repetição sem nova execução |
| HTTPS → arquivo ausente no executor de produção | Falha segura, nenhum Popen e nenhuma tentativa alternativa |
| Status/HMAC/TLS/pinning Android | Regressões passaram, incluindo credencial errada, repetição, expiração, revogação, certificado inválido e indisponibilidade |
| Interface e versão | Teste JavaScript de versão dinâmica, permissões e quatro estados passou |
| WoL Kotlin compilado | Pacote de 102 bytes, normalização MAC e rejeições passaram; **nenhum UDP enviado** |
| Originais/recuperação | **86 registros preservados** |
| Revisão Git | Fontes baseline protegidos/WakeBridge preservados; sem padrões de credenciais no índice |

Nos testes automatizados, toda criação de aplicativo real foi substituída. Há
cobertura para caminhos inválidos/ausentes, cadastro conflitante, reparse points,
assinatura/publisher errados, falta de estado/signatário nativo, mudança de arquivo,
falha Popen, sessão indevida, IDs fora da allowlist e argumentos extras via HTTPS.
Os testes usam bancos/certificados temporários e servidores em 127.0.0.1, não o
agente real nem seus dados. A primeira tentativa de suíte no sandbox encontrou
WinError 10013 em socket de loopback; a suíte passou no contexto autorizado para
esses testes, sem alteração de firewall ou regra de rede.

Uma checagem separada **somente de leitura** executou o resolver e o verificador
nativo sobre a instalação real, sem chamar launch_steam/Popen. Resultado:
`C:\Program Files (x86)\Steam\steam.exe` validado. Isso testa a integração nativa
de confiança, não a abertura do aplicativo. Não houve dependência instalada,
novo APK, acesso ADB ou atualização no Samsung.

**Preservação.** Os três dumps Steam mantêm seus hashes exatos. Banco real aberto
por URI SQLite `mode=ro`: zero grants, dois comandos históricos e zero pendentes.
CS2 e energia continuam bloqueados; nenhum grant Steam foi concedido. Configuração
DPAPI é legível, identidade TLS tem o mesmo fingerprint e o certificado está no
prazo. Os fontes HTTPS, WoL, armazenamento `lone-wol-settings-v1`, Kotlin/ponte JS,
origem WebView, APK e credenciais não foram alterados. O agente real não foi
iniciado/reiniciado. A preservação não equivale a um novo teste LAN ou WoL físico.

**Diagnóstico separado do agente offline — preliminar.** A coleta de leitura
encontrou uma transição de sessão Windows desde os testes da tarde:

| Evidência existente | Horário America/Sao_Paulo |
| --- | --- |
| User32 1074, solicitação de encerramento/reinício | 15:11:05 |
| EventLog 6006, parada do serviço de log | 15:11:11 |
| Último boot informado pelo Windows | 18:54:05 |
| EventLog 6005, início do serviço de log | 18:54:18 |

Esses registros contextualizam o fim da sessão anterior; não são um evento de
crash do agente nem identificam por si a causa da ausência após o login. Nenhuma
ação de energia foi executada nesta tarefa. Não foi encontrado processo do agente
nem listener 8776. A entrada HKCU Run LoneSmartRoomSecureAgent permanece presente,
correta, com aspas e 221 caracteres; executável e script existem. Não foi
encontrada entrada específica de StartupApproved que comprove bloqueio nem as
políticas DisableCurrentUserRun/DisableLocalMachineRun nos locais consultados.
Ausência dessas entradas também não comprova execução bem-sucedida no login.

O endereço 172.31.161.169 existe, Ethernet está Privada, configuração aponta para a
mesma LAN/porta, DPAPI funciona e certificado TLS é válido e mantém a identidade.
Não foram encontrados eventos Python 1000/1001 desde o boot nem registros Shell-Core
correlatos ao script. Não há log persistente próprio do agente no local examinado;
pythonw não captura automaticamente um traceback em arquivo. Assim, **o motivo
exato de não iniciar ou encerrar precocemente após o login continua inconclusivo**.
Um problema transitório na inicialização não pode ser excluído por verificações
atuais bem-sucedidas. Não houve nova coleta habilitada, alteração de Registro,
startup, firewall, serviço, driver ou tentativa de iniciar o agente.

A próxima investigação operacional deve ser autorizada separadamente: iniciar
somente o processo do agente com captura sanitizada de erro e confirmar HTTPS,
sem alterar startup/firewall. Isso não é pré-requisito para um teste **local** do
launcher e não está autorizado/executado nesta entrega.

**Limites/riscos remanescentes.** A criação direta ainda pode alcançar a rotina
SteamUI/GameManager64 que falhou. A validação de assinatura offline pode bloquear
uma instalação legítima se faltar cache de confiança/revogação; não há redução
automática dessa verificação. Instalações em junction/symlink são recusadas de
propósito. As verificações reduzem a janela de troca do arquivo, mas não oferecem
proteção absoluta contra um invasor local que controla o diretório e corre com
CreateProcess. O mecanismo de confiança usa APIs Windows existentes, com falha
fechada caso fiquem indisponíveis. Nenhuma estabilidade física foi demonstrada.

**Plano para um único teste físico, pendente de autorização expressa.**

1. Conferir que Steam/WebHelper/CS2 estão encerrados. Se houver cliente ativo,
   cancelar e pedir fechamento manual, sem encerrar processos automaticamente.
2. Preservar logs e hashes dos dumps; registrar processos/serviços e contexto
   relevantes. Manter AMD, Windows e segurança inalterados.
3. Uma única chamada **local** a `secure_apps.launch_allowed('steam')` em worker
   equivalente, com recibo exclusivo que impeça repetição. Nenhum Samsung,
   HTTPS, grant ou inicialização do agente é necessário. A chamada atravessa o
   guard de usuário interativo e o novo launcher; não é uma URI alternativa.
4. Observar biblioteca real, sessão/processos e eventos por 60 segundos. Na primeira
   falha, parar, preservar o dump e não tentar outra vez. A saída do PID inicial
   não será considerada isoladamente falha/sucesso se o bootstrap fizer handoff.
5. Aceitação deste teste: biblioteca visível e funcionamento durante a observação,
   sem novo crash correlato; retorno de Popen sozinho não basta. CS2 permanece
   bloqueado. Um sucesso isolado não comprova confiabilidade em sessões futuras.

**Reversão definida:** parar os testes, manter todos os grants zerados e reverter
somente `af89e9a61a622ef58811c472247554496f2e7bff` com Git. O commit contém apenas
launcher/integrador/testes; não há schema novo ou dados para restaurar. Não fazer
reset destrutivo, downgrade Android, limpeza de dados, troca de certificados ou
fallback físico para URI. Se o agente estiver ativo numa etapa futura, qualquer
recarga será tratada separadamente; não reiniciar Windows. Nenhuma reversão foi
executada nesta tarefa.
