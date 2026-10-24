# Prévia da evolução visual

Revisão visual no mesmo repositório do Lone Smart Room. Entrada:
`android.html` ou `windows.html`, em navegador, com os dois arquivos auxiliares
`visual.css` e `prototype.js` no mesmo diretório. Abas, painéis e teclado são
interativos; comandos de dispositivos e persistência ficam indisponíveis.
Não copiar diretamente para assets de produção antes da revisão e dos bindings
descritos em `../UI-MIGRATION-PLAN.md`.

A marca é um placeholder explícito: a Variante 3 — Contorno Luminoso ainda não
foi localizada. O ícone antigo não é usado como logo definitiva e nenhuma marca
foi recriada por aproximação.

O teste `tests/visual-prototype-smoke.cjs` usa o Electron já instalado, em renderer
oculto isolado, sem preload/nativo, e gera oito PNGs em `docs/design/previews/`.
O perfil de teste fica em `.cache/visual-prototype-tests/`. Nenhum APK é gerado,
instalado ou acessado por esse teste, e o agente não é consultado.
