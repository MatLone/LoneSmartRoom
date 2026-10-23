# Atualização e validação física do Samsung — 2026-10-23

Validação posterior autorizada: o despertar após suspensão foi confirmado pelo
usuário e seguido de nova consulta HTTPS no Samsung. Consulte
[SUSPEND-WOL-TEST.md](SUSPEND-WOL-TEST.md). A pendência de despertar descrita abaixo
refere-se ao momento da instalação.

## Resultado

Após autorização expressa do usuário, foi executado exatamente o `adb install -r`
preparado no relatório anterior. ADB retornou `Performing Streamed Install` e
`Success`, com código de saída 0. Não houve desinstalação, limpeza de dados,
downgrade, mudança de identificador ou alteração de assinatura.

O Galaxy S25 FE identificado como Samsung SM-S731B agora executa
`com.lonesmartroom.app`, **2.0.0-dev.1 / versionCode 15**. O diretório de dados
permaneceu `/data/user/0/com.lonesmartroom.app`.

O APK instalado foi extraído novamente para
`.cache/validation/samsung-installed-v15.apk`. Seu SHA-256 corresponde exatamente
ao candidato autorizado:
`62188be1557c1c7097fac88cf7efcef8e397fa4fdd83c52b79e3c5fa1f6f539f`.
`apksigner` verificou a assinatura instalada com o certificado original:
`02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.

## Wake-on-LAN e interface

Antes da instalação, a configuração atual foi relida e comparada ao backup DPAPI
preparado na tarefa anterior. Não havia divergência. Uma nova cópia protegida foi
preservada em `recovery/device-settings/samsung-wol-20261023T135235452717Z.dpapi`.

Depois da instalação, antes da primeira abertura, MAC, broadcast e porta UDP foram
lidos novamente da mesma entrada `lone-wol-settings-v1` da origem `file://`.
Os três valores coincidiram exatamente com o backup anterior. Uma cópia protegida
posterior foi mantida em
`recovery/device-settings/samsung-wol-20261023T135329976826Z.dpapi`.
Os arquivos anteriores não foram apagados. Não há valores WoL nos relatórios/Git.

Após abrir, encerrar somente o processo do aplicativo e reabrir, os campos exibidos
no painel WoL foram novamente comparados em memória ao backup protegido: passaram.
Isso verifica tanto a preservação em disco quanto o carregamento pela WebView.
Não foi restaurado ou sobrescrito qualquer banco de dados.

As três abas responderam: Controles, Monitoramento PC e Gamer Launcher. Cores e
layout preto/grafite/vermelho foram preservados. Monitoramento e Gamer Launcher
continuam com os dados de demonstração existentes, identificados como tal. Não
foram acionadas funções de jogos ou cenas.

**Problema visual identificado:** o cabeçalho herdado ainda exibe “Versão 1.4”.
O Android e o APK confirmam 2.0.0-dev.1. O texto pertence ao `app.js` preservado;
não foi alterado nem foi gerado outro APK nesta tarefa. A correção deve entrar em
uma atualização posterior, mantendo os contratos WoL.

## Pareamento e status HTTPS reais

O agente continuou ativo em `172.31.161.169:8776`, com Ethernet no perfil Privado.
O Samsung utilizou seu Wi-Fi dentro da sub-rede autorizada. Nenhum túnel ADB,
redirecionamento de porta ou proxy substituiu o caminho Android–LAN–Windows.

O código temporário foi iniciado no Windows e transferido ao campo nativo de
senha do aplicativo apenas em memória pela sessão ADB autenticada. Não foi
copiado para argumentos do processo ADB no host, clipboard, arquivo ou relatório.
O fluxo de teste comparou a URL e o fingerprint exibidos pelo diálogo Android com
a identidade local do agente antes de confirmar. A resposta real HTTPS gerou uma
identidade individual autorizada; nenhum valor secreto foi exposto ao WebView.

A primeira tentativa de automação não alcançou a confirmação da identidade por
causa do posicionamento do diálogo após o teclado. Seu código foi invalidado,
sem credencial autorizada remanescente. A repetição mediu o botão depois do teclado
e concluiu a confirmação; nenhuma verificação TLS foi relaxada.

O aplicativo confirmou o pareamento, consultou `/v2/status` e mostrou **Conectado**
com a última comunicação. O agente registrou nonce da requisição autenticada da
nova identidade. A consulta foi repetida automaticamente após encerrar e reabrir
o app, sem novo pareamento. Isso valida o caminho real pelo Wi-Fi e a recuperação
das credenciais persistidas. Não comprova estado de energia; a interface continua
explicitando essa limitação.

A identidade autorizada do Samsung permanece ativa para uso normal. Só o hash
público de seu identificador está no recibo. A revogação permanece disponível no
gerenciador local Windows; não foi revogada a credencial que acabou de ser validada.

## Credenciais e bloqueio de comandos

O arquivo `no_backup/agent-v2.enc` existe, com 320 bytes. Foi lido apenas em
memória para conferir tamanho e ausência da chave secreta, tanto binária quanto
hexadecimal, no conteúdo cifrado. Não foi feito dump de credenciais em texto claro.
O código de produção utiliza AES-256-GCM e chave do Android Keystore; a conexão
autenticada após reinício do processo comprova sua persistência e uso para abrir
o cofre. Não foi realizada atestação de hardware/StrongBox, portanto esse nível
de proteção não é afirmado. O Windows continua protegendo a chave por DPAPI.

Os três botões de energia do painel — Suspender, Reiniciar e Desligar —
foram observados desabilitados, mesmo com status Conectado. Nenhum foi acionado.
O canal seguro permanece limitado a pareamento e status. Não houve execução de
comandos remotos, alterações no firewall/roteador ou no estado de energia do PC.
Os testes negativos de certificado, replay, expiração e revogação já registrados
nas etapas anteriores não foram repetidos como injeção de falhas no Samsung.

## Teste físico WoL preparado, ainda pendente

O MAC protegido corresponde à Ethernet deste Windows, a interface está ativa,
o broadcast corresponde à LAN autorizada e a porta é uma das suportadas (7/9).
Não foi enviado magic packet nem alterado o estado de energia nesta tarefa.

Para provar despertar real após esta atualização, o PC precisa estar suspenso ou
desligado. Qualquer teste que provoque suspensão/desligamento exige confirmação
separada do usuário. O envio deve partir do botão Android já disponível e independe
do agente HTTPS. Ao voltar, conferir o despertar observado e depois consultar o
status HTTPS; um retorno positivo de envio UDP não substitui a observação física.

## Evidências e limites

- Originais e recuperação: 86 registros verificados novamente, sem alterações.
- Nenhum fonte funcional foi alterado; o APK instalado é o candidato previamente
  compilado e testado. Não houve nova compilação ou instalação adicional.
- Capturas locais, sem códigos de pareamento: `.cache/validation/android-v15-controls.png`
  e `.cache/validation/samsung-connected.png` (ignoradas pelo Git).
- Hierarquias temporárias de acessibilidade foram removidas após inspeção. Seus
  conteúdos brutos não foram copiados para o Git nem impressos nos logs.
- Recibo público: `samsung-installation-results.json`. Flags de não instalação
  nos recibos internos do helper de backup descrevem somente esse helper; a
  instalação autorizada é registrada neste relatório e no recibo principal.
- Relatórios de preparação permanecem como histórico; sua autorização pendente
  foi posteriormente concedida e utilizada somente para o candidato registrado.
