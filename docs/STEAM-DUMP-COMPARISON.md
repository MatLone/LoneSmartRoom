# Comparação local dos dumps Steam — 23/10/2026

A hipótese mais bem fundamentada passou a ser **recursão/reentrada anormal
envolvendo `GameManager64.dll`, componente do pacote AMD, com pressão ou
esgotamento de pilha e uma falha posterior no tratamento de exceção**. Os dois
dumps mostram a mesma cadeia de chamadas. Isso é evidência direta de execução
desse módulo na cadeia da falha, além do inventário anterior de programas ativos.
A função privada, o gatilho e uma correção definitiva ainda não estão identificados.

Análise autorizada exclusivamente local, somente leitura. Nenhuma abertura de
Steam/CS2, alteração de driver/configuração ou instalação de depurador foi feita.
Dados comparativos e recibos sanitizados: [steam-dump-comparison-results.json](steam-dump-comparison-results.json).
Horários usados neste relatório: America/Sao_Paulo, UTC−03:00.

**Método e preservação.** WinDbg/CDB não foram encontrados nos locais examinados.
Foi possível usar o **Microsoft DbgEng 10.0.26100.1 já instalado no System32**,
com assinatura válida, por um cliente temporário de APIs oficiais do SDK. Não é
uma instalação completa do WinDbg. A Microsoft documenta que esse motor fornece
o núcleo usado por WinDbg/CDB e permite clientes próprios.
[Microsoft: Debugger Engine Overview](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/debugger-engine-overview).

Foram usados `OpenDumpFile`, `GetStoredEventInformation`, `GetContextStackTrace`,
consultas de módulos/símbolos, desassemblagem e leituras limitadas de código,
CWD e limites da pilha. Não houve attach a processos vivos, execução de comandos
do depurador, extensões ou shell. Execução de alvos, shell e SQM foram
desabilitados na sessão. As imagens locais foram lidas como dados para melhorar
o desempilhamento. Argumentos de pilha, strings arbitrárias, ambiente completo
e saída bruta do depurador não foram registrados.

Durante a preparação do cliente, um erro no mapeamento de métodos variádicos do
SDK falhou antes de `OpenDumpFile`. O mapeamento foi corrigido e validado contra
os índices do header instalado antes das análises válidas. Não foi novo crash
Steam e não alterou os dumps.

Os arquivos foram abertos em seus locais originais, sem cópia ou modificação.
Tamanho, última escrita e SHA-256 permaneceram iguais antes/depois da análise:

| Dump em `%LOCALAPPDATA%\CrashDumps` | Bytes | SHA-256 preservado |
| --- | ---: | --- |
| `steam.exe.20876.dmp` | 17.364.367 | `ae3569578d04cad5f2c2d399851b939c5f91394b152d5786a3f08e1014f470c1` |
| `steam.exe.10876.dmp` | 17.343.512 | `bfe4a7dc39a7e85ac29f39eaae3fe17dcd2a527c77f5d5c77069bdb0d9c2ed03` |

**Símbolos oficiais.** Foram obtidos PDBs exatos de `ntdll`, `KERNELBASE` e
`kernel32` por GET HTTPS em `msdl.microsoft.com`. As solicitações contiveram
somente nome/GUID/age do PDB; conteúdo de dumps não foi enviado. O cache está em
`.cache/steam-dump-analysis/symbols`, fora do Git. As imagens correspondem ao
tamanho/timestamp registrados nos dumps. A sessão exigiu símbolos exatos;
`ntdll` e `KERNELBASE` carregaram PDB (`SymbolType=3`). `kernel32` permaneceu
deferido na cadeia examinada.

A busca do PDB exato `GameManager64.pdb` no servidor público Microsoft retornou
404. Isso não prova que o fabricante não possua símbolos; nesta análise seus
endereços permanecem como módulo+RVA, sem nomes de funções privadas.

**Exceções e comparação.** Os eventos Windows anteriores correlacionam os
dumps aos crashes das 12:51:15,589 e 12:53:16,278. A análise dos arquivos mostrou:

| Campo | Dump 20876 | Dump 10876 |
| --- | --- | --- |
| PID / thread da exceção | 20876 / 24004 | 10876 / 17044 |
| Exceção | `0xc0000005`, leitura | `0xc0000005`, leitura |
| Endereço da instrução | `0x7ffa1d546447` | `0x7ffa1d546447` |
| Símbolo resolvido | `ntdll!__chkstk+0x37` | `ntdll!__chkstk+0x37` |
| Offset no módulo | `ntdll+0x166447` | `ntdll+0x166447` |
| Endereço lido inválido | `0x9d00900000` | `0x46c1100000` |
| RSP | `0x9d00901438` | `0x46c11013f8` |
| StackLimit / StackBase | `0x9d00901000` / `0x9d00a00000` | `0x46c1101000` / `0x46c1200000` |
| Módulos carregados | 122 | 144 |
| Quadros analisados | 512, limite atingido | 512, limite atingido |
| Quadros em `GameManager64+0x3ff5` | 485 na amostra | 485 na amostra |
| CWD Steam no instante da falha | Pasta da instalação Steam | Pasta da instalação Steam |

A instrução é `test byte ptr [r11],r11b`; nos dois casos R11 contém o endereço
de leitura que falhou, **0x1000 abaixo de StackLimit**. `__chkstk` é uma rotina
auxiliar de sondagem de pilha do compilador.
[Microsoft: __chkstk](https://learn.microsoft.com/en-us/windows/win32/devnotes/-win32-__chkstk).
Os atributos reais da página ausente não puderam ser estabelecidos: a consulta
de memória retornou outro intervalo capturado no minidump. Não foi inferido
estado guard/reservado/commit dessa página.

**Pilhas.** Desconsiderando bases ASLR e endereços de pilha, os primeiros
512 quadros têm a mesma sequência módulo/RVA. Os ponteiros de pilha avançam
estritamente; no trecho repetido, o avanço é de **96 bytes por quadro**.
Isso sustenta um encadeamento profundo de chamadas/reentradas, e não apenas
um endereço repetido sem avanço do desempilhamento. O trecho relevante,
lido do ponto da falha para seus chamadores, contém:

```text
ntdll!__chkstk+0x37
ntdll!RtlUnwindEx
ntdll!__C_specific_handler
KERNELBASE!__GSHandlerCheck_SEH
ntdll!RtlDispatchException / RtlRaiseException
KERNELBASE!RaiseException / OutputDebugStringA
crashhandler64 + offsets
tier0_s64 + offsets
ntdll!KiUserExceptionDispatch
ntdll!RtlpLowFragHeapAllocFromContext
ntdll!RtlpAllocateNTHeapInternal / RtlAllocateHeap
GameManager64+0x51384, +0x5107, +0x5e81, +0x32e8, +0x4530, +0x3f90
GameManager64+0x3ff5 repetido 485 vezes dentro da amostra
```

Não são 485 chamadas totais do processo: o limite de 512 quadros foi atingido,
portanto a cadeia pode continuar. O trecho de código que precede o retorno
`+0x3ff5` não estava disponível na leitura do dump; não foi comprovada uma
instrução específica chamando diretamente a própria função. A interpretação
é recursão/reentrada anormal com forte suporte na pilha, não reconstrução de
código-fonte privado.

A presença de `crashhandler64`, `tier0_s64`, `OutputDebugStringA` e funções de
unwind mostra tratamento de exceção ativo no caminho da falha final. É plausível
que o `0xc0000005` observado seja secundário à pilha já pressionada. O registro
original de uma eventual exceção anterior não foi recuperado separadamente;
não foi afirmado que ele tinha código `0xc00000fd`.

**Módulos e origem do componente.** Os 122 nomes normalizados do primeiro dump
também estão no segundo. O segundo acrescenta 22 módulos, incluindo `friendsui`
e componentes Windows de shell, texto e criptografia. As bases variam entre os
processos, mas o padrão de falha e os offsets relevantes permanecem iguais.
A lista completa de nomes está no recibo JSON.

`GameManager64.dll` está em `C:\Windows\System32`, com imagem de 638.976 bytes,
timestamp PE `0x6ac99f78` e arquivo de 631.312 bytes, SHA-256
`29b3eab40f6576a9de2e5f2da1c75a655ea4e4d839d599191ee18fa9e489b4b8`.
Sua versão individual não é fornecida pelos metadados de versão consultados.
O vínculo com AMD foi confirmado localmente por:

- `C:\Windows\INF\oem75.inf`: provider Advanced Micro Devices, Inc., classe
  Display, DriverVer `10/16/2026,32.0.21045.16010`, catálogo `u0205305.cat`.
- O INF inclui `GameManager64.dll` e copia `detoured64.dll` como `detoured.dll`.
- O mesmo INF está associado à AMD Radeon RX 6750 XT instalada.
- Ambos os arquivos têm assinatura de catálogo válida, com emissor Microsoft
  Windows Hardware Compatibility Publisher. Isso não os transforma em DLLs
  do núcleo Windows nem comprova ausência de defeitos.

`detoured.dll` também aparece nos dois dumps. Sua descrição identifica o
marcador da tecnologia Microsoft Research Detours, consistente com instrumentação
do processo; o marcador não identifica sozinho qual API foi interceptada.
AppInit estava desativado e sem lista nesses locais consultados, portanto esse
mecanismo específico não foi confirmado como origem do carregamento.

Não há base para atribuir `GameManager64.dll` à Razer apenas porque existe um
serviço com nome semelhante, nem para culpar genericamente SignalRGB/OpenRGB.
O vínculo instalado comprovado é com o pacote AMD. Ainda não foi identificada
a configuração ou funcionalidade AMD responsável por ativá-lo; overlay,
Anti-Lag ou outro recurso não foram apontados como causa confirmada.

**Diretório de trabalho.** Os dois PEBs mostram que a Steam já usava
`C:\Program Files (x86)\Steam` no momento do crash. O CWD inicial do agente
era a raiz do projeto, mas não permanecia como CWD da Steam na falha. Isso
enfraquece substancialmente a hipótese anterior de CWD como causa direta e não
justifica alterar o launcher agora. Um efeito anterior, antes de a Steam ajustar
seu diretório, não pode ser excluído apenas com esse snapshot.

**Conclusão por nível de evidência.** Está confirmado o mesmo acesso inválido,
a cadeia profunda dentro de GameManager64 em ambos os dumps, sua origem no
pacote AMD, o tratamento de exceção no caminho e o CWD Steam correto na falha.
A hipótese principal é uma interação/recursão desse componente com a
inicialização Steam, levando à pressão de pilha e falha durante o tratamento.
Ela é mais fundamentada que o simples inventário de overlays, mas não estabelece
a função privada, o evento que inicia a recursão, a feature AMD ou uma correção
definitiva. Não há evidência para substituir ntdll ou modificar o agente.

**Próximo teste de menor risco, apenas proposto.** Depois de autorização
separada, realizar **uma única abertura pelo atalho Windows existente**, como
usuário normal, sem mudar configuração e mantendo os grants remotos zerados.
Observar processo/janela e eventos; parar na primeira falha, sem retry ou CS2.
Isso fornece o controle independente ainda ausente e separa o caminho
Android/URI do padrão associado ao componente AMD, sem mudar drivers ou Registro.

Se o mesmo padrão ocorrer, a etapa seguinte seria planejar isolamento reversível
e suportado do componente/feature AMD responsável, somente após identificar o
controle apropriado e obter autorização. Não foi recomendado apagar/renomear
DLLs de System32, editar chaves ocultas, trocar driver, limpar cache ou desativar
antivírus. Nenhuma dessas ações foi executada.

**Estado preservado.** Continuam zero permissões de abertura e somente os dois
pedidos Steam anteriores no banco, consultado em modo somente leitura. Android,
APK, credenciais, pareamento, agente HTTPS, startup e WoL não foram alterados.
O agente não foi reiniciado; nenhum processo foi encerrado. As únicas escritas
foram cache local de símbolos, cliente temporário, recibos sanitizados e estes
documentos. Os 86 registros de originais/recuperação passaram novamente.
