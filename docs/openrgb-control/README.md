# OpenRGB — implementação e homologação parcial

Implementação: `d0a479c`. Base preservada: `ce0dc55`. Branch: `feature/openrgb-control`. Data: 29/10/2026.

## Resultado

Serviço main, preload restrito, interface em Controles, quatro cenas editáveis, restauração, consentimento Gamer e solicitações NEX estão implementados. **O controle físico ainda não está homologado.** Não instalar esta candidata antes de resolver e validar a divergência de retorno.

A única tentativa autorizada ocorreu entre **11:38:34.957Z e 11:38:36.153Z** (1,196 s). O pedido era aplicar `#FF153F` somente à zona Chipset Accent da B660M por 8 s. O retorno divergiu imediatamente (`rgb_readback_mismatch`); por isso o intervalo de 8 s não começou. A recuperação conferiu modo e cores iguais ao estado anterior no cache do SDK. O usuário informou **“Não percebi mudança”**. Nenhuma segunda escrita de teste foi realizada. A Nollie não foi alvo.

A falha não é mascarada como sucesso. O protocolo v3 não fornece confirmação de escrita por ACK; o serviço compara o descritor retornado com o estado esperado. A leitura de retorno não é prova visual da iluminação. A tentativa não registrou quais campos divergiram, portanto não é possível atribuir causa ao driver, concorrência ou temporização. Após a falha, foi adicionado diagnóstico limitado com contagens de diferenças em identidade, modo e cores, sem dumps ou caminhos. A recuperação mantém os mesmos critérios; não há repetição automática nem relaxamento da comparação.

## Capacidades realmente consultadas

| Controladora | Zonas observadas | Condição |
|---|---|---|
| Nollie 16_OS2_1 | Channel 1–16 | Todos reportam 0 LEDs; escrita bloqueada. O LSR não redimensiona nem configura canais. |
| B660M AORUS PRO DDR4 | LED_C1, Chipset Accent, LED_C2 | 1 LED por zona, modo Direct e brilho nativo reportados. Escrita física pendente de homologação. |
| B660M AORUS PRO DDR4 | D_LED1, D_LED2 | 0 LEDs; indisponíveis para escrita. |

Servidor anuncia protocolo 6, cliente negocia protocolo 3. Direct, Static, Breathing, Flashing, Color Cycle, Double Flash, Random, Wave 2 e Wave 4 são capacidades reportadas, **não efeitos fisicamente homologados**. Brilho é convertido para o intervalo nativo do modo; não é simulado pela multiplicação de RGB. Modos com gravação automática são bloqueados. Efeitos e brilho são globais ao dispositivo; cor por zona exige modo per-LED.

A primeira auditoria encontrou intervalos de velocidade decrescentes (9 → 0), válidos para os modos reportados. O parser deixou de exigir ordem crescente para esses extremos, com regressão específica; não foram modificadas as capacidades do servidor.

## Integração e segurança

- Renderer → API preload `rgb` com operações enumeradas → main → SDK fixo em `127.0.0.1:6742`. Renderer sem Node, sem sockets e sem API genérica de pacotes/comandos.
- Verificação do PID proprietário do listener por nome OpenRGB e restrição a loopback, reaproveitando o leitor Windows. **Isso não é autenticação criptográfica, pinagem de executável nem isolamento contra processos da mesma conta.** Metadados têm cache de até 15 s; concorrência local e troca do endpoint permanecem limitações.
- Somente pacotes 0, 1, 40 (leitura/negociação), 1050, 1051 e 1101 (cor/modo volátil). Sem resize, firmware, perfis OpenRGB, detecção invasiva ou persistência da controladora.
- Contrato estrito, limite de 32 KiB por solicitação, 256 KiB por resposta, 4 MiB por sessão, 4096 LEDs, 32 controladoras, timeout e serialização. Mudança da lista de dispositivos cancela a sessão; identidade estável é recalculada antes de escrever.
- Confirmação nativa antes da aplicação manual. Estado revalidado depois da confirmação. Jornal anterior persistido antes de escrever; resultado incerto bloqueia novas aplicações até recuperação explícita.
- Cenas Gamer/Trabalho/Relaxar/Noturno começam sem participantes. Configurações ficam no arquivo próprio `workbench/rgb/rgb-control-v1.json`, limitado a 2 MiB e com gravação por substituição atômica. Perfis OpenRGB não são sobrescritos.
- Automação Gamer desativada por padrão, ligada ao detector CS2 existente, somente com consentimento e cena configurada. Restauração automática recusa conflito com edição externa. Após interrupção, não reaplica nem restaura sem revisão. Jogos não foram executados.
- NEX transforma frases específicas em propostas tipadas. O botão da proposta encaminha à mesma confirmação nativa; texto sozinho nunca aciona o equipamento. Não foi incorporado OpenJarvis.

## Testes e evidências

33 suítes Node, **3.731 verificações aprovadas**, incluindo protocolo, parser, limites, reconexão, cancelamento, cenas, persistência, restauração, consentimento Gamer, falha de retorno, recuperação, arquivos corrompidos, propostas NEX, DOM, preload e regressões do Electron. Provedores de testes explicitamente simulados; não são prova de hardware. Python/Android não foram modificados e suas suítes não foram repetidas.

A regressão de falha confirma: um write TCP não é tratado como sucesso; erro deixa journal incerto, remove a leitura atual, impede retry automático e permite recuperação explícita. Há vetor binário independente para o pacote 1051 da zona 3. O diagnóstico novo não foi executado em uma segunda sessão física.

Capturas são do **Electron de desenvolvimento real**, perfil isolado, com capacidades consultadas do OpenRGB real. Sem sensores CPU/GPU iniciados nesta prévia. A última sessão visual encerrou cooperativamente em **45,026 s**; a tentativa de captura inferior das cenas ocorreu depois do encerramento e não produziu imagem. As cenas têm cobertura automatizada de DOM; não se declara essa captura concluída.

![B660M na interface](b660-readonly.png)
![Nollie sem LEDs configurados](nollie-readonly.png)

Recibos locais preservados: `.cache/openrgb-control/physical-test/started.json`, `result.json`, `user-observation.json`; as cópias sanitizadas neste diretório registram o insucesso. Não apagar/reutilizar o marcador para repetir o teste.

## Preservação

Checagem somente leitura às **11:43:17Z**: 118 arquivos instalados da dev.9 r12 iguais ao artefato anterior; 201 arquivos do backup Windows e 31 do backup do agente verificados; preferências workbench e prefixo original de debug.log preservados. Certificados, configuração e identidades do banco iguais à referência; banco íntegro, zero grants e zero comandos pendentes. HKCU Run igual à alteração anteriormente autorizada, sem alteração nesta tarefa.

Agente original identificado na cadeia 6040 → 18256 → 19612 → 6500; um listener 8776; HTTP 200 autenticado, TLS 1.3, hostname e pinagem válidos. Aplicativo instalado fechado e zero processos de monitoramento. A enumeração dos pipes estava indisponível — não se afirma verificação direta de liberação desse namespace. Android não acessado. Firewall não modificado, mas não foi feito inventário comparativo completo de suas regras. Nenhum driver, dependência, serviço ou tarefa instalado. Nenhum benchmark de consumo realizado: a integração não tem polling RGB periódico; reutiliza o ciclo Gamer quando explicitamente ativado, mas o consumo operacional ainda depende de medição.

## Pacotes e próxima validação

[Hashes, tamanhos, inspeções e arquivos modificados](ARTIFACTS.md).

Candidata separada **2.0.0-dev.9 OpenRGB r2**, mesmo appId `com.lone.smartroom`, sem alteração da instalação ou perfil de produção. NSIS assistido e portátil apenas preparados; ambos sem Authenticode. A r1 foi preservada e substituída como candidata pela r2, que completa a ligação visual do NEX. Não executar os pacotes para inspecioná-los.

Antes de uma instalação: diagnosticar a divergência e obter aprovação específica para **um novo teste temporário instrumentado**, com novo recibo independente, backup do estado, aplicação somente à zona aprovada e restauração conferida. Não reutilizar a autorização consumida. Configuração dos canais Nollie é uma decisão separada do usuário; não realizar resize para forçar sucesso.

## Reversão

Nenhuma reversão de produção é necessária: nada foi instalado. No código, reverter somente o commit desta funcionalidade em `feature/openrgb-control` (sem reset destrutivo, sem remover caches/recibos ou backups); `ce0dc55` permanece acessível. Antes de eventual futura atualização, criar backup da instalação e perfil, conferir hashes e consentimento; manter o instalador anterior r12 e sua referência. Se houver RGB pendente no futuro, concluir a recuperação explícita antes de trocar código, nunca apagar o jornal para desbloquear escrita.

## Fontes do protocolo

Implementação independente baseada no [SDK oficial](https://gitlab.com/CalcProgrammer1/OpenRGB/-/blob/master/Documentation/OpenRGBSDK.md), em particular os blocos dos pacotes 1050/1051/1101. A [implementação oficial do servidor](https://gitlab.com/CalcProgrammer1/OpenRGB/-/blob/master/NetworkServer.cpp) foi consultada para investigar a divergência; ela não comprova qual revisão está instalada no PC. Nenhum código GPL do servidor foi copiado para o cliente e nenhum binário OpenRGB é redistribuído.

Pendências anteriores (TLS 10054, Crashpad, validações próprias de inicialização/encerramento e outras homologações) não foram tratadas nem declaradas resolvidas.
