# Recuperação HTTPS e homologação Windows / Android

27/10/2026, America/Sao_Paulo. Base: `ad2778b`. O bloqueio registrado naquela
pré-verificação foi seguido de autorização expressa para uma única recuperação
manual e continuidade sequencial da homologação.

**Resultado:** agente original recuperado e deixado ativo; Android dev.9/v23
instalado uma vez, com dados preservados e status Conectado; Windows dev.7
testado uma vez e encerrado normalmente. A homologação Windows permanece
**parcial**, pelos cenários não observados listados adiante. A splash nativa
Android também permanece sem comprovação visual suficiente nesta sessão.

## 1. Por que o agente estava offline

Fatos encontrados em leitura:

- Na pré-verificação não havia supervisor, worker, mutex ou listener 8776.
- O último `bootstrap_ready` anterior era de 25/10 às 23:41:17 locais
  (`2026-10-26T02:41:17.735Z`), sem erro posterior de encerramento nos registros
  disponíveis.
- O Windows registrou encerramento e novo boot em 26/10: evento 1074 às
  20:24:30, 6006 às 20:24:37, Kernel-General 12 às 20:25:03 e EventLog 6005 às
  20:25:17 locais. O bootstrap antigo antecede esse boot.

Isso é compatível com a sessão anterior terminando no reboot e não sendo
restabelecida automaticamente. **Não prova por que HKCU Run não restabeleceu o
serviço**, nem se houve despacho da entrada. Não há evidência suficiente para
atribuir a ausência a TLS, corrupção, certificados, Electron ou ADLX. A
inicialização automática continua pendente; recuperação manual não a corrige.

Na preparação do helper desta sessão, a comparação textual da sub-rede falhou.
Host e porta coincidiam; a comparação canônica por `ipaddress.ip_network`, como
no procedimento anterior, confirmou a mesma rede. Corrigiu-se somente essa
comparação no helper de auditoria em cache. Não houve mudança de configuração e
nenhum lançamento havia ocorrido naquele momento.

## 2. Recuperação manual única

Entrada executada: `agent/windows/agent_launcher.py`, SHA-256
`8f137269555ad33b744c4b19b65ac5726785f6d1482ff3182f5f3a495ee32a08`.
Sete arquivos do manifesto da preparação validada conferidos. Python da venv,
argumentos fixos `-I -B` e caminho absoluto do launcher, diretório de trabalho
explicitamente na raiz do projeto. Sem shell, elevação ou launcher alternativo.
O launcher com encerramento gracioso não foi utilizado.

Pré-gates: ausência confirmada de processos/listener/mutex; banco íntegro;
zero grants e comandos pendentes; configuração LAN aprovada, perfil Privado;
certificado vigente e pin correspondente; arquivos protegidos iguais à referência;
logs com ACL restrita à conta. O marcador de tentativa única foi criado antes
da chamada de criação do processo. Não houve segunda tentativa.

| Papel | PID | Pai |
|---|---:|---:|
| Redirecionador venv do supervisor | 16828 | helper de lançamento |
| Supervisor Python efetivo | 2096 | 16828 |
| Redirecionador venv do worker | 8592 | 2096 |
| Worker HTTPS efetivo | 14908 | 8592 |

Os redirecionadores normais da venv não são instâncias operacionais duplicadas.
Imagem, argumentos fixos, criação, árvore, conta, sessão e token sem elevação
foram validados; não se confiou só nos PIDs. Mutex existente retido pelo worker,
com ACL conferida, sem outro lançamento para testar duplicação.

Listener único 8776 do PID 14908, em endereço privado autorizado, sem wildcard.
GET autenticado `/v2/status` HTTP **200**, TLS **1.3**, certificado/hostname e
pinagem conferidos antes de enviar os cabeçalhos HMAC. Credencial existente
usada somente em memória; nenhuma identidade ou grant novo.

A observação de recuperação durou **61,49 s**, com 12 inventários saudáveis e
mesma identidade. O agente foi mantido ativo durante e depois das demais etapas.

## 3. Atualização Android

Galaxy S25 FE identificado por ADB autorizado, modelo **SM-S731B**, Android 16.
Versão inicial: **2.0.0-dev.7, código 21**. APK instalado foi copiado para cache
local para conferência independente, sem alterar o aparelho.

| Campo | Resultado |
|---|---|
| Package | `com.lonesmartroom.app` |
| Nova versão | **2.0.0-dev.9**, código **23** |
| APK | `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.9-v23.apk` |
| Tamanho | 1.246.709 bytes |
| SHA-256 | `92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2` |
| Certificado instalado anterior e candidato | `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8` |
| Apksigner | Assinatura v2 válida em ambos |

Executou-se uma única vez o equivalente exato abaixo, com o serial real
confirmado do Samsung no lugar do marcador:

```powershell
& '<USERPROFILE>\AppData\Local\Android\Sdk\platform-tools\adb.exe' -s '<serial-Samsung-confirmado>' install -r '<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\android\LoneSmartRoom-2.0.0-dev.9-v23.apk'
```

Resultado: **Success**. Não houve `pm clear`, desinstalação, downgrade,
`-d`, `-g`, troca de assinatura ou reconstrução do candidato aprovado. A cópia
do APK efetivamente instalado correspondeu integralmente ao candidato.

### Dados e segurança Android

- As configurações `lone-wol-settings-v1` foram lidas privadamente, comparadas
  após instalar e novamente após a interface, sem publicar seus valores.
- Antes de instalar, configurações WoL e cofre cifrado receberam cópias locais
  seladas com DPAPI e verificação de ida/volta. Os caminhos completos e hashes
  estão no recibo local ignorado, não no relatório público.
- UID, diretório de dados e data da primeira instalação preservados.
- O conteúdo cifrado de `no_backup/agent-v2.enc` permaneceu byte a byte igual
  imediatamente após a instalação, antes da primeira abertura. Consultas normais
  posteriores podem persistir o horário de última comunicação.
- O aplicativo abriu com o pareamento anterior e mostrou **Conectado**, com
  `Agente autenticado acessível`, sem novo cadastro. Isso valida o uso do cofre
  existente nesta atualização; não promete recuperação do Keystore após uma
  hipotética desinstalação.
- Steam/CS2 estavam visualmente bloqueados, com botões desabilitados. Zero grants
  e histórico de comandos inalterado. Nenhum botão operacional foi acionado.

**WoL: configuração preservada, sem teste funcional nesta tarefa.** Nenhum
pacote UDP foi enviado; não se afirma novo despertar físico do PC.

### Validação visual real

Passaram: abertura, versão, cabeçalho oficial com somente E vermelho, símbolo do
ícone oficial na tela inicial One UI, três abas, navegação, rolagem observada,
abertura/fechamento dos painéis de marca, conexão e dispositivo. Painéis de
equipamentos futuros mantiveram controles desabilitados. Não foram editadas
configurações.

A barra de status termina em **97 px**; a marca começa em **112 px**, com
**15 px de respiro**. Não foi detectada sobreposição entre a marca e a barra
de status. Não foram identificados cortes impeditivos nas áreas inspecionadas;
conteúdo abaixo da dobra permaneceu acessível por rolagem. Isso não equivale a
testar todas as escalas de fonte ou orientações do Samsung.

CPU/GPU/RAM/discos remotos continuam explicitamente indisponíveis no Android.
Nenhuma medição fictícia foi apresentada. Não houve marcador `FATAL EXCEPTION`
para o PID atual no buffer de crash consultado.

**Splash nativa: inconclusiva.** A gravação real da abertura foi preservada e
13 quadros foram decodificados localmente com Windows MediaComposition, sem
nova abertura. Os quadros inspecionados registram fundo sólido e depois o
cabeçalho/interface; não comprovam a logo nativa centralizada. Os recursos
assinados mantêm a inspeção estática aprovada da dev.9, mas isso não substitui
verificação visual da splash. Não foi realizado outro cold start para tentar
capturá-la e não se implementou correção.

Houve uma falha transitória de leitura ADB/UIAutomator após abrir. Uma nova
leitura da árvore visual funcionou sem reinstalar, limpar ou reabrir o app.

## 4. Sessão física Windows dev.7

Pré-gates: **116 arquivos da instalação** corresponderam ao manifesto anterior;
backup `Windows-before-dev7-20261026T152048Z`, com **194 arquivos**, conferido;
perfil com **78 arquivos** e preferência automática de bandeja desligada;
nenhum aplicativo/componente de monitoramento residual. A diferença para os
77 arquivos de um inventário mais antigo não foi tratada como perda: comparou-se
o perfil atual antes/depois, com 78 em ambos e nenhum removido.

Nenhuma instalação, compilação, execução portátil ou alteração do código
Windows. Uma abertura do executável instalado, observador somente leitura com
handles de consulta, sem cliente IPC de auditoria novo.

### Tempo e encerramento

- Abertura solicitada: **00:18:59,646 local**.
- Criação efetiva do processo: **00:19:00,336 local**.
- Observação do processo até confirmar todos encerrados: **84,22 s**.
- Total contado desde a solicitação de abertura: **84,91 s**, abaixo de 120 s.
- Meta de Sair perto de 45 s: **não atingida**. A solicitação de encerramento
  ocorreu perto de 60 s após priorizar as verificações e a interação de bandeja.
  Não se apresenta essa meta como cumprida.

O usuário confirmou restauração pelo ícone LONE da bandeja e depois seleção de
**Sair** no menu contextual. O observador confirmou exit code **0**, todos os
filhos encerrados e ausência de pipes/resíduos. Não houve encerramento forçado,
X como substituto, nova abertura ou repetição da sessão.

| Componente observado | PIDs |
|---|---|
| Electron | 10112 (principal), 11072, 1908, 19756 |
| Intermediário IPC | 1672 |
| Coletor | 10548 |
| Ponte ADLX | 10244 |

Identidades retidas: imagens esperadas, descendência da única instância, criação,
mesma conta/sessão e sem elevação. Dois endpoints de monitoramento vistos durante
a sessão; **zero ao final**, sem processos órfãos.

### Interface e telemetria observadas

Dashboard Controles e Monitoramento PC abriram. Widget compacto exibiu os mesmos
sensores, com navegação inferior. Foi acionada a minimização explícita para
bandeja. A ferramenta não oferece prova confiável de visibilidade somente por
`list_windows`: ela ainda lista o handle oculto; não se interpretou isso como
falha do aplicativo. Restauração e Sair foram confirmados pelo usuário, e o
observador permaneceu acompanhando a mesma árvore de processos.

Na ativação inicial da janela, a interface ocultou métricas GPU e mostrou
`atualizando após restauração` / `aguardando nova amostra` (cartões Aquecendo).
Depois mostrou novas leituras válidas. Nas evidências às 00:19:17/23/31, a GPU
apresentava cadência de 2 s, idade de ingresso de 0,3–0,4 s e limite de ingresso
1,5 s; cache ativo com limite de 3 s. A expiração inativa de 11 s e a falha após
10 s permanecem preservadas no pacote validado, mas não foram cronometradas
fisicamente neste teste. Não foram induzidas falhas.

**Não foi capturado o instante da GPU após a restauração específica pela bandeja.**
A evidência de reativação inicial não é apresentada como substituta dessa prova.
Não foi feito outro ciclo para preencher essa lacuna.

Exemplos de leituras reais das capturas/árvores, não médias da sessão:

| Métrica | Leituras observadas |
|---|---|
| CPU total do PC | 13,5%; 17,5%; 19,7% |
| RAM | 15,8 GiB total; aproximadamente 12,2–12,3 GiB usada; 3,5 GiB disponível; 77,7–78% |
| GPU | 1–5%; 54–55 °C; hotspot 58 °C |
| VRAM | 1.211–1.262 MB usada; 12.272 MB total |
| Clock / potência / ventoinha | 225–272 MHz; 41 W; 484–487 RPM |
| Volume C: | 475,6 GiB total; 231,4 GiB disponível; ocupação 51,3% |
| C: I/O | Leitura 0 bytes/s a 127,88 KiB/s; gravação 3,95 a 759,28 KiB/s nas observações |
| C: atividade PDH | 0,2–0,4% nas observações |
| Volume D: | 447,1 GiB total; 242,1 GiB disponível; ocupação 45,9% |
| D: I/O / atividade | Leitura/gravação 0 bytes/s válidos; atividade alternou Indisponível e `<0,1%` válido |

Os intervalos acima representam apenas os pontos capturados, não extremos
garantidos de todo o hardware durante a sessão. Zero válido não substituiu
indisponibilidade. Ocupação, I/O e atividade permaneceram métricas diferentes.
CPU e disco indicaram cadência contratada de 1 s; capacidade/VRAM total, 60 s.
Não houve amostragem independente suficiente para calcular a distribuição exata
de todos os intervalos dos sensores ou o total de frames GPU válidos/rejeitados.

O desktop continua exibindo **COMUNICAÇÃO NÃO INTEGRADA**: seu cliente
autenticado do agente não foi criado nesta tarefa. A telemetria local funciona
por transporte de monitoramento separado, e a comunicação Android–agente foi
verificada separadamente. O estado desktop não foi falsificado como Conectado.

### Consumo dos componentes do aplicativo

Média de CPU: soma de `GetProcessTimes` desde criação, dividida pelo tempo
observado e por **12 processadores lógicos**. RSS: soma de working sets das
amostras aproximadamente a cada segundo; páginas compartilhadas podem ser
contabilizadas mais de uma vez. Observador e helper gráfico excluídos dos totais.

| Componente | CPU média da máquina | RSS médio | Pico RSS somado |
|---|---:|---:|---:|
| Electron | 0,6895% | 357,35 MiB | 372,36 MiB |
| Coletor | 0,1067% | 29,84 MiB | 30,68 MiB |
| Intermediário IPC | 0,0680% | 22,92 MiB | 23,54 MiB |
| Ponte ADLX | 0,0479% | 23,09 MiB | 24,07 MiB |
| **Conjunto** | **0,9121%** | **433,20 MiB** | **450,48 MiB** |

O pico conjunto de CPU em janela aproximada de 1 s foi **9,37%**. Esses números
incluem inicialização e interações de janela e não são garantia de uso em repouso.
Havia outros aplicativos já abertos pelo usuário, inclusive vídeo no navegador
e Steam. Não foram iniciados, encerrados ou utilizados pelo teste para gerar
carga. Não comparar diretamente com a referência de desenvolvimento de 0,529%
como se as condições fossem equivalentes; não se afirma regressão.

### Pendências da homologação física Windows

- Aba Gamer Launcher não foi revisitada nesta sessão; controles permanecem sem
  cliente operacional e sem grants. Não usar teste histórico como evidência nova.
- Minimizacão normal, redimensionamento, painel flutuante e captura do menu da
  bandeja não foram completados; priorizou-se o encerramento.
- Retomada GPU imediatamente após restauração pela bandeja, expiração inativa
  de 11 s e falha persistente de 10 s sem recuperação: não comprovadas fisicamente
  nesta sessão. Nenhuma falha foi fabricada.
- Nenhum evento Application Error/WER/hang relevante (1000/1001/1002) no
  intervalo consultado. Não houve crash ou congelamento observado. Entretanto,
  stderr do aplicativo não foi capturado nesta abertura gráfica; não é possível
  afirmar ausência de mensagens Crashpad 0xE9 ou declarar a pendência resolvida.

O primeiro screenshot Windows retornou a janela de outro aplicativo que estava
à frente, apesar de a árvore textual identificar o LONE. Foi retido somente em
cache e excluído da galeria. As capturas publicadas de monitoramento e widget
foram inspecionadas visualmente; não são prévias HTML ou imagens geradas.

## 5. Estado final e preservação

- Windows **dev.7** preservada e fechada, sem coletores/IPC/ADLX residuais.
- Android **dev.9/código 23** instalado; configurações WoL e pareamento mantidos.
- Agente recuperado **ativo**, mesma identidade, worker **14908**, listener
  único 8776 e status autenticado HTTP 200/TLS 1.3. Banco íntegro, zero grants.
- Identidades e segredos cifrados do banco e permissões iguais ao início da
  recuperação. Os registros normais de autenticação não são tratados como
  corrupção ou alteração indevida.
- HKCU Run e regra de firewall pertinente mantiveram seus hashes antes/depois.
- 116 arquivos da instalação inalterados, backup de 194 arquivos conferido
  novamente e intacto. Nenhum backup anterior foi excluído ou restaurado.
- Perfil Windows com 78 arquivos antes/depois, nenhum removido. Houve alterações
  normais de cache, logs de storage e `desktop-window-state.json` durante a sessão;
  não se afirma igualdade byte a byte do perfil após usar a interface. Preferências
  válidas, modo final widget e bandeja automática desligada.
- Nenhuma alteração em fonte de produção, Android/Kotlin, agente, certificados,
  HMAC, serviços, tarefas, drivers ou política de rede. Nenhum Steam/CS2 foi
  iniciado pelo teste, nenhum WoL ou comando de energia foi enviado.

TLS 10054 não foi reproduzido nem corrigido. Inicialização automática, shutdown
gracioso do agente, Crashpad e homologação parcial dev.7 permanecem pendentes.

## 6. Evidências e próxima recomendação

Veja [galeria de capturas reais](captures.md) e
[`evidence/summary.json`](evidence/summary.json). Os recibos públicos não incluem
senhas, tokens, certificados privados, serial ADB ou caminhos sensíveis. Cofres,
settings cifrados, dumpsys completo e gravação bruta permanecem nos diretórios
locais de recuperação/cache ignorados pelo Git.

Recomendação: tratar a inicialização automática como investigação separada,
correlacionando despacho pós-login e bootstrap sem alterar a configuração por
suposição. Para completar a homologação, propor depois uma sessão curta e
específica para captura da retomada por bandeja e cenários restantes, com o
usuário pronto para Sair, sem tentar todos os itens no mesmo orçamento. Verificar
se a splash nativa foi efetivamente exibida em um cold start autorizado, sem
confundir cabeçalho HTML com splash do sistema.

Nenhuma nova sessão física foi iniciada para completar lacunas. Não há rollback
operacional indicado: a atualização Android teve sucesso e o Windows não foi
substituído. Não desinstalar/downgrade Android como reversão automática; qualquer
correção futura deve preservar dados, package e assinatura com código superior.
O agente deve permanecer ativo. Reverter o commit documental desta entrega só
retira o relatório do Git, não restaura instalações ou credenciais.
