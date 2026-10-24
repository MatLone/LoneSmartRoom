# Cabeçalho Android e engrenagem — dev.7 / código 21

Revisão de 24/10/2026 na branch `feature/ui-migration-preview`. Nenhuma instalação ou consulta por ADB foi realizada nesta tarefa. O último estado físico documentado do Samsung continua sendo dev.5/código 19. As imagens novas são **prévias locais**, com barra de status simulada e bridges de teste isoladas, sem acesso às credenciais ou ao agente operacional.

## Resultado visual

- [Comparativo: captura física anterior e proposta local](01-comparativo-cabecalho-configurar.png).
- [Cabeçalho ampliado com versão](02-cabecalho-ampliado.png).
- [Botão Configurar ampliado](03-configurar-ampliado.png).
- [Controles 390 × 844](390-controls-preview.png) e [360 × 800](360-controls-preview.png).
- [Monitoramento 390 × 844](390-monitor-preview.png) e [360 × 800](360-monitor-preview.png).
- [Gamer Launcher 390 × 844](390-gamer-preview.png) e [360 × 800](360-gamer-preview.png).
- [Painel flutuante 360 × 800](360-device-panel-preview.png).
- [Engrenagem vetorial](settings-gear.svg), com renderizações em 16, 17, 20, 22, 24, 32 e 192 px nesta pasta.

A referência do problema é a captura física já preservada em `../samsung-dev5-physical-2026-10-24/screens/03-controles-conectado.png`. Não houve uma nova captura do aparelho. Recortes ampliados preservam os pixels das prévias; não representam maior resolução física.

## Alterações limitadas à apresentação

O cabeçalho Android usa `padding-top: calc(max(32px, env(safe-area-inset-top, 0px)) + 12px)`: respeita o inset informado pela WebView e mantém reserva mínima quando ele vale zero. Insets laterais também são considerados. A marca passou de largura máxima de 244 para 224 px no Android, com espaçamento inferior de 14 px, versão em 9 px e botão de configurações com área de toque de 44 × 44 px. O conteúdo das abas continua rolável.

A documentação do Android explica que a propagação de insets para CSS depende da versão da WebView e da integração nativa, podendo haver espaço adicional quando o host nativo também aplica padding. [Fonte oficial: insets em WebViews](https://developer.android.com/develop/ui/views/layout/webapps/understand-window-insets). A integração Kotlin existente foi preservada. A reserva mínima de 32 px é uma decisão conservadora de layout, não uma medição do Samsung. **Ainda é necessário verificar a altura final no One UI/Android 16 após autorização de teste físico**; a prévia não comprova o comportamento de todos os hosts nativos.

A nova engrenagem tem oito dentes simétricos, contorno com cantos chanfrados, centro circular e o mesmo traço de 1,7 da família de ícones. Substitui o SVG nos aliases `settings` e `gear` do shell Android, atendendo cabeçalho e botão Configurar. As duas cópias legadas de `app.js` (Android e Electron) receberam exclusivamente o mesmo desenho. Os painéis flutuantes usam esses renderizadores quando solicitam a engrenagem; ícones de fechar e controles deslizantes permanecem distintos.

Arquivos de produção alterados:

1. `apps/android/app/src/main/assets/mobile-v2.css`: posicionamento do cabeçalho Android.
2. `apps/android/app/src/main/assets/mobile-shell.js`: apenas SVG da engrenagem e comentário descritivo.
3. `apps/android/app/src/main/assets/app.js` e `apps/windows-ui/app.js`: apenas SVG legado idêntico.
4. `apps/android/app/build.gradle.kts`: versão dev.7/código 21.

Também foram acrescentados o teste `tests/android-header-insets.cjs`, o capturador isolado `scripts/capture-header-settings-preview.cjs`, esta revisão e sua regra de preservação de bytes em `.gitattributes`. `scripts/preservation_rules.py` foi atualizado somente para reconhecer a substituição exata do SVG legado; não permite mudanças em handlers.

## Build e assinatura

- APK: `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.7-v21.apk`.
- Package: `com.lonesmartroom.app`.
- Versão: `2.0.0-dev.7`, código `21`; os códigos 19 e 20 já estavam utilizados.
- SHA-256 do APK: `a45bd56f07ba578f7100b9266e71e2ef72635ec774fb3393615f739dc416fc2c`.
- Certificado SHA-256: `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
- Assinatura verificada, incluindo APK Signature Scheme v2, com a identidade original. Nenhuma chave ou senha foi incluída nesta revisão.
- `assembleDebug` e `lintDebug` concluídos em modo offline: 46 tarefas, 23 executadas e 23 atualizadas; 33 segundos. Lint: zero erros e dez avisos existentes, discriminados no recibo de preservação. Estes avisos não foram corrigidos fora do escopo visual.
- Builds dev.5/v19 e dev.6/v20 preservadas no mesmo diretório de artefatos; seus hashes estão em `evidence/preservation-and-build.json`. Não executar downgrade presumindo preservação automática dos dados.

## Testes e preservação

| Verificação | Resultado |
| --- | --- |
| Suíte segura Python | 76/76 aprovados |
| Renderer Android | 65 assertivas e 15 casos responsivos aprovados |
| Novo teste de cabeçalho | 60 casos: cinco tamanhos, quatro insets superiores, três abas |
| WoL JavaScript | 11 cenários aprovados, sem envio real |
| Pacote WoL Kotlin de produção | Normalização MAC, bytes e rejeição de entradas inválidas aprovados; zero UDP |
| Ícone adaptativo e splash compilados | 20 recursos/atributos verificados no APK |
| Fontes protegidas | 33 arquivos byte a byte iguais ao estado anterior |
| Marca e recursos nativos entre v20 e v21 | 30 entradas do APK idênticas |
| Originais e recuperação | 86 registros preservados |

O teste novo emula `env(safe-area-inset-top)` em 0, 24, 32 e 48 px por meio do comando oficial CDP `Emulation.setSafeAreaInsetsOverride`. Verifica posição da logo, versão e botão, área de toque, igualdade dos ícones, espaço rolável e ausência de transbordamento horizontal. A API está definida no [protocolo oficial do Chrome DevTools](https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/pdl/domains/Emulation.pdl). Medições completas em `inset-measurements.json`.

Durante a preparação, a emulação CDP falhou no renderer offscreen com `UnknownVizError`; a alternativa com janela oculta mediu os insets corretamente, mas produziu capturas desatualizadas e depois atingiu timeout ao tentar capturar pelo CDP. As capturas inválidas não foram entregues. A solução foi separar a medição CDP da captura offscreen estável. Os dois fluxos finais passaram, e as imagens das abas foram conferidas visualmente. Esses erros de ferramenta permanecem nos logs locais `.cache/validation/header-dev7/`; não foram atribuídos ao aplicativo ou ao TLS.

**Pendência TLS preservada:** o reset intermitente não reapareceu nesta execução de 76 testes; isso não comprova sua resolução. O agente operacional e seus limites de corpo não foram modificados. A investigação anterior continua em [TLS.md](../brand/compact-review-2026-10-24/TLS.md).

Nenhum arquivo Kotlin, executor, autenticação, certificado, HMAC, permissão, grant, chave de armazenamento ou configuração WoL foi alterado. Nenhum pacote WoL foi enviado, e Steam/CS2 não foram abertos. Ícones nativos e splash oficial continuam iguais à build anterior.

## Próxima validação

Submeter as prévias à aprovação. Somente com nova autorização: conferir novamente versão/assinatura e estado dos dados, atualizar por `adb install -r` e observar a posição real abaixo da barra de status. Não há instalação programada ou executada nesta entrega.

Os recibos e logs de sucesso estão em `evidence/`. `SHA256SUMS.txt` permite conferir os arquivos desta revisão. O hash do commit é informado na entrega, pois inserir o próprio hash no conteúdo do commit criaria referência circular.
