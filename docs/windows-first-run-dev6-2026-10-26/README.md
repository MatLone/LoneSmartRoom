# Primeira sessão instalada Windows dev.6 — resultado parcial

**Estado final recuperado: dev.6 instalada e fechada, sem processos de monitoramento
ou pipes residuais; agente HTTPS original ativo. O protocolo físico NÃO foi aprovado:**
o limite de 180 s não foi cumprido, e parte das verificações ficou pendente.

Base `acda97e`, branch `feature/ui-migration-preview`, checkpoints e backups
preservados. Uma única abertura do executável instalado; sem reinstalação,
compilação, portátil, correções funcionais, jogos ou carga artificial.
[Resumo estruturado](summary.json).

## Cronologia e limite excedido

Horários locais em America/Sao_Paulo, UTC−03:00, **26/10/2026**:

| Momento | Evidência |
|---|---|
| 09:12:20,346 | Criação do processo principal 20660; início da sessão pelo horário real do processo |
| 10,2 s | Captura do widget inicial, sensores já disponíveis pela acessibilidade |
| 19,2 s | Widget na aba Monitoramento, com CPU/GPU/RAM/temperatura reais |
| 36,3 s | Dashboard completo, mesma janela 262382 |
| 69,3 s | Rolagem para GPU/armazenamento |
| 83,3 s | Gamer Launcher, ações bloqueadas |
| 99,3–114,3 s | Painel de permissões aberto e fechado |
| 128,3 s | Monitoramento novamente no dashboard |
| Aproximadamente 145 s | Minimização explícita para bandeja; processos permaneceram ativos |
| 180 s | Prazo autorizado, sem confirmação de encerramento |
| 185,314 s | Observador finalizou seu registro; aplicativo e dois pipes ainda ativos |
| 09:17:44 | Conferência somente leitura ainda encontrou sete processos, pelo menos **323,8 s** após a abertura |
| 09:47 | Após o usuário informar “pronto”, confirmados aplicativo/componentes encerrados e pipes ausentes |
| 09:58 | Conferência final: agente original autenticado, zero grants, aplicativo fechado |

**185,3 s é a duração do registro de desempenho, não a duração total da aplicação.**
O instante exato de Sair não foi capturado; o aplicativo ficou ativo além de 323,8 s
e já estava fechado na conferência das 09:47. Não se afirma encerramento no prazo.

O planejamento das interações/capturas consumiu a margem reservada para assistência
manual na bandeja. O observador ainda registrou cinco segundos além do limite.
Não houve repetição, kill ou reinicialização para compensar isso. A observação foi
interrompida e foi solicitado apenas Sair manualmente. **Não há evidência de que um
pedido Sair tenha sido recebido e falhado dentro do prazo**; o que faltou foi
concluir/confirmar esse fluxo a tempo. O usuário informou a conclusão posteriormente.

## Pré-verificação

- Versão dev.6 confirmada por PE, ASAR e registro; recursos e manifesto íntegros.
- Nenhum Electron, intermediário, coletor, ponte ADLX ou pipe anterior.
- Perfil inicial com 77 arquivos e backup pré-dev.6 verificados antes da abertura.
- Agente original identificado por imagem, argumentos, criação e parentesco, não
  somente por PID. TLS 1.3, certificado/hostname/pin, HTTP 200 e zero grants.
- Nenhuma dependência, driver, elevação ou interface de rede nova.
- Observador separado, com handles de consulta e contadores de recursos, sem
  leitura do conteúdo da memória, cliente IPC ou controle de processos.

O aplicativo foi aberto normalmente pela ferramenta Computer Use. Não houve
injeção, flags de depuração, alteração do ASAR ou instrumentalização dos provedores.

## Interface e sensores observados

Identidade oficial, título neutro, três abas, navegação, rolagem, painel de
permissões e sua saída funcionaram nas capturas. Steam/CS2 permaneceram desabilitados.
Não foi criada identidade desktop; “Comunicação não integrada” é o estado correto
do cliente Electron, separado do coletor local conectado e do HTTPS do Samsung.

O widget inicial mostrou os indicadores compactos; o dashboard exibiu os detalhes.
A alternância manteve a mesma janela 262382 e processo principal. Não foram
observadas sobreposições relevantes nas áreas capturadas, mas não houve inspeção
completa de todas as regiões no widget nem redimensionamento manual.

| Indicador real | Valores nas observações disponíveis |
|---|---|
| CPU i5-12400 | Aproximadamente 5,2–12,8% nas imagens/textos |
| RAM | 10,3–10,4 GiB usados; total utilizável 15,8 GiB; disponível aproximadamente 5,4 GiB |
| GPU RX 6750 XT | 1–5% |
| Temperatura / hotspot | 53 °C / 55–56 °C |
| VRAM usada / total | 908–942 MB / 12.272 MB, unidades nativas ADLX |
| Clock | 118–205 MHz |
| Potência | 36–37 W |
| Ventoinha | 492–495 RPM |
| C: | 475,6 GiB de capacidade, 236,5 GiB disponíveis, 50,3% ocupado |
| D: | 447,1 GiB de capacidade, 242,1 GiB disponíveis, 45,9% ocupado |
| I/O | Zero válido de leitura; gravações C: observadas até 1,53 MiB/s; D: com zero válido |
| Atividade PDH | Valores `<0,1%` e estado Indisponível; sem substituir ausência por zero |

São **observações esparsas da interface**, não extremos garantidos de todas as
amostras do SDK nem médias da sessão inteira. A árvore de acessibilidade às vezes
atrasou em relação à pintura da nova aba. As imagens e textos foram preservados
separadamente; [leituras das imagens](evidence/visual-readings.json) não são
apresentadas como payloads brutos. [Análise](evidence/analysis.json) registra contagens
e estatísticas apenas dos valores efetivamente extraídos dos textos.

Uma instância por componente foi observada: intermediário **19876**, coletor
**14052**, ponte ADLX **19092**; Electron principal **20660**, filhos 1688/21668/20708
e um filho transitório 21760. Não confundir subprocessos Chromium com dashboards
duplicados. A ponte permaneceu a mesma além dos antigos 82 s, sem bootstrap repetido.
Dois nomes de pipe foram observados: métricas e lease GPU. O observador não os abriu.

## Frescor: evidências e limites

- Metadados reais mostraram cadência GPU ativa de **2 s**, limite de exibição
  **3 s**, idades de ingresso arredondadas **0,3–0,4 s** e cache **0,7–2,3 s**.
  Estado válido e conteúdo evoluindo foram observados; idades mantêm significados
  distintos, conforme a política aprovada.
- O limite de ingresso **1,5 s** e exibição inativa **11 s** estavam nos arquivos
  instalados já verificados, preservados byte a byte. Não houve flexibilização.
- Não foi provocado timestamp inválido, futuro ou antigo. O primeiro frame não
  foi capturado; na primeira observação aos 10,2 s já existiam leituras válidas.
- O protocolo de produção não expõe contadores nativos completos. **Frames válidos
  e rejeitados totais são desconhecidos, não zero.** Não foram inventadas contagens.
- Não foi capturado “Atualizando” após restauração, nem a cadência inativa de 10 s
  no hardware. A restauração e esse comportamento permanecem pendentes. Não se
  substitui teste físico pelos testes simulados anteriormente aprovados.
- Cadência efetiva das métricas não foi medida continuamente: os textos informam
  1 s nos básicos e 2 s na GPU, mas capturas espaçadas não comprovam jitter de
  cada sensor. O intervalo de aproximadamente 1 s abaixo é do observador de processos.

## Desempenho registrado

Janela do observador: **185,314 s**, incluindo a extrapolação indicada acima.
GetProcessTimes (kernel+user), normalizado por 12 processadores lógicos e tempo
observado; RSS soma working sets, podendo duplicar páginas compartilhadas.
Observador externo excluído dos totais. Picos de CPU são buckets observados de
aproximadamente um segundo, não picos instantâneos; descoberta de processos pode
concentrar CPU de startup no primeiro bucket disponível.

| Componente | CPU média da máquina | Pico CPU observado | RSS média MiB | Pico RSS MiB |
|---|---:|---:|---:|---:|
| Electron, somados seus filhos | 0,6001% | 4,0347% | 368,28 | 474,16 |
| Coletor Python | 0,0492% | 3,5140% | 31,82 | 32,25 |
| Intermediário IPC | 0,0330% | 4,2952% | 24,00 | 24,29 |
| Ponte ADLX | 0,0232% | 2,6030% | 24,64 | 25,08 |
| Total simultâneo observado | **0,7054%** | **10,6728%** | **448,74** | **555,72** |

Picos dos componentes não devem ser somados, pois podem ocorrer em momentos
diferentes. Intervalos do observador: média **1,00035 s**, mínimo 1,00006 s,
máximo 1,00103 s. [Recursos completos](evidence/resources.json).

Referência de desenvolvimento: 0,529% CPU, 454,22 MiB RSS média, 480,73 MiB pico.
A CPU média e o pico residente desta observação foram maiores; a média residente
foi menor. Condições não equivalentes: versão empacotada, perfil, acessibilidade,
capturas, transições visuais e duração diferentes. **Não se conclui regressão nem
se atribuem diferenças exclusivamente à GPU.** Não foi medido o custo da aplicação
entre a saída do observador e o encerramento manual posterior.

## Bandeja, encerramento e pendências físicas

| Item | Resultado |
|---|---|
| Alternar widget → dashboard | Observado na mesma janela |
| Navegar três abas / rolar / painel | Observado |
| Minimização explícita para bandeja | Janela oculta, mesmos processos ativos |
| Minimização normal para barra de tarefas | Não testada |
| Redimensionamento manual | Não testado |
| Restaurar pelo ícone / mesma janela após restauração | Não capturado |
| Modo Widget pelo menu da bandeja | Não testado |
| Menu contextual e Sair | Conclusão manual informada pelo usuário; menu/instante não capturados |
| Encerrar até 180 s | **Não cumprido** |
| Estado final sem filhos/pipes | Confirmado após a conclusão manual |

O observador inicialmente registrou processos vivos ao atingir seu limite; eles
não foram classificados como órfãos naquele momento, pois o aplicativo ainda
estava ativo. Após a conclusão manual, não restaram Electron, coletor, intermediário,
ponte ADLX ou nomes de pipe do monitoramento. Não foi usado encerramento forçado.
Não se inferiu sucesso de shutdown apenas a partir de envio de comando.

## Logs e diferença de tarefa

O pacote original tinha 116 arquivos. A execução criou somente **debug.log**, 332
bytes; os 116 anteriores e os 114 arquivos de payload mantiveram seus hashes.
A verificação estrita de extras inicialmente sinalizou esse arquivo, que foi
examinado e preservado, sem exclusão. SHA-256:
`9144f2dc7ef0980c4478a0f5c020275765dc7a301ea505567b136c57c9979ad2`.

Duas mensagens de `crashpad/registration_protocol_win.cc:136`, TransactNamedPipe,
erro **0xE9**, às **09:12:21,394** e **09:14:21,399**. Referem-se ao registro Crashpad;
não são o pipe de métricas nem TLS. O aplicativo continuou respondendo nas capturas.
Consulta de eventos 1000/1001 e recuperação de vídeo 4101, de 09:12:19 até 09:49,
não encontrou eventos relevantes. Isso **não prova** que o Crashpad esteja saudável:
a causa do registro falho e a disponibilidade de crash reporting seguem pendentes.
Console do renderer não foi instrumentado; não se declara ausência de toda mensagem
interna. Nenhum mecanismo foi desabilitado ou corrigido.

Run/RunOnce, Inicializar, serviços e firewall tiveram zero diferenças. Nenhuma
tarefa foi criada/removida, mas o hash XML de
`\Microsoft\Windows\Flighting\OneSettings\RefreshCache` mudou. Metadados registram
execução às **09:21:12**, resultado 0. Essa execução foi posterior à janela de
desempenho do observador. Não há evidência de que Lone Smart Room alterou a tarefa,
nem identificação conclusiva do ator/causa da mudança de XML. A ocorrência fica
documentada como **inconclusiva**, sem intervenção na tarefa.

## Dados, backup e agente ao final

- Perfil continua com **77 arquivos**, sem adições/remoções. Vinte hashes mudaram:
  caches, DIPS, arquivos LevelDB/Session Storage e preferências visuais. Não se
  afirma igualdade byte a byte do perfil após uma execução normal.
- Preferências: somente `mode` mudou de widget para dashboard, conforme a ação
  realizada. Posição/dimensões de ambos os modos e demais chaves ficaram iguais;
  bandeja automática continua desligada. Não houve importação ou limpeza de perfil.
- Backup `Windows-before-dev6-20261026T103447Z`: **186 arquivos**, 401609147 bytes,
  manifesto SHA-256 `c8866baa193893a386f22244b20630dcbcdba2a7c74d1daf85be868f659ffcd8`,
  hashes de todos os dados conferidos, ACL exclusiva em 228 entradas. Backups
  anteriores também íntegros. Não se descriptografou armazenamento.
- Mesmo supervisor HTTPS **5024**, worker **18304** e redirectors esperados,
  criação/imagem/argumentos conferidos; único listener LAN **8776**. Na última
  conferência às **09:58**, TLS 1.3, certificado/hostname/pin e status/apps HTTP 200.
- **Zero grants e comandos pendentes**; banco íntegro, identidades cifradas,
  esquema/revogações preservados. Consultas podem atualizar nonce/last-seen.
- 86 arquivos operacionais protegidos e 97 hashes de fontes preparados sem
  diferenças; Android, agente, certificados, credenciais e DLL AMD preservados.
- Sem reinstalação, nova dependência, driver, autostart, jogos, WoL ou energia.
  TLS e encerramento gracioso do agente não foram alterados.

## Capturas e próxima decisão

- [Widget inicial](evidence/01-widget-initial.jpg)
- [Widget com monitoramento](evidence/02-widget-monitor.jpg)
- [Dashboard com GPU](evidence/03-dashboard-monitor.jpg)
- [Armazenamento](evidence/04-dashboard-storage.jpg)
- [Gamer bloqueado](evidence/05-gamer-blocked.jpg)
- [Painel de permissões](evidence/06-permissions-panel.jpg)
- [Painel fechado](evidence/07-panel-closed.jpg)
- [Dashboard antes da bandeja](evidence/08-monitor-before-tray.jpg)

Nenhuma correção foi implementada. O próximo teste exige nova autorização: deve
priorizar bandeja/retomada e iniciar Sair com margem substancial, sem repetir todas
as capturas antes do encerramento. Contagens exatas de frames e cadências exigem
planejamento de observabilidade aprovado separadamente, sem abrir depuração ou
instrumentar silenciosamente a instalação. Não se deve repetir a sessão atual
automaticamente nem usar kill para garantir prazo. Esta entrega é documental.
