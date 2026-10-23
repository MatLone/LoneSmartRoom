# Steam: teste único pelo atalho Windows — 23/10/2026

**Resultado: abertura bem-sucedida nesta tentativa.** A biblioteca Steam foi
confirmada visualmente; o processo permaneceu ativo nas 58 amostras da janela de
60,05 segundos e continuava respondendo na leitura posterior, aproximadamente
73 segundos após o lançamento. Não houve segundo lançamento, teste de CS2 ou
acionamento pelo Android/agente. Este resultado não demonstra estabilidade de
longo prazo nem resolve a causa das duas falhas anteriores.

Horários locais: America/Sao_Paulo (UTC−03:00). Recibo resumido:
[steam-windows-shortcut-results.json](steam-windows-shortcut-results.json).
Análise anterior: [STEAM-DUMP-COMPARISON.md](STEAM-DUMP-COMPARISON.md).

## Procedimento e evidências

- Antes do teste, às 13:48:21, não havia `steam`, `steamwebhelper`,
  `steamservice` ou `cs2` ativos. O Steam Client Service estava parado, Manual.
- AMD External Events Utility estava Running/Auto, PID 2992, com `atiesrxx`
  na sessão 0 e `atieclxx` na sessão interativa 1. AMD Crash Defender também
  estava ativo. Foram registrados somente processos e serviços relevantes,
  sem linhas de comando completas ou ambiente.
- Às **13:48:55,703**, foi solicitado uma única vez o atalho original
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Steam\Steam.lnk`, por
  `Start-Process -FilePath` (ShellExecute do Windows). O link foi validado antes:
  destino `C:\Program Files (x86)\Steam\steam.exe`, sem argumentos e com diretório
  de trabalho `C:\Program Files (x86)\Steam`. Não foi usada a URI do agente.
- Um recibo criado exclusivamente antes da chamada impede repetir o script
  acidentalmente. O retorno de ShellExecute não foi tratado como prova de sucesso;
  foram observados os processos e a janela real em seguida.
- `steam.exe`, PID **10892**, sessão 1, permaneceu ativo e respondendo; a janela
  da biblioteca pertence a `steamwebhelper`, PID **4900**. A janela existente foi
  trazida ao primeiro plano para confirmar sua apresentação, sem abrir outro
  processo. Não foram feitas interações com jogos, configurações ou autenticação.
- Versão de arquivo observada: **11.15.70.27**, igual à registrada nas falhas
  anteriores. O Steam Client Service passou a Running/Manual, PID 2176, durante
  a inicialização normal do cliente; não foi iniciado/parado por comando nosso.
- **Zero eventos Steam/steamwebhelper 1000 ou 1001** entre 13:48:55,703 e
  13:50:29,854. Uma primeira consulta posterior teve erro de conversão de data;
  ela foi corrigida e repetida somente em leitura. O intervalo acima corresponde
  à consulta válida, não ao resultado incompleto. A ausência de eventos não foi
  usada isoladamente para concluir sucesso.
- Nenhum dump novo `steam.exe.*.dmp` na pasta examinada. Os dois originais em
  `%LOCALAPPDATA%\CrashDumps` mantiveram tamanho, data de escrita e SHA-256 exatos.
  Não houve leitura adicional do conteúdo de memória, compartilhamento de dumps
  ou habilitação de novas coletas.

## Hipótese AMD e limites da conclusão

Na Steam que abriu corretamente, a enumeração de módulos confirmou
**`C:\Windows\System32\GameManager64.dll` e `detoured.dll` carregados**.
AMD External Events Utility continuou Running/Auto com o mesmo PID antes/depois.
Portanto, a presença desse serviço e desses módulos **não foi suficiente para
provocar crash nesta tentativa**. Isso não descarta uma interação intermitente,
condição de corrida, ordem de inicialização ou reentrada no componente AMD.

Os dumps anteriores continuam sendo evidência local concreta da cadeia profunda
em `GameManager64+0x3ff5`, com falha final em `ntdll!__chkstk+0x37`. Já o vínculo
causal específico com o serviço AMD External Events Utility não foi demonstrado
por este teste: não houve isolamento ou alteração do serviço.

Foi encontrado um relato original de usuário de **16/10/2026**, com comentários
de 19–20/10, sobre Steam, GameManager64 e AMD External Events Utility. O autor
descreve comportamento dependente de outros aplicativos/ordem de inicialização.
É evidência anedótica externa, com versões e hardware diferentes; as afirmações
de hook específico e corrida feitas ali não foram comprovadas neste PC.
[Relato original no AMDHelp](https://www.reddit.com/r/AMDHelp/comments/1x7ld0h/psabug_radeon_users_with_steam_crashing_at_launch/).

As notas oficiais AMD 26.10.1, atualizadas em **20/10/2026**, listam problemas de
crash associados a overlays em determinados cenários, mas não identificam esta
recursão Steam/GameManager64 nem confirmam esse serviço como causa. Não foram
aplicadas as intervenções sugeridas nos relatos.
[AMD: notas 26.10.1](https://www.amd.com/en/resources/support-articles/release-notes/rn-rad-win-26-10-1.html).

O sucesso pelo atalho fornece o controle independente antes ausente. **Não prova
que o agente cause o crash**, nem que esteja isento: ainda diferem caminho de
ativação, momento, ordem de inicialização e estado de outros aplicativos.
O CWD correto também já constava nos dois dumps anteriores; não há base para
alterar o diretório de trabalho como correção comprovada.

## Preservação e próximo procedimento

Zero permissões remotas de abertura e exatamente dois pedidos Steam históricos
foram confirmados antes/depois por SQLite somente leitura. Steam/CS2 continuam
bloqueados no agente. Não houve reinício do agente, alteração de APK, Android,
credenciais, pareamento, WoL, firewall, Registro, drivers ou serviços AMD.
Nenhum processo foi encerrado. A Steam foi deixada aberta.

O próximo procedimento de menor risco é **comparar em leitura os registros de
inicialização bem-sucedida com os das falhas e revisar o handler Windows da URI
`steam://` e o contexto do executor**, sem novos lançamentos. Se ainda for
necessário um teste físico, planejar separadamente uma única abertura local por
URI, com autorização nova, somente após o usuário fechar a Steam normalmente.
Não testar a URI com o cliente atual aberto: isso mediria apenas entrega a uma
instância existente. Não habilitar comandos remotos ou executar CS2 para essa
comparação. Um eventual teste de isolamento do serviço AMD exige autorização
específica e plano de restauração; não é a primeira intervenção recomendada.

Recibos detalhados permanecem locais em `.cache/validation/steam-shortcut-*`,
fora do Git. Somente o relatório e o resumo sanitizado são versionados.
