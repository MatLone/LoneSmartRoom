# Licenças — avaliação interna local da dev.7

Fonte principal: [acordo original ADLX no repositório](../../third_party/adlx-v1.4/ADLX%20SDK%20License%20Agreement.pdf),
revisão oficial fixada `66557d410ce4c463f5f7106597d94f53dd84bc82`.
O SHA do PDF corresponde ao manifesto upstream preservado; a cópia dentro do
runtime e dos pacotes é idêntica. [Recibo](evidence/license-review.json).

Os oito textos de página foram extraídos localmente com ferramenta já disponível.
A revisão focou definições, licença, distribuição/EULA e Schedule A/B. Tentativa
de abrir a mesma revisão pelo serviço web retornou content-type não suportado;
a análise utilizou o original local fixado por hash, sem substituir ou baixar SDK.

- Seção 1.6 restringe a finalidade licenciada a software para hardware AMD apropriado.
- Seções 2(a)/(b) tratam do uso/cópia/desenvolvimento internos.
- Seção 2(c) e seção 3 condicionam distribuição de objetos incorporados ao software
  a produtos AMD e acordo de usuário final compatível, incluindo Schedule B.
- Não é licença MIT. A inclusão de um aviso ou do PDF não satisfaz sozinha todos
  os requisitos de distribuição a terceiros. Publicação precisa de revisão
  específica/EULA adequada; esta entrega não a aprova.

Mantém-se o escopo existente de avaliação interna local pelo proprietário. Ponte
própria compilada contra interfaces oficiais; helper/samples não linkados.
Não se redistribuem fontes/headers SDK ou a DLL do driver. O runtime ADLX deve
estar previamente instalado e é verificado no System32. Nada altera seu driver.
O acordo completo e os avisos estão incluídos, sem aceite em nome de terceiros.

CPython mantém a licença original; Electron/Chromium mantêm seus arquivos de
licença. DLLs do runtime Microsoft são as já presentes no snapshot autorizado;
não há instalador de runtime. Os componentes independentes conservam seus termos.
Uma distribuição pública exige também revisar essas condições, não só ADLX.

Esta é uma conferência técnica dos termos do pacote para o uso delimitado, não
uma liberação geral de redistribuição. Nenhuma licença original foi modificada.
