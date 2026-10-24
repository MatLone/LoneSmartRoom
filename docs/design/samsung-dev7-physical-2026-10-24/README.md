# Samsung — atualização controlada dev.7 / código 21

24/10/2026 · America/Sao_Paulo · branch `feature/ui-migration-preview`.
Checkpoint preservado: `908538a94767ea166c1634063e74e5c5715fc6c5`.

**Instalação concluída: dev.5/código 19 → dev.7/código 21**, no Galaxy S25 FE SM-S731B, Android 16/API 36. Uma única execução de `adb install -r`, exit code 0 e resposta `Success`, encerrada às 03:22:19. O Android registrou `lastUpdateTime` às 03:22:21. Nenhuma desinstalação, limpeza de dados, troca de assinatura, downgrade ou repetição da instalação.

## Identidade e compatibilidade

| Campo | Resultado |
| --- | --- |
| Package original e instalado | `com.lonesmartroom.app` |
| Versão viva anterior | `2.0.0-dev.5` / 19 |
| Versão instalada e APK novamente extraído | `2.0.0-dev.7` / 21 |
| Certificado SHA-256 de ambos | `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8` |
| SHA-256 do APK v21 instalado | `a45bd56f07ba578f7100b9266e71e2ef72635ec774fb3393615f739dc416fc2c` |
| Assinatura | Verificada por apksigner, incluindo esquema v2; APK extraído igual ao candidato autorizado |
| Identidade dos dados | UID 10368, diretório de dados e primeira instalação preservados |

Antes de instalar foram conferidos 19 assets empacotados contra o checkpoint aprovado, sete arquivos funcionais da WebView contra o APK vivo v19, oito fontes Kotlin e 33 arquivos protegidos. As 30 entradas de marca e recursos nativos do APK continuam idênticas ao v19. HTTP global continua bloqueado e backup Android desativado.

O comando executado foi `adb -s <Samsung validado> install -r <APK v21 validado>`, com seleção explícita do único Galaxy S25 FE conectado. O serial não é publicado. APK utilizado: `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.7-v21.apk`.

## Capturas e validação visual real

[Comparativo real: antes/depois, três abas e Configurar](00-validacao-real.jpg). Os PNGs integrais têm 1080 × 2340 pixels, sem reconstruir a interface.

| Tela | Evidência e resultado |
| --- | --- |
| Cabeçalho real | [Recorte](02-cabecalho-real.png), [Controles completo](screens/11-controles-final.png). Logo, versão dev.7 e nova engrenagem visíveis. |
| Splash nativa | [Quadro real](screens/01-splash-nativa-real.jpg). Marca centralizada, sem diagonais, preservada. |
| Controles e consulta HTTPS | [Conectado](screens/02-controles-conectado.png). Consulta manual concluída com o pareamento existente. |
| Monitoramento PC | [Tela](screens/03-monitoramento.png), [rolagem](screens/04-monitoramento-inferior.png). Métricas indisponíveis, sem valores simulados. |
| Gamer Launcher | [Zero grants](screens/05-gamer-zero-grants.png), [rolagem](screens/06-gamer-inferior.png). Steam/CS2 desabilitados. |
| Explicação de permissões | [Painel real](screens/07-painel-permissoes.png). Abriu e fechou; os dois aplicativos seguem bloqueados. |
| Controles inferiores e dispositivo | [Rolagem](screens/08-controles-inferior.png), [painel Lâmpada](screens/09-painel-dispositivo.png). Abriu/fechou; controles indisponíveis permanecem desabilitados. |
| Identidade oficial | [Painel da marca](screens/10-painel-identidade.png). Logo, ícone interno e referência completa da splash preservados. |
| Botão Configurar | [Recorte real](03-configurar-real.png). Abriu o painel de conexão; a engrenagem do cabeçalho também abriu o mesmo painel. |

O inset real `statusBars`, informado pelo Android em `dumpsys window displays`, ocupa **y=0..97 px**. O início do contêiner da logo fica em **y=112 px**, 15 px abaixo; o botão da engrenagem inicia em **y=133 px**, 36 px abaixo. Horário, Wi-Fi e bateria permanecem na barra superior, sem sobreposição com esses elementos. A versão está em y=294..322 px. Esses números são pixels físicos deste aparelho, não dp ou pixels CSS.

As três abas, navegação inferior fixa, rolagem e painéis foram conferidos. Não se observou corte horizontal, sobreposição indevida ou conteúdo inacessível nas telas examinadas. Conteúdos abaixo da dobra ficam disponíveis por rolagem. Não foram alterados resolução, densidade, orientação ou configurações do Samsung. Esta validação corresponde ao S25 FE observado, sem afirmar cobertura de todos os aparelhos Android.

A splash foi extraída a 800 ms da gravação real da primeira abertura após a atualização, com Windows MediaComposition/WinRT instalado. O quadro registra a transição nativa da janela; não houve substituição artificial da marca. Vídeo original preservado localmente em `.cache/validation/samsung-v21-physical/splash-opening.mp4`; hash e método em [splash-provenance.json](evidence/splash-provenance.json). Não foi necessário novo lançamento para extração. Continua visível um breve intervalo escuro entre a splash e a WebView, já registrado na validação anterior; não foi alterado nesta tarefa.

## Preservação funcional e segurança

- **WoL:** mesma origem `file://`, mesma chave `lone-wol-settings-v1`, MAC, broadcast e porta iguais à cópia protegida anterior. Leitura estável do WAL e verificação de checksums; os três campos visíveis também conferem. Nenhuma edição/salvamento ou pacote WoL enviado. O painel com valores de rede não foi publicado em captura.
- **Credenciais Android:** os 418 bytes do cofre cifrado eram iguais imediatamente antes e depois da instalação, antes da abertura. Após o uso, o cofre continua presente e o pareamento autenticou sem novo código. Não se exige igualdade do ciphertext após consultas, que podem atualizar a última comunicação.
- **HTTPS:** consulta de status autenticada concluída às **03:24:23**, estado **Conectado** e energia **Não verificado**. Nenhuma ausência de resposta foi interpretada como PC desligado.
- **Agente Windows:** listener 8776 confirmado, PID 13012, sem iniciar ou reiniciar o processo. O PID 19032 é o processo pai do runtime da venv, não foi criada outra instância nesta tarefa. Configuração, certificados, arquivos protegidos e identidade pareada conferem com o snapshot anterior.
- **Permissões:** **zero grants**, zero comandos pendentes e histórico inalterado em quatro comandos. Steam e CS2 continuam desabilitados. Nenhum aplicativo, comando de energia ou pacote WoL foi acionado.
- **Fontes e recuperação:** 33 fontes protegidas e 86 registros de originais/recuperação preservados. APKs v19, v20 e v21 tiveram seus hashes novamente conferidos. Nenhuma alteração em Kotlin, WoL, HTTPS, HMAC, certificados, pareamento, grants, executores, firewall ou configurações do Windows.

Os dados verificados e a identidade do armazenamento foram preservados; estes registros não constituem exportação completa de todos os dados privados nem das chaves AndroidKeystore.

## Backups locais protegidos

- APK vivo anterior: `.cache/validation/samsung-v21-physical/installed-before-v21.apk`.
- APK vivo posterior: `.cache/validation/samsung-v21-physical/installed-after-v21.apk`.
- WoL protegido: `recovery/device-settings/samsung-v21-wol-before-20261024T062200752248Z.dpapi`.
- Cópia DPAPI do cofre já cifrado: `recovery/device-settings/samsung-v21-vault-before-20261024T062200753630Z.dpapi`.

Os backups foram verificados por round-trip DPAPI e ficam fora do Git. APKs anteriores, cópias de recuperação e dumps continuam nos seus locais. Nenhum downgrade foi realizado; não se presume recuperação automática das chaves ou dos dados após desinstalar/limpar armazenamento.

## Ocorrências e limites

Não foi observada falha de instalação, assinatura ou autenticação no escopo autorizado. Não apareceu marcador de crash no buffer consultado para o PID atual do aplicativo; isso não equivale a uma auditoria completa de todos os processos Android.

Os helpers tiveram falhas de coleta: acesso inicial ao ADB/CIM restrito pela sandbox, uma leitura transitória do UIAutomator após abrir, um argumento acentuado não reconhecido pelo helper por codificação local e incompatibilidade do WinRT com PowerShell Core. As leituras concluíram com o contexto permitido, UTF-8 explícito e Windows PowerShell já instalado. O primeiro helper de geometria também não encontrou nós SystemUI: esse aparelho expôs apenas a árvore do aplicativo, então o inset foi obtido diretamente do Android. Esses ajustes afetaram somente helpers locais; não foram correções no app, no agente ou no Windows. Não houve repetição da instalação nem dos comandos funcionais por causa dessas falhas.

**TLS conhecido:** a pendência de reset intermitente para requisições com corpo excessivo continua em [TLS.md](../brand/compact-review-2026-10-24/TLS.md), sem correção aplicada. As consultas normais bem-sucedidas desta instalação não comprovam sua resolução. Nenhuma nova falha de conexão Android–Windows foi observada. A suíte automatizada completa não foi repetida nesta tarefa física; seus resultados da preparação dev.7 permanecem em [revisão anterior](../header-settings-dev7-2026-10-24/README.md).

## Estado final

Samsung atualizado para **2.0.0-dev.7 / código 21**, devolvido à aba Controles, com estado autenticado Conectado. Repositório na branch original, checkpoint `908538a` preservado. Esta entrega acrescenta documentação/capturas e a regra de conservação de seus bytes no Git; nenhum código funcional foi modificado.

Recibos sem valores de credenciais em `evidence/`. `SHA256SUMS.json` permite verificar os arquivos desta revisão. O hash do novo commit documental é informado na entrega final.
