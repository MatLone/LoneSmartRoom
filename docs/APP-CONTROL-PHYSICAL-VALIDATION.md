# Atualização v16 e validação física de aplicativos

Data: 23/10/2026. Horários abaixo em America/Sao_Paulo (UTC−03:00).
Branch: `feature/secure-pairing-status`; checkpoint preservado:
`374ffec81d933bdcc15976f5df08c864d07be467`.

Recibo público verificável: [app-control-physical-results.json](app-control-physical-results.json).

## Resultado

A atualização Android e a preservação de dados passaram. O agente recebeu e
despachou o pedido autenticado para Steam, mas **a Steam não abriu e apresentou
falha de processo no Windows**. A sequência foi interrompida; **CS2 não recebeu
permissão nem foi executado**. A causa do crash permanece indeterminada.

O usuário autorizou expressamente `adb install -r`, a preparação do agente e os
testes físicos Steam → CS2, condicionados à interrupção na primeira falha. Não
houve autorização nem execução de ações de energia neste ciclo.

## Atualização Android e preservação

- `adb install -r`: `Success`, aproximadamente às 12:46. Não houve desinstalação,
  limpeza de dados, downgrade ou segunda instalação.
- Pacote instalado: `com.lonesmartroom.app`.
- Versão instalada: `2.0.0-dev.2`; `versionCode`: **16**.
- APK: `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.2-v16.apk`.
- SHA-256 do APK:
  `a6fcf7f36885777def7d55ecd758f16ccd1f907eba8dbf7105cf8404b58f62b3`.
- Certificado SHA-256 original reconfirmado:
  `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
- Cabeçalho conferido no Samsung: versão correta, proveniente dos metadados do
  aplicativo. A pendência visual “Versão 1.4” foi resolvida no aparelho.
- MAC, broadcast e porta WoL coincidiram com a base protegida antes e depois da
  atualização. Valores não foram publicados. Recibos locais:
  `.cache/validation/physical-v16-wol-before.json` e
  `.cache/validation/physical-v16-wol-after.json`; recuperação protegida por DPAPI.
- O arquivo cifrado do cofre Android, de 320 bytes, permaneceu byte a byte igual
  imediatamente após a atualização. Não houve novo pareamento ou rotação de
  credenciais. Os registros de solicitação adicionados posteriormente ao cofre
  não devem ser confundidos com essa comparação inicial.
- Após os comandos, o cofre tem 420 bytes, incluindo os metadados cifrados da
  solicitação. A chave do dispositivo não foi encontrada em texto puro nesse
  arquivo. O registro DPAPI do Samsung no Windows coincide com o backup anterior.
  Isso não constitui atestação de hardware do Android Keystore.
- Origem WebView, dados locais e configurações WoL existentes foram preservados.
  Nenhum novo teste de suspensão ou envio WoL foi realizado neste ciclo.
- Suspender, Reiniciar e Desligar continuaram desabilitados na interface,
  conforme `.cache/validation/physical-v16-power.json`.

## Agente e autorização específica

Antes da recarga, foi preservado backup consistente do SQLite e cópia protegida
da configuração e identidade TLS em:

`recovery/runtime/before-v16-app-control-20261023T154823815090Z/`

Somente o agente deste repositório foi recarregado: PID anterior `16264`, novo
PID `24880`, em sessão interativa 1, sem elevação. A porta HTTPS local continuou
`8776`, com o mesmo pin TLS e Ethernet Privada. Firewall, roteador e inicialização
automática não foram alterados.

O Samsung manteve seu pareamento e consultou status autenticado **Conectado** às
12:49:59, após a recarga. Foi concedida somente a permissão `steam` ao dispositivo
Samsung identificado. Nenhum outro dispositivo recebeu permissão e `cs2` nunca
foi concedido. Para correlação sem publicar o identificador completo, seu SHA-256:

`166cb61910bd92e530414644b88fafdc3f8c48d01f29d1bef7946fabc80ca39e`

A permissão temporária Steam foi revogada às 12:54:08, restaurando o estado
anterior sem aplicativos autorizados. Status e pareamento não foram revogados.
Na conferência final, ambos os botões de abertura ficaram desabilitados no
Samsung. A inicialização por login, a regra Privada/LAN e todos os perfis de
firewall habilitados foram novamente conferidos, sem mudanças.

## Steam: despacho confirmado, abertura física falhou

O teste usou o cartão de aplicativos autenticados, não os botões legados de
simulação. As observações anteriores ao envio não encontraram Steam/CS2 em
execução; o processo Steam existente em uma observação mais antiga já havia
encerrado antes do teste.

| Pedido | Aceito | Despachado (`executed`) | Falha registrada pelo Windows |
| --- | --- | --- | --- |
| `208a16f65b55bb17fadd6c7f59f3fafc` | 12:51:12 | 12:51:14 | 12:51:15.589 |
| `0f53580788dd8d253ed7ba7e175fbd22` | 12:53:07 | 12:53:09 | 12:53:16.278 |

Depois do primeiro pedido, não foram encontrados processo ou janela Steam/CS2;
o usuário confirmou que a Steam não abriu. A sequência automatizada foi
interrompida, sem retry nem avanço para CS2. A confirmação nativa do primeiro
pedido não foi observada diretamente pela automação.

O segundo registro corresponde a uma **nova confirmação nativa feita pelo
próprio usuário no Samsung**, conforme sua confirmação expressa. Não foi
repetição automática ou replay do primeiro ID. Esse pedido também não resultou
em abertura comprovada e registrou crash equivalente.

Os dois eventos Windows indicaram:

- Aplicativo: `steam.exe`, versão `11.15.70.27`.
- Módulo informado: `ntdll.dll`, versão `10.0.26100.9711`.
- Exceção: `c0000005`; deslocamento: `0000000000166447`.

A consulta somente leitura da associação `steam://` encontrou destino Steam
existente, placeholder da URI e assinatura Authenticode válida. A associação
não foi alterada. Esses dados não demonstram integridade de toda a instalação
nem excluem problemas de bootstrap, dependências ou estado do cliente.

**Não há causa raiz comprovada.** O módulo apontado pelo evento não deve ser
tratado isoladamente como causador do crash. Não foram alterados Windows,
drivers, configurações Steam/CS2 ou arquivos do jogo para tentar corrigir a falha.

## Segurança, limites e ocorrências

O caminho Android → HTTPS autenticado → autorização por app → fila → executor
funcionou para os registros acima. O estado `executed` significa que
`os.startfile('steam://open/main')` retornou sem exceção: não comprova processo,
janela ou aplicativo carregado. O aviso correspondente apareceu no Android.

As restrições de rede, HTTPS/pin, credenciais protegidas, HMAC e proteção contra
repetição foram mantidas. Não houve comando arbitrário de terminal pelo Android,
ação de energia, abertura CS2 ou mudança de firewall/roteador. Nenhuma senha,
chave privada ou credencial de pareamento foi publicada neste relatório.

Houve falha transitória na coleta de hierarquia da interface por ADB, resolvida
em leitura posterior. Uma checagem de orquestração também interpretou um
`LASTEXITCODE` anterior como falha após a recarga do agente; o novo processo e o
status HTTPS comprovaram a recarga. Isso não levou a segunda recarga ou instalação.

Os 86 registros de preservação de originais/recuperação passaram novamente. Os
builds e testes automatizados anteriores não foram repetidos neste turno; seus
resultados, limites e artefatos estão em [APP-CONTROL-CYCLE1.md](APP-CONTROL-CYCLE1.md).
Nenhum fonte funcional foi alterado nesta validação.

## Próximos passos

1. Revisar somente os dados técnicos pertinentes ao crash Steam e seu bootstrap,
   sem coletar credenciais ou alterar configurações. Não presumir correção.
2. Apresentar o diagnóstico antes de qualquer nova tentativa física. Novo teste
   Steam/CS2 exige revisão do resultado e autorização; CS2 continua bloqueado.
3. Considerar, em implementação futura e separada, confirmação observável de
   processo/janela e estados que distingam despacho de abertura verificada.
   Essa melhoria não foi implementada neste turno.
