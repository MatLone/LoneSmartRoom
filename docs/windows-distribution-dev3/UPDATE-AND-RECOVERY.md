# Plano de atualização e reversão — preparado, não executado

Todos os passos abaixo são futuros e dependem de nova autorização. Não foi feita leitura do inventário de programas instalados, cópia de perfis em uso, alteração no Registro ou instalação nesta entrega.

## 1. Inventário antes de qualquer atualização

1. Identificar com o usuário qual instalação/atalho Windows é utilizado. Registrar caminho absoluto, nome, versão, arquitetura, SHA-256 e Authenticode do EXE e do instalador anterior disponível. Não executar o EXE para descobrir a versão.
2. Consultar somente leitura as entradas de desinstalação HKCU/HKLM em 32/64 bits. Correlacionar DisplayName, DisplayVersion, InstallLocation e identificador/GUID. Não executar UninstallString, não usar Win32_Product e não assumir que um arquivo em dist está instalado.
3. Para esta identidade, GUID esperado do NSIS: `49c682c0-0c26-5957-855e-4881f73b25df`, derivado do appId `com.lone.smartroom`. Versões com outro identificador ou instalação de máquina exigem plano específico, não migração automática.
4. Determinar os diretórios efetivos de perfil/userData/sessionData usados pela versão anterior através de código/configuração e arquivos existentes. Verificar tanto o nome de produto quanto o package name, sem renomear ou unir perfis. Registrar caminhos e contagens/hashes, sem publicar valores locais.
5. Verificar espaço livre e permissões do usuário. Se a instalação anterior inclui componentes do agente, inicialização automática ou outros serviços, separar esses componentes antes de usar este instalador: ele não os migra.

**Interromper** se a identidade, o perfil, o tipo de instalação ou o comportamento do desinstalador antigo não puderem ser comprovados. O novo instalador bloqueia instalações de máquina registradas e recusa modo silencioso; não tentar contornar esses bloqueios com elevação, flags ou edição do Registro.

## 2. Backup consistente e recuperável

1. Pedir ao usuário que encerre apenas o aplicativo Electron normalmente; não encerrar o agente ou jogos nem forçar processos. Confirmar que não restaram instâncias usando o perfil. A existência de um portátil aberto também importa.
2. Copiar integralmente a pasta da instalação anterior e cada perfil confirmado para uma nova pasta local de recuperação, fora de Git e das pastas de instalação. Preservar LevelDB, preferências, permissões e todos os arquivos; não copiar somente JSONs visíveis.
3. Proteger o backup conforme a sensibilidade dos dados, com acesso restrito ao usuário e proteção do disco/backup disponível. Não enviar para serviços externos, não imprimir tokens e não copiar credenciais para código-fonte. Preservar a mesma conta Windows para dados protegidos por DPAPI.
4. Criar manifesto de hashes, verificar cada cópia e registrar metadados do aplicativo/atalho/registro de instalação necessários à recuperação. Preservar o instalador anterior verificado se disponível; não o executar.
5. Confirmar o caminho de recuperação e a capacidade de restaurar arquivos para uma pasta de teste vazia, sem iniciar o aplicativo nem tocar no perfil original. Sem backup verificado, não instalar.

## 3. Verificar a entrega sem executar

Os exemplos usam a raiz do repositório e apenas leem metadados:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.cache/artifacts/windows/desktop-dev3-distribution/Lone-Smart-Room-2.0.0-dev.3-x64-Setup-DEV.exe'
Get-AuthenticodeSignature -LiteralPath '.cache/artifacts/windows/desktop-dev3-distribution/Lone-Smart-Room-2.0.0-dev.3-x64-Setup-DEV.exe'
```

Comparar SHA-256 com `PACKAGES-SHA256.txt`, nome/versão com o relatório e status esperado **NotSigned**. Um hash confirma a correspondência com esta entrega, não fornece identidade de publicador. Se Windows/antivírus bloquear, parar e analisar; não desabilitar proteções nem remover bloqueios automaticamente.

## 4. Instalação futura controlada

1. Obter autorização específica após inventário/backup. Usar o mesmo usuário, sem Run as administrator e sem modo silencioso. Não executar o portátil como alternativa para contornar um bloqueio do instalador.
2. Executar somente o Setup verificado, manualmente, com o aplicativo anterior fechado. O pacote detectado como atualização pede confirmação adicional com resposta padrão Não. Confirmar somente depois de rever o destino e o backup.
3. Se a versão antiga for registrada, o NSIS poderá chamar seu desinstalador para substituir os binários. Não assumir que a opção de preservação do novo pacote controla um desinstalador antigo. Se a inspeção anterior não demonstrar segurança para os dados, interromper e preparar outra estratégia.
4. Manter o diretório de instalação validado, sem selecionar uma pasta diferente supondo isolamento: o mesmo GUID pode acionar a substituição registrada. Nenhum agente, serviço, firewall ou inicialização será configurado por esta entrega.
5. O assistente foi configurado para **não abrir o aplicativo no final**. Antes do primeiro lançamento autorizado, conferir os binários e comparar os perfis com os backups. Qualquer alteração inesperada nos dados interrompe a sequência.

## 5. Primeiro lançamento e aceitação, ainda pendentes

Somente com autorização para o teste físico: abrir uma vez, observar a marca, três abas, painéis, minimizar/restaurar/fechar e widget. Conferir a versão Windows dev.3 e a localização do perfil; não autorizar migração silenciosa de dados ou identidade.

Critérios: instalação no escopo/path previstos; EXE e ASAR iguais aos hashes desta entrega; dados anteriores presentes; nenhuma cópia de identidade Android; nenhuma permissão concedida; indicação **comunicação não integrada**; zero ações operacionais e ausência de erros críticos. Não testar Steam/CS2, WoL ou energia. O problema TLS continua impedindo integração operacional, inclusive status desktop autenticado.

## 6. Reversão sem apagar dados

Não foi homologada uma reversão física: a versão instalada real ainda não foi inventariada. Preparação exigida:

1. Encerrar o Electron de forma normal. Preservar a pasta e o perfil pós-teste em um segundo snapshot, sem apagar arquivos nem sobrescrever o backup anterior.
2. Como o destino e a identidade devem permanecer os mesmos, restaurar os binários completos da versão anterior verificada para o destino confirmado, preservando também uma cópia integral da versão nova. Fazer a troca somente após validar os caminhos absolutos e autorização específica; não usar remoção recursiva ou comandos de limpeza como atalho.
3. Manter os dados atuais intactos sempre que compatíveis. Se o runtime anterior não puder ler o perfil, restaurar uma **cópia** do snapshot pré-atualização depois de preservar o perfil pós-teste completo. Não mesclar LevelDB manualmente. Documentar qualquer informação criada após o snapshot; nunca prometer rollback de dados sem perda automática.
4. Conferir atalhos e registro da aplicação contra o inventário. Caso seja necessário reparar o registro ou usar o instalador antigo, revisar apenas as entradas da aplicação e o comportamento daquele instalador em uma autorização separada. Não importar backups amplos do Registro nem executar desinstaladores com flags de exclusão de dados.
5. Validar hashes anteriores e só então autorizar uma abertura de conferência. Nenhum passo restaura ou modifica Android, banco do agente, certificados, pareamento ou grants.

O caminho mais seguro para uma instalação antiga com layout desconhecido pode ser apenas abortar a atualização e manter o aplicativo existente. Não é necessário instalar para preservar o checkpoint Git.

## Reversão do código desta preparação

Reverter o commit de empacotamento desta entrega por `git revert ee010427fcf3660699997126b4868a381d118a0d` em árvore limpa e após revisão. Comando proposto, não executado. Não reverter `9be26ac` ou `e561245`: a interface aprovada fica preservada. Não executar `reset --hard`, não apagar a cache de builds e não reinstalar APK.
