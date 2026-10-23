# Teste autorizado de suspensão e Wake-on-LAN — 2026-10-23

O usuário autorizou expressamente uma única suspensão normal do Windows e fará
manualmente o envio de “Enviar Wake-on-LAN” no Samsung. Não foram autorizados
desligamento, reinicialização, mudanças de configuração WoL ou envio automático.

## Preparação salva antes da suspensão

- Samsung SM-S731B no Wi-Fi `172.31.216.105/24`; Ethernet Windows `172.31.161.169/24`.
  Mesma LAN autorizada `172.31.145.10/24`, confirmada por ADB.
- Ethernet no perfil Privado; agente HTTPS ouvindo em `172.31.161.169:8776`.
- Windows informa suporte a Espera S3; hibernação não está habilitada.
- O aplicativo instalado permanece 2.0.0-dev.1 / código 15. Dados e configuração
  WoL foram preservados e verificados na etapa anterior, sem mudanças neste teste.
- O ADB reconectou na porta anunciada por mDNS. Houve uma interrupção transitória
  de automação da interface; nenhuma suspensão ocorreu durante essa inspeção.
- Registros e alterações desta preparação foram salvos antes da solicitação de
  suspensão. O agente fica ativo intencionalmente, para retomar após o despertar.
- Pendência visual mantida: cabeçalho herdado ainda mostra “Versão 1.4”.

O teste utiliza a API normal Windows `SetSuspendState(false, false, false)`:
suspensão sem hibernação e mantendo habilitados os eventos de despertar.
Referência: [documentação Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/powrprof/nf-powrprof-setsuspendstate).
A permissão necessária é habilitada somente no token do processo auxiliar local;
nenhum comando remoto Android de energia é liberado. Um marcador de execução
única impede repetir a suspensão ao retomar ou ao ocorrer erro de transporte.

## Execução e resultado

Os arquivos da preparação foram salvos no commit
`8f40a3407657c0c19b6dd0e25359f4351c73ca47` antes da suspensão. A execução foi
protegida por marcador de uso único. Foi solicitada e registrada **uma suspensão**,
sem desligamento, reinicialização ou envio WoL pelo agente de desenvolvimento.

- Suspensão registrada: **11:40:56 de 23/10/2026**, horário de São Paulo
  (`2026-10-23T14:40:56.4391195Z`).
- Retorno registrado: **11:41:31**, horário de São Paulo
  (`2026-10-23T14:41:31.3372913Z`).
- Intervalo informado pelo Windows: aproximadamente **35 segundos**.
- Eventos do log System: Kernel-Power 42 (recordId 694), Kernel-Power 107
  (recordId 696) e Power-Troubleshooter 1 (recordId 706).
- Motivo da suspensão: Application API. Estado efetivo/solicitado registrado: 4;
  o Windows havia informado S3 como único estado de espera disponível.
- A API de suspensão retornou com sucesso. O marcador foi finalizado e não permite
  executar outra suspensão ao retomar o procedimento.

**O usuário confirmou expressamente: “Despertou pelo Wake-on-LAN no aplicativo”.**
O teste físico foi concluído com essa observação e com os eventos de suspensão e
retorno. O Windows informou origem **Unknown**, `WakeSourceType=0`, sem dispositivo
de despertar identificado. Portanto, não há atribuição independente à placa de
rede no log Windows; essa limitação fica preservada no resultado.

## Comunicação depois do despertar

- A Ethernet permaneceu Privada e o listener retomou em `172.31.161.169:8776`.
- O processo do agente permaneceu com PID 16264, o mesmo anterior à suspensão;
  não foi reiniciado manualmente, nem foi necessário abrir Electron.
- Foi solicitada **nova consulta** pelo Samsung, usando o pareamento já salvo.
  A interface mostrou **Conectado**, com última comunicação atualizada.
- O banco do agente registrou nonce autenticado novo, com requisição aproximada
  em `2026-10-23T14:45:34Z`, posterior ao retorno. O status não foi inferido de uma
  indicação antiga da tela.
- Não houve novo pareamento, exposição de credenciais, alteração de configurações
  WoL, firewall ou roteador. Não houve reinstalação, limpeza de dados ou liberação
  dos comandos remotos de energia do Android.

O script de consulta voltou à aba Controles e fechou somente um eventual painel
WoL para acessar o botão de status. Nenhuma ação de energia adicional foi executada.

## Preservação e pendência visual

Os 86 registros de originais e recuperação passaram novamente. Nenhum fonte
funcional foi alterado. Backups anteriores e os relatórios da instalação permanecem
preservados. O teste foi apenas de suspensão; não há nova validação de desligamento
completo nesta etapa, que não foi autorizada.

Permanece pendente corrigir o cabeçalho **“Versão 1.4”** em uma atualização futura.
A versão efetivamente instalada continua **2.0.0-dev.1 / código 15**.

Recibo: `suspend-wol-test.json`. Captura local após a nova consulta:
`.cache/validation/suspend-wol-connected.png`, fora do Git e sem credenciais.
