# Windows 2.0.0-dev.3 — distribuição local preparada

24/10/2026, branch `feature/ui-migration-preview`. Preparação de build: `ee010427fcf3660699997126b4868a381d118a0d`. Checkpoints preservados: `9be26ac` e `e561245`. Nenhuma instalação, execução do aplicativo empacotado ou integração operacional com o agente foi realizada.

## Pacotes entregues

Pasta na raiz do repositório: `.cache/artifacts/windows/desktop-dev3-distribution/`.

| Artefato | Bytes | MiB aproximados |
| --- | ---: | ---: |
| `Lone-Smart-Room-2.0.0-dev.3-x64-Setup-DEV.exe` | 101606378 | 96,90 |
| `Lone-Smart-Room-2.0.0-dev.3-x64-Portable-DEV.exe` | 101320255 | 96,63 |

SHA-256 do instalador:

```text
c405093ec9f45fbee8abedd3fbba103d53292cb7b57a901d5969cc74d73d0000
```

SHA-256 do portátil:

```text
b69b0cf1f13711aa4424053656c01cbadfe599a38e157835071d0b627e7f2611
```

Ambos: nome **Lone Smart Room**, versão **2.0.0-dev.3**, build de desenvolvimento para uso local, assinatura Authenticode **NotSigned**. O aplicativo contido é x64 (`PE machine 8664`); o bootstrap NSIS é x86 (`14c`), que verifica a plataforma e extrai o payload x64. Isso não é uma build do aplicativo para Windows 32 bits.

Identidade preservada: package `lone-smart-room`, `build.appId` **com.lone.smartroom**, produto **Lone Smart Room**, GUID NSIS determinístico **49c682c0-0c26-5957-855e-4881f73b25df**. Nenhuma alteração de `userData` ou nome da aplicação. Diretórios efetivos de uma instalação anterior precisam ser inventariados antes de atualizar; não foram sondados nesta tarefa.

O EXE interno e o ASAR são **idênticos em bytes** aos já validados em `e561245`:

```text
Lone Smart Room.exe: 84ecf7acdc79a03307e29c51ed3e5e556f35b7bcf460833a1095da2f516d286e
app.asar:           eba95a3adc738d2e2916ca87de6c5bff68ea9be890471ed3c8179a50b201921a
```

## Política de instalação preparada

- Assistente NSIS para usuário atual, seleção de pasta e ícones oficiais. Sem execução ao finalizar, sem atalho automático na área de trabalho e sem elevação solicitada.
- Instalação silenciosa recusada. Registro de instalação existente é examinado em HKCU/HKLM, views 32/64. Instalação de máquina bloqueia este pacote por usuário; exige plano separado.
- Uma instalação registrada do mesmo aplicativo/usuário exige confirmação adicional de substituição, com resposta padrão **Não**. O instalador padrão pode chamar o desinstalador da versão anterior após aprovação: backup e revisão do legado continuam obrigatórios.
- `deleteAppDataOnUninstall:false`; não há ações personalizadas para apagar perfis. Nunca usar `--delete-app-data` em desinstaladores. O comportamento de um desinstalador legado desconhecido não é garantido por esta configuração.
- Sem regras de firewall, serviços, tarefas, Run keys, inicialização automática, protocolos novos ou atualizador operacional.
- O assistente usa o layout padrão NSIS; logos e identidade da aplicação foram mantidas, e os wrappers/desinstalador recebem o ICO oficial. A aparência do assistente ainda não foi observada em execução.

Configuração separada de build: `apps/windows-ui/electron-builder.development.cjs` e `apps/windows-ui/build/development-installer.nsh`. O package.json funcional, runtime Electron, frontend e preload não foram modificados. A personalização utiliza o mecanismo de include do [electron-builder NSIS](https://www.electron.build/v26/docs/nsis/).

## Particularidades do portátil

É um wrapper NSIS portátil, sem registro de instalação; extrai os arquivos para uma pasta temporária e abriria o aplicativo somente quando o usuário executasse o pacote. **Não foi executado aqui.** Não é um perfil portátil isolado: mantém a identidade e o `userData` padrão da aplicação. Não testar em paralelo com uma instalação usando o mesmo perfil.

Na implementação 26.15.3 inspecionada, `unpackDirName:false` resulta em nome temporário gerado por build, não em uma garantia de isolamento de perfil nem de diretório diferente a cada execução. Não usar o wrapper como backup de dados. A preservação de nome não substitui a confirmação futura do caminho real do perfil. O [Electron documenta `userData` e o nome da aplicação](https://www.electronjs.org/docs/latest/api/app).

## Build sem executar instalador gerado

Toolchain existente: Node 22.16.0, Electron 45.0.0, electron-builder/app-builder-lib 26.15.3, NSIS 3.04, 7-Zip 24.09. Nenhuma instalação/atualização de dependência ou alteração do Windows foi necessária.

```powershell
# Na raiz, somente para produzir novos artefatos em uma saída vazia revisada:
node scripts/build-windows-distribution.cjs
```

O script recusa sobrescrever a pasta de distribuição existente. Para outra compilação, escolher/revisar uma nova saída e ajustar a inspeção correspondente, preservando esta entrega. O fluxo antigo `scripts/windows-build.ps1` não foi utilizado: ele executa npm ci e pode gravar em dist.

O fluxo NSIS padrão do builder executaria um EXE intermediário para produzir o desinstalador. O adaptador de build desta entrega mantém o template oficial e usa **UninstallerReader** do próprio builder para extrair o desinstalador estaticamente, sem esse lançamento e sem fallback para execução. O adaptador exige a versão revisada 26.15.3 e não entra no ASAR. Essa dependência de API interna precisa ser revisada quando o builder mudar.

Ferramentas de compilação/compressão foram executadas; nenhum EXE gerado da distribuição foi executado. O recibo registra executáveis auxiliares (`cmd`, PowerShell, 7za, makensis), sem argumentos ou credenciais. A API de comandos-string exec/execSync foi bloqueada no runner; isso não significa que o build não usou shells auxiliares. O log do builder escreve “signing with signtool.exe” mesmo sem assinatura: prevalecem a tabela de certificados vazia e o resultado independente NotSigned.

A primeira tentativa falhou no carregamento do NSIS dentro do sandbox (relocação de DLL). A consulta de versão e a compilação fora dele funcionaram, com o mesmo compilador e sem mudanças no sistema. A tentativa foi preservada em `.cache/artifacts/windows/desktop-dev3-distribution-attempt1/`, com seu log. O alias 7z de WindowsApps também não pôde ser executado; a inspeção usou o 7za já disponível na cache.

O procedimento é reproduzível com os insumos fixados, mas não promete EXEs externos idênticos bit a bit em novas builds: timestamps e identificadores temporários do wrapper podem variar. Os hashes desta entrega identificam os arquivos efetivamente inspecionados.

## Validação desta entrega

| Verificação | Resultado |
| --- | --- |
| Política NSIS, identidade, execução estática do desinstalador | 43 asserções aprovadas |
| Inspeção offline NSIS, 7z, ASAR e PE | 160 verificações aprovadas |
| Política Electron/preload/recursos | 49 asserções aprovadas |
| Regressão versão/permissões/estados | Aprovada, sem abrir aplicativos |
| WoL JavaScript | 11 cenários, zero pacotes enviados |
| Manifesto original e recuperação | 86 registros preservados |
| Snapshot de arquivos protegidos/builds anteriores | 255 arquivos idênticos |
| Banco do agente, somente leitura | 0 grants, 0 pendentes; histórico permaneceu em 4 |

Os dois payloads 7z passaram no teste de integridade, contêm 76 entradas e o mesmo ASAR de 22 arquivos. Foram conferidos conteúdo contra fonte, ausência de links/caminhos inseguros, chaves/certificados/bancos/configurações locais e padrões de credenciais. Os wrappers, o desinstalador e o aplicativo contêm as imagens do ICO oficial e manifests asInvoker. Os textos de consentimento e bloqueio de instalação de máquina foram encontrados no instalador compilado.

Reprodução das verificações, sem instalar ou executar artefatos gerados:

```powershell
node tests/windows-distribution-policy.cjs
node tests/windows-distribution-artifacts.cjs
node tests/electron-window-policy.cjs
node tests/version-launch-ui.cjs
node tests/android-wol-ui.cjs
.venv/Scripts/python.exe -B scripts/verify-preservation.py
```

A inspeção de artefatos somente decodifica os containers NSIS e usa o 7za de cache para testar/extrair arquivos em `.cache/validation/windows-distribution/`. Não chama o instalador nem o EXE extraído. Nenhum recurso de assinatura de produção foi utilizado.

A inspeção estática não substitui homologação física do assistente, instalação/atualização/desinstalação ou restauração de backups. Nenhum desses procedimentos foi executado. A suíte Python completa não foi reexecutada: o agente permanece intocado e a falha TLS não foi convertida em aprovação.

Minimizar, restaurar, fechar, dashboard/widget e DPI mantêm o código exato validado anteriormente nos 213 checks nativos e 27 composições. Esses testes de janela não foram repetidos sobre o pacote final nesta fase. [Relatório nativo anterior](../design/windows-desktop-integration/README.md).

## Segurança e preservação

Mantidos contextIsolation, sandbox e nodeIntegration desabilitado; preload limitado a janela/versão; CSP com `connect-src 'none'`. Nenhum transporte HTTP/HTTPS operacional, segredo do Samsung ou permissão foi adicionado. Os scripts legados continuam arquivados e sem carregamento no entry visual.

Android/APKs, WoL, agente, TLS, pareamento, certificados, credenciais, executores, backups e builds anteriores preservados. Zero chamadas à API operacional; nenhuma execução de jogos ou energia, reinício do agente, ADB ou alteração de rede/drivers/inicialização. A [pendência TLS](../design/brand/compact-review-2026-10-24/TLS.md) continua separada e bloqueia novos clientes autenticados.

- [Plano de instalação e reversão — não executar ainda](UPDATE-AND-RECOVERY.md)
- [Assinatura futura](SIGNING.md)
- [Proposta separada de bandeja e preferências](TRAY-PROPOSAL.md)
- [Inspeção dos artefatos](evidence/artifact-inspection.json)
- [Metadados e Authenticode](evidence/windows-metadata.json)
- [Preservação](evidence/preservation.json)
- [Hashes dos pacotes](PACKAGES-SHA256.txt)

Antes do teste físico: obter nova autorização, inventariar a instalação real, validar backup e revisar as limitações acima. Não executar nenhum pacote a partir deste relatório sem essa autorização.
