# Reversão da integração visual Windows

Nada foi instalado ou substituído na aplicação Windows utilizada pelo usuário. As janelas de desenvolvimento desta validação foram fechadas. Nenhuma reversão de sistema é necessária nesta etapa.

## Pontos de recuperação

- Estado aprovado anterior à integração: `ddb1480d7538b095f06a46bacc832cb0523c8344`.
- Checkpoint documental Android preservado: `d5323f7`.
- Alteração visual isolada: `9be26acc24788cdf2192bb555b8860f39bb55845`.
- Cópia local prévia: `.cache/backups/windows-ui-ddb1480/`, dentro do repositório. Contém código/configuração/assets anteriores; não duplica node_modules ou distribuições.
- Builds Windows e APKs anteriores permanecem em seus locais, sem sobrescrita. O novo unpacked está exclusivamente em `.cache/artifacts/windows/desktop-dev3/`.

## Procedimento proposto, não executado

1. Confirmar que a árvore está limpa e preservar qualquer novo trabalho. Encerrar somente eventual janela de desenvolvimento pertencente a este teste.
2. Se for autorizada a reversão do código desta integração, aplicar um commit de reversão:

```powershell
git revert 9be26acc24788cdf2192bb555b8860f39bb55845
```

3. Revisar o diff; ele reverte entry/preload/UI, versão Windows e a exceção estrita de hashes da revisão de preservação. Documentação/capturas podem continuar no histórico. Conflitos com mudanças futuras exigem revisão, sem reset destrutivo.
4. Reexecutar verificações de preservação e a validação pertinente ao código restaurado antes de distribuição. Não aplicar o harness de widget ao código antigo como se esse recurso já existisse.

Alternativamente, consultar arquivos anteriores pelo Git ou pela cópia local sem sobrescrever trabalho atual. Não usar `reset --hard`, excluir backups, desinstalar aplicativos, limpar dados ou fazer downgrade Android como parte desta reversão.

## Antes de uma futura instalação Windows

Inventariar o executável/versão e o caminho de perfil da instalação realmente utilizada pelo usuário, planejar backup do perfil fechado, definir distribuição/assinatura e autorização expressa. Nesta fase apenas a identidade de build existente foi preservada (`lone-smart-room`, `com.lone.smartroom`); não foi feita migração de dados de uma instalação Windows em uso.

O perfil de revisão em `.cache/windows-desktop-review/` é isolado. Não copiar credenciais do Samsung nem criar identidade operacional para testar a distribuição visual. Não restaurar banco/configuração do agente, certificados, credenciais ou grants por cópia de um perfil Electron. Não reinstalar APK ou reiniciar agente como consequência da reversão visual.
