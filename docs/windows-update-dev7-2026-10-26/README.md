# Atualização assistida Windows dev.6 → dev.7

26/10/2026. Checkpoints `d4f39a7`, `de23ee2` e anteriores preservados.
Branch `feature/ui-migration-preview`.

**Resultado: Windows 2.0.0-dev.7 instalada, aplicativo fechado.** Uma abertura
do NSIS e um acionamento de Instalar, sem repetição. O dashboard, widget, sensores
e IPC de monitoramento não foram iniciados. Agente HTTPS original ativo e zero grants.

## Gates anteriores à abertura

Conferidos antes do NSIS: dev.6 registrada e íntegra; 114 arquivos de payload
iguais ao artefato dev.6; instalação com 117 arquivos incluindo metadados e log;
perfil com 77 arquivos; quatro backups anteriores inalterados. Nenhum Electron,
coletor, intermediário, ADLX ou instalador residual.

Mesmos supervisor 5024, worker 18304 e redirectors esperados, verificados por
imagem, argumentos, criação e cadeia. Listener LAN único 8776, TLS 1.3,
hostname/certificado/pin e GETs status/apps autenticados HTTP 200, zero grants
e comandos pendentes. Fonte do repositório e artefatos anteriores íntegros.

O NSIS foi recalculado e conferido:

- `Lone-Smart-Room-2.0.0-dev.7-x64-Setup-DEV.exe`
- **105740715 bytes**
- SHA-256: **`0033ee706adfd9edcd29d2f87b5bddc5751bcbd2a6337125e09adb84d49d7870`**
- Payload x64, mesma identidade `com.lone.smartroom`, ícones oficiais e manifesto
  do monitoramento válidos; atualização por usuário, assistida, sem elevação,
  `runAfterFinish=false`, sem exclusão intencional do perfil.

Condições/licença ADLX permanecem as da
[revisão do pacote](../windows-dev7/LICENSE-REVIEW.md): avaliação interna local,
licença original preservada; fontes/headers/helper e DLL do driver não distribuídos.
Nenhuma liberação pública ou aceite de nova EULA foi realizado.

A primeira leitura do AppData feita no sandbox apontou para seu diretório
redirecionado, onde não existe a instalação. Foi refeita no contexto real do
usuário, ainda sem abrir o NSIS. Não foi divergência da instalação nem tentativa
de reparo. Todos os gates passaram depois disso.
[Recibo final anterior à abertura](evidence/preflight-pass.json).

## Backup atualizado e protegido

Local:
`<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev7-20261026T152048Z`

| Conteúdo | Quantidade |
| --- | ---: |
| Instalação dev.6 | 117 arquivos |
| Perfil Electron de produção | 77 arquivos |
| Total de dados | **194 arquivos / 402160249 bytes** |
| Diretórios registrados | 39 |
| Entradas de ACL conferidas, incluindo metadados | **238** |

Manifesto SHA-256:
**`3edc66d1c8fcdc55efa31ef06ea6697f19e6866bb4406a3f13b40b6c3ea70043`**.
Os hashes dos três arquivos de controle estão em
[backup-metadata-hashes.json](evidence/backup-metadata-hashes.json).

O backup está fora do Git e do destino do instalador. Sua raiz tem DACL protegida,
owner da conta autorizada e somente regras de acesso dessa conta; a verificação
independente confirmou todas as 238 entradas antes e depois da atualização.
Isso não pretende isolar administradores com privilégios de recuperação do Windows.

Todos os arquivos de origem foram abertos exclusivamente antes da cópia; nenhum
arquivo bloqueado foi forçado. Conjuntos de diretórios/arquivos e hashes da origem
foram conferidos antes/depois da cópia. A verificação independente confirmou
hashes, tamanhos e estrutura. O perfil foi novamente comparado após instalar.

Dados do perfil foram copiados opacamente, sem descriptografar seu conteúdo.
Manifesto com caminhos detalhados/SID e dados de perfil permanece somente no
diretório protegido. Não foi copiado nem alterado diretamente o banco do agente
para realizar esse backup. Backups pré-dev.3/4/5/6 continuam intactos.
[Cópia](evidence/backup-result.json), [verificação independente](evidence/backup-independent-after.json)
e [ACL final](evidence/backup-acl-after.json).

## Sequência assistida observada

1. Gates e backup independente aprovados **antes** da abertura única do NSIS.
2. Confirmada a substituição dos arquivos da instalação existente, pelo botão Sim.
3. O diálogo inicial fechou; a captura da janela antiga perdeu seu alvo.
   A nova janela foi reidentificada e observada, **sem repetir Sim ou lançar outro NSIS**.
4. Conferido o destino existente:
   `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room`.
5. Instalar acionado uma única vez; observada a etapa de progresso.
6. Observada a página de instalação concluída. Não existia opção marcada ou
   disponível para executar o aplicativo. Concluir fechou somente o assistente.
7. Conferências posteriores feitas por leitura/parse de arquivos, sem abrir
   qualquer executável instalado, atalho, portátil, sensor ou IPC do projeto.

Não foi observado bloqueio de SmartScreen/Defender, elevação inesperada ou janela
Error do instalador. Nenhuma proteção foi desativada/contornada. O erro de captura
na troca de diálogo foi da observação, não evidência de erro do NSIS.

[Confirmação](evidence/01-update-confirmation.jpg) ·
[Destino](evidence/03-current-stage.jpg) ·
[Instalando](evidence/04-after-install-click.jpg) ·
[Concluído sem execução](evidence/05-installation-stage.jpg).
O texto acessível coletado imediatamente após Instalar ainda refletia a página
anterior, enquanto a imagem já mostrava progresso. A conclusão foi verificada
em observação posterior independente, sem reutilizar índices dessa transição.

## Conferência estática instalada

| Item | Resultado |
| --- | --- |
| FileVersion e registro | **2.0.0-dev.7** |
| ProductVersion numérico | 2.0.0.0, conforme pacote aprovado |
| Aplicativo | `<USERPROFILE>\AppData\Local\Programs\Lone Smart Room\Lone Smart Room.exe` |
| SHA-256 do aplicativo | `83230a8511efd2d0b6383826456cd95c59d3324ac5b169d3265bfb549d4c2559` |
| Authenticode | **NotSigned** |
| Payload instalado | **114 arquivos iguais ao artefato** |
| Metadados adicionais | Desinstalador exato do NSIS e ícone oficial; total instalado **116 arquivos** |
| ASAR/recursos selecionados | 18 recursos instalados iguais aos fontes aprovados |
| Sidecar | 39 arquivos + manifesto/pin íntegros; CPU/GPU/RAM/discos e Named Pipe presentes |
| Perfil | **77 arquivos byte a byte iguais**, inclusive preferências |
| Preferências | Esquema 1, dashboard, bandeja automática desligada; posições/dimensões preservadas |
| Atalho Menu Iniciar | Target correto, existente, sem argumentos; não executado |

O instalador removeu da pasta de programa o `debug.log` antigo de **332 bytes**.
Ele foi preservado e conferido no backup em `data/installation/debug.log`, SHA
`9144f2dc7ef0980c4478a0f5c020275765dc7a301ea505567b136c57c9979ad2`.
Não houve exclusão manual nem tentativa de recolocá-lo na produção.
Isso explica 117 arquivos antes e 116 depois, sem perda do perfil ou do log para
recuperação. [Registro](evidence/old-log-preservation.json).

O modelo puro foi analisado isoladamente; nenhum host foi inicializado. Os bytes
do host/renderer instalados correspondem à correção aprovada. Confirmados no pacote:

- Ingresso ADLX **1,5 s**; expiração GPU **3 s ativa / 11 s inativa**.
- Atualizando até nova amostra dinâmica válida/fresca e indisponibilidade explícita
  após **10 s**, sem transformar esse prazo em tolerância de idade.
- Primeiro frame inválido, null, zero válido e desatualizado conservam tratamentos
  distintos; contrato v1 e verificações de manifesto/identidade preservados.
- Preload restrito, CSP sem cliente operacional de rede e hardening mantidos.
  Não há novo cliente Electron–agente ou concessão de permissões.

Essas são **verificações estáticas de presença/integridade da implementação**,
não leituras reais dos sensores nem validação dinâmica da instalação.
[Recursos](evidence/installed-resources.json) e [políticas](evidence/monitoring-static.json).

## Estado final e limites

À conferência posterior, mesmo agente original, listener único 8776 e autenticação
TLS 1.3/HTTP 200; **zero grants e zero comandos pendentes**. Certificados, HMAC,
identidades cifradas, revogações e esquema do banco íntegros. Os GETs de status
usam a identidade existente somente em memória; nonces/last-seen podem ser
registrados normalmente pelo servidor. Não houve escrita direta ou backup do banco.

Sem processos Electron, coletor, intermediário, ponte ADLX ou instalador.
Run/RunOnce, Inicializar, serviços, tarefas e firewall não diferiram do inventário
inicial nem do gate imediatamente anterior à instalação. Nenhuma nova inicialização
automática. A observação histórica OneSettings permanece inconclusiva, sem mudança
durante esta atualização nem intervenção na tarefa.

98 arquivos de fontes, 80 arquivos de artefatos/runtimes anteriores e 86 arquivos
operacionais protegidos sem diferenças. Android, credenciais, DLL do driver e
pareamento preservados. Não se realizou confirmação física no Samsung.
[Preservação](evidence/preservation-after.json) e [status autenticado](evidence/authenticated-final.json).

A primeira execução física da dev.7 ainda precisa de autorização. Até lá, a
interface, sensores, widget, bandeja e retomada no **pacote instalado** não são
declarados homologados dinamicamente. PDH opcional e pendências TLS/Crashpad/
encerramento gracioso do agente continuam separadas, sem correções nesta etapa.

## Reversão proposta — não executada

1. Se aparecer um problema, preservar evidências; não reinstalar/reverter
   automaticamente, limpar perfil ou mexer no agente.
2. Obter autorização específica. Se Electron tiver sido aberto no futuro,
   fechá-lo normalmente por Sair e confirmar que seus próprios componentes
   terminaram. Não usar força/reinício para liberar arquivos.
3. Preservar uma cópia protegida do estado/perfil novo antes de qualquer retorno.
4. Conferir o manifesto `3edc66d1…70043`, todos os 194 hashes/tamanhos e ACLs do
   backup acima. Restaurar sob a mesma conta Windows; não descriptografar credenciais.
5. Escolher um procedimento revisado para recuperar binários **e registro de
   instalação/desinstalador** da dev.6. O NSIS dev.6 preservado tem hash
   `fccf8683210f24577462b1b0ef5ce100cf1373e23beac4ac5b91383dbfb0b545`.
   Não presumir que ele aceitará downgrade; se bloquear, parar. Cópia cega de
   executáveis sobre o registro dev.7 não é um plano completo de recuperação.
6. Perfil é esquema 1 e não mudou nesta instalação. Restaurá-lo somente se
   necessário, guardando o estado novo; verificar hashes/ACL antes de autorizar
   uma execução. Não desinstalar nem apagar dados para forçar retorno.
7. Confirmar agente original ativo, autenticação e zero grants antes/depois.

Nenhuma restauração ou rollback ocorreu. O novo commit desta etapa é apenas
documental; revertê-lo não reverte uma instalação Windows. Fonte funcional
permanece nos checkpoints preservados; não foi implementada funcionalidade nova.

**Parada: dev.7 instalada, aplicativo fechado, agente HTTPS ativo, zero grants.
Nenhuma primeira execução física está em andamento ou será iniciada sem autorização.**
