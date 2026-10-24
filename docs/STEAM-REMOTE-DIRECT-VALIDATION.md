# Steam pelo Samsung — teste único, 23/10/2026

**Resultado: abertura remota validada neste teste.** O Samsung enviou um único
pedido autenticado por HTTPS ao agente existente. A Steam abriu com o executor
direto e o usuário confirmou a biblioteca aberta e utilizável antes e depois
de **60,704 segundos** de observação. Não houve repetição ou execução de CS2.

| Evidência | Resultado |
| --- | --- |
| Pedido recebido, horário de São Paulo | 21:05:37 |
| Estado terminal do executor | Executado, 21:05:39; sem erro |
| Novos registros de comando no banco | Exatamente 1, Steam |
| Steam | PID 8916, pai 6204 (agente), sessão interativa 1 |
| Método efetivo | steam.exe absoluto validado, sem argumentos; Popen direto, sem URI |
| Processos associados | 7 steamwebhelper e steamservice; nenhum CS2 |
| Observação após confirmação visual | 21:07:08–21:08:09; 60 amostras, Steam presente e respondendo em todas |
| Biblioteca utilizável | Confirmada pelo usuário no início e no final |
| Application Error 1000 / WER 1001 / Application Hang 1002 correlatos | Nenhum encontrado desde o início do teste até a coleta final |
| Novos dumps Steam | Nenhum; SHA-256 dos três dumps anteriores preservados |
| Samsung após revogação | Conectado; Steam e CS2 desabilitados na interface |

O executor em uso é o do commit `af89e9a61a622ef58811c472247554496f2e7bff`.
Foi usada a identidade Samsung já pareada, sem criar credenciais ou novo
pareamento. A concessão local foi **somente Steam** e foi revogada assim que
o comando atingiu estado terminal, antes do fim da observação. A verificação
final encontrou **zero grants**, um novo comando Steam executado e nenhum CS2.
Autenticação, proteção contra repetição e validação de entrada não foram alteradas.

**Limites da observação e da instrumentação.** O observador automático de janelas
não encontrou uma janela Steam targetable; a evidência visual foi fornecida pelo
usuário, em duas confirmações explícitas. A evidência automática complementar
é a continuidade dos processos, ausência dos eventos correlatos e de novos dumps.
O estado “Executado” sozinho não foi usado para concluir sucesso.

O primeiro controlador tinha limite total de 240 segundos, incluindo a espera
pelo toque no celular. Ele revogou o grant corretamente e registrou o comando
executado, mas terminou antes da observação visual complementar; seu campo
`outcome` conservou incorretamente o texto padrão “No command observed”. Esse
rótulo não corresponde ao banco nem ao próprio campo `command` do recibo. O recibo
bruto foi preservado e a auditoria final registrou a discrepância. Um observador
separado, sem grants ou lançamentos, completou os 60,704 segundos após a
confirmação visual. Não se repetiu a solicitação para corrigir a instrumentação.

**Preservação.** Não houve alteração de fonte funcional, instalação Android,
reinício do agente/Windows, encerramento de processos, troca de certificado,
driver, Registro ou configuração da Steam. Configuração TLS/DPAPI e registros
cifrados dos dispositivos mantiveram seus hashes. Listener 8776, rede Ethernet
Privada e regra de firewall restrita à LAN permaneceram iguais. Verificação de
originais e recuperação: **86 registros íntegros**. Wake-on-LAN e dados Android
permaneceram preservados; não houve novo teste físico de WoL ou comandos de energia.

Recibos, amostras, cópias locais dos logs e hashes de preservação ficam em
`.cache/validation/steam-remote-once-20261023`, fora do Git. Logs completos,
identificadores de dispositivo, chaves e credenciais não foram incluídos no
relatório versionado. [Resumo sanitizado](steam-remote-direct-results.json).

**Próximo procedimento de menor risco:** encerrar esta rodada com todos os grants
revogados e revisar o resultado antes de autorizar qualquer novo lançamento.
O teste sustenta o caminho direto Android → HTTPS → Popen nesta sessão; não
determina o gatilho original da recursão AMD nem comprova confiabilidade em
sessões futuras. CS2 e energia continuam bloqueados, e a Steam foi deixada aberta.
