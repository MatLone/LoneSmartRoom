# Inventário e backup Windows — 24/10/2026

Escopo autorizado: inventário somente leitura e backup local protegido. Branch `feature/ui-migration-preview`; checkpoints `ee01042` e `c51e01e` preservados. Nenhum instalador, portátil, aplicativo Electron ou jogo foi iniciado nesta tarefa. Nenhum processo existente foi encerrado.

## Conclusão da instalação

**Não foi encontrada uma instalação anterior do Electron Lone Smart Room nos registros e locais consultados.** Também não foi encontrado um perfil de produção do aplicativo. Portanto, a próxima instalação deve ser tratada como **primeira instalação desktop**, e não como atualização de uma versão instalada identificada.

| Item inventariado | Resultado |
| --- | --- |
| Desinstalação HKCU/HKLM, views 32/64 | Nenhuma entrada Lone Smart Room ou GUID esperado |
| Pacotes Appx do usuário com identidade Lone Smart Room | Nenhum |
| 15 caminhos padrão de instalação/perfil | Nenhum encontrado |
| Atalhos do usuário e públicos, Desktop/Menu Iniciar/Startup | Nenhum relacionado ao Electron ou agente |
| Processos `electron.exe`, `Lone Smart Room.exe`, `lone-smart-room.exe` | Nenhum |
| Inicialização automática do Electron | Nenhuma identificada |
| Serviços/tarefas agendadas com referência Lone Smart Room | Nenhum identificado |
| Perfil/configurações de produção Electron | Não encontrados |

Os 15 caminhos verificam os nomes `Lone Smart Room`, `lone-smart-room` e `LoneSmartRoom` em Roaming, Local, Local/Programs, Program Files e Program Files (x86). Atalhos foram examinados nos diretórios reais conhecidos do usuário e públicos. A existência de outras instalações portáteis não registradas, com outro nome ou em discos/diretórios não relacionados, não pode ser descartada por este inventário direcionado. Não houve varredura de todos os discos nem abertura de aplicativos para identificá-los.

Existem **árvores de código-fonte**, e não instalações comprovadas:

| Local em `<USERPROFILE>\Documents` | Versão do package | Identidade |
| --- | --- | --- |
| `Lone_Smart_Room_v1.3` | 1.3.0 | `lone-smart-room`, `com.lone.smartroom` |
| `Lone_Smart_Room_v1.4` | 1.4.0 | `lone-smart-room`, `com.lone.smartroom` |

Essas duas árvores não têm pasta dist. Permaneceram intactas. Os pacotes já produzidos no repositório também não demonstram que houve instalação. A pasta `AppData\Local\electron\Cache` encontrada é cache de distribuição do runtime, não um perfil Lone Smart Room, e não foi incluída no backup de configurações.

A identidade preparada para a primeira instalação permanece `com.lone.smartroom`, package `lone-smart-room`, produto Lone Smart Room, GUID NSIS `49c682c0-0c26-5957-855e-4881f73b25df`. Não há versão/caminho de uma instalação anterior a informar.

## Agente HTTPS separado

O agente Python **já está em execução** e não é a aplicação Electron:

- Listener 8776 pertencente ao PID **13012**, `C:\Python313\pythonw.exe`.
- Processo pai PID **19032**, launcher `.venv\Scripts\pythonw.exe`, associado a `agent\windows\secure_agent.py` neste repositório. São pai/filho do mesmo agente observado, não duas instâncias escutando a porta.
- Mesmo PID do listener antes/depois, sem reinício e sem chamadas à API HTTPS nesta tarefa. Isso comprova presença do listener, não uma nova validação do endpoint autenticado.
- Entrada existente `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\LoneSmartRoomSecureAgent`, apontando ao Python e script do agente no repositório. As duas views consultadas retornaram o mesmo nome/lançamento; foi contada como **uma entrada lógica**, sem criar, duplicar ou remover inicialização.
- Não houve teste de novo login, reinicialização ou funcionamento de startup: apenas a presença/configuração da entrada foi inventariada.
- Demais processos de ferramentas/prévias encontrados foram preservados. Metadados completos, sem argumentos sensíveis, permanecem no inventário privado do backup; não foram tratados como uma instalação Electron.

O banco foi consultado somente leitura: **0 grants, 0 comandos pendentes, histórico mantido em 4 comandos**. Credenciais, certificados, banco e arquivos operacionais do agente não foram incluídos neste backup de dados do Electron. Nenhuma credencial foi descriptografada.

## Backup efetivamente criado

```text
<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev3-20261024T145523Z
```

Destino fora do Git, das árvores originais, do agente e dos destinos do instalador. A pasta pai e a raiz de backup foram criadas com ACL NTFS protegida, herança externa removida e acesso exclusivo ao SID do usuário atual. Todos os arquivos/diretórios criados foram verificados quanto a proprietário e regras de acesso; não foram copiadas ACLs das fontes. A proteção aplicada é de permissões NTFS, sem criptografia adicional de arquivo.

Como não há instalação/perfil de produção identificado, foi feito **somente o backup dos dados relevantes existentes**: cinco ambientes de teste Windows Electron, cada um com diretórios profile/session. Os cinco diretórios profile estavam vazios e também foram preservados.

| Caminho relativo no repositório | Arquivos nos diretórios profile + session | Bytes |
| --- | ---: | ---: |
| `.cache/electron-smoke/` | 58 | 7192778 |
| `.cache/windows-dashboard-preview-test/` | 57 | 2941484 |
| `.cache/windows-desktop-review/1/` | 78 | 8695245 |
| `.cache/windows-desktop-review/1_25/` | 75 | 8625376 |
| `.cache/windows-desktop-review/1_5/` | 68 | 8526077 |
| **Total** | **336** | **35980960** |

Dados copiados sob `data/repository/`, preservando a estrutura relativa. São 10 raízes de profile/session e 139 diretórios correspondentes às fontes verificados, incluindo vazios. As duas cópias de metadados do inventário ficam em `inventory/`. `manifest.json`, `SHA256SUMS.txt` e `RECOVERY-NOTES.txt` complementam o backup.

Os arquivos de sessão foram copiados como bytes opacos; nenhum conteúdo de preferências, Local Storage ou credenciais foi impresso, interpretado ou descriptografado. Não é um backup do Samsung, do pareamento do agente ou de uma instalação de produção inexistente. Não importar esses ambientes demonstrativos para o futuro perfil de produção.

## Integridade e limitações

**336/336 arquivos de dados aprovados**, sem falhas de leitura/cópia, bloqueios ou mudanças detectadas durante a cópia. Hash da fonte antes, destino e fonte depois conferidos; segunda passagem independente confirmou SHA-256, tamanhos, estrutura de diretórios, cópias de metadados e ACLs. Não foi executada restauração, nem mesmo para pasta de teste.

SHA-256 do `manifest.json` privado:

```text
724eb1cd62aa884ab3af8f88d7d58df35c6e95814c6717b756aa75d2898f397f
```

O manifesto contém os hashes individuais e caminhos necessários à recuperação; ele e os dados permanecem apenas no backup protegido. No Git entram somente este relatório e recibos resumidos, sem valores de configurações ou cópia de perfis. A verificação é de consistência e integridade da cópia; não comprova restauração funcional de um perfil nem a existência de configurações de produção.

Preservação adicional: **255 arquivos de fonte/runtime/builds idênticos** ao início desta tarefa e **86 registros originais/recuperação verificados**. Android instalado não foi acessado. Sem envio WoL, jogos, energia, modificações de Registro/firewall/inicialização/drivers ou correção TLS. Apenas os novos diretórios de backup receberam ACLs.

## Conflitos e condições para prosseguir

1. Nenhuma instalação registrada conflita atualmente com o GUID novo. Revalidar imediatamente antes da futura instalação: o inventário é um retrato no tempo.
2. As fontes antigas compartilham o mesmo appId, mas não devem ser instaladas para “recuperar” uma versão anterior que não estava instalada. Portátil e instalado podem compartilhar o perfil padrão; não os abrir em paralelo ou usar o portátil como isolamento de dados.
3. **Não selecionar o repositório, projetos originais, pasta do agente, dados ou backup como destino NSIS.** A inicialização atual do agente depende do repositório. Destino proposto: `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room`, ausente no inventário. Se o assistente oferecer outra localização, revisar antes de confirmar.
4. Setup/Portable continuam NotSigned e seus hashes anteriores foram preservados. Bloqueios do Windows exigem interrupção e análise, sem desativar proteções.
5. A interface continua sem cliente operacional; a pendência TLS segue bloqueando novos clientes autenticados. Não transformar a primeira instalação visual em teste de jogos, WoL, energia ou pareamento.

[Plano específico de primeira instalação e recuperação](RECOVERY.md). Nenhuma instalação ou restauração foi autorizada/executada nesta entrega. Solicitar nova autorização antes de instalar ou abrir o pacote.

## Recibos publicados sem dados de configuração

- [Inventário resumido](evidence/inventory-summary.json)
- [Resultado da cópia protegida](evidence/backup-result.json)
- [Verificação independente](evidence/independent-verification.json)
- [Preservação de arquivos e permissões](evidence/preservation.json)
- [Estado observado do agente ao final](evidence/runtime-after.json)
- [Resumo das verificações](evidence/verification-summary.json)
- [SHA-256 dos relatórios e recibos](SHA256SUMS.txt)
