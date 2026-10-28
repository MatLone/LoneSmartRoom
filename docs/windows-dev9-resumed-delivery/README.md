# Entrega Windows retomada — 28/10/2026

O trabalho foi recuperado na branch `feature/windows-control-center`, preservando
os checkpoints anteriores e o worktree `feature/hardware-readonly-c1` (`f345172`).
A interrupção anterior coincidiu com indisponibilidade da revisão automática por
limite de uso. Não foi contornada. A instalação assistida r9 já havia abortado
antes de remover a dev.8; não foi repetida nesta retomada.

## Resultado consolidado

**Agente pronto para migração operacional completa: NÃO.** O supervisor,
encerramento cooperativo, concorrência, retentativas limitadas e diagnóstico
passivo estão implementados e testados isoladamente. Falta homologar login,
recuperação e encerramento reais; o bootstrap ainda precisa receber o publisher
registrado e a autorização de leitura específica para habilitar o relay. Sem
isso, a rota permanece desativada. Nenhuma identidade do Samsung foi emprestada
ao Electron. Um processo ou listener presente não comprova autenticação.

A versão instalada continua **2.0.0-dev.8**, confirmada lendo seu ASAR. O agente
está offline, sem listener 8776. Não foi iniciado, reiniciado ou substituído.

| Funcionalidade | Implementada | Testada com dados reais nesta entrega | Funciona instalada | Bloqueio / limite |
|---|---|---|---|---|
| 12 áreas, três abas, widget e painéis | Sim | Electron de desenvolvimento, perfis separados | Sem nova homologação da dev.8 | Candidata r10 não instalada |
| CPU, RAM, discos e GPU contínuos | Sim, componentes existentes preservados | Sem nova sessão de sensores/ADLX | Validações anteriores; retomada física ainda parcial | Não declarar homologação adicional |
| Inventário CPU e 12 núcleos, DIMMs, discos | Sim | Windows/CIM e main/preload reais | Novo apresentador ainda não instalado | Temperatura e potência CPU nulas |
| Apps, processos, drivers, serviços, periféricos e startup | Sim, somente leitura | Consultas reais, com limites de retorno | Novas correções ainda não instaladas | Não é scanner irrestrito nem ferramenta de reparo |
| Rede, taxas por adaptador, ping e DNS | Sim | Contadores reais; ping/DNS apenas localhost | Candidata não instalada | Não mede banda da Internet; primeira taxa é null |
| Diagnóstico das leituras de hardware | Sim, projeção do cache | Contrato sintético e interface real sem coletor | Ainda não instalado | Sem sondas adicionais; cache ausente é explícito |
| NEX local e conversa limitada | Sim | UI real; medidas do cache testadas com fixtures identificadas | Ainda não instalado | Sem IA externa, voz ou execução de comandos |
| Histórico/gráficos e CSV | Existentes, preservados | Regressões; sem nova coleta física | Sem nova homologação | Não há dados inventados definitivos |
| FPS por CSV PresentMon e overlay | Sim, leitor e janelas | CSV sintético no fluxo real main/preload/arquivo | FPS real não homologado | Capturador externo não instalado/executado; nenhum jogo iniciado |
| Manutenção e perfis | Prévia e preferências locais | Regressões isoladas | Não há reparos operacionais | Limpeza/otimizações/reversão sistêmica não habilitadas |
| Mouse, teclado, padrões e áudio | Ferramentas existentes | Navegação e mocks; sem nova homologação física | Não revalidado | Dependem de interação/permissão |
| RGB, voz e automação física | Parcial/contratos | Não | Não | Hardware, APIs e autorização específicos |
| Supervisor e diagnóstico passivo HTTPS | Sim em desenvolvimento | Leitura de processos/listener; sem autenticação com agente offline | Legado preservado | Login e migração ainda exigem validação própria |

## Correções e implementações

- Instalador x86 seleciona o PowerShell x64 nativo por Sysnative. Helper usa APIs
  .NET para hash e ACL; não altera política de execução ou segurança do Windows.
  A causa e a tentativa anterior estão em [relatório do instalador](../windows-dev9-installer-fix/README.md).
- Inventário isola falha dos contadores por núcleo da identificação da CPU.
  Uma consulta anterior retornou indisponível; sua causa exata não foi capturada.
  As leituras posteriores foram válidas, sem afirmar que toda falha WMI foi eliminada.
- Processos auxiliares recebem ambiente mínimo e módulos do Windows conhecidos.
- Taxas de rede usam timestamps da fonte e identidade estável do adaptador.
  Reinício de contador, intervalo inválido e primeira amostra resultam em null;
  zero válido continua zero. Bytes/s não são confundidos com velocidade do link.
- Tabelas paginam 50 itens até o limite de 300 retornados; rótulos, unidades,
  uso por núcleo e detalhes técnicos ficam separados. Conteúdo usa textContent.
- Diagnóstico de hardware reaproveita a projeção revisada do worktree C1, sem
  substituir o manifesto de runtime nem criar outro coletor ou IPC.
- NEX resume somente cache real validado, respeita frescor e barreira de retomada
  GPU; histórico local de até 40 mensagens/64 KiB, escrita atômica e recusa a
  arquivos alterados/corrompidos. Não consulta o agente nem executa ações.

## Evidências e testes

- **3.498 verificações Node, 27 suítes**, sem falhas.
- **137 testes Python** da consolidação do agente; zero falhas/erros/skips.
- Regressões anteriores do runtime mantidas: 268 Python, 35 C++ com substitutos,
  37 de encerramento isolado. Não foram repetidas sem alteração nesses componentes.
- **2.323 inspeções do runtime**, 39 arquivos e 527 módulos stdlib; sem chamadas
  nativas, sensores ou execução do interpretador empacotado.
- **518 verificações estáticas de distribuição**; 68 arquivos ASAR, pacote x64,
  ícone oficial, metadados, ausência de credenciais e payloads NSIS/portátil iguais.
- **7 verificações NSIS→helper nativo** e 8 cenários de preservação/ACL em fixtures;
  não equivalem a instalar o produto.
- Electron real de desenvolvimento: 100%, 125% e 150%; 34/35/35 verificações,
  respectivamente, 16 capturas por execução; zero erros renderer. Última execução
  contém hashes do apresentador atual. Encerramento normal, sem coletores físicos.
- Leitura real identificou i5-12400 (6/12), 16 GiB em dois DIMMs, C:/D:, aplicativos,
  serviços e periféricos. Clock informado 2500 MHz é metadado, não medição turbo.
- Duas consultas de rede observaram intervalo 3,469 s: um adaptador recebeu
  2743,15 B/s e enviou 647,16 B/s; outro apresentou zeros válidos. Nenhuma carga
  artificial ou teste de Internet foi produzido.

A revisão visual em 150% observou RSS somado médio **482,09 MiB**, máximo amostrado
**485,26 MiB** em apenas três amostras de Electron, sem coletores e com compositor
por software. Páginas compartilhadas podem ser somadas mais de uma vez. CPU fica
registrada nas unidades brutas de `getAppMetrics`, sem inferir uma porcentagem
total comparável à sessão física anterior. Não é teste de vazamento prolongado.

Capturas reais de desenvolvimento: [hardware](captures/hardware.png),
[NEX](captures/nex.png), [widget](captures/widget.png),
[diagnóstico](captures/diagnostics.png), [overlay](captures/overlay.png).
Sem coletor, NEX e painéis mantêm indisponibilidade; o CSV de FPS simulado é
identificado somente em sua própria captura, não como telemetria real.

## Artefatos

Candidata **2.0.0-dev.9 r10**, appId `com.lone.smartroom`, x64, **NotSigned**.
Nenhum novo instalador, portátil ou executável empacotado foi executado.

- NSIS: 105.795.323 bytes; SHA-256
  `be5148a92bd13ed82b19e09b76d4a1fc7f264ea621f8245fb89499218fea9c9a`.
- Portátil: 105.504.500 bytes; SHA-256
  `e72be4c11a41016e11d3e2f8bab6598e6280794bad1f1fd420adb006583004ae`.
- Fontes do agente r2: 70 arquivos, sem estado/venv/segredos; ZIP SHA-256
  `d275e4d8048d54743ad53f6519fee7d0f747f03aee0a9ecb0804d65539ff243f`.

Caminhos, tamanhos e hashes completos: [artifacts.json](artifacts.json).
Distribuição: `.cache/artifacts/windows/desktop-dev9-consolidated-candidate-r10/`.
Fontes: `.cache/artifacts/agent/agent-reliability-dev9-r2/`.
As revisões anteriores permanecem preservadas; **r9 não deve ser implantada**.
Os avisos do builder sobre signtool não significam que o produto foi assinado:
Authenticode foi conferido e os dois pacotes continuam NotSigned.

## Preservação e próxima homologação

Reverificação final: instalação (118 arquivos) e perfil (83) iguais ao baseline;
quatro arquivos protegidos, identidades do banco e HKCU Run preservados; banco
quick_check íntegro, **zero grants e zero comandos pendentes**. Backup anterior
com 195 arquivos verificado. Backup dev.9 atualizado com 201 arquivos novamente
verificado, manifesto SHA-256
`f6131c8f01068abde895404fb87d16f5b1904a990c6ba8c01c9e80420034c02a`,
ACL exclusiva já validada na criação. Nenhum processo Electron/Python/ADLX ao fim;
listener 8776 ausente. Android não foi acessado; nenhuma alegação de nova inspeção
no aparelho. Não houve alterações no firewall, serviços, tarefas ou HKCU Run.

Próxima etapa requer autorização separada: verificar hashes e backup, executar
UMA instalação assistida r10 sem abertura final e verificar estática antes de
homologar aplicativo. Não contornar SmartScreen/Defender. Conservar backup e
journal de preservação fora da instalação. Se o helper recusar, interromper,
não repetir ou apagar journals. Rollback autorizado: fechar normalmente o app,
validar o manifesto do backup e restaurar instalação/perfil correspondente sem
sobrepor dados novos desconhecidos; nunca limpar perfil ou banco do agente.

A migração do agente é independente: registrar publisher por identidade retida,
configurar escopo de leitura separado de grants, preservar certificado/DPAPI e
provar single-instance, status autenticado e encerramento antes de alterar Run.
Não existe implantação automática ou garantia de despacho HKCU Run.

TLS 10054, inicialização após login, encerramento operacional do agente, Crashpad,
retomada física GPU e demais pendências de hardware continuam abertas. Esta
entrega não as declara resolvidas.

Commits: `9d4c115` (supervisão/evidências), `c7daf8c` (instalador),
`d199962` (inventários, diagnóstico de cache, NEX e candidata r10).
A reversão do código deve usar revert dos checkpoints desta entrega, em branch
isolada; não resetar trabalho concorrente nem restaurar produção automaticamente.
