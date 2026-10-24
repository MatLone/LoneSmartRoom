# Ícone oficial NEX — Android 2.0.0-dev.4

24/10/2026 · `feature/ui-migration-preview` · implementação `1e4c155`.
Base preservada: `72f33fd7cd7c6bfe13707e74d0fefc8746da255e`.

O hexágono NEX foi integrado ao ícone nativo do mesmo aplicativo Lone Smart Room. Não houve instalação, consulta ADB ou alteração de dados no Samsung. Este APK é um candidato de desenvolvimento para aprovação visual, não uma atualização já aplicada.

## APK e assinatura

- Artefato: `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.4-v18.apk`.
- Package name: `com.lonesmartroom.app`; nome: **Lone Smart Room**.
- `versionName`: **2.0.0-dev.4**; `versionCode`: **18**. Antes da tarefa, fontes e artefatos locais estavam no máximo em 17; não havia candidato 18.
- SHA-256 do APK: `3a61d82c2b7aa5d457d1dfcbae9365361b0692ecbb807fd7078f9e2281e1c732`.
- Certificado SHA-256: `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
- `apksigner verify`: aprovado, incluindo assinatura v2. O mesmo certificado foi confirmado no APK anteriormente extraído do Samsung, no candidato dev.2 autorizado/instalado na etapa anterior e neste dev.4. Não foi consultada a instalação atual por ADB nesta tarefa; a comparação utiliza evidência local preservada da assinatura conhecida.

A chave original foi usada no local original pelo mecanismo existente do AGP, sem cópia de keystore ou credenciais para Git, documentação ou logs. A configuração de assinatura não mudou. Os candidatos v15, v16 e v17 permanecem preservados. O APK de saída que existia antes desta compilação também foi copiado e conferido em `.cache/artifacts/android/before-nex-893b121b387a.apk`.

## Arte e revisão visual

- [Referência fornecida × ícone proposto em tamanho grande](review/00-referencia-e-icone.png).
- [Máscaras circular/arredondada e miniaturas 48/56/72/96 px](review/01-mascaras-e-tamanhos.png).
- [Simulação de tela inicial em 390 × 844](review/03-simulacao-home-samsung-390x844.jpg), com ícone de **56 × 56 CSS px**.
- [PNG grande arredondado](rounded-512.png) e [circular](circle-512.png).

A imagem fornecida está preservada byte a byte em [nex-hexagon-icon.png](../nex-hexagon-icon.png). O [master transparente](foreground-master.png) foi derivado exclusivamente dessa referência com a skill `imagegen`, modo built-in de edição, para retirar a moldura arredondada e o fundo externo. Isso evita uma borda dentro da máscara do Android. A aparência metálica, o núcleo luminoso e a composição vermelha foram mantidos visualmente; a extração gerada não é uma garantia de identidade pixel a pixel da textura. Método e prompt estão em [IMAGEGEN.md](IMAGEGEN.md).

Os recursos finais são reproduzidos deterministicamente a partir do master preservado, sem nova geração. Não há texto dentro do ícone. O painel interno de identidade e o favicon também passaram a mostrar o ícone NEX. A logo LONE SMART ROOM do cabeçalho, sua seleção compacta e todos os vetores anteriores continuam intactos.

As imagens de máscaras são composições dos mesmos pixels/camadas usados nos recursos nativos. A simulação de home é uma página estática capturada no navegador, explicitamente identificada como simulação. Os demais ícones, horário e indicadores são ilustrativos. Não é screenshot do Samsung, nem comprovação da máscara exata da versão instalada da One UI. Texturas muito finas naturalmente desaparecem em miniaturas; o contorno vermelho e o núcleo continuam identificáveis na inspeção visual.

## Recursos adaptativos

Foram criadas camadas de 108 dp, fundo grafite `#080a0d` e foreground RGBA com margem. O conteúdo visível foi ajustado para diâmetro de projeto de 63 dp, dentro de uma área segura conservadora circular de 66 dp. O teste mede pixels com alfa ≥ 8 em todas as densidades e confirma raio máximo menor que 33 dp; halos de transparência muito baixa não definem a borda geométrica da marca.

A [documentação oficial Android](https://developer.android.com/develop/ui/compose/system/icon_design_adaptive) define camadas de 108 dp, área segura interna de 66 dp e máscaras determinadas pelo launcher. O formato adaptativo desde API 26 atende ao mecanismo de ícones de Android 12–16. Isso não equivale a testes de execução em cada versão: foram mantidos `minSdk 26`, `compileSdk 35` e `targetSdk 35`, sem dispositivos/emuladores novos.

| Recurso por densidade | mdpi | hdpi | xhdpi | xxhdpi | xxxhdpi |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fallback padrão/redondo | 48 | 72 | 96 | 144 | 192 px |
| Foreground adaptativo | 108 | 162 | 216 | 324 | 432 px |

`mipmap-anydpi-v26/ic_launcher.xml` e `ic_launcher_round.xml` usam o mesmo foreground e o fundo separado. O Manifest referencia somente esses novos mipmaps como ícone normal e redondo. O antigo drawable de casa foi mantido sem alteração para preservação, aparece como recurso não utilizado e **não é referenciado pelo launcher**.

Não foi fornecida camada monocromática nesta entrega. Ícones temáticos e coloração forçada pelo launcher não estão representados nas imagens: o Android pode aplicar a paleta do usuário, inclusive automaticamente em Android 16 QPR2, conforme a mesma documentação oficial. Não foi alterada nenhuma configuração de tema do aparelho para forçar vermelho.

## Compilação e testes

Build offline com SDK, JDK e dependências já existentes:

```powershell
scripts/android-build.ps1 -OriginalSigning -Tasks @('assembleDebug','lintDebug','--offline')
```

**Build e lint concluídos com sucesso**, 46 tarefas, em aproximadamente 1 min 3 s. Nenhuma dependência foi instalada. A inspeção com `aapt2` confirmou no APK assinado **17 recursos de launcher**: dois XMLs adaptativos e 15 PNGs nas cinco densidades, suas dimensões e referências compiladas ao fundo/foreground NEX. Também foram conferidos os assets de marca empacotados, o pacote, a versão e as referências do cabeçalho.

| Teste | Resultado final |
| --- | --- |
| Suíte Python segura | **74/74**, 21,612 s. |
| Verificações complementares da suíte | Legado com mocks; versão/comandos Android; **11 cenários WoL** aprovados. |
| Renderer Android | **65 asserções e 15 casos responsivos**, sem bridges reais. |
| Teste dos pixels/densidades | **20 arquivos de imagem/vetor** verificados; área segura, transparência, vermelho e núcleo luminoso preservados nas cinco densidades. |
| WoL Kotlin | Aprovado com as classes desta build, **zero UDP**. |
| Preservação | **86 registros** aprovados; originais e recuperação inalterados. |
| Compatibilidade e inspeção APK | Assinatura original, v2, origem/armazenamento WebView, assets e recursos nativos aprovados. |

A primeira execução Python terminou com **73/74**: a regra de preservação detectou a alteração do Manifest, pois ainda não conhecia a exceção autorizada para o ícone. A regra e seu mapeamento de origem foram atualizados para aceitar exatamente a troca de `android:icon` e a inclusão de `android:roundIcon`, mantendo comparação byte a byte do restante do Manifest. Não foi excluído nenhum teste nem relaxada a verificação de TLS. O [log inicial](validation/full-suite-initial.txt) e o [log final](validation/full-suite-final.txt) foram preservados.

As cópias de logs versionadas normalizam quebras de linha para LF e removem apenas espaços finais de stdout. Os logs brutos permanecem na pasta ignorada `.cache/validation/nex-icon-dev4/`.

O reset TLS intermitente continua como pendência registrada na [investigação anterior](../compact-review-2026-10-24/TLS.md). Esta execução completa passou, mas isso não demonstra correção da intermitência. Nenhum código do agente, teste de transporte, certificado, HMAC ou endpoint foi modificado para obter esse resultado.

### Avisos de lint

**Zero erros, nove avisos, nenhum suprimido para esta entrega.**

- `AndroidGradlePluginVersion`, `DiscouragedApi`, `SetJavaScriptEnabled`, `CustomX509TrustManager` e `DataExtractionRules`: avisos das configurações/implementações existentes, sem correções fora do escopo. O alerta genérico de TrustManager não foi tratado liberando certificados; permanecem a validação existente e os testes de certificado inválido.
- `ObsoleteSdkInt`: a pasta convencional `v26` coincide com o minSdk atual.
- `UnusedResources`: drawable legado de casa preservado e sem uso pelo launcher.
- `MonochromeLauncherIcon`, duas ocorrências: ausência da camada monocromática no ícone padrão/redondo.

A lista estruturada está em [validation/lint-summary.json](validation/lint-summary.json).

## Arquivos alterados e preservação

| Grupo | Alteração |
| --- | --- |
| `apps/android/app/build.gradle.kts` | Somente versionCode 18/versionName dev.4. |
| `apps/android/app/src/main/AndroidManifest.xml` | Somente referências dos ícones normal/redondo. |
| `apps/android/app/src/main/res/mipmap-*`, `values/nex_icon.xml` | 15 PNGs, dois adaptativos e cor de fundo. |
| `assets/brand/nex-app-icon.png`, `assets/index.html` | Ícone no painel de identidade/favicon; cabeçalho preservado. |
| `scripts/build-nex-icon.cjs`, `scripts/verify-nex-apk.py` | Geração determinística e inspeção do APK. |
| `scripts/preservation_rules.py`, `scripts/verify-compatible-apk.py`, `tests/test_baseline.py` | Exceção exata para as referências de ícone e conferência dos assets, sem dispensar as demais verificações. |
| `tests/android-icon-resources.cjs`, `tests/android-mobile-smoke.cjs` | Verificação da área segura/densidades e nova imagem do painel. |
| `docs/design/brand/nex-*` | Referência, master derivado, prévias, relatório e evidências. |

A relação exata está em [validation/changed-files.txt](validation/changed-files.txt). Não foram alterados Kotlin, WoL, bridges, armazenamento `lone-wol-settings-v1`, autenticação HTTPS, pareamento, credenciais, certificados, Windows/Electron, executores Steam/CS2, grants, regras de rede ou diagnóstico TLS. Os checkpoints anteriores continuam ancestrais. Nenhum app real foi iniciado e o agente não foi reiniciado.

Após a aprovação visual, preparar uma atualização controlada com confirmação de assinatura e estado do aparelho, seguida de `adb install -r` autorizado. Não executar downgrade como recuperação automática: uma instalação anterior não garante preservação dos dados. Esta entrega termina antes de qualquer instalação.
