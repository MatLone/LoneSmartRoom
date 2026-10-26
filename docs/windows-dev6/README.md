# Windows 2.0.0-dev.6 — preparação dos pacotes

Base `2be0247`, checkpoint `bcafe3a` e seus ancestrais preservados. Branch
`feature/ui-migration-preview`. Nenhuma instalação, execução física do Electron
ou coleta ADLX real nesta etapa. A instalação de produção permanece dev.5.

## Frescor

A [política completa](../../contracts/monitoring-display-freshness-v1.md) separa:

| Camada | Política |
|---|---|
| Ingresso ADLX | Idade finita entre zero e **1,5 s**; rejeitar futuro, não finitos, `age_null` e timestamp sem avanço |
| Cache v1 | TTL existente de três intervalos, histórico limitado; snapshot não renova idade/horário |
| Exibição GPU dinâmica | Expira em **3 s ativa / 11 s inativa**: cadência 2/10 s mais um tick de atualização de 1 s |
| Informação GPU | Idade no ingresso + idade no cache; soma conservadora, distinta da validade no ingresso |
| Capacidade VRAM/discos | Cadência 60 s, TTL v1 de 180 s; não usar cadência dinâmica para inventário |

Os campos opcionais v1 `ingress_age_seconds` e `information_age_seconds` conservam
compatibilidade com os campos anteriores. A idade do cache começa antes da leitura,
portanto a soma pode contar parte do tempo de leitura conservadoramente. Não se
converte o epoch SDK em UTC por aproximação. O ingresso continua validado pelo
provedor, independentemente da UI.

No limite de exibição, valor null/desatualizado. Cache de 2,69 s não é anunciado
como frame SDK ainda com ≤1,5 s de idade. Metadados mostram origem, unidade, horário,
estado, cadência e idades separadas. Ao restaurar, a GPU fica **Atualizando**, sem
números antigos, até receber uma amostra em cadência ativa produzida após a
restauração. Não se esconde a transição aumentando o limite de ingresso.

`age_null` inicial continua inválido/null; o próximo frame pode recuperar no mesmo
processo. CPU/RAM/I/O mantêm aquecimento e TTL existentes. Zero válido permanece
distinto de indisponível; percentuais pequenos positivos aparecem `<0,1%`.
Ocupação, leitura/gravação e atividade PDH seguem independentes, sem fallback.

## Monitoramento e ciclo de vida

```text
APIs Windows + ADLX em processo nativo separado
  → provedores → coletor/cache Python → Named Pipe local protegido v1
  → intermediário Python → stdio privado → Electron main
  → preload restrito → dashboard / widget
```

Inclui CPU i5-12400, RAM, C:/D: (capacidade, ocupação, disponibilidade, leitura,
gravação, atividade PDH opcional) e oito campos GPU: utilização, temperatura,
hotspot, VRAM usada/total, clock, potência e RPM. Suporte é descoberto pelo SDK;
incompatibilidade/falha fica indisponível, nunca zero fictício. Não há temperatura
CPU, FPS ou controle de hardware. Nenhum provedor fictício é incluído no payload.

- Uma instância Electron e uma tentativa de host/coletor por sessão; sem respawn.
- Main verifica pin do manifesto e os **39 arquivos** do runtime, recusando extras,
  links e redirecionamentos. Caminhos/argumentos internos fixos, `shell=false`,
  CPython 3.13.3 isolado, sem Python do agente ou dependências do usuário.
- Handles retidos, SID, sessão, imagem, processo pai e ausência de elevação são
  conferidos. Modo permanente exige bundle real validado e dono Electron.
- Uma ponte por SID usa lease `FIRST_PIPE_INSTANCE` e DACL explícita. Somente esse
  handle mais stdio são herdados; a herança é revertida no pai. O lease é mantido
  pelo filho nativo até sua saída efetiva, inclusive após falha do pai.
- No modo application, a ponte substitui os antigos limites **82 s / 45 leituras**
  por EOF/stop e watchdog de **30 s sem pedidos válidos**. Desenvolvimento limitado
  conserva os limites anteriores. Linhas, filas, memória e frequência continuam
  limitadas; somente latest/stop, sem API genérica ou controle da GPU.
- Main usa um timer de 1 s ativo / 10 s oculto ou sem foco. Leituras autorizadas
  inferem demanda: CPU/RAM/I/O 1/5 s, GPU 2/10 s, capacidade 60 s. Restauração pede
  snapshot imediato sem criar outro processo/timer.
- Named Pipe mantém DACL da conta, recusa remota, validação de identidade,
  requisição 256 bytes, resposta 128 KiB, timeout 1,5 s, limite 2 pedidos/s e burst 4.
  Não há novo endpoint TCP/HTTP nem alteração do contrato de operações v1.
- IPC transitório reconecta ao mesmo worker. Falha GPU não derruba básicos/Electron.
- Sair fecha stdio, para agendamento, conclui leituras, fecha PDH/pipe, libera ADLX
  e espera os filhos antes de soltar o lease. Timeout não é sucesso e não aciona
  kill; a interface permanece disponível para decisão. Nenhum autostart Windows.

Tray, X normal, três abas, widget, redimensionamento, identidade e preferências
esquema 1 preservados. Renderer sem Node, com isolamento, sandbox, CSP sem conexões
e preload restrito. Continua sem cliente HTTPS operacional desktop.

## Testes e inspeções

- **284 testes Python**, zero falhas/erros/skips: contratos, cache, básicos,
  IPC/identidade/lifetime, ADLX/frames inválidos e regressões WoL/Steam/CS2 com mocks.
- **415 verificações Node**: janela, bandeja, instância única, persistência,
  IPC/reconexão/falhas, renderização, fronteiras de frescor e restauração simulada.
- **35 asserts C++** no mock, incluídos na suíte Python da ponte. Seus 22 processos
  substitutos encerraram sem resíduos; nenhum carregou ADLX real.
- **2.323 verificações** do payload: importação pelo Python existente com hooks que
  recusam sensores, novas DLLs, rede, Registry e subprocessos.
- **288 verificações** estáticas de NSIS/portátil; arquivos extraídos/testados sem
  execução. Mais 21 recursos ASAR, 40 arquivos do sidecar incluindo manifesto e
  sete imagens do ícone PE conferidos contra as origens.

Os dois erros iniciais nos testes foram corrigidos: temporário passou para área
gravável do workspace e a janela substituta recebeu eventos de atividade. As suítes
completas foram repetidas e passaram. Ver [resumo](evidence/test-summary.json) e
[97 hashes de fontes](evidence/source-hashes.json).

A primeira tentativa de build falhou no despacho do compilador existente
(`spawn UNKNOWN`) no sandbox. Consulta com permissão apropriada retornou v3.04;
a segunda tentativa terminou em diretório novo. Intermediários anteriores foram
preservados. Nenhuma proteção Windows foi alterada. O uninstaller foi extraído
estaticamente; a guarda de build proibiu execução de artefatos gerados.

## Artefatos locais — não executar sem autorização

Diretório:
`<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\windows\desktop-dev6-gpu-distribution-attempt2`

| Pacote | Bytes | SHA-256 |
|---|---:|---|
| `Lone-Smart-Room-2.0.0-dev.6-x64-Setup-DEV.exe` | 105741349 | `fccf8683210f24577462b1b0ef5ce100cf1373e23beac4ac5b91383dbfb0b545` |
| `Lone-Smart-Room-2.0.0-dev.6-x64-Portable-DEV.exe` | 105455223 | `c97575b9032d5c7912267d75d6d3ea8ba177a93f62545f4dbee5eed337c0b9d8` |

Hashes também em [SHA256SUMS.txt](SHA256SUMS.txt). Identidade `com.lone.smartroom`,
produto Lone Smart Room, ASAR/FileVersion `2.0.0-dev.6`; ProductVersion numérico
2.0.0.0. Payload x64; wrappers NSIS PE x86, como no fluxo anterior. Instalação
assistida por usuário, sem elevação, `runAfterFinish=false`, perfil preservado.

Ponte, Electron, NSIS e portátil estão **NotSigned**, sem Authenticode, comprovado
por tabela PE e Get-AuthenticodeSignature. Mensagem genérica de signing do builder
não é comprovação de assinatura. Não houve bypass de SmartScreen/Defender.

SDK V1.4 fixado na revisão 66557d410ce4c463f5f7106597d94f53dd84bc82. A licença
[oficial AMD](https://github.com/GPUOpen-LibrariesAndSDKs/ADLX/blob/66557d410ce4c463f5f7106597d94f53dd84bc82/ADLX%20SDK%20License%20Agreement.pdf)
foi examinada localmente: não é MIT. Ponte própria usa os headers; helper, samples,
headers e DLL do driver não são distribuídos. Licença original e avisos incluídos.
Estes pacotes são para **avaliação interna local**. Distribuição a terceiros depende
de revisão e EULA compatível com seção 3/Schedule B; um aviso sozinho não basta.

O loader continua restrito à DLL System32 x64, assinatura/catálogo e hash oficial
validado. Mudança de hash após atualização do driver resulta em recusa segura,
sem busca alternativa de DLL ou instalação de driver.

## Preservação, desempenho e limites

Conferência final de 26/10/2026 08:30 UTC: mesmo supervisor **5024**, worker **18304**,
criação/imagens/argumentos corretos; redirectors venv esperados 19996/20352. Mesmo
listener LAN único 8776, sem wildcard. TLS 1.3, certificado/hostname/pin conferidos
antes do HMAC, status/apps HTTP 200, **zero grants/comandos pendentes**. Banco
íntegro, identidades cifradas/esquema/revogações preservados. Nonces/last-seen das
consultas podem mudar; não se afirma igualdade byte a byte do banco ativo.

Instalação dev.5 (**109 arquivos**), perfil (**77**) e backups pré-dev.3 (**341**),
pré-dev.4 (**75**), pré-dev.5 (**156**) com SHA-256 antes/depois iguais. Mais **86
arquivos operacionais protegidos** sem diferenças. Run, firewall, DLL AMD, Android
e fontes do agente preservados. Nenhum processo Electron/monitoramento residual.
Nenhuma nova confirmação física no Samsung foi solicitada nesta preparação.

Sem medição física atual. Referência anterior: CPU conjunta **0,529%**, RSS somada
média **454,22 MiB**, pico **480,73 MiB**. Páginas compartilhadas podem ser contadas
mais de uma vez; não se garante consumo igual no pacote. Polling reduzido, um
timer/filho por finalidade, texto alterado só quando muda e DOM adiado quando
oculto são medidas conservadoras, sem prometer CPU inferior a 0,5%.

ACL por SID não isola processos maliciosos da mesma conta. Hashes locais não
substituem Authenticode ou impedem alteração simultânea de ASAR/payload por quem
tem escrita. SDK/kernel travado pode exceder prazos; não há kill automático nem
garantia absoluta contra órfãos em crash/queda de energia. Ciclo permanente foi
simulado por 1.000 s no coletor e mais de 82 s/45 respostas no host. A versão
empacotada ainda exige validação física de bootstrap, frescor, desempenho e saída.

PDH continua opcional, sem causa comprovada para cada lacuna histórica. TLS,
Crashpad e encerramento gracioso do agente seguem separados, sem correções aqui.
Não se executou Steam, CS2, WoL ou energia.

## Atualização e reversão propostas — não executadas

1. Obter autorização específica para NSIS; inventariar dev.5 e fechar normalmente
   pela bandeja. Conferir saída dos seus filhos, sem tocar no agente HTTPS.
2. Criar novo backup protegido da instalação/perfil, fora do Git/destino, mantendo
   os anteriores. Preservar preferências, ACLs, hashes; não copiar perfil em uso.
3. Recalcular hashes, confirmar unsigned, mesmo appId, destino
   `%LOCALAPPDATA%\Programs\Lone Smart Room` e perfil `%APPDATA%\Lone Smart Room`.
4. Executar só o NSIS assistido autorizado e não abrir ao concluir. Parar diante
   de bloqueio de segurança; não usar portátil como substituto do instalador.
5. Comparar arquivos/perfil, confirmar agente original ativo e zero grants.
   Solicitar autorização separada para primeira sessão física limitada da dev.6.
6. Para reversão futura, fechar só o aplicativo normalmente, preservar primeiro
   seu perfil atual, comparar esquema 1 e repor binários dev.5 de backup/artefato
   validado mediante autorização. Restaurar perfil apenas se necessário e com
   cópia do estado novo. Não desinstalar/limpar dados nem presumir downgrade seguro.
7. Código: `git revert` dos commits desta etapa em ordem inversa após revisão;
   sem reset destrutivo ou remoção de checkpoints, pacotes e evidências.

Backup pré-dev.5 preservado:
`<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev5-20261025T104128Z`.
Não houve necessidade de criar/restaurar backup operacional nesta preparação.

## Commits de implementação

- `7aa50c2d73271fed800b840b42bff0033ca2124d`: ciclo ADLX sob propriedade da
  aplicação, proveniência temporal aditiva e testes Python/C++.
- `b2e64d44dba22695cc6b0e78c0ea5ca4db2944a9`: política de exibição/retomada,
  integração empacotada, runtime, inspeção e testes Node da dev.6.
- Relatório, hashes e evidências sanitizadas são registrados em commit documental
  posterior. Binários, logs operacionais e inventários privados permanecem fora do Git.
