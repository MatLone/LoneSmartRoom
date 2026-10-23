# Três dumps Steam e proposta mínima de launcher — 23/10/2026

**Conclusão:** o dump 20108 reproduz a mesma cadeia dos dois anteriores, incluindo
`GameManager64+0x3ff5` e a falha final em `ntdll!__chkstk+0x37`. O desempilhamento
ampliado deste novo arquivo mostra **10.650 quadros consecutivos em +0x3ff5**,
com avanço de 96 bytes por quadro. A hipótese técnica mais consistente é
recursão/reentrada anormal envolvendo o componente AMD, consumindo a pilha,
seguida de falha durante sondagem/tratamento de exceção. O gatilho privado e uma
correção definitiva ainda não estão demonstrados.

**Iniciar steam.exe diretamente é tecnicamente viável e merece um teste futuro
controlado, mas ainda é uma possível mitigação.** O único atalho sem argumentos
funcionou; não se demonstrou que sempre funcionará ou que CreateProcess evitará
a interação AMD. Nenhuma mudança de launcher foi implementada nesta etapa.

Base documental: `3e622c62c95ad1120bfe37c47955e7847a0d54c9`, branch
`feature/secure-pairing-status`. Horários America/Sao_Paulo, UTC−03:00.
[Resumo técnico sanitizado](steam-three-dumps-results.json).
[Análise dos dois primeiros dumps](STEAM-DUMP-COMPARISON.md).
[Teste Python/URI](STEAM-PYTHON-URI-TEST.md).

**Método e integridade.** O novo dump foi aberto em seu local original:

```text
<USERPROFILE>\AppData\Local\CrashDumps\steam.exe.20108.dmp
17.527.625 bytes; última escrita 23/10/2026 14:09:16,610
SHA-256 dbd1ac5a3e62bb2ab97e5464349468569c547b24b52aee664148d51ecdc9c07a
```

SHA-256, tamanho e data de escrita permaneceram iguais antes/depois das duas
leituras (512 e até 16.384 quadros). Os dois dumps antigos também mantiveram seus
hashes. Não houve cópia/upload/alteração/remoção de dumps, nova coleta, attach a
processos vivos, abertura Steam/CS2 ou instalação de ferramenta.

Foi usado **Microsoft DbgEng 10.0.26100.1 já instalado**, com assinatura válida,
via cliente temporário baseado no SDK local. Os clientes anteriores foram
preservados; a variante nova aceita somente PID 20108, tamanho e hash esperados.
As interfaces/estruturas têm validações ABI antes de OpenDumpFile. Execução de
alvos, comandos de shell, suporte gerenciado e SQM foram desabilitados; não foram
usados comandos do depurador ou extensões. Saída bruta, argumentos de pilha,
ambiente completo e strings arbitrárias da memória não foram gravados.

Os PDBs Microsoft exatos de ntdll, KERNELBASE e kernel32 foram reutilizados do
cache local, com SHA-256 conferido contra os recibos de download oficial anteriores.
Não houve nova solicitação de símbolos nesta análise; o caminho de símbolos é
exclusivamente local. Os três módulos resolveram PDB na leitura profunda.
GameManager64 continua sem símbolos privados. Tamanho/timestamp PE das oito
imagens locais relevantes coincidem com os módulos do novo dump; hashes das
imagens Windows/GameManager64 coincidem com os validados anteriormente. Imagens
foram mapeadas como dados para desempilhamento, nunca executadas.

**Comparação dos três contextos.** A comparação dos dois primeiros usa seus
recibos anteriores; nesta etapa apenas o novo dump foi aberto no DbgEng.

| Campo | 20876 — Android/URI | 10876 — Android/URI | 20108 — Python local/URI |
| --- | --- | --- | --- |
| Evento Windows | 12:51:15,589 | 12:53:16,278 | 14:09:15,422 |
| Thread da exceção | 24004 | 17044 | 23192 |
| Exceção | Leitura `0xc0000005` | Igual | Igual |
| Instrução/endereço | `ntdll!__chkstk+0x37`, `0x7ffa1d546447` | Igual | Igual |
| RVA ntdll | `0x166447` | Igual | Igual |
| Instrução | `test byte ptr [r11],r11b` | Igual | Igual |
| RAX | `0x500` | Igual | Igual |
| R11/endereço lido | `0x9d00900000` | `0x46c1100000` | `0x80c8200000` |
| StackLimit | `0x9d00901000` | `0x46c1101000` | `0x80c8201000` |
| RSP | `0x9d00901438` | `0x46c11013f8` | `0x80c82013f8` |
| StackBase | `0x9d00a00000` | `0x46c1200000` | `0x80c8300000` |
| Leitura abaixo de StackLimit | `0x1000` | Igual | Igual |
| Módulos carregados | 122 | 144 | 144 |
| Primeiros 512 quadros | Cadeia normalizada de referência | Idêntica | Idêntica |
| +0x3ff5 nos primeiros 512 | 485 quadros | 485 | 485 |
| CWD no crash | Pasta Steam | Pasta Steam | Pasta Steam |

As bases ASLR e os endereços de pilha mudam, mas a sequência módulo/RVA dos
primeiros 512 quadros é exatamente igual nos três arquivos.

**Pilha ampliada do 20108.** GetContextStackTrace retornou S_OK e **10.688 quadros**,
sem atingir o limite de 16.384. O método reconstrói a pilha a partir do contexto
registrado da exceção; não imprime argumentos ou executa código do alvo.
[Microsoft: GetContextStackTrace](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/dbgeng/nf-dbgeng-idebugcontrol4-getcontextstacktrace).

O topo mantém __chkstk/unwind/dispatch, KERNELBASE RaiseException/OutputDebugStringA,
crashhandler64, tier0_s64, alocação de heap em ntdll e a entrada na cadeia AMD.
Os quadros **27–10.676**, inclusive, repetem `GameManager64+0x3ff5`, com avanço
estrito de 96 bytes. Entre primeiro e último são **1.022.304 bytes** de intervalo
de pilha, aproximadamente 998 KiB. Não são 10.650 chamadas totais do processo;
é a contagem desses quadros consecutivos na thread examinada.

Abaixo da repetição, em direção à origem da thread, aparecem:

```text
tier0_s64+0x14204
SteamUI+0x91ce34
SteamUI+0x916cdb
tier0_s64+0x119af, +0xc5bf, +0xc649, +0xbe42, +0xd0ef, +0x11bd1
kernel32!BaseThreadInitThunk+0x17
ntdll!RtlUserThreadStart+0x2c
```

Isso relaciona a cadeia à inicialização interna SteamUI/tier0 nessa thread.
Sem símbolos privados, não identifica qual tarefa/função SteamUI iniciou o
encadeamento nem comprova uma API específica de criação de processo interceptada.
Os dois dumps anteriores não foram ampliados: os 485 quadros publicados para
eles eram apenas a amostra limitada a 512, sem contagem total comparável.

**Esgotamento versus outras causas.** O acesso que falha é uma sondagem de pilha;
R11 está uma página abaixo de StackLimit, enquanto RSP permanece 1.016 bytes
acima dele no novo dump. A cadeia repetida ocupa quase todo o intervalo entre
os limites TEB. Esses fatos dão forte suporte a consumo/esgotamento da pilha,
em vez de uma simples atribuição genérica a ntdll ou à presença de um overlay.
__chkstk é uma rotina auxiliar do compilador usada em sondagem de pilha.
[Microsoft: __chkstk](https://learn.microsoft.com/en-us/windows/win32/devnotes/-win32-__chkstk).

Ainda assim, o código final registrado é AV `0xc0000005`, não uma confirmação
separada de `STATUS_STACK_OVERFLOW (0xc00000fd)`. O caminho de tratamento da Steam
está ativo e pode ter produzido uma falha secundária. O registro original de
eventual exceção anterior não foi recuperado. QueryVirtual retornou um intervalo
capturado que não cobre a página inválida; proteção/guard/estado dessa página
não foi inferido. O código imediatamente anterior a +0x3ff5 também não foi
recuperado pelo minidump: não foi comprovada uma instrução de chamada direta a
si própria. A conclusão é recursão/reentrada anormal fortemente sustentada pelo
desempilhamento, sem reconstrução de código-fonte privado. Outros defeitos de
memória não foram excluídos por uma análise integral de heap/hardware.

**Módulos e diferenças.** Os 122 nomes do primeiro dump estão no novo. O novo
acrescenta 22 módulos, principalmente Windows shell/criptografia e friendsui.
Entre os conjuntos de 144 do segundo e do novo, 142 nomes são comuns: saem
textinputframework/textshaping e entram windows.fileexplorer.common/wintypes.
Não apareceu um novo módulo de terceiro que explique a diferença. Nos módulos
comuns, tamanho de imagem e timestamp são iguais; isso não equivale a comparar
todos os bytes de memória. GameManager64 e detoured estão novamente carregados.
A origem AMD do pacote já havia sido comprovada pelo INF/catálogo local; não
foi confundida com o serviço Razer de nome semelhante.

**Hipótese técnica principal.** Uma interação de inicialização interna Steam
com o componente AMD GameManager64 provoca uma cadeia recursiva/reentrante longa,
consome a pilha e culmina em falha durante sondagem/tratamento de exceção. O mesmo
padrão existe em três processos, inclusive sem Android/HTTPS. A função privada,
feature AMD, condição de corrida, API interceptada e gatilho exato não estão
identificados. O serviço AMD ativo e a DLL carregada também estavam presentes no
único sucesso pelo atalho; sua mera presença não basta para explicar o defeito.

**Proposta mínima específica — somente avaliação.** Alterar a integração Steam
em `agent/windows/secure_apps.py::launch_allowed`, depois da validação da allowlist
e do usuário interativo, para chamar um pequeno launcher direto dedicado, por
exemplo `steam_launcher.py`. Preservar `agent.py` v1.5 original, as demais ações
e toda a cadeia de autenticação/claim/deduplicação. O launcher dedicado deverá:

1. Resolver somente a instalação Steam registrada localmente. Nesta máquina,
   HKCU SteamExe/SteamPath e HKLM InstallPath nas visões consultadas convergem para
   `C:\Program Files (x86)\Steam\steam.exe`. O arquivo existe, versão 11.15.70.27,
   Authenticode Valid, signatário `Valve Corp.`. Isso foi consultado
   em leitura, sem executar o arquivo.
2. Canonicalizar e validar um caminho absoluto local, com nome steam.exe, dentro
   da instalação aprovada, arquivo existente e identidade Authenticode/publisher
   Valve verificada por API Windows. Resolver redirecionamentos e rejeitar UNC,
   caminhos ambíguos, conflito entre fontes e destino fora da instalação. Falha
   de validação deve produzir erro seguro, sem busca em PATH ou fallback para URI.
   Não fixar para sempre o hash atual: uma atualização legítima da Steam muda o
   arquivo e precisa de política explícita de revalidação, não liberação genérica.
3. Criar o processo com **lista de argumentos contendo somente o executável**,
   `shell=False`, `executable` absoluto validado, `cwd=exe.parent` e
   `close_fds=True`. Nenhuma URI, flag, caminho ou argumento poderá vir da rede.
   A tabela autorizada continuará sendo por ID: Steam → esse launcher; nenhuma
   seleção genérica de executáveis. Usar o usuário/sessão normal atual, sem
   runas, credenciais alternativas, serviço SYSTEM ou desktop oculto.
4. Usar, por exemplo, `subprocess.Popen`/CreateProcessW, sem shell, flags de
   debugger, elevação, breakaway de Job ou mudança de variáveis. O handle de
   processo permite observar PID/exit code com limites; não herdar os handles
   do HTTPS/arquivos sensíveis. O retorno continua significando despacho, não
   confirmação de biblioteca pronta. Não alterar silenciosamente o contrato de
   status ou declarar sucesso só porque Popen retornou.

No Windows, Popen usa CreateProcess; caminho absoluto e shell=False evitam a
resolução por shell. Fechamento de handles e CWD explícito devem fazer parte da
chamada validada.
[Python: subprocess](https://docs.python.org/3.13/library/subprocess.html#subprocess.Popen),
[Microsoft: criação de processos e herança de handles](https://learn.microsoft.com/en-us/windows/win32/procthread/creating-processes).

A escolha de CreateProcess elimina a resolução de protocolo e permite PID, mas
**difere da ativação do link por ShellExecute** que funcionou. Não impede injeção
ou carregamento AMD no processo Steam nem evita necessariamente a rotina SteamUI
que aparece no dump. O plano é testar um contorno pequeno e reversível, sem
alterar driver ou prometer resolver a causa raiz.

HTTPS, validação TLS, HMAC, nonces, grants por dispositivo, LAN/Privado, fila,
deduplicação e startup independente do Electron permanecem no mesmo fluxo.
Nenhuma migração de dados ou novo APK Android é necessária para essa alteração
interna proposta. **CS2 permanece sem grants e sem teste; não haverá concessão
automática nem encadeamento Steam → CS2.** As permissões Steam também ficam zero
até uma autorização separada para um teste remoto.

**Plano de testes futuro, sem execução nesta etapa.**

- Primeiro, testes com resolver, verificador Authenticode e Popen injetados como
  doubles: caminho válido; ausência/conflito de cadastro; arquivo ausente; UNC,
  redirecionamento ou destino inválido; assinatura inválida/publisher incorreto;
  acesso negado; sessão 0/elevação; ID e argumentos não permitidos. Asserções:
  uma chamada com argv de um item, CWD Steam, sem shell/URI e sem fallback/retry.
- Reexecutar os testes existentes de credencial errada, repetição, revogação,
  autorização específica e fila. Garantir que nenhuma alteração de launcher
  ignora o claim ou habilita CS2/energia. Validar hashes de WoL e inventário,
  sem APK novo e sem executar aplicativos nos testes automatizados.
- Após revisão e autorização física: **uma única abertura local direta pelo
  launcher**, com Steam previamente encerrada pelo usuário e estado AMD mantido.
  Se houver cliente aberto, cancelar sem matá-lo. Observar biblioteca, processos
  e eventos por pelo menos 60 segundos, preservar dumps/logs e parar na primeira
  falha. Considerar eventual handoff/reinicialização legítima do bootstrap: a
  saída do primeiro PID, isoladamente, não prova crash nem sucesso.
- Critério desse teste: janela real da biblioteca, processo Steam no usuário e
  sessão esperados, estabilidade observada e ausência de novo crash correlato.
  Um sucesso ainda é evidência limitada; um plano posterior precisará repetições
  autorizadas em sessões distintas para falar em confiabilidade. Somente depois
  avaliar um teste remoto separado, autorizando Steam exclusivamente no Samsung
  e revogando o grant ao final. CS2 continua bloqueado.

**Reversão.** Implementação futura em commit isolado apenas de launcher/testes.
Em caso de regressão, parar os testes e manter/revogar grants, preservando dados
e evidências. Reverter esse commit específico com Git, sem reset destrutivo,
reinstalação Android, limpeza de dados, restauração de banco antigo ou mudança
de certificado. O caminho URI restaurado continua bloqueado, sem teste automático
ou fallback após falha direta. Uma eventual recarga do agente exige autorização
operacional correspondente; não reiniciar Windows. O checkpoint documental
anterior é `3e622c62c95ad1120bfe37c47955e7847a0d54c9`.

**Preservação e pendência operacional.** As leituras SQLite `mode=ro` confirmam
zero grants, dois pedidos históricos e zero pendentes. Android, WoL, pareamento,
credenciais e fontes funcionais não foram alterados. Os três dumps estão intactos.
Nenhum aplicativo, processo, serviço, driver ou Registro foi modificado.

Na consulta desta etapa, às **19:04:35**, Get-NetTCPConnection não encontrou
listener 8776 (`CmdletizationQuery_NotFound`) e não foram localizados processos
pythonw com o script do agente deste repositório. Isso difere do recibo das
14:10; não determina quando ou por que deixou de estar disponível. Não houve
tentativa de iniciar/reiniciar/corrigir o agente. Antes de um teste remoto futuro,
será necessário confirmar/restabelecer sua disponibilidade sob autorização
apropriada. O banco continua bloqueando os aplicativos. Os 86 registros de
originais/recuperação passaram; a revisão do índice verifica fontes protegidas e
WakeBridge, sem alegar um novo teste físico de WoL.
