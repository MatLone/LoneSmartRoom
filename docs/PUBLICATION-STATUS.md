# Cópia saneada de publicação — 2026-10-29

Esta cópia preserva as nove branches de desenvolvimento e a topologia de 206
commits, incluindo um commit WIP separado com os 11 arquivos SignalRGB pendentes.
O repositório original e suas duas worktrees não foram reescritos.

A branch main avança por fast-forward até o checkpoint documental completo, sem
incorporar o WIP SignalRGB. O commit do antigo main continua ancestral de main.
O trabalho SignalRGB fica em feature/signalrgb-control e ainda exige validação.
As demais branches preservam seus marcos históricos saneados; não houve merge
funcional de branches divergentes.

## Privacidade e portabilidade

- Caminhos pessoais foram removidos; caminhos Python usam Path.home() e os
  equivalentes PowerShell usam USERPROFILE.
- O segmento de rede real foi substituído por uma rede privada sintética
  172.31.250.0/24. O MAC pessoal padrão foi trocado por endereço sintético local.
  Configure explicitamente os valores do seu ambiente em estado local ignorado.
  Esses valores não descrevem a instalação operacional do autor.
- Constantes RFC1918 e fixtures sintéticas de testes foram preservadas: não são
  evidências de rede privada real nem credenciais.
- Logs, recibos JSON operacionais e capturas de tela pessoais foram excluídos
  somente do histórico publicado. Alguns links históricos para essas evidências
  poderão não resolver. Os originais continuam preservados localmente.
- Código de todos os módulos, assets dos aplicativos e marca, Gradle Wrapper,
  fontes ADLX e licença de redistribuição foram mantidos.
- Não foram encontrados tokens ou material de chave privada pelos padrões
  utilizados. Delimitadores PEM em prepare-agent-candidate.py são verificações
  contra inclusão de chaves, não chaves privadas. Auditoria heurística não prova
  ausência absoluta de segredos.

## Verificações executadas

- Topologia e correspondência dos commits conferidas por mapa local antigo/novo.
- Nenhum arquivo de código perdido em qualquer uma das nove branches.
- Python: análise sintática sem erros; JavaScript/CJS: 61 arquivos sem erros.
- OpenRGB SDK: 70 verificações; controle RGB: 68; NEX RGB: 14.
- Android WoL: 11 cenários sem pacotes reais; estados de telemetria: 19 cenários.
- Telemetria HTTPS com mocks/loopback: 17 testes passaram; o teste JVM adicional
  depende de classes Android compiladas e cache Kotlin ausentes na cópia limpa.
- A regressão Windows no WIP registrou 25/33 suites aprovadas, 3.281 assertions.
  As demais dependem de caches/runtime/venv de desenvolvimento ou de atualização
  dos mocks para o WIP SignalRGB. Não se declara esse trabalho homologado.
- Testes antigos do leitor de diagnóstico também têm incompatibilidades de mocks
  registradas; a função HTTP correspondente não foi alterada pelo saneamento.

Nenhuma instalação, execução de sensores reais, controle RGB físico, comando de
energia, jogo ou consulta ao agente operacional foi necessário para publicar fontes.
O saneamento não resolve pendências funcionais TLS, Crashpad, bootstrap ou RGB.

## Restauração e rastreabilidade

O bundle original verificado, cópias dos arquivos pendentes e mapa de commits
permanecem fora das referências publicadas. Novos hashes são específicos desta
cópia. Não fazer fetch/merge desta cópia para sobrescrever o histórico original.
Para desenvolvimento remoto, clonar o repositório publicado em novo diretório.
