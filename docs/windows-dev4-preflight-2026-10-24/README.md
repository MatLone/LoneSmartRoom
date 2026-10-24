# Pré-instalação Windows dev.4 — 24/10/2026

**Preparação concluída; atualização não executada.** A instalação permanece **2.0.0-dev.3**. Nenhum Electron, NSIS ou portátil foi iniciado nesta tarefa. O agente não foi iniciado, reiniciado ou modificado. A atualização dev.4 exige autorização específica posterior.

Branch `feature/ui-migration-preview`, sobre `ced82d08a31d4bb06c39c450109c38cbfd6957c8`, preservando `3d56561` e checkpoints anteriores. As únicas alterações versionadas desta tarefa são documentação, recibos de verificação e verificador de backup. Código funcional e pacotes não foram alterados.

Horários locais neste relatório: America/Sao_Paulo, UTC−03:00. Recibos JSON conservam UTC. Última consulta de processos/listener: **16:42:39 de 24/10/2026**. Estes resultados são um retrato desse momento; repetir verificações antes da futura instalação.

## 1. Instalação e dados existentes

| Item | Resultado confirmado |
|---|---|
| Executável | `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe` |
| Versão / produto | `2.0.0-dev.3` / Lone Smart Room |
| Identidade | `com.lone.smartroom`; pacote `lone-smart-room` |
| Registro NSIS | GUID `49c682c0-0c26-5957-855e-4881f73b25df`, instalação por usuário em HKCU |
| Destino registrado | Caminho acima, confirmado em ambas as visões do Registro; uma instalação lógica |
| Perfil de produção | `<USERPROFILE>\AppData\Roaming\Lone Smart Room` |
| Perfil inventariado | 72 arquivos, 26 subdiretórios, 8.589.376 bytes; sem pontos de nova análise |
| Preferências dev.4 | `desktop-window-state.json` ainda não existe no perfil dev.3 |
| Processos Electron | Nenhum nas consultas inicial e final |
| Integridade instalada | 76 arquivos comparados com os registros anteriores, sem divergências |
| Atalho existente | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Lone Smart Room.lnk`, preservado |
| Authenticode | `NotSigned` |

SHA-256 do executável dev.3 instalado: `84ecf7acdc79a03307e29c51ed3e5e556f35b7bcf460833a1095da2f516d286e`.

O perfil fica fora da pasta de instalação e inclui Local State, armazenamento e sessões do Electron. O conteúdo não foi exibido ou descriptografado. Os arquivos `.log` encontrados em Local Storage/Session Storage são journals LevelDB, não logs de diagnóstico. Não foram importados perfis demonstrativos nem encerrados processos. Não foi encontrada instalação concorrente em HKLM na inspeção do instalador.

O Electron e o agente Python são componentes distintos. Dados privados do agente permanecem em `.runtime/secure-agent` no repositório; essa pasta não pertence ao perfil Electron e não é incluída no instalador.

## 2. Novo backup do perfil de produção

**Local:**

`<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev4-20261024T174801Z`

Criado às **14:48:01**, fora do Git e da instalação. Contém `data/profile/`, estrutura de diretórios, `manifest.json`, `SHA256SUMS.txt` e `RECOVERY-NOTES.txt` privados. Totais: **72 arquivos de dados, 27 diretórios incluindo a raiz do perfil, 8.589.376 bytes**.

- Todos os arquivos de origem foram mantidos abertos para leitura com `FileShare.None` durante a cópia, recusando arquivos em uso; nenhum ficou bloqueado ou foi forçado. A lista de arquivos/diretórios foi revalidada e não havia Electron ativo.
- Hash da origem antes/depois e hash da cópia coincidiram; nenhuma alteração nos arquivos originais.
- Raiz do backup com herança removida, proprietário e permissão FullControl apenas para o usuário atual; descendentes com acesso privado herdado. ACLs da origem não foram alteradas. O diretório pai privado já existente apenas foi verificado.
- Nenhuma credencial foi descriptografada. Conteúdo opaco do perfil foi preservado sob ACL restrita. ACL não é criptografia adicional; recuperação de material protegido pelo Windows pode depender da mesma conta e máquina.
- Verificação independente: **aprovada**, incluindo tamanhos, SHA-256, diretórios e ACLs; zero problemas de cópia. Nenhuma restauração executada.

SHA-256 esperado do `manifest.json` privado:

`13c12ff4d0e896dda9915b4d8d9b337aa480565059e844ac6bc41a9932444dcc`

O verificador [Verify-ProfileBackup.ps1](Verify-ProfileBackup.ps1) é somente leitura, já foi executado com sucesso e não restaura, descriptografa ou inicia software. O manifesto privado e o perfil **não foram incluídos no Git**.

O backup anterior `Windows-before-dev3-20261024T145523Z` também foi preservado e revalidado: **336 arquivos, 139 diretórios, 35.980.960 bytes**, hashes e ACLs corretos. Ele contém perfis isolados anteriores; **não deve ser importado como perfil de produção**. O backup novo é a referência para recuperar o perfil instalado atual. Os binários instalados não foram duplicados nesse backup de perfil; o NSIS dev.3 preservado e verificado fornece os arquivos de aplicação para uma recuperação futura autorizada.

## 3. Agente HTTPS offline: evidências e limites

**Confirmado:** nenhum processo do agente e nenhum listener em **8776** nas consultas desta tarefa. Zero grants ativos, quatro comandos históricos e nenhum pendente, por consultas SQLite estritamente de leitura e apenas contagens. Dois dispositivos registrados, um não revogado; nenhuma identidade ou segredo foi exposto.

Linha do tempo:

| Horário local | Evidência |
|---|---|
| 13:32:08 | Último registro funcional anterior: listener 8776, PID 13012, Python 3.13; processo anterior criado em 23/10 às 21:22:53 |
| 14:09:07 | System/User32 1074, seguido de EventLog 6006 e Kernel-General 13 |
| 14:09:40 | Kernel-General 12 e LastBootUpTime confirmam novo boot; EventLog 6005 às 14:09:53 |
| Preparação posterior e 16:42:39 | Agente ausente, sem listener |

O reboot confirmado encerrou o ciclo de vida do processo anterior. **Não foi determinada a causa de o agente não permanecer ativo após o login**. Esta tarefa não executou ações de energia; não foram coletados autor ou motivo da reinicialização.

Verificações de leitura:

- Entrada HKCU Run `LoneSmartRoomSecureAgent` idêntica ao último estado funcional, com launcher `.venv\Scripts\pythonw.exe` e `agent\windows\secure_agent.py serve`. Launcher, Python base `C:\Python313\pythonw.exe` e script existem.
- Nenhuma entrada correspondente encontrada em StartupApproved nas áreas consultadas. Isso não comprova execução, habilitação ou bloqueio no login.
- Configuração DPAPI, material TLS protegido, certificado público e chave existente mantêm os hashes do último estado funcional. Não foram descriptografados. Validade temporal do certificado público correta; SAN de IP corresponde a adaptador local cujo perfil atual é Privado. Isso não comprova disponibilidade da rede durante o login.
- Não há `.log` persistente em `.runtime/secure-agent`. O código atual não mantém um log persistente de diagnóstico para falhas de inicialização; uma exceção não tratada em `pythonw` é uma hipótese, sem erro concreto encontrado.
- Não há hash histórico de `devices.db` nos snapshots anteriores: comparação entre etapas é **inconclusiva**, não uma divergência. O hash coletado no início e no fim desta tarefa coincide.
- Nenhum evento Application Error/WER/.NET/hang correlacionado encontrado no intervalo consultado. Sem iniciar o processo ou descriptografar a configuração, não é possível validar abertura DPAPI, bind TLS ou capturar uma eventual exceção atual.

**Próximo diagnóstico separado:** autorização futura para uma inicialização controlada do agente com observação local e sem grants, se desejado. Não faz parte da atualização visual e não foi executado. Nenhuma configuração de rede, inicialização, serviço, credencial ou tarefa OneSettings\RefreshCache foi modificada.

## 4. Janela transitória “Error”

Foram consultadas evidências existentes da revisão dev.4, sem executar novamente nenhum pacote. O inventário de janelas daquela revisão associou uma janela intitulada `Error` ao runtime de desenvolvimento `apps/windows-ui/node_modules/electron/dist/electron.exe`. Ela desapareceu antes de capturar conteúdo ou recuperar PID, stack ou mensagem.

A primeira sessão tinha stdout `Isolated Tray review ready`, stderr vazio e encerramento normal por X (código 0). A sessão posterior do menu nativo também encerrou por Sair com código 0, destruiu o Tray e não registrou repetição da janela. Essa associação do observador **não determina a origem ou a causa do erro** e não o relaciona ao NSIS.

Nos canais existentes Application, WER, CodeIntegrity, AppLocker e Defender não foram encontrados registros correlacionados nas consultas realizadas; não houve falha de leitura registrada. Nenhum canal ou coleta de dumps foi habilitado. Ausência de eventos não exclui erro JavaScript tratado ou uma caixa de diálogo sem registro persistente.

**Conclusão:** origem inconclusiva; nenhum bloqueio de instalação foi comprovado por essas evidências. Não equivale a garantir ausência de defeito. Preservar a pendência e observar a primeira execução futura, mediante autorização, registrando imediatamente texto, horário e processo se a janela reaparecer. Não reproduzida nesta tarefa.

## 5. Integridade dos pacotes dev.4

Pasta preservada: `.cache/artifacts/windows/desktop-dev4-tray-distribution/` no repositório.

| Pacote | Tamanho exato | SHA-256 |
|---|---:|---|
| `Lone-Smart-Room-2.0.0-dev.4-x64-Setup-DEV.exe` | 101.606.566 bytes | `e54710fa58103e8c0573f0d1dabbf7ed7e68b3abcc5eda3d85f4305ab32c3570` |
| `Lone-Smart-Room-2.0.0-dev.4-x64-Portable-DEV.exe` | 101.320.430 bytes | `0fd73fb56ddbf56d84e80ac9a03ab25d2e84e7d740fbb5278e0ef408c6f84075` |

**172 verificações offline aprovadas**: integridade dos arquivos e payloads extraídos, aplicativo x64, versão, sete imagens no ICO oficial, 24 arquivos ASAR correspondentes às fontes revisadas, identidade, strings de consentimento NSIS e varredura de material privado. Nenhum certificado privado, token, senha, identidade Samsung, base local ou pasta do agente foi encontrado no payload revisado. Bootstrap NSIS x86 envolvendo aplicação x64 é esperado.

Ambos os pacotes estão **sem assinatura Authenticode (`NotSigned`)**, destinados a desenvolvimento local. Hash comprova correspondência ao artefato revisado, não identidade de um editor certificado. Não desativar ou contornar SmartScreen, Defender ou políticas; interromper se bloqueado.

A primeira execução do verificador copiado encontrou apenas a ausência do recibo `build-execution.json` na pasta de inspeção. O recibo anterior foi copiado sem alteração e a inspeção completa passou. Isso não representou execução ou falha de instalação do pacote.

### Estratégia de atualização inspecionada

- Mesmo appId, nome, GUID NSIS, diretório registrado e perfil. Configuração assistida por usuário, sem elevação ou helper de elevação.
- `oneClick:false`, `runAfterFinish:false`, `deleteAppDataOnUninstall:false`; sem criação automática de atalho desktop, serviços, firewall ou autostart.
- Macro própria recusa instalação silenciosa ou concorrência por máquina e exige confirmação explícita para substituir aplicação existente, com resposta padrão Não.
- Templates locais do electron-builder 26.15.3 confirmam que a atualização assistida chama **internamente o desinstalador anterior** para substituir os arquivos da aplicação, com `/S /KEEP_APP_DATA` e `--updated`. Isso é parte do mecanismo NSIS, não um comando manual de desinstalação a executar nesta preparação. Não usar `--delete-app-data`.
- Não há migração/limpeza de perfil na aplicação. A revisão estática sustenta preservação dos dados, complementada pelo backup; o comportamento dinâmico da atualização ainda depende de teste autorizado.
- X continua encerrando normalmente; preferência preparada `minimizeToTray` padrão **false**. Nenhuma preferência de produção foi criada ou ativada.
- Electron continua sem cliente operacional do agente, com isolamento, API preload limitada e CSP `connect-src 'none'`; não cria identidade, grant ou credencial desktop.

## 6. Validação e preservação

| Verificação desta preparação | Resultado |
|---|---|
| Backup novo + verificador independente | Aprovados; 72 arquivos, tamanhos, hashes e ACLs |
| Backup anterior | Aprovado e preservado |
| Instalação dev.3 | 76 arquivos comparados, sem divergência |
| Inspeção offline dos pacotes dev.4 | 172 verificações aprovadas; sem executar binários gerados |
| Comparação antes/depois | **1.257 arquivos protegidos inalterados** |
| Originais e cópias de recuperação | **86 registros do manifesto aprovados** |
| Grants / comandos pendentes | **0 / 0**; quatro comandos históricos inalterados |
| Processos/listener finais | 0 Electron, 0 listener 8776; agente não iniciado |

O conjunto protegido inclui instalação, perfil, backups anteriores, pacotes, Android e estado/código do agente. Nenhum novo teste funcional de Steam, CS2, WoL ou TLS foi realizado; as verificações não substituem validação física posterior. Android instalado, executores, pareamento, certificados e credenciais permanecem preservados. A pendência TLS sobre requisições excessivas/ambíguas **continua aberta e separada**, sem correção aplicada e sem integração operacional de novos clientes.

Uma tentativa de consulta final não chegou a executar por limite de uso da revisão automática de aprovação. Após o usuário solicitar continuação, a mesma revisão permitiu as consultas finais, concluídas com sucesso. Nenhuma proteção foi contornada.

## 7. Riscos e próximo passo

1. Authenticode ausente: eventual bloqueio do Windows deve interromper a instalação.
2. Agente offline sem causa de startup confirmada: funcionalidade remota indisponível; independente da atualização visual.
3. Janela Error inconclusiva: exige observação na primeira execução futura; sem reprodução nesta etapa.
4. Instalação NSIS sobre dev.3 ainda não executada: repetir inventário/backup se o perfil mudar; verificar dados após atualização antes de abrir a interface.
5. Backup local sob ACL privada não substitui cópia externa criptografada e pode depender da conta Windows para dados protegidos. Nenhuma transferência foi realizada.

O procedimento completo está em [UPDATE-AND-RECOVERY.md](UPDATE-AND-RECOVERY.md). **Aguardar autorização específica para executar somente o NSIS dev.4 assistido e inspecionar os arquivos após a atualização, sem abrir o aplicativo automaticamente.** Não há instalação ou restauração em andamento.
