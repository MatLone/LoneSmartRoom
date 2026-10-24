# Primeira instalação Windows dev.3 — 24/10/2026

**Instalação NSIS concluída, código de saída 0. O dashboard instalado não foi aberto.** Instalação assistida para o usuário atual, sem argumentos de linha de comando, modo silencioso ou elevação. Foi executado apenas o Setup expressamente autorizado; o portátil e o desinstalador não foram executados.

## Identificação e pré-verificação

- Produto/versão: **Lone Smart Room 2.0.0-dev.3**.
- Setup: `Lone-Smart-Room-2.0.0-dev.3-x64-Setup-DEV.exe`, 101606378 bytes.
- SHA-256 autorizado e conferido novamente imediatamente antes do lançamento: `c405093ec9f45fbee8abedd3fbba103d53292cb7b57a901d5969cc74d73d0000`.
- Destino inexistente e nenhuma instalação anterior registrada antes da execução. Não houve substituição de versão anterior.
- Marca/ícones confirmados pela inspeção offline já registrada do mesmo instalador com hash idêntico; recursos novamente conferidos após a instalação.
- Backup validado antes/depois: `Windows-before-dev3-20261024T145523Z`, fora do repositório, ACL exclusiva do usuário, manifesto SHA-256 `724eb1cd62aa884ab3af8f88d7d58df35c6e95814c6717b756aa75d2898f397f`.
- Configuração NSIS auditada: `runAfterFinish:false`, sem scripts de agente, firewall, serviços ou inicialização automática. O assistente final não apresentou opção para executar a aplicação.

## Caminho definitivo e identidade

```text
<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe
```

Instalação registrada em **HKCU**. GUID NSIS `49c682c0-0c26-5957-855e-4881f73b25df`; localização conferida na chave própria da aplicação. As duas views consultadas mostram o mesmo registro lógico. AppUserModelID do atalho: **com.lone.smartroom**, preservando o identificador Windows. Package interno: `lone-smart-room`.

Metadados do EXE instalado: ProductName Lone Smart Room, FileVersion **2.0.0-dev.3**, ProductVersion numérico **2.0.0.0**. O package do ASAR confirma a versão completa **2.0.0-dev.3**. Não foi necessário executar o EXE para obter esses dados.

**Authenticode: NotSigned**, tanto no aplicativo quanto no desinstalador. Não houve assinatura simulada, mudança de proteção, desbloqueio de arquivo ou contorno de aviso de segurança.

## Integridade instalada

| Verificação | Resultado |
| --- | --- |
| Arquivos do payload Electron | **74/74 idênticos** à distribuição aprovada |
| Arquivos internos do ASAR | **22 verificados**, comparados com as fontes correspondentes |
| Logo, símbolo e ícones oficiais | SVG, PNG e ICO presentes e iguais à fonte |
| Arquivos adicionais do NSIS | Somente desinstalador e `uninstallerIcon.ico` |
| Preload/isolamento | contextIsolation/sandbox ativos; nodeIntegration desabilitado |
| Comunicação operacional | Ausente; CSP renderer mantém `connect-src 'none'` |
| Perfis de produção | Não criados nesta instalação sem primeira execução |

SHA-256 do EXE instalado:

```text
84ecf7acdc79a03307e29c51ed3e5e556f35b7bcf460833a1095da2f516d286e
```

SHA-256 do `resources\app.asar` instalado:

```text
eba95a3adc738d2e2916ca87de6c5bff68ea9be890471ed3c8179a50b201921a
```

São os mesmos hashes do aplicativo previamente validado em desenvolvimento. A inspeção utilizou leitura de arquivos, metadados PE, ASAR e atalhos; não abriu o aplicativo nem ativou seu cliente.

## Atalhos e configuração do sistema

Foi criado **um atalho no Menu Iniciar**:

```text
<USERPROFILE>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Lone Smart Room.lnk
```

Destino: executável instalado, diretório de trabalho igual à pasta de instalação, sem argumentos adicionais e com ícone do EXE oficial. O atalho não foi aberto. Não houve atalho novo na área de trabalho ou Startup; os atalhos preexistentes permaneceram iguais.

Snapshots somente leitura antes/depois confirmaram:

- **34 leituras de entradas Run/RunOnce** em hives/views: nenhuma adição, remoção ou alteração de valores.
- Diretórios Startup: nenhuma alteração.
- **204 tarefas agendadas**: mesmos nomes, ações e propriedades de gatilhos inventariadas.
- **325 serviços**: mesmos nomes, caminhos e modos de início inventariados.
- **717 regras de firewall**: mesmos nomes, estados, direções, ações e perfis inventariados; nenhuma regra adicionada/removida.

Os registros de instalação/desinstalação e o atalho do próprio aplicativo são alterações esperadas do NSIS. Nenhuma chave foi editada manualmente pelos scripts de conferência. Não foi configurada inicialização automática do Electron.

## Agente e preservação

- Agente HTTPS continua com listener na porta **8776**, PID **13012**, mesmo processo/data de criação antes e depois. Não houve início, encerramento ou reinício do agente.
- A entrada de inicialização já existente do agente permaneceu com o mesmo valor. Ela é independente do Electron instalado.
- **0 grants, 0 comandos pendentes, histórico de 4 comandos sem alteração**.
- **255 arquivos protegidos** de fonte/runtime/builds sem mudanças.
- **336 arquivos de sessões anteriores** inalterados; nenhum perfil demonstrativo importado.
- **341 arquivos totais do backup** inalterados, incluindo os 336 arquivos de dados e metadados auxiliares. ACLs e estrutura do backup novamente validadas: 139 diretórios correspondentes às fontes.
- **86 registros de originais/recuperação** conferidos sem alterações.

Nenhum acesso ao Samsung/ADB, envio WoL, jogo, comando de energia, alteração de driver/rede, restauração ou rollback. Nenhuma credencial foi descriptografada ou copiada para o pacote. Sem requisições à API operacional. A presença do listener não constitui uma nova validação de status autenticado; essa consulta não fez parte desta instalação.

A pendência de tratamento TLS permanece documentada e inalterada. Nenhum cliente desktop autenticado foi habilitado e nenhuma correção experimental foi aplicada.

## Evidência visual e ocorrências

- [Destino confirmado no assistente real](screenshots/01-destino-nsis.jpg)
- [Conclusão real, sem opção para abrir o app](screenshots/02-conclusao-nsis.jpg)

Capturas nativas da janela específica do instalador, em JPEG, sem recriação visual. O assistente NSIS utiliza sua arte padrão, com ícone oficial; estas imagens não representam execução do dashboard.

Nenhum alerta ou bloqueio de Defender/SmartScreen/Windows foi observado durante a instalação. As proteções não foram alteradas. Houve um timeout inicial de aprovação da ferramenta Computer Use; a observação foi recuperada uma vez, sem novo lançamento do instalador ou contorno de segurança. Uma captura inicial ocluída não foi usada como evidência; as imagens salvas foram obtidas após ativar a janela correta. Não houve falha do NSIS.

O assistente foi fechado pelo botão Concluir e retornou **exitCode 0**. Depois do fechamento, não restavam janela/processo do instalador nem janela/processo do dashboard. O comportamento na primeira abertura, inclusive eventual bloqueio do Windows nessa abertura, permanece não testado.

## Próxima autorização necessária

[Procedimento proposto para a primeira abertura visual](FIRST-RUN.md). Não abrir o EXE ou o atalho antes dessa autorização. A instalação não concede autorização para ações remotas, login automático, grants ou comunicação operacional.

Recibos publicados sem valores de configurações: [pré-verificação](evidence/preflight.json), [saída NSIS](evidence/installer-exit.json), [inspeção instalada](evidence/installed-inspection.json), [metadados](evidence/installed-metadata.json), [manifesto de arquivos instalados](evidence/installed-files-manifest.json), [preservação antes/depois](evidence/post-install-preservation.json) e [atalho](evidence/shortcuts-inspected.json). Snapshots detalhados de outros programas/serviços ficaram apenas na cache local e não foram adicionados ao Git.
