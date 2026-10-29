# Artefatos OpenRGB r2 — NÃO INSTALAR antes de homologação física

Implementação: `d0a479c`. Versão 2.0.0-dev.9; appId `com.lone.smartroom`; aplicação x64, bootstrap NSIS/portátil PE x86. Authenticode: **NotSigned**. Nenhum artefato gerado foi executado.

566 inspeções offline aprovadas, mais conferência de 21 recursos ASAR, runtime e 7 imagens do ícone oficial. Os 76 arquivos ASAR foram comparados ao código-fonte durante a inspeção completa. A varredura de nomes/conteúdo não encontrou padrões de credenciais ou chaves privadas.

Pasta: `.cache/artifacts/windows/desktop-dev9-openrgb-candidate-r2/`.

## Setup

Lone-Smart-Room-2.0.0-dev.9-x64-OpenRGB-Candidate-Setup.exe

Tamanho: 105,815,300 bytes.

SHA-256: `8e49a4237187de844c33633d9170ecd31d2e13a3f1a69fed549e7539fa691992`

## Portable

Lone-Smart-Room-2.0.0-dev.9-x64-OpenRGB-Candidate-Portable.exe

Tamanho: 105,524,302 bytes.

SHA-256: `16da501c009fee994f04068223cc6148decf6898d5a242d25b1b06102876f1f6`

## Arquivos alterados

Novos módulos: `openrgb-sdk.cjs`, `rgb-control.cjs`, `rgb-renderer.js`, `nex-rgb.cjs`. Integração: `desktop-main.cjs`, `desktop-policy.cjs`, `preload.cjs`, `focused-renderer.js`, `workbench-service.cjs`, `windows-inventory.ps1`, `workbench.css`, `index.html` e lista de empacotamento em `package.json`. Configuração separada de build e scripts de build/inspeção receberam o alvo `--openrgb`. Testes novos de SDK, controle, DOM e NEX, fixture de peer simulado e atualização do teste da bandeja. Script físico de execução única mantém seu marcador consumido.

Reversão do código: `git revert d0a479c`, somente na branch de desenvolvimento e após preservar eventuais mudanças posteriores. Não há instalação a reverter. Não apagar recibos ou backups.
