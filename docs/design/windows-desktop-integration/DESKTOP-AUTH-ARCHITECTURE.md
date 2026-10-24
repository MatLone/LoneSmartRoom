# Cliente desktop autenticado — proposta, não implementada

## Condição de entrada obrigatória

**Nenhum novo cliente desktop autenticado operacional deve ser habilitado enquanto o comportamento TLS relevante para requisições excessivas/ambíguas não estiver corrigido e validado.** Isso inclui consulta de status. A interface atual não possui transporte operacional. Este documento não autoriza alterações no agente, certificados, rede ou grants.

Pendência preservada: [diagnóstico TLS e matriz de falhas](../brand/compact-review-2026-10-24/TLS.md). Rejeitar uma requisição e não despachar comando são diferentes de entregar a resposta de erro completa: os resets antes do fim da resposta continuam uma falha conhecida do contrato testado. A proposta de descarte limitado não resolve todos os casos e não foi aplicada.

## Separação de responsabilidades

```text
Renderer: exibição de estados e confirmação de ações permitidas
        │ API preload tipada, sem segredos ou caminhos
        ▼
Main: sessão desktop, validação IPC, TLS/pin, HMAC, nonce, estado
        │ HTTPS autenticado, somente rede/localidade aprovada
        ▼
Agente existente: autenticação, revogação, replay, grants, allowlist
        │ executores já validados, sem alterações nesta entrega
        ▼
Steam / CS2 (só após autorização específica futura)
```

O processo principal concentra operações privilegiadas. Manter contextIsolation, sandbox, nodeIntegration desabilitado, origem/frame validados, CSP e recursos locais controlados. O preload atual contém apenas operações de janela/versão. Uma expansão futura deve ser pequena, tipada e revisada: por exemplo consulta de estado e pedido de aplicativo por enum fechado, sem expor `ipcRenderer`, URL arbitrária, caminho, argumentos, shell, biblioteca Node ou conteúdo de credenciais. A documentação Electron recomenda esse isolamento e a validação dos emissores: [segurança](https://www.electronjs.org/docs/latest/tutorial/security/) e [contextBridge](https://www.electronjs.org/docs/latest/api/context-bridge).

## Identidade e pareamento próprios

1. Identidade independente por instalação desktop; nunca reaproveitar device_id, segredo, armazenamento ou grant do Samsung.
2. Pareamento explicitamente iniciado na interface confiável do Windows, com código/token temporário de uso único ou QR do mecanismo existente. Antes de enviar o segredo temporário, validar o endpoint e a identidade TLS por material confiável/confirmado localmente. Não fazer confiança cega no primeiro certificado apresentado pela rede.
3. Validar cadeia/identidade esperada e pin do certificado conforme o contrato atual. Uma futura implementação Node deve definir expressamente o trust anchor local e a checagem de hostname/pin compatíveis com o agente; não basta desabilitar a validação da cadeia e comparar depois. Não usar trust-all ou `rejectUnauthorized:false`.
4. Persistir a identidade retornada somente depois de pareamento confirmado. Certificado trocado ou pin divergente exige falha fechada e fluxo explícito de recuperação, sem substituir automaticamente o pin.
5. Revogação por dispositivo no agente, separada de outros clientes. Não criar grants ao parear nem ao abrir a interface.

## Credenciais

Proposta para Windows: armazenamento cifrado pelo main com `safeStorage`, proteção DPAPI do usuário e permissões de arquivo adequadas. Avaliar a API assíncrona da versão instalada. Verificar disponibilidade e falhar fechado caso não haja proteção; nunca cair para texto puro, renderer, localStorage, logs ou repositório. O renderer recebe apenas estado não sensível.

DPAPI não constitui isolamento contra outros programas maliciosos executados como o mesmo usuário; essa limitação deve constar da revisão. A API não elimina a necessidade de conferir identidade do servidor e autoridade do pedido. Referência: [Electron safeStorage](https://www.electronjs.org/docs/latest/api/safe-storage).

## Autenticação e repetição

Reutilizar exatamente o protocolo existente, sem inventar uma variante desktop. Código de referência: `agent/windows/secure_protocol.py`. A mensagem autenticada é:

```text
LSR2\n{device}\n{stamp}\n{nonce}\n{method}\n{path}\n + bytes exatos do corpo
```

HMAC-SHA256, identidade individual, timestamp e nonce criptográfico de 128 bits representado por 32 hexadecimais. Preservar os nomes de cabeçalhos e a janela temporal já implementados. O agente consome nonces de forma persistente e atômica por dispositivo. Serializar o corpo uma vez e assinar os mesmos bytes enviados; não reformatar JSON depois da assinatura.

Timeout depois do envio não confirma execução nem autoriza repetição automática de comando. Mostrar resultado desconhecido quando necessário; consultar o identificador/estado pelo contrato existente. “Executado” significa despacho aceito pelo executor e não prova que Steam ou CS2 chegaram à tela utilizável. Confirmação de processo/menu é uma observação separada.

## Autorizações e estados

- Consulta autenticada de status primeiro; comandos somente em uma fase futura autorizada.
- Grant individual por aplicativo, dispositivo e validade. Sem concessão automática, herança entre clientes ou extensão de prazo pela UI.
- Permissões consultadas no agente são a autoridade; um botão habilitado não substitui validação no servidor.
- Rede privada/sub-rede autorizada; preservar bloqueio em perfil Público e regras existentes. Não abrir roteador nem acrescentar regras nesta fase.
- Agente continua independente do ciclo de vida do Electron. Fechar/minimizar/widget não inicia, encerra ou reinicia o agente.
- Conectado requer resposta autenticada recente. Desconectado significa falha de comunicação; nunca confirma PC desligado. Exibir desconhecido e última comunicação separadamente.
- Métricas somente com provedor real futuro; ausência de sensor não equivale a zero ou temperatura ambiente.

## Critérios para liberar implementação operacional

1. Aprovar uma correção separada de framing/encerramento TLS. Preservar o limite funcional atual de 1024 bytes, recursos e deadlines limitados e ausência de despacho para corpos rejeitados.
2. Validar 1023/1024/1025 bytes, excessos moderados/grandes, corpo ausente/parcial/lento, Content-Length duplicado/malformado, Transfer-Encoding concorrente e encerramento controlado. Definir explicitamente a garantia de resposta completa versus fechamento seguro em cada caso; não converter reset inesperado em teste aprovado silenciosamente.
3. Testar concorrência/limite agregado, cliente Android preservado, certificado inválido, pin/hostname divergentes, token expirado/usado, credencial errada, replay, revogação, indisponibilidade e reinício do agente, sem executores reais.
4. Testar IPC vindo de iframe/origem/janela indevidos, argumentos fora da enum, armazenamento indisponível, ausência de fallback em texto puro e vazamento de segredo para DOM/logs.
5. Com identidade desktop própria e zero grants, comprovar status autenticado. Abrir Steam/CS2 ou alterar grants requer autorização futura específica e teste físico controlado.

Esta proposta mantém o protocolo e os executores atuais. Não há mudanças operacionais incluídas no commit visual.
