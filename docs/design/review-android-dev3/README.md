# Revisão visual Android — 2.0.0-dev.3

Capturas reais do navegador renderizando a interface integrada. Não são imagens
geradas por IA nem capturas do Samsung. Nenhum arquivo de código do aplicativo,
backend ou projeto Windows foi alterado para esta revisão.

Pasta completa:

`<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\docs\design\review-android-dev3`

## Arquivos recomendados para enviar à revisão

1. [00-comparativo-principais.png](00-comparativo-principais.png): as três abas
   completas lado a lado, em largura de 390 px, com o conteúdo inferior incluído.
2. [01-comparativo-estados-e-bloqueios.png](01-comparativo-estados-e-bloqueios.png):
   conectado/desconectado de demonstração, Steam/CS2 com grants vazios de
   demonstração e painel flutuante de dispositivo.
3. [02-comparativo-responsivo.png](02-comparativo-responsivo.png): viewports
   originais de Controles em 390 × 844 e 360 × 800 px, sem ampliar textos ou CSS.

## Capturas individuais

| Tela | Smartphone: 390 px | Largura menor: 360 px |
| --- | --- | --- |
| Controles completa | [390-controles-completa.png](390-controles-completa.png) | [360-controles-completa.png](360-controles-completa.png) |
| Monitoramento PC completa | [390-monitoramento-pc-completa.png](390-monitoramento-pc-completa.png) | [360-monitoramento-pc-completa.png](360-monitoramento-pc-completa.png) |
| Gamer Launcher completa | [390-gamer-launcher-completa.png](390-gamer-launcher-completa.png) | [360-gamer-launcher-completa.png](360-gamer-launcher-completa.png) |
| Painel de dispositivo | [390-painel-dispositivo.png](390-painel-dispositivo.png) | [360-painel-dispositivo.png](360-painel-dispositivo.png) |
| Steam/CS2, zero grants — DEMONSTRAÇÃO | [390-steam-cs2-zero-grants-DEMONSTRACAO.png](390-steam-cs2-zero-grants-DEMONSTRACAO.png) | [360-steam-cs2-zero-grants-DEMONSTRACAO.png](360-steam-cs2-zero-grants-DEMONSTRACAO.png) |
| Conectado — DEMONSTRAÇÃO | [390-conectado-DEMONSTRACAO.png](390-conectado-DEMONSTRACAO.png) | [360-conectado-DEMONSTRACAO.png](360-conectado-DEMONSTRACAO.png) |
| Desconectado — DEMONSTRAÇÃO | [390-desconectado-DEMONSTRACAO.png](390-desconectado-DEMONSTRACAO.png) | [360-desconectado-DEMONSTRACAO.png](360-desconectado-DEMONSTRACAO.png) |

São **40 arquivos de imagem**: 23 screenshots originais de viewport em `raw/`,
14 imagens individuais em PNG e três pranchas comparativas. Os originais são
JPEG, formato fornecido pelo navegador. Os PNGs preservam seus pixels; não
recuperam detalhes perdidos pela compressão JPEG.

## Método e fidelidade

- A prévia existente utilizada foi `http://127.0.0.1:58774/index.html`, servindo
  os assets de `apps/android/app/src/main/assets`. As três abas e o painel de
  dispositivo foram operados nessa mesma prévia, em abas de captura limpas.
- Os viewports do aplicativo foram 390 × 844 e 360 × 800 CSS px, DPR 1. A
  navegação e a rolagem foram realizadas pela interface do navegador.
- As imagens `*-completa.png` unem trechos sobrepostos de rolagem: o cabeçalho
  e a navegação inferior aparecem uma vez, e toda a altura do conteúdo foi
  coberta. Por isso são mais altas que um viewport de smartphone. Não houve
  reescrita de textos, redesenho de componentes ou alteração de CSS para caber.
- A composição usa pixels sobrepostos da captura seguinte para evitar repetir
  o pequeno indicador da navegação fixa nas emendas. Os screenshots integrais
  de cada etapa estão preservados em `raw/`, com posições e dimensões nos JSONs.
- Antes da captura, o foco de teclado da rolagem foi retirado clicando na área
  inerte da marca pendente, sem acionar funcionalidades. Isso evita confundir
  um contorno de foco do navegador com uma borda permanente do layout.
- `capture-metrics.json` e `demo-capture-metrics.json` registram dimensões,
  posições de rolagem, bloqueio dos botões e transbordamento. `manifest.json`
  registra arquivos, dimensões e SHA-256 das imagens.

## Demonstrações identificadas

Conectado/desconectado e grants vazios foram apresentados em uma prévia auxiliar
isolada em loopback, com faixa visível **“DEMONSTRAÇÃO · sem conexão ao agente
real”**. Ela carrega os mesmos assets integrados e chama apenas os callbacks
de apresentação já existentes. Os horários são dados de demonstração.

Não há bridge `LoneAgent` ou `LoneAndroid` nessa prévia. Não foram consultados
status, credenciais ou grants do agente real; não houve HTTPS real, UDP WoL,
pareamento ou comando de abertura. Os botões Steam/CS2 ficaram desabilitados nas
duas larguras. Nenhuma permissão real foi concedida ou revogada.

O invólucro de demonstração informa a versão pública lida de `build.gradle.kts`
por uma implementação local de `LoneAppInfo.getVersionName()`. Esse adaptador
existe somente na prévia auxiliar, em memória, e não foi incluído no aplicativo,
APK ou código versionado. Sua faixa de 56 px fica fora do quadro do aplicativo;
o quadro mantém as mesmas alturas de 844/800 px.

**Limitação observada na prévia comum:** sem a bridge Android, o componente de
versão mostra seu fallback “Widget Windows 11 · Versão indisponível”. Isso está
preservado nas capturas originais. Não comprova erro no APK Android, onde a
versão vem da bridge nativa; essa validação no Samsung continua pendente.

## Observações para aprovação visual

- Preto/grafite, vermelho de destaque, contornos e linguagem dos cartões estão
  consistentes nas três abas. A navegação inferior permanece visível enquanto
  o conteúdo rola; o destino selecionado usa vermelho.
- Não foi encontrado transbordamento horizontal nas três abas ou nos estados
  capturados em 390/360 px. Conteúdo vertical fora do primeiro viewport é rolável
  e aparece integralmente nos PNGs completos.
- O painel flutuante coube nas duas larguras. Controles indisponíveis usam
  desabilitação, cadeados e textos explícitos. Hardware permanece sem medições;
  NEX e marca final permanecem pendentes.
- Para decisão estética futura: o texto do botão WoL quebra em duas linhas em
  ambas as larguras, com divisão diferente de “Wake-on-LAN”. Legendas, avisos e
  rótulos da navegação são pequenos, especialmente em 360 px. Nenhum ajuste foi
  aplicado nesta tarefa; avaliar legibilidade no tamanho real e, posteriormente,
  com fontes ampliadas no aparelho.
- A marca definitiva continua ausente. Não é possível aprovar sua aplicação
  final ou a correspondência exata com a Variante 3 sem a arte original.
- Estas capturas não substituem testes da WebView Android, áreas do sistema,
  gestos, teclado e acessibilidade no Samsung. A aprovação estética final cabe
  à revisão do usuário.

## Preservação

Os commits `6b9a6b3c801b0466cebffd3406df35e34c43c5b2` e
`f02b1b65e04e80055b40e5aedf9d547a3f197979` foram mantidos. Nenhuma instalação,
reinstalação, desinstalação, limpeza de dados, execução de Steam/CS2, alteração
de grant, driver, firewall ou configuração funcional foi realizada.
