# Expansão modular LSR / NEX — inventário e plano

26/10/2026. Escopo desta etapa: inventário do repositório, arquitetura e plano
verificável. **Nenhuma funcionalidade operacional nova foi habilitada.**
Base: `7c4ddd100c44bba3e90d95760b2e34b7057111b7`.
Branch: `feature/modular-expansion-plan`.

O pedido inclui todas as famílias funcionais descritas na conversa de referência.
O histórico recuperado lista as funções, mas não disponibiliza todas as capturas;
este plano não afirma ter auditado cada tela nem reproduzir sua aparência.
Identidade, textos, código e assets serão próprios do LSR/NEX.

## Checkpoint C0

Antes das edições foi salvo `.cache/modular-expansion-2026-10-26/source-checkpoint.json`:
HEAD, branch original, status e SHA-256 de **1.869 arquivos** versionados ou
preexistentes fora do Git. Esse recibo local não contém conteúdo de credenciais.
Não é backup da instalação nem do banco operacional e não substitui os backups
anteriores. O commit base e a recuperação existente permanecem preservados.

Três arquivos estavam fora do Git na primeira inspeção; durante a preparação do
checkpoint um quarto apareceu. O recibo inclui `diagnostics/evidence_adapters.py`,
`evidence_cache.py`, `evidence_contract.py` e `mock_evidence.py`.
Não foram incorporados a este trabalho, alterados ou usados como integração nova.
Nenhum AGENTS.md foi encontrado na árvore inspecionada.

## Inventário verificado em fontes e documentação

“Existente” abaixo significa código/evidência encontrados, não uma nova validação
física. Documentos históricos que dizem “futuro” ou “não instalado” precisam ser
lidos com os recibos posteriores; não representam necessariamente o estado atual.

| Família solicitada | Base real encontrada | Lacuna / próxima entrega |
|---|---|---|
| Painel | Electron: `desktop.js`, `monitoring-model.js`, `monitoring-renderer.js`; dashboard/widget | Consolidar disponibilidade, histórico e evidência; não criar nota arbitrária de otimização |
| Manutenção | Central simulada e leitores passivos em `diagnostics/`; não é motor de reparo | Separar inspeção de DISM/SFC/CHKDSK e reparos, DNS/IP, rede, Update, áudio, Explorer, ícones, Store/Start; cada execução futura com plano próprio |
| Sensores | `monitoring/`, Win32/PDH, cache, Named Pipe, ponte própria `native/adlx/bridge.cpp` | Rede por interface, SMART/NVMe/horas e sensores adicionais dependem de suporte/provedor; não inferir saúde de espaço livre |
| Limpeza | Espaço e I/O dos volumes; não foi encontrado fluxo seguro completo de limpeza | Análise sob demanda por categoria, orçamento de I/O, estimativa e revisão dos arquivos antes de excluir |
| Inicialização | Evidência do autostart do agente em `diagnostics/startup_evidence.py` | Inventário dos demais Run/Startup/tarefas; alteração individual com valor anterior e reversão |
| Windows | Gates e diagnóstico existentes; sem catálogo completo de ajustes | Leitura de Game Mode, energia, efeitos, HAGS e recursos suportados antes de propor mudanças |
| Mouse / teclado | Sem módulo dedicado encontrado | Leitura de configurações; ajustes individuais de aceleração/acessibilidade, preservando estado anterior |
| GPU / monitor | ADLX somente leitura e retomada GPU | Inventário de modos/taxas; nenhuma escrita ADLX, OC/UV, troca de driver ou perfil presumido |
| Perfis | Preferências do shell em `desktop-preferences.cjs`; não são perfis de tweaks | JSON declarativo versionado, preview do diff, aplicabilidade e rollback por item; nunca scripts importados |
| Jogos | Steam/CS2 em `agent/windows/steam_launcher.py`, `cs2_launcher.py`, grants por dispositivo | Descoberta de outros jogos em leitura; “preparar e jogar” primeiro só mostra preflight e usa launcher permitido |
| Overlay | Widget próprio existente; não equivale a overlay dentro do jogo | Avaliar janela externa opt-in; sem DLL injection, hooks ou acesso à memória do CS2 |
| Testes mouse / monitor | Sem módulo dedicado encontrado | Testes interativos isolados; polling aparente depende da API/agendamento, sem promessa de precisão elétrica |
| Testes rede | Status HTTPS e presença não equivalem a speedtest/ping/perda | Alvo permitido, duração/volume limitados e consentimento para tráfego ativo; não concluir perda de jogo a partir de ICMP isolado |
| Instalador de apps | Sem catálogo/instalador em lote encontrado | Catálogo fixo com publisher/ID, detecção em leitura, preview, origem e licenças; instalar exige confirmação por lote |
| Debloat / IA | Sem motor dedicado encontrado | Inventariar apps/recursos/políticas; dependências, escopo por usuário e recuperação explícitos antes de remoção |
| Restauração | Histórico Git, recovery e documentação de preservação | Detectar disponibilidade de System Restore; ponto não substitui backup nem garante desfazer todos os efeitos |
| Histórico / exportação | Cache métrico circular, recibos de diagnóstico e histórico durável de comandos de apps | Histórico local limitado e exportação CSV/JSON sanitizada com origem/tempo/unidade; sem exportar segredos |
| Android / NEX | Kotlin/WebView, WoL independente, cliente HTTPS nativo, confirmação de apps | Consumir projeções futuras em leitura por contrato específico; nenhum shell remoto ou grant implícito |

Fontes de segurança: `contracts/secure-status-v2.md`, `contracts/app-launch-v2.md`,
`apps/windows-ui/main.cjs`, `preload.cjs`, `agent/windows/secure_*.py`.
O pareamento não concede execução. As permissões locais de Steam/CS2 e a confirmação
nativa Android continuam separadas. Não se adiciona capacidade usando o endpoint
de status nem a allowlist de apps como atalho.

## Evidência operacional existente e pendências

- [Dev.7 física](../windows-first-run-dev7-2026-10-26/README.md): CPU i5-12400,
  RX 6750 XT, RAM e volumes observados; homologação parcial de widget/bandeja/retomada.
- [CS2 remoto](../CS2-REMOTE-PHYSICAL-VALIDATION.md): abertura até menu confirmada
  em sessão anterior; não mede FPS, frametime, input latency ou estabilidade em partida.
- [Central de diagnóstico](../diagnostic-center-2026-10-26/README.md): integração
  visual simulada isolada. Não apresentar suas fixtures como saúde atual do PC.
- [Validação passiva](../diagnostics-passive-second-2026-10-26/README.md): HTTPS
  autenticado observado naquela sessão; não garante estado atual ou encerra a
  investigação TLS 10054. Autostart continua inconclusivo e encerramento gracioso
  do agente carece de validação operacional completa.

Nesta tarefa não se leu banco, certificado, perfil instalado ou credenciais, nem
se contatou o agente. Não há afirmação nova sobre processos, grants ou saúde atual.

## Etapas e checkpoints

| Etapa | Entrega concreta | Critério para fechar o checkpoint |
|---|---|---|
| C0 — esta entrega | Inventário, plano, arquitetura e regressões offline | Plano entregue; gate global pendente pela divergência histórica de hash e alterações concorrentes documentadas |
| C1 — diagnóstico em leitura | Projeção dos recibos/cache existentes, estados reais separados de simulação | Contrato restrito, TTL/origem/timestamp, falha/recuperação testadas; integração HTTPS só após tratar seu gate TLS |
| C2 — inventários | Inicialização, apps, rede, modos de monitor, ajustes atuais e candidatos de limpeza | Consultas sob demanda, limites de tempo/volume, cancelamento e ausência de escrita verificáveis |
| C3 — histórico e perfis de observação | Min/max por sessão, CSV/JSON sanitizado, perfis de visualização | Memória/disco limitados, dados antigos identificados, importação validada e sem código executável |
| C4 — ferramentas interativas | Mouse/monitor/rede; preflight de jogo; estudo do overlay externo | Testes reais explicitamente iniciados, sem hooks; custo e limitações medidos antes de anunciar compatibilidade |
| C5 — alterações reversíveis | Uma ação por vez: configurações, inicialização, perfis de ajustes | Preview, confirmação local, backup do valor, precondições, leitura posterior e rollback testado com mocks |
| C6 — manutenção/instalação/remoção | Reparos específicos, instalação em lote, limpeza, debloat e restauração | Confirmação de cada plano; impacto em reinício/rede/dependências e limites de recuperação apresentados |
| C7 — integração e distribuição | Android/NEX por capacidades específicas, builds e atualização compatível | Regressão HTTPS/WoL/credenciais, assinatura e recuperação; instalação e ações reais aprovadas separadamente |

Cada checkpoint gera diff revisável, testes, limitações, hashes e procedimento de
reversão antes de avançar. Código de desenvolvimento pode ser preparado dentro do
pedido; aplicar mudanças no Windows, remover dados, conceder execução, instalar
ou atualizar aplicativos/dispositivos depende da confirmação do plano concreto.
“Incorporar tudo” não transforma essas ações em execução automática.

## Critérios CS2 e escopo de segurança

Reutilizar o coletor/cache atuais; não duplicar polling, processo ADLX ou cliente
do pipe. Pausar trabalho da UI oculta e adiar scans pesados durante jogos.
Não incluir limpeza automática de RAM, shader cache ou prefetch no preflight;
esses itens exigem avaliação e autorização próprias e podem prejudicar medições.
Não aplicar pacotes genéricos de latência, prioridades, serviços, timers, energia
ou ajustes de GPU baseados apenas nos modelos i5-12400/RX 6750 XT.

Não criar exclusões automáticas do Defender, desabilitar proteções, alterar Secure
Boot/TPM ou contornar anticheat. Overlay futuro não pode prometer aprovação pelo
anticheat sem evidência específica. Testes A/B futuros devem registrar versão,
cenário repetível, frametimes/p95/p99, CPU, RSS, duração e condições comparáveis;
o custo aceitável precisa ser definido e medido, não anunciado como zero.

Arquitetura proposta: [ARCHITECTURE.md](ARCHITECTURE.md).
Validação desta etapa: [VALIDATION.md](VALIDATION.md).
