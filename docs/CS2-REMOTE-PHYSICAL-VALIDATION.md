# CS2 pelo Samsung — teste único, 23/10/2026

**Aprovado neste teste:** um único pedido pelo Galaxy S25 FE atravessou o canal
HTTPS/HMAC, foi despachado pelo novo executor Steam e abriu o CS2 até o menu
principal. O usuário confirmou o menu utilizável; a interface também foi
verificada visualmente no Windows. Houve **60,8 segundos de observação após a
confirmação do menu**, com o mesmo processo respondendo em todas as 60 amostras.

Checkpoint preservado: `419cdfc3307d404f5542c692a6762254b670fdc7`.
Nenhum fonte funcional mudou nesta rodada. [Recibo sanitizado](cs2-remote-physical-results.json).

| Etapa | Evidência / horário America/Sao_Paulo |
| --- | --- |
| Regressão antes do teste | **70 testes aprovados**, 19,054 s, executores substituídos |
| Recarga exclusiva do agente | 21:22:56; listener antigo PID 6204 substituído pelo PID 13012; wrapper novo PID 19032 |
| Identidade/rede | Mesmo certificado, configuração DPAPI, credenciais e LAN; firewall Privado inalterado |
| Samsung após recarga | Conectado, sem novo pareamento e sem instalação Android |
| Grant temporário | Somente CS2, exclusivamente para a única identidade pareada ativa do Samsung |
| Pedido autenticado recebido | **21:26:22**, exatamente um novo registro CS2 no banco |
| Executor terminou o despacho | **21:26:25**, estado Executado, sem erro |
| Processo real surgiu | **21:26:28,479**, cs2.exe PID **16224**, sessão interativa 1, caminho esperado |
| Menu confirmado | Pelo usuário, seguido de verificação visual da janela Counter-Strike 2 |
| Intervalo de observação após o menu | **21:28:08–21:29:09**, 60,8 s; 60 amostras com CS2 presente/respondendo |
| Verificação visual final | Menu principal continuou renderizado; nenhuma partida iniciada |
| Falhas/hangs correlatos | Nenhum evento 1000/1001/1002 encontrado até a coleta final |
| Dumps novos | Nenhum nos locais verificados; os hashes dos dumps anteriores permanecem iguais |
| Segurança final | **Zero grants**, zero comandos pendentes; Steam e CS2 desabilitados no Samsung |
| Comunicação final | Samsung Conectado; uma instância HTTPS em 172.31.161.169:8776, PID 13012, sem stderr |

## Método e prova de abertura

Antes de recarregar o agente, foram confirmados código limpo no checkpoint,
ausência de CS2 ativo, zero grants/pendentes, identidade TLS preservada, configuração
LAN Privada e a regra de firewall original. O resolvedor validou em leitura a
Steam assinada e a instalação CS2 com criação de processos bloqueada nessa
checagem. A recarga encerrou somente o agente e seu wrapper identificados;
nenhuma configuração de inicialização ou serviço foi alterada.

O novo processo carregou o adapter do checkpoint, cujo ramo CS2 usa somente
Steam validada com `['-applaunch', '730']`, cwd da Steam, `shell=False`, sem
argumentos de rede, URI ou fallback. A Steam existente permaneceu com PID 8916.
O pedido foi feito pela WebView do Samsung e confirmado **uma única vez** no
diálogo nativo Counter-Strike 2. As duas ações tiveram recibos exclusivos que
impediam repetição pelas ferramentas. Não houve pedido de abertura pela API a
partir do PC, nem execução direta de cs2.exe.

O grant foi revogado imediatamente após o despacho terminal, às **21:26:25**,
impedindo novos pedidos enquanto o jogo carregava. O controlador também executou
a revogação em finally e conferiu zero permissões ao terminar. Steam e energia
não receberam grants. O banco real passou de três para quatro comandos, com
exatamente um novo CS2 executado, vinculado à identidade Samsung já existente.

“Executado” foi tratado somente como despacho: a abertura real foi comprovada
separadamente pelo PID/caminho/sessão/horário do processo e pelo menu. A consulta
do sistema usou somente metadados limitados do processo, sem ler memória,
debugger ou injeção. A primeira captura da janela em segundo plano mostrou o
desktop em primeiro plano e não foi usada como prova do menu. Após ativar somente
a janela CS2 já existente, as capturas mostraram o menu, inclusive ao final.
Nenhuma tecla, clique ou entrada de jogo foi enviada; não se acionou Jogar.

## Preservação e limites

Foram consultados Application Error 1000, Windows Error Reporting 1001 e
Application Hang 1002; não houve registro correlato Steam/CS2 no intervalo. Foram
verificados CrashDumps do usuário e dumps locais da Steam, sem novos dumps Steam/CS2
no primeiro local ou candidatos novos no segundo. Não foi habilitada coleta,
analisada memória ou feita transmissão de dumps. Isso não representa busca
exaustiva em todos os diretórios possíveis do computador.

Configuração/certificados e registros cifrados dos dispositivos mantiveram seus
hashes. Pareamento, proteção de credenciais, HMAC, anti-replay, HTTPS, restrições
de rede, firewall e startup foram preservados. Verificação de recuperação:
**86 registros íntegros**. Não realizamos alterações no Android, código/configuração
Wake-on-LAN, drivers AMD, serviços, VAC, configurações gráficas, arquivos/opções
de inicialização do jogo ou configurações Windows. Não houve partida, nova tentativa, instalação Android,
reinício do Windows ou encerramento de Steam/CS2.

Recibos e amostras locais ficam em `.cache/validation/cs2-remote-once-20261023`,
fora do Git; logs brutos, identificadores de dispositivo, conteúdo de memória,
credenciais e imagens com dados da conta não foram incluídos nos relatórios
versionados. **Steam e CS2 foram deixados abertos**, com todos os grants revogados.

O resultado valida o lançamento remoto até o menu nesta sessão, dentro da janela
observada. Não comprova estabilidade de partidas/sessões futuras, estado de VAC
ou a causa original dos crashes Steam. A autorização de teste está consumida;
qualquer nova abertura precisa de autorização específica. Nenhum próximo teste
ou concessão permanente de permissão foi iniciado.
