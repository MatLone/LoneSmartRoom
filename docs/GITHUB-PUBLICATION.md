# Publicação privada — preparação de 2026-10-29

Destino existente: https://github.com/MatLone/LoneSmartRoom. O conector GitHub
confirmou `visibility=private`, permissão de push, tamanho informado zero e branch
padrão main. Nenhum código foi enviado nesta preparação.

## Inventário e preservação

Nove branches, dois worktrees, 204 commits alcançáveis e 2.420 arquivos rastreados
no checkout principal. Nenhum remote configurado. HEAD: `e85a9c0`, branch
`feature/signalrgb-control`. Alterações SignalRGB pendentes foram copiadas antes
da preparação; não foram modificadas funcionalmente por esta tarefa.

Branches: main, feature/hardware-readonly-c1, feature/modular-expansion-plan,
feature/openrgb-control, feature/secure-pairing-status, feature/signalrgb-control,
feature/telemetry-android-development, feature/ui-migration-preview e
feature/windows-control-center.

Em `.cache/github-publication`, o bundle `pre-publication-all-refs.bundle` passou
em `git bundle verify`: histórico completo das nove branches e referências HEAD.
O diretório datado da auditoria preserva refs, patch binário, cópia dos arquivos
pendentes e hashes SHA-256. Não publicar esse bundle: contém histórico não saneado.
O segundo worktree estava limpo no inventário.

Windows, Android, agente, NEX, Gamer Launcher, monitoramento, Touch Panel, recursos
e integrações RGB estão presentes localmente. Branches divergentes foram mantidas;
nenhum merge foi realizado. SignalRGB permanece trabalho não homologado.

## Auditoria e bloqueio

O auditor leu 4.253 objetos, incluindo 2.913 blobs, alcançáveis por todas as refs.
Encontrou 148 objetos com caminhos pessoais Windows, 43 com rede privada e dois
logs versionados. São contagens por objeto, não pessoas ou arquivos distintos.
Há evidências reais em diagnósticos de conta/inicialização e relatórios de build;
endereços em fixtures podem ser sintéticos e precisam de classificação contextual.

Os dois alertas de delimitadores PEM eram falsos positivos confirmados: o script
prepare-agent-candidate.py contém os delimitadores para rejeitar chaves. Não há
chave naquele código. Os padrões não encontraram tokens GitHub/AWS/serviço nem
arquivos de credenciais pelas extensões verificadas. Isso não garante ausência
de segredos: a análise é heurística e conteúdo binário requer inspeção específica.

**Push bloqueado por dados pessoais no histórico.** Nenhuma branch ou commit foi
publicado. Remote não foi configurado para evitar um push prematuro.

## Solução preparada para decisão

1. Criar cópia independente do bundle, sem compartilhar objetos graváveis com o
   original. Preservar também o trabalho pendente e todas as branches.
2. Classificar evidências pessoais, caminhos, identificadores de máquina/rede e
   fixtures sintéticas. Remover logs operacionais somente da cópia de publicação.
3. Sanear todos os commits afetados, mantendo fontes, recursos, topologia,
   branches, datas e autoria não sensível. Caminhos fixados em código exigem
   revisão própria para não quebrar execução ou remover funções silenciosamente.
4. Gerar mapa local hashes antigos → novos. Saneamento altera inevitavelmente
   hashes dos commits afetados e descendentes; o original mantém todos os hashes.
5. Reauditar a cópia, inspecionar binários e testar substituições. Conferir
   cobertura Windows/Android/agente/recursos e código ainda não commitado.
6. Confirmar novamente privacidade e refs remotas. Conectar o destino sem
   sobrescrever remote existente. Publicar explicitamente branches aprovadas,
   sem force, mirror ou sobrescrever main remota.
7. Verificar árvores, refs, histórico e privacidade no GitHub após o envio.

Decisão necessária antes do saneamento: aceitar novos hashes na cópia publicada
e remoção/anonimização das evidências pessoais, preservando integralmente o Git
local original. Nenhuma reescrita foi executada nesta preparação.

## Exclusões e reversão

Gitignore ampliado para SQLite, dumps, logs, perfis, backups, credenciais e
artefatos locais. Arquivos existentes permanecem no disco. Arquivos já rastreados
não foram removidos automaticamente. README atualizado com arquitetura, módulos,
requisitos e builds sem chaves privadas.

Para recuperar o estado anterior, clonar o bundle em outro diretório e comparar
seletivamente README/gitignore. Não usar reset/clean sobre alterações RGB. Nunca
restaurar sobre instalações, bancos, credenciais ou perfis operacionais.

Não houve teste físico, instalação, consulta ao agente, alteração de firewall,
Registro, certificados ou credenciais. O estado operacional do agente e backups
não foi revalidado nesta tarefa; não se declara medição de saúde ou integridade
operacional apenas pela ausência de modificações.
