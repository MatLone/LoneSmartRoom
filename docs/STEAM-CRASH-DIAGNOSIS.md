# Diagnóstico Steam — coleta de 23/10/2026

A Steam sofreu duas falhas nativas durante a inicialização. A causa raiz ainda
não está identificada. O pedido Android chegou ao agente, a associação Windows
recebeu a URI correta e houve criação de processos Steam, seguida de crash.
Não há evidência suficiente para responsabilizar o agente, um overlay, o driver
AMD ou a DLL `ntdll.dll`.

Horários deste relatório: **America/Sao_Paulo, UTC−03:00**. Coleta somente de
leitura, na branch `feature/secure-pairing-status`, partindo do commit
`bd0b0006ce02772e033afbba88b49b933322f9c9`. Nenhuma nova abertura, correção,
reinicialização de processo ou alteração de configuração foi executada.
O [recibo técnico sanitizado](steam-crash-diagnostic-results.json) registra os
dados consultados e as limitações. Os arquivos de diagnóstico em `.cache` não
integram os fontes funcionais.

**Eventos e confiabilidade.** Foram encontrados os dois eventos abaixo em
Application Error, ID **1000**:

| Horário | Registro | Processo/PID | Versão | Módulo / versão | Exceção / fault offset |
| --- | --- | --- | --- | --- | --- |
| 12:51:15,589 | 746 | steam.exe / 20876 (`0x518c`) | 11.15.70.27 | ntdll.dll / 10.0.26100.9711 | `0xc0000005` / `0x0000000000166447` |
| 12:53:16,278 | 747 | steam.exe / 10876 (`0x2a7c`) | 11.15.70.27 | ntdll.dll / 10.0.26100.9711 | `0xc0000005` / `0x0000000000166447` |

Nos dois eventos, o executável é
`C:\Program Files (x86)\Steam\steam.exe`; o módulo informado é
`C:\WINDOWS\SYSTEM32\ntdll.dll`. O executável Steam é x64, apesar do nome
da pasta de instalação. Os PIDs coincidem com os nomes dos dumps existentes.

O histórico usado pelo Monitor de Confiabilidade, consultado por
`Win32_ReliabilityRecords`, retorna exatamente esses registros 746 e 747.
Não são outros dois crashes independentes. Não foi localizado evento **1001**
correspondente à Steam. A configuração existente contém WER `Disabled=1` e,
na política, `Disabled=1`, `LoggingDisabled=1` e `DontShowUI=1`;
`WerSvc` estava parado, com início Manual. Isso é consistente com a ausência
de informação adicional WER; nenhuma dessas configurações foi alterada.

A busca pediu registros desde 09/10, porém o evento Application mais antigo
disponível é de **23/10 às 03:29:50**. Portanto, não é possível afirmar que a
Steam não apresentou falhas nos 14 dias anteriores. A coleta não encontrou
eventos Display/WHEA correlatos no recorte que cobre os crashes; isso não
descarta defeito de driver, RAM ou hardware.

`0xc0000005` indica violação de acesso à memória. A Microsoft explica que uma
DLL de sistema pode ser o local onde o problema se manifesta, após uma falha
originada em outro módulo. O evento sozinho não identifica a instrução, a pilha
ou o causador. [Referência Microsoft](https://learn.microsoft.com/en-us/troubleshoot/windows-server/performance/troubleshoot-application-service-crashing-behavior).

**Logs já existentes.** Foram examinados recortes de `bootstrap_log.txt`,
`cef_log.txt`, `console_log.txt`, `webhelper.txt`, `content_log.txt` e
`connection_log.txt`. A correlação detalhada usou até 6000 linhas finais dos
quatro primeiros arquivos, com mensagens técnicas predefinidas e horários
12:40–13:00. Conteúdo bruto, contas, URLs sensíveis e argumentos completos não
foram gravados no relatório.

- O bootstrap registra `steam://open/main` às **12:51:14** e **12:53:09**,
  coincidindo com os despachos anteriores. Isso confirma que a associação
  encaminhou a URI esperada à Steam.
- O bootstrap concluiu sua verificação às **12:51:14** e **12:53:11**. Na segunda
  tentativa, também indicou ausência de atualização a aplicar. Concluir essa
  verificação não comprova inicialização saudável de todos os componentes.
- O WebHelper registrou inicialização e encerramento próximos aos dois crashes.
  A simples ocorrência da palavra crash em argumentos de Crashpad não foi
  tratada como prova de um crash separado do WebHelper.
- No CEF há falhas de verificação CRL em `cast_crl.cc:443`, às **12:51:17** e
  **12:53:14**, além de erros em `google_update_settings.cc:265`. Não existe
  vínculo causal demonstrado com a exceção do processo principal; a primeira
  mensagem CRL ocorreu depois do primeiro evento de crash.
- O recorte correlacionado não confirmou crash de GPU. Mensagens de outras
  datas presentes no histórico CEF não foram atribuídas às duas tentativas.

**Dumps e relatórios existentes.** Apenas nomes, tamanhos e horários foram
consultados. Nenhum dump foi aberto, copiado, enviado ou submetido a depurador.
Nenhuma coleta nova foi habilitada.

| Arquivo | Tamanho | Última escrita |
| --- | ---: | --- |
| `%LOCALAPPDATA%\CrashDumps\steam.exe.20876.dmp` | 17.364.367 bytes | 23/10/2026 12:51:16,865 |
| `%LOCALAPPDATA%\CrashDumps\steam.exe.10876.dmp` | 17.343.512 bytes | 23/10/2026 12:53:17,373 |
| `C:\Program Files (x86)\Steam\dumps\crash_cs2.exe_20261013232213_1.dmp` | 845.901 bytes | 13/10/2026 23:22:13,673 |

O dump CS2 é anterior a esta tarefa e não indica execução atual. As pastas WER
`ReportArchive` e `ReportQueue` em ProgramData estavam vazias. As equivalentes
do usuário e `C:\Windows\Minidump` não foram encontradas nos locais consultados.
A enumeração de `C:\Windows\LiveKernelReports` foi negada pelo Windows;
não houve tentativa de contornar acesso ou alterar permissões.

A próxima análise de dumps precisa de autorização para tratar seu conteúdo
localmente. Mesmo dumps menores podem conter dados sensíveis; formatos de
triagem não garantem remoção completa desses dados.
[Referência Microsoft sobre dumps](https://learn.microsoft.com/en-us/sysinternals/downloads/procdump).

**Processos e software encontrado.** Na amostra das **13:00:37**, não havia
`steam.exe`, `steamwebhelper.exe`, `steamservice.exe` ou `cs2.exe` em execução.
Nenhum processo foi encerrado. `Steam Client Service` estava parado/Manual;
esse estado isolado não identifica a causa da exceção.

| Software | Evidência encontrada | Limite da evidência |
| --- | --- | --- |
| AMD Software 26.10.1 | RadeonSoftware, AMDRSServ, AMDRSSrcExt, amdow e Crash Defender ativos | Não comprova overlay habilitado nem módulo carregado na Steam |
| SignalRGB 2.5.80 | Cliente, launcher e serviço ativos | Presença de controle RGB não comprova interferência |
| OpenRGB 1.0.0, conforme cadastro instalado | Processo/serviço ativos em sessão 0 | Não comprova injeção no cliente Steam |
| Razer Chroma/Synapse 4.0.827, Cortex 11.12.0.14 e THX | Produtos instalados e serviços Razer/SDK/áudio ativos | Participação no crash não verificada |
| Logitech G HUB | Atualizador, bandeja e agente ativos | Participação no crash não verificada |
| MSI Afterburner 4.6.6 / RTSS 7.3.7 | Instalados; sem processos correspondentes na amostra | Não prova ausência no instante histórico do crash |
| Discord 1.0.9265 / iCUE 5.49.34 | Instalados; sem cliente Discord e com serviços consultados parados | Inventário atual, não histórico de módulos |
| Microsoft Defender | Único antivírus retornado por SecurityCenter2; proteção ativa | Não foi desativado ou reconfigurado |

Os filtros adicionais não encontraram processos GameOverlayUI, Game Bar, OBS,
Overwolf, Nahimic, HWiNFO ou AIDA64. Isso não é um inventário exaustivo de todo
software instalado. A Valve reconhece a possibilidade geral de interferência
por aplicativos em segundo plano; essa orientação não demonstra culpa de
qualquer programa desta máquina.
[Referência Valve](https://help.steampowered.com/pt-br/faqs/view/1F39-DCB4-FF28-5748).

Os dispositivos gráficos consultados foram AMD Radeon RX 6750 XT, driver
`32.0.21045.16010`, e Intel UHD Graphics 730, `32.0.101.6129`. O Windows informa
versão `10.0.26300`, cadastro `26H2`, UBR `9711`. Esses dados identificam o
ambiente; não estabelecem incompatibilidade ou necessidade de trocar drivers.

**Como o agente inicia a Steam.** O fluxo é HTTPS/HMAC e LAN autorizada →
validação/permite apenas IDs Steam/CS2 → grant específico → fila com
deduplicação → verificação de usuário não elevado/sessão diferente de zero →
executor legado. Em `agent/windows/agent.py:112`, a chamada é exclusivamente:

```python
os.startfile('steam://open/main')
```

Não há texto remoto de shell, argumento arbitrário, CMD ou PowerShell nesse
lançamento. O CPython 3.13.3 chama `ShellExecuteW`, usa diretório padrão herdado
e `show_cmd=1`. O retorno sem exceção faz o dispatcher registrar `executed`;
ele não obtém PID, código de saída ou comprovação de janela. O processo do
agente ser oculto não significa que esse código peça ocultação da Steam.
[Documentação Python](https://docs.python.org/3.13/library/os.html#os.startfile),
[implementação CPython utilizada](https://github.com/python/cpython/blob/v3.13.3/Modules/posixmodule.c#L13550).

A inspeção atual confirmou:

- Agente real PID **24880**, wrapper **16260**, sessão **1**, mesmo proprietário
  do Explorer interativo; token **não elevado**. Nenhum deles foi reiniciado.
- CWD efetivo: raiz de `Lone_Smart_Room_2.0`, conforme a configuração da recarga.
  Leitura limitada dos parâmetros PEB e ambiente, sem varredura de heap,
  consulta a cofres, criação de dump ou registro dos valores completos.
- Ausência das variáveis selecionadas `ELECTRON_RUN_AS_NODE`, `NODE_OPTIONS`,
  `NODE_PATH`, `PYTHONHOME`, `PYTHONPATH`, `VIRTUAL_ENV`, `SteamAppId`,
  `SteamGameId`, `SteamOverlayGameId`, `__COMPAT_LAYER` e caminhos Qt consultados.
  O PATH possui 35 entradas; seus valores brutos não foram publicados.
- Associação `steam://` aponta para o Steam instalado e contém placeholder
  `%1`, sem flags adicionais encontradas. O bootstrap recebeu a URI correta.
- Não foram encontradas camadas AppCompat específicas para `steam.exe` nos
  locais HKCU/HKLM consultados, nem chave IFEO específica para esse executável.

Sessão/proprietário não são uma comprovação completa de desktop/window station.
O ambiente da Steam no instante de cada crash não foi recuperado. A entrada de
inicialização por login do agente não define CWD; a recarga usada neste teste
define. Essa diferença futura deve ser considerada no desenho de execução.

**Comparação manual e remota.** O usuário esclareceu que tentou somente pelo
Samsung. A segunda tentativa manual foi outra confirmação no aplicativo,
portanto ambas percorreram a mesma cadeia Android → agente → URI.
Não foi realizado um controle independente pelo atalho do Windows.

| Aspecto | Atalhos Windows existentes, apenas inspecionados | Caminho remoto observado |
| --- | --- | --- |
| Destino | steam.exe instalado, sem argumentos | Associação com URI `steam://open/main` |
| Diretório inicial | `C:\Program Files (x86)\Steam` | Raiz do repositório herdada pelo agente |
| Usuário | Seria o usuário que acionasse o atalho | Mesmo proprietário do Explorer, não elevado |
| Resultado nesta investigação | Não executado | Duas inicializações seguidas de crash |

Existe uma diferença verificável de contexto. Seu efeito precisa de comparação
controlada; ainda não é justificativa para mudar CWD, URI ou associação.

**Hipóteses em ordem provisória de plausibilidade.** A ordem abaixo orienta a
investigação pelo que foi observado, sem probabilidades medidas. Nenhuma causa
está confirmada; as hipóteses podem se sobrepor.

| Ordem | Hipótese | Fundamentação e limite | O que ajudaria a decidir |
| --- | --- | --- | --- |
| 1 | Defeito ou incompatibilidade na inicialização nativa da versão atual do cliente Steam | O executável iniciou, terminou verificação e falhou duas vezes no mesmo módulo/offset. Não distingue bug interno de efeito externo | Pilha, instrução da exceção e módulos do dump existente |
| 2 | Efeito do contexto URI/CWD herdado | Há diferença concreta entre atalhos e agente, mas faltou controle independente | Comparar atalho, URI pelo Windows e Android, após autorização |
| 3 | Interação com módulos de terceiros, captura, áudio ou RGB | Há programas relevantes ativos; não foi verificada injeção na Steam | Lista de módulos e pilha do dump; só então isolamento de um candidato |
| 4 | Outros arquivos/dependências Steam danificados | A verificação de bootstrap reduz esse indício, mas não atesta todos os módulos | Dump e verificações dirigidas, sem apagar caches ou reinstalar |
| 5 | Defeito de driver, componentes Windows ou memória/hardware | Possibilidade geral sem evidência direta adicional neste recorte | Evidência específica antes de qualquer teste ou alteração no sistema |

**O que já foi afastado ou perdeu sustentação.** Para os dois pedidos
registrados, não houve bloqueio de HTTPS, autenticação ou permissão que
impedisse o despacho. Destino ausente/associação apontando a outro executável
não corresponde à consulta atual. O agente não rodava elevado ou em sessão 0.
Não há processo residual Steam na amostra atual. Não foi encontrado flag
especial nas variáveis ou camadas de compatibilidade examinadas.

As assinaturas Authenticode da Steam e das duas cópias consultadas de ntdll
(System32/SysWOW64) são válidas. A versão **numérica** de ntdll é
`10.0.26100.9711`, coerente com os eventos. A versão textual do recurso mostra
`10.0.26100.9549`; essa diferença não foi confundida com troca de DLL ou prova
de corrupção. Assinatura válida não exclui bug, corrupção em memória ou falha
em outro arquivo. A ausência de WHEA/Display não exclui hardware.

**Próximas etapas e correção de menor risco.** A proposta inicial é obter
evidência do dump existente antes de escolher uma correção. Ela evita provocar
outro crash e preserva o estado atual. Requer autorização para analisar
localmente a pilha e os módulos, com saída técnica filtrada e sem compartilhar
o arquivo. Não foram encontrados WinDbg/cdb/dumpchk no PATH nem pacote WinDbg
na consulta feita; isso não é uma busca exaustiva por ferramentas, nem autoriza
instalação automática.

Se ainda for necessária comparação física, propor uma autorização separada
para uma sequência pequena: atalho Windows → mesma URI pelo Windows → Android,
em estados iniciais equivalentes, verificando processo/janela e parando na
primeira falha. Não encerrar processos à força nem incluir CS2 nesse diagnóstico.
Essa comparação diferencia executável, URI e contexto sem mudar configuração.

Somente se houver evidência de que a diferença de CWD provoca a falha, a correção
preferível no Lone seria tornar o diretório do launcher explícito e restrito à
instalação Steam validada, mantendo URI fixa, allowlist, grant e HMAC. Se o dump
apontar outro módulo, a proposta deve ser dirigida a ele, com uma mudança
reversível por vez. Não há base atual para reinstalar Steam, limpar cache,
trocar drivers, desativar antivírus ou substituir DLLs.

Uma melhoria separada de observabilidade pode distinguir “Despachado ao Windows”
de “processo/janela verificados”, sem apresentar retorno de ShellExecute como
sucesso físico. Isso não corrige o crash e não foi implementado nesta etapa.

**Preservação e estado final.** O banco foi consultado em modo somente leitura:
continuam **zero grants de aplicativos** e apenas os dois pedidos Steam já
conhecidos. Steam e CS2 permanecem bloqueados para novos testes. HTTPS continua
no mesmo listener do agente, com perfil Privado, regra LAN e startup por login
preservados. Não houve ADB ou instalação no Samsung, alteração WoL, pareamento,
credencial, firewall, Registro, serviço, driver, arquivo Steam/Windows ou fonte
funcional. Os **86 registros de originais e recuperação passaram** novamente.
A execução original Android permanece na versão v16 validada anteriormente;
essa versão não foi novamente consultada no aparelho nesta coleta.
