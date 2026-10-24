# Engrenagem — revisão visual dev.6 / código 20

24/10/2026 · branch `feature/ui-migration-preview` · checkpoint anterior `cbf90595ebb1d875c458c6cf733f4d5335bd512a`.

**Correção exclusivamente visual aplicada; APK assinado gerado, sem instalação.** A engrenagem irregular foi substituída por um contorno de seis dentes simétricos, furo central e traço de 1,7 no viewBox 24. A cor continua herdada dos controles existentes, preservando grafite/preto, vermelho da marca e contraste dos ícones. Não houve alteração de logo, ícone nativo, splash, espaçamento global ou navegação.

## Prévias para aprovação

- [Antes/depois ampliado, tamanhos pequenos e cabeçalho](00-engrenagem-antes-depois.png).
- [Interface completa antes/depois](01-interface-antes-depois.png).
- Interface após a correção: [390 × 844](390-depois.png) e [360 × 800](360-depois.png).
- Painel de conexão: [390 px](390-painel-conexao.png) e [360 px](360-painel-conexao.png); [painel de dispositivo](360-painel-dispositivo.png).
- [SVG isolado](settings-gear.svg). PNGs de 16, 17, 20, 22, 24, 32 e 192 px estão nesta pasta.

São renderizações locais da interface integrada, com bridges simuladas e sem acesso ao aparelho. As imagens de “antes” substituem somente o desenho SVG no DOM de teste; não representam reinstalação ou execução de uma versão antiga no Samsung. Nos painéis, os campos de rede foram preenchidos somente no DOM da prévia com valores fictícios, sem salvar. Nenhuma configuração real do usuário está sendo demonstrada.

## Pontos padronizados

| Local | Resultado |
| --- | --- |
| Cabeçalho Android, nas três abas | Mesma engrenagem de **22 × 22 CSS px**; botão e área de toque preservados. |
| Botão “Configurar” do cartão do computador | Mesma geometria em **17 × 17 CSS px**, herdando a apresentação existente. |
| Alias `gear` da interface Android | Reutiliza a mesma constante `settingsGear`; não há mais um desenho de documento no fallback. |
| `gear` no renderer legado Windows e cópia Android preservada | Mesma geometria SVG, substituindo apenas o literal da antiga engrenagem. Os arquivos continuam idênticos entre si. |
| Painéis flutuantes | Abertura/fechamento conferidos na prévia. Não havia outra engrenagem própria dentro deles; os controles de fechar continuam “X”. |

Os símbolos de ajustes por barras, como os sliders da navegação e da apresentação legada, não são versões da engrenagem e foram preservados. Não foi inserido nenhum botão, alterado destino de clique ou adicionado comando. O Windows não foi iniciado ou compilado nesta tarefa; sua troca consiste apenas no literal estático do desenho legado, sem instalação.

## Arquivos de implementação

- `apps/android/app/src/main/assets/mobile-shell.js`: uma constante SVG e os aliases `settings`/`gear`; código restante reconstruído e comparado com o checkpoint, sem diferenças.
- `apps/windows-ui/app.js` e `apps/android/app/src/main/assets/app.js`: somente a definição literal `gear`; nenhum handler, parâmetro, estado ou operação foi alterado.
- `apps/android/app/build.gradle.kts`: somente `versionName` dev.6 e `versionCode` 20, preservando o candidato v19 já assinado.
- `scripts/preservation_rules.py`: exceção exata e única para o literal SVG legado. Continua recusando qualquer diferença além dos dois rótulos de versão previamente aprovados e deste desenho específico.
- `scripts/verify-compatible-apk.py`: verifica essa exceção exata, sem dispensar WoL, armazenamento ou assinatura.
- `scripts/capture-gear-review.cjs`: captura local com bridges de teste e campos fictícios.
- `scripts/verify-official-brand-apk.py`: destino opcional para o recibo, evitando sobrescrever as evidências do v19.
- `.gitattributes`: preserva os bytes das evidências desta pasta para seus checksums continuarem válidos após checkout.

## APK preparado

| Campo | Valor |
| --- | --- |
| Versão | **2.0.0-dev.6 / versionCode 20** |
| Pacote | `com.lonesmartroom.app` |
| Artefato | `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.6-v20.apk` |
| SHA-256 | `793195510543ec1c676b21a929fe6f10573c18858556c91b98d94a3565027b8b` |
| Certificado SHA-256 | `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8` |

`apksigner` aprovado, incluindo assinatura v2. A chave original foi usada pela configuração local existente, sem cópia de chave ou credenciais. Package, origem WebView e contrato de armazenamento mantidos. A compatibilidade usa a assinatura original já comprovada no Samsung e no APK de recuperação; não houve nova consulta ADB ao aparelho. O APK dev.5/v19 continua preservado, com seu hash anterior.

## Validação e pendência TLS

| Verificação | Resultado |
| --- | --- |
| Compilação offline assinada + lint | **BUILD SUCCESSFUL**, 1 min 1 s; **0 erros / 10 avisos**, sem novas supressões. |
| Renderer Android | **65 asserções / 15 casos responsivos aprovados**, incluindo permissões e controles bloqueados. |
| Prévia desta revisão | 390 × 844 e 360 × 800, sem overflow; engrenagens de 22/17 px com markup idêntico. |
| JavaScript | Sintaxe, versão, estados e permissões aprovados com executores simulados. |
| Wake-on-LAN | **11 cenários JS** e pacote Kotlin de produção aprovados; zero UDP. |
| Suíte Python completa | **75/76 aprovados**, 25,075 s; um reset TLS conhecido. |
| Inspeção do APK | **20 recursos nativos** de ícone/splash conferidos. **30 entradas** de recursos e marca do APK idênticas ao v19. |
| Preservação | **86 registros** de originais/recuperação e **34 arquivos** de funcionalidade/marca inalterados; as duas cópias legadas diferem somente pelo SVG permitido. |

**A suíte global não está totalmente verde.** `test_pair_rate_limit_and_request_limit` reproduziu `ConnectionResetError / WinError 10054` durante a leitura da resposta para um corpo de 1025 bytes. Isso corresponde à pendência anterior de encerramento TLS com corpo excessivo. O log completo está em [validation/python-suite.txt](validation/python-suite.txt); o diagnóstico anterior permanece em [TLS.md](../brand/compact-review-2026-10-24/TLS.md). Não houve correção no agente, alteração de limite, autenticação, HMAC ou tolerância a reset. Não foi repetida a suíte até obter um resultado verde.

Como o script agregado para após a falha Python, os testes JS e Kotlin foram concluídos separadamente. A primeira captura isolada também parou ao esperar uma lista vazia de chamadas simuladas: havia três consultas automáticas esperadas na inicialização. O helper passou a registrar/verificar essas três chamadas de fixture separadamente; nenhum clique da revisão gerou chamada adicional. Isso não alterou o aplicativo nem ocultou uma chamada real. O perfil da prévia é isolado e nunca usa as bridges do Samsung ou o agente operacional.

Kotlin, WoL, HTTPS, pareamento, credenciais, grants, certificados e executores Steam/CS2 não foram modificados. Não houve instalação, consulta de dados do celular, envio WoL, execução de Steam/CS2, ação de energia, reinício do agente ou mudança de sistema.

## Próximo procedimento — ainda não autorizado

O candidato atual para aprovação é **v20**, substituindo v19 como proposta de atualização. Após aprovação visual e autorização expressa, será necessário revalidar o aparelho, a versão e o certificado vivos, preservar o estado e executar uma única instalação com `adb install -r` do **APK v20**, sem desinstalar ou limpar dados. Qualquer erro interrompe o procedimento; não há retry, downgrade ou correção por desinstalação. A pendência TLS continua separada e deve ser considerada antes da autorização.
