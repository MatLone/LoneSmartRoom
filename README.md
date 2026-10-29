# Lone Smart Room 2.0

Central de controle e monitoramento do PC e do ambiente, com dashboard Windows,
aplicativo Android e agente HTTPS autenticado. Projeto em desenvolvimento:
interface presente no código não implica integração física homologada.

## Três áreas oficiais

- **Controles**: dispositivos, configurações e integrações RGB locais.
- **Monitoramento PC**: CPU, GPU AMD, RAM, discos, histórico e diagnóstico.
- **Gamer Launcher**: biblioteca, sessões, permissões e integrações de jogos.

A identidade oficial usa preto/grafite, vermelho #FF153F e apenas o E de LONE
vermelho. NEX oferece consultas e propostas locais tipadas; texto livre não é uma
API genérica de comandos.

## Arquitetura e estrutura

| Diretório | Conteúdo |
| --- | --- |
| `apps/windows-ui` | Electron, dashboard, preload restrito, widget, bandeja, Touch Panel, overlay, RGB e NEX |
| `apps/android` | Kotlin, interface WebView, recursos, Gradle e cliente HTTPS |
| `agent/windows` | HTTPS, HMAC, antirreplay, identidade, armazenamento e launchers |
| `agent/development` | Ciclo de vida e integrações em desenvolvimento |
| `monitoring` | Provedores, contratos, cache e Named Pipe protegido |
| `telemetry` | Contratos e transporte autenticado de métricas |
| `diagnostics` | Evidências e classificação de saúde somente leitura |
| `native` | Ponte AMD ADLX |
| `contracts` | Contratos versionados |
| `third_party` | Fontes e licenças externas, incluindo ADLX |
| `tests`, `scripts` | Testes, builds e inspeções |
| `docs` | Arquitetura, evidências, limitações e procedimentos |

No Windows, o processo principal intermedia operações permitidas. O renderer
usa contextIsolation e preload restrito. Provedores alimentam coletor, cache e
Named Pipe local. Cada amostra conserva origem, unidade, timestamp e validade;
ausência de sensor nunca vira zero. Android usa HTTPS autenticado, pinagem e
identidade persistente. Permissões de leitura e de comandos devem permanecer
separadas; telemetria em desenvolvimento exige implantação coordenada.

## Estado das funcionalidades

O código inclui monitoramento básico e AMD, histórico, diagnóstico, ferramentas
locais, biblioteca, NEX e painéis auxiliares. Integrações físicas têm limitações
próprias: OpenRGB depende das capacidades e do readback; SignalRGB está em
implementação e depende das permissões da API. FPS externo, automações e recursos
por dispositivo não devem ser apresentados como reais sem fonte validada.

Permanecem separadas as pendências TLS 10054, inicialização automática,
encerramento cooperativo, avisos Crashpad e homologações físicas específicas.
Não existe temperatura fictícia de CPU. Evidências antigas em docs não garantem
o estado atual das instalações; consulte a branch e o relatório correspondente.

## Requisitos e build sem credenciais privadas

Consultar `docs/toolchain.json`, arquivos de versão e lockfiles. A base utiliza
Node 22.16.x/npm 10.9.x, Python 3.13, JDK 21, Android SDK 35/build-tools 35.0.0 e
Gradle Wrapper fixado. A ponte ADLX x64 requer MSVC e Windows SDK compatíveis.
Respeitar as licenças e condições de redistribuição dos componentes externos.

Com as ferramentas disponíveis, em PowerShell na raiz:

```powershell
# Cria venv local e verifica hashes das dependências Python.
.\scripts\prepare-agent.ps1

# Assinatura debug isolada; não usa chave privada distribuída pelo Git.
.\scripts\android-build.ps1
.\scripts\android-build.ps1 -Tasks @('lintDebug', 'testDebugUnitTest')

# Prepara pacotes Windows; não instala a aplicação.
.\scripts\windows-build.ps1

# Regressões Windows isoladas com substitutos.
node scripts/test-windows-control-center.cjs

# Auditoria offline de todas as refs e do trabalho pendente.
python -B scripts/audit-publication.py
```

A chave original Android não pertence ao Git. Builds comuns usam chave debug
isolada e não devem ser instalados sobre o app pareado. Atualizações compatíveis
exigem a chave original local, conferência do certificado e autorização de
implantação. Nunca desinstalar ou limpar dados para contornar uma assinatura.

Saídas ficam em `apps/android/app/build`, `apps/windows-ui/dist` e `.cache`.
Scripts de validação física exigem revisão e autorização; nem todo script usa mocks.
Clonar/compilar não autoriza iniciar agente, controlar hardware ou executar jogos.

## Publicação e dados locais

Não versionar credenciais, certificados privados, keystores, bancos, pareamentos,
grants, perfis pessoais, logs, dumps, dependências, caches ou instaladores gerados.
O gitignore não remove dados já presentes no histórico. Auditar todas as branches
e seus ancestrais antes do push. Sanear em cópia isolada preservando o original;
não usar force push nem mirror para substituir trabalho remoto.

A preparação de publicação e seus impedimentos estão em
[docs/GITHUB-PUBLICATION.md](docs/GITHUB-PUBLICATION.md).

## Privacidade desta publicação

Esta é uma cópia saneada do histórico. Consulte [o relatório de publicação](docs/PUBLICATION-STATUS.md). Defaults de rede e MAC são sintéticos e devem ser configurados localmente. Logs, recibos operacionais e capturas pessoais foram preservados apenas no backup local. O trabalho SignalRGB pendente está separado em feature/signalrgb-control.
