# Plano coordenado — nenhuma implantação executada

## Diferença entre protótipo e operação

O protótipo reúne broker/HTTPS no mesmo intermediário que já lê o Named Pipe.
O agente operacional é outro processo, independente do Electron. Apenas adicionar
uma rota a `StatusServer` não lhe dará acesso àquele cache em memória.

O Named Pipe atual permite o cliente próprio identificado por handle, imagem,
criação, SID e sessão. **Não se deve relaxar essa verificação para aceitar o agente.**
O código implementado nesta etapa não cria esse novo canal operacional.

## Alterações necessárias, sujeitas a revisão posterior

1. Implementar um relay local específico e somente leitura, alimentado pela mesma
   leitura/cache do intermediário, sem coletor duplicado. O agente será consumidor.
   Preferir pipe separado com DACL do SID autorizado, rejeição remota, validação
   de processo/criação/sessão e rendezvous protegido contra substituição. A ACL
   por usuário não isola completamente processos maliciosos da mesma conta.
2. Contrato v1, geração/sequência, origem, idade monotônica acumulada, UTC,
   disponibilidade e limite de tamanho; não renovar amostras no relay. Coletor
   desligado normalmente deve resultar em Indisponível, sem iniciá-lo por um GET.
3. Integrar leitor limitado de cache ao agente e rota fixa `GET /v2/telemetry`.
   Manter hostname/pin/certificado/HMAC/nonce, rede privada e listener 8776.
   Não copiar identidade do Samsung ao Electron, nem criar endpoints de comandos.
4. Política de leitura específica, vazia/desativada por padrão e separada de
   `app_permissions`. Autorizar explicitamente o dispositivo escolhido só para
   métricas; Steam/CS2/energia continuam sem grants. Não migrar todos os pareados
   automaticamente para essa leitura. O JSON/identidade DEV deste teste não deve
   ser promovido a configuração operacional.
5. Uma futura atualização Windows será necessária se o relay entrar no runtime
   do intermediário instalado. Preparar nova versão/pacote apenas com autorização.
   Não alterar agora a dev.7 ou criar serviço/tarefa/inicialização permanente.
6. A atualização do agente precisa de procedimento de parada/retomada aprovado.
   O legado não deve ser presumido compatível com o novo encerramento gracioso.
   Não substituir arquivos carregados, matar processos ou reiniciar o Windows
   para realizar essa migração sem autorização específica.

## Gates antes de habilitar a rota operacional

- Confirmar correção em nova sessão loopback real, não somente em replay: snapshots
  não nulos, CPU/RAM/discos válidos e GPU conforme suporte, timestamps avançando.
- Idades no cliente dentro de TTL, ADLX ≤1,5 s, GPU 3/11 s; nulos e zero válidos
  distintos. Rejeições devem registrar regra sanitizada, sem reabrir a ponte.
- Exercitar relay/ACL/identidade, desconexão/reconexão, cache antigo e múltiplos
  clientes com mocks e testes nativos autorizados. Mensagens somente leitura e
  limites de payload, frequência e timeout preservados.
- Rever o risco conhecido de TLS 10054 antes da ativação. A correção terá tarefa
  própria; esta preparação não certifica a segurança operacional da nova rota
  enquanto a pendência relevante não estiver corrigida/validada ou sob decisão
  de risco explicitamente aprovada. Não reproduzir payloads malformados no agente.

## Backup e atualização futura

Antes de qualquer instalação: aparelho/assinatura/package/code, hashes dos
artefatos, processo/listener original, zero grants, pareamento e versão Windows.
Backup novo e independente da instalação/perfil e configuração do agente em local
com ACL restrita. Se houver snapshot do banco ativo, usar mecanismo SQLite
consistente para destino protegido; não copiar arquivo SQLite inconsistente nem
descriptografar/exportar credenciais em relatório. Preservar os backups anteriores.

Validar por fases: novo relay e leitor → rota habilitada explicitamente → consulta
autenticada local → Android atualizado com `adb install -r` → consulta de métricas
na aba. Atualização do agente/Windows e instalação Android exigem autorizações
próprias. Nunca desinstalar, limpar dados, alterar assinatura, usar `pm clear` ou
refazer o pareamento automaticamente.

Para um teste LAN de desenvolvimento antes da migração operacional, é necessária
identidade própria e perfil de credenciais de teste independente, ou teste Android
instrumentado em memória. O candidato atual usa o AgentVault existente e **não
deve ser repareado contra o servidor DEV**, pois isso substituiria a configuração
real. Não ignorar a pinagem para conectar a um certificado de teste. Porta/rede e
eventuais requisitos de firewall de outro listener exigem revisão específica.

## Homologação futura no Samsung

Com o backend validado e autorizado: verificar status existente; abrir Monitoramento
PC; confirmar fontes, unidades, horário/idade e valores reais; sair da aba e
confirmar pausa; voltar e exigir amostras novas; testar perda/recuperação sem
valores antigos atuais. Indisponibilidades podem ser simuladas apenas em fixture
identificada, sem provocar falha no driver. Não acionar WoL, jogos ou energia.
Preservar agente ativo, pareamento, certificado, credenciais e zero grants ao final.

## Reversão

Feature flag da rota/leitor desativada é a primeira contenção: mantém status e
demais funções existentes. Revogar só o escopo de leitura, sem tocar grants de
comandos. Restaurar binários/configuração anteriores somente por encerramento
normal previamente autorizado e conferindo hashes; nunca forçar o legado.

Android: preferir desligar a consulta de telemetria ou uma build de correção com
versionCode **maior que 24** e assinatura original, preservando o armazenamento.
Não fazer downgrade destrutivo para v23. O contrato não exige migração do AgentVault
ou das preferências WoL. Se qualquer gate falhar, interromper a implantação e
registrar o estado antes de novas ações.
