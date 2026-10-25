# Gate de liberação da sessão legada — 24/10/2026

**Decisão: não liberar a sessão e não executar o teste físico novo.** Não foi
encontrado um caminho de encerramento gracioso disponível e especificamente
autorizado para os processos legados atuais. Nenhum processo foi encerrado,
reiniciado, sinalizado ou atualizado. Nenhuma partida da versão nova foi feita.

Preservados `0ddcd8c8d395406ede1d27af9d8d4c62eb4cd04b`,
`2d345f8cd60ff4fd6ed8241b1ad030c09dca6d6f` e
`808dffb5c3c16b8c3ea346133666771002dcb73d`.

## Identidade, atividade e integridade confirmadas

| Item | Evidência |
|---|---|
| Supervisor | PID 6396, pai 5580, criado 24/10 20:25:48 local, Pythonw base e comando esperados, mesma conta |
| Worker/agente | PID 17992, pai 7672, criado na mesma sessão, argumentos `--worker`, imagem/comando/conta esperados |
| Porta | Um listener 8776 do PID 17992, sem bind wildcard |
| TCP | Três amostras entre 22:00:05 e 22:00:09 local: um listener, zero sockets de cliente em cada amostra |
| Aplicativos | Zero grants e zero registros `accepted`/`dispatching` no banco |
| Banco | `PRAGMA quick_check` retornou somente `ok`, journal `delete`; conexão de diagnóstico somente leitura |
| Credenciais | Identidades, segredos ainda criptografados, revogações, permissões e esquema iguais aos recibos anteriores; sem descriptografia |
| Arquivos | 268 arquivos protegidos fora do banco de replay sem diferenças; hashes da implementação nova também correspondem ao manifesto |
| Run/firewall | Hashes correspondem aos recibos anteriores, sem alterações |

Os horários são de 24/10/2026 em America/Sao_Paulo. Os JSON preservam UTC, já em
25/10 para parte dessas verificações. Os horários de criação, imagem, papel e conta
confirmam que não são apenas PIDs coincidentemente reutilizados.

**Limitação de observabilidade:** a versão antiga não exporta contagem exata de
handlers ativos. As amostras TCP e o estado persistido não mostram trabalho em
andamento, mas não provam ausência absoluta de uma operação transitória nem impedem
uma nova consulta do Samsung entre amostras. Nenhuma requisição HTTPS foi enviada
pelo diagnóstico para evitar acrescentar atividade.

## Opções de parada examinadas

| Opção | Resultado / motivo para não executar |
|---|---|
| Ctrl+C / KeyboardInterrupt | Existe no código, porém ambos os processos estão sem console. Sondagem de console existente retornou erro 6 para ambos |
| Fechar janela | Enumeração encontrou zero janelas top-level dos PIDs; nenhuma mensagem WM_CLOSE foi enviada |
| Novo canal local | Não carregado pela versão legada; não se presumiu compatibilidade e não foi sinalizado |
| API / CLI antiga | Não existe operação de stop na implementação carregada; não foi criado endpoint remoto |
| Encerrar supervisor | Não para o worker, que mantém seu próprio mutex; não é solução de liberação |
| EOF de stdin | Processos usam DEVNULL e o loop não lê stdin; não é canal de controle |
| Mudar rede ou firewall | Proibido nesta fase; o loop antigo apenas aguardaria a rede e manteria o processo/mutex |
| Debugger / injetar exceção | Não é encerramento cooperativo previamente implementado; exigiria interferência não autorizada |
| TerminateProcess / Stop-Process / taskkill | Parada não graciosa; não autorizada e não executada |
| Reinício/logoff | Não autorizados; não executados e não garantem execução de finalizadores Python |

O helper de console se desvinculou apenas de seu próprio console, tentou consultar
os consoles existentes dos PIDs e terminou. Não alocou console, não enviou eventos
Ctrl+C/Ctrl+Break, mensagens de janela ou escrita de memória.
[Microsoft — AttachConsole](https://learn.microsoft.com/en-us/windows/console/attachconsole)
documenta erro 6 quando o alvo não possui console; [FreeConsole](https://learn.microsoft.com/en-us/windows/console/freeconsole)
atua no processo chamador. A sondagem confirma a indisponibilidade desse caminho,
não tenta criar retroativamente um mecanismo de parada no agente.

## Alternativas para decisão — nenhuma executada

**A. Manter a sessão atual e adiar o teste (recomendação nas permissões atuais).**
Preserva conectividade e não introduz risco de parada abrupta. A autorização do
teste continua condicional; não basta para iniciar outra versão com porta/mutex ocupados.

**B. Autorizar separadamente uma transição excepcional em janela de manutenção.**
Envolveria um backup consistente do agente e, se não surgir outro caminho seguro,
uma parada não graciosa **somente do worker desta sessão**, após reconferir conta,
imagem, comando, horário de criação, árvore e listener. Não é uma ação graciosa,
não tem risco zero e está expressamente proibida na autorização atual. Não é
proposta uma seleção genérica de processos Python, encerramento da árvore por nome
ou kill do supervisor.

Com a saída do worker confirmada, o supervisor deve obter o código de término e
encerrar naturalmente. Isso precisa ser verificado, nunca presumido. Se qualquer
pai/redirecionador permanecer, parar a sequência e pedir nova orientação, sem ampliar
automaticamente a seleção de processos. Não retentar nem iniciar a nova versão em falha.

Como alternativa de manutenção futura, um encerramento normal de sessão/Windows
poderia ser planejado com autorização própria, mas não faz parte desta fase e não
comprova parada graciosa do Python. Não é necessário reiniciar o Windows para o
teste da versão nova quando a porta/mutex já estiverem livres.

## Redução de risco e recuperação exigidas antes da alternativa B

Nenhum backup novo de credenciais foi criado neste diagnóstico. O backup existente
`Windows-before-dev4-20261024T174801Z` foi verificado novamente: 72 arquivos,
27 diretórios, 8.589.376 bytes, hashes/tamanhos e ACL exclusiva válidos. **É o backup
do perfil Electron; não substitui um snapshot consistente recente do agente.**

Plano a aprovar antes de uma parada excepcional:

1. Pedir ao usuário que não envie consultas/comandos durante a janela. Amostrar
   novamente TCP e fila; ainda assim não alegar que a versão antiga ficou quiescida.
2. Criar destino fora do Git/instalação, por exemplo em `Documents\Lone Smart Room
   Backups\Agent-before-graceful-transition-<UTC>`, com ACL exclusiva à conta.
3. Produzir snapshot de `devices.db` pela API de backup consistente do SQLite,
   abrindo a origem em modo somente leitura. Não copiar simplesmente o arquivo de
   um banco ativo nem presumir que os arquivos de journal possam ser ignorados.
4. Preservar `config.dpapi`, `tls.dpapi`, `server.crt` e `server.key` como bytes
   existentes, sem descriptografar; manter ACL restrita, registrar hashes e verificar
   `quick_check` no snapshot. Não incluir nenhum desses arquivos no Git.
5. Só então, com autorização excepcional específica e identidade reconferida,
   executar a ação aprovada, se escolhida. Verificar processos/listener/mutex e
   integridade do banco antes de qualquer nova partida.
6. Se houver falha de integridade, não iniciar/reparear/rotacionar certificados ou
   restaurar automaticamente. Preservar o banco e pedir autorização de recuperação.

Uma parada abrupta pode interromper I/O e não executar finalizadores. O journal
SQLite reduz riscos transacionais, mas não justifica prometer ausência de perdas.
[Microsoft — TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)
documenta a interrupção das threads/I/O e os riscos de estado de DLLs.

Recuperação, somente se necessária e aprovada: agente offline, validar hashes e
restaurar seletivamente o snapshot íntegro sob a mesma conta DPAPI; conferir que
certificado/pin e segredos criptografados correspondem. **Não sobrescrever o banco
atual cegamente:** snapshot antigo pode reverter revogações, permissões e nonces.
Revisar o último estado autorizado e a janela anti-repetição; antes de reabrir após
eventual restauração, aguardar a expiração de requisições reutilizáveis com relógio
estável (margem conservadora de ao menos 121 s após a saída efetiva do agente para
os limites atuais de timestamp). Não alterar relógio, autenticação ou grants para
contornar essa verificação. Não há restauração executada nem rollback destrutivo.

## Estado após o eventual teste — requer decisão explícita

O teste autorizado contém **uma partida** e um encerramento gracioso. Se concluído
sem partida adicional, o estado final será **agente parado, porta 8776 livre**;
o Samsung deixará de obter status HTTPS atualizado. Isso não significa PC desligado,
e não apaga pareamento, credenciais ou WoL.

Se o usuário quiser manter a conectividade ao final, deve autorizar expressamente
**uma partida manual adicional do agente**, depois de provar o encerramento completo
da sessão de teste. Trata-se de reiniciar somente o processo, não o Windows. Essa
segunda partida ainda não foi autorizada. Não haverá religamento implícito.

A decisão sobre o estado final também precisa estar resolvida antes do teste.
Quando ambas as condições forem aprovadas (liberação e estado final), aplica-se
o procedimento do relatório `docs/graceful-shutdown-2026-10-24/README.md`: nova
instância única, status autenticado/Samsung, estabilidade 60 s, stop local único,
verificação real de PIDs, porta, mutex e logs. Timeout não será tratado como sucesso.

## Estado mantido nesta entrega

Legado continua ativo: supervisor 6396, worker 17992, listener 8776. Nenhuma nova
validação física da versão com shutdown foi feita. Última confirmação do usuário
no Samsung: **Conectado**; não foi realizada nova captura/consulta Android nesta fase.
Pareamento e armazenamento permanecem íntegros. Nenhuma concessão de grants, ação
de energia, WoL, Steam/CS2, alteração Android/Electron, Run, firewall, serviço,
certificado, credencial ou correção TLS. Aguardando autorização específica da
alternativa escolhida e decisão sobre o estado final.
