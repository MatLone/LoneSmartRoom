# Launcher seguro — preparação isolada (24/10/2026)

Implementação preparada na branch `feature/ui-migration-preview`, sobre o checkpoint
`78101019515b6f056760ef90c789e9b412a38261`. **Não ativada.** O agente permanece offline,
HKCU Run não foi alterado e nenhum teste abriu a porta 8776. Não houve execução de
Steam, CS2, WoL, comandos de energia ou aplicativo instalado.

## Código e arquitetura

- `agent/windows/agent_launcher.py`: supervisor e bootstrap fixos; não importa
  `secure_agent` na importação do launcher. Aceita somente ausência de argumentos
  ou o modo interno `--worker`; não recebe executáveis, comandos ou parâmetros.
- `agent/windows/launcher_win32.py`: caminhos locais sem reparse points, identidade
  do token, detecção de elevação, ACLs e mutex nativo. Apenas biblioteca padrão.
- `agent/windows/launcher_logs.py`: JSONL com esquema fechado e rotação serializada.
- `scripts/test-agent-launcher-isolated.py`: suíte reproduzível que bloqueia
  bind/connect e permite Popen real somente para o helper descartável dos testes.

O supervisor usa caminhos absolutos derivados da instalação, valida os arquivos e
o prefixo da venv, rejeita contexto elevado e cria **um** bootstrap com:

```python
[pythonw_absoluto, '-I', '-B', launcher_absoluto, '--worker']
# executable=pythonw_absoluto, cwd=raiz_absoluta, shell=False, close_fds=True
# stdin/stdout/stderr=DEVNULL, CREATE_NO_WINDOW; sem retry ou fallback
```

Os argumentos são uma lista; espaços não são interpretados por shell. `-I` exclui
CWD, user site e PYTHONPATH da resolução inicial. Somente a pasta fixa dos módulos
do projeto é reinserida. Variáveis PYTHON* são removidas do ambiente do filho. O
interpretador fica em `.venv/Scripts/pythonw.exe`; o destino final é exclusivamente
`agent/windows/secure_agent.py`, com o verbo fixo `serve`, executado via runpy no
bootstrap. Não são expostas novas interfaces remotas ou de gerenciamento.

O bootstrap verifica dependências conhecidas e o ambiente, define CWD novamente e
mantém o mutex enquanto o agente executa **no mesmo processo e thread proprietária**.
O supervisor aguarda e registra o código de término, sem relançar ou matar processos.
`child_created` e `bootstrap_ready` **não comprovam agente online**: somente uma
consulta HTTPS autenticada futura poderá demonstrar disponibilidade operacional.

## Instância única

Mutex global por SID da conta, com nome derivado de SHA-256, compartilhado entre
sessões e cópias do launcher. DACL protegida concede acesso somente ao SID atual.
A aquisição é atômica, com espera zero: um bootstrap prossegue e os demais saem
com `duplicate`/18 **antes de importar ou executar o agente**. Inicializações
simultâneas podem criar brevemente supervisores/bootstraps adicionais; não criam
dois agentes via esse mecanismo.

O proprietário é o bootstrap, não o supervisor. Se o supervisor terminar, o agente
continua protegido. Se o proprietário falhar, o kernel libera/abandona o mutex;
uma próxima execução adquire-o ou recebe WAIT_ABANDONED, registra recuperação e
valida novamente o ambiente. Não há arquivo de lock persistente nem PID reciclado.
Sem banco compartilhado do launcher, não há estado seu a recuperar após abandono.
Referências: [Microsoft — mutexes](https://learn.microsoft.com/en-us/windows/win32/sync/mutex-objects)
e [WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

Compatibilidade com o mecanismo antigo: dentro do mutex, consulta fixa e somente
leitura de processos Python/`secure_agent.py` e listeners 8776, via PowerShell do
diretório obtido por GetSystemDirectoryW, sem PATH/SystemRoot fornecidos pelo chamador.
Se houver ocupação ou a consulta falhar, não executa o agente. Não encerra processos.
**Limitação:** uma execução legada direta pode nascer depois desse snapshot porque
não usa o mutex. O bind exclusivo existente é a última barreira, após inicialização
do Store. A garantia de exclusão antes do Store aplica-se às entradas que usam o
novo launcher. A futura migração deve ocorrer com o agente parado, sem manter duas
entradas de startup; wrappers legados permanecem intocados nesta entrega.
O comando existente `install-startup` ainda gera a entrada direta antiga: não deve
ser reutilizado após uma futura migração sem revisão específica desse gerenciamento.

## Logs seguros

Destino futuro: `.runtime/agent-startup-logs/startup.log`, na raiz 2.0, fora do Git.
**Esse diretório operacional não foi criado.** Logs dos testes ficaram somente em
diretórios descartáveis de `.cache/tests`, eliminados após cada teste.

- JSONL: UTC, PID, evento enumerado e, quando aplicável, fase, código numérico ou
  nome de dependência em lista fechada. Sem mensagens livres ou traceback.
- Eventos: tentativa, validação de caminhos, ambiente inválido, dependência ausente,
  falha de criação, filho criado/finalizado, duplicidade, ocupação legada,
  recuperação de mutex e falha do agente.
- Nunca grava argumentos de exceções, ambiente, credenciais, SID, conteúdo de
  certificados, chaves privadas, HMAC, senhas, tokens ou informações da memória.
- Diretório e arquivos criados com proprietário atual e DACL protegida de acesso
  exclusivo à conta. Verifica ACL existente; **não corrige ACL ampla automaticamente**.
  Links, junctions, hardlinks de arquivo e objetos de outro proprietário são recusados.
- Até 65.536 bytes por arquivo; atual + três backups `.1`–`.3`, total normal máximo
  **256 KiB**. Retenção por tamanho/quantidade, sem prazo fixo em dias. A rotação e
  os append são protegidos por outro mutex, com timeout de 3 segundos.
- Nenhum envio externo. `.runtime/` e `.cache/` já estão ignorados no Git, incluindo
  arquivos rotacionados. Direitos administrativos com tomada de posse e malware
  executando como a própria conta não são barrados por uma DACL por usuário.

Se o logger/ACL não puder ser inicializado, retorna 21 e não lança o agente; não
cria um log alternativo desprotegido. Se Python, suas DLLs ou o próprio launcher
nem chegarem a executar, não haverá recibo local. Contexto elevado é recusado antes
da criação de logs. Essas ausências de log precisam de diagnóstico Windows externo.
Modelo da DACL: [Microsoft — Security Descriptor String Format](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-descriptor-string-format).

## Testes e evidências

**77 testes Python aprovados, zero falhas, erros ou skips:** 42 do launcher e 35 de
preservação, recuperação WoL e executores Steam/CS2 com Popen substituído.

Cobertura: início simulado; caminhos/cwd inválidos; dependências ausentes/quebradas;
falha de Popen/espera; argumento externo rejeitado; token elevado/venv incorreta;
duplicidade; dois processos substitutos concorrentes; mutex abandonado; recuperação
após falha; término inesperado; esquema/sanitização; ACL exclusiva; recusa de ACL
ampla sem modificá-la; reparse/hardlinks; retenção e escrita concorrente.

Além disso: **11 cenários Node WoL**, **85 assertivas Electron Tray** e **51 de
política/preload** aprovados; 86 registros do manifesto de recuperação verificados.
Testes nativos usam somente subprocessos CLI descartáveis (`launcher_substitute.py`)
e nomes `Global\LoneSmartRoom.LauncherTests.<uuid>`, nunca o mutex operacional.
Permissões são aplicadas somente a arquivos temporários próprios.

Execução reproduzível (sem agente/rede):

```powershell
& .venv/Scripts/python.exe -B scripts/test-agent-launcher-isolated.py
```

Os primeiros testes nativos detectaram que a máscara genérica GA no descriptor do
mutex não permitia reabertura. Substituída por MUTEX_ALL_ACCESS explícita. Também foi
corrigida uma corrida apenas na limpeza dos helpers. O sandbox bloqueou a criação
de hardlink de teste; a suíte nativa final rodou no contexto do usuário, sem UAC ou
mudança de privilégio, e passou. Essas falhas não foram ignoradas.

`preservation.json`: **269 arquivos protegidos sem diferenças**, incluindo fontes
anteriores, perfil/instalação Windows e cinco arquivos de estado privado do agente;
zero grants, zero processos de agente/launcher/Electron e zero listeners 8776.
Não houve descriptografia. Backup `Windows-before-dev4-20261024T174801Z` novamente
verificado: 72 arquivos, 27 diretórios, 8.589.376 bytes, hashes/tamanhos e ACL exclusiva
válidos; manifesto `13c12ff4d0e896dda9915b4d8d9b337aa480565059e844ac6bc41a9932444dcc`.

Nesta entrega **não foi repetida a suíte HTTPS com listeners efêmeros**, nem o teste
físico Android–Windows: o runner impede toda rede. A preservação de HTTPS/HMAC,
certificados e permissões é comprovada por hashes/contagem e ausência de alterações,
não por nova validação operacional. A pendência TLS permanece separada e sem correção.

## HKCU Run: plano preparado, NÃO aplicado

Valor `REG_SZ` `LoneSmartRoomSecureAgent`, em
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

Atual, confirmado somente em leitura (221 caracteres):

```text
"<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.venv\Scripts\pythonw.exe" "<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\agent\windows\secure_agent.py" serve
```

SHA-256 do texto UTF-8, sem newline:
`3139f837ebc03ab77c5c16bc00fcb76031fb6a50ef8ccbcd4a014d6c4b509dc5`.

Proposta futura, **não executar agora** (223 caracteres):

```text
"<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\.venv\Scripts\pythonw.exe" -I -B "<USERPROFILE>\Documents\ChatGPT\Lone Smart Room\Lone_Smart_Room_2.0\agent\windows\agent_launcher.py"
```

`run-migration-plan.json` contém o valor antigo e o proposto, sem escrever no Registro.
Ambos abaixo do limite de 260 caracteres. A entrada continua por login, sem serviço,
tarefa agendada ou elevação. **O launcher não resolve ausência de despacho pelo Windows.**
A divergência anterior entre consultas diretas e WMI continua inconclusiva; não
reescrever a entrada apenas para fazê-la aparecer no WMI.

Após autorização separada:

1. Conferir commit/hashes desta implementação, backup, conta não elevada e estado
   offline/zero grants; recusar se a entrada tiver divergido do valor registrado.
2. Fazer primeiro **uma execução manual do launcher**, sem mudar Run. Verificar
   tentativa, cwd, ausência de duplicação, listener HTTPS na interface privada já
   autorizada e status autenticado no Samsung, sem comandos operacionais.
3. Se aprovada, solicitar autorização específica para trocar **somente esse REG_SZ**,
   preservando nome/tipo, valor anterior e recibo protegido. Nenhuma segunda entrada.
4. Teste posterior de login/reinicialização exige autorização própria; observar os
   logs antes de concluir se houve despacho ou falha de bootstrap.

## Reversão e riscos

**Nada foi ativado nesta tarefa:** a reversão do código é um `git revert` do commit
desta entrega, mantendo os checkpoints e sem reset destrutivo. Isso não desinstala
nem restaura estado operacional. Não remover o launcher se futuramente Run depender dele.

Se a migração de Run vier a ser aprovada e apresentar problema: preservar logs e
confirmar qual processo está ativo; qualquer parada deve ser autorizada, sem matar
outros Python. Com o agente parado, restaurar somente o REG_SZ anterior e conferir
seu hash. Não apagar `.runtime/secure-agent`, perfil Electron, backups ou credenciais;
não executar restore global do Registro. Não reiniciar automaticamente para testar.

Limitações restantes: Python e venv podem mudar de local; não há reparo automático;
os dois processos Python consomem recursos adicionais; consultas CIM/TCP podem falhar
e bloquear o início por segurança; não há reinício automático após crash; persistência
de logs em falha de energia não é garantida. Não há Authenticode do launcher Python.
A proteção depende da integridade da conta, do código e da venv locais.

**Parar aqui. Próxima autorização necessária: uma execução manual controlada do novo
launcher com o agente real; HKCU Run continuará intocado nesse primeiro teste.**
