# Plano único coordenado de implantação e reversão

O fluxo real de desenvolvimento está comprovado. Nenhuma implantação está
autorizada por este documento. O próximo marco deve agrupar a ligação operacional
ao cache, atualização controlada do backend e homologação Android.

## Preparar a ligação ao cache no código, antes da janela de implantação

Hoje o protótipo coloca HTTPS/broker no intermediário que já possui a leitura do
coletor. O agente operacional é um processo separado. É necessário preparar um
relay/cache local **específico e somente leitura**, sem iniciar outro coletor.
Preservar a verificação restrita do Named Pipe existente; não acrescentar o agente
como cliente genérico daquele pipe. Um canal separado precisa validar SID,
sessão, identidade/criação/imagem dos processos, DACL, posse do endpoint e
rendezvous protegido. Mesma conta não significa isolamento forte de processos.

Integrar esse leitor e uma rota fixa `/v2/telemetry` ao código de desenvolvimento
do agente, desativados por padrão. Autorização de leitura específica para o
Samsung, separada de grants Steam/CS2/energia, inicialmente vazia. Não promover
identidade/certificado/banco temporários DEV à operação.

Sem coletor ativo: Indisponível; não iniciar sensores por um GET. Conservar
sequência, geração, origem, UTC/idade acumulada e null/zero/stale. Testar relay,
ACL/identidade, desconexão, reconexão, excesso de payload e rejeição de clientes
com substitutos antes da janela operacional. O limite ADLX 1,5 s e GPU 3/11 s
permanecem. O Android já pausa consultas fora da aba e aplica expiração local.

## Janela única de atualização, sujeita à autorização consolidada

1. Conferir APK dev.10/v24, package, certificado original, versão/aparelho e
   hashes; confirmar agente/listener/grants. Criar backup novo protegido de
   instalação/perfil/runtime e configuração do agente, mantendo os anteriores.
   Se necessário banco ativo, utilizar backup SQLite consistente para destino
   protegido, sem exportar/descriptografar credenciais.
2. Revisar o risco TLS 10054 e o procedimento de parada segura do agente legado.
   São gates operacionais reais: não presumir encerramento gracioso disponível,
   não matar processos nem reiniciar o Windows para contorná-los. Uma eventual
   decisão de risco/parada precisa estar explicitamente coberta pela autorização.
3. Atualizar somente os componentes revisados do runtime/relay e agente, mantendo
   diretórios, certificado/pin, HMAC, identidade e listener 8776. Não criar serviço,
   tarefa, regra de firewall ou entrada de inicialização. A instalação Windows
   dev.7 só será substituída se o pacote do relay revisado exigir essa atualização.
4. Autorizar apenas a leitura de métricas para o Samsung pareado. Confirmar
   status/telemetria autenticados, dados atuais e zero grants de comandos.
5. Atualizar o Android exclusivamente com `adb install -r` do candidato original
   validado. Não desinstalar, limpar dados, refazer pareamento ou alterar assinatura.
6. No Samsung: abrir Monitoramento PC e confirmar CPU/GPU/RAM/C:/D:, unidades,
   origem, horário/idade; comparar a mesma amostra do backend e do cliente. Sair
   da aba para confirmar pausa; retornar exigindo dados válidos e sem valores
   antigos apresentados como atuais. Não iniciar jogos/energia/WoL.
7. Encerrar os componentes de teste normalmente. Manter agente operacional ativo,
   pareamento, dados e zero grants; publicar um relatório consolidado de homologação.

## Reversão e critérios de interrupção

Primeira contenção: desabilitar a rota/leitor e revogar somente o escopo de leitura
de telemetria, preservando o status autenticado e todos os grants zerados.
Restaurar binários/configuração anteriores somente por procedimento de parada
normal previamente aprovado, conferindo hashes e banco íntegro. Não substituir
arquivos carregados ou forçar o agente legado.

Android: preservar armazenamento; usar correção com versionCode maior que 24 e
assinatura original se houver regressão. Não fazer downgrade destrutivo ou `pm clear`.

Interromper a implantação diante de assinatura/hash/aparelho incompatível, dúvida
sobre parada segura, identidade/ACL incorreta, falha de autenticação/pin, ausência
de dados atuais ou necessidade de alteração de sistema fora do escopo aprovado.
Nenhuma dessas falhas deve gerar reparo automático.
