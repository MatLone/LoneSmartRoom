# Validação visual complementar — registro parcial

27/10/2026, America/Sao_Paulo. Base preservada: `7eed61a`.

**Windows: retomada GPU não homologada.** A instrumentação não capturou a
restauração e o protocolo completo ultrapassou o limite de 120 segundos.
**Samsung: uma abertura normal foi posteriormente gravada**, após a confirmação
manual do usuário. A splash nativa permanece **inconclusiva**: o processo estava
em cache e a gravação mostra o retorno à interface. Não houve reinstalação,
limpeza de dados ou repetição física. Ver [adendo da splash Android](ANDROID-SPLASH.md).

## Windows — fatos e limitações

Uma única abertura do executável dev.7 instalado. Antes dela: 116 arquivos da
instalação conferidos; nenhum Electron/coletor/ADLX residual; mesma instância
HTTPS autenticada, listener único 8776, banco íntegro e zero grants.

O aplicativo abriu inicialmente como widget, conforme a preferência persistida.
Foram observados widget, dashboard e aba Monitoramento. Acionou-se a opção
explícita de minimizar para bandeja. A consulta visual imediatamente após ocultar
retornou `window is not a usable app window`; isso não demonstra crash.

O usuário confirmou restauração pelo ícone LONE e posteriormente Sair pelo menu
da bandeja. Porém, **a confirmação manual não substitui as capturas da GPU**.
Não houve captura no instante da restauração ou em +2/+5/+10 segundos.

### Falha identificada no procedimento de captura

O roteiro executado não cumpriu o planejamento de observação anterior ao clique:

| Marco | Tempo desde a solicitação de abertura |
|---|---:|
| Captura inicial do widget | 1,74 s |
| Captura do dashboard | 20,30 s |
| Captura da aba Monitoramento | 31,78 s |
| Início efetivo da busca automática da janela restaurada | **89,73 s** |
| Encerramento da busca | **96,09 s** |
| Janela efetiva dessa busca | **6,35 s** |

A preparação e o encadeamento das ferramentas durante a sessão consumiram o
orçamento reservado à evidência essencial. Houve 37 consultas de janelas nessa
busca e nenhuma retornou o alvo. Os registros não permitem determinar o instante
real do clique do usuário, nem separar atraso de observação de uma limitação
da enumeração de janelas. Não se atribui o resultado a um defeito da GPU, do
aplicativo ou à interação do usuário.

O observador parou aos **118,23 s de vida do processo**, ainda com Electron,
IPC, coletor e ADLX ativos. Seu resultado original `ok:false` foi preservado.
O código **259** nesse recibo significa `STILL_ACTIVE`, não uma exceção ou código
final de crash.

A verificação posterior confirmou todos os componentes encerrados e zero pipes,
após a confirmação de Sair do usuário. Essa verificação terminou aos **222,19 s
desde a solicitação de abertura**. O instante exato da morte dos processos não
foi registrado depois do término do observador. Portanto:

- não se comprova saída dentro dos 120 segundos;
- o procedimento completo de validação não terminou no prazo;
- não se apresenta a sessão como aprovada;
- nenhuma segunda abertura, parada forçada ou reparo foi realizado.

As capturas anteriores à minimização mostram a interface preenchida, mas não
fornecem evidência suficiente de idade e origem após restaurar. A árvore de
acessibilidade obtida nesses pontos não reteve os detalhes de idade/ingresso
necessários. Esses números não foram usados para validar retomada, frescor,
CPU/RAM/discos após restauração ou descarte de frames antigos.

### Capturas reais disponíveis — somente antes da bandeja

- [Widget inicial](captures/01-initial.jpg)
- [Dashboard](captures/02-dashboard.jpg)
- [Monitoramento antes de minimizar](captures/03-monitor.jpg)

São arquivos retornados pela captura do aplicativo instalado, sem retoque ou
geração de imagens. A extensão pública corresponde ao JPEG original do capturador;
os hashes e horários estão em `evidence/captures-provenance.json`. Não foram
usadas capturas da sessão anterior como se fossem desta restauração.

## Samsung — preparação e dependência manual

ADB autorizado, Galaxy S25 FE SM-S731B, Android dev.9/código 23. Conferidos em
leitura: identidade do diretório de dados preservada, WoL salvo igual à cópia
protegida e zero grants no agente. Não foram expostos valores de configuração ou
credenciais.

Abriu-se a tela Recentes para localizar e fechar normalmente somente o LONE.
O cartão não estava na página visível. Foi solicitada ao usuário a ação:

> Fechar somente o cartão Lone Smart Room pelo gesto normal dos Recentes,
> sem Fechar tudo; deixar a tela inicial com o ícone LONE visível, sem abri-lo.

No checkpoint `ce88c0f`, ainda não havia confirmação dessa preparação. As
consultas de leitura encontravam o processo/tarefa LONE e a última árvore visual
não mostrava o ícone da tela inicial pronto para o toque. Nenhum gesto foi
enviado concorrentemente à ação manual solicitada. Na continuação autorizada,
o usuário confirmou o fechamento normal e a tela inicial foi conferida antes
da única abertura gravada.

Naquele checkpoint, o gravador e o decodificador estavam apenas preparados.
Posteriormente, criou-se o marcador exclusivo `android-launch-once.json` e
gravou-se uma única abertura pelo ícone observado. O marcador de preparação
anterior não constitui uma segunda tentativa. Não se identificou splash nativa
centralizada na gravação; nenhuma imagem de asset estático foi apresentada como
captura nativa.

A execução Android utilizou a autorização original, sem nova confirmação por
comando. Não se utilizou `am force-stop`, limpeza, desinstalação, reinstalação
ou mudança de segurança para obter um cold start. A abertura não será repetida
automaticamente para tentar capturar a splash.

Imagens dos Recentes, que contêm outros aplicativos, permaneceram em cache local
ignorado e não foram incluídas no Git.

## Preservação comprovada após encerrar o Windows

- Nenhum Electron, coletor, intermediário ou ponte ADLX residual; zero pipes de
  monitoramento na conferência posterior.
- Agente original: supervisor efetivo **2096**, worker **14908**, mesma imagem,
  argumentos, criação e cadeia. Listener único **8776**, status autenticado
  HTTP 200, **TLS 1.3**, hostname e pinagem validados.
- Banco íntegro; identidades/segredos cifrados/permissões com os mesmos digests;
  **zero grants**. Nenhum comando operacional enviado.
- Configuração e certificados protegidos com os mesmos hashes.
- Instalação dev.7: **116 arquivos** conferidos novamente. Backup
  `Windows-before-dev7-20261026T152048Z`: **194 arquivos** e manifesto íntegros.
  Nenhum backup foi excluído ou restaurado.
- Preferência automática de bandeja continua desligada. Modo final dashboard,
  persistido normalmente pelo próprio aplicativo durante o teste. Não houve
  edição manual do perfil.
- HKCU Run e regra de firewall pertinente com hashes iguais antes/depois.
  Não houve investigação ou correção da inicialização automática.
- Sem alterações nos aplicativos, APK, agente, serviços, tarefas, drivers,
  certificados, credenciais ou mecanismos de segurança. Nenhum novo adaptador
  da Central de Diagnóstico foi ativado.
- Nenhum WoL, Steam/CS2 ou comando de energia foi executado pelo teste. TLS
  10054 não foi reproduzido. Demais pendências permanecem abertas.

## Próximos passos, sem nova execução automática

1. A abertura Android foi realizada; a splash continua inconclusiva. Uma futura
   observação de início a frio natural exigirá autorização própria, sem provocar
   encerramento forçado ou alterar o aplicativo para prolongar a splash.
2. O Windows exige **nova autorização específica**, pois a sessão complementar
   foi consumida sem homologação. Não iniciar outra sessão nesta entrega.
3. Em um protocolo futuro, deixar todo o sampler carregado antes do lançamento;
   confirmar a prontidão da interação manual; armar a observação antes de pedir
   o clique de restauração; priorizar Sair se a captura não estiver pronta. Não
   escrever o roteiro de captura durante o tempo medido. Uma falha de ferramenta
   deve resultar em registro inconclusivo, sem flexibilizar frescor ou prazo.

Os recibos originais de falha e a verificação posterior de ausência de resíduos
foram preservados separadamente. Reverter este commit documental somente retira
o relatório; não restaura aplicativos ou autoriza rollback operacional. O agente
deve permanecer ativo. Checkpoints e backups anteriores permanecem preservados.
