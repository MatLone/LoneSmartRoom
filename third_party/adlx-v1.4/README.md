# AMD ADLX V1.4 — fontes oficiais para uso local

Origem: https://github.com/GPUOpen-LibrariesAndSDKs/ADLX

Revisão fixada: `66557d410ce4c463f5f7106597d94f53dd84bc82` (tag V1.4).
`manifest.json` registra URL, tamanho e SHA-256 de cada arquivo original, sem alterações.
Inclui somente headers necessários, dependências transitivas, helper C++ de referência
e a licença oficial completa. Nenhuma DLL ou instalador foi baixado.

O SDK está sujeito a **ADLX SDK License Agreement.pdf**, preservado integralmente.
Não foi reclassificado como MIT/open source. Esta incorporação é para desenvolvimento
interno no repositório local; não houve publicação ou redistribuição. Antes de uma
distribuição futura, avaliar os requisitos de licença aplicáveis ao pacote e à EULA.

O helper upstream é preservado para referência e **não é compilado/linkado**: seu
loader usa o nome da DLL. O projeto usa o loader próprio em `native/adlx/bridge.cpp`,
com caminho System32 fixo, assinatura, hash e arquitetura verificados.

Headers contêm declarações de outras interfaces do SDK. Isso não as expõe: a ponte
compila somente consultas de GPU/performance e lifecycle da própria sessão; não
obtém serviços de tuning nem chama setters. Não alterar estes arquivos upstream;
as regras e adaptações ficam no código do projeto.
