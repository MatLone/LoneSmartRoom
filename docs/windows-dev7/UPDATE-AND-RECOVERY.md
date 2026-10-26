# Atualização dev.6 para dev.7 — procedimento futuro

**Plano não executado.** Preparação de pacotes não autoriza instalar ou abrir.
Manter a dev.6 fechada e o agente original ativo até decisão específica.

## Gates e backup antes de instalar

1. Obter autorização para uma única instalação assistida pelo NSIS; portátil
   não será usado para substituir ou contornar o instalador.
2. Confirmar dev.6, destino `%LOCALAPPDATA%\Programs\Lone Smart Room`, mesmo
   appId `com.lone.smartroom`, ausência de Electron/monitoramento/ADLX residuais.
   Se aberto, fechar normalmente por Sair; nunca encerrar à força.
3. Identificar o agente original por executável, argumentos, criação e parentes;
   confirmar listener único 8776, autenticação válida e zero grants. Não pará-lo.
4. Inventariar instalação e `%APPDATA%\Lone Smart Room`, preferências de dashboard,
   widget, posições/tamanhos e bandeja. Não importar perfis de demonstração.
5. Criar **novo** backup `Windows-before-dev7-<UTC>` em
   `Documents\Lone Smart Room Backups`, fora de Git, instalação e perfil.
   Não sobrescrever os backups pré-dev.3/4/5/6. Copiar apenas com app fechado;
   se algum arquivo estiver bloqueado, registrar e parar, sem forçar consistência.
6. Proteger o novo diretório por ACL da conta autorizada, preservar estrutura,
   registrar contagem/tamanho/SHA-256 por arquivo e conferir novamente a cópia.
   Não descriptografar credenciais ou colocar inventário sensível em Git.
   Não copiar/modificar o banco do agente para respaldar Electron.
7. Recalcular o hash do NSIS:
   `0033ee706adfd9edcd29d2f87b5bddc5751bcbd2a6337125e09adb84d49d7870`.
   Confirmar dev.7/x64, proveniência e NotSigned. Diante de bloqueio Defender,
   SmartScreen ou elevação inesperada, interromper sem desativar proteções.

## Instalação e inspeção estática autorizadas separadamente

1. Executar o NSIS uma vez em modo assistido. Conferir destino existente e a
   confirmação explícita de substituição dos binários da versão anterior.
2. Não alterar conta/destino, não criar autostart, serviço, tarefa ou regra de
   firewall. O fluxo permanece por usuário/asInvoker, sem elevação.
3. Não marcar execução final: `runAfterFinish=false`. Não abrir dashboard/widget
   nem executar sensores nesse estágio. Parar e diagnosticar caso surja condição
   imprevista; não repetir automaticamente a instalação.
4. Comparar versão dev.7 e arquivos com o payload inspecionado, recursos oficiais,
   runtime/manifesto, atalhos e perfil preservado. ProductVersion numérico 2.0.0.0
   é esperado; conferir FileVersion/ASAR/DisplayVersion com o prerelease completo.
5. Confirmar ausência de novos processos, autostart/serviços/tarefas/firewall,
   integridade do backup e mesmo agente ativo/autenticado/zero grants.
6. Solicitar autorização específica para a primeira sessão física do pacote.
   O comportamento esperado de preferências é compatível porque os componentes
   de persistência/esquema 1 não mudaram. Isso ainda exige conferência física.

## Primeira execução posterior — autorização própria

Usar o plano complementar de 120 s, iniciar relógio na abertura, priorizar dados
e retomada nos primeiros 45 s, depois Sair e conferir filhos/pipes antes do limite.
Não repetir/forçar saída. Confirmar GPU Atualizando, leitura nova e indisponibilidade
sem zero fictício; cenários que não ocorrerem naturalmente ficam não observados.
Nenhum jogo, comando de energia ou concessão de grant é necessário para homologar.
O agente deve continuar ativo. A instalação e esta execução são decisões separadas.

## Recuperação e reversão — não executar agora

- Se uma instalação falhar, preservar logs/arquivos/resultados e não abrir ou
  repetir o pacote automaticamente. Não desinstalar nem limpar dados como tentativa
  de conserto. Não modificar o agente para recuperar o Electron.
- Para retornar à dev.6, obter autorização, fechar somente o Electron normalmente
  e comprovar que seus componentes terminaram. Se não terminar, registrar e pedir
  decisão, sem kill ou reinício do Windows.
- Preservar primeiro uma cópia protegida do perfil/estado que a dev.7 chegou a
  criar. Repor apenas binários dev.6 verificados por backup/artefato original,
  mediante procedimento revisado para os arquivos presentes. Não presumir que o
  instalador aceitará downgrade nem que sua execução preserve dados automaticamente.
- Conferir o perfil atual contra o backup e esquema 1. Restaurar configurações
  antigas somente quando necessário, guardando também o estado novo. Validar
  hashes/ACLs antes de uma execução autorizada. Manter backups anteriores íntegros.
- Não utilizar uninstaller, limpeza de perfil, exclusão recursiva de diretórios
  ou rollback automático neste plano.

O NSIS dev.6 original preservado tem SHA
`fccf8683210f24577462b1b0ef5ce100cf1373e23beac4ac5b91383dbfb0b545`;
sempre recalcular antes de qualquer uso autorizado. Backups e manifestos anteriores
foram conferidos nesta preparação. **Não houve atualização a reverter agora.**

Reversão apenas de código: revisar `git revert` do commit documental e depois
`d4f39a704089720659c87f0a2992aa2ac75afee8`, em ordem inversa. Isso repõe metadados
de build anteriores; não altera a dev.6 instalada e não apaga pacotes novos/antigos.
Os scripts recusam sobrescrever saídas existentes; nova compilação requer outro
destino revisado. A correção `3dc783c` e os checkpoints permanecem no histórico.
