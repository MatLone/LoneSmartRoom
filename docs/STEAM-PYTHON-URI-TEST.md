# Steam: teste único local por Python/URI — 23/10/2026

**Resultado: falha reproduzida sem Samsung ou API HTTPS.** Uma chamada local
`os.startfile('steam://open/main')` iniciou a Steam, mas ela sofreu crash cerca
de 5,45 segundos depois. Não permaneceu funcionando por 60 segundos. O evento
coincide com os dois anteriores em executável/versão, módulo/versão, exceção e
offset. Isso não confirma ainda a mesma pilha GameManager64: o novo dump não
teve seu conteúdo de memória analisado.

Horários America/Sao_Paulo, UTC−03:00. Branch `feature/secure-pairing-status`,
base `19fb4dcb515bbfeca45d9a155a5d59345ed67b6c`.
[Recibo sanitizado](steam-python-uri-results.json).
[Comparação anterior de contexto](STEAM-LAUNCH-CONTEXT-COMPARISON.md).

**Antes do teste.** Às 14:07:04, nenhum processo Steam, WebHelper, SteamService,
GameOverlayUI ou CS2 foi encontrado. Steam Client Service estava Stopped/Manual.
Não foi necessário solicitar fechamento, encerrar processo ou alterar serviço.
AMD External Events Utility estava Running/Auto, PID 2992, com atiesrxx/atieclxx;
AMD Crash Defender estava Running/Auto, PID 2984. Esses serviços mantiveram o
mesmo estado, modo e PID após o teste.

Os seis logs existentes foram copiados e verificados por SHA-256 para
`.cache/validation/steam-python-uri-20261023/before-logs`. Os originais ficaram
em seus locais; sua escrita normal pelo cliente durante o teste foi preservada
em `after-logs`. Nenhum conteúdo bruto desses logs entra em Git ou relatório.
Os dois dumps anteriores foram mantidos no local original, com hashes registrados.

**Execução única e contexto.** Às **14:09:09,977**, um helper temporário fora dos
fontes funcionais executou uma única chamada com os mesmos argumentos omitidos
do executor: `operation`, `arguments`, `cwd` e `show_cmd`. Não foi usado o servidor,
o Android, um grant remoto, `agent.main`, executor de energia ou CS2.

| Campo | Valor comprovado no helper |
| --- | --- |
| Runtime | `C:\Python313\pythonw.exe`, CPython 3.13.3, mesmo runtime real do agente |
| Diretório efetivo | Raiz de `Lone_Smart_Room_2.0`, igual ao CWD atual do agente |
| Thread de execução | Uma `lsr-app-launch`, `daemon=True`, como o worker do agente |
| Usuário/sessão | Sessão interativa 1, sem elevação; nenhuma credencial alternativa ou runas |
| Variáveis selecionadas | As mesmas 13 variáveis técnicas examinadas no agente estavam ausentes |
| API/URI | `os.startfile('steam://open/main')`, sem inicialização explícita de COM |
| Retorno da API | Sem exceção às 14:09:10,055; classificado apenas como despacho |

Um recibo exclusivo no controlador e outro antes de `os.startfile` impedem
repetição acidental. O helper contém somente uma chamada à URI fixa e sua AST
foi conferida antes da execução, sem invocá-la nesse exame. Não houve fallback
ou segunda abertura. A execução do Python foi oculta como a do agente; a Steam
recebeu o padrão `show_cmd=1`, sem pedido para ocultar sua interface.

O modelo reproduz API, runtime, CWD e thread, mas não todos os detalhes do processo
residente: o helper é novo, vive aproximadamente 81 ms e não hospeda HTTPS/fila
persistente; o agente continua ativo desde 12:49. Ambiente completo, PATH e
histórico de COM do processo/thread não foram demonstrados idênticos. Nenhuma
variável foi redefinida para forçar equivalência. Esses limites impedem atribuir
uma causa única ao contexto que difere do atalho.

**Observação e evento.** O monitor durou **60,699 segundos**, com 60 amostras.
Steam PID **20108** apareceu em seis amostras, das 14:09:10,973 às 14:09:16,054;
ao fim, não havia processos Steam ou CS2. Um handle de janela WebHelper apareceu
na amostragem, mas não foi confirmada uma biblioteca estável visualmente; a
consulta de janelas feita após o lançamento já não encontrou janela Steam.
Processos transitórios ou handle de janela não foram tratados como sucesso.

| Campo | Crash Android 1 | Crash Android 2 | Teste Python/URI local |
| --- | --- | --- | --- |
| Horário do evento 1000 | 12:51:15,589 | 12:53:16,278 | **14:09:15,422** |
| RecordId / PID | 746 / 20876 | 747 / 10876 | **769 / 20108 (`0x4e8c`)** |
| Executável | `C:\Program Files (x86)\Steam\steam.exe` | Mesmo | Mesmo |
| Versão Steam | 11.15.70.27 | Mesma | Mesma |
| Módulo | `C:\Windows\System32\ntdll.dll` | Mesmo | Mesmo |
| Versão módulo | 10.0.26100.9711 | Mesma | Mesma |
| Exceção | `0xc0000005` | Mesma | Mesma |
| Fault offset | `0x0000000000166447` | Mesmo | Mesmo |

A consulta final até 14:11:07 encontrou **um evento 1000 novo e nenhum 1001**
Steam/WebHelper no intervalo desta tentativa. O bootstrap registra a URI esperada
e verificação concluída às 14:09:10. Há mensagem google_update_settings no CEF
nesse horário e shutdown de WebHelper/CEF às 14:09:17. Não se atribuiu causalidade
a mensagens já encontradas também na abertura anterior bem-sucedida.

**Dumps e logs preservados.** O Windows produziu automaticamente:

```text
%LOCALAPPDATA%\CrashDumps\steam.exe.20108.dmp
17.527.625 bytes; última escrita 23/10/2026 14:09:16,610
SHA-256 dbd1ac5a3e62bb2ab97e5464349468569c547b24b52aee664148d51ecdc9c07a
```

Não foi habilitada coleta, nem aberto esse arquivo em depurador, copiado para
serviços externos ou examinado seu conteúdo de memória. Hash é controle de
integridade, não análise da exceção. Os dumps 10876 e 20876 mantiveram os hashes
anteriores; as seis cópias de logs anteriores também passaram na verificação
após o teste. Cópias e recibos ficam exclusivamente no cache local ignorado pelo Git.

**Hipóteses atualizadas.**

- **Ganhou sustentação:** a falha pode ser reproduzida no caminho local de
  inicialização por URI, com runtime/CWD/thread próximos aos do agente. O fluxo
  Android, autenticação e transporte HTTPS não são necessários para reproduzi-la.
- **Perdeu sustentação:** um defeito exclusivo da requisição Samsung/HTTPS ou
  necessidade da presença do agente como solicitante. Nenhum pedido remoto foi
  enviado; o histórico permanece com exatamente dois pedidos antigos.
- **Permanece possível:** uma interação Steam–GameManager64/AMD sensível a URI,
  parâmetros, momento ou outro estado de inicialização. Os dois dumps antigos
  comprovavam a cadeia profunda; a coincidência do novo evento torna uma causa
  comum plausível, sem provar a pilha nova ou a API interceptada.
- **Não foi separado:** URI versus CWD inicial versus thread versus intermitência.
  Há agora três falhas por URI/contexto semelhante e um sucesso sem argumentos;
  a amostra ainda não prova que toda URI falhe nem que o atalho sempre funcione.
- O serviço AMD ativo e a DLL carregada também existiam no sucesso anterior.
  Portanto, sua mera presença não explica a diferença, e nenhuma correção ou
  parada de serviço foi justificada como solução comprovada.

**Próximo procedimento de menor risco, somente proposto:** obter autorização
para analisar **localmente e em leitura o novo dump 20108**, comparando a pilha,
instrução e módulos com os dois anteriores pelo motor oficial já disponível.
Isso pode confirmar ou afastar a recorrência da mesma cadeia GameManager64 sem
provocar outra inicialização. Não fazer novo teste físico, mudar CWD do produto,
editar associação, parar serviço AMD ou modificar driver antes dessa comparação.

**Preservação final.** Zero permissões remotas, dois comandos históricos e zero
pendentes, por SQLite `mode=ro`, antes/depois. Agente HTTPS permanece PID 24880
no listener existente; não foi reiniciado nem recebeu comando de execução.
Nenhuma alteração funcional, ADB, APK, WoL, pareamento, credencial, Registro,
firewall, driver ou serviço. Nenhum processo foi encerrado por nossas ferramentas.
Os 86 registros de originais/recuperação passaram novamente. Validação documental
do índice inclui guard de WakeBridge; não foi realizado novo teste físico de WoL.
