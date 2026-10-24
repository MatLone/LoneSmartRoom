# Samsung — instalação oficial dev.5 / código 19

24/10/2026 · America/Sao_Paulo · branch `feature/ui-migration-preview`.
Checkpoint do projeto antes desta validação: `0c762ffe51b1efff3f6f0bafaa0f5470cd707e8e`.

**Instalação autorizada concluída com sucesso: dev.4/v18 → dev.5/v19**, no Galaxy S25 FE SM-S731B, Android 16/API 36. Uma única execução de `adb install -r`, exit code 0 e resposta Success, concluída aproximadamente às **02:39:31**. Nenhuma desinstalação, limpeza de dados, troca de assinatura, downgrade ou repetição automática.

Foi utilizado exatamente o APK **v19** autorizado nesta mensagem. A correção posterior da engrenagem permanece no repositório e no candidato dev.6/v20; **v20 não foi instalado**. O Samsung v19 usa a identidade oficial aprovada e a engrenagem anterior, conforme informado antes da execução.

## Identidade e verificações anteriores à instalação

| Campo | Resultado |
| --- | --- |
| Pacote original e instalado | `com.lonesmartroom.app` |
| Versão viva anterior | **2.0.0-dev.4 / código 18** |
| Versão instalada e extraída após atualização | **2.0.0-dev.5 / código 19** |
| Certificado SHA-256 de ambos | `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8` |
| SHA-256 do APK v19 instalado | `1acb6d927a3c8db3bb0f0a6be754d442b603a4b3b526dd79cc447e8235abd7e1` |
| Assinatura | Verificada por `apksigner`, incluindo esquema v2; instalado idêntico ao candidato autorizado |
| Identidade dos dados | UID 10368, diretório e primeira instalação preservados |
| `lastUpdateTime` informado pelo Android | 24/10/2026, 02:39:32 |

Antes de instalar foram conferidos **19 assets empacotados** contra o checkpoint aprovado `cbf90595ebb1d875c458c6cf733f4d5335bd512a`, **20 recursos nativos de ícone/splash** contra os recibos do candidato e **8 arquivos Kotlin** de segurança. Os clientes JavaScript funcionais no APK v19 são idênticos aos do v18 extraído do aparelho. HTTP global continua bloqueado e backup Android desativado. Não houve divergência de assinatura, de recursos ou de comportamento esperado em código.

O comando efetivamente executado selecionou explicitamente o Samsung validado por ADB e usou apenas `install -r` com `.cache/artifacts/android/LoneSmartRoom-2.0.0-dev.5-v19.apk`. Não foram usados flags de downgrade, desinstalação, limpeza ou troca de identidade. O serial físico não está publicado neste relatório.

## Capturas e validação visual real

[Comparativo das seis telas principais](00-validacao-real.jpg). Capturas integrais em **1080 × 2340**:

| Tela | Evidência / resultado |
| --- | --- |
| Ícone oficial na tela inicial | [01-home-lone-oficial.png](screens/01-home-lone-oficial.png), [recorte real](11-icone-home-recorte.png). Símbolo angular, LONE e SMART ROOM presentes, sem cubo e sem casa. Atalho existente preservado. |
| Splash nativa | [02-splash-nativa-real.jpg](screens/02-splash-nativa-real.jpg). Marca centralizada em fundo escuro, sem diagonais. |
| Cabeçalho e Controles | [03-controles-conectado.png](screens/03-controles-conectado.png). LONE/SMART ROOM e versão dev.5, HTTPS autenticado Conectado. |
| Monitoramento PC | [04-monitoramento.png](screens/04-monitoramento.png). Métricas explicitamente indisponíveis; nenhum valor fictício. |
| Gamer Launcher | [05-gamer-zero-grants.png](screens/05-gamer-zero-grants.png). Steam e CS2 desabilitados. |
| Painel flutuante de dispositivo | [06-painel-dispositivo.png](screens/06-painel-dispositivo.png). Abre/fecha; controles indisponíveis continuam bloqueados. |
| Conteúdo inferior e rolagem | [Controles](screens/07-controles-inferior.png), [Monitoramento](screens/08-monitoramento-inferior.png), [Gamer](screens/09-gamer-inferior.png). |
| Painel da marca | [10-painel-identidade.png](screens/10-painel-identidade.png). Arte completa da splash distingue-se da abertura nativa. |

As abas, retorno a Controles, navegação inferior fixa, rolagem e abertura/fechamento dos painéis foram verificados. Não se observou transbordamento horizontal ou conteúdo inacessível. Partes abaixo da dobra ficam acessíveis por rolagem. Não foi alterada densidade, resolução, orientação ou configuração do Samsung para produzir as imagens; a validação física corresponde a esse aparelho, sem alegar cobertura de todos os formatos Android.

Os PNGs são capturas reais sem reconstrução. A splash transitória foi extraída a **0,9 s** da [gravação real de abertura](media/abertura-real-samsung.mp4), usando os componentes oficiais Windows MediaComposition/WinRT já instalados. O JPEG é um quadro decodificado desse vídeo, sem inserir a marca artificialmente. A [proveniência](evidence/splash-provenance.json) registra arquivo, hash, método e posição. A gravação ocorreu na primeira abertura após a atualização; não houve segunda instalação ou relançamento para extraí-la.

## Preservação e comunicação

- **WoL:** o registro `lone-wol-settings-v1`, na mesma origem `file://`, foi lido antes, imediatamente depois e ao final. MAC, broadcast e porta coincidem exatamente. O painel real de conexão também exibiu os mesmos valores; não houve edição/salvamento ou captura pública desses campos. Leituras estáveis e checksums do WAL conferidos. **Nenhum pacote WoL enviado.**
- **Cofre Android:** os 418 bytes cifrados de `no_backup/agent-v2.enc` eram idênticos imediatamente após instalar e antes de abrir o app. As consultas posteriores podem atualizar a última comunicação e mudar o ciphertext; não se afirma que permaneça byte a byte igual após o uso. O cofre segue presente e o pareamento existente autenticou sem novo código.
- **HTTPS:** abertura autenticou e uma consulta manual de status também concluiu. Última comunicação exibida: **24/10/2026, 02:43:56**. Estado **Conectado**, mensagem de agente autenticado acessível e estado de energia **Não verificado**. Nenhuma ausência de resposta foi tratada como PC desligado.
- **Agente:** listener 8776 confirmado, mesmo processo **13012**, sem iniciar/reiniciar o agente. Identidade pareada e arquivos protegidos de credenciais, configuração e TLS iguais ao snapshot anterior.
- **Permissões:** **zero grants, zero comandos pendentes, histórico inalterado em quatro comandos**. Steam e CS2 aparecem desabilitados. O “Executado” no conteúdo inferior é histórico da validação anterior, não um novo lançamento nesta etapa.
- **Preservação adicional:** 86 registros de originais/recuperação aprovados. Nenhuma alteração de código Android, Kotlin, agente Windows, executores, certificados, regras de rede, firewall, drivers ou arquivos funcionais nesta tarefa.

Os resultados comprovam os dados examinados e a autenticação real; não constituem cópia completa de todos os arquivos privados do aplicativo. Não foram realizados testes reais de despertar ou abertura de programas.

## Backups locais e recuperação

Permanecem fora do Git, sem valores em texto claro publicados:

- APK vivo anterior: `.cache/validation/samsung-v19-physical/installed-before-v19.apk`.
- APK vivo posterior: `.cache/validation/samsung-v19-physical/installed-after-v19.apk`.
- WoL protegido: `recovery/device-settings/samsung-v19-wol-before-20261024T053851718998Z.dpapi`.
- Cópia DPAPI do cofre já cifrado: `recovery/device-settings/samsung-v19-vault-before-20261024T053851721897Z.dpapi`.
- APKs v14 e demais versões, backups anteriores e dumps permanecem nos locais existentes, sem exclusão.

A cópia do cofre não exporta chaves AndroidKeystore e não garante restauração após apagar dados. Nenhum downgrade ou rollback foi tentado; não se presume que versões anteriores preservem os dados automaticamente.

## Falhas, limites e pendências

1. **Nenhuma falha funcional nova observada** no escopo de abertura, navegação e consultas autorizadas. Sem erro de instalação, assinatura ou autenticação. Nenhum teste de energia ou programa foi executado.
2. **TLS conhecido preservado:** o reset intermitente para payloads excessivos continua documentado em [TLS.md](../brand/compact-review-2026-10-24/TLS.md). O serviço não recebeu correção experimental. As consultas normais bem-sucedidas não demonstram correção dessa intermitência. Não foi repetida a suíte Python nesta instalação; seus resultados anteriores permanecem registrados, incluindo falhas.
3. **Captura transitória:** uma leitura inicial do UIAutomator falhou durante a abertura; a leitura com a interface estabilizada funcionou. Não foi falha de consulta HTTPS e não houve repetição de comando funcional. O Chromium disponível não decodificou o vídeo H.264; a extração terminou localmente pelo WinRT oficial, sem instalar ferramentas. As tentativas intermediárias afetaram apenas helpers/arquivos locais de revisão.
4. **Transição visual:** a gravação registra um breve fundo escuro entre a splash e o carregamento da interface. Não foi aplicada alteração para prolongar a splash ou ocultar essa transição.
5. **Engrenagem:** a atualização explicitamente autorizada era o v19. A correção visual do v20 e seu APK permanecem preservados, sem instalação. Qualquer atualização para essa versão requer autorização própria.

## Estado final do projeto

Samsung: **dev.5/v19 instalado**. Repositório: branch `feature/ui-migration-preview`, com o avanço dev.6/v20 preservado e esta entrega acrescentando somente documentação/evidências e regra de conservação dos bytes de revisão no Git. Não foi feito reset ou checkout destrutivo para voltar o código à versão instalada.

`evidence/` contém os recibos sem credenciais ou valores WoL. `SHA256SUMS.json` registra hashes dos arquivos desta entrega. Os helpers e registros brutos permanecem na pasta ignorada `.cache/validation/samsung-v19-physical/`. Nenhuma informação foi enviada a serviços externos.
