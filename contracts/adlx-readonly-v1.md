# ADLX somente leitura — contrato opcional em preparação

Implementação desta fase: `monitoring/adlx_provider.py`, com adapter injetado e
testes sintéticos. **Não há loader DLL, wrapper nativo compilado ou integração à
instalação/worker operacional neste commit.** Nenhum valor dos testes é medição do PC.

## Fronteira nativa proposta — depende de aprovação

O adapter deverá oferecer exclusivamente `open`, `devices`, `capabilities`,
`total_vram`, `latest` e `close`. Não haverá método genérico de invocação,
endereços de função, comandos, caminhos externos ou API de tuning. O núcleo Python
não aceita um caminho de DLL no lugar de um adapter tipado por esse protocolo.

Proposta para a próxima fase: wrapper local x64 pequeno, usando headers/helper
AMD fixados numa revisão compatível com o runtime instalado, com exports próprios
somente leitura. O SDK e a toolchain ainda não foram incorporados. Não baixar
binários de bindings não auditados nem copiar DLLs para System32. A DLL AMD deverá
vir da instalação de driver existente, por caminho absoluto confiável e verificação
de versão/hash/assinatura. Não usar busca no diretório atual ou PATH fornecido pelo
renderer. Carregamento, compilação, dependências e teste físico exigem autorização.

O adapter deve recusar elevação, balancear inicialização/terminação e referências
somente de sua sessão, liberar frames/listas por RAII e respeitar a afinidade/thread
exigida pelo SDK. Não criar serviços, drivers, tarefas, autostart ou portas TCP.
Não obter serviços de tuning, clock, tensão, curva de ventoinhas, display ou jogos.

Para coleta contínua, usar a estratégia de histórico recente recomendada pelo SDK,
com lista limitada e seleção da amostra mais nova. Não chamar uma aquisição completa
por indicador. Consultar intervalo/default existente; não modificar configuração
de amostragem do driver/SDK nesta proposta. Caso seja necessário iniciar rastreamento
de métricas, balancear apenas sua referência e validar esse efeito antes do teste.

Uma chamada nativa bloqueada não pode ser preemptada com segurança pelo Python.
Recomenda-se primeiro worker GPU separado dos provedores básicos, para que uma
falha do SDK não bloqueie CPU/RAM/discos. O custo desse isolamento precisa ser medido
antes de decidir a composição permanente. O núcleo mockado não promete timeout
forçado de chamadas nativas: o Collector rejeita amostras que retornem fora do prazo.

## Seleção e descoberta

Enumerar GPUs; não selecionar índice zero. Exigir chave explícita de enumeração,
vendor AMD `0x1002`, GPU discreta e nome compatível com RX 6750 XT. Ausência,
duplicação/ambiguidade ou outro dispositivo falham de forma fechada. O identificador
da sessão não deve ser presumido persistente após reinicialização/hotplug.

Cada `Capability(ok, supported)` separa erro na consulta de suporte de suporte
negativo. Somente sucesso com `supported=true` autoriza leitura daquele indicador.
`TotalVRAM` não tem IsSupported correspondente: seu resultado determina disponibilidade.
Não inferir capacidade de 12 GB a partir do nome comercial.

| Métrica opcional | Descoberta | Getter | Unidade conservada |
|---|---|---|---|
| `gpu.adlx.utilization` | IsSupportedGPUUsage | GPUUsage | percent |
| `gpu.adlx.temperature` | IsSupportedGPUTemperature | GPUTemperature | celsius |
| `gpu.adlx.hotspot_temperature` | IsSupportedGPUHotspotTemperature | GPUHotspotTemperature | celsius |
| `gpu.adlx.vram_used_mb` | IsSupportedGPUVRAM | GPUVRAM | megabytes |
| `gpu.adlx.vram_total_mb` | Resultado TotalVRAM | TotalVRAM | megabytes |
| `gpu.adlx.core_clock` | IsSupportedGPUClockSpeed | GPUClockSpeed | megahertz |
| `gpu.adlx.power` | IsSupportedGPUPower | GPUPower | watts |
| `gpu.adlx.fan_rpm` | IsSupportedGPUFanSpeed | GPUFanSpeed | rpm |

`GPUPower` não é intercambiável com `GPUTotalBoardPower`. Não foi criado fallback
entre essas medidas. Zero RPM é válido somente com suporte e leitura bem-sucedida;
sensor ausente jamais se transforma em fan stop. VRAM usada maior que o total
informado é erro, não valor a ser ajustado silenciosamente.

A documentação AMD chama VRAM de **MB**. Os IDs novos preservam a unidade nativa
e não a reinterpretam automaticamente como bytes, MB decimal ou GiB. Os slots
anteriores `gpu.vram_*` em bytes não foram alterados. Uma futura conversão exige
confirmar a escala do SDK/driver e testá-la; não se inventa fator de conversão.

## Amostra, disponibilidade e tempo

O adapter devolve `Frame(device_key, sdk_timestamp_ms, age_seconds, readings)`.
Cada Reading contém estado e valor. O timestamp bruto SDK é preservado no
diagnóstico do provider. `collected_at` no contrato existente continua sendo o UTC
da coleta local; não é apresentado como conversão direta de TimeStamp do ADLX.

O SDK descreve TimeStamp como duração em ms desde o epoch do sistema. A ponte
nativa deve calibrar/validar essa referência com monotônico/UTC; não presumir Unix
epoch ou converter cegamente. `age_seconds` deve medir a idade real do frame, não
o tempo da chamada. Essa calibração ainda não foi testada fisicamente.

O núcleo rejeita frame de outra GPU, idade negativa/não finita/acima de 1,5 s,
timestamp repetido/regressivo, valor inválido e canal desconhecido. Repetir um frame
não produz uma nova leitura válida com número antigo. Ausência tem valor null e
estado unsupported/unavailable/error/permission_denied, conforme o caso. Stale é
derivado pelo cache; o provider não pode forjar esse estado.

Cadências padrão reutilizam Collector: utilização/VRAM usada/clock 1 s;
temperaturas/potência/RPM 2 s; capacidade 60 s. O gate interno impede leitura dinâmica
mais rápida que 1 s e não cria timer próprio. No futuro teste, preferir Schedule
fast/thermal de 2 s, capacidade 60 s. Frequência inativa usa os mecanismos existentes;
a instalação dev.5 ainda não propaga visibilidade para `set_active`.

Falha temporária de leitura pode recuperar no próximo ciclo com frame novo.
Falha de bootstrap não gera loop de inicialização. DeviceLost invalida também a
capacidade e libera o adapter; não redescobre/reinicia automaticamente. Encerramento
é idempotente; erro na liberação é registrado sem conteúdo de exceção ou retry forçado.

## Compatibilidade v1

SCHEMA_VERSION continua 1; campos existentes, unidades antigas, catálogo padrão
de 22 slots e catálogo básico de 21 métricas não mudam. Há três unidades aditivas
para o perfil GPU opcional. O cache e o Collector existentes são reutilizados.

**O snapshot GPU não pode ser enviado ao renderer dev.5 atual.** Ele mantém allowlist
estrita e rejeita campos GPU/unidades desconhecidas. A composição GPU não foi ligada
ao Named Pipe, preload, empacotamento ou Electron. `basic_v1_projection` é uma
fronteira futura interna, testada para conservar valores/metadados básicos; a sequência
do cache continua global e pode também contar publicações GPU.

Antes de qualquer integração permanente, negociar perfil/capacidade com o consumidor
ou revisar a versão do transporte e atualizar explicitamente a allowlist de métricas.
Não ampliar API preload, aceitar IDs/caminhos genéricos ou transmitir o catálogo novo
a clientes legados. A segurança atual permanece fechada por padrão.
