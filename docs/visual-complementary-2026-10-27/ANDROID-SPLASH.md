# Splash Android — resultado da abertura normal autorizada

27/10/2026, America/Sao_Paulo. Continuação do registro `ce88c0f`, após o usuário
confirmar que fechou somente o cartão LONE nos Recentes e deixou a tela inicial
pronta. **Não houve nova sessão Windows.**

## Resultado

**Reabertura da interface confirmada; splash nativa inconclusiva.**

Uma única abertura pelo ícone oficial da tela inicial Samsung, com gravação
real por `adb shell screenrecord`, sem chamada `am start`, force-stop, limpeza,
reinstalação ou alteração de configurações. O processo LONE **21326** estava
presente antes do toque e permaneceu com o mesmo PID depois. O fechamento normal
nos Recentes não foi tratado como garantia de término do processo. Esta sessão
não demonstra um início a frio.

O vídeo mostra a tela inicial, a animação de abertura/retorno e a interface
principal com o símbolo angular vermelho e apenas o E de LONE em vermelho.
**O cabeçalho HTML não é a splash nativa.** Também não se contou o símbolo da
imagem de fundo da tela inicial como splash do aplicativo.

Nos quadros examinados não foi identificada uma tela nativa com logo centralizada.
Isso não permite concluir que a splash esteja defeituosa ou ausente em um início
a frio; tampouco permite homologá-la. Não houve tela preta persistente, overlay
preso ou travamento aparente na sequência registrada e na captura posterior.

## Evidências e tempos

| Marco | Registro |
|---|---|
| Início do procedimento de gravação | 01:07:41,259 local |
| Toque no ícone observado | 01:07:42,064 local |
| Limite solicitado ao gravador | 7 segundos |
| Duração de mídia informada pelo decodificador | **1.111,6 ms** |
| Quadros extraídos do mesmo vídeo | 12, nos offsets 0–1.100 ms |
| SHA-256 do vídeo | `55af9deeb095cf2b531a1fafd4d8978e631c2ad459986125ee621fd8570e077f` |
| Aberturas físicas nesta etapa Android | **1** |

O limite solicitado não é a duração efetiva de mídia. Não foi determinada a
causa de o arquivo expor duração menor. Os offsets dos quadros são relativos ao
vídeo; não equivalem diretamente à latência desde o toque medido no computador.
Não se inferiu tempo exato de splash a partir deles.

Na primeira extração local, o decodificador tentou ler 1.200 ms e recusou o
pedido por exceder os 1.111,6 ms da composição. Corrigiu-se somente o helper
local de leitura para respeitar a duração real. Depois foram extraídos também
os quadros iniciais do mesmo arquivo. **Não houve outra abertura para fazer a
extração passar**, nem modificação do APK ou do aparelho.

Na primeira auditoria final, a árvore de acessibilidade não expôs `platformLabel`
e o helper parou com `KeyError`. Uma leitura posterior encontrou o app e esse
campo, sem reabrir a atividade. Isso foi registrado como limitação transitória
da leitura, não como falha do aplicativo.

### Capturas reais desta abertura

- [Animação, offset de 700 ms](captures/android-reopen-700ms.jpg)
- [Interface, offset de 1.100 ms](captures/android-reopen-1100ms.jpg)
- [Interface após a gravação](captures/android-after-opening.png)

Essas imagens **não são apresentadas como splash nativa**. Não houve retoque,
montagem, geração de imagem ou substituição pela arte estática aprovada. A
gravação integral permanece no cache local, pois inclui a tela inicial fora do
aplicativo:

`.cache/validation/visual-complementary-2026-10-27/android-splash.mp4`

Os metadados sanitizados e hashes estão em `evidence/android-splash-result.json`,
`evidence/android-video-decode.json` e `evidence/android-capture-provenance.json`.

## Preservação e estado final

- Android **2.0.0-dev.9/código 23** e identidade do diretório de dados mantidos.
- WoL salvo igual à cópia protegida anterior; nenhum pacote WoL enviado.
- Cofre existente presente, sem exclusão ou novo pareamento. A comparação
  operacional Windows manteve identidade, permissões e histórico de comandos.
- A gravação mostra `Conectado`, com última comunicação **00:36:53**. Esse horário
  é anterior à abertura às 01:07; não foi apresentado como autenticação Android
  nova causada pela reabertura. Não se tocou em Atualizar status.
- O verificador local confirmou separadamente o agente original ativo, com o
  mesmo supervisor/worker, listener único 8776, GET de status autenticado HTTP
  **200**, **TLS 1.3**, hostname e pinagem validados. Banco íntegro e **zero grants**.
- Sem marcador `FATAL EXCEPTION` no buffer de crash consultado para o PID atual.
- Nenhum Electron ou componente de monitoramento Windows residual identificado.
  Não se abriu novamente a dev.7, não se ativaram sensores ou novos adaptadores.
- Nenhuma instalação, alteração de fonte, certificado, credencial, HKCU Run,
  firewall, serviço, tarefa ou driver foi realizada. Não houve jogos ou energia.

O teste Windows anterior continua **não homologado**, com a falha de captura e
prazo preservada no relatório principal; este adendo não modifica esse resultado.
TLS 10054, inicialização automática, encerramento gracioso e demais pendências
continuam abertas. Não foi investigada a inicialização automática nesta etapa.

## Encerramento e continuidade

A sessão Android autorizada foi consumida. Não se repetirá automaticamente a
abertura, nem se utilizará encerramento forçado ou alteração visual para obter
uma splash mais longa. Recomenda-se observar, mediante autorização própria, um
próximo início a frio natural. Até lá, registrar a splash como **Não verificada**.

Este registro é documental. Sua reversão em Git não reinstala, apaga dados ou
altera o agente. Manter as instalações atuais e o agente HTTPS ativo.
