# Primeira execução física da interface — proposta, ainda não autorizada

O Windows dev.3 está instalado. Esta tarefa não abriu o dashboard, não criou um perfil de produção e não importou dados de teste. O próximo protocolo deve permanecer exclusivamente visual.

1. Obter autorização expressa para **uma abertura** do EXE instalado, pelo mesmo usuário normal. Confirmar novamente o caminho, SHA-256, ausência de instâncias Electron Lone Smart Room e preservação do agente/backup. Não abrir o NSIS novamente nem utilizar o portátil.
2. Caminho autorizado a propor:

```text
<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe
```

3. Iniciar uma única vez, sem elevação, argumentos adicionais ou flags de revisão. Caso uma proteção do Windows impeça a abertura, interromper e relatar; não remover bloqueios ou desativar proteções.
4. Observar a criação normal do perfil do aplicativo e confirmar seu caminho real. Não copiar dados demonstrativos, credenciais do Samsung, certificados ou identidade do agente. Registrar somente metadados, sem valores locais sensíveis.
5. Confirmar marca oficial e versão **Windows 2.0.0-dev.3**. Capturar as abas **Controles**, **Monitoramento PC** e **Gamer Launcher**, com navegação lateral e recursos futuros identificados como indisponíveis.
6. Exercitar somente operações visuais: painéis de configuração locais, abrir/fechar painel, rolagem, redimensionamento, dashboard/widget, navegação inferior do widget e minimizar/restaurar pela barra de tarefas. Não existe bandeja ou login automático implementado nesta versão.
7. A interface deve mostrar **comunicação não integrada**, estado do PC desconhecido e ausência de medições reais. A leitura de permissões pelo desktop continua indisponível; não deve apresentar permissões inventadas como consulta ao agente. Não efetuar pareamento nem introduzir cliente operacional para mudar essas indicações.
8. Não acionar Steam/CS2, WoL, energia, dispositivos, grants, NEX ou integrações futuras. Nenhuma chamada operacional ao agente faz parte do teste. Preservar Android e a pendência TLS.
9. Depois de a interface carregar, observar estabilidade por 60 segundos, sem ações operacionais. Registrar erros visuais/de execução; em caso de falha, interromper sem nova abertura, reinstalação ou rollback automático.
10. Se o protocolo autorizado incluir encerramento, fechar somente o Electron normalmente e verificar que o agente segue no mesmo processo/listener e com zero grants. Confirmar preservação dos arquivos de origem e do backup. Não apagar o perfil criado.

Critérios de aprovação: janela real utilizável, versão correta, identidade íntegra, três abas/painéis/widget sem cortes ou sobreposições nos casos testados, controles indisponíveis sem execução e agente independente. A aprovação visual não libera comunicação autenticada: o tratamento TLS relevante ainda exige correção e validação em etapa própria.

Nenhum dos passos de abertura deste documento foi executado durante a instalação. Uma necessidade de remoção/recuperação deve seguir autorização separada e os planos já documentados, mantendo dados e backups.
