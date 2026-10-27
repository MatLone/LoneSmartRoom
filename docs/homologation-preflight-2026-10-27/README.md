# Homologação Windows e Android — bloqueio na pré-verificação

Data local: 2026-10-27, America/Sao_Paulo.

## Resultado

A sequência foi interrompida na Etapa 1, antes da instalação Android e antes de
qualquer abertura do Windows instalado. O agente HTTPS já estava offline:
nenhum supervisor/worker identificado e nenhum listener TCP 8776. A consulta de
listener terminou normalmente; não se tratou de indisponibilidade dessa leitura.

Não houve execução de `adb install -r`, instalação, desinstalação, limpeza de
dados, abertura de Electron, início de sensores ou inicialização do agente.

## Verificações concluídas

| Verificação | Resultado |
|---|---|
| Repositório | Árvore inicialmente limpa; `git fsck --no-dangling` aprovado |
| Checkpoints | `7c4ddd1`, `a7310a4`, `8fb005c`, `90c89b6`, `75d00eb`, `e6f2897`, `d7e2fc8`, `29d12a6`, `1aa7d3a`, `97c82ca` preservados como ancestrais |
| Samsung por ADB | Um Galaxy S25 FE, modelo SM-S731B, conectado e autorizado por depuração sem fio |
| Android instalado | `com.lonesmartroom.app`, 2.0.0-dev.7, código 21 |
| APK candidato | Mesmo package, 2.0.0-dev.9, código 23; 1.246.709 bytes |
| SHA-256 do candidato | `92713289374d0c7824ec573713f78e406e1f73b914714c10264d19dc06ac7df2` |
| Certificado do candidato e do APK atualmente instalado | Ambos `02c5b46ab301cdfb7a1d858588b1122eb00be1bfd12349ea9f0d1e40a53d1bc8`; apksigner verificou assinatura v2 de ambos |
| Windows instalado | Executável presente, FileVersion `2.0.0-dev.7`; não aberto |
| Processos do agente | Zero candidatos nas consultas realizadas |
| Listener 8776 | Ausente |
| Electron / componentes de monitoramento pesquisados | Nenhum identificado |
| Banco operacional | `PRAGMA quick_check` aprovado, abertura somente leitura |
| Grants | Zero |
| Configuração e certificados protegidos | Hashes de `config.dpapi`, `server.crt`, `server.key`, `tls.dpapi` iguais aos registros anteriores |

Os identificadores de transporte ADB, caminhos internos do aparelho e o dumpsys
completo ficaram somente no cache local ignorado. O APK instalado foi copiado
para esse cache para conferir seu certificado; isso não modifica dados do app.
Não foram expostos ou descriptografados segredos.

A primeira tentativa de inventário ADB no sandbox não conseguiu acessar o daemon.
A verificação foi refeita no contexto normal do usuário, mediante a autorização
de ferramentas, e encontrou o dispositivo. Nenhuma instalação foi tentada em
qualquer contexto. Não houve elevação administrativa ou instalação de ferramentas.

## Não verificado / pendente

- TLS 1.3, autenticação, hostname e pinagem atuais: sem serviço, nenhuma consulta
  HTTPS foi enviada; os hashes preservados não comprovam disponibilidade.
- Dados WoL e pareamento no Samsung: não acessados nem alterados; a preservação
  após atualização ainda exige instalação e conferência posteriores. Nenhum WoL
  funcional foi enviado.
- Identidade visual real dev.9, safe areas, três abas, splash e ícone no Samsung:
  aguardam atualização. O candidato preserva as inspeções publicadas em
  `docs/android-dev9-2026-10-26`; não se apresentam prévias como capturas atuais.
- Integridade completa da instalação Windows e comparação atual dos backups:
  não concluídas; verificou-se apenas a presença e versão do executável antes de
  registrar o bloqueio. Nenhum backup foi modificado ou restaurado.
- Homologação física Windows dev.7: nenhuma sessão iniciada, sem medições novas
  de CPU/RAM, widget, sensores, bandeja ou retomada GPU.
- Não houve escrita em HKCU Run, firewall, serviços ou tarefas. Não foi feita
  nesta interrupção uma comparação completa de seus hashes.

As pendências TLS 10054, inicialização automática, encerramento gracioso,
Crashpad 0xE9 e homologação parcial dev.7 continuam abertas. A causa de o agente
estar offline hoje não foi determinada por esta pré-verificação; não atribuir
causalidade à atualização ou aos testes, pois nenhum dos dois começou.

## Próxima decisão

Solicitar autorização específica para uma recuperação manual única do agente
pelo launcher anteriormente validado, com novos gates de identidade, integridade,
porta livre e zero grants. Não alterar HKCU Run nem usar o mecanismo de
encerramento ainda não validado. Se houver divergência, parar antes do lançamento.

Depois da recuperação aprovada, renovar as verificações desta homologação antes
de instalar o mesmo APK por `adb install -r`, com serial novamente confirmado.
Não repetir automaticamente lançamento ou instalação se houver falha.

Para Windows, propor uma sessão única de até 120 s, contar desde o lançamento,
priorizar verificações e Sair até aproximadamente 45 s, reservando o restante
para conferir encerramento e preservação. Se a bandeja não for controlável,
solicitar ao usuário somente a ação pontual necessária, com instrução objetiva.
Não começar essa sessão enquanto os gates anteriores não forem aprovados.

## Evidências e reversão

`preflight.json` contém apenas o resumo sanitizado. Os registros detalhados ficam
em `.cache/validation/homologation-2026-10-27`, fora do Git. A tarefa não realizou
mudança operacional que exija reversão. Não restaurar backups nem executar
downgrade, desinstalação ou limpeza para reverter este registro documental.
