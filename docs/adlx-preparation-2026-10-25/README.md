# Preparação ADLX — RX 6750 XT — 25/10/2026

Checkpoint preservado: `c96555d`. Fase limitada a pesquisa, código isolado e mocks.
**Nenhuma DLL ADLX foi carregada, GPU consultada, sessão Electron aberta,
dependência instalada ou pacote reconstruído.** A instalação Windows dev.5 permanece
com o monitoramento básico aprovado. As observações dessa versão estão em
[relatório separado](../windows-dev5-observations-2026-10-25/README.md).

## Compatibilidade esperada e limites da auditoria

A RX 6750 XT com driver AMD no Windows 11 é candidata à integração. Foi encontrado
`C:\Windows\System32\amdadlx64.dll`, versão **1.4.0.121**, 5.221.904 bytes,
assinatura Authenticode válida. SHA-256:
`992f6db497a3c8af8d26e578c7b7fce90ed67e506d7790cc3221e4a01b67852a`.
Esta inspeção leu metadados/arquivo; não demonstra inicialização bem-sucedida do SDK
nem compatibilidade de um sensor particular. Não foi localizada uma matriz oficial
que garanta todos os indicadores nessa placa/driver.

O ADLX oferece descoberta individual de suporte. As decisões serão tomadas a partir
de resultados reais desses métodos, não do nome comercial. Ver
[IADLXGPUMetricsSupport, AMD](https://gpuopen.com/manuals/adlx/adlx-sdk-references/adlx-interfaces/performance-monitoring/iadlxgpumetricssupport/).

| Indicador preparado | Condição para ficar disponível | Situação física nesta fase |
|---|---|---|
| Utilização (%) | IsSupportedGPUUsage e leitura válida | Não consultado |
| Temperatura GPU (°C) | IsSupportedGPUTemperature e leitura válida | Não consultado |
| Hotspot (°C) | IsSupportedGPUHotspotTemperature e leitura válida | Não consultado |
| VRAM utilizada (MB nativos) | IsSupportedGPUVRAM e leitura válida | Não consultado |
| VRAM total (MB nativos) | Sucesso de IADLXGPU::TotalVRAM, valor positivo | Não consultado; não fixado em 12 GB |
| Clock do núcleo (MHz) | IsSupportedGPUClockSpeed e leitura válida | Não consultado |
| Potência GPU (W) | IsSupportedGPUPower e leitura válida | Não consultado; não equivale a potência total da placa |
| Ventoinha (RPM) | IsSupportedGPUFanSpeed e leitura válida | Não consultado; zero válido exige suporte confirmado |

Portanto, **nenhuma métrica foi confirmada como disponível ou incompatível**. Hotspot,
potência e RPM continuam opcionais. Falha na descoberta difere de suporte negativo;
ambas mantêm valor null, com estado correspondente. A especificação dos getters consta
em [IADLXGPUMetrics, AMD](https://gpuopen.com/manuals/adlx/adlx-sdk-references/adlx-interfaces/performance-monitoring/iadlxgpumetrics/).

## Código efetivamente preparado

- `monitoring/adlx_provider.py`: núcleo Python de provedor, adapter somente leitura
  injetado, seleção explícita de GPU AMD discreta, descoberta antes da leitura,
  validação de canais/valores/idade/timestamp e liberação idempotente.
- `monitoring/contracts.py`: unidades aditivas `megahertz`, `watts` e `megabytes`.
  Schema permanece v1; catálogos existentes de 22 slots/21 métricas básicas preservados.
- `contracts/adlx-readonly-v1.md`: fronteira nativa, unidades, timestamps, cadências,
  falhas, lifecycle e limites da compatibilidade.
- `tests/monitoring/test_adlx_provider.py` e `scripts/test-adlx-isolated.py`: 28 testes
  com fixtures explicitamente simuladas. O runner bloqueia novas cargas nativas,
  processos, sockets e Registro por audit hook.

Fluxo preparado: **adapter mock → provedor ADLX → Collector existente → cache**.
Não há wrapper nativo, loader de DLL ou integração GPU ao Named Pipe, preload,
Electron, APK ou agente HTTPS. Não se deve tratar o provedor como operacional.

O perfil opcional usa IDs `gpu.adlx.*`; não altera a semântica em bytes dos antigos
`gpu.vram_*`. MB nativo é conservado sem conversão presumida para GiB. Timestamp
SDK bruto é diagnóstico; `collected_at` continua sendo o horário UTC local da coleta.
A calibração da idade/epoch SDK pertence à futura ponte nativa e ainda precisa de teste.

O consumidor dev.5 possui allowlist estrita de métricas básicas. **Não aceita o novo
snapshot GPU.** A projeção básica adicionada é apenas helper interno testado, sem
ligação ao transporte. Uma futura integração exige negociação explícita de perfil
ou revisão do transporte/consumidor, sem enviar unidades novas ao cliente legado.

Cadências reaproveitadas: utilização/VRAM/clock 1 s, temperaturas/potência/RPM 2 s,
capacidade 60 s; redução inativa já prevista pelo Collector. Não foi acrescentado
timer próprio. Para a primeira sessão GPU recomenda-se 2 s nas leituras dinâmicas.
Falha inicial não gera loop de bootstrap; perda da GPU invalida também sua capacidade
e libera o adapter. Leituras atrasadas/repetidas não são renovadas como atuais.

## Dependências e permissões — aprovação ainda necessária

O núcleo e os testes usam somente a biblioteca padrão já existente do Python.
Nenhum pacote pip/npm foi instalado. O caminho nativo exige uma ponte C/C++ x64
pequena ou binding oficial previamente auditado. Não há implementação dessa ponte
nesta entrega. `cl.exe` e `cmake.exe` não foram encontrados no PATH consultado;
isso não prova ausência de toda toolchain no computador.

Proposta: avaliar headers/helper AMD da revisão compatível **V1.4 / 66557d4** com
o runtime presente, antes de incorporá-los ou compilar. O repositório oficial já
possui versões posteriores; escolher a mais recente automaticamente não comprova
compatibilidade com a DLL 1.4. Ver [release V1.4](https://github.com/GPUOpen-LibrariesAndSDKs/ADLX/releases/tag/V1.4)
e [releases oficiais](https://github.com/GPUOpen-LibrariesAndSDKs/ADLX/releases).

Não usar ctypes para adivinhar vtables C++, bindings binários de terceiros ou DLL
obtida fora do driver existente. A ponte deverá fixar caminho absoluto confiável,
validar versão/assinatura/hash, expor apenas getters definidos e gerenciar referências.
Não terá exports de tuning nem acesso genérico a métodos, parâmetros ou executáveis.
Não exigirá driver adicional, administrador, serviço, Registry ou autostart.
Se a integração não funcionar sem essas condições, parar e apresentar alternativas.

Para coleta contínua, avaliar histórico recente limitado em vez de aquisição completa
por indicador, conforme [GetGPUMetricsHistory, AMD](https://gpuopen.com/manuals/adlx/adlx-sdk-references/adlx-interfaces/performance-monitoring/iadlxperformancemonitoringservices/getgpumetricshistory/).
Balancear somente o rastreamento da própria sessão; não mudar intervalo/configuração
global nem obter interfaces de controle da GPU. Uma chamada nativa travada não pode
ser interrompida com segurança pelo núcleo Python. Recomenda-se primeiro worker GPU
separado dos sensores básicos; sobrecarga e comportamento de liberação ainda precisam
ser medidos. Nenhuma estimativa de CPU/RAM ADLX é apresentada como medição real.

## Validação executada

| Suíte | Resultado | Escopo |
|---|---:|---|
| Provedor ADLX injetado | 28 testes aprovados | Sem SDK ou sensores |
| Regressões básicas/preservação/WoL/launchers | 133 testes aprovados | Substitutos e mocks; sem abrir aplicativos |
| IPC e lifecycle | 28 testes aprovados | Sem Named Pipe operacional ou coleta real |
| Electron/políticas/renderer/distribuição | 296 verificações aprovadas | Node, sem Electron nativo |
| Manutenção: recuperação IPC/stale/janela/DOM | 23 verificações aprovadas | Substitutos, sem janela real |

Total: **189 testes Python + 319 verificações Node**, sem falhas ou skips nas suítes
registradas. Incluem zero legítimo, NaN/fora de faixa, ausência, erro/recuperação,
capacidade incoerente, GPU incorreta, repetição/idade, cadências, cache, encerramento
e recusa de campos GPU pelo pipeline básico. Evidências sanitizadas em `evidence/`.
Isso não valida ABI nativa, sensores, compatibilidade com jogos ou desempenho físico.

## Próxima fase proposta — depende de autorização específica

1. Autorizar separadamente obtenção/auditoria dos headers/helper e preparação da ponte
   somente leitura. Não instalar toolchain/dependências sem nova aprovação se faltarem.
2. Testar essa ponte com substitutos e verificar exports, arquitetura x64, origem/hash,
   lifecycle, ausência de tuning, carga por caminho fixo e recusa de elevação.
3. Só com pré-condições aprovadas, realizar **uma sessão GPU isolada de até 90 s**,
   sem Electron instalado, IPC operacional, jogos, carga artificial ou alteração do driver.
4. Antes: confirmar identidade do agente HTTPS, listener único 8776, zero grants,
   integridade dos perfis/backups e ausência de processo GPU residual. Falha → não iniciar.
5. Na sessão: enumerar/selecionar RX 6750 XT, consultar capacidades uma vez, registrar
   somente métricas autorizadas, validade/idade/unidades, zeros legítimos, falhas,
   intervalos e CPU/RSS do próprio worker. Não gerar carga para obter leituras.
6. Encerrar normalmente, balancear referências, confirmar ausência de worker residual
   e preservação do agente. Timeout/falha → registrar, não matar nem repetir automaticamente.
7. Comparar VRAM com a unidade informada pelo SDK e referência local de leitura;
   não converter ou publicar no dashboard antes de resolver escala/timestamp.

Hoje essa sessão **não está pronta para execução**, pois a ponte nativa está pendente.
Não se autoriza implicitamente instalá-la através deste plano.

## Preservação e reversão

Nenhum arquivo do Electron instalado, perfil de produção, Android ou agente foi
modificado. Banco/credenciais são verificados em leitura sem descriptografia;
somente GET autenticado de status/permissões, sem novo pareamento ou grant.
TLS e encerramento gracioso continuam pendências separadas.

Verificação final às 11:59 UTC: supervisor **400** e worker **8680**, com imagem,
argumentos, criação, parentesco e usuário correspondentes à sessão original.
Listener único 8776 pertencente ao worker; GET `/v2/status` e `/v2/apps` retornaram
200 com TLS 1.3, hostname e pin validados. Lista de aplicativos autorizados vazia;
zero grants no banco e nenhum comando pendente. Não houve nova verificação física
no Samsung nesta fase.

Comparação exata dos inventários: instalação 109 arquivos, perfil 77, backups dev.3
341, dev.4 75 e dev.5 156, todos sem diferenças (contagens incluem metadados de backup).
Mais 86 arquivos operacionais protegidos sem diferenças; banco íntegro, identidades,
segredos cifrados, revogações e schema preservados. HKCU Run e regras de firewall
conferidos por hash sem mudança; nenhum coletor ou processo Electron do aplicativo
encontrado. Inventários privados permanecem fora do Git, em cache ignorado.

Após os commits, reversão de código será por `git revert` dos commits desta fase,
em ordem inversa, com revisão das dependências. Não usar reset de checkpoints,
rollback da instalação ou restauração de dados. O código GPU não está registrado
em inicialização nem no runtime operacional; não há processo GPU a parar.

Commits de implementação/testes:

- `959d3db50e53b0ba9faf8dfe4f44f0ca54dd3885`: núcleo ADLX, unidades opcionais,
  contrato e 28 testes simulados.
- `7975c0d01f9827838f8ad28fca0e2d38abb3c471`: recuperação IPC/janela/renderer
  com mocks e reanálise offline da dev.5.

Procedimento de reversão proposto, **não executado**: árvore limpa, revisão do diff,
`git revert 7975c0d 959d3db`, execução das regressões básicas/Node. Manter estes
relatórios como histórico ou reverter seu commit documental separadamente. Isso não
envolve a instalação dev.5, banco, perfis ou backups. O checkpoint `c96555d` continua
ancestral da branch, sem reset/rebase.
