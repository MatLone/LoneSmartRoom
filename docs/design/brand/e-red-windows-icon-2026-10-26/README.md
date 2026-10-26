# Ajuste final: somente E vermelho e ícone Windows no Android

Implementação visual `86f6540`, branch `feature/ui-migration-preview`, sobre o checkpoint preservado `098d1a2`. Não houve instalação, nova sessão física Windows, acesso ao Samsung, comandos operacionais ou coleta de hardware.

## Revisão visual

- [Comparação anterior × nova marca e Windows × Android](comparison-windows-android.png).
- [Prancha HTML](review.html).
- [Cabeçalho Android 390 px](android-header-390.png) e [360 px](android-header-360.png).
- [Interface Windows local](windows-dashboard-preview.png) e [marca do Windows ampliada pelo recorte](windows-header-preview.png).
- [Ícone Samsung em 56 px, simulação](samsung-icon-simulation.png).
- [Splash nativa proposta, simulação](native-splash-simulation.png) e [arte completa](exports/splash-screen.png).
- [Logo horizontal ampliada](exports/logo-horizontal.png), [compacta](exports/logo-compact.png).
- [Windows original](exports/windows-original.png), [fonte Android idêntica](exports/android-source-identical.png), [máscara circular](exports/android-circle-512.png), [máscara arredondada](exports/android-rounded-512.png).

Os cabeçalhos são renderizações dos arquivos reais do projeto em Chromium/Electron isolado, sem carregar o main/preload de produção. As telas Samsung e splash são **simulações identificadas**, não capturas de aparelho ou garantia do layout controlado pelo Android. Nenhum perfil de produção foi utilizado. Ver [proveniência](preview-provenance.json).

## 1. Alteração estritamente limitada à letra E

- L, O e N conservam o preenchimento branco/gradiente branco original.
- Somente o path vetorial do E recebeu `fill="#ff153f"`, o vermelho `--red` oficial do dashboard Windows.
- SMART ROOM manteve cor, traço, espaçamentos e estilo anteriores.
- Nenhum path, transform, viewBox, proporção, contorno, espessura ou geometria foi alterado nos logotipos.
- Aplicação: logos horizontal, cabeçalho pequeno, compacta e splash completa Android; logos horizontal e de cabeçalho Windows; duas imagens da splash nativa Android.

Os testes removem o novo atributo `fill` do E e exigem igualdade de toda a árvore SVG com os originais arquivados. Também exigem igualdade textual com uma substituição única no SVG original. Isso impede recolorir LONE inteira ou redesenhar a tipografia/símbolo.

Nas splashes rasterizadas, a comparação com os dois PNGs anteriores confirmou **zero diferenças no canal alfa**. As mudanças RGB ficaram restritas à região do E: 1.137 pixels em `lone_splash_safe.png` e 4.112 pixels em `lone_splash_lockup.png`. Os demais elementos conservaram seus pixels. Os originais vieram do checkpoint anterior e estão em `reference/`, com hashes.

## 2. Ícone Android proveniente do asset Windows original

Fonte: `apps/windows-ui/assets/brand/windows-icon.svg` e seu PNG já existente. Os três masters Windows SVG/PNG/ICO permaneceram byte a byte intactos.

SHA-256 do PNG original: `5da66a0836d86fee89682f5ed6c2d35b09676700f91a69637818c19882896964`.

- `assets/brand/app-icon.svg` Android é cópia exata do SVG Windows.
- `assets/brand/lone-app-icon.png` Android é cópia exata do PNG Windows, incluindo símbolo, fundo, gradiente e moldura originais, sem textos adicionados.
- Launcher legado: redimensionamento direto do mesmo PNG nas cinco densidades; a versão round recebe somente o recorte circular.
- Adaptive: mesmo tile Windows em viewport central de 72 dp sobre camada de 108 dp, com escala uniforme e translação. Nenhum traço ou contorno foi reconstruído.
- Os XMLs adaptativos, identificadores de recursos e cor de fundo permaneceram iguais. A moldura não foi redesenhada ou duplicada: é a própria moldura do Windows.

**Diferença técnica esperada:** a máscara circular/arredondada do launcher pode recortar partes da moldura externa original. O símbolo angular permanece inteiro. O raio crítico medido foi de 30,54 a **31,10 dp**, dentro do limite conservador de **33 dp** (diâmetro 66 dp) nas cinco densidades. O teste anterior que exigia todo o foreground sem moldura dentro desse círculo foi substituído por verificações explícitas do símbolo crítico e da identidade dos pixels com o asset Windows; não se declarou a moldura como conteúdo crítico preservado em toda máscara.

As propostas de splash mantêm a logomarca completa com E vermelho; elas não foram substituídas pelo ícone sem lettering. A aparência exata no One UI, com temas e animações do sistema, permanece para validação após aprovação e instalação autorizada.

## Arquivos alterados

O [manifesto exato](change-manifest.json) registra SHA-256 antes/depois dos **28 arquivos visuais ativos**:

| Grupo | Alteração |
|---|---|
| Android `assets/brand/{logo-horizontal,logo-header-small,logo-compact,splash-screen}.svg` | Apenas fill do E |
| Windows `assets/brand/{logo-horizontal,logo-header-small}.svg` | Mesmos vetores Android com apenas E vermelho |
| Android `assets/brand/{app-icon.svg,lone-app-icon.png}` | Cópias dos masters Windows |
| Android `assets/brand/{brand-manifest,header-small-manifest}.json` | Proveniência e novos hashes |
| Android `res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/*.png` | 15 imagens launcher/round/foreground |
| Android `res/drawable-nodpi/lone_splash_{safe,lockup}.png` | E vermelho, pixels restantes e alfa preservados |
| Android `assets/index.html` | Somente descrição/alt do ícone, para não afirmar lettering inexistente |

Ferramentas novas: `build-e-red-brand.py`, `render-e-red-brand.cjs`, `capture-e-red-brand-review.cjs`. Testes novos/adaptados: `test_brand_e_update.py`, `test_brand_assets.py`, `test_android_visual_preservation.py`, `android-icon-resources.cjs`. Nenhum handler, bridge, Kotlin/Java, CSS da interface, manifesto Android, versão ou configuração de assinatura mudou.

Os masters anteriores estão arquivados em `reference/`; os arquivos históricos de identidade e seus exports anteriores não foram sobrescritos. Os geradores históricos permanecem para recuperação; o pipeline desta revisão é o novo gerador, que preserva os originais e aplica a única substituição autorizada.

## Testes

| Verificação | Resultado |
|---|---|
| Python completo | **214 aprovados**, zero falhas/erros |
| Marca/geometry/proveniência Python | 13 aprovados, incluídos na suíte geral |
| Preservação Android específica | 3 aprovados, incluídos na suíte geral |
| Renderer Android existente | 65 assertions, 15 casos responsivos |
| Renderer Android da família Windows | 352 assertions, 63 casos responsivos |
| Imagens, vetores e splashes | 27 arquivos verificados, cinco densidades, zero diferenças alfa nas splashes |
| Android `processDebugResources` e `lintDebug`, offline | Aprovados; zero erros e dez avisos existentes |

As suítes têm sobreposição. Foram usados apenas runtimes/dependências já disponíveis, sem instalação de ferramentas. Os testes HTTPS usam fixtures loopback e identidades temporárias, não o agente operacional. Não houve envio real de WoL ou abertura Steam/CS2. Uma falha inicial do exportador foi corrigida somente em desenvolvimento: o sharp precisava compor no canvas original antes de redimensionar o buffer; os testes de pixels confirmaram preservação da geometria.

## Preservação e build

[Conferência final](preservation.json): do conjunto de 1.338 arquivos protegidos, 27 assets receberam as mudanças autorizadas; os **1.311 demais arquivos** permaneceram idênticos. O 28º arquivo visual é a descrição HTML, conferida no manifesto. Instalação Windows, perfil de produção, backups e recuperação permaneceram intactos. Quatro arquivos protegidos de runtime e o banco/identidades/schema/permissões mantiveram integridade; **zero grants**.

O supervisor e worker originais permaneceram com as mesmas identidades, listener único 8776 e hashes da entrada Run e das regras relevantes do firewall. Não houve requisição operacional ao agente nesta tarefa. Não foram modificados certificados, credenciais, HMAC, antirreplay, pareamento, WoL, executores, Android instalado ou Windows instalado. Nenhum Electron/monitoramento residual foi encontrado após as prévias.

**Não foi gerado novo APK instalável.** A versão e assinatura Android continuam configuradas como antes; o APK dev.8/v22 anterior permaneceu com seu hash original e **não contém estes ajustes novos**. Depois da aprovação visual, uma próxima build deverá receber numeração nova, ser assinada com a chave original local e passar novamente por inspeção de recursos e apksigner antes de qualquer instalação. Nenhuma instalação foi preparada para execução automática.

As pendências TLS, Crashpad, encerramento gracioso e homologação física parcial Windows ficaram fora deste trabalho.

## Reversão e aprovação

Para desfazer em desenvolvimento, reverter o commit documental desta entrega e depois `86f6540`, revisando eventuais conflitos. Isso restaura os assets e testes anteriores sem alterar instalações ou dados. Não executar reset destrutivo, limpeza de dados, downgrade ou restauração de backup. Nenhuma reversão foi executada.

Aprovação solicitada: E vermelho, ícone Windows reutilizado e comportamento visual das máscaras. A implantação e validação física ficam pendentes de autorização separada.
