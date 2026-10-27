# Integração dos adaptadores com a Central

Fluxo implementado: cinco adaptadores Python → EvidenceHub/cache existente →
worker mock limitado → provider do Electron main → host/contrato existente →
preload já restrito a cenários enumerados → cartões existentes.

Ativação exige simultaneamente revisão isolada, prévia de diagnóstico e
`--lone-diagnostic-adapters-development`. Sem isso, não há worker. Os leitores
reais continuam não importados/não ativados. O worker executa os adaptadores e
o cache em vez de confiar em strings de estado recebidas do renderer.

A entrada fixa é `{v:1,scenario:<enum>}` de até 256 bytes. Há apenas uma consulta
pendente, timeout de 900 ms, resposta de até 24 KiB, além dos limites existentes
do host (500 ms, 18 KiB sanitizados). O processo usa Python absoluto existente,
`-I -B`, `shell:false`, cwd fixo e ambiente mínimo. Não recebe caminhos, comandos,
credenciais ou parâmetros nativos. EOF encerra o worker normalmente. Timeout
fecha stdin e descarta o resultado; não usa kill nem reparo automático.

O audit hook do worker rejeita sockets, Registro, subprocessos, os.startfile e
carregamento/chamadas ctypes. Toda evidência é `simulation:true`; o contrato
continua rejeitando evidência operacional nessa composição. Os 13 cenários da
interface são mapeados aos casos dos adaptadores, incluindo reconexão, erro,
inatividade normal e startup inconclusivo. Não existe promoção de ausência de
evidência a Saudável.

Validação executada: 70 verificações ponta a ponta com worker Python mock real,
main host e modelo real de cartões; encerramento por EOF e processos de teste
concluídos. Regressões Node: 891 verificações em 12 suítes. As cinco pendências
conhecidas continuam presentes no sidecar. Não houve consultas ao agente ativo,
inspeção de grants operacional, coleta física ou abertura da instalação Windows.

CPU/RAM desse worker ainda não foram medidos em uso interativo. Seu catálogo é
finito (14 cenários) e o cache continua limitado; não há loop de sondagem. A futura
ativação passiva real exige fonte revisada, timestamps atuais, autorização própria
e sessão separada. Reverter este commit desliga a integração opt-in; não há banco,
perfil, serviço, certificado ou instalação para restaurar.
