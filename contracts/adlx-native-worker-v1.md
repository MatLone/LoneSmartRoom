# Worker ADLX somente leitura — contrato privado v1

Complementa `adlx-readonly-v1.md`. Implementação local de desenvolvimento;
**primeira sessão física interrompida por invalid_frame**, sem validação sustentada
das métricas dinâmicas. Não integrar ao dashboard antes da correção e nova validação.

## Processo e fronteira

`scripts/adlx-native-session.py` → `monitoring/adlx_bridge.py` → stdio herdado privado
→ `native/adlx/bridge.cpp` → runtime ADLX oficial. Retorno pelo mesmo canal ao
AdlxProvider, Collector e cache existentes. Nenhuma comunicação com agente HTTPS,
renderer, Named Pipe operacional ou rede. Não há servidor/endereço público.

A fábrica real aceita somente `.cache/adlx-build/bridge.exe`, sem argumentos,
com hash do executável, fonte e revisão SDK conferidos no manifesto de build.
Popen usa shell=False, close_fds=True e CREATE_NO_WINDOW; o processo nativo exige
stdin/stdout do tipo pipe antes de abrir ADLX. Ele recusa execução elevada.

Os handles são herdados pelo processo filho próprio; não há endpoint nomeado que
possa ser registrado/substituído por outro cliente. O PID da mensagem ready precisa
corresponder ao filho criado. Isso não é autenticação criptográfica contra outros
processos sob a mesma conta que possam depurar/duplicar handles ou modificar o repo.
O manifesto local e código no perfil do usuário também não constituem isolamento
contra o proprietário da própria conta. O worker roda sem elevação.

## Runtime

- GetSystemDirectoryW determina o único caminho permitido: amdadlx64.dll de System32.
- Handle do arquivo com FILE_SHARE_READ permanece aberto durante a sessão, sem
  compartilhamento de escrita/exclusão. Caminho final normalizado deve coincidir.
- PE AMD64 e SHA-256 fixado da DLL 1.4.0.121 antes da carga.
- WinVerifyTrust, inclusive assinatura por catálogo com hash de membro e contexto
  SHA-256, usando o catálogo registrado pelo Windows; não há catálogo fornecido pelo cliente.
- Sem UI, sem relaxar revogação, usando material de confiança em cache. Falta de
  confiança verificável recusa a carga; não há fallback que aceite assinatura inválida.
- LoadLibraryExW por caminho absoluto com busca restrita ao diretório da DLL e System32.
  Caminho do módulo carregado conferido novamente. Dependências estáticas restritas
  a System32 por /DEPENDENTLOADFLAG:0x800; CRT compilada com /MT.
- Fonte do SDK fixada em 66557d410ce4c463f5f7106597d94f53dd84bc82; helper upstream
  preservado e não linkado. Nenhum binding binário ou DLL baixada.

O pin do hash recusa atualizações de runtime até nova revisão; não atualizar driver
ou substituir DLL para contornar o pin. A DLL aqui usa assinatura por catálogo
Microsoft Windows Hardware Compatibility Publisher, e não assinatura embutida AMD.

## APIs utilizadas

GetProcAddress somente para ADLXInitialize, ADLXTerminate e ADLXQueryVersion.
GetGPUs, VendorId, Name, Type, TotalVRAM, GetPerformanceMonitoringServices,
GetSupportedGPUMetrics, os sete IsSupported correspondentes, GetSamplingInterval,
GetGPUMetricsHistory e getters das sete métricas. Seleção de exatamente uma GPU AMD
discreta RX 6750 XT; não assumir índice zero.

StartPerformanceMetricsTracking/StopPerformanceMetricsTracking balanceiam a referência
da própria sessão. Não mudam clocks, limites ou curvas. Nenhum SetSamplingInterval,
SetMaxPerformanceMetricsHistorySize, ClearPerformanceMetricsHistory, tuning, FPS,
API genérica ou execução de aplicativos. Listas/frames/interfaces são liberados antes
de ADLXTerminate. Não há loop de reinicialização da biblioteca.

## Protocolo e limites

Comandos de entrada: exclusivamente `latest\n` e `stop\n`, no máximo 32 caracteres.
Não são JSON arbitrário, caminhos, argumentos, expressões ou comandos do sistema.
Saída: JSON por linha, v=1, eventos phase, ready, frame, warming_up, error e stopped.
Até 16.384 bytes por linha; queue Python limitada a oito mensagens. Mensagens inválidas,
NaN, duplicação de chave, tipos inesperados, identidade ou proveniência incorreta
falham de forma fechada. Mock tem binário separado e simulated=true; nunca é aceito
como medição real.

Worker limita requisições a uma por segundo e 45 leituras; controlador usa 2 s.
Lista retornada de métricas limitada a oito frames. Histórico de cache limitado aos
limites existentes. Buffers, diagnósticos e linhas limitados. Verificação de RSS acima
de 512 MiB pede encerramento normal; isso não é um hard limit de alocação do driver.
Recursos internos da DLL não são controlados/preemptados pelo Python.

Lifetime cooperativo do loop nativo: 82 s; sessão planejada: 70 s incluindo bootstrap.
Bootstrap até 10 s, resposta até 2 s, pedido local de parada com espera até 5 s.
Nenhum kill/terminate, restart ou retry de sessão. Chamada nativa bloqueada pode
ultrapassar prazo; nesse caso registrar timeout/residual e pedir decisão humana.
O limite de 90 s não é garantido por encerramento forçado de uma DLL travada.

## Tempo e validade — pendência da primeira sessão

Frame nativo contém timestamp_ms do ADLX, age_seconds e clock_source. A implementação
compara o timestamp com uptime, Unix ms e Windows epoch ms, exigindo correspondência
única numa janela de 5 s. Se nenhuma for demonstrada, age fica null e o adapter recusa
o frame. Não cria conversão Unix presumida ou renova uma amostra sem validar sua idade.
O provedor também exige idade até 1,5 s e avanço do timestamp; cache deriva stale.

Os mocks cobrem clocks conhecidos e recusa de idade null. **Isso não prova que o
timestamp desta versão do ADLX usa um desses domínios.** Na sessão real apareceu
invalid_frame sem preservação do frame rejeitado; a causa exata ainda não está provada.
A próxima etapa deve acrescentar diagnóstico temporal sanitizado e casos realistas
de buffer inicial, sem ampliar tolerâncias nem fabricar valores.

collected_at nas métricas é o UTC da leitura local, não uma conversão declarada do
timestamp SDK. MB de VRAM é mantido nativo, sem conversão presumida para GiB.
Falha de leitura não transforma disponibilidade em suporte negativo ou valor zero.

## Encerramento e isolamento do teste

Collector pede stop; adapter envia exclusivamente stop ao próprio worker. Worker para
seu tracking, libera interfaces, chama ADLXTerminate e FreeLibrary e retorna código
distinto se cleanup falhar. Encerramento do filho e leitor Python é verificado.
Não existe comando para encerrar o agente HTTPS nem alteração em seu mecanismo legado.

O runner exige `--execute-once`, pré-verificação recente, recibos de testes correspondentes
ao código, banco íntegro/zero grants e marcador de tentativa criado com modo exclusivo.
Uma tentativa consumida não é apagada para repetir. Futuro teste precisa autorização
nova e pasta de evidências separada. Nenhum autostart, serviço, tarefa ou instalação.

O perfil GPU não é publicado no Named Pipe v1 da dev.5. O consumidor básico mantém
allowlist e unidades existentes; a futura UI exige negociação/revisão explícita.
