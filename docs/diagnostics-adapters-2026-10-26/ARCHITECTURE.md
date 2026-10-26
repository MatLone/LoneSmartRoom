# Autodiagnóstico — arquitetura antes de integração operacional

Escopo desta fase: desenvolvimento isolado sobre a fundação existente, recibos e snapshots simulados, testes e apresentação somente leitura. Nenhum leitor real será ativado. Android dev.9, assets aprovados, Windows instalado, agente e suas configurações ficam fora da implementação.

## Fluxo planejado para esta entrega

`FixtureReader limitado → adaptador de evidência tipada → Probe v1 → DiagnosticEngine/cache → apresentação PT-BR → prévia documental estática`

1. **HTTPS:** interpretar recibo de uma consulta GET de status. Somente resposta 200 com TLS, hostname, pin e HMAC da requisição confirmados poderá gerar evidência saudável. Timeout/ausência não prova PC desligado. Nesta fase os recibos são substitutos; não há cliente HTTP, leitura de credenciais ou endpoint novo.
2. **Listener:** distinguir porta presente de identidade do processo verificada. PID isolado não é prova. Nenhuma consulta de porta pelo módulo nesta fase.
3. **Named Pipe:** avaliar recibos de conexão, identidade/SID/sessão/localidade, versão, tamanho e falhas. Conexão saudável não significa sensores saudáveis. Nenhum pipe será aberto pelo novo módulo.
4. **Coletores:** projetar snapshots simulados no contrato métrico v1 existente, mantendo valor zero válido, null, erro e desatualização distintos. CPU/RAM e GPU serão avaliados separadamente. Importar somente os contratos/catálogos puros, nunca APIs nativas ou workers.
5. **ADLX:** interpretar estado e evidências da ponte; nunca carregar DLL. Exigir validade e ingresso de até 1,5 s quando houver amostra GPU válida. Quadros rejeitados não serão promovidos a atuais e não provocarão reinício.
6. **Inicialização:** correlacionar recibo de login, configuração esperada e eventos sanitizados já existentes. `attempt`, `child_created` e `bootstrap_ready` não provam que HKCU Run foi despachado, nem que HTTPS está online. Sem origem/correlação suficiente, concluir inconclusivo. Não alterar Run, logs, serviços ou tarefas.
7. **Apresentação:** estados Saudável, Indisponível, Desatualizado e Falha; ausência de evidência explicitamente “Não verificado”. Preservar códigos, horários, origem simulada e última comunicação conhecida. Não expor payloads, valores de segredo, nomes de arquivos pessoais ou exceções livres.

## Limites e confiança

- Apenas provedores `simulated`; JSON UTF-8 limitado a 32 KiB, chaves duplicadas e números não finitos rejeitados. Filas limitadas, sem polling automático ou reparos.
- O relógio monotônico local é recebido pela fixture/observador, não obtido de um cliente remoto. Idade de métricas inclui entrega do snapshot; consultar cache não renova amostra.
- Preservar ingresso ADLX 1,5 s e frescor GPU 3/11 s. Essas regras não mudam os contratos/validadores operacionais existentes, nem o fluxo de retomada de 10 s.
- Recibos booleanos não autenticam recursos por si: são projeções de verificações que um futuro leitor autorizado deverá realizar na fronteira de confiança. ACL por usuário não isola processos maliciosos da mesma conta.
- Leitor de fixture não é sandbox para um plugin Python arbitrário. O runner isolado bloqueará rede, Registro, DLLs e criação de processos.
- O campo adicional de detalhe diagnóstico será uma enumeração fixa, compatível com consumidores v1 que ignorem campos desconhecidos. Nenhuma alteração ao contrato de métricas v1 ou às APIs preload existentes.

## Integração operacional futura — não autorizada nesta fase

Revisar separadamente leitores reais, timeouts, identidade do processo/peer e escopo de dados. Priorizar recibos de consultas já autorizadas e snapshots já validados, sem criar coleta redundante. O processo principal Electron poderá futuramente disponibilizar somente um snapshot diagnóstico sanitizado por API preload restrita. Renderer nunca receberá credenciais, pipe genérico, comando shell ou função de reparo.

Antes de qualquer teste real: nova autorização com limites de duração, uma única sessão somente leitura, nenhum restart/repair, nenhum grant e verificação posterior de processos/perfis. Não exigir o Samsung para concluir esta fase.
