# Protocolo implementado: status HTTPS v2

Somente TLS 1.2+; certificado autoassinado RSA-3072/SHA-256 com SAN IPv4 e EKU
serverAuth. O Android exige o SHA-256 DER exato, validade temporal, assinatura do
certificado e verificação padrão de hostname/SAN. Não há trust-all, redirecionamento
ou HTTP alternativo. O endereço deve ser IPv4 RFC1918 numa LAN explícita /24..30.

## Pareamento iniciado no Windows

`secure_agent.py pair` cria um código aleatório de 192 bits, válido por 180 segundos.
O SQLite persiste somente seu hash e prazo. Um novo código invalida o anterior;
o consumo é transacional e de uso único. Máximo de cinco tentativas por IP/minuto.

O texto `LSR2.<base64url(JSON)>` contém `url`, `network`, `sha256`, `code`, `expires`.
Ele deve ser copiado diretamente da tela Windows confiável. O Android mostra URL e
fingerprint para comparação antes de conectar. Obter o fingerprint da própria
conexão não é um método de confiança e não é realizado pelo cliente.

`POST /v2/pair`, JSON `code` e `label`, retorna `ok`, `device_id` e `secret` somente
pela conexão TLS já autenticada. Identificadores são aleatórios de 128 bits; chaves
HMAC são individuais de 256 bits. O segredo não passa pelo JavaScript da WebView.

## Consulta autenticada

`GET /v2/status`, sem corpo, exige:

- `X-Lone-Device`: 32 caracteres hexadecimais minúsculos.
- `X-Lone-Timestamp`: Unix UTC em segundos, janela de 60 segundos.
- `X-Lone-Nonce`: 128 bits aleatórios, em hexadecimal.
- `X-Lone-Signature`: HMAC-SHA256 hexadecimal da representação abaixo.

```text
LSR2\n{device_id}\n{timestamp}\n{nonce}\nGET\n/v2/status\n
```

Não há espaço adicional ou newline após o último `\n`. Para generalização da
função de assinatura, bytes do corpo seguem esse último newline; a rota de status
aceita somente corpo vazio. O SQLite impede repetição inclusive após reinício,
e a revogação é verificada na mesma transação que consome o nonce.

Resposta autenticada pelo TLS: `ok=true`, `agent=online`, `version=2.0.0`,
`scope=status`. Isso significa agente alcançável; não descreve estado elétrico do PC.
401 não distingue dispositivo inexistente, assinatura inválida, expirado ou revogado.

Limites: corpo de pareamento de 1024 bytes, 12 conexões simultâneas, timeout de
socket de cinco segundos, nenhuma rota de ações. Requisições rejeitadas podem
ter até 4096 bytes drenados para devolver uma resposta limpa, sem processar o corpo.

## Armazenamento e separação

Windows: `.runtime/secure-agent`, fora do Git, chaves de dispositivos protegidas por
DPAPI CurrentUser; chave TLS PKCS8 cifrada com senha aleatória protegida por DPAPI.
Android: AES-256-GCM com chave do Android Keystore e arquivo em noBackupFilesDir.
Nenhuma credencial é escrita em localStorage, logs ou interface JavaScript.

A API HTTP/HMAC v1 e seus executores permanecem nos arquivos legados para
compatibilidade e preservação; o agente seguro não os importa nem os inicia.
O cliente Android v2 não conhece rotas de energia ou de abertura de aplicativos.
