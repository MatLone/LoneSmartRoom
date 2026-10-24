# Samsung — instalação física dev.4 / código 18

24/10/2026, America/Sao_Paulo. Branch `feature/ui-migration-preview`.
Base de código e documentação anterior: `aa200ab245715653e15a9dc0d4915c36e177a8f4`.

**Atualização autorizada concluída com sucesso no Galaxy S25 FE, SM-S731B, Android 16/API 36.** Uma única instalação com `adb install -r`, exit code 0 e resposta Success. Nenhuma desinstalação, limpeza de dados, downgrade ou repetição automática. O aplicativo foi aberto e validado no aparelho real; não se trata da prévia de navegador.

## Instalação e identidade

| Verificação | Resultado |
| --- | --- |
| Aplicativo anterior, extraído antes da atualização | `com.lonesmartroom.app`, dev.2 / código 16 |
| Instalado e novamente extraído após atualização | Mesmo pacote, **2.0.0-dev.4 / código 18** |
| Certificado SHA-256 de ambos e do candidato | `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8` |
| SHA-256 do APK v18 instalado | `3a61d82c2b7aa5d457d1dfcbae9365361b0692ecbb807fd7078f9e2281e1c732` |
| Assinatura | `apksigner` aprovado, incluindo esquema v2; APK instalado idêntico ao candidato |
| Atualização | Aproximadamente 01:35; `lastUpdateTime` do Android 01:35:36 |
| Identidade dos dados | UID 10368, diretório e `firstInstallTime` preservados |

O comando autorizado usou o dispositivo ADB explicitamente selecionado e o artefato `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.4-v18.apk`. O identificador físico do aparelho não está publicado nesta revisão. A assinatura original foi apenas verificada; nenhuma chave privada ou senha foi copiada ou registrada.

Antes da instalação foram reconferidos os 17 recursos de launcher empacotados e os 20 arquivos de imagem/vetor, incluindo área segura nas cinco densidades. Máscaras circular e arredondada já propostas permanecem em `../brand/nex-icon/review/01-mascaras-e-tamanhos.png`. No Samsung real, o hexágono completo aparece na máscara da One UI, sem corte visível dos vértices. A abertura pelo atalho da tela inicial também funcionou. Não foram alteradas configurações de tema, densidade ou launcher.

## Capturas reais e navegação

[Comparativo de seis telas](00-comparativo-real.jpg). Os nove PNGs em `screens/` são capturas ADB integrais, sem reconstrução ou montagem de conteúdo. Resolução: **1080 × 2340**. O comparativo apenas redimensiona essas capturas; o recorte do ícone mantém os pixels originais.

| Tela | Evidência |
| --- | --- |
| Controles, LONE e status autenticado | [01-controles-conectado.png](screens/01-controles-conectado.png) |
| Monitoramento PC | [02-monitoramento.png](screens/02-monitoramento.png) |
| Gamer Launcher bloqueado | [03-gamer-zero-grants.png](screens/03-gamer-zero-grants.png) |
| Painel flutuante de dispositivo | [04-painel-dispositivo.png](screens/04-painel-dispositivo.png) |
| Identidade interna | [05-painel-identidade.png](screens/05-painel-identidade.png) |
| Rolagem das três abas | [Controles](screens/06-controles-inferior.png), [Monitoramento](screens/07-monitoramento-inferior.png), [Gamer](screens/08-gamer-inferior.png) |
| Ícone na tela inicial real | [09-home-nex-real.png](screens/09-home-nex-real.png), [recorte](10-icone-home-recorte-real.png) |

As três abas foram selecionadas, o cabeçalho apresentou dev.4 e a logo LONE, e os painéis de conexão, dispositivo e identidade abriram e fecharam. A configuração exibida de WoL foi conferida sem editar/salvar e sem publicar seus valores. As três áreas principais foram roladas até o conteúdo inferior: navegação fixa e conteúdo acessível, sem transbordamento horizontal observado. Cartões parcialmente visíveis antes da rolagem são conteúdo abaixo da dobra. Não foi feita uma nova bateria física em outras resoluções; os testes responsivos anteriores permanecem como evidência complementar.

Monitoramento, dispositivos não integrados e NEX continuam explicitamente indisponíveis. Nenhuma leitura fictícia foi apresentada como telemetria. O resultado histórico “Executado” no final do Gamer Launcher pertence ao teste anterior; não significa lançamento realizado nesta validação.

## Preservação e comunicação

- O registro `lone-wol-settings-v1`, na origem `file://` da WebView existente, foi lido sem abrir um gravador LevelDB. MAC, broadcast e porta coincidem exatamente antes/depois e na leitura final; checksums do WAL e leitura dupla estável aprovados. Nenhum pacote WoL foi enviado.
- O cofre Android `no_backup/agent-v2.enc` tinha exatamente o mesmo ciphertext imediatamente após a atualização, antes de abrir a nova interface. Depois foram realizadas consultas autenticadas normais; a gravação de última comunicação pode mudar esse ciphertext. Não se afirma imutabilidade do cofre após essas consultas.
- O pareamento existente voltou a autenticar sem novo código ou credencial. Estado final **Conectado**, última comunicação exibida **24/10/2026, 01:55:11**, com mensagem de agente autenticado acessível. O estado de energia permanece “Não verificado”, sem inferir desligamento por ausência de resposta.
- Listener HTTPS 8776 confirmado, processo **13012**, sem iniciar ou reiniciar o agente. Credenciais protegidas, identidade do dispositivo e arquivos TLS/configuração do Windows iguais ao snapshot anterior.
- **Zero grants, zero comandos pendentes e histórico inalterado em quatro comandos**. Steam e CS2 aparecem desabilitados; não houve acionamento de aplicativos ou energia, alteração de permissões, firewall, roteador ou drivers.
- Verificação de preservação executada novamente: **86 registros aprovados**, originais e cópias de recuperação intactos. Nenhum código Android, Kotlin, agente, executor ou recurso visual foi modificado nesta tarefa física.

Isso comprova os dados examinados e a autenticação real; não é uma auditoria byte a byte de todos os arquivos privados do aplicativo.

## Recuperação local preservada

Arquivos abaixo permanecem ignorados pelo Git; valores em texto claro não foram salvos:

- APK extraído antes: `.cache/validation/samsung-v18-physical/installed-before-v18.apk`.
- APK extraído depois: `.cache/validation/samsung-v18-physical/installed-after-v18.apk`.
- WoL anterior protegido: `recovery/device-settings/samsung-wol-20261024T043344719084Z.dpapi`.
- WoL posterior protegido: `recovery/device-settings/samsung-wol-20261024T043559123595Z.dpapi`.
- Cópia DPAPI do cofre já cifrado: `recovery/device-settings/samsung-v18-vault-before-20261024T043338898873Z.dpapi`.

A cópia do cofre não exporta chaves AndroidKeystore nem constitui restauração completa após apagar dados. Não se presume que downgrade preserve dados; nenhuma recuperação ou downgrade foi executado.

## Intercorrências e pendências

1. **Texto não crítico:** o painel de identidade ainda contém “EM REVISÃO” e referência à instalação aguardando aprovação. A captura registra a inconsistência; não houve correção ou nova instalação fora do escopo.
2. **TLS separado:** o reset intermitente com payload acima do limite permanece documentado em `../brand/compact-review-2026-10-24/TLS.md`. A conexão física bem-sucedida não resolve essa intermitência. O agente operacional não foi alterado.
3. A primeira coleta de rolagem encontrou o celular fora do aplicativo; os gestos foram interrompidos pela verificação da interface. Após sua confirmação, as capturas foram refeitas e validadas. Imagens da lista de aplicativos não foram publicadas como telas do Lone Smart Room.
4. A revisão automática de aprovação rejeitou o toque para adicionar o atalho, por alterar a organização persistente da tela inicial e não haver confirmação suficiente do alvo. Nenhum toque dessa operação foi executado. Você adicionou o atalho manualmente e confirmou; então foram feitas apenas a captura e a abertura por ele. Não houve tentativa de contornar a rejeição.
5. O leitor de metadados foi adaptado apenas no helper ignorado para consultar UID por `pm list packages -U` no Android 16. Nenhum código funcional foi alterado. Não foi observado crash do aplicativo durante a validação.

Não foram repetidos os testes físicos de despertar, Steam ou CS2. Os resultados automatizados **74/74 Python**, **65 asserções/15 casos responsivos**, **11 cenários WoL**, Kotlin sem UDP e build/lint aprovados pertencem à preparação deste mesmo APK e estão em `../brand/nex-icon/validation/`; não são apresentados como nova execução integral nesta instalação. Nesta etapa foram repetidas a inspeção do APK, a verificação de imagens e os 86 registros de preservação, além dos testes físicos descritos.

## Evidências e próximo passo

`evidence/` contém resultados estruturados sem credenciais ou valores WoL; `SHA256SUMS.json` registra os hashes e dimensões dos arquivos entregues. Os helpers e registros brutos locais permanecem em `.cache/validation/samsung-v18-physical/`.

Próximo passo: revisar a aparência no uso diário e aprovar uma correção apenas dos textos pendentes. Testes reais de WoL ou de launchers exigem autorização própria; a instalação não os executou nem concedeu permissões para eles.
