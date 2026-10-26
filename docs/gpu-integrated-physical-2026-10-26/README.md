# Primeira sessão física GPU integrada — desenvolvimento isolado

26/10/2026, America/Sao_Paulo. Base funcional: `bcafe3a`; `08fd2fb`, `ccfe941` e
todos os checkpoints anteriores preservados. Nenhuma mudança funcional nesta entrega.

**Resultado: fluxo físico integrado validado na sessão limitada, com ressalvas de
frescor de exibição e desempenho descritas abaixo.** Não houve empacotamento,
instalação, atualização da dev.5 ou segunda sessão.

## Execução e pré-verificação

Uma sessão real de **68,193 s**, aproximadamente **01:00:52–01:02:01** locais.
A interface pediu Sair após 66,55 s de sua observação; coletor/ponte encerraram de
forma cooperativa. O limite de 90 s não foi atingido.

Antes da abertura: Git limpo em `bcafe3a`; recibos de **280 testes Python, 379
verificações Node e 31 asserts C++** confrontados com 121 entradas de hashes dos
fontes; binários real/mock/verificador correspondentes ao fonte C++ atual.
Essas suítes não foram apresentadas como novas execuções integrais nesta etapa.
Três testes adicionais com substitutos validaram o observador temporário; Python
e JavaScript passaram também por verificação de sintaxe sem iniciar sensores.

DLL oficial System32 `amdadlx64.dll`, versão previamente verificada 1.4.0.121,
PE x64, hash e assinatura/catálogo conferidos pelo verificador sem carregar ADLX.
SHA-256: `992f6db497a3c8af8d26e578c7b7fce90ed67e506d7790cc3221e4a01b67852a`.
Na execução real, a ponte informou `runtime_verified`, `adlx_loaded` e
`adlx_initialized`. Diagnóstico nativo de frames permaneceu desligado.

Não havia Electron, ponte ou coletores de desenvolvimento residuais. O perfil
novo e exclusivo ficou sob `.cache/windows-monitoring-development/<run-id>/`.
Instalação, perfil de produção e backups foram comparados antes/depois por hash.
Agente original, listener único 8776, certificado/hostname/pin, TLS 1.3/status
autenticado 200 e zero grants passaram antes da abertura.

Uma falha de aspas no comando de preparação ocorreu **antes** de criar o marcador
ou iniciar Electron. A preparação foi movida a um arquivo temporário. O marcador
exclusivo registra somente **uma** abertura física; nenhum programa foi relançado
após o teste. Ajustes dos testes do observador foram apenas nos substitutos/roteiro,
sem alterar a implementação funcional aprovada.

## Instrumentação e alcance

Electron de desenvolvimento real, perfil isolado e fontes aprovados. Um bootstrap
temporário observou os processos: os entrypoints originais Python foram executados
por `runpy` com wrappers locais para registrar chamadas/estatísticas e inspecionar
o handle. Não houve troca de sensor, alteração de métricas, relógio, tolerância,
origem, retorno ou regra de validação. A rota de lançamento ficou instrumentada;
não se trata de uma medição sem observador ou de uma instalação empacotada.

Os wrappers somente encaminharam os argumentos fixos, chamaram as implementações
originais e registraram metadados autorizados. Nenhum payload ADLX bruto, memória
de processo, credencial, SID ou ambiente completo foi exportado. As informações de
handle foram consultadas apenas para o filho recém-criado e identificado.

O observador externo mediu processos conhecidos por handle, imagem, token e
horário de criação; não confiou em PIDs históricos. Sua própria CPU/RSS não integra
os totais da aplicação. O trabalho de observação dentro de Electron/coletor, as
capturas e a navegação integram o custo observado desses processos.

## Leituras reais GPU

ADLX identificou **AMD Radeon RX 6750 XT**, discreta, vendor AMD. Todas as sete
capacidades dinâmicas consultadas retornaram sucesso/suporte. Intervalo interno
informado pelo SDK: 1.000 ms. Sem jogos, benchmark, carga artificial ou tuning.

**Uma inicialização nativa; 30 tentativas: 29 frames válidos e um rejeitado
(96,67% válidos).** O primeiro frame foi recusado por `age_null`; suas leituras
dinâmicas ficaram nulas/com erro. A mesma ponte continuou e entregou os 29 frames
seguintes, sem nova inicialização e sem disponibilidade parcial nesses frames.

| Métrica | Unidade | Mínimo | Média válida | Máximo |
|---|---|---:|---:|---:|
| Utilização GPU | % | 0 | 0,483 | 3 |
| Temperatura GPU | °C | 52 | 52,966 | 53 |
| Hotspot | °C | 55 | 55,966 | 56 |
| VRAM utilizada | MB | 980 | 1.007 | 1.048 |
| VRAM total | MB | 12.272 | 12.272 | 12.272 |
| Clock | MHz | 48 | 85,379 | 171 |
| Potência | W | 34 | 34,448 | 35 |
| Ventoinha | RPM | 488 | 492,862 | 497 |

29 leituras válidas por métrica dinâmica; capacidade, duas leituras. MB conserva
a unidade nativa ADLX, sem reinterpretar como GiB. Zero de utilização foi real,
não substituição de dado ausente. Não ocorreu zero RPM nesta sessão; esse caso
permanece coberto pelos testes simulados. O desvio exato do primeiro timestamp não
foi recolhido novamente: observou-se a regra `age_null`, sem afirmar que foram
novamente os mesmos −2 ms da sessão anterior.

Intervalos entre tentativas GPU: mínimo **2,0002 s**, média **2,2491 s**, máximo
**9,0086 s**, incluindo a redução de demanda durante a ocultação e as transições
de atividade. Não houve polling GPU abaixo da cadência mínima de dois segundos.

## CPU, RAM e armazenamento preservados

Resumo das amostras únicas recebidas pelo Electron, não de todas as leituras que
o coletor possa ter feito entre snapshots. Fonte, unidade, UTC e validade permanecem
em `evidence/analysis.json`. Os valores descrevem atividade normal durante o teste.

- CPU total do i5-12400: **5,806–23,773%**, média **11,215%**, 53 leituras válidas.
  Isso é uso total do PC, separado do consumo do monitoramento abaixo.
- RAM utilizável informada pelo Windows: **16.925.159.424 bytes** (~15,76 GiB).
  Uso médio **95,890%** (94,935–96,897%). Disponível: **525.119.488–857.309.184 bytes**,
  média **695.565.577 bytes**. A pressão de RAM observada limita comparações com
  outros cenários; não foram encerrados programas para alterar essa condição.
- Capacidade C: **510.677.479.424 bytes** (~475,6 GiB), ocupação média **49,689%**,
  disponível médio **256.892.295.168 bytes**. D: **480.101.003.264 bytes** (~447,1 GiB),
  ocupação **45,851%**, disponível **259.957.473.280 bytes**.
- C: leitura **0–20.108.583 bytes/s**, média **964.915 bytes/s**; gravação
  **20.391–6.898.397 bytes/s**, média **858.906 bytes/s**. D: leitura e gravação
  **zero válido** nas 53 amostras disponíveis de cada taxa.
- Atividade PDH C: 49 amostras válidas, quatro indisponíveis e uma de aquecimento;
  valores válidos **0,0215–4,5735%**, média **0,4639%**. D: 25 válidas, 28
  indisponíveis e uma de aquecimento; **0,00216–0,07249%**, média válida **0,0250%**.
  As indisponibilidades ficaram nulas; não foram convertidas em zero ou substituídas
  por ocupação/taxas. A causa exata dessas lacunas não foi investigada com dados
  brutos nesta sessão, nem foi implementado fallback.

Capacidades foram vistas em intervalos ~60,002 s. CPU/RAM/I/O tiveram timestamps
únicos recebidos em intervalos típicos ~1 s, com lacuna máxima ~9,04 s durante o
período de polling reduzido. Isso não mede diretamente cada chamada do provedor
básico; consultar o cache menos vezes pode omitir leituras intermediárias.

## Integridade temporal — ressalva importante

Idade ADLX no ingresso dos 29 frames aceitos: **0,2641–0,5491 s**, média **0,3878 s**.
Todos ficaram abaixo do limite **1,5 s**. A regra temporal, o contrato e os fontes
funcionais permaneceram idênticos. Nenhum dado futuro foi aceito ou corrigido.
Não foram injetados NaN, futuros, erros de driver ou desconexões nesta sessão física.

**O limite de 1,5 s é aplicado no ingresso do frame, não como SLA de idade máxima
na tela.** O cache mantém a política aprovada de stale após três intervalos (GPU
ativa: 6 s; inativa: 30 s). Nas 54 observações com janela visível, houve 51 estados GPU
disponíveis, um aquecendo, um erro inicial e um desatualizado ao retornar da bandeja.
Em 29 observações visíveis disponíveis, a idade do cache excedeu 1,5 s; máximo
**2,6918 s**. Não se deve afirmar frescor fim a fim ≤1,5 s com essa política.
A idade nativa no ingresso e a idade de cache não foram correlacionadas por frame
para calcular uma idade total exata na tela.
Nem todas essas observações estavam na aba Monitoramento; filtrando somente essa
aba, houve 32 observações, 19 disponíveis com idade de cache acima de 1,5 s, o mesmo
máximo de 2,6918 s e a mesma ocorrência stale de retorno. Os estados iniciais de
aquecimento/erro foram observados nos dados antes das primeiras capturas válidas.

Não houve alternância periódica válido/stale a cada ciclo ativo de dois segundos.
Ao restaurar após cerca de 12 s oculto, houve **uma observação stale aos 36,707 s**,
recuperada aos **37,714 s**, após a nova consulta. A interface não conservou o número
nessa indicação stale. É uma transição do cache/polling reduzido, não evidência de
falha de frescor no ingresso ADLX. Se o requisito desejado for ≤1,5 s também na
exibição, será necessária uma decisão explícita de arquitetura/cadência, separada
desta validação; nenhuma tolerância foi alterada para eliminar a transição.

## Handle, Named Pipe e encerramento

| Componente | PID observado |
|---|---:|
| Electron main | 3404 |
| Outros processos Electron observados | 21996, 7076, 21732 |
| Intermediário IPC | 20280 |
| Coletor | 18780 |
| Ponte ADLX | 22324 |

Ponte criada uma vez. `shell=False`, `close_fds=True`, lista explícita apenas com
o lease adicional aos stdio. A observação física registrou herança **false → true →
false** no pai. O processo nativo foi identificado por imagem/token próprios e
o handle conhecido foi duplicado temporariamente apenas para consultar tipo/ACL.

O filho possuía um pipe no mesmo valor de handle, com DACL protegida igual à do pai:
uma ACE da conta autorizada, máscara **0x00120183**, sem concessão de create-instance.
O servidor associado ao objeto era o coletor **18780**. A cópia de inspeção foi
fechada imediatamente, sem ler/escrever no pipe, fechar o handle original, alterar
ACL ou ler memória do processo. A semântica de herança de mesmo objeto/valor/acesso
é documentada pela [Microsoft](https://learn.microsoft.com/en-us/windows/win32/procthread/inheritance).

O Named Pipe de métricas entregou **56 respostas**, sem rejeições ou timeouts.
Não se fez segunda inicialização para testar duplicação. Falha abrupta do pai,
perda real de driver e falhas de herança continuam cobertas somente por substitutos;
não foram provocadas fisicamente. ACL por conta não isola completamente um atacante
que já execute código sob a mesma conta.

Sair foi acionado pelo **callback real do item Sair do menu da bandeja**, no processo
de desenvolvimento. Worker informou parada limpa, sem timeout, GPU limpa e saída
confirmada; Electron terminou com código **0**. Não houve kill, terminate ou retry.
Os sete processos observados encerraram; o inventário posterior não encontrou
componentes de desenvolvimento ou aplicativo residual. Ambos os pipes (métricas e
lease) ficaram ausentes, consultados sem conectar/criar endpoint: Win32 **2**.
Saída nativa limpa/processo encerrado é a evidência de liberação dos recursos/DLL;
não houve tracing intrusivo de FreeLibrary ou inspeção de memória.

## Dashboard, widget e estabilidade visual

Capturas **reais** em `screenshots/`: dashboard 1360×960 e widget 390×844. As três
abas, painel flutuante, unidades e indicadores funcionaram, sem transbordamento
horizontal nas verificações de geometria. A rolagem foi usada para GPU/armazenamento;
conteúdo abaixo da dobra não foi tratado como corte. Logo, cores e navegação
preservadas. CPU/RAM permaneceram nos cartões; GPU e temperatura/VRAM no modo compacto.

Foram exercidos os callbacks do menu real de bandeja para widget, restauração e
Sair; minimizar para bandeja ocultou a janela, e o mesmo ID de janela foi restaurado.
Não se fez clique físico do mouse na área de notificação nem captura do menu do
Explorer: essa parte do comportamento da bandeja já havia sido validada na dev.4.
Não se mediram escalas 125%/150%, múltiplos monitores ou sessão longa desta integração.

O cabeçalho “Comunicação não integrada” refere-se corretamente ao futuro cliente
Electron–agente; o estado separado “Coletor local conectado” representa o pipe.
Não houve comunicação operacional do Electron com HTTPS ou criação de identidade
desktop. Estados desconectados não foram simulados na interface física.

Nenhum erro de renderer/console, crash ou travamento observado. `stderr` ficou
vazio: **zero mensagens Crashpad**, inclusive 0xE9. Consulta limitada aos eventos
Application Error 1000, WER 1001 e recuperação de vídeo 4101 não encontrou evento
relevante no intervalo. Isso não resolve a pendência histórica de Crashpad.

## Desempenho real

CPU por GetProcessTimes (kernel+usuário) desde a criação, dividida por tempo total
da sessão e **12 processadores lógicos**. Picos são máximos de intervalos observados
de aproximadamente um segundo, não picos instantâneos. Memória por working set.

| Componente | CPU média, % da máquina | Pico de intervalo, % | RSS média MiB | Pico RSS MiB |
|---|---:|---:|---:|---:|
| Electron (quatro processos) | 0,34942 | 2,99196 | 376,956 | 402,016 |
| Intermediário IPC | 0,02482 | 0,26016 | 22,705 | 22,762 |
| Coletor | 0,08783 | 0,39020 | 31,570 | 31,691 |
| Ponte ADLX | 0,06683 | 0,13010 | 24,535 | 24,566 |
| Total observado | **0,52891** | **3,25050** | **454,224** | **480,727** |

Médias RSS por componente usam os intervalos em que ele estava vivo; total usa a
soma por instante. Não é obrigatório que a soma das médias de componentes com
contagens diferentes seja igual à média total. Partida/encerramento entram na
observação; RSS pode contar páginas compartilhadas mais de uma vez. O JSON também
contém médias/picos de intervalos e memória por PID. Processos transitórios que
terminassem antes da descoberta poderiam não ser medidos.

A referência de planejamento era ~0,53%/491 MiB; os números desta sessão são
próximos em CPU e menores em RSS, mas não demonstram causalidade/otimização, pois
sessões, pressão de RAM e observadores diferem. **A meta abaixo de 0,5% não foi
atingida na média incluindo a partida.** Não se omite esse custo usando apenas a
média dos intervalos pós-descoberta. Não houve benchmark, jogo ou carga artificial.

## Preservação e próximos passos

Agente original mantido: supervisor **5024**, worker **18304**, mesmos caminhos,
argumentos e horários de criação; listener único **8776**, TLS **1.3**, cadeia/
hostname/pin verificados e status HMAC **200** após a sessão. **Zero grants e zero
comandos pendentes.** Não houve nova interação física com Samsung ou novo pareamento.

Integridade sem diferenças: instalação dev.5 **109 arquivos**, perfil de produção
**77**, backups dev.3 **341**, dev.4 **75**, dev.5 **156**, **86 arquivos operacionais**.
Banco íntegro e identidades/segredos cifrados/schema/revogações iguais por hashes
lógicos; não se presume igualdade byte a byte do SQLite ativo após consultas de status.
Fontes da sessão, DLL oficial, evidências anteriores, HKCU Run e firewall intactos.

Sem atualização do Android, pacote Windows, rede, serviços, tarefas, drivers,
grants ou credenciais. Não foram executados Steam, CS2, WoL ou energia. TLS e
encerramento gracioso do agente não foram alterados. Agente deixado ativo.

Antes de um instalador com GPU permanente, considerar: política de frescor na tela,
meta de CPU ainda não atingida nesta medição, indisponibilidades PDH, watchdog
nativo de 82 s e modo GPU atual limitado a 70 s de desenvolvimento. A sessão curta
não valida produção permanente, estabilidade em jogos ou execução prolongada.
Esses pontos não foram corrigidos durante o teste.

Nenhum commit de código funcional foi necessário nesta etapa. O novo commit é
documental, com evidências/capturas e hashes dos observadores locais. Git funcional
permanece no conteúdo de `bcafe3a`; os checkpoints anteriores seguem ancestrais.
Nenhum repositório foi publicado.

Não é necessário rollback da instalação ou perfil. Reversão documental, se desejada,
é um `git revert` do commit deste relatório, sem apagar backups/evidências locais.
Reverter a implementação GPU (`ccfe941`, depois `08fd2fb`) seria uma decisão futura
separada, não executada. Não houve restauração, reset destrutivo ou parada do agente.

**Próxima autorização:** preparar a próxima versão instalável, sem instalar, após
decidir como tratar frescor de exibição e vida útil permanente. Não se preparou
qualquer pacote nesta sessão.
