# Primeira sessão física Windows dev.5 — 25/10/2026

**A instalação dev.5 abriu, exibiu monitoramento real e encerrou normalmente pelo
Sair da bandeja, com participação do usuário.** Foi uma única sessão de
**179,1187 s**, dentro do máximo de 180 s e acima do planejamento de aproximadamente
150 s. Não houve reinstalação, compilação, segunda abertura, carga artificial,
jogo, alteração funcional ou encerramento forçado.

**Há pendências:** CPU observada acima da referência anterior, duas mensagens de
erro do Crashpad e cobertura física parcial de alguns controles da janela. Esta
execução não constitui aprovação completa de desempenho ou de todos os cenários
de falha. Nenhuma correção foi aplicada.

Horário de São Paulo (**UTC−03:00**): abertura **08:06:52,364**; todos os componentes
observados já estavam encerrados em aproximadamente **08:09:51,482**. Evidências
JSON conservam UTC e tempos monotônicos. O observador fez 180 amostras e terminou.

## Pré-verificação independente

- Instalado **2.0.0-dev.5**, `com.lone.smartroom`, no destino aprovado. Os 106
  arquivos do payload, desinstalador e ícone correspondiam aos artefatos preparados.
- Zero Electron, coletores, intermediários ou instaladores residuais; zero pipes
  `LoneSmartRoom.Monitoring.Dev.v1.*` antes de abrir.
- Perfil de produção: 76 arquivos com hashes iguais ao estado pós-instalação.
  Backup `Windows-before-dev5-20261025T104128Z`: 153 arquivos de dados, manifesto,
  estrutura e hashes íntegros; não houve restauração.
- Agente verificado por imagem, proprietário/SID, argumentos, parentesco e horário
  de criação. A comparação temporal usa DateTime normalizado, evitando repetir o
  falso alerta da instalação. Supervisor 400, worker 8680 e redirectors 17772/10996
  mantiveram suas identidades. Listener único 8776 do worker; zero grants.
- GETs fixos autenticados `/v2/status` e `/v2/apps`: 200/TLS 1.3, hostname/cadeia/pin
  validados antes da autenticação. Nenhuma identidade nova ou segredo registrado.
- Fonte do ciclo de vida conferida: main verifica o runtime fixado, cria uma ponte,
  a ponte cria seu worker e ambos mantêm os vínculos esperados. Sair aguarda seus
  componentes por fechamento do canal de vida; não usa a parada do agente HTTPS.
- Observador testado apenas para consulta, sem elevação, antes da abertura. Ele
  não inicia nem encerra processos e não abre conexão no pipe de monitoramento.

## Aplicativo real e proveniência

Foi aberto uma única vez:
`<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe`.

Não foram usados Electron de desenvolvimento, flags de depuração, NODE_OPTIONS,
perfil alternativo, portátil ou captura HTML isolada. A janela observada foi
**986010**, processo principal **9108**; a árvore de acessibilidade identificou
`resources/app.asar/index.html` da instalação de produção. As imagens em
`screenshots/` são capturas reais dessa sessão.

| Componente | PIDs observados | Resultado |
|---|---|---|
| Electron | 9108, 8484, 19364, 9792 | Um principal, filhos Chromium esperados |
| Intermediário IPC | 19380, filho de 9108 | Uma instância |
| Coletor | 11812, filho de 19380 | Uma instância |

Todos os processos retidos foram verificados com imagem esperada, criação da
sessão, mesmo SID/sessão Windows e **sem elevação**. Nenhum processo desconhecido
foi finalizado ou controlado. O agente não é descendente nem componente da UI.

## Resultado visual e funcional

- Logo/símbolo oficiais, preto/grafite/vermelho, versão dev.5 e título **Seu espaço,
  sob controle** preservados.
- Abas **Controles**, **Monitoramento PC** e **Gamer Launcher** abertas com sucesso.
  Steam e CS2 apareceram desabilitados; nenhum botão operacional foi acionado.
- Painel flutuante de permissões abriu e fechou, mantendo o bloqueio e a explicação
  de autorizações. Não foram alteradas permissões ou campos de conexão.
- Transição widget inicial → dashboard → widget funcionou, na mesma sessão.
  Navegação inferior e rolagem do widget permitiram visualizar os indicadores.
- Em Monitoramento: **Coletor local conectado · leitura do Windows**. O cabeçalho
  **Comunicação não integrada** refere-se ao cliente HTTPS desktop ainda ausente;
  é independente do Named Pipe. Não foi simulado estado autenticado desktop.
- A ação explícita **Minimizar para bandeja** foi enviada na janela real. O usuário
  confirmou restauração pelo ícone e seleção de **Sair**. A ferramenta não expõe
  a área de ícones ocultos como janela controlável; não houve captura do menu ou
  da restauração manual. O observador registrou um único processo principal.
- Dimensões/posição e preferência foram preservadas antes/depois: dashboard
  **1360 × 960 em (280,36)**; widget **429 × 820 em (1462,106)**; último modo widget;
  bandeja automática **desligada**. Não foi realizado novo teste de arrastar ou
  redimensionar, nem de minimizar normalmente para a barra de tarefas, nesta sessão.
- Não houve sobreposição ou corte relevante nas telas selecionadas. Conteúdo
  abaixo da dobra do widget é acessado por rolagem; não se trata de captura de
  página inteira nem validação de todas as escalas Windows.

## Métricas reais vistas na interface

CPU identificada por leitura posterior: **12th Gen Intel Core i5-12400**.
Valores abaixo são leituras visuais arredondadas, não exportação do contrato bruto.

| Métrica | Observação real |
|---|---|
| CPU total | 8,9%–25% nas nove capturas/observações selecionadas de Monitoramento |
| RAM utilizável | 15,8 GiB |
| RAM utilizada | Aproximadamente 9,0–9,1 GiB |
| RAM disponível | Aproximadamente 6,7 GiB |
| RAM utilizada (%) | 57,3%–57,6% nas observações selecionadas |
| C: capacidade / disponível / ocupado | 475,6 GiB / 235,5 GiB / 50,5% |
| D: capacidade / disponível / ocupado | 447,1 GiB / 348,7 GiB / 22% |
| C: leitura | Zero válido e valores até 71,82 KiB/s nas observações |
| C: gravação | Zero válido e valores até 1,37 MiB/s nas observações |
| D: leitura / gravação | 0 bytes/s, com indicação de leitura válida nas observações |
| Atividade C: | `<0,1%`, `0,1%` e `Indisponível`, conforme validade |
| Atividade D: | `<0,1%` e `Indisponível`, conforme validade |

**Distinções confirmadas:** taxa válida zero permanece numérica; atividade nula
aparece como Indisponível; percentual positivo muito pequeno aparece como `<0,1%`;
capacidade é identificada como **Ocupação do disco**, separada de B/s e atividade.
Não houve substituição de uma métrica por outra ou fallback de PDH.

O subconjunto de **nove horários distintos de I/O acessíveis pela UI** apresentou
atividade válida em **8/9 quadros C:** e **5/9 D:**. Esses números descrevem apenas
os quadros selecionados, **não a disponibilidade de todas as amostras dos 179 s**.
Taxas D: iguais a zero não comprovam incapacidade de medir atividade futura sob
carga; não se produziu carga artificial para tentar obter números diferentes.

GPU, temperaturas, VRAM, RPM e FPS permaneceram indisponíveis. Histórico gráfico
continua explicitamente sem integração; não foram desenhadas curvas fictícias.

## Atualização, validade e cache

Cinco observações de acessibilidade feitas aproximadamente a cada 1,09 s deram
os seguintes intervalos entre carimbos CPU: **1,002; 1,002; 2,013; 1,012 s**.
Os carimbos I/O acompanharam as mesmas atualizações com diferenças milissegundárias.
O salto de 2,013 s pode representar um quadro não observado entre duas rotinas de
aproximadamente 1 Hz; a sessão não permite separar atraso do provedor, transporte,
renderer e captura. Não se declara frequência perfeita de 1 Hz durante todo o teste.

A capacidade permaneceu no seu ritmo mais lento e separada da leitura I/O. Origem,
horário, última leitura válida e estado estavam disponíveis nos detalhes. A UI e
o widget continuaram recebendo o mesmo pipeline depois do antigo limite de 70 s
das sessões de desenvolvimento, até o encerramento da aplicação.

Não foi forçada perda de conexão, pausa do coletor ou dado desatualizado nesta
instalação. A expiração e reconexão continuam cobertas pelos testes automatizados
da release, mas **não foram induzidas fisicamente nesta sessão**. Também não houve
leitura de diagnósticos internos do cache por cliente adicional; a conclusão física
se limita às leituras e aos horários observados na interface.

## IPC e encerramento

Foi observado **um único nome de pipe** da sessão. O pipe não existia nas três
primeiras amostras de bootstrap (aproximadamente 0,05, 1,05 e 2,05 s); apareceu e
permaneceu único durante a coleta. Na última amostra, todos os processos haviam
saído e o pipe estava liberado. Não foi criado cliente de teste externo ao par
autorizado, nem endpoint TCP/HTTP adicional.

O payload verificado preserva DACL explícita da conta, FIRST_PIPE_INSTANCE,
rejeição remota, identidade dos processos pares/SID/sessão, mensagens somente
leitura e limites validados. A conexão física bem-sucedida evidencia o caminho
legítimo. Não foram repetidos ataques, clientes indevidos ou inspeção invasiva de
ACL durante essa sessão. ACL por usuário não isola completamente outros programas
sob a mesma conta.

O usuário confirmou **restauração e Sair pela bandeja**. Última amostra com processos
ativos: **178,1117 s**; em **179,1122 s** não havia processo observado ou pipe.
O observador fechou seus handles e terminou. Não se mediu precisamente a latência
entre o clique humano e o encerramento. Códigos de saída individuais não foram
capturados; não se deve inferi-los apenas da ausência de processos.

Verificação independente posterior: **zero Electron, coletores, intermediários e
instaladores**, sem pipe de monitoramento. O observador não usou terminate, kill,
WM_CLOSE, comandos de shell, canal de parada do agente ou conexão IPC de controle.

## Desempenho observado

Contadores **GetProcessTimes** (kernel+user) dos processos próprios desde sua
criação, divididos pelo tempo de sessão e **12 processadores lógicos**. Memória:
working set via **K32GetProcessMemoryInfo**. Descoberta por Toolhelp e handles retidos
somente para consulta/sincronização. O próprio observador foi excluído dos totais.

| Componente | CPU média da máquina | Pico em intervalo de ~1 s | RSS média | RSS pico |
|---|---:|---:|---:|---:|
| Coletor | 0,0640% | 5,4661% | 29,85 MiB | 30,32 MiB |
| Intermediário IPC | 0,0443% | 4,1645% | 23,40 MiB | 23,71 MiB |
| Electron, quatro processos | 2,0427% | 9,2399% | 383,95 MiB | 401,98 MiB |
| **Conjunto** | **2,1510%** | **14,8359%** | **437,20 MiB** | **455,80 MiB** |

Cadência do **observador de processos**, distinta da cadência dos sensores:
180 amostras; intervalos **1,00005–1,00078 s**, média **1,00034 s**.
Picos por componente podem ocorrer em momentos distintos; não devem ser somados
para obter o pico conjunto. Working sets podem contar páginas compartilhadas mais
de uma vez. A primeira leitura de cada processo inclui custos acumulados de sua
criação; picos não isolam estado ocioso ou uma operação específica.

Referência anterior de desenvolvimento: CPU média 0,4613%, RSS média 441,25 MiB,
pico 463,43 MiB. A CPU atual foi maior, principalmente no Electron. A soma de memória
foi ligeiramente menor. Houve consultas de acessibilidade, screenshots, mudanças
de abas, layout e caches de primeira execução; essas condições diferem da sessão
anterior. Não foi realizada sessão ociosa comparável, portanto **não se estabelece
causa nem regressão comprovada**. A média conjunta observada ficou acima da referência
de planejamento de 0,5%; não se deve apresentá-la como meta cumprida.

## Erros e limites encontrados

O novo `debug.log` da pasta de programas contém **duas mensagens ERROR do Crashpad**:

```text
08:06:53,489  crashpad/util/win/registration_protocol_win.cc:136
08:08:53,484  crashpad/util/win/registration_protocol_win.cc:136
TransactNamedPipe: Não há processo no outro extremo do pipe. (0xE9)
```

A origem indicada é o protocolo de registro do **Crashpad**, diferente do código
do Named Pipe de monitoramento. A sessão não identifica o gatilho nem comprova
efeito sobre futuros relatórios de crash. Não se deve ocultar a falha ou concluir
que ela é inofensiva apenas porque a UI permaneceu funcionando. Merece diagnóstico
separado, sem reproduzir automaticamente ou alterar Crashpad nesta autorização.

Não foram encontrados eventos correspondentes Application Error/WER/hang
(1000/1001/1002) para o aplicativo no período consultado. O observador registrou
zero falhas próprias de identidade/recursos, sem congelamento observado da UI.
Isso não equivale a provar ausência de qualquer erro interno não registrado.

Limitações físicas: não foram exercitados redimensionamento/arraste, minimizar
normalmente pela barra de tarefas, perda/reconexão de IPC, stale induzido ou todas
as escalas/DPI. O menu da bandeja e a restauração foram confirmados pelo usuário,
sem screenshot próprio. A sessão chegou perto do máximo; futuras validações devem
reservar mais margem de tempo para a interação manual da bandeja.

## Preservação final

- **108 arquivos preexistentes da instalação intactos por hash**. Foi acrescentado
  somente `debug.log` pelo funcionamento normal do Electron; não foi apagado.
- Perfil: um arquivo novo de cache gráfico e 20 arquivos alterados em caches,
  DIPS e logs LevelDB de armazenamento local/sessão, compatíveis com uma execução
  normal. Nenhum arquivo removido. Preferências de janela, modo, posições e bandeja
  automática são idênticas ao estado inicial. Não houve limpeza, importação,
  descriptografia ou restauração. Inventário detalhado fica no cache privado.
- Novo backup: **156 arquivos, com metadados**, hashes idênticos antes/depois.
  Backups pré-dev.3 e pré-dev.4 igualmente preservados. **86 arquivos operacionais**
  fora dos escopos autorizados de UI/perfil/instalação mantiveram seus hashes.
- Banco íntegro, identidade cifrada, revogações, esquema e zero grants preservados.
- Supervisor **400**, worker **8680**, redirectors **17772/10996** permanecem com
  os mesmos caminhos, proprietário e horários de criação. Listener único
  **8776 → 8680**. GETs finais autenticados **200/TLS 1.3**, pin válido, agente online
  e nenhuma autorização de aplicativo.
- Run/RunOnce, pastas Inicializar, serviços, tarefas e firewall sem diferenças nas
  configurações comparadas. Não se alterou OneSettings\RefreshCache.
- Android, WoL, certificados, HMAC, credenciais, pareamento e executores preservados.
  Não houve Steam, CS2, pacote WoL, energia ou mudança de drivers/serviços/rede.
- A pendência TLS e o encerramento gracioso do **agente HTTPS** continuam separados;
  somente o encerramento dos componentes de monitoramento próprios foi exercitado.

## Evidências e próximos passos

`evidence/resources.json` contém as medições; `analysis.json` separa observações
visuais de métricas completas do observador; `metric-ui-samples.json` registra os
carimbos consultados. Capturas e árvores de acessibilidade são da instalação real.
Os scripts de observação/análise usados estão preservados como texto para auditoria.
Nenhum inventário privado de perfil, segredo, dump ou chave foi incluído no Git.

Recomendação: analisar separadamente o consumo do Electron e o erro Crashpad,
primeiro em leitura. Nova medição comparável ou reprodução física requer outra
autorização. O aplicativo fica **instalado e encerrado**, o agente HTTPS original
**ativo**, pareamento Samsung preservado e **zero grants**.

Este checkpoint acrescenta somente documentação. Nenhuma correção funcional foi
implementada. Os commits `c377a5c` e todos os checkpoints anteriores são preservados.
