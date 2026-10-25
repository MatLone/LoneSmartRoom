# IPC local de monitoramento — Named Pipe em desenvolvimento isolado

## Atualização de implementação — desenvolvimento isolado, 25/10/2026

O adaptador descrito abaixo foi implementado em `winpipe.py`, `pipe_protocol.py` e
`pipe_server.py`, com hosts explícitos em `scripts/monitoring-pipe-{client,server}.py`.
O serviço lógico `ipc.py` permanece independente; seu estado `not_implemented`
descreve uso direto sem adaptador. O wrapper nativo anuncia `windows_named_pipe_v1`.
Nenhum transporte foi ativado na instalação Electron dev.4 ou no agente HTTPS.

Fluxo: provedores Win32 básicos → coletor/cache independentes → Named Pipe exclusivo
de desenvolvimento → adaptador Python de leitura → stdio privado do Electron main
→ preload limitado → renderer. O intermediário Python evita instalar um addon FFI
no Electron. Cada sessão é explícita e limitada; não há coleta permanente/autostart.

- Nome local fixo por versão, com sufixo aleatório de sessão; `FIRST_PIPE_INSTANCE`
  e um handle mantido durante toda a sessão, sem lacuna entre reconexões.
- DACL protegida com uma ACE para o SID da conta, máscara `0x00120183`, sem
  `FILE_CREATE_PIPE_INSTANCE`/append para o cliente. DACL conferida por leitura nativa.
  Clientes remotos rejeitados pelo Windows, uma conexão/instância por vez.
- Ambas as pontas verificam PID obtido do pipe e identidade do processo cujo handle
  foi mantido desde a criação: usuário, sessão, imagem e timestamp de criação.
  O servidor valida também o token de impersonação do cliente e sempre reverte
  antes de chamar o serviço; falha de reversão encerra o worker.
- Framing v1: comprimento uint32 big-endian + JSON UTF-8; 256 bytes de requisição,
  128 KiB de resposta; confirmação fixa de entrega de um byte antes de desconectar.
  Operações somente `snapshot` e `capabilities`. Sem stop/configuração/execução.
- Prazo total de transação 1,5 s, accept cancelável, admissão global de 2 pedidos/s
  com burst 4, cancelamento overlapped aguardado antes de liberar buffers/handles.
  Não usa `FlushFileBuffers` sem prazo. EOF do pipe anônimo herdado encerra somente
  o filho criado pela sessão, sem endpoint remoto de lifecycle e sem kill.
- Reconexões só ao mesmo processo/handle atestado; não recria worker automaticamente.
  TTL de desenvolvimento, stop cooperativo e erro explícito se o prazo exceder.
- Renderer sem Node/rede, `contextIsolation`/sandbox habilitados. Somente
  `getMetrics()` e `onMetrics(callback)` foram acrescidos ao preload; nenhum nome
  de pipe, caminho, SID, PID ou operação chega do renderer.

**Limite de segurança:** ACL de usuário e atestação de processos não isolam malware
executado sob a mesma conta. O dono pode alterar DACLs/arquivos ou atacar processos
da própria conta. O sufixo aleatório não é segredo de autenticação; não há certificado,
HMAC ou identidade Samsung neste canal. Não se promete isolamento de administrador.
Uma segunda conta real não foi usada no teste nativo; há inspeção efetiva da DACL,
testes de política/identidade com mocks e rejeição nativa de PID inesperado da mesma conta.

O restante deste arquivo conserva o contrato lógico e os requisitos de projeto que
orientaram a implementação; resultados físicos são documentados na entrega de integração.

`ipc.py` implementa um serviço de leitura chamado diretamente pelos testes.
**Não é um servidor de named pipe**, não consulta tokens Windows, não aplica ACL
nativa e não autentica um processo real nesta entrega. Os testes de política usam
atestados sintéticos. Não conectar esse serviço a um canal que confie na identidade
informada pelo cliente.

## Contrato atual

Somente dois pedidos JSON completos, sem parâmetros adicionais:

```json
{"v":1,"op":"snapshot"}
```

```json
{"v":1,"op":"capabilities"}
```

Sem operações de configuração, histórico, subscribe, shell, caminho, grant, stop,
Steam/CS2 ou energia. Uma consulta só lê cache, nunca aciona um provedor.
`capabilities` lista slots declarados, não promete sensores detectados; indica
`transport=not_implemented` e ausência de provedores reais incluídos no pacote.

Requisição: máximo 256 bytes. Resposta: máximo 128 KiB. JSON UTF-8 estrito, objeto
único, versão inteira, chaves exatas, sem duplicatas/NaN/infinito. Token bucket global:
rajada de quatro pedidos, reposição de dois por segundo, sem mapa ilimitado por PID.
Erros não refletem conteúdo recebido, identidade, caminhos ou mensagens de exceção.
Coletor em encerramento/parado não serve um snapshot como se estivesse em execução.

O parser recebe separadamente `PeerEvidence`, exclusivamente do adaptador de
transporte confiável. Exige autenticação confirmada, conta/SID e sessão esperadas,
origem local; os mesmos campos enviados em JSON não autorizam nada. Essa decisão
lógica foi testada, **não a captura/validação nativa desse atestado**.

## Adaptador Windows futuro — exige implementação e autorização próprias

1. Named pipe local dedicado ao monitoramento, nome por instalação/sessão, sem
   listener TCP, sem abertura de firewall e sem reutilizar identidades do Samsung.
2. Descritor explícito e protegido, limitado à conta/logon autorizado. Não usar
   descritor padrão, `Everyone` ou anônimo. Separar direitos de leitura/escrita de
   dados do direito de criar instâncias do pipe; não conceder `FILE_GENERIC_WRITE`
   ao cliente indiscriminadamente. Limitar número de instâncias/conexões e mensagens.
   [Microsoft: segurança e direitos de named pipes](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights).
3. Rejeitar clientes remotos na criação do pipe. Tratar endpoint já ocupado como
   falha fechada; não conectar automaticamente a outro servidor por coincidência
   de nome. Não permitir que o cliente substitua o SID/sessão esperados.
4. Obter identidade do cliente pelo contexto autenticado do Windows, verificar
   SID/sessão e correlação com processo. Se usada impersonação, checar o retorno,
   consultar o token apenas para validação e garantir `RevertToSelf` em `finally`.
   Falha de impersonação impede servir o pedido; não elevar para contornar isso.
   [Microsoft: ImpersonateNamedPipeClient](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-impersonatenamedpipeclient).
5. Cliente deve validar também o servidor e a instalação esperada antes de exibir
   dados como confiáveis. Nome do pipe ou PID isoladamente não prova identidade.
   ACL da conta não isola malware com a mesma conta, que continua fora da proteção
   prometida. Não armazenar senha/HMAC nem distribuir segredo do agente para este IPC.
6. Adicionar framing limitado, prazo absoluto de leitura/escrita, backpressure,
   cancelamento de I/O e liberação de todos os handles. Fragmentos, cliente lento,
   desconexão e concorrência precisam de testes nativos separados. O parser atual
   recebe um frame completo e não comprova essas propriedades de transporte.
7. Integrar futuramente apenas no Electron main, com preload pequeno, esquema e
   origem/frame validados, contextIsolation/sandbox preservados e renderização por
   texto seguro. Nenhum dado de telemetria vira HTML, caminho de arquivo ou comando.

A integração HTTPS para Samsung e eventual cliente desktop autenticado continuam
sujeitas ao gate TLS já documentado; IPC de leitura não aplica uma correção indireta
ao agente. Nenhuma dessas etapas foi ativada na instalação dev.4.
