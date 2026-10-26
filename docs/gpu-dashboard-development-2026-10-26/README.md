# GPU ADLX no dashboard e widget — integração de desenvolvimento

26/10/2026, America/Sao_Paulo. Base: `f144b61`. Branch: `feature/ui-migration-preview`.
Autorização limitada a implementação e testes simulados. **Nenhuma sessão física,
abertura do Electron, compilação de pacote, instalação ou atualização foi realizada.**

## Implementação

Fluxo preparado: ponte ADLX isolada → provedor GPU → coletor/cache v1 → Named Pipe
protegido → processo principal Electron → preload existente → dashboard/widget.

- `monitoring/development_collector.py`: composição opcional dos 21 indicadores
  básicos com oito métricas GPU. O catálogo básico permanece intacto. CPU/RAM/I/O
  continuam com 1 s; GPU dinâmica usa 2 s; capacidades usam 60 s. Em inatividade,
  CPU/RAM/I/O passam a 5 s, GPU a 10 s e capacidades permanecem em 60 s.
- `monitoring/gpu_development.py`: valida contexto limitado, propriedade exclusiva
  da ponte e encerramento cooperativo. A opção GPU é recusada em pacote instalado,
  modo permanente, demonstração e duração acima de 70 s.
- Scripts pipe client/server: encaminham somente o flag interno fixo
  `--gpu-development`; preservam requisições estritas `snapshot`/`capabilities`,
  contrato v1, ACL, SID/sessão/imagem/criação do cliente e limites existentes.
- Electron: `--lone-gpu-development` só tem efeito junto às opções existentes de
  revisão/monitoramento de desenvolvimento e run ID hexadecimal válido. O perfil
  fica em `.cache/windows-monitoring-development/<run-id>/`, separado da produção.
  Nenhum novo canal preload, endpoint TCP/HTTP ou cliente do agente foi adicionado.
- `monitoring-model.js`: allowlist adicional explícita dos oito IDs ADLX,
  origens/unidades/faixas e cadências; o modo básico continua aceitando somente
  os 21 IDs originais. Payload GPU não entra no host básico sem opt-in.

Métricas preparadas: utilização %, temperatura GPU/hotspot °C, VRAM usada/total MB,
clock MHz, potência W e ventoinha RPM. O suporte efetivo continua vindo das consultas
ADLX; a existência de um cartão não declara um sensor disponível.

## Frames, validade e compatibilidade

O primeiro `age_null` permanece rejeitado: estado de erro/valor null, sem fabricação
de zero, clamp, correção de timestamp ou troca de relógio. O coletor continua a
amostrar a **mesma ponte** na próxima cadência; um frame subsequente válido pode
restabelecer a leitura. Não se reaplica `ADLXInitialize` nem se cria processo por frame.
Falhas persistentes da ponte deixam GPU indisponível/com erro; CPU, RAM e discos
continuam com seus provedores. Não há reinicialização automática da ponte após falha.

Foram comparadas as ASTs de `_validate_frame`, `_validate_native_diagnostic`,
`_reading`, `_reject`, `latest` e `note_provider` com `f144b61`: **idênticas**.
Também permaneceram byte a byte iguais: provedor ADLX, contrato v1, fonte C++,
protocolo/implementação Win32 de pipe e preload. A mudança em `adlx_bridge.py`
é de criação/propriedade do processo, não de aceitação de métricas.

O frescor **nativo no ingresso é 1,5 s**, incluindo as verificações existentes de
tempo de transporte. Timestamps futuros/não finitos não passam. Depois do ingresso,
o cache conserva a política existente de stale em três intervalos: 6 s para GPU
ativa e 30 s na cadência inativa. São verificações diferentes; consultar o cache
não renova a coleta. Desconexão esconde números anteriores e a última leitura válida
fica separada da indicação de dado atual.

VRAM permanece nos **MB nativos declarados pelo ADLX**; não foi rotulada como GiB
nem multiplicada/dividida por 1024 sem base no contrato. RAM/volumes em bytes mantêm
a conversão explícita já existente para GiB. VRAM usada acima do total disponível,
total zero, inteiros inválidos e faixas incompatíveis são recusados.

## Processos, exclusão e segurança local

Antes de criar a ponte, o worker reserva um Named Pipe local de propriedade,
com nome fixo derivado do SID e `FIRST_PIPE_INSTANCE`, DACL da conta verificada e
clientes remotos recusados. Esse objeto **não aceita conexões nem comandos**;
serve apenas de lease. Nome ocupado ou DACL inesperada interrompem a inicialização.
Nenhum processo existente é encerrado para adquirir a propriedade.

Só o handle desse lease, além dos stdio necessários, é herdado pelo filho ADLX por
`STARTUPINFO.lpAttributeList.handle_list`, com `shell=False` e `close_fds=True`.
Assim, a reserva persiste até a saída do nativo mesmo se seu pai desaparecer.
A herança do handle no pai é restaurada após criar o filho. Se essa restauração
falhar, o processo criado não é perdido: o transporte conserva a referência,
recusa bootstrap e solicita parada normal. Os caminhos/argumentos do executável
continuam fixos e verificados; nenhum handle/parâmetro é recebido do renderer.

No encerramento: fecha-se o serviço de leituras, para-se o coletor, solicita-se
`stop` à ponte e aguarda-se sua saída real antes de liberar o lease do pai.
Timeout não significa sucesso. Uma parada pendente mantém a supervisão e informa
`pending_stop`; não usa kill/terminate. Saída não limpa permanece falha mesmo sem
processo residual. O supervisor existente aguarda a saída do worker antes de sair.

A ACL por usuário e as verificações de processos **não oferecem isolamento completo
contra outro programa comprometido sob a mesma conta**. A proteção de propriedade
vale para o fluxo controlado; um usuário com capacidade de executar código local
não é tratado como uma fronteira de segurança forte.

Permanecem os limites existentes: requisições 256 B, respostas 128 KiB, mensagens
nativas 16 KiB/fila de oito, rate limit e deadlines. A ponte mantém limite de
solicitações, memória e watchdog já aprovados. Diagnósticos de frames continuam
desligados por padrão; nenhum log de frame foi ativado nesta etapa.

## Dashboard e widget

A aba Monitoramento PC reutiliza os quatro cartões: CPU, GPU, RAM e **Temperatura
GPU**. Adiciona um painel de detalhes da RX 6750 XT com hotspot, VRAM usada/total,
clock, potência e RPM, mais origem, unidade, horário e validade. Não adiciona
temperatura da CPU, FPS ou controle de ventoinhas. A faixa de recursos bloqueados
foi esclarecida como controle de ventoinhas, pois RPM agora pode ser uma leitura.

O widget conserva CPU/RAM e apresenta GPU %, temperatura e VRAM de forma compacta.
O mesmo payload validado alimenta ambos os modos; não existe segunda ponte para
o widget. O painel usa colunas adaptáveis e quebra de texto, sem mudar a navegação,
identidade, três abas, bandeja, preferências, posição ou comportamento do botão X.
Funções não implementadas e o gráfico histórico continuam indisponíveis.

Sensores nulos/desatualizados ficam explícitos; zero RPM e zero de I/O continuam
numéricos quando válidos. Percentuais positivos pequenos mostram `<0,1%`.

Ao minimizar, ocultar ou perder foco, o main reduz polling de cache de 1 s para
10 s. No worker GPU, quatro segundos sem snapshot autorizado ativam cadências
inativas; consultas próximas ao retornar reativam as cadências normais. Isso não
adiciona operação de controle ao protocolo. Clientes negados não mudam a demanda.
O renderer recebe estado oculto sem escrever no DOM e reavalia a idade ao voltar.
Textos iguais não são reatribuídos em cada tick; cartões/ponte não são recriados.

## Testes executados

| Suíte | Resultado |
|---|---:|
| Novos composição, vida útil, exclusão, herança e cache/IPC GPU | 22 testes Python |
| Contrato/cache/básicos e regressões WoL/Steam/CS2 simuladas | 133 testes Python |
| Pipe Win32/admissão/vida útil simulados | 28 testes Python |
| Provedor ADLX e casos temporais | 28 testes Python |
| Ponte mock/diagnósticos | 59 testes Python |
| Orquestração ADLX simulada anterior | 10 testes Python |
| Políticas, bandeja, monitoramento básico, renderer e distribuição | 296 verificações Node |
| Recuperação IPC/stale/janela/inatividade | 23 verificações Node |
| Nova integração GPU/model/main/DOM/widget | 60 verificações Node |
| Política C++ dentro da suíte mock | 31 asserts |

**280 testes Python e 379 verificações Node passaram, sem falhas ou skips finais.**
Os 31 asserts estão incluídos na suíte da ponte, não somados novamente ao total Python.
Somente o binário separado `bridge-mock.exe` pôde ser executado pelo runner da ponte
(22 processos no último recibo, zero residuais). DLL real, sensores, sockets e Registro
foram recusados por audit hooks; Popen/herança de handles foram substituídos nos testes
da integração. Nenhum Electron real foi aberto para esses testes de DOM/janela.

Casos: primeiro frame inválido, recuperação, perda da ponte, stale, suporte parcial,
zero verdadeiro, limite temporal/futuro/NaN/inf, cliente negado, comandos extras
recusados, perda/retorno de IPC, unidades e coerência VRAM, limites do cache,
cadências ativa/inativa, uma única inicialização, ocupação/atividade separadas,
encerramento pendente, falhas de herança e nenhuma chamada de kill/terminate.

Falhas intermediárias preservadas nos logs locais: o novo teste identificou duas
escritas redundantes por refresh nos rótulos compactos; elas foram corrigidas.
Um fixture DOM antigo não possuía o novo container GPU; foi atualizado e as 19
asserções antigas passaram novamente. Não foram omitidas asserções para obter aprovação.

No substituto DOM, uma atualização básica escreve 28 textos; tick sem amostra nova
e atualização oculta passaram de 28 para **zero** escritas. Isso **não mede CPU,
layout, Chromium, GPU ou consumo real**, nem comprova melhoria de desempenho físico.
Capturas reais e inspeção de pixels/scroll em diferentes escalas continuam pendentes.

## Consumo projetado e limites

Não há medição física integrada desta entrega. Referências anteriores, de sessões
diferentes: básicos+IPC+Electron 0,4613% CPU/441,25 MiB RSS médio; GPU isolada
0,06687% CPU/49,29 MiB RSS médio. A soma aritmética seria aproximadamente
**0,528%/490,54 MiB**, apenas uma ordem de grandeza para planejamento, não uma
previsão validada. RSS pode contar páginas compartilhadas duas vezes e as cargas
das sessões não são equivalentes. A meta abaixo de 0,5% permanece não comprovada.

O desenho mantém uma ponte, um cache limitado e os processos básicos existentes,
sem polling GPU separado no renderer. Leituras nativas lentas/bootstrap podem atrasar
o thread serial do coletor; cache/IPC/UI continuam independentes. Frescor e erro devem
refletir o atraso, sem declarar dados antigos atuais. Isso precisa ser medido.

O fluxo GPU é propositalmente **limitado a 70 s de desenvolvimento**. O watchdog
existente do nativo é 82 s; não foi removido para criar uma coleta permanente não
validada. Integração em pacote de produção exigirá revisão separada do ciclo longo,
manifesto/runtime e execução física. Nada foi empacotado nesta etapa.
O novo lease e a herança do handle foram verificados com substitutos, não com
processos Windows reais nesta entrega. A validação Win32 desse novo caminho e a
inspeção visual real dependem da próxima autorização.

## Preservação e estado final

Supervisor HTTPS **5024**, worker **18304**, identidades/imagens/argumentos/criação
iguais ao início, listener único **8776**, TLS **1.3**, certificado/hostname/pin
validados e status HMAC **HTTP 200** antes/depois. **Zero grants e comandos pendentes.**
O Samsung não foi acessado nem recebeu nova atualização; não há confirmação humana
nova nesta etapa, somente a validação HTTPS de leitura. Nenhuma identidade desktop
ou credencial foi criada/copiada para o Electron.

SHA-256 sem diferenças: instalação dev.5 **109 arquivos**, perfil **77**, backups
dev.3 **341**, dev.4 **75**, dev.5 **156**, e **86 arquivos operacionais protegidos**.
Banco íntegro; identidades, segredos cifrados, schema e revogações iguais por hash
lógico. HKCU Run e firewall iguais. Fonte C++/DLL oficial, preload, arquivos Android,
certificados, agente, artefatos e evidências físicas anteriores preservados.
Nenhum processo Electron/coletor/ponte/intermediário de desenvolvimento residual.

Não houve instalação, coleta física, jogos, WoL, energia, novos grants, drivers,
serviços, tarefas ou autostart. TLS, Crashpad e encerramento gracioso do agente
seguem separados. O agente foi deixado ativo; não se alterou ou reiniciou seu processo.

## Plano de uma sessão integrada — ainda NÃO autorizada/executada

1. Obter autorização específica para **uma única sessão**, planejada em 70 s e com
   limite total de 90 s, sem pacote instalado. Reconfirmar agente por identidade,
   listener/auth200, zero grants, ausência de coletores e preservação dos cinco trees.
2. Conferir hashes dos fontes/recibos, binário real x64, DLL System32 assinada e SDK
   fixado. Nenhuma dependência nova. Confirmar execução sem elevação e perfil/run ID
   novos, sem importar perfil de produção.
3. Uma abertura do Electron **de desenvolvimento**, com
   `--lone-development-review --lone-monitoring-development --lone-gpu-development`
   e `LONE_MONITORING_RUN_ID` de 32 caracteres hexadecimais. Esses parâmetros estão
   documentados para uso futuro; não foram executados nesta entrega.
4. Confirmar árvore de processos, lease único com herança correta e Named Pipe
   autenticado. Observar o primeiro frame sem forçar rejeição: se inválido, deve
   permanecer null até chegar leitura válida na mesma ponte. Não reiniciar por erro.
5. Capturar dashboard Monitoramento, Controles com indicadores compactos, widget e
   painel informativo. Conferir CPU/RAM/C:/D: junto à GPU, units/tempos, zeros válidos,
   stale e suporte parcial conforme realmente ocorrerem. Não fabricar indisponibilidade.
6. Medir por handles/PID+criação/imagem: coletor, intermediário, ponte e todos os
   processos Electron. CPU = deltas kernel+usuário/tempo monotônico/12 processadores;
   memória = RSS e commit, alertando contagem compartilhada. Registrar intervalos,
   estado de cache e primeira validade. Sem carga artificial ou aplicativos extras.
7. Alternar dashboard/widget e ocultar/restaurar pela bandeja uma vez, verificando
   cadência reduzida e retorno. Nenhuma mudança de preferências ou auto-start.
   Organizar capturas e interação para escolher **Sair até ~70 s**, com margem de limpeza.
8. Encerrar por Sair/EOF normal; confirmar saída da ponte/worker/intermediário/Electron
   e liberação dos handles de pipe/lease. Não testar duplicação por uma segunda partida.
   Se houver travamento, reportar pending/timeout e solicitar orientação, sem force,
   repetição, calibração de relógio ou nova sessão. Não anunciar limpeza não confirmada.
9. Reconfirmar agente original ativo/auth200, listener 8776, zero grants, perfis e
   backups íntegros. Parar antes de empacotar ou implantar qualquer versão.

## Commits e reversão

- `08fd2fb`: coletor GPU de desenvolvimento, propriedade e vida útil/IPC; testes Python.
- `ccfe941`: main/model/renderer/dashboard/widget e regressões Node.
- Commit documental desta pasta: recibos sanitizados e plano físico.

Reversão proposta, não executada: árvore limpa, revisar os dois diffs e executar
`git revert ccfe941 08fd2fb`, preservando evidências. Não usar reset destrutivo,
restaurar banco/perfis ou parar o agente. Não é necessário rollback da instalação
dev.5, que não mudou. `f144b61`, `6cdb395`, `2031043` e demais checkpoints permanecem
ancestrais da branch. Nenhum repositório foi publicado.
