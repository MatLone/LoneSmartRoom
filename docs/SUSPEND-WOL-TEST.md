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

## Verificação após o retorno

Consultar novos eventos de suspensão/retorno do Windows e a origem do despertar,
reconfirmar a interface Privada e o listener, e solicitar uma nova consulta pelo
cliente Android. Só registrar “Conectado” após nova comunicação autenticada.
Se os eventos não distinguirem WoL de recuperação pelo botão físico, registrar
essa limitação e solicitar a observação do usuário. Não atribuir automaticamente
qualquer retorno ao WoL.

Recibo: `suspend-wol-test.json`. Enquanto não houver evidências de retorno e nova
consulta Android, o resultado do teste permanece pendente. Backups anteriores e
os relatórios da instalação permanecem preservados.
