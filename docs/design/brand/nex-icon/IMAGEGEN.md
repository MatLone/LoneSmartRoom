# Origem e extração do ícone NEX

Referência definitiva fornecida pelo usuário, preservada sem regravação em `docs/design/brand/nex-hexagon-icon.png`. SHA-256: `9a7b0b1233dc75a20db2094a175c4a2357018e60cf201938c9bd9076fb157ca4`.

Foi utilizada a skill `imagegen`, modo built-in de edição, para extrair o hexágono e remover a moldura arredondada externa e o fundo ao redor. O resultado derivado está em `foreground-master.png`, com canal alfa. Não é recuperação de um arquivo vetorial original nem garantia de identidade pixel a pixel da textura. A comparação visual entre referência e derivado faz parte da aprovação antes de instalar. Nenhum texto ou símbolo de casa foi acrescentado.

Prompt utilizado:

> Precise non-creative extraction for an Android adaptive launcher icon. Edit the supplied approved source image only: isolate the complete central red neon metallic three-dimensional HEXAGON with the luminous cube/core. Remove ONLY the outer rounded-square app tile/frame, its external glow, and the background outside the central hexagonal emblem. Return a centered complete cutout on genuine transparent background, with comfortable transparent margin around all six vertices. Preserve the source emblem's exact orientation, geometric panel layout, metallic texture, dark interior panels, red-white neon edges, central luminous red cube and lighting. Keep dark/black regions INSIDE the hexagon opaque as in the source. Retain a soft modest red glow immediately around the hexagon, but no rounded-square contour anywhere. No text, no invented geometry, no house icon, no added glyphs. This is extraction of an approved mark, not a redesign. No alternate interpretation.

A partir do master, `scripts/build-nex-icon.cjs` apenas redimensiona, posiciona e compõe as camadas/miniaturas de forma determinística com Sharp já instalado. Não chama serviços externos nem exige nova geração para reproduzir os recursos Android.
