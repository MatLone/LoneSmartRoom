# ADLX nativo — pré-verificação e condição de parada — 25/10/2026

Base preservada: `ce1ee6c`, `959d3db` e `7975c0d`, na branch
`feature/ui-migration-preview`. Nenhuma alteração funcional ou de instalação.

## Resultado desta etapa

**A ponte nativa e a sessão física ainda não foram executadas.** A verificação
localizou uma toolchain existente capaz de compilar/linkar um programa mínimo x64,
mas não localizou os headers/helper ADLX nos diretórios verificados. A autorização
do usuário exige aprovação específica antes de instalar SDK ou dependência adicional.
Foi solicitada autorização para incorporar somente fontes oficiais ADLX V1.4,
com licença, revisão e hashes, sem instalador, driver ou instalação global. Enquanto
essa resposta estiver pendente, não obter os arquivos para compilação, não carregar
ADLX e não consumir a única sessão física autorizada.

Essa condição de parada não é falha de coleta nem teste físico reprovado: nenhuma
tentativa de inicializar ADLX ocorreu. Os requisitos nativos permanecem pendentes.

## Ferramentas encontradas sem instalar ou reparar

| Item | Resultado |
|---|---|
| MSVC x64 | `C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe` |
| Windows SDK existente | 10.0.19041.0, headers e bibliotecas x64 presentes |
| Compilação de verificação | Programa mínimo com Windows.h e static_assert de 64 bits compilou e linkou com sucesso |
| Artefato de verificação | PE x64 `0x8664`; sem código ADLX, sensores ou rede; não executado |
| Alterações de ambiente | INCLUDE/LIB somente no processo de compilação; nada persistido no Windows |
| Instalações/reparos | Nenhum |

`vswhere -all` descreve a instalação Build Tools 2019 como incompleta e não
launchable, com operação anterior cancelada. Isso **não impediu a compilação mínima**.
Não foi executado reparo, instalador, atualização ou script de configuração global.
Esse teste não comprova, por si, que uma futura ponte ADLX completa compilará.

Os comandos de compilador não estavam no PATH inicial. A busca direcionada encontrou
os arquivos acima; portanto não é correto concluir que falta compilador neste PC.
Os fontes mínimos e resultados temporários permanecem apenas em cache ignorado.

## Dependência ainda não incorporada

Não foram encontrados `ADLX.h`, `ADLXHelper.h` ou `IPerformanceMonitoring.h` nas
buscas direcionadas do repositório/cache, Documentos, Downloads, diretórios AMD e
toolchain examinados. Não é afirmação de inexistência em todos os discos.

A existência do runtime `amdadlx64.dll` não fornece os headers de desenvolvimento.
O header oficial declara a ABI e depende de outros headers; sua leitura por navegação
não instala ou incorpora o SDK ao projeto. Não foram copiadas declarações de vtable
por aproximação. Ver [ADLX.h oficial V1.4](https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/ADLX/V1.4/SDK/Include/ADLX.h)
e [release oficial V1.4 / 66557d4](https://github.com/GPUOpen-LibrariesAndSDKs/ADLX/releases/tag/V1.4).

Proposta concreta sujeita à resposta:

1. Obter somente fontes oficiais necessários e licença, fixando revisão completa e
   SHA-256 em manifesto local. Auditar dependências transitivas dos headers/helper.
2. Armazená-los como dependência de código-fonte dentro do repositório, sem instalador,
   cópia para System32, atualização AMD, runtime pip/npm ou modificação global.
3. Usar MSVC e Windows SDK já presentes. Se faltarem componentes adicionais, parar
   novamente antes de instalar qualquer um.
4. Compilar uma ponte x64 de interface restrita somente leitura, separada de Electron
   e agente HTTPS, e testar com substitutos antes de qualquer carga ADLX real.
5. Só com todos os gates aprovados, executar a única sessão GPU autorizada de até 90 s,
   aproximadamente 2 s por atualização, sem jogos ou carga artificial. O plano detalhado
   continua em `docs/adlx-preparation-2026-10-25/README.md`.

## Inspeção do runtime AMD — arquivo, sem carga

| Verificação | Resultado |
|---|---|
| Caminho | `C:\Windows\System32\amdadlx64.dll` |
| Arquitetura PE | x64 `0x8664` |
| SHA-256 | `992f6db497a3c8af8d26e578c7b7fce90ed67e506d7790cc3221e4a01b67852a` |
| Versão previamente inspecionada | 1.4.0.121; arquivo permanece sem alteração |
| Authenticode | Valid |
| Signatário retornado pelo Windows | Microsoft Windows Hardware Compatibility Publisher |
| LoadLibrary/ADLXInitialize | Não chamados |
| GPU/driver identificados via ADLX | Não consultados |
| Capacidades e valores reais GPU | Não consultados; nenhum valor fabricado |

Assinatura válida e arquitetura correta são pré-condições, não prova de inicialização
do SDK ou suporte dos sensores. A futura ponte precisa repetir as verificações antes
da carga e recusar caminhos externos, substituições e execução elevada.

## Regressões executadas novamente

- 28 testes do núcleo ADLX com adapter simulado, sem DLL.
- 133 testes básicos, cache, contratos e regressões com substitutos.
- 28 testes IPC/lifecycle com substitutos.
- 296 verificações Node de Electron/renderer/janela/políticas/distribuição.
- 23 verificações adicionais de recuperação, stale e janela com mocks.

**189 testes Python + 319 verificações Node aprovados, sem skips ou falhas.**
São regressões da implementação atual, não os futuros testes da ponte nativa.
Inicialização nativa, falha de carga, erros de driver, timeouts, limites do novo canal
e liberação ADLX ainda precisarão ser exercitados com substitutos quando a ponte
existir. Não houve coleta física, medição de desempenho GPU ou novo empacotamento.

## Preservação final

Verificado em leitura às 12:14 UTC (09:14 local): supervisor PID 400, worker PID 8680,
mesmos executáveis, argumentos, criação, usuário e parentesco da sessão original.
Listener único 8776 pertencente ao worker. GET `/v2/status` e `/v2/apps` retornaram
200, TLS 1.3 com hostname/pin validados e lista autorizada vazia. Zero grants globais
no banco e nenhum comando pendente; nenhuma credencial foi descriptografada.

Instalação Windows (109 arquivos), perfil de produção (77), backups dev.3 (341),
dev.4 (75) e dev.5 (156), incluindo metadados, idênticos por SHA-256 aos inventários
anteriores. Mais 86 arquivos operacionais protegidos sem diferenças. Banco íntegro;
identidades, segredos cifrados, schema e revogações preservados. HKCU Run e firewall
sem mudança de hash. Nenhum coletor ou Electron do aplicativo encontrado em execução.

Não foram alterados Android, Electron instalado, agente, certificados, HMAC, grants,
serviços, driver ou rede. Não foram executados Steam, CS2, WoL ou energia. TLS,
Crashpad e encerramento gracioso permanecem separados. Evidências públicas sanitizadas
em `evidence/`; inventários privados ficam em cache ignorado, fora do Git.

## Reversão e retomada

Esta etapa altera somente documentação/evidências. Não existe ponte GPU ativa a
encerrar nem componente instalado a remover. Reversão documental, se necessária:
`git revert` do commit desta etapa, após revisar a árvore; não restaurar banco/perfil,
não usar reset e não tocar no agente. Os artefatos de compilação mínima em cache não
participam do runtime e não foram registrados em inicialização.

**Próximo gate: resposta explícita sobre os fontes oficiais ADLX.** Não solicitar
integração GPU ao dashboard ainda: a ponte e a sessão física precisam ser concluídas
primeiro. A autorização de uma sessão física não foi consumida ou ampliada.
