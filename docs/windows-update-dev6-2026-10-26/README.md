# AtualizaÃ§Ã£o assistida Windows dev.5 â†’ dev.6

**Resultado: 2.0.0-dev.6 instalada e fechada; agente HTTPS original ativo.**
ExecuÃ§Ã£o em 26/10/2026, na branch `feature/ui-migration-preview`, preservando
`7aa50c2`, `b2e64d4`, `2c970dc` e os checkpoints anteriores. Esta entrega altera
somente a instalaÃ§Ã£o autorizada e adiciona documentaÃ§Ã£o; nenhum fonte funcional
foi modificado, compilado ou empacotado novamente. [Resumo](summary.json).

## Gates anteriores ao NSIS

Antes de abrir o instalador: dev.5 confirmada por ASAR, PE e registro de instalaÃ§Ã£o;
mesmo identificador `com.lone.smartroom` e destino por usuÃ¡rio. Nenhum Electron,
coletor, ponte ADLX ou instalador residual. Perfil e trÃªs backups anteriores
conferidos por hashes; banco do agente Ã­ntegro, zero grants e comandos pendentes.
Supervisor/worker, horÃ¡rios de criaÃ§Ã£o, imagens e argumentos conferidos contra a
sessÃ£o original. TLS 1.3, certificado/hostname/pin validados antes de autenticar;
GET status/apps retornaram HTTP 200. Nenhuma identidade nova foi criada.

O NSIS x64 aprovado foi recalculado e inspecionado estaticamente:

```text
Lone-Smart-Room-2.0.0-dev.6-x64-Setup-DEV.exe
SHA-256 fccf8683210f24577462b1b0ef5ce100cf1373e23beac4ac5b91383dbfb0b545
Tamanho 105741349 bytes
```

Origem: `.cache/artifacts/windows/desktop-dev6-gpu-distribution-attempt2/` neste
repositÃ³rio. Payload x64, recursos oficiais, runtime/manifesto e conteÃºdo do
instalador correspondentes Ã  preparaÃ§Ã£o aprovada. Instalador **NotSigned**;
nenhuma proteÃ§Ã£o foi desativada ou contornada e nÃ£o houve elevaÃ§Ã£o.

Uso ADLX permanece interno/local, conforme os avisos da preparaÃ§Ã£o. A licenÃ§a
original acompanha o runtime; nÃ£o se redistribui DLL AMD, headers, helper ou
samples. NÃ£o hÃ¡ instalaÃ§Ã£o de driver, serviÃ§o ou tarefa. PublicaÃ§Ã£o a terceiros
continua pendente de revisÃ£o/EULA, separada deste uso local autorizado.

## Backup atualizado e verificado

```text
<USERPROFILE>\Documents\Lone Smart Room Backups\Windows-before-dev6-20261026T103447Z
```

- **186 arquivos de dados**: 109 da instalaÃ§Ã£o dev.5 e 77 do perfil; **401609147
  bytes**, 37 diretÃ³rios registrados, alÃ©m do manifesto/checksums/notas.
- Todos os arquivos de origem foram mantidos com handles exclusivos durante a
  cÃ³pia. NÃ£o houve arquivo bloqueado, cÃ³pia forÃ§ada ou encerramento de processos.
- Hash de cada arquivo de origem antes/depois igual ao da cÃ³pia, e estrutura/
  tamanhos conferidos independentemente, antes e depois da instalaÃ§Ã£o.
- ACL de raiz protegida, proprietÃ¡rio esperado e somente a conta autorizada;
  **228 entradas** de arquivo/diretÃ³rio conferidas antes e depois. Nenhum segredo
  foi descriptografado. O backup nÃ£o inclui o banco ou os dados do agente.
- Fora do Git e da instalaÃ§Ã£o; backups anteriores preservados. ConteÃºdo do perfil
  e inventÃ¡rios privados nÃ£o foram incluÃ­dos neste relatÃ³rio ou no Git.

SHA-256 dos metadados de recuperaÃ§Ã£o:

| Arquivo no backup | SHA-256 |
|---|---|
| `manifest.json` | `c8866baa193893a386f22244b20630dcbcdba2a7c74d1daf85be868f659ffcd8` |
| `SHA256SUMS.txt` | `66b239bb37a559f537a8d744e6dd666dbbde33d5c98574175b9d228de033b206` |
| `RECOVERY-NOTES.txt` | `510423f32a2b7e2e727ebd703e7bd66d0e98bd5bdbbd6606b7b3a0588dab82a7` |

O manifesto privado contÃ©m os hashes individuais para recuperaÃ§Ã£o; ele nÃ£o foi
copiado para o Git. Ver [verificaÃ§Ã£o independente](evidence/backup-independent-after.json).

## SequÃªncia e ocorrÃªncia da ferramenta

A primeira solicitaÃ§Ã£o de abertura Ã  ferramenta Computer Use expirou na aprovaÃ§Ã£o
do aplicativo. A inspeÃ§Ã£o posterior encontrou **nenhum instalador aberto**, nenhum
Electron e ainda dev.5 instalada. NÃ£o houve tentativa automÃ¡tica subsequente.
O usuÃ¡rio autorizou expressamente nova abertura apÃ³s renovar os gates.

Os gates e o backup foram revalidados **antes** dessa segunda solicitaÃ§Ã£o. Ela
abriu o NSIS: confirmaÃ§Ã£o de substituiÃ§Ã£o, destino e botÃ£o Instalar observados.
Houve **uma Ãºnica instalaÃ§Ã£o fÃ­sica**, no mesmo diretÃ³rio:

```text
<USERPROFILE>\AppData\Local\Programs\Lone Smart Room
```

O diÃ¡logo de confirmaÃ§Ã£o desapareceu apÃ³s Sim, invalidando seu handle; a janela
de destino foi reobservada, sem repetir o clique. NÃ£o foi erro do aplicativo.
O assistente concluiu normalmente e foi fechado por Concluir. A tela final nÃ£o
mostrou opÃ§Ã£o Executar, coerente com `runAfterFinish=false`. Dashboard, widget,
runtime, sensores e portÃ¡til **nÃ£o foram executados**.

NÃ£o houve bloqueio observado de Defender/SmartScreen, UAC, aviso de licenÃ§a,
solicitaÃ§Ã£o de reinicializaÃ§Ã£o ou erro de instalaÃ§Ã£o. O timeout anterior foi da
aprovaÃ§Ã£o da ferramenta; nÃ£o se atribui essa ocorrÃªncia Ã  seguranÃ§a do Windows.

EvidÃªncias reais do assistente:

- [ConfirmaÃ§Ã£o](evidence/01-update-confirmation.jpg)
- [Destino](evidence/02-destination.jpg)
- [Instalando](evidence/03-installing.jpg)
- [ConcluÃ­do sem execuÃ§Ã£o](evidence/04-completed-without-launch.jpg)

## InspeÃ§Ã£o estÃ¡tica posterior

- PE, ASAR e registro confirmam **2.0.0-dev.6**, produto Lone Smart Room, mesmo
  destino/identidade. ExecutÃ¡vel: `Lone Smart Room.exe` no diretÃ³rio acima.
- **114 arquivos de payload** iguais ao `win-unpacked` aprovado; total instalado
  **116**, incluindo uninstaller e seu Ã­cone. Uninstaller comparado ao bloco NSIS
  extraÃ­do estaticamente; Ã­cone conferido com o asset oficial.
- 18 recursos ASAR comparados e **39 arquivos do runtime** verificados pelo
  manifesto fixado. Inclui CPython 3.13.3, provedores CPU/RAM/volumes/PDH,
  coletor/cache, protocolo/implementaÃ§Ã£o Named Pipe e ponte ADLX somente leitura.
- O modelo instalado, analisado isoladamente como funÃ§Ã£o pura, conserva frescor
  GPU **3 s ativa / 11 s inativa**. O provedor instalado conserva ingresso
  **1,5 s**, mÃ­nimo de 2 s e oito campos GPU. Sem inicializar sensores ou IPC.
- Ponte instalada SHA-256:
  `c08a395c28865bdf07d1941a019ed3137ab5f70ada874bb85ffbc7f5f02e90ad`.
- **Named Pipe estÃ¡ presente como implementaÃ§Ã£o**, nÃ£o como endpoint ativo:
  aplicativo fechado nÃ£o deve iniciar monitoramento. Funcionamento real nÃ£o foi
  testado nesta atualizaÃ§Ã£o. Nenhum valor simulado foi apresentado como real.
- Os **77 arquivos do perfil** mantiveram hashes/conjunto exatos. Esquema 1,
  Ãºltimo modo **widget**, posiÃ§Ãµes/dimensÃµes e preferÃªncias preservados;
  minimizaÃ§Ã£o automÃ¡tica para bandeja continua **desligada**.
- ComparaÃ§Ã£o de Run/RunOnce (34 entradas), Inicializar (3 arquivos), serviÃ§os
  (323), tarefas (196) e firewall (712): **zero adiÃ§Ãµes, remoÃ§Ãµes ou mudanÃ§as**.
- Estado final: **zero processos Electron, monitoramento, ADLX e instaladores**.
  Nenhuma coleta ou nova interface de rede foi ativada.

Ver [recursos](evidence/installed-resources.json),
[monitoramento estÃ¡tico](evidence/monitoring-static.json) e
[estado do sistema](evidence/system-after.json).

## Agente e dados preservados

ConferÃªncia final autenticada em **26/10/2026 11:54 UTC**:

- Mesmo supervisor **5024**, worker **18304** e redirectors venv 19996/20352;
  identidade/imagens/argumentos/criaÃ§Ã£o iguais ao baseline. Nenhum reinÃ­cio.
- Listener Ãºnico **8776**, vinculado ao worker original em endereÃ§o LAN, sem
  wildcard. TLS 1.3 e status/apps HTTP 200, pin/hostname/certificado validados.
- **Zero grants e comandos pendentes**, banco Ã­ntegro, identidades cifradas,
  esquema e revogaÃ§Ãµes inalterados. Consultas podem atualizar nonce/last-seen;
  nÃ£o se exige igualdade byte a byte do banco operacional ativo.
- **86 arquivos operacionais protegidos** sem divergÃªncias; fontes do agente,
  Android, credenciais/certificados e DLL AMD preservados. **97 hashes dos fontes
  preparados** tambÃ©m conferidos, sem modificaÃ§Ãµes funcionais nesta etapa.
- Backups prÃ©-dev.3 (**341 arquivos**), prÃ©-dev.4 (**75**) e prÃ©-dev.5 (**156**)
  mantiveram hashes; novo backup dev.6 Ã­ntegro e com ACL restrita.

NÃ£o se abriu o Android nem solicitou nova confirmaÃ§Ã£o fÃ­sica do Samsung. NÃ£o se
executou Steam, CS2, WoL, energia ou teste funcional dos sensores. Electron segue
sem cliente HTTPS operacional. TLS, Crashpad e encerramento gracioso do agente
continuam pendÃªncias separadas, sem correÃ§Ã£o aqui.

## ReversÃ£o preparada â€” nÃ£o executada

1. Se houver problema em futura sessÃ£o, sair normalmente do aplicativo e aguardar
   seus componentes. NÃ£o forÃ§ar processos nem tocar no agente HTTPS.
2. Antes de restaurar, preservar separadamente o perfil/instalaÃ§Ã£o novos; registrar
   o problema e obter autorizaÃ§Ã£o especÃ­fica. Se houver bloqueios, nÃ£o forÃ§ar cÃ³pia.
3. Validar os hashes de manifesto/checksums acima, cada arquivo e ACL da cÃ³pia
   dev.5. O esquema de preferÃªncias permanece 1, sem migraÃ§Ã£o de credenciais.
4. Reavaliar o NSIS dev.5 preservado e seu SHA-256
   `fe616c66c71f30f7d6c220b49864b60b6aba5cbd4c6ee0a14a76763ddf776c49`,
   o suporte de substituiÃ§Ã£o e a consistÃªncia entre binÃ¡rios/registro antes de
   qualquer reversÃ£o assistida. NÃ£o executar downgrade automaticamente.
5. Com autorizaÃ§Ã£o, restaurar apenas os componentes da aplicaÃ§Ã£o de forma coerente
   com o registro. NÃ£o desinstalar/limpar dados. Comparar o resultado ao payload
   dev.5 antes de abrir. Perfil sÃ³ deve ser restaurado se necessÃ¡rio, com cÃ³pia do
   estado atual e sem presumir que downgrade preserve tudo automaticamente.
6. Banco, credenciais, certificados, Run e processos do agente nÃ£o fazem parte
   da reversÃ£o do Electron. NÃ£o restaurar hives gerais, serviÃ§os ou configuraÃ§Ãµes
   de rede. Preservar todos os pacotes, backups e checkpoints.

## PrÃ³ximo teste â€” requer autorizaÃ§Ã£o especÃ­fica

Uma Ãºnica sessÃ£o da dev.6 instalada, aproximadamente 150 s e mÃ¡ximo 180 s,
sem jogos/carga artificial: conferir agente/zero grants/perfil, abrir uma vez,
observar bootstrap e sensores reais, dashboard/widget/bandeja, atividade/inatividade
e retomada, medir CPU/RSS por componente e regularidade, validar null/zero/frescor.
Observar a ponte alÃ©m do antigo limite de 82 s. Encerrar normalmente por Sair,
conferir filhos/leases/pipe liberados e agente original intacto. Sem repetiÃ§Ã£o,
kill, atualizaÃ§Ã£o ou correÃ§Ãµes automÃ¡ticas se houver falha. Esta sessÃ£o **nÃ£o foi
executada nem estÃ¡ autorizada pelo procedimento de instalaÃ§Ã£o**.

Este registro Ã© exclusivamente documental. NÃ£o modifica o cÃ³digo nem reverte
os checkpoints funcionais. A Ã¡rvore Git deve permanecer limpa apÃ³s seu commit.
