# Plano específico após o inventário — não executar agora

## Situação comprovada

Nenhuma instalação anterior ou perfil de produção Electron foi identificado nos locais inventariados. Não existe, portanto, um binário instalado anterior que este backup permita restaurar. As árvores de código v1.3/v1.4, checkpoints e pacotes locais continuam nos locais originais e não foram modificados.

Este backup preserva somente dados dos ambientes de teste Windows Electron, com estrutura e hashes. Ele **não contém** o agente, certificados, banco de pareamento ou Android. Não usar esse backup para restaurar esses componentes.

## Verificar a integridade sem restaurar

1. Acessar como o mesmo usuário Windows a pasta `<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev3-20261024T145523Z`. Não ampliar suas ACLs para facilitar acesso de outro usuário.
2. Calcular SHA-256 de `manifest.json` e comparar com o hash publicado no README desta entrega. Os exemplos abaixo são somente leitura:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev3-20261024T145523Z\manifest.json'
Get-Acl -LiteralPath '<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev3-20261024T145523Z'
```

3. Para cada `files[].destinationRelative`, conferir tamanho e SHA-256 contra o manifesto, com caminho absoluto validado dentro do backup. Conferir também cada raiz em `profiles` e diretório em `directories`, incluindo vazios. Uma falha impede restaurar ou instalar com confiança nesse backup.
4. Manter inventário/manifesto/dados no armazenamento protegido. Não publicar configurações, conteúdos de bancos ou arquivos de sessão para demonstrar integridade. Hash local não é assinatura digital de publicador.

Verificador somente leitura incluído nesta entrega, executado com sucesso contra o backup:

```powershell
& .\docs\windows-inventory-backup-2026-10-24\Verify-Backup.ps1 -BackupRoot '<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev3-20261024T145523Z' -ExpectedManifestSha256 '724eb1cd62aa884ab3af8f88d7d58df35c6e95814c6717b756aa75d2898f397f'
```

O comando verifica hashes, tamanhos, diretórios e ACLs; não grava no backup, não lê valores das preferências e não restaura arquivos.

A conferência independente desta tarefa verificou 336 arquivos e 139 diretórios correspondentes às fontes, bem como ACLs de todas as entradas. Nenhum arquivo foi restaurado.

## Recuperar dados de teste, somente com autorização futura

1. Confirmar qual ambiente de teste precisa ser recuperado e se existe algum Electron usando seu diretório. Pedir encerramento normal ao usuário se necessário; não matar processos nem tocar no agente.
2. Preservar uma cópia protegida do estado atual desse ambiente antes de qualquer substituição.
3. Validar o mapeamento `data/repository/<relative>` do manifesto para o mesmo `<relative>` na raiz correta do repositório. Autorizar explicitamente apenas esses diretórios; não copiar uma pasta `.cache` inteira sobre outra.
4. Restaurar uma cópia para os caminhos de teste aprovados, sem apagar o backup e sem mesclar manualmente arquivos LevelDB de gerações diferentes. Conferir hashes e estrutura antes de qualquer abertura autorizada.
5. Não copiar esses perfis de prévia/teste para `%APPDATA%\Lone Smart Room` ou outro perfil de produção. O conteúdo demonstrativo não constitui configurações reais do aplicativo instalado.

## Primeira instalação visual, futura

1. Obter autorização específica. Reconsultar registros/atalhos/processos e caminhos, pois podem ter mudado desde este inventário. Se aparecer instalação ou perfil de produção, interromper e fazer novo backup consistente dessa instalação.
2. Conferir SHA-256 e NotSigned do Setup conforme [a entrega de distribuição](../windows-distribution-dev3/README.md). Não usar flags silenciosas, elevação ou o portátil para contornar bloqueios.
3. Confirmar destino separado das fontes, agente e backups. Proposta: `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room`. Não iniciar a instalação com destino em Documents, no repositório ou no backup.
4. Executar somente o NSIS verificado depois da autorização. Se detectar versão antiga inesperada ou pedir substituição, cancelar: este inventário não prevê substituição de instalação anterior.
5. O instalador está configurado para não abrir o app ao finalizar. Antes do primeiro lançamento autorizado, conferir os hashes do EXE/ASAR e confirmar que o agente e seu startup continuam intactos.
6. Autorizar separadamente ou no protocolo físico explícito uma única abertura visual: marca, versão dev.3, abas, painéis, widget, minimizar/restaurar/fechar. Confirmar que a interface mostra comunicação não integrada. Não parear nem acionar Steam/CS2, WoL ou energia.

## Retornar ao estado anterior à primeira instalação

Não há aplicativo Electron anteriormente instalado para fazer downgrade. Se a nova interface apresentar problema:

1. Interromper o teste e solicitar encerramento normal do Electron. Preservar logs pertinentes e um backup protegido do novo perfil e dos binários antes de propor remoção.
2. O retorno ao estado sem instalação pode usar, **após nova autorização**, o desinstalador desta build previamente revisado, mantendo dados. Não passar flags de apagar app data e não tratar desinstalação como operação já autorizada nesta tarefa.
3. Preservar o perfil novo mesmo se a instalação for removida. Não apagar diretórios manualmente nem instalar uma versão antiga para forçar retorno. Se o perfil impedir testes posteriores, preparar uma estratégia separada com snapshot e autorização, sem limpeza automática.
4. Dados de teste podem ser recuperados pelo procedimento acima, se necessário. Fontes originais e backups permanecem intactos. Agente, Run key, certificados, grants e Samsung ficam fora da reversão do Electron.
5. Uma eventual necessidade de reparar entradas de instalação exige revisão e autorização apenas para essas entradas da aplicação; não restaurar o Registro inteiro.

## Reversão documental

Esta tarefa não altera código funcional ou pacotes. O commit documental pode ser revertido por um novo `git revert <commit-deste-relatorio>` depois de revisão, sem tocar nos checkpoints `ee01042`/`c51e01e` nem no backup físico. Não usar reset destrutivo nem excluir o backup como parte dessa reversão.
