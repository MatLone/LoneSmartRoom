# Comparação de inicialização Steam — 23/10/2026

As diferenças comprovadas são **entrada por URI versus executável sem argumentos,
diretório inicial e processo/thread que solicita a abertura**. O protocolo está
apontando para a instalação correta; os logs confirmam que a Steam recebeu a URI
nas duas falhas. Nenhuma diferença identificada demonstra, sozinha, o gatilho da
recursão em `GameManager64.dll`. A hipótese principal permanece uma interação
durante a inicialização envolvendo esse módulo, possivelmente intermitente ou
sensível ao contexto. Não há base para corrigir o agente ou alterar o driver agora.

Coleta exclusivamente de leitura dos componentes examinados, sem novas aberturas
Steam/CS2, attach de depurador, encerramento de processos ou alterações de sistema.
Somente recibos locais e documentação foram escritos. Horários: America/Sao_Paulo,
UTC−03:00. Base: `1d99f5540c31f9660d7922d7c328fa4baf5809fb`, branch
`feature/secure-pairing-status`.
[Resumo sanitizado das evidências](steam-launch-context-results.json).

**Atalho, URI e criação do processo.** Os três links existentes (Menu Iniciar
do usuário, Menu Iniciar comum e Desktop público) têm o mesmo destino Steam,
argumentos vazios, CWD da instalação e `WindowStyle=1`. Foram apenas inspecionados,
sem salvar ou executar links nesta etapa.

| Aspecto | Atalho original, teste anterior bem-sucedido | Agente, duas tentativas anteriores com crash |
| --- | --- | --- |
| Entrada | Link Windows para `C:\Program Files (x86)\Steam\steam.exe` | `os.startfile('steam://open/main')`, executor legado `agent/windows/agent.py:112` |
| Linha de inicialização | Executável sem argumentos, confirmado no bootstrap | `"C:\Program Files (x86)\Steam\steam.exe" -- "steam://open/main"`, confirmado pela associação e bootstrap |
| CWD inicial | Link define `C:\Program Files (x86)\Steam` | API recebe `cwd=None`; CWD atual do agente é a raiz do repositório |
| CWD no instante do crash | Não houve crash; CWD vivo não foi capturado | Os dois dumps já analisados mostram a pasta Steam, e não a raiz do repositório |
| Solicitante | `Start-Process -FilePath <link original>`, Shell do Windows, fora do agente | Thread única `lsr-app-launch` em Python 3.13.3/pythonw, via `ShellExecuteW` |
| Forma de exibição | Link normal; biblioteca confirmada visualmente | `show_cmd=1` no CPython; não pede ocultação da Steam |
| Identidade/sessão | PID 10892 em sessão 1 no teste; não foi solicitado `runas` ou credencial alternativa | PID 24880 em sessão 1, proprietário igual ao Explorer e token não elevado, novamente confirmados |
| Resultado registrado | Janela + processo observados | `executed` significa retorno sem exceção de ShellExecute; não confirma PID/janela ou sobrevivência |

O teste chamado manual foi a ativação do **link original por Start-Process**,
não um clique observado no Explorer. Ele é independente do Android e do agente,
mas seu ambiente histórico não pode ser tratado como idêntico ao do Explorer.
Start-Process normalmente herda o ambiente do solicitante; não foram usados
`-UseNewEnvironment`, `-Credential`, `-Verb RunAs` ou argumentos adicionais.
[Microsoft: Start-Process](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/start-process?view=powershell-7.5).

No CPython utilizado, `operation`, `arguments` e `cwd` são nulos e `show_cmd=1`
quando omitidos; a implementação chama `ShellExecuteW`. Não há `CreateProcess`
direto, CMD, PowerShell ou texto de shell vindo do Android nesse executor.
O diretório padrão da API é o CWD do solicitante. O retorno não permite esperar
o encerramento ou obter o exit status por `os.startfile`.
[CPython 3.13.3: implementação](https://raw.githubusercontent.com/python/cpython/v3.13.3/Modules/posixmodule.c),
[Python: os.startfile](https://docs.python.org/3.13/library/os.html#os.startfile),
[Microsoft: ShellExecuteW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shellexecutew).

O worker do agente não pede elevação ou credenciais alternativas, não muda CWD
nem define ambiente específico para Steam. Também não há inicialização explícita
de COM nesse caminho do código. A documentação ShellExecute menciona requisitos
de COM para certas extensões; não foi comprovado que isso afete este handler.
Essa diferença de thread/API fica como contexto não isolado, sem diagnóstico de
falha COM. Já está comprovado que os processos Steam chegaram a iniciar.

**Registro do protocolo.** Nas consultas HKCU, HKLM e HKCR, em visões 32 e 64 bits,
o comando de `steam\shell\Open\command` é idêntico:

```text
"C:\Program Files (x86)\Steam\steam.exe" -- "%1"
```

O valor é REG_SZ; `URL Protocol` está presente; o executável existe. Não foram
encontrados `DelegateExecute` ou `ddeexec` nesse verbo nem um `UserChoice` para
steam no caminho consultado. A visão HKCR combina cadastro de usuário/máquina;
por isso ambos foram conferidos, sem modificações.
[Microsoft: visão combinada de HKCR](https://learn.microsoft.com/en-us/windows/win32/sysinfo/merged-view-of-hkey-classes-root).

O separador literal **`--`** não foi incluído na antiga coleta que extraía apenas
flags com letras. A inspeção atual registra a linha exata. Ele também aparece nas
duas linhas bootstrap que falharam; não é texto arbitrário enviado pelo Samsung
nem prova de erro no registro. Não houve sinal de desvio para outro executável,
wrapper, argumentos adicionais ou diferença entre as visões consultadas.

**Ambiente, usuário e sessão.** Uma leitura limitada dos parâmetros PEB dos
processos existentes do agente e Explorer confirmou os pontos abaixo. As APIs
pediram somente QUERY_INFORMATION/VM_READ e TOKEN_QUERY, sem escrita, injeção,
suspensão ou criação de dump. Ambiente e linha de comando completos não foram
serializados; nenhum cofre/credencial foi consultado.

- Agente real continua PID 24880, criado às 12:49:28, sessão 1, mesmo proprietário
  do Explorer, não elevado. O wrapper PID 16260 permanece. Listener HTTPS continua
  no mesmo processo. Esses dados são coerentes com os recibos anteriores.
- Explorer: sessão 1, não elevado, CWD `C:\Windows\System32`. Agente: CWD na raiz
  de `Lone_Smart_Room_2.0`. Ambos têm texto de desktop inicial `WinSta0\Default`
  nos parâmetros; isso não comprova o desktop real de cada thread durante os
  lançamentos históricos.
- Nos dois processos estão ausentes `ELECTRON_RUN_AS_NODE`, `NODE_OPTIONS`,
  `NODE_PATH`, `PYTHONHOME`, `PYTHONPATH`, `VIRTUAL_ENV`, `SteamAppId`,
  `SteamGameId`, `SteamOverlayGameId`, `__COMPAT_LAYER`, `QT_PLUGIN_PATH`,
  `QT_QPA_PLATFORM_PLUGIN_PATH` e `_NO_DEBUG_HEAP`.
- Ambos têm 35 entradas PATH, mas as strings PATH diferem. Não foram publicados
  caminhos brutos. Não há evidência de que essa diferença provoque a recursão;
  o handler usa caminho absoluto. Isso também não exclui influência de PATH na
  busca de dependências ou de executáveis auxiliares.
- A Steam e o processo solicitante do teste bem-sucedido já não estavam disponíveis
  nesta coleta. Seus ambientes/tokens históricos não foram recuperados. A leitura
  atual do Explorer é referência e não substitui esses dados. O ambiente completo
  dos processos que falharam tampouco foi comparado nesta etapa.

**Correlação dos logs existentes.** Foram lidos integralmente os arquivos atuais
bootstrap, CEF, console, WebHelper, connection e content (cada um abaixo de 50 MiB),
com saída de classificações técnicas e sem mensagens brutas, contas, URLs ou
argumentos sensíveis. O recorte dos dois crashes foi comparado ao sucesso e ao
encerramento posterior. Timestamps Chromium sem ano foram contextualizados pelo
dia 23/10 e pelo lançamento correspondente; não se atribuiu todo o histórico
CEF ao ano atual nem a estas três tentativas.

| Evidência | Crash 1 | Crash 2 | Atalho bem-sucedido |
| --- | --- | --- | --- |
| Bootstrap iniciou | 12:51:14 | 12:53:09 | 13:48:55 |
| Entrada no bootstrap | `-- "steam://open/main"` | `-- "steam://open/main"` | Sem argumentos |
| Updater build | Oct 21 2026 14:10:53 | Mesmo | Mesmo |
| Verificação concluída | 12:51:14 | 12:53:11 | 13:48:57 |
| Sem atualização a aplicar | Não confirmado no recorte dessa tentativa | 12:53:10 | 13:48:56; novamente 13:50:58 |
| CEF google_update_settings.cc:265 | 12:51:14 | 12:53:11 | 13:48:57 |
| CEF cast_crl.cc:443 | 12:51:17 | 12:53:14 | 13:49:00 |
| Evento 1000 | 12:51:15,589, registro 746 | 12:53:16,278, registro 747 | Nenhum encontrado após o início até a consulta das 13:58:02 |
| Fim observado/registrado | Crash; shutdown WebHelper 12:51:17 | Crash; shutdown WebHelper 12:53:18 | Janela observada anteriormente; shutdown WebHelper 13:52:50 e bootstrap 13:52:51 |

A ausência atual da Steam, combinada com os marcadores de shutdown, ausência de
novo evento e dumps inalterados, é **compatível com encerramento organizado**.
Não comprova quem solicitou o fechamento nem fornece o exit code. Não houve
encerramento por nossas ferramentas; não se reclassificou automaticamente como
crash tardio.

Os parâmetros técnicos do launcher WebHelper coincidem entre as três tentativas,
inclusive `--disable-gpu` e `--disable-gpu-compositing`. Foram apenas observados;
nenhuma configuração gráfica foi alterada. Os nomes de flags foram comparados,
sem publicar seus argumentos de conta/identidade. Não foi confirmado crash de GPU
nos recortes classificados. As mensagens CRL/google_update aparecem também no
sucesso: não são evidência diferencial suficiente para corrigir certificados,
Registro, GPU ou cache.

Não foram encontradas referências a `GameManager64` ou `vulkandriverquery` nos
recortes técnicos examinados desses seis logs. Isso não demonstra ausência dos
módulos/processos nem valida a corrida específica descrita por terceiros.
As pilhas anteriores continuam sendo a evidência direta da recursão/reentrada;
os logs de inicialização não mostram a função privada, duas threads concorrentes
na API interceptada ou o evento que inicia a cadeia.

**Hipóteses atualizadas.** São hipóteses que podem se sobrepor; dois crashes e
um sucesso não permitem medir frequência ou separar estatisticamente as causas.

| Hipótese | Evidência a favor | Limite e prioridade de investigação |
| --- | --- | --- |
| Interação de inicialização Steam/componente AMD, possivelmente intermitente | Mesma cadeia profunda em GameManager64 nos dois dumps; origem AMD já comprovada | Módulo também presente no sucesso com serviço ativo. Prioridade alta, gatilho não identificado |
| Entrada URI/argumentos/thread/CWD inicial influencia esse gatilho | Diferença concreta em entrada e contexto; duas falhas por URI e um sucesso sem argumentos | Ainda falta uma URI local controlada. Não prova que a URI ou agente seja defeituoso |
| Estado/ordem de outros programas ou corrida | Compatível com sucesso posterior sem desligar o serviço ou remover a DLL | Não há rastreio histórico suficiente para identificar programa, ordem ou corrida específicos |
| CWD incorreto como causa direta persistente | CWD inicial difere | Perde força: os dois dumps mostram CWD Steam correto no instante da falha; efeito anterior não excluído |
| Protocolo desviado, usuário errado ou sessão 0 do agente | Não sustentada pelas consultas atuais e registros anteriores | Handler correto, bootstrap recebe URI, agente é usuário interativo não elevado |
| Erros CEF, arquivos corrompidos ou defeito geral Windows/hardware | Possibilidades gerais | Erros CEF repetidos no sucesso, verificação concluída e mesmo build não fornecem indicação para intervenção; não foram descartados todos os demais defeitos |

Os relatos de outubro sobre AMD External Events Utility permanecem hipótese
externa, já referenciada no [teste anterior](STEAM-WINDOWS-SHORTCUT-TEST.md).
A presença do serviço/módulo é insuficiente para explicar a diferença observada;
uma incompatibilidade específica AMD–Steam pode depender de outras condições.
Não há confirmação de que parar esse serviço resolveria este computador.

**Um único teste proposto, ainda não executado.** Após autorização separada,
fazer **uma abertura local por `os.startfile('steam://open/main')` no mesmo Python
3.13.3 do agente**, com CWD da raiz do repositório, usuário normal/sessão 1 e uma
única thread de trabalho. Não usar HTTPS, Samsung ou concessão remota. Isso
aproxima API, URI, CWD e modelo de thread do executor, mantendo o Android fora
do caminho e sem implementar correção.

1. Confirmar ausência de Steam/SteamWebHelper/CS2 antes da tentativa. Se já houver
   cliente aberto, cancelar sem encerrá-lo. Registrar estado dos serviços,
   versões, sessão e variáveis técnicas selecionadas, sem mudar configurações.
2. Usar um recibo exclusivo para impedir repetição automática. Executar somente
   a chamada fixa acima uma vez; não alterar handler, ambiente, driver ou serviço.
   Não importar/iniciar o servidor nem chamar os executores de energia.
3. Observar janela e processo por pelo menos 60 segundos, com eventos 1000/1001
   e metadados de dumps. O retorno da API será somente despacho. Na primeira
   falha, parar e preservar tudo, sem retry, CS2 ou nova análise de memória automática.
4. Se falhar com o padrão anterior, o Android/HTTPS não será necessário para
   reproduzir o crash; URI/contexto/interação nativa continuam candidatos. Se
   funcionar, o resultado aponta para intermitência/contexto não reproduzido e
   não comprova inocência ou culpa do agente. Um teste único ainda não estabelece
   abertura confiável nem autoriza liberar CS2.

Este teste não isola individualmente CWD, URI e thread, e seu processo pai/ambiente
pode diferir do agente residente. Esses limites devem constar do recibo futuro.
Nenhum script de abertura nova foi criado ou executado nesta etapa.

**Preservação.** Banco aberto por URI SQLite `mode=ro`: zero grants de aplicativos,
dois pedidos históricos e zero pedidos em andamento. Agent HTTPS continua PID
24880; não houve reinício ou requisição de execução. Dumps originais mantêm os
hashes anteriores. Android, APK, WoL, pareamento, credenciais e configurações de
segurança não foram alterados; não houve ADB, builds ou testes físicos. Recibos
detalhados estão em `.cache/validation/steam-*`, fora do Git. A validação dos 86
registros de originais/recuperação e o guard do WakeBridge são registrados junto
ao commit documental, sem alegar um novo teste físico de WoL.
