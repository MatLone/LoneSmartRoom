# Primeira integração física ADLX — 25/10/2026

**Resultado parcial: carga, inicialização e descoberta funcionaram; as métricas
dinâmicas não foram validadas.** A única tentativa foi interrompida na primeira
leitura por `invalid_frame`, sem repetição. Nenhuma integração ou atualização do
Electron/Android ocorreu.

## Implementação concluída

- Fontes oficiais ADLX V1.4 incorporados, autorizados pelo usuário, fixados na revisão
  `66557d410ce4c463f5f7106597d94f53dd84bc82`, com URLs, hashes e licença integral.
- Ponte C++ x64 própria, somente leitura, separada de Electron, agente e Python.
  Caminho System32, arquitetura, hash e assinatura do runtime conferidos antes da carga.
- Suporte a assinatura por catálogo, efetivamente usada por esta DLL, conforme
  [WINTRUST_CATALOG_INFO, Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_catalog_info).
- Helper upstream preservado para referência, não compilado/linkado: seu loader usa
  o nome da DLL. Nenhum binário SDK ou runtime foi baixado.
- Adapter Python, stdio privado limitado, contrato GPU opcional, Collector/cache
  existentes, recursos por processo, encerramento normal e marcador de tentativa única.
- MSVC 14.29.30133 x64 e Windows SDK 10.0.19041.0 existentes; compilação /MT, /W4 /WX,
  DEP/ASLR e busca de dependências System32. Não instalaram/repararam componentes.

Detalhamento: `contracts/adlx-native-worker-v1.md`. Código não conectado ao Named Pipe,
preload, dashboard, widget ou agente HTTPS. A aplicação Windows instalada segue dev.5.

## Pré-verificação

Antes da carga: testes correspondentes aos fontes, binários compilados e hashes
conferidos; verificação nativa somente do arquivo também aprovada. Não havia Electron,
worker de GPU, coletor ou intermediário de desenvolvimento residual. A identidade
do supervisor 400 e worker 8680 foi conferida por imagem, usuário, argumentos,
parentesco e criação. Listener único 8776; GETs autenticados 200, pin/hostname validados;
zero grants e banco íntegro. Perfis/instalação/backups idênticos aos inventários anteriores.

Runtime: `C:\Windows\System32\amdadlx64.dll`, x64, versão de arquivo 1.4.0.121,
SHA-256 `992f6db497a3c8af8d26e578c7b7fce90ed67e506d7790cc3221e4a01b67852a`,
assinatura por catálogo válida, signatário Microsoft Windows Hardware Compatibility
Publisher. Não é necessário nem correto exigir assinatura embutida AMD para esse arquivo.

## Tentativa física única

Início **14:20:10,915, America/Sao_Paulo** (17:20:10,915 UTC). Planejados 70 s, limite
autorizado 90 s; duração efetiva **0,628135 s**, incluindo inicialização e encerramento.
O erro abortou a sessão antes da segunda leitura. Não houve jogo, benchmark, carga
artificial, nova sessão ou reinicialização automática.

| Etapa | Evidência |
|---|---|
| Arquivo verificado | phase runtime_verified |
| DLL carregada | phase adlx_loaded |
| ADLX inicializado | phase adlx_initialized |
| GPU identificada | AMD Radeon RX 6750 XT, vendor 0x1002, discreta |
| Versão informada pelo SDK | 1.4 |
| Intervalo interno informado | 1.000 ms; não foi alterado |
| Primeira consulta dinâmica | Resposta rejeitada pelo adapter: invalid_frame |
| Parada | shutdownClean=true, bridgeReturnCode=0, sem force/restart |

A versão do pacote Adrenalin/driver gráfico não foi consultada. Não confundir versão
do SDK ou de amdadlx64.dll com versão desse pacote.

## Suporte descoberto e valores válidos

As sete consultas IsSupported foram bem-sucedidas e retornaram true. Isso confirma
suporte **declarado pelo SDK/driver**, não a validade de valores rejeitados. A AMD
prevê essa [descoberta por indicador](https://gpuopen.com/manuals/adlx/adlx-sdk-references/adlx-interfaces/performance-monitoring/iadlxgpumetricssupport/).

| Identificador | Unidade | Suporte declarado | Leitura aceita |
|---|---|---|---|
| gpu.adlx.utilization | % | Sim | null / error |
| gpu.adlx.temperature | °C | Sim | null / error |
| gpu.adlx.hotspot_temperature | °C | Sim | null / error |
| gpu.adlx.vram_used_mb | MB nativos | Sim | null / error |
| gpu.adlx.vram_total_mb | MB nativos | TotalVRAM retornou sucesso | **12.272 MB** |
| gpu.adlx.core_clock | MHz | Sim | null / error |
| gpu.adlx.power | W | Sim | null / error |
| gpu.adlx.fan_rpm | RPM | Sim | null / error |

Origem: amd.adlx. Horário de coleta local atribuído pelo Collector à capacidade:
`2026-10-25T17:20:11.412Z` (não é conversão de timestamp ADLX). Uma amostra de capacidade, portanto mínimo/média/máximo
numericamente 12.272 MB, n=1. Não foi convertido para GiB nem fixado em 12 GB nominais.
Todas as estatísticas dinâmicas têm n=0, min/média/max null. Nenhum zero de fixture
foi aproveitado como medição do computador. Nenhum sensor foi declarado incompatível;
os valores ficaram indisponíveis por rejeição do frame.

Não há intervalo efetivo de atualização mensurável, pois só ocorreu uma consulta.
Os 2 s configurados no coletor e 1 s informado pelo SDK não são uma frequência
fisicamente demonstrada nesta sessão. Cache terminou com 16 registros, incluindo os
oito registros iniciais de aquecimento e oito publicados; não são 16 medições válidas.

## Desempenho observado — somente startup, não regime contínuo

| Componente | CPU contabilizada na janela | RSS pontual |
|---|---:|---:|
| Ponte PID 21448 | 5,3896% da CPU total, normalizados por 12 processadores lógicos | 25,0195 MiB |
| Coletor Python PID 18248 | Incremento de CPU contabilizado 0 s; não comprova custo zero | 25,6641 MiB |
| Soma | 5,3896% nesta janela curta | 50,6836 MiB |

Método: GetProcessTimes e K32GetProcessMemoryInfo nos próprios processos. Ponte:
0,40625 CPU-s / 0,628135 wall-s / 12 × 100. Coletor: CPU final menos baseline do próprio
processo. Uma amostra de RSS, em aproximadamente +0,526 s; páginas compartilhadas
podem ser contadas duas vezes na soma. Não há amostras suficientes para uma série
de CPU intervalar, memória estável, picos sustentados ou comparação com metas.
O custo de inicialização domina essa medição; não se extrapola 5,39% para uso contínuo.
Processos/serviços do driver fora da ponte não foram incluídos no custo medido.

## Falha: fatos, hipótese e lacuna de diagnóstico

**Confirmado:** o adapter recebeu uma mensagem JSON mas a recusou como invalid_frame;
nenhum domínio de relógio foi aceito em diagnostics.clock_sources. O worker chegou a
inicializar ADLX/selecionar GPU/descobrir capacidades e terminou com código zero após
pedido normal. Não houve evidência de travamento desse worker; não se induziu crash
ou habilitou dump/telemetria adicional.

**Hipótese de confiança moderada:** a validação de timestamp/idade/domínio pode ter
recusado uma amostra inicial ou um epoch SDK diferente dos clocks previstos. O código
recusa age_seconds=null ou clock_source desconhecido, além de verificar formato,
tipos e conjunto de campos. Ainda é possível outra inconsistência do frame.

**Inconclusivo:** timestamp bruto e mensagem rejeitada não foram preservados.
sdk_frame=null significa que a mensagem não passou pela validação; não revela o
valor bruto. Logo não é possível afirmar qual campo falhou ou que o driver entregou
dados inválidos. Não inventar timestamp, reconstruir números ausentes ou atribuir
isso a incompatibilidade AMD, TLS, Crashpad ou ao agente.

Os mocks cobriam recusa de idade null e clocks conhecidos, mas não provaram o epoch
ou comportamento do primeiro frame desta versão real do ADLX. Essa lacuna deve ser
resolvida antes de aceitar dados dinâmicos. O fechamento de segurança evitou publicar
uma leitura que não conseguia validar.

## Testes automatizados e builds

| Suíte | Resultado final |
|---|---:|
| Núcleo ADLX com fixtures | 28 testes |
| Ponte e protocolo, somente binário mock separado | 25 testes; 20 processos mock, zero residuais |
| Sessão/recursos/encerramento com relógio sintético | 10 testes |
| Monitoramento básico, cache, contratos e regressões | 133 testes |
| IPC/lifecycle com substitutos | 28 testes |
| Políticas/janela/renderer/distribuição Node | 296 verificações |
| Recuperação/stale/manutenção Node | 23 verificações |
| Política interna C++ incluída no teste mock | 19 asserts |

**224 testes Python + 319 verificações Node aprovados**, sem falha/skip nos recibos
finais. Os 19 asserts C++ estão dentro da suíte da ponte, não são testes físicos.
Foram corrigidas asserções dos fixtures e a inspeção do comando auditado do Windows
durante a criação da suíte; os logs intermediários permanecem no cache. A falha física
não foi ocultada pelos resultados dos mocks e permanece reprovando as leituras dinâmicas.

Builds x64 preparados: bridge.exe, bridge-mock.exe e bridge-verify.exe, somente no
cache de desenvolvimento, sem empacotamento ou instalação. Hash do bridge.exe usado:
`dd3c72bbac7f9a66ed2ec6694db443dd99f159261b73885d1903288cc2138c8e`.
Manifestos de build e fontes correspondentes em evidence/.

## Estado final e preservação

Ponte 21448 e coletor 18248 encerrados normalmente. Nenhum monitor, bridge de teste
ou Electron residual na inspeção final. Sem kill, segunda inicialização ou retry.
ADLX tracking/interfaces/Terminate/FreeLibrary concluíram pelo caminho normal, worker
retornou zero. O marcador da tentativa e todas as evidências permanecem preservados.

Agente original: supervisor 400 e worker 8680, identidade/usuário/criação/argumentos
e parentesco correspondentes à sessão original. Listener único 8776; status e apps
autenticados retornaram 200 por TLS 1.3 com hostname/pin validados; zero grants e zero
comandos pendentes no banco. Samsung não foi acessado nesta etapa.

Comparação final: instalação 109 arquivos, perfil 77, backups dev.3 341, dev.4 75 e
dev.5 156, todos idênticos por SHA-256; contagens incluem metadados dos backups.
Mais 86 arquivos operacionais protegidos sem diferenças. DLL AMD sem alteração;
banco íntegro, identidades/segredos cifrados/schema/revogações preservados. HKCU Run
e regras de firewall sem mudança de hash. Nenhum APK, Electron instalado, certificado,
grant, driver, serviço ou configuração GPU foi atualizado. Nenhuma API setter foi chamada.

## Próximo procedimento proposto — requer nova autorização

**Não integrar GPU ao dashboard/widget ainda.** Proposta de menor risco:

1. Acrescentar, isoladamente, diagnóstico sanitizado e limitado da rejeição: nomes/tipos
   dos campos permitidos, timestamp bruto SDK, relógios de comparação e motivo específico.
   Não gravar memória, caminhos privados, identificadores extras ou payload genérico.
2. Acrescentar mocks de timestamp inicial zero, epoch relativo/desconhecido, frame
   anterior ao aquecimento e idade nula. Preservar fail-closed, limites e ausência de
   valores falsos; não aceitar qualquer timestamp só para passar na coleta.
3. Avaliar a referência de tempo/aquecimento conforme SDK. Não implementar conversão
   ou relaxamento de tolerância sem comprovação. Nenhuma alteração desse tipo foi feita
   depois da tentativa física.
4. Com testes correspondentes aprovados e autorização física específica, realizar uma
   nova sessão única, com novo diretório/ID de evidências. Não apagar o marcador atual,
   não reinicializar automaticamente nem repetir a tentativa já consumida.
5. Só após amostras dinâmicas válidas e estabilidade, solicitar integração ao Electron
   de desenvolvimento e negociação do perfil de métricas; manter instalação dev.5 intacta.

Commits de implementação: `05e471c` (SDK) e `ac56a30` (ponte, adapter, sessão e mocks).
Os checkpoints ce1ee6c, 959d3db e 7975c0d permanecem ancestrais da branch.
Reversão proposta, não executada: revisar árvore e `git revert ac56a30 05e471c`, com
regressões correspondentes. Não restaurar banco/perfis ou reinstalar o aplicativo.
Nenhum processo GPU continua ativo; artefatos de cache não iniciam automaticamente.
Preservar documentação e recibos mesmo se o código for revertido.
