# Primeira execução física — Windows 2.0.0-dev.3

Data: 24/10/2026. Checkpoint preservado: `40f11dfcdceacb75d0a0418790ac2d3afa25b9a6`. Branch: `feature/ui-migration-preview`.

**Resultado:** uma única sessão da aplicação instalada abriu corretamente, permitiu navegar nas três seções, utilizar o Modo Widget e os painéis, redimensionar, maximizar/restaurar, minimizar/restaurar e fechar normalmente. Observação visual responsiva de **292,006 segundos**, superior aos 60 segundos exigidos. Nenhuma correção de código foi aplicada.

## Sessão e identidade

- Executável: `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe`.
- Uma chamada de `Start-Process`, sem argumentos, usuário normal, sem elevação. Instalador e portátil não foram executados.
- Início: **13:22:59,134 -03:00**; término: **13:31:47,471 -03:00**. Duração total aproximada: 528,337 segundos, incluindo preparação da observação e interações.
- Primeira captura carregada registrada às **13:26:33,433**; janela restaurada e responsiva às **13:31:25,439**: janela de observação conservadora de **292,006 segundos**. Não se presume observação visual contínua anterior à primeira captura.
- PID principal **42920**; subprocessos observados **58968**, **56848**, **30324**. Todos responderam na amostra durante a sessão. São a árvore normal de uma sessão Electron, não quatro aberturas independentes.
- Código de saída **0**; nenhum processo ou janela do Lone Smart Room restante após o encerramento. Nenhum relançamento.
- Versão visível **Windows · Versão 2.0.0-dev.3** e título **Seu espaço, sob controle.** confirmados. Logo oficial e ícone angular apareceram na interface; recursos do pacote conferidos antes da execução.
- EXE SHA-256: `84ecf7acdc79a03307e29c51ed3e5e556f35b7bcf460833a1095da2f516d286e`.
- ASAR SHA-256: `eba95a3adc738d2e2916ca87de6c5bff68ea9be890471ed3c8179a50b201921a`.
- O executável continua sem assinatura Authenticode. Não houve solicitação observada para contornar proteções do Windows.

## Validações visuais e da janela

| Verificação | Resultado observado |
|---|---|
| Controles | Cartão do PC, dispositivos, área WoL e NEX renderizados; rolagem acessível |
| Monitoramento PC | CPU, GPU, RAM e temperatura indisponíveis; sem medições ou curvas fictícias |
| Gamer Launcher | Cartão CS2 e Steam renderizados; botões de lançamento desabilitados |
| Comunicação | Indicador separado **COMUNICAÇÃO NÃO INTEGRADA**, sem confundir desconhecido com desligado |
| Painéis flutuantes | Permissões, conexão e dispositivo abriram; fechamento pelos próprios botões confirmado |
| Configurar | Abriu painel informativo de conexão; vinculação e campos operacionais indisponíveis |
| Modo Widget | Dashboard → Widget → dashboard na mesma sessão; três abas testadas na navegação inferior |
| Rolagem compacta | Conteúdo até WoL/NEX/rodapé alcançável; navegação inferior permaneceu fixa |
| Redimensionamento | Alteração real de largura do Widget pelo menu nativo Tamanho; layout permaneceu legível |
| Maximizar/restaurar | Captura de 1920 × 1032 e retorno à composição de 1362 × 961 |
| Minimizar/restaurar | Ferramenta confirmou `window is minimized`; ativação restaurou a mesma janela, sem nova abertura |
| Fechar | Botão Fechar encerrou árvore do aplicativo, saída 0 e zero janelas restantes |
| Bandeja | Ausência esperada; nenhuma implementação de Tray ou autostart foi introduzida |

As capturas possuem **1362 × 961**, **442 × 821**, **431 × 821** e **1920 × 1032** pixels, incluindo a borda da janela. Não foram alteradas as escalas/DPI do Windows; portanto esta sessão não certifica todas as combinações de escala e tamanho. Não foram observados cortes inesperados, sobreposições ou falhas de navegação nos estados capturados. O conteúdo fora do viewport é alcançado por rolagem.

A tentativa inicial de arraste do canto selecionou texto em vez de redimensionar. A seleção foi removida; o redimensionamento foi então comprovado pelo menu nativo da própria janela. Isso não modificou código ou configurações do Windows. A marca d'água de ativação do Windows e o destaque do ponteiro presentes em algumas capturas pertencem ao ambiente de captura; as imagens não foram retocadas.

## Capturas reais da aplicação instalada

Todos os JPG abaixo foram capturados da janela cujo executável é o instalado em `AppData\Local\Programs`. Não são prévias HTML nem execução do Electron de desenvolvimento. Horários e dimensões constam em `visual-records.json`.

| Arquivo | Conteúdo |
|---|---|
| `01-controles-instalado.jpg` | Controles inicial, logo, versão, título e menu lateral |
| `02-monitoramento-instalado.jpg` | Monitoramento PC |
| `03-gamer-launcher-instalado.jpg` | Gamer Launcher, Steam/CS2 bloqueados |
| `04-painel-permissoes.jpg` | Painel flutuante de permissões |
| `05-widget-gamer.jpg` | Widget Gamer Launcher |
| `06-widget-monitoramento.jpg` | Widget Monitoramento PC |
| `07-widget-controles.jpg` | Widget Controles |
| `08-widget-painel-conexao.jpg` | Painel Configurar no Widget |
| `09-widget-redimensionado.jpg` | Widget após mudança real da largura |
| `10-widget-rolagem.jpg` | Rolagem, dispositivos e navegação inferior |
| `11-widget-painel-dispositivo.jpg` | Painel da lâmpada, controles indisponíveis |
| `12-widget-final-rolagem.jpg` | Final do conteúdo, WoL, NEX e rodapé |
| `13-dashboard-restaurado-rolagem.jpg` | Retorno do Widget ao dashboard |
| `14-dashboard-maximizado.jpg` | Janela maximizada |
| `15-restaurado-apos-minimizar.jpg` | Mesma janela após minimizar/restaurar |
| `16-ultimo-estado-antes-fechar.jpg` | Último estado da aplicação antes do encerramento |

`17-estado-apos-encerramento.svg` é **um quadro gerado a partir das verificações**, identificado dentro da imagem. Não é uma captura da área de trabalho ou uma janela fictícia do aplicativo fechado. A comprovação posterior ao encerramento é `session-exit.json` e `final-verification.json`, com saída 0, zero processos e ausência de janela na nova enumeração. A ferramenta disponível captura janelas específicas; não existe janela do app depois de fechada.

## Eventos e limitações de diagnóstico

- Consulta somente leitura do log Application entre início e término + 30 segundos: IDs **1000, 1001, 1002 e 1026**, filtrando referências ao Lone Smart Room.
- **Zero eventos correspondentes**, sem erro de acesso ao log. Nenhum crash, travamento ou erro visual observado.
- **Zero dumps no perfil novo**. Não foi habilitada coleta adicional, logging de depuração ou instrumentação do renderer.
- Console JavaScript/renderer não foi capturado: a versão empacotada não mantém um log diagnóstico dedicado. Os dois arquivos `.log` encontrados são journals LevelDB, não evidência de erro nem logs de console. Assim, ausência absoluta de mensagens internas não é afirmada.
- Uma consulta inicial de eventos falhou por conversão de data no script de evidências; corrigiu-se apenas esse script isolado e repetiu-se a leitura com sucesso. Isso não foi erro do Electron e não envolveu nova execução da aplicação.

## Preservação e segurança

- **255 arquivos protegidos** (fontes, artefatos e dados existentes do agente): hashes idênticos antes/depois.
- **76 arquivos instalados** idênticos antes/depois, incluindo os 74 arquivos de runtime e dois recursos do desinstalador. Os 22 arquivos ASAR e a identidade oficial foram conferidos com o código/pacote previamente aprovado.
- **336 arquivos dos perfis antigos de testes** e **341 arquivos totais do backup** idênticos antes/depois.
- Backup `<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev3-20261024T145523Z`: 336 arquivos de dados, 35.980.960 bytes e 139 diretórios verificados; SHA-256 e ACLs restritas ao usuário aprovados. Nenhuma restauração, cópia de credenciais para Git ou descriptografia.
- Verificador de recuperação original: **86 registros aprovados**, originais e cópias preservados.
- Única nova área persistente do app: perfil normal de primeira execução em `<USERPROFILE>\AppData\Roaming\Lone Smart Room`; após fechamento, 72 arquivos, 8.589.376 bytes. Não foi importado perfil de demonstração nem exportado conteúdo desse perfil para Git.
- Agente HTTPS permanece no **mesmo PID 13012**, mesma data de criação, listener **8776** ativo antes/depois. Nenhuma requisição operacional do desktop, reinicialização do agente ou mudança no pareamento.
- Banco consultado somente em leitura: **zero grants**, **quatro comandos históricos inalterados**, **zero comandos em andamento**. Nenhuma identidade ou grant desktop foi criado.
- Sem ações Steam/CS2, WoL, energia ou dispositivos; sem acesso ao Samsung. Processos Steam já presentes no ambiente não foram acionados nem encerrados.
- Android, WoL, certificados, credenciais, autenticação, executores e pendência TLS não foram alterados. A constatação é de preservação de arquivos/dados; não houve novo teste funcional WoL/Android nesta sessão.
- A política Electron permanece com `contextIsolation=true`, `nodeIntegration=false`, sandbox e `connect-src 'none'`; o cliente autenticado desktop continua indisponível.

## Comparação das configurações do sistema

34 entradas Run/RunOnce, arquivos de inicialização, registros do aplicativo instalado, atalhos, 325 definições de serviços e 717 regras de firewall permaneceram iguais nos campos inventariados. Não houve novas tarefas: a contagem permaneceu 204.

Foi detectada **uma diferença**, conservada em `task-difference.json`: o hash dos gatilhos da tarefa preexistente `\Microsoft\Windows\Flighting\OneSettings\RefreshCache` mudou. O hash da ação não mudou. A consulta posterior identificou autor Microsoft Corporation, descrição de atualização periódica OneSettings, última execução **13:31:39 -03:00**, resultado **0**, e StartBoundary **13:32:39 -03:00**. O horário é compatível com atualização em segundo plano, mas **a autoria exata da mudança não pôde ser comprovada**, pois o log operacional do Task Scheduler já estava desabilitado e não foi habilitado. Não foi executado comando de criação/alteração de tarefa, serviço ou Registro nesta sessão. Não se afirma que toda a máquina ficou byte a byte inalterada.

## Estado final e próximos passos

A primeira sessão visual pode ser considerada **aprovada nos cenários exercitados**, sujeita à revisão das capturas pelo usuário. O aplicativo está fechado; o agente permanece ativo e independente. Nada será reaberto, instalado ou corrigido automaticamente.

A pendência TLS continua separada. Comunicação autenticada desktop, bandeja, persistência de janela ou autostart exigem escopo e autorização próprios; esta validação visual não os habilita. Não é necessário rollback para o resultado observado. Se futuramente necessário, seguir o plano de recuperação existente sem apagar o perfil recém-criado nem os backups.

Este commit contém somente documentação, capturas e a regra de preservação de bytes desta pasta em `.gitattributes`. O código funcional permanece no checkpoint `40f11df`.
