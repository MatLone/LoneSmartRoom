# Marca Lone Smart Room — recriação vetorial para aprovação

A imagem fornecida pelo usuário foi adotada como **referência oficial**. Os
assets desta pasta são uma **recriação vetorial baseada na referência aprovada**,
e aguardam aprovação visual final. Não são os arquivos mestres originais
recuperados, e a fonte original não foi identificada.

Implementação registrada no commit `cd65a18e07af4d8221ba36206d59c14cd33b0a65`,
na branch `feature/ui-migration-preview`.

O símbolo foi reconstruído a partir da aplicação maior no ícone do app, mantendo
o contorno angular em vermelho neon, o retorno inferior e o detalhe interno. O
lettering LONE foi reconstruído em contornos geométricos, com O chanfrado e E
segmentado. SMART ROOM usa traços finos e espaçamento amplo. Como a referência é
uma imagem aplicada em mockups, pode haver diferenças de proporção, espessura e
terminações em relação a uma eventual arte original. A revisão visual deve
avaliar essas diferenças antes de qualquer instalação.

Não foi utilizado o antigo ícone de casa nem introduzida uma marca alternativa.
Os textos e controles demonstrativos presentes na imagem de referência foram
tratados apenas como contexto visual; não viraram funcionalidades do projeto.

## Assets gerados

Os SVGs utilizados pela interface estão em
`apps/android/app/src/main/assets/brand/` na raiz do repositório:

| Uso | Vetor | Exportação PNG |
| --- | --- | --- |
| Logo horizontal principal | [logo-horizontal.svg](../../../apps/android/app/src/main/assets/brand/logo-horizontal.svg) | [1560 × 448, transparente](exports/logo-horizontal.png) / [fundo grafite](exports/logo-horizontal-on-graphite.png) |
| Versão compacta vertical | [logo-compact.svg](../../../apps/android/app/src/main/assets/brand/logo-compact.svg) | [960 × 960, transparente](exports/logo-compact.png) / [fundo grafite](exports/logo-compact-on-graphite.png) |
| Símbolo isolado | [symbol.svg](../../../apps/android/app/src/main/assets/brand/symbol.svg) | [448 × 448](exports/symbol.png) |
| Ícone do app | [app-icon.svg](../../../apps/android/app/src/main/assets/brand/app-icon.svg) | [1024 × 1024](exports/app-icon.png), [512 × 512](exports/app-icon-512.png), [192 × 192](exports/app-icon-192.png) |
| Splash screen | [splash-screen.svg](../../../apps/android/app/src/main/assets/brand/splash-screen.svg) | [1080 × 2400](exports/splash-screen.png) |

Os vetores não usam fontes instaladas, scripts, imagens embutidas, arquivos de
terceiros ou URLs externas. A emissão luminosa é um filtro SVG local. Cores
principais: vermelho `#ff0033`, grafite `#080a0d`, lettering `#f5f5f7`.

[Referência preservada](reference/approved-reference.png), com SHA-256 registrado
em `brand-manifest.json`. A imagem temporária enviada pelo usuário não foi
modificada. SVGs são gerados por `scripts/build-brand-assets.py`; PNGs são
rasterizados diretamente desses vetores por `scripts/render-brand-assets.cjs`,
utilizando a biblioteca sharp já disponível no runtime local. Não houve
instalação de dependências ou uso de geração de imagens por IA.

## Aplicação efetivamente feita

1. O cabeçalho Android substitui MARCA PENDENTE e a composição textual anterior
   pela logo horizontal em SVG. O identificador `brandAsset` foi mantido.
2. A versão continua vindo do módulo nativo existente. Nenhum número foi fixado
   no cabeçalho do aplicativo.
3. A logo agora abre um painel visual de identidade: novo ícone do app e prévia
   da splash screen, com indicação de recriação em revisão. O painel abre no
   início do conteúdo e permite rolagem em telas menores.
4. O favicon da prévia usa o novo ícone angular. O rodapé informa a recriação
   baseada na referência, substituindo a informação de marca não localizada.
5. Apenas `index.html`, `mobile-v2.css` e o módulo de apresentação
   `mobile-shell.js` foram alterados no app, além da inclusão dos assets.

**Limite desta etapa:** o ícone do launcher instalado e a abertura nativa Android
não foram substituídos. O pedido de ícone interno/splash foi aplicado na prévia
da interface, para aprovação antes de integrar os recursos nativos e preparar
outro candidato APK. Não foi alterado Kotlin, Java, Manifest, estilos nativos,
package name ou configuração de assinatura.

O APK dev.3 anteriormente preservado continua com o conteúdo anterior e **não
contém esta marca**. Não foi reconstruído nem sobrescrito. Após aprovação visual,
será necessário preparar e verificar outro candidato com versão própria,
preservando os APKs anteriores. Nenhum APK foi instalado no Samsung.

## Capturas para aprovação

- [00 — prancha dos assets](review/00-marca-recriada.png).
- [01 — três abas Android com a marca](review/01-interface-marca-aplicada.png).
- [02 — painel de ícone e splash](review/02-icone-splash-interface.png).
- [03 — comparação responsiva](review/03-responsivo.png).

Capturas individuais em `review/`: `390-controles.jpg`, `390-monitoramento.jpg`,
`390-gamer.jpg`, `390-icone-splash-painel.jpg`, `390-splash-painel.jpg` e os
equivalentes em 360 px. São screenshots reais de navegador, não do Samsung.

O quadro do aplicativo mede 390 × 844 ou 360 × 800 CSS px; a faixa externa de
28 px identifica a prévia local. Os mesmos HTML/CSS/JS são servidos por uma
allowlist estática em loopback. Um adaptador somente de metadado público informa
a versão lida do projeto para representar o cabeçalho Android; não existe bridge
LoneAgent ou LoneAndroid nessa prévia. Nenhum status de conexão foi simulado como
real, e Steam/CS2 permaneceram bloqueados. A prévia não acessa o agente ou o celular.

Não foi encontrado transbordamento horizontal nas três abas em ambas as
larguras. A marca e os assets do painel carregaram corretamente. O painel usa
rolagem vertical para apresentar a splash inteira em telas menores. Detalhes
estéticos e fidelidade da recriação permanecem sujeitos à aprovação do usuário.

## Preservação e testes

- Comparação com o conteúdo do commit `0512ad4` dos arquivos Kotlin/Java,
  recursos Android nativos, Manifest, Gradle, agente Windows, Electron e clientes
  JS de WoL/HTTPS/permissões: **inalterados**, considerando apenas a normalização
  CRLF/LF existente no checkout Git para arquivos de texto. Relação e hashes em
  [validation.json](validation.json).
- Wake-on-LAN mantém código Kotlin, bridge, armazenamento e fluxo existentes.
  Nenhum código de WoL, status, pareamento, HMAC, certificado ou grant foi alterado.
- **60 verificações de renderer aprovadas**, incluindo 15 combinações de
  largura/aba, carregamento dos assets, modal e bloqueios com bridges simuladas.
- **3 testes de assets aprovados**: SVG local sem código/conteúdo externo,
  proveniência por hashes e geração determinística do vetor.
- **11 cenários WoL da interface aprovados**, teste Kotlin do pacote WoL aprovado
  sem envio UDP, e testes de versão/estados de comandos aprovados.
- **86 registros de preservação aprovados**: originais e recuperação intactos.
- Regressão Python completa: **73 de 74 passaram** em duas execuções; o teste
  já existente `test_strict_json_duplicate_headers_and_limits` recebeu
  `ConnectionResetError / WinError 10054` ao ler a resposta TLS da fixture.
  A reexecução isolada do mesmo teste passou. O backend e esse teste não foram
  modificados. Isso fica registrado como instabilidade de transporte a investigar
  separadamente; esta entrega não declara a suíte completa integralmente verde.
- Não foi executado novo build Android nesta fase visual. Não houve acesso ADB,
  instalação, limpeza de dados, execução de Steam/CS2, envio WoL real, concessão
  de grants ou alteração de firewall/serviços/drivers.

Os checkpoints `6b9a6b3`, `f02b1b6`, `0512ad4` e seus ancestrais são preservados.
A reversão da aplicação visual é feita por commit, sem tocar no dispositivo ou
nas credenciais. A próxima decisão é a aprovação das artes e capturas; ela não
equivale a autorização de instalação no Samsung.
