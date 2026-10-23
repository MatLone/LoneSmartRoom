# Ativação autorizada da LAN — 2026-10-23

Validação física posterior: o Samsung atualizado pareou e consultou status HTTPS
pelo Wi-Fi da LAN. Consulte [SAMSUNG-INSTALLATION.md](SAMSUNG-INSTALLATION.md).
Os limites de testes locais abaixo descrevem a ativação anterior.

## Estado atual

- Ethernet confirmada como Privada, IP 172.31.161.169, sub-rede autorizada 172.31.145.10/24.
- Firewalls Windows Público, Privado e Domínio habilitados; não foram desabilitados.
- Agente seguro iniciado em segundo plano, independente do Electron, com apenas um
  listener em 172.31.161.169:8776. Nenhum bind 0.0.0.0 ou IPv6 foi utilizado.
- Regra `Lone Smart Room Secure Status HTTPS`: entrada TCP 8776, perfil Privado,
  interface Ethernet, destino 172.31.161.169, origem 172.31.145.10/24 e edge traversal Block.
- A regra também restringe o executável ao proprietário verificado do listener:
  C:\Python313\pythonw.exe. O launcher da .venv redireciona para essa imagem Windows.
- O script verifica a interface, o perfil e a linha de comando do listener antes
  de permitir a regra. Não substitui regras existentes e não altera o roteador.
- O código do agente continua recusando redes Públicas e origens fora da LAN.
  A mudança de perfil para Público não foi provocada como teste, para não
  interromper a rede do usuário; essa proteção já é coberta pelos testes da etapa 2.

## Testes realizados no listener ativo

`scripts/probe-secure-lan.py` utiliza o certificado real e o endereço Ethernet do
agente. Emite um código de teste em memória, sem imprimir credenciais e sem
invalidar uma janela de pareamento que o usuário já esteja usando.

- Pareamento HTTPS real: passou.
- Classes de produção Kotlin AgentAuth e Java PinnedTls executadas na JVM:
  status com credencial correta 200; repetição 401; chave incorreta 401;
  certificado com pin incorreto rejeitado; rota de ações 404.
- Revogação da identidade temporária seguida de nova consulta: 401.
- Credencial de teste revogada no finally, inclusive se o teste falhar. Seu registro
  revogado permanece no banco para rastreabilidade. Não há chave no relatório/Git.
- Regressão de preservação: cinco testes passaram; pacote WoL compilado passou
  sem envio UDP; os 86 registros de originais e cópias de recuperação não mudaram.
- Comando manual de inicialização reconhece o processo existente sem duplicá-lo.

Recibos sem credenciais: `docs/lan-firewall-receipt.json` e
`docs/lan-probe-results.json`.

## Limites da validação

Atualização posterior: o Samsung foi conectado por ADB e teve sua assinatura
verificada, sem instalação. Consulte [SAMSUNG-VALIDATION.md](SAMSUNG-VALIDATION.md).
Os limites abaixo descrevem o momento dos testes de ativação da LAN.

O cliente JVM foi executado no próprio Windows, usando o endereço da Ethernet.
Isso comprova o protocolo e a identidade TLS do serviço ativo, mas não comprova
travessia da regra de firewall a partir de um segundo dispositivo. A regra foi
inspecionada no Windows e a validação entre equipamentos permanece pendente.

ADB não encontrou Samsung conectado. Nenhum APK foi instalado ou atualizado,
nenhum dado do Android foi limpo e nenhuma configuração WoL foi alterada. A chave
debug original corresponde ao APK de recuperação; ainda é necessário comparar
com o certificado do APK efetivamente instalado no Samsung.

Não foram executados desligamento, suspensão, reinicialização ou abertura de
aplicativos pelo canal Android. Não houve acesso/configuração do roteador, NAT,
UPnP ou encaminhamento de portas; configurações já existentes no roteador não foram
auditadas. Não foi realizado teste físico de Wake-on-LAN nesta ativação.

## Próximo teste com o aparelho

Conectar o Samsung por USB/ADB para inspeção somente leitura da assinatura do APK
instalado. Seguir o plano de assinatura em STAGE2.md antes de qualquer atualização.
Após compatibilidade e preservação de dados comprovadas, testar o cliente no Wi-Fi
da LAN autorizada, comparar o fingerprint com a tela Windows e validar somente
status e revogação. Não ampliar a sub-rede ou liberar HTTP como contorno.
