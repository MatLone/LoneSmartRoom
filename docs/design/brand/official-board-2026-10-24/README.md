# Identidade oficial LONE — dev.5 / código 19

24/10/2026 · `feature/ui-migration-preview` · base anterior `68f7db99a50d479e8c53b1c250dc46483151def1`.

Commit da implementação: `9314a1ca977a78fab40cbd363cb1573e38915dcc`. A documentação, as prévias e os resultados desta validação estão no commit posterior.

A nova prancha fornecida pelo usuário é a referência principal. O símbolo angular vermelho e o lettering LONE / SMART ROOM substituem o cubo/hexágono nas aplicações ativas do Android. A imagem original está preservada em [reference/approved-board.png](reference/approved-board.png). Os assets antigos estão preservados, byte a byte, em [previous-dev4/](previous-dev4/), no histórico Git e nos APKs anteriores. O ícone de casa não foi ativado.

**APK assinado e compilado; não instalado. A suíte global não está totalmente aprovada devido à pendência TLS já existente.** Não houve ADB, acesso ao Samsung, alteração de dados do aparelho, envio WoL nem abertura de Steam/CS2 nesta tarefa.

## Revisão visual

- [Aplicações propostas](review/00-aplicacoes-propostas.jpg): ícone Android, adaptativo, Windows, símbolo, logo horizontal, cabeçalho e splash.
- [Prancha original × recriação](review/01-referencia-vs-recriacao.jpg).
- [Máscaras circular/arredondada e tamanhos 48, 56, 72 e 96 px](review/02-mascaras-e-tamanhos.png).
- [Splash completa × proposta nativa Android 12+](review/03-splash-layout-vs-nativa.png).
- Interface integrada em [390 × 844](review/390-controls-preview.png) e [360 × 800](review/360-controls-preview.png). As outras abas e o painel da marca também estão em `review/`.

As capturas da interface são renderizações locais dos assets integrados, com bridges de teste isoladas, sem chamadas reais. Estão identificadas como PRÉVIA LOCAL; não são capturas do Samsung nem prova de execução física da nova versão.

### Fidelidade e adaptações explícitas

Recriação vetorial baseada na referência aprovada, com contornos geométricos locais e rasterização determinística. Não foi recuperada a fonte original, nem prometida equivalência pixel a pixel da textura, do halo ou dos gradientes. O símbolo foi redesenhado conforme as proporções e cantos chanfrados da nova prancha. O lettering usa contornos geométricos, sem dependência de fonte instalada. Nenhuma ferramenta generativa ou serviço externo foi usado nesta recriação.

O cabeçalho compacto agora inclui SMART ROOM. Altura geométrica do subtítulo: aproximadamente **8,1 CSS px a 360 px** e **8,8 CSS px a 390 px**, frente aos cerca de 5 px da aplicação anterior. O tamanho é pequeno, mas o subtítulo não foi removido; as duas prévias permitem avaliar a legibilidade. Sem transbordamento horizontal nos seis cenários capturados e nos quinze casos responsivos automatizados. O nome completo permanece no rótulo do aplicativo e no texto alternativo.

No ícone de fallback Android e no material Windows há moldura própria, como na prancha. O adaptativo usa **foreground transparente sem moldura fixa**, fundo grafite separado e enquadramento conservador dentro da área segura de 66 dp. A máscara final é controlada pelo launcher. Não há um círculo ou quadrado vermelho duplicado dentro da máscara do Samsung. Esse enquadramento é uma adaptação técnica do conceito; a borda e o halo não reproduzem literalmente o círculo da prancha. O subtítulo é decorativo nos ícones mínimos; sua leitura não é garantida a 48 px. Símbolo vermelho e lettering branco permanecem presentes em todas as densidades verificadas.

**Splash:** foram integrados recursos nativos, sem editar Kotlin. Android 26–30 usa fundo grafite e lockup central no window background. Android 31+ recebe explicitamente fundo e imagem segura da splash do sistema. A composição completa com diagonais e traço inferior foi exportada e aplicada à prévia interna, mas essas decorações **não foram implementadas na splash controlada pelo sistema**. Não foi adicionada Activity, temporizador ou segunda tela artificial. A imagem comparativa mostra a diferença antes de pedir instalação. A aparência exata na One UI e a duração da abertura ainda dependem de validação física autorizada.

O ícone Windows foi preparado em [SVG](windows-icon.svg), [PNG](exports/windows-icon.png) e [ICO multirresolução](exports/lone-smart-room-windows.ico). O Electron e seu ícone em uso **não foram modificados** nesta fase Android.

## APK e assinatura

| Campo | Resultado |
| --- | --- |
| Package / nome | `com.lonesmartroom.app` / Lone Smart Room |
| Versão | **2.0.0-dev.5**, `versionCode` **19** |
| Artefato local | `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.5-v19.apk` |
| SHA-256 do APK final | `1acb6d927a3c8db3bb0f0a6be754d442b603a4b3b526dd79cc447e8235abd7e1` |
| Certificado SHA-256 | `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8` |
| Verificação | `apksigner` aprovado, inclusive esquema v2 |
| Compatibilidade | Mesmo certificado do APK v18 extraído após a instalação física anterior e do APK funcional de recuperação |

A numeração local disponível ia até 18 antes da alteração. Não foi consultada novamente a versão viva do telefone: a comparação usa o APK v18 já extraído e verificado. A chave original foi usada no local existente pela configuração de assinatura já aprovada. Não foram copiados keystore ou senhas para o repositório, relatórios ou logs.

Um primeiro APK v19 intermediário foi preservado em `.cache/artifacts/android/draft-official-brand-v19-bbd62e4de802.apk`. A inspeção mostrou que o tema `values-v27` ainda sobrepunha as cores de abertura; somente esse recurso e a opção de barra escura correspondente em v31 foram corrigidos. O hash acima identifica exclusivamente o APK final. O v18 instalado e todos os demais APKs anteriores permanecem preservados.

## Arquivos substituídos / acrescentados

| Grupo | Alteração |
| --- | --- |
| `assets/brand/*.svg` e manifests | Nova logo principal, vertical, símbolo, cabeçalho legível, ícone e splash; proveniência atualizada. |
| `assets/brand/lone-app-icon.png` | Substitui a referência ativa a `nex-app-icon.png`; versão antiga arquivada. |
| `assets/index.html` | Favicon e painel de marca atualizados, incluindo texto que distingue splash nativa e layout completo. IDs, formulários e scripts funcionais preservados. |
| `assets/mobile-v2.css` | Somente largura da marca no cabeçalho: 244/224 px. |
| `res/mipmap-*` | Fallback normal/redondo e `ic_lone_foreground` em cinco densidades; removidos apenas os foregrounds NEX substituídos. |
| `res/values/lone_brand.xml` | Fundo grafite; substitui a cor nomeada para NEX. |
| `res/drawable*`, `values/styles.xml`, `values-v27/styles.xml`, `values-v31/styles.xml` | Imagens de abertura, background central e tema de splash do sistema. |
| `app/build.gradle.kts` | Somente código 19 e nome dev.5; assinatura, SDK e package inalterados. |
| `scripts/*official-brand*`, testes de marca/ícone e smoke | Geração, prévia isolada e inspeção dos recursos compilados. |

O Manifest Android permanece idêntico ao v18: continua apontando para os mesmos mipmaps padrão/redondo e não libera HTTP ou backup. Os antigos scripts de geração foram preservados como histórico; a reprodução desta marca deve usar os novos scripts listados abaixo.

## Testes — incluindo falhas

| Verificação | Resultado |
| --- | --- |
| Build offline assinado + lint final | **BUILD SUCCESSFUL**, 40 s, 46 tarefas; **0 erros / 10 avisos**. |
| Recursos compilados do APK | **20** recursos de ícone/splash, referências adaptativas, três variantes de tema e atributos do sistema conferidos. |
| Imagens e vetores | **20 arquivos** aprovados; cinco densidades, transparência e raio visível ≤ 33 dp. |
| Renderer Android isolado | **65 asserções / 15 casos responsivos**, aprovado; zero chamadas a bridges reais. |
| Prévia integrada | Oito capturas, 390 × 844 e 360 × 800; sem overflow e zero chamadas nativas. |
| JavaScript / launchers | Sintaxe, versão dinâmica, botões condicionados às permissões e estados de comando aprovados, executores simulados. |
| WoL | **11 cenários JS** e teste do pacote Kotlin real aprovados; nenhum UDP enviado. |
| Python completa, rodada 1 | **75/76**, 22,016 s; 1 erro de reset TLS. |
| Python completa, rodada 2 | **74/76**, 22,570 s; 2 erros de reset TLS. |
| Preservação | **86 registros** de originais/recuperação e **30 arquivos funcionais** atuais inalterados. |
| Estado operacional Windows, somente leitura | **0 grants, 0 comandos pendentes, 4 comandos históricos**; identidade e configuração protegida iguais ao snapshot anterior. |

Falhas reais: `test_strict_json_duplicate_headers_and_limits` nas duas rodadas e `test_pair_rate_limit_and_request_limit` na segunda. O cliente recebeu `ConnectionResetError / WinError 10054` ao ler a resposta esperada para corpo excessivo, incluindo o caso de 1025 bytes. A hipótese de fechamento TLS com corpo pendente já está documentada em [TLS.md](../compact-review-2026-10-24/TLS.md). O resultado atual é compatível com essa intermitência, mas não a corrige. Nenhum teste foi removido, tolerância a reset adicionada ou transporte operacional alterado. As duas execuções completas estão preservadas em `validation/`.

O script agregado interrompe após a falha Python; por isso os testes JS e Kotlin foram também executados separadamente e seus resultados registrados. A inspeção inicial precisou ler os atributos compilados do framework por seus IDs oficiais do SDK local, em vez de esperar nomes expandidos no `aapt2`. A primeira chamada externa do renderer reportou falha por um status residual do wrapper PowerShell, embora as 65 asserções tivessem passado; a segunda execução confirmou o resultado do próprio script. Nenhum desses ajustes alterou o aplicativo ou relaxou uma asserção TLS.

Avisos de lint não suprimidos: AGP antigo, orientação, JavaScript, TrustManager, extração de dados, pasta v26, drawable antigo sem uso, coincidência de nome XML/PNG com esse drawable e duas ausências de camada monocromática. Detalhes em [lint-summary.json](validation/lint-summary.json). Não se alterou a validação de certificado para eliminar o aviso genérico de TrustManager. O ícone de casa permanece recuperável e sem referência ativa do launcher.

## Preservação e limites

Kotlin, WakeBridge, `WakeOnLan.kt`, clientes JS, armazenamento `lone-wol-settings-v1`, origem `file:///android_asset/`, scripts de navegação, HTTPS/HMAC, certificados, credenciais e executores Steam/CS2 não foram alterados. As três abas e a autorização por dispositivo continuam com os clientes existentes. O Android instalado permanece dev.4/v18 conforme a última validação física; não se executou nenhuma atualização nesta tarefa.

O banco operacional foi aberto exclusivamente em modo de leitura para conferir permissões. O agente não foi iniciado/reiniciado. Não houve comandos reais de energia, execução de jogos, nova conexão ao Samsung nem acesso aos dados privados do aparelho. Compatibilidade de assinatura e de armazenamento em código não substitui o teste físico posterior à instalação autorizada.

## Reprodução

Usar apenas dependências locais existentes; os scripts não instalam ferramentas:

```powershell
.venv/Scripts/python.exe scripts/build-official-brand.py
node scripts/render-official-brand.cjs '<CAMINHO_LOCAL_DO_SHARP_EXISTENTE>'
scripts/prepare-compatible-apk.ps1 -SdkRoot '<SDK_ANDROID_LOCAL>'
.venv/Scripts/python.exe scripts/verify-official-brand-apk.py --sdk-root '<SDK_ANDROID_LOCAL>'
```

Os artefatos anteriores não devem ser sobrescritos se os hashes mudarem: o verificador de build recusa substituir um candidato diferente. Reservar nova versão para alterações futuras. A geração dos exports Windows em ICO e das pranchas de comparação usa Pillow já disponível; não é parte do APK.

## Atualização futura — não executada

O [procedimento de instalação](UPDATE.md) mantém `adb install -r`, sem desinstalar ou limpar dados. **Ponto de parada atual:** revisão das prévias e autorização expressa antes de qualquer instalação. A pendência TLS deve ser considerada nessa decisão, sem declarar a suíte global aprovada. Nenhuma autorização desta tarefa foi interpretada como permissão para instalar.
