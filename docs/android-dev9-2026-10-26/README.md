# Android 2.0.0-dev.9 / código 23 — candidato assinado

Build preparada após a aprovação visual oficial dos commits `86f6540` e `c1c44c8`. Nova versão disponível na sequência local, após dev.8/código 22; não existia candidato dev.9/v23. **Nenhum APK foi instalado e nenhum acesso ADB/Samsung foi realizado.**

## Artefato

- Package: `com.lonesmartroom.app`.
- Versão: **2.0.0-dev.9**, `versionCode` **23**.
- Caminho: `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.9-v23.apk`.
- Tamanho: consultar o valor exato em [tests-summary.json](tests-summary.json), campo `apkBytes`.
- SHA-256: `92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2`.
- Certificado SHA-256: `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`.
- Apksigner: assinatura válida e esquema v2 confirmado. O mesmo certificado foi conferido no APK funcional recuperado da versão 1.4.

A chave original foi utilizada exclusivamente em seu local existente para assinar a build, sem copiar arquivo de assinatura, senha ou chave privada para Git, logs ou relatórios. Este é um APK de desenvolvimento assinado; não foi produzido pacote Windows. [Recibo da assinatura e compatibilidade](apk-verification.json).

A compatibilidade é com o certificado original verificado anteriormente no Samsung. O aparelho permanece com o usuário; sua versão, assinatura e dados atuais **não foram consultados novamente nesta tarefa**. A conferência física deverá ser renovada antes de uma futura instalação.

## Conteúdo aprovado confirmado no APK

- Redesign Android já aprovado, mantendo Controles, Monitoramento PC e Gamer Launcher.
- L, O e N brancos, somente E vermelho `#FF153F`; SMART ROOM e toda a geometria preservados.
- Ícone Android proveniente do mesmo asset original Windows, nas cinco densidades e como adaptive icon.
- Cabeçalhos horizontal/compacto e splash com a marca aprovada. Android 12+ conserva sua apresentação nativa centralizada; a arte completa continua como referência visual.
- Nenhuma medição remota fictícia. Os sensores sem transporte Android permanecem indisponíveis.

As [prévias aprovadas](../design/brand/e-red-windows-icon-2026-10-26/README.md) continuam representando os assets desta build. Os 28 arquivos visuais ativos conferidos no manifesto de aprovação permaneceram byte a byte iguais durante o build.

[Inspeção compilada](resource-inspection.json): 20 recursos e referências nativas conferidos, incluindo launcher/round/adaptive, densidades, cor de fundo, splash e atributos do tema. [Comparação de pixels](compiled-pixels.json): 17 PNGs extraídos do APK com zero diferenças nos pixels visíveis e no alfa em relação às fontes revisadas. RGB de pixels totalmente transparentes foi desconsiderado por não afetar renderização. Seis assets principais da marca também foram comparados byte a byte dentro do APK.

[Teste das fontes dos ícones](icon-tests.json): símbolo crítico com raio máximo de aproximadamente 31,10 dp, dentro da área segura de 33 dp. As máscaras circular/arredondada podem recortar a moldura externa original, como mostrado e aprovado nas prévias; o símbolo permanece inteiro.

## Alterações e testes

O commit de preparação **`75d00eb` alterou somente duas linhas** de `apps/android/app/build.gradle.kts`: `versionName` e `versionCode`. Os assets aprovados foram reutilizados, sem regeneração ou mudança visual adicional. Nenhum Kotlin/Java, bridge, handler, manifesto, permissão, configuração de assinatura ou código Windows foi alterado.

| Validação | Resultado |
|---|---|
| Gradle offline `assembleDebug` e `lintDebug` | Aprovados |
| Python completo | 214 testes aprovados; zero falhas/erros |
| Renderer Android existente | 65 assertions; 15 casos responsivos |
| Safe areas/cabeçalho | 60 casos aprovados |
| Renderer da família Windows | 352 assertions; 63 casos responsivos |
| Ícones/vetores/splashes | 27 arquivos aprovados |
| Recursos nativos compilados | 20 recursos/atributos inspecionados |
| Pixels de PNGs no APK | 17 imagens aprovadas |
| WoL Kotlin em JVM | Pacote e validação aprovados; nenhum UDP enviado |
| WoL JavaScript | 11 cenários aprovados |
| Versão, permissões e estados de comandos JS | Aprovados; nenhum comando real |

As suítes têm sobreposição. Os renderers usam perfis isolados e bridges substitutas; não executam o aplicativo Windows instalado. A suíte HTTPS utiliza fixtures loopback e executores simulados, sem atingir o agente operacional.

Lint apresentou **zero erros e dez avisos existentes**, registrados em [tests-summary.json](tests-summary.json). Incluem versões de ferramenta, APIs WebView/trust manager e recursos/extração. Não foram suprimidos nem usados como motivo para enfraquecer segurança. Nenhuma ferramenta ou dependência foi instalada. Pendências TLS, Crashpad e encerramento gracioso permanecem separadas.

Reprodução local com ferramentas já existentes:

```powershell
.\scripts\prepare-compatible-apk.ps1 -SdkRoot '<SDK_ANDROID_EXISTENTE>'
.\scripts\test-android-packet.ps1
.venv\Scripts\python.exe -B scripts\verify-official-brand-apk.py --sdk-root '<SDK_ANDROID_EXISTENTE>'
```

O preparador preserva candidatos anteriores e recusa sobrescrever um candidato existente com conteúdo diferente. Uma reconstrução futura que produzir bytes diferentes deverá receber nova identificação; não substituir silenciosamente o arquivo cujo hash está neste relatório.

## Preservação

[Conferência pós-build](preservation.json): 1.338 arquivos protegidos e quatro arquivos de runtime mantiveram hashes. Banco íntegro; identidades, segredos cifrados, revogações, schema e permissões preservados. **Zero grants**.

[Recibo da release](release-preservation.json): dez APKs anteriores preservados, nenhum asset aprovado alterado. Instalação Windows dev.7, perfil de produção, backups e recuperação permaneceram intactos. Não houve nova instalação Windows ou execução física do dashboard.

[Agente](agent-after.json): supervisor e worker originais mantiveram imagens, argumentos, parentesco e horários de criação; listener único 8776 do worker esperado. Hashes da entrada Run e das regras relevantes de firewall iguais aos iniciais. Nenhum reinício, sinalização, atualização ou requisição HTTP foi feito ao agente nesta tarefa. [Conferência de processos](residuals.json): nenhum aplicativo/componente de monitoramento residual identificado.

WoL, `lone-wol-settings-v1`, origem `file:///android_asset/index.html`, DOM storage, HTTPS, HMAC, antirreplay, pinagem, certificados, credenciais, pareamento, autorizações, preferências e bloqueios permaneceram sem alterações. Não foram executados Steam, CS2, WoL real, energia ou sensores físicos. A assinatura e o package preservam os pré-requisitos para atualização; preservação efetiva dos dados no aparelho ainda exige validação física autorizada.

## Plano de atualização sem perda de dados — não executado

1. Aguardar o retorno do usuário e autorização específica para instalação. Identificar novamente o Galaxy S25 FE e seu serial, sem selecionar automaticamente outro dispositivo.
2. Conferir package, versão/código e certificado instalados. Se a assinatura divergir, se o código instalado for incompatível ou se o estado atual for inesperado, interromper. Não tentar resolver com desinstalação, limpeza ou downgrade.
3. Registrar privadamente as configurações WoL necessárias à recuperação e o estado do pareamento, sem expor credenciais. Não presumir que copiar arquivos cifrados permita recuperar chaves do Android Keystore após uma desinstalação.
4. Recalcular o SHA-256 deste APK e repetir apksigner antes de instalar.
5. Executar somente após autorização, com o serial confirmado:

```powershell
& '<SDK_ANDROID_EXISTENTE>\platform-tools\adb.exe' -s '<SERIAL_CONFIRMADO>' install -r '<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.cache\artifacts\android\LoneSmartRoom-2.0.0-dev.9-v23.apk'
```

Não acrescentar `-d`, `-g`, comandos de desinstalação ou `pm clear`. Se houver erro, parar sem repetição automática ou tentativa destrutiva.

6. Após a atualização autorizada: conferir versão 23, ícone/splash/cabeçalhos, barra de status e navegação real, três abas, rolagem e painéis. Confirmar WoL salvo e pareamento anterior; consultar somente status HTTPS, quando o agente estiver disponível, e verificar zero grants.
7. Não enviar WoL real nem executar jogos ou energia sem autorização própria. Não cadastrar novamente o dispositivo como solução automática para uma falha.

## Reversão e estado final

Em desenvolvimento, reverter o commit documental desta entrega e depois `75d00eb` restaura somente a numeração anterior; os commits visuais aprovados permanecem preservados. Não executar isso sobre o Samsung ou interpretar reversão Git como downgrade autorizado.

Depois de uma futura instalação v23, não presumir que o APK anterior possa ser instalado preservando dados. Em caso de problema, manter os dados e preparar, após diagnóstico e autorização, uma correção com código superior e mesma assinatura. Backups/APKs anteriores são recursos de recuperação, sem promessa de que desinstalação ou downgrade preservem armazenamento/Keystore.

**Estado final:** APK dev.9/v23 assinado e verificado; aplicativos instalados e agente preservados; nenhuma instalação realizada. A próxima etapa depende exclusivamente de autorização separada para validação física no Samsung.
